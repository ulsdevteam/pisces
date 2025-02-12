from requests.exceptions import ConnectionError

from .helpers import (ArchivesSpaceHelper, MissingArchivalObjectError,
                      add_group, closest_creators, closest_parent_value,
                      combine_references, handle_cartographer_reference,
                      indicator_to_integer)


class MergeError(Exception):
    pass


class BaseMerger:
    """Base merger class."""

    def __init__(self, clients):
        try:
            self.aspace_helper = ArchivesSpaceHelper(clients["aspace"])
            self.cartographer_client = False
        except Exception as e:
            raise MergeError(e)

    def merge(self, object_type, object):
        """Main merge function.

        Fetches and merges additional data from secondary data sources, then
        delivers merged data to the configured URL."""
        try:
            identifier = self.get_identifier(object)
            target_object_type = self.get_target_object_type(object)
            additional_data = self.get_additional_data(object, target_object_type)
            return self.combine_data(object, additional_data), target_object_type
        except MissingArchivalObjectError:
            pass
        except ConnectionError as e:
            raise MergeError(f"Error merging {identifier}: {e} for request {e.request.__dict__}")
        except Exception as e:
            raise MergeError(f"Error merging {identifier}: {e}")

    def get_identifier(self, object):
        """Returns the identifier for the object."""
        try:
            identifier = object["uri"]
        except KeyError:
            identifier = object["ref"]
        return identifier

    def get_additional_data(self, object, object_type):
        pass

    def combine_data(self, object, additional_data):
        return add_group(object, self.aspace_helper.aspace.client)

    def get_target_object_type(self, data):
        """Returns object type.

        Archival objects that have children are mapped differently from those
        without.
        """
        if data.get("jsonmodel_type") == "archival_object":
            if self.aspace_helper.has_children(data["uri"]):
                return "archival_object_collection"
        return data.get("jsonmodel_type")

    def arrangement_map_component_by_uri(self, uri):
        resp = self.cartographer_client.get("/api/find-by-uri/", params={"uri": uri})
        resp.raise_for_status()
        json_data = resp.json()
        if json_data["count"] > 0:
            return json_data["results"][0]
        return None


class ArchivalObjectMerger(BaseMerger):

    def get_additional_data(self, object, object_type):
        """Fetches additional data from ArchivesSpace and Cartographer.

        Args:
            object (dict): source object (an ArchivesSpace archival object record).
            object_type (str): the source object type, either `archival_object`
                or `archival_object_collection`.

        Returns:
            dict: a dictionary of data to be merged.
        """
        data = {"ancestors": [], "linked_agents": []}
        if self.cartographer_client:
            data.update(self.get_cartographer_data(object))
        data.update(self.get_archivesspace_data(object, object_type))
        return data

    def get_cartographer_data(self, object):
        """Gets ancestors, if any, from the archival object's resource record in
        Cartographer."""
        data = {"ancestors": []}
        result = self.arrangement_map_component_by_uri(object["resource"]["ref"])
        if result:
            for a in result.get("ancestors", []):
                data["ancestors"].append(handle_cartographer_reference(a))
        return data

    def get_language_data(self, object, data):
        """Gets language data from ArchivesSpace.

        This logic accomodates ArchivesSpace API changes between 2.6 and 2.7.
        """
        if "lang_materials" in object:
            if object.get("lang_materials") in ["", [], {}]:
                data["lang_materials"] = closest_parent_value(object, "lang_materials")
        else:
            data["language"] = closest_parent_value(object, "language")
        return data

    def parse_instances(self, instances):
        """Attempts to parse extents from instances.

        Initially, child subcontainers are parsed to determine
        the extent number and extent type. If a child subcontainer does not
        exist, the parent container is parsed.
        """

        def append_to_list(extents, extent_type, extent_number):
            """Merges or appends extent objects to an extent list.

            Only operates over instances with a sub_container (i.e. skips
            digital object instances.

            Args:
                extents (list): a list of extents to update.
                extent_type (str): the extent type to add.
                extent_number (int): the extent number to add
            """
            matching_extents = [e for e in extents if e["extent_type"] == extent_type]
            if matching_extents:
                matching_extents[0]["number"] += extent_number
            else:
                extents.append({"extent_type": extent_type, "number": extent_number})
            return extents

        extents = []
        for instance in [i for i in instances if i.get("sub_container")]:
            try:
                sub_container_parseable = all(i_type in instance.get("sub_container", {}) for i_type in ["indicator_2", "type_2"])
                if sub_container_parseable:
                    number_list = [i.strip() for i in instance["sub_container"]["indicator_2"].split("-")]
                    range = sorted(map(indicator_to_integer, number_list))
                    extent_type = instance["sub_container"]["type_2"]
                    extent_number = range[-1] - range[0] + 1 if len(range) > 1 else 1
                else:
                    instance_type = instance["instance_type"].lower()
                    sub_container_type = instance["sub_container"]["top_container"]["_resolved"].get("type", "").lower()
                    extent_type = "{} {}".format(instance_type, sub_container_type) if sub_container_type != "box" else sub_container_type
                    extent_number = 1
                extents = append_to_list(extents, extent_type.strip(), extent_number)
            except Exception as e:
                raise Exception(f"Error parsing instances: {e}") from e
        return extents

    def get_position(self, object):
        """Gets the position of the object within the collection.

        This is calculated based on the sum of previous ancestors, previous top
        ancestors in ArchivesSpace, and previous ancestors in Cartographer.
        """

        previous_ancestors_count = 0
        for idx, ancestor in enumerate(object["ancestors"]):
            target_node = object["ancestors"][idx - 1] if idx > 0 else object
            if "resource" not in ancestor["ref"]:
                tree_node = self.aspace_helper.tree_node(object["resource"]["ref"], ancestor["ref"])
                previous_ancestors_count += self.aspace_helper.objects_before(
                    target_node,
                    tree_node,
                    object["resource"]["ref"],
                    ancestor["ref"])

        target_node = object["ancestors"][-2] if len(object["ancestors"]) > 1 else object
        tree_root = self.aspace_helper.tree_root(object["resource"]["ref"])
        previous_top_ancestors_count = self.aspace_helper.objects_before(
            target_node,
            tree_root,
            object["resource"]["ref"])

        cartographer_count = 0
        if self.cartographer_client:
            result = self.arrangement_map_component_by_uri(object["resource"]["ref"])
            if result:
                resp = self.cartographer_client.get(f"{result['ref']}objects_before/").json()
                cartographer_count = resp.get("count", 0)

        return sum([previous_ancestors_count, previous_top_ancestors_count, cartographer_count])

    def get_archivesspace_data(self, object, object_type):
        """Gets dates, languages, and extent from archival object's
        resource record in ArchivesSpace.
        """
        data = {"linked_agents": []}
        if object.get("dates") in ["", [], {}, None]:
            data["dates"] = closest_parent_value(object, "dates")
        data.update(self.get_language_data(object, data))
        if not object.get("extents"):
            extent_data = self.parse_instances(object["instances"])
            if object_type == "archival_object_collection" and not extent_data:
                extent_data = closest_parent_value(object, "extents")
            data["extents"] = extent_data
        if object_type == "archival_object_collection":
            data["linked_agents"] = closest_creators(object)
        data["position"] = self.get_position(object)
        return data

    def combine_data(self, object, additional_data):
        """Combines additional data with source data.

        Moves data from resolved objects to expected keys within main object.
        Removes resolved top_container data.
        """
        for k, v in additional_data.items():
            if isinstance(v, list):
                object[k] = object.get(k, []) + v
            else:
                object[k] = v
        for instance in object.get("instances", []):
            if instance.get("sub_container", {}).get("top_container", {}).get("_resolved"):
                del instance["sub_container"]["top_container"]["_resolved"]
        object = super(ArchivalObjectMerger, self).combine_data(object, additional_data)
        return combine_references(object)


