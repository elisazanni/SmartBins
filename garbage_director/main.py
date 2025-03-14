import asyncio
import json
import time
import osmnx as ox
from street import Street, Node
from MQTT_Bridge.MQTT_Subscriber import MQTT_Subscriber
from telegram import Bot

CITY = 'Modena'
CITY_RADIUS = 15000
STARTING_NODE = Node(435435864, 44.6673004, 10.9769295)
MQTT_TOPIC = f'pattumi/{CITY}'
GARBAGE_THRESHOLD = 60

class GarbageDirector():

    def __init__(self, mqtt_topic: str, city: str , center_address: str, garbage_threshold: int, city_radius = 15000):
        self.mqtt_topic = mqtt_topic
        self.city = city
        self.center_address = center_address
        self.garbage_threshold = garbage_threshold
        self.channel = MQTT_Subscriber(self.mqtt_topic)
        self.addresses_list = []
        self.streets = []
        self.__init__addresses()
        self.city_graph = ox.graph_from_address(f'{center_address}, {self.city}',
                          dist=city_radius)  # , network_type="drive")
        self.city_graph = ox.add_edge_speeds(self.city_graph)
        self.city_graph = ox.add_edge_travel_times(self.city_graph)

    def __init__addresses(self):
        while self.channel.garbage_median() == {}:
            time.sleep(10)
        self.median = self.channel.garbage_median()
        self.addresses_list = [address for address in self.median[self.city].keys()]
        for address in self.addresses_list:
            # TODO: cache streets to a file.
            try:
                self.streets.append(Street(CITY, address))
            except ValueError as e:
                print(e)
                print("The software will keep working")
        # Order the list based on the distance to the garbage collection center
        # self.streets.sort(key=lambda s: s.start_node.distance(STARTING_NODE))
        print(self.streets)

    async def send_notification(self, chat_id, light_state, garbage_type, street):
        bot = Bot('6243331827:AAFlZgbqd6EGnRZE-d99zM9PQjI0-i2wcXk')
        if light_state:
            text = f"Il passaggio per la raccolta {garbage_type} in {street} è confermato."
        else:
            text = f"Il passaggio per la raccolta {garbage_type} in {street} è annullato."
        try:
            async with bot:
                await bot.send_message(text=text, chat_id=chat_id)
        except:
            pass
        
    def compute_collection_path(self, garbage_type: str, path_str=None) -> bool:
        # Update all information
        self.channel.update_all()
        while self.channel.garbage_median() == {}:
            time.sleep(5)
        self.median = self.channel.garbage_median()
        print(self.median)
        # Build the list of streets that require collection
        needing_streets_names = [address for address, value in self.median[self.city].items() if value[garbage_type] >= self.garbage_threshold]
        needing_streets = [street for street in self.streets if street.name in needing_streets_names]
        if len(needing_streets) == 0:
            print('No streets need collection')
            return False
        print(needing_streets)
        solution = []
        solution.append(min(needing_streets, key=lambda s: STARTING_NODE.distance(s.start_node)))
        needing_streets.remove(solution[0])

        while len(needing_streets) > 0:
            solution.append(min(needing_streets, key=lambda s: solution[-1].end_node.distance(s.start_node)))
            needing_streets.remove(solution[-1])

        try:
            with open("chats.json") as f:
                chats = json.load(f)
        except:
            chats = None

        for street in self.streets:
            if street in solution:
                self.channel.set_address_light(1, street.name, self.city)
                self.channel.empty_address_bins(street.name, self.city, garbage_type)
                if chats is not None:
                    for chat_id, address in chats.items():
                        if isinstance(address[1], str) and address[1].upper() == street.name.upper():
                            asyncio.run(self.send_notification(chat_id, True, garbage_type, street.name))
            else:
                self.channel.set_address_light(2, street.name, self.city)
                if chats is not None:
                    for chat_id, address in chats.items():
                        if isinstance(address[1], str) and address[1].upper() == street.name.upper():
                            asyncio.run(self.send_notification(chat_id, False, garbage_type, street.name))

        print(f'CORRECT STREET ORDER: {solution}')
        start_node = ox.distance.nearest_nodes(
            self.city_graph, STARTING_NODE.longitude, STARTING_NODE.latitude)

        routes = []
        first_street_node = ox.distance.nearest_nodes(self.city_graph,
             solution[0].start_node.longitude,
             solution[0].start_node.latitude)
        routes.append(ox.distance.shortest_path(self.city_graph,
             start_node, first_street_node, 
             'travel_time', cpus=None))
        while len(solution) > 0:
            first = ox.distance.nearest_nodes(self.city_graph, 
                solution[0].start_node.longitude,
                solution[0].start_node.latitude)
            last = ox.distance.nearest_nodes(self.city_graph, 
                solution[0].end_node.longitude,
                solution[0].end_node.latitude)
            routes.append(ox.distance.shortest_path(self.city_graph,
                first, last, 
                'travel_time', cpus=None))
            if len(solution) > 1:
                first = last
                last = ox.distance.nearest_nodes(self.city_graph, 
                    solution[1].start_node.longitude,
                    solution[1].start_node.latitude)
                routes.append(ox.distance.shortest_path(self.city_graph,
                    first, last, 
                    'travel_time', cpus=None))
            solution.remove(solution[0])
        
        route_map = ox.plot_route_folium(self.city_graph, routes[0])
        for i, route in enumerate(routes[1:]):
            try:
                if i % 2 == 0:
                    color = '#f88432'
                else:
                    color = '#3284f8'
                route_map = ox.plot_route_folium(self.city_graph, route, route_map=route_map,  color=color)
            except ValueError:
                continue
        if path_str is not None:
            route_map.save(path_str)
        else:
            route_map.save(f'garbage_map_{garbage_type}.html')
        return True
        
if __name__ == '__main__':
    while True:
        try:
            gd = GarbageDirector(MQTT_TOPIC, CITY, 'Via Enrico Caruso 150', GARBAGE_THRESHOLD, city_radius=CITY_RADIUS)
            gd.compute_collection_path('vetro', '../website/static/test.html')
            time.sleep(90)
        except KeyboardInterrupt:
            break



# Il mercoledì
"""
garbage_types = ['carta', 'plastica e lattine', 'umido', 'vetro', 'indifferenziato']
if day == mercoledì and hour == 23:
    gd.compute_collection_path('carta')
    for type in garbage_types:
        if type != 'carta':
            self.channel.set_light(0, f"pattumi/{self.city}/{street.name}/+/{type}")

"""
