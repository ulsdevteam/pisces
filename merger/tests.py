import json
import os
from unittest.mock import patch

import vcr
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from fetcher.fetchers import BaseDataFetcher

from .mergers import (AgentMerger, ArchivalObjectMerger, ArrangementMapMerger,
                      ResourceMerger, SubjectMerger)

merger_vcr = vcr.VCR(
    serializer='json',
    cassette_library_dir='fixtures/cassettes/merger',
    record_mode='once',
    match_on=['path', 'method', 'query'],
    filter_query_parameters=['username', 'password', 'modified_since'],
    filter_headers=['Authorization', 'X-ArchivesSpace-Session'],
    filter_post_data_parameters=['password']
)


object_types = [
    ("agent_corporate_entity", AgentMerger, ["agent_corporate_entity"]),
    ("agent_family", AgentMerger, ["agent_family"]),
    ("agent_person", AgentMerger, ["agent_person"]),
    ("archival_object", ArchivalObjectMerger, ["archival_object", "archival_object_collection"]),
    ("resource", ResourceMerger, ["resource"]),
    ("subject", SubjectMerger, ["subject"]),
    ("arrangement_map_component", ArrangementMapMerger, ["resource"])
]


class MergerTest(TestCase):
    """Tests Merger."""

    def setUp(self):
        self.factory = APIRequestFactory()

    @patch("merger.mergers.ArchivalObjectMerger.get_position")
    def test_merge(self, mock_position):
        """Tests Merge.

        get_position is mocked because it is tested separately below and requires
        additional fetches not in the cassette.
        """
        mock_position.return_value = 1
        for source_object_type, merger, target_object_types in object_types:
            with merger_vcr.use_cassette("{}-merge.json".format(source_object_type)):
                transform_count = 0
                clients = BaseDataFetcher().instantiate_clients()
                for f in os.listdir(os.path.join("fixtures", "merger", source_object_type)):
                    with open(os.path.join("fixtures", "merger", source_object_type, f), "r") as json_file:
                        source = json.load(json_file)
                        merged, t = merger(clients).merge(source_object_type, source)
                        # with open(os.path.join("fixtures", "transformer", t, "{}.json".format(merged["uri"].split("/")[-1])), "w") as df:
                        #     json.dump(merged, df, indent=4, sort_keys=True)
                        self.assertNotEqual(
                            merged, False,
                            "Merger returned an error: {}".format(merged))
                        transform_count += 1
                        self.assertTrue(merged.get("jsonmodel_type") in target_object_types)
                        self.check_counts(source, source_object_type, merged, merged.get("jsonmodel_type"))
                        self.check_group(merged)
                        self.check_position(merged)
                        self.check_embedded(merged)

    def check_counts(self, source, source_object_type, merged, target_object_type):
        """Tests counts of data keys in merged object.

        Archival objects are expected to have values in dates and one of
            language or lang_materials fields.
        Archival object collections are expected to have values in dates,
            extents, linked_agents, and one of language or
            lang_materials fields
        Resources are expected to have at least as many ancestors in the merged
            data as in the source.
        """
        if target_object_type == "archival_object":
            for field in ["dates", "extents"]:
                self.assertTrue(self.not_empty(merged.get(field)), "{} on {} was empty".format(field, merged))
            self.assertTrue(
                bool(self.not_empty(merged.get("language")) or self.not_empty(merged.get("lang_materials"))), merged)
        elif target_object_type == "archival_object_collection":
            for field in ["dates", "extents", "linked_agents"]:
                self.assertTrue(self.not_empty(merged.get(field)), "{} on {} was empty".format(field, merged))
            self.assertTrue(
                bool(self.not_empty(merged.get("language")) or self.not_empty(merged.get("lang_materials"))))
        elif target_object_type == "resource":
            if source_object_type == "arrangement_map":
                self.assertTrue(len(merged.get("ancestors", [])) > len(source.get("ancestors", [])),
                                "{} does not have more ancestors in merged data than source data.".format(merged))
            else:
                self.assertTrue(len(merged.get("ancestors", [])) >= len(source.get("ancestors", [])),
                                "{} does not have equal or more ancestors in merged data than source data.".format(merged))

    def check_group(self, merged):
        field_list = ["identifier", "title", "dates", "creators"]
        if merged.get("jsonmodel_type") == "subject":
            field_list = ["identifier", "title"]
        elif merged.get("jsonmodel_type", "").startswith("agent_"):
            field_list = ["identifier", "title", "creators"]
        for field in field_list:
            self.assertTrue(self.not_empty(merged["group"][field]), "Group field {} on object {} was empty".format(field, merged["uri"]))

    def check_position(self, merged):
        if merged.get("jsonmodel_type") in ["archival_object", "resource"]:
            self.assertTrue(isinstance(merged.get("position"), int))

    def not_empty(self, value):
        return False if value in ['', [], {}, None] else True

    def check_embedded(self, merged):
        """Tests that title and type fields are present in embedded reference objects."""
        for key in ["ancestors", "subjects", "linked_agents"]:
            for obj in merged.get(key, []):
                self.assertTrue(
                    self.not_empty(obj.get("title")),
                    "Title field of {} in {} is empty".format(obj.get("ref"), merged.get("uri")))
                self.assertTrue(
                    self.not_empty(obj.get("type")),
                    "Type field of {} in {} is empty".format(obj.get("ref"), merged.get("uri")))

    def test_parse_instances(self):
        with merger_vcr.use_cassette("archival_object-merge.json"):
            clients = BaseDataFetcher().instantiate_clients()
            merger = ArchivalObjectMerger(clients)
            fixture_dir = os.path.join("fixtures", "merger", "instance_parse")
            for f in os.listdir(fixture_dir):
                with open(os.path.join(fixture_dir, f), "r") as json_file:
                    source_data = json.load(json_file)
                    for parsed_pair in source_data:
                        parsed = merger.parse_instances(parsed_pair["source"])
                        self.assertEqual(parsed, parsed_pair["parsed"])

    def test_position(self):
        """Asserts that collection positions are calculated correctly."""
        EXPECTED = {"/repositories/2/archival_objects/1113591": 14362,
                    "/repositories/2/archival_objects/13832": 140323,
                    "/repositories/2/archival_objects/482045": 36134,
                    "/repositories/2/archival_objects/487369": 40707,
                    "/repositories/2/archival_objects/892776": 134904}
        with merger_vcr.use_cassette("position.json"):
            clients = BaseDataFetcher().instantiate_clients()
            merger = ArchivalObjectMerger(clients)
            fixture_dir = os.path.join("fixtures", "merger", "position")
            for f in os.listdir(fixture_dir):
                with open(os.path.join(fixture_dir, f), "r") as json_file:
                    source_data = json.load(json_file)
                    collection_index = merger.get_position(source_data)
                    self.assertEqual(
                        collection_index, EXPECTED[source_data['uri']],
                        f"Expected {EXPECTED[source_data['uri']]}, got {collection_index}")
