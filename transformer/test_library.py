import json
import objectpath
import os
from transformer.models import *
from pisces import settings


def process_tree_item(data):
    if not Identifier.objects.filter(source=Identifier.CARTOGRAPHER, identifier=data.get('ref')).exists():
        c = Collection.objects.create(source_tree=data)
        SourceData.objects.create(collection=c, source=SourceData.CARTOGRAPHER, data=data)
        Identifier.objects.create(collection=c, source=Identifier.CARTOGRAPHER, identifier=data.get('ref'))
        print("Imported {}".format(data.get('ref')))
        # Save collections in tree that come from AS
    for collection in data.get('children'):
        if 'maps' in collection.get('ref'):
            process_tree_item(collection)


def import_fixture_data(source_filepath=None):
    source_filepath = os.path.join(source_filepath) if source_filepath else os.path.join(settings.BASE_DIR, 'fixtures')
    TYPE_MAP = {'agent_corporate_entity': [Agent, 'agent'],
                'agent_family': [Agent, 'agent'],
                'agent_person': [Agent, 'agent'],
                'archival_objects': [Object, 'object'],
                'resources': [Collection, 'collection'],
                'subjects': [Term, 'term']}

    for d in os.listdir(source_filepath):
        # Handle data from ArchivesSpace
        if (d not in ['trees', 'maps']) and os.path.isdir(os.path.join(source_filepath, d)):
            cls = TYPE_MAP[d][0]
            key = TYPE_MAP[d][1]
            for f in os.listdir(os.path.join(source_filepath, d)):
                with open(os.path.join(source_filepath, d, f)) as jf:
                    data = json.load(jf)
                    if not Identifier.objects.filter(source=Identifier.ARCHIVESSPACE, identifier=data.get('uri')).exists():
                        # Handle archival object records
                        if d == 'archival_objects':
                            resource_id = data.get('resource').get('ref').split('/')[-1]
                            # Load tree JSON
                            with open(os.path.join(source_filepath, 'trees', '{}.json'.format(resource_id))) as tf:
                                tree_data = json.load(tf)
                                full_tree = objectpath.Tree(tree_data)
                                partial_tree = full_tree.execute("$..children[@.record_uri is '{}']".format(data.get('uri')))
                                # Save archival object as Collection if it has children, otherwise save as Object
                                # Tree.execute() is a generator function so we have to loop through the results
                                for p in partial_tree:
                                    if p.get('has_children'):
                                        key = 'collection'
                                        obj = Collection.objects.create(source_tree=p)
                                    else:
                                        key = 'object'
                                        obj = cls.objects.create()
                        # Handle resource records
                        elif d == 'resources':
                            resource_id = data.get('uri').split('/')[-1]
                            with open(os.path.join(source_filepath, 'trees', '{}.json'.format(resource_id))) as tf:
                                tree_data = json.load(tf)
                                obj = cls.objects.create(source_tree=tree_data)
                        # Handle agent and term records
                        else:
                            obj = cls.objects.create()
                        # Create SourceData and Identifier objects
                        SourceData.objects.create(**{key: obj, "source": SourceData.ARCHIVESSPACE, "data": data})
                        Identifier.objects.create(**{key: obj, "source": Identifier.ARCHIVESSPACE, "identifier": data.get('uri')})
                        print("Imported {}".format(data.get('uri')))
                    else:
                        print("Skipped {}".format(data.get('uri')))
        # Handle data from Cartographer
        elif d == 'maps':
            for f in os.listdir(os.path.join(source_filepath, d)):
                # Load arrangement map data
                with open(os.path.join(source_filepath, d, f)) as jf:
                    data = json.load(jf)
                    process_tree_item(data)
