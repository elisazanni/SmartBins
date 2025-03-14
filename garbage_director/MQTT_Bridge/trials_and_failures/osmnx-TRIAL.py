import networkx as nx
import osmnx as ox
import folium
ox.config(use_cache=True, log_console=True)
# get a graph
G = ox.graph_from_place('Piedmont, California, USA', network_type='drive')

# impute missing edge speed and add travel times
G = ox.add_edge_speeds(G)
G = ox.add_edge_travel_times(G)

# calculate shortest path minimizing travel time
orig, dest = list(G)[0], list(G)[-1]
print(G)
route = nx.shortest_path(G, orig, dest, 'travel_time')

# create folium web map
route_map = ox.plot_route_folium(G, route)
route_map.show_in_browser()