class ArrangementMapMerger(BaseMerger):

    def get_target_object_type(self, data):
        return "resource"

    def get_additional_data(self, object, object_type):
        """Fetches the ArchivesSpace resource record referenced by the
        ArrangementMapComponent.

        Args:
            object (dict): source object (an ArrangementMapComponent).
            object_type (str): the source object type, `arrangement_map_component`.

        Returns:
            dict: a dictionary of data to be merged.
        """
        return self.aspace_helper.aspace.client.get(
            object["archivesspace_uri"],
            params={"resolve": ["subjects", "linked_agents"]}).json()

    def combine_data(self, object, additional_data):
        """Adds Cartographer ancestors to ArchivesSpace resource record."""
        additional_data["ancestors"] = [handle_cartographer_reference(a) for a in object.get("ancestors", [])]
        additional_data["position"] = object["order"]
        additional_data = add_group(additional_data, self.aspace_helper.aspace.client)
        return combine_references(additional_data)


class AgentMerger(BaseMerger):
    pass


class ResourceMerger(BaseMerger):

    def get_additional_data(self, object, object_type):
        """Gets additional data from Cartographer and ArchivesSpace.

        Args:
            object (dict): source object (an ArchivesSpace resource record).
            object_type (str): the source object type, always `resource`.

        Returns:
            dict: a dictionary of data to be merged.
        """
        if self.cartographer_client:
            return self.get_cartographer_data(object)

    def get_cartographer_data(self, object):
        """Returns ancestors (if any) for the resource record from
        Cartographer."""
        data = {"ancestors": []}
        result = self.arrangement_map_component_by_uri(object["uri"])
        if result:
            resp = self.cartographer_client.get(f"{result['ref']}objects_before/").json()
            data["order"] = resp.get("count", 0)
            for a in result.get("ancestors", []):
                data["ancestors"].append(handle_cartographer_reference(a))
        return data

    def combine_data(self, object, additional_data):
        """Combines existing ArchivesSpace data with Cartographer data.

        Adds Cartographer ancestors to object's `ancestors` key.
        """
        object["ancestors"] = additional_data["ancestors"] if self.cartographer_client else []
        object["position"] = additional_data.get("order", 0) if additional_data else 0
        object = super(ResourceMerger, self).combine_data(object, additional_data)
        return combine_references(object)


class SubjectMerger(BaseMerger):
    pass
