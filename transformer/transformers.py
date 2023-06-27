import json
from os.path import join

from django.conf import settings
from jsonschema.exceptions import ValidationError
from odin.codecs import json_codec
from rac_schema_validator import is_valid

from .mappings import (SourceAgentCorporateEntityToAgent,
                       SourceAgentFamilyToAgent, SourceAgentPersonToAgent,
                       SourceArchivalObjectToCollection,
                       SourceArchivalObjectToObject,
                       SourceResourceToCollection, SourceSubjectToTerm)
from .models import DataObject
from .resources.source import (SourceAgentCorporateEntity, SourceAgentFamily,
                               SourceAgentPerson, SourceArchivalObject,
                               SourceResource, SourceSubject)


class TransformError(Exception):
    """Sets up the error messaging for AS transformations."""
    pass


class Transformer:
    """Data Transformer.

    Selects the appropriate mapping configs, transforms and validates data.
    Validated data is saved to the application's database as a DataObject.

    Args:
        object_type (str): the object type of the source data.
        data (dict): the source data to be transformed.
    """

    def run(self, object_type, data):
        try:
            self.identifier = data.get("uri")
            from_resource, mapping, schema_name = self.get_mapping_classes(object_type)
            transformed = self.get_transformed_object(data, from_resource, mapping)
            online_pending = self.get_online_pending(
                data.get("instances", []), transformed.get("online", False))
            self.validate_transformed(transformed, schema_name)
            self.save_validated(transformed, online_pending)
            return transformed
        except ValidationError as e:
            raise TransformError("Transformed data is invalid: {}".format(e))
        except Exception as e:
            raise TransformError("Error transforming {} {}: {}".format(object_type, self.identifier, str(e)))

    def get_mapping_classes(self, object_type):
        TYPE_MAP = {
            "agent_person": (SourceAgentPerson, SourceAgentPersonToAgent, settings.SCHEMAS["agent"]),
            "agent_corporate_entity": (SourceAgentCorporateEntity, SourceAgentCorporateEntityToAgent, settings.SCHEMAS["agent"]),
            "agent_family": (SourceAgentFamily, SourceAgentFamilyToAgent, settings.SCHEMAS["agent"]),
            "resource": (SourceResource, SourceResourceToCollection, settings.SCHEMAS["collection"]),
            "archival_object": (SourceArchivalObject, SourceArchivalObjectToObject, settings.SCHEMAS["object"]),
            "archival_object_collection": (SourceArchivalObject, SourceArchivalObjectToCollection, settings.SCHEMAS["collection"]),
            "subject": (SourceSubject, SourceSubjectToTerm, settings.SCHEMAS["term"])
        }
        return TYPE_MAP[object_type]

    def get_online_pending(self, instances, online):
        """
        If published digital object instances are present in the source but the transformed
        `online` field is set to False, mark the object as pending an online asset.

        Args:
            instances (list): source instances.
            online (bool): value of `online` field from transformed object.
        """
        published_digital_instances = [v for v in instances if v["instance_type"] == "digital_object" and v.get("digital_object", {}).get("_resolved", {}).get("publish")]
        if len(published_digital_instances) and not online:
            return True
        return False

    def get_transformed_object(self, data, from_resource, mapping):
        from_obj = json_codec.loads(json.dumps(data), resource=from_resource)
        transformed = json.loads(json_codec.dumps(mapping.apply(from_obj)))
        return self.remove_keys_from_dict(transformed)

    def remove_keys_from_dict(self, data, target_key="$"):
        """Removes all matching keys from dict."""
        modified_dict = {}
        if hasattr(data, 'items'):
            for key, value in data.items():
                if key != target_key:
                    if isinstance(value, dict):
                        modified_dict[key] = self.remove_keys_from_dict(data[key])
                    elif isinstance(value, list):
                        modified_dict[key] = [self.remove_keys_from_dict(i) for i in data[key]]
                    else:
                        modified_dict[key] = value
        else:
            return data
        return modified_dict

    def validate_transformed(self, data, schema_name):
        """Validates an object againse the specified schema."""
        base_schema = None
        if settings.SCHEMAS.get("base"):
            base_file = open(join(settings.SCHEMAS['base_dir'], settings.SCHEMAS['base']), 'r')
            base_schema = json.load(base_file)
            base_file.close()
        with open(join(settings.SCHEMAS['base_dir'], schema_name), 'r') as object_file:
            object_schema = json.load(object_file)
            is_valid(data, object_schema, base_schema)

    def save_validated(self, data, online_pending):
        es_id = data["uri"].split("/")[-1]
        try:
            existing = DataObject.objects.get(es_id=es_id)
            existing.data = data
            existing.indexed = False
            existing.online_pending = online_pending
            existing.save()
        except DataObject.DoesNotExist:
            DataObject.objects.create(
                es_id=es_id,
                object_type=data["type"],
                data=data,
                indexed=False,
                online_pending=online_pending)
