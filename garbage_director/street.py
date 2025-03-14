import math
from pathlib import Path
import networkx as nx
import osmnx as ox
ox.config(use_cache=True, log_console=True)

class Way():
    def __init__(self, id: int, oneway: bool, nodes: list):
        self.id = id
        self.oneway = oneway
        self.nodes = nodes
        if len(self.nodes) < 2:
            raise Exception("There cannot be a way with less than two nodes")
        if len(self.nodes) > 2:
            self.nodes = [nodes[0], nodes[-1]]

    def __eq__(self, other: 'Way') -> bool:
        return self.id == other.id

    def __iter__(self):
        return iter(self.nodes)

    def __contains__(self, node: int):
        return node in self.nodes

    def __str__(self):
        return f'(Way ID {self.id}: Oneway {self.oneway}, Nodes {self.nodes})'

    def __repr__(self) -> str:
        return self.__str__()


class Node():
    def __init__(self, id, latitude, longitude):
        self.id = id
        self.latitude = latitude
        self.longitude = longitude

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return f'(Node ID: {self.id}: Latitude {self.latitude}, Longitude {self.longitude})'

    def __repr__(self) -> str:
        return self.__str__()

    def distance(self, other):
        R = 6378.137  # Radius of earth in KM
        dLat = other.latitude * math.pi / 180 - self.latitude * math.pi / 180
        dLon = other.longitude * math.pi / 180 - self.longitude * math.pi / 180
        a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(self.latitude * math.pi / 180) * \
            math.cos(other.latitude * math.pi / 180) * \
            math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        d = R * c
        return d * 1000  # Distance in meters
        # return math.sqrt((self.latitude - other.latitude)**2 + (self.longitude - other.longitude)**2)


