import re

from fetcher.helpers import instantiate_aspace, list_chunks
from pisces import settings


class MissingArchivalObjectError(Exception):
    pass


def indicator_to_integer(indicator):
    """Converts an instance indicator to an integer.

    An indicator can be an integer (23) a combination of integers and letters (23b)
    or just letters (B, Be). In cases where indicator data only consists of letters,
    the function will return an integer based on the ordinal value of the lowercased
    first letter in the indicator.
    """
    try:
        integer = int(indicator)
    except ValueError:
        parsed = re.sub("[^0-9]", "", indicator)
        if len(parsed):
            return indicator_to_integer(parsed)
        integer = ord(indicator[0].lower()) - 97
    return integer


def get_ancestors(obj):
    """Returns the full resolved record for each ancestor."""
    for a in obj["ancestors"]:
        yield a["_resolved"]


def closest_parent_value(obj, key):
    """Iterates upwards through a hierarchy and returns the first match for a key.

    Iterates up through an archival object's ancestors and returns the first
    value which matches a given key."""
    for ancestor in get_ancestors(obj):
        if ancestor.get(key) not in ['', [], {}, None]:
            return ancestor[key]


def closest_creators(obj):
    """Iterates upwards through a hierarchy and returns the first creator.

    Iterates up through an archival object's ancestors looking for linked agents,
    then iterates over the linked agents to see if it contains an agent with
    the role of creator. Returns the first creator it finds."""
    for ancestor in get_ancestors(obj):
        if len([c for c in ancestor.get("linked_agents") if c.get("role") == "creator"]):
            return [c for c in ancestor.get("linked_agents") if c.get("role") == "creator"]
    return []


def get_date_string(dates):
    date_strings = []
    for date in dates:
        if date.get("expression"):
            date_strings.append(date["expression"])
        elif date.get("end"):
            date_strings.append("{}-{}".format(date["begin"], date["end"]))
        else:
            date_strings.append(date["begin"])
    return ", ".join(date_strings)


def combine_references(object):
    """Adds type and title fields to references, then removes unneeded resolved objects."""
    for key in ["ancestors", "children", "subjects", "linked_agents"]:
        for obj in object.get(key, []):
            if obj.get("_resolved"):
                type = "collection"
                if key == "subjects":
                    type = obj["_resolved"]["terms"][0]["term_type"]
                elif key == "linked_agents":
                    type = obj["_resolved"]["agent_type"]
                if obj["_resolved"].get("subjects"):
                    obj["subjects"] = combine_references(obj["_resolved"])["subjects"]
                obj["type"] = type
                obj["title"] = obj["_resolved"].get("title", obj["_resolved"].get("display_string"))
                obj["dates"] = get_date_string(obj["_resolved"].get("dates", []))
                del obj["_resolved"]
    return object


def add_group(object, aspace_client):
    """Adds group object, with data about the highest-level collection containing this object."""

    top_ancestor = object
    if object.get("ancestors"):
        last_ancestor = object["ancestors"][-1]
        top_ancestor = last_ancestor["_resolved"] if last_ancestor.get("_resolved") else aspace_client.get(
            last_ancestor.get("archivesspace_uri", last_ancestor.get("ref")),
            params={"resolve": ["linked_agents", "subjects"]}).json()

    group_obj = combine_references(top_ancestor)

    creators = [a for a in group_obj.get("linked_agents", []) if a["role"] == "creator"]
    if object["jsonmodel_type"].startswith("agent_"):
        creators = [{"ref": object["uri"], "role": "creator", "type": object["jsonmodel_type"], "title": object["title"]}]

    object["group"] = {
        "identifier": group_obj.get("ref", group_obj.get("uri")),
        "creators": creators,
        "dates": group_obj.get("dates", group_obj.get("dates_of_existence", [])),
        "title": group_obj.get("title"),
    }
    return object


def handle_cartographer_reference(reference):
    if self.cartographer_client:
      reference["ref"] = reference["archivesspace_uri"]
      reference["type"] = "collection"
      del reference["archivesspace_uri"]
      return reference


class ArchivesSpaceHelper:
    def __init__(self, aspace):
        self.aspace = aspace if aspace else instantiate_aspace(settings.ARCHIVESSPACE)

    def has_children(self, uri):
        """Checks whether an archival object has children using the tree/node endpoint.
        Checks the child_count attribute and if the value is greater than 0, return true, otherwise return False."""
        resp = self.aspace.client.get(uri)
        if resp.status_code == 404:
            raise MissingArchivalObjectError("{} cannot be found".format(uri))
        obj = resp.json()
        resource_uri = obj['resource']['ref']
        tree_node = self.aspace.client.get(f"{resource_uri}/tree/node?node_uri={obj['uri']}").json()
        return True if tree_node['child_count'] > 0 else False

    def tree_root(self, resource_uri):
        """Gets a resource tree starting at the root."""
        return self.aspace.client.get(f"{resource_uri}/tree/root").json()

    def tree_node(self, resource_uri, node_uri):
        """Gets a resource tree starting at a node."""
        return self.aspace.client.get(f"{resource_uri}/tree/node?node_uri={node_uri}").json()

    def objects_within(self, uri_list):
        """Gets the number of objects which have a URI in their ancestors array."""
        count = 0
        for chunk in list_chunks(uri_list, 190):
            search_uri = f"search?q={{!terms f=ancestors}}{','.join(chunk)} AND publish:true&page=1&fields[]=uri&type[]=archival_object&page_size=1"
            result = self.aspace.client.get(search_uri)
            try:
                data = result.json()
                count += data["total_hits"]
            except Exception as e:
                raise Exception(f"Error fetching child counts for URI {result.url}: {e}")
        return count

    def objects_before(self, target_node, initial_node, resource_uri, parent_uri=None):
        """Gets a count of previous archival objects in a resource."""
        count = 0
        target_position = target_node["position"] if ("position" in target_node) else target_node["_resolved"]["position"]
        for offset in range(initial_node["waypoints"]):
            results_url = (f"{resource_uri}/tree/waypoint?offset={offset}&parent_node={parent_uri}" if parent_uri else
                           f"{resource_uri}/tree/waypoint?offset={offset}")
            results_page = self.aspace.client.get(results_url).json()
            if target_position < ((offset + 1) * initial_node["waypoint_size"]):
                previous_results = [r for r in results_page if r["position"] < target_position]
                count += sum([self.objects_within([p["uri"] for p in previous_results]), len(previous_results)])
                count += 1
                return count
            count += sum([self.objects_within([r["uri"] for r in results_page]), len(results_page)])
            count += 1
        return count