class Street():
    ################################################################
    """
    must remove all duplicated oneway roads. Once that is done

    0. Define a function that returns the "next node", which is either:
        - A node directly connected using a way
        - The closest non-connected node (which should still be less than 100m away)


    1. Start from a random WAY. Add it to way list.
    2. Use the "next node" function on both nodes. If the leftmost node
    has no next, then it is the start node. If the rightmost node has
    no next, then it is the end node. If one or both have a next, add the
    way to the respective list position.
    """
    ################################################################

    def __init__(self, city: str, name: str):
        self.city = city
        self.name = name
        self.response = ox.downloader.overpass_request(
            '[out:json][timeout:25];' +
            f'area["name"="{city}"]["boundary"="administrative"]["admin_level"="8"] -> .a;' +
            f'way(area.a)["name"="{name}"];' +
            'out;')
        self.ways = []
        self.changes_direction_of_travel = False
        self.__init_lists()
        self.__simplify_nodes()
        self.__build__street()

    @property
    def start_node(self) -> 'Node':
        return self.ways[0].nodes[0]

    @property
    def end_node(self) -> 'Node':
        return self.ways[-1].nodes[-1]

    def __init_nodes(self):
        # This function gets latitude and longitude for each node
        # 1. Find all the unique nodes referenced in the response
        node_ids = set()
        for way in self.response['elements']:
            node_ids = node_ids.union(way['nodes'])

        # 2. Prepare a query that contains all the nodes
        nodes_query = ['[out:json][timeout:25]; (']
        for node_id in node_ids:
            nodes_query.append(f'node({node_id});')
        nodes_query.append('); out;')

        # 3. Query (takes a bit)
        nodes_response = ox.downloader.overpass_request(''.join(nodes_query))

        # 4. Use the info to build Node objects
        nodes = {}
        for node in nodes_response['elements']:
            nodes[node['id']] = Node(node['id'], node['lat'], node['lon'])
        return nodes

    def __init_lists(self):
        if len(self.response['elements']) == 0:
            raise ValueError(f'The requested street {self.name} was not found')

        nodes = self.__init_nodes()

        for way in self.response['elements']:
            if oneway := way['tags'].get('oneway', False) == 'yes':
                oneway = True
            else:
                oneway = False
            n = [nodes[node_id] for node_id in way['nodes']]
            self.ways.append(Way(way['id'], oneway, n))

        # Determine if there are both oneway and twoway sections
        first_direction_of_travel = self.ways[0].oneway
        for way in self.ways:
            if way.oneway != first_direction_of_travel:
                self.changes_direction_of_travel = True
                break

    def __is_duplicate(self, way1, way2):
        for node in way1:
            if node in way2:
                # If there is a twoway section with this node,
                # then way2 is a duplicate.
                for way in self.ways:
                    if way == way1 or way == way2 or way.oneway:
                        continue
                    for node2 in way:
                        if node2 == node:
                            return True
        return False

    def __simplify_nodes(self):
        # We should delete one oneway section if there are two
        # that have a node in common with a twoway road, because
        # it is most likely to be an intersection

        for i, way1 in enumerate(self.ways):
            if not way1.oneway:
                continue
            for j, way2 in enumerate(self.ways[i+1:]):
                if not way2.oneway:
                    continue
                if self.__is_duplicate(way1, way2):
                    way2.id = -1
        self.ways[:] = [w for w in self.ways if w.id != -1]

    def __find_next_way(self, currently_selected_ways):
        # Easy: Search for a way with a node in common with
        # one in the selection's outer elements

        for way in self.ways:
            if way in currently_selected_ways:
                continue
            # Try with the leftmost element
            if way.nodes[0] == currently_selected_ways[0].nodes[0]:
                # We are moving in the other direction! Swap nodes.
                t = way.nodes[0]
                way.nodes[0] = way.nodes[-1]
                way.nodes[-1] = t
                return 'left', way
            if way.nodes[-1] == currently_selected_ways[0].nodes[0]:
                return 'left', way

            # Then try with the rightmost element
            if way.nodes[0] == currently_selected_ways[-1].nodes[-1]:
                return 'right', way
            if way.nodes[-1] == currently_selected_ways[-1].nodes[-1]:
                # We are moving in the other direction! Swap nodes.
                t = way.nodes[0]
                way.nodes[0] = way.nodes[-1]
                way.nodes[-1] = t
                return 'right', way

        # Harder: if no directly connected way is found, search for
        # close-by nodes, by longitude. It will search for the nearest node.
        minimum_from_left = None
        minimum_left_node_id = None
        minimum_left_way_index = None

        minimum_from_right = None
        minimum_right_node_id = None
        minimum_right_way_index = None

        left = currently_selected_ways[0].nodes[0]
        right = currently_selected_ways[-1].nodes[-1]
        for i, way in enumerate(self.ways):
            if way in currently_selected_ways:
                continue
            for node in way.nodes:
                left_distance = left.distance(node)
                right_distance = right.distance(node)
                if minimum_from_left is None or left_distance < minimum_from_left:
                    minimum_from_left = left_distance
                    minimum_left_node_id = node.id
                    minimum_left_way_index = i
                if minimum_from_right is None or right_distance < minimum_from_right:
                    minimum_from_right = right_distance
                    minimum_right_node_id = node.id
                    minimum_right_way_index = i
        direction = None
        candidate = None
        if (minimum_from_left is None or minimum_from_right is None or
            minimum_left_node_id is None or minimum_right_node_id is None or
                minimum_left_way_index is None or minimum_right_way_index is None):
            return direction, candidate

        if minimum_from_left < minimum_from_right:
            if minimum_from_left > 500:
                return None, None
            if self.ways[minimum_left_way_index].nodes[-1].id != minimum_left_node_id:
                # We are moving in the other direction! Swap nodes.
                t = self.ways[minimum_left_way_index].nodes[0]
                self.ways[minimum_left_way_index].nodes[0] = self.ways[minimum_left_way_index].nodes[-1]
                self.ways[minimum_left_way_index].nodes[-1] = t
            direction = 'left'
            candidate = self.ways[minimum_left_way_index]
        else:
            if minimum_from_right > 500:
                return None, None
            if self.ways[minimum_right_way_index].nodes[0].id != minimum_right_node_id:
                # We are moving in the other direction! Swap nodes.
                t = self.ways[minimum_right_way_index].nodes[0]
                self.ways[minimum_right_way_index].nodes[0] = self.ways[minimum_right_way_index].nodes[-1]
                self.ways[minimum_right_way_index].nodes[-1] = t
            direction = 'right'
            candidate = self.ways[minimum_right_way_index]

        return direction, candidate

    def __build__street(self):
        currently_selected_ways = [self.ways[0]]

        while len(currently_selected_ways) < len(self.ways):
            direction, way = self.__find_next_way(currently_selected_ways)
            if direction is None or way is None:
                break
            if direction == 'left':
                currently_selected_ways = [way] + currently_selected_ways
            else:
                currently_selected_ways.append(way)
        self.ways = currently_selected_ways

    def __str__(self) -> str:
        return f"Street({self.city}, {self.name}): Start node {self.start_node}, End node {self.end_node}"

    def __repr__(self) -> str:
        return self.__str__()