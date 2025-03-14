import threading

from MQTT_Interface_simulation import MQTT_Publisher
from MQTT_Bridge.bridge import Bidoni_Handler
import json
import random
from threading import Thread
import time
import random

def select_random_bridges(bin_dict):
    k=random.randint(0,len(list(bin_dict.keys())))
    chosen=random.sample(list(bin_dict.keys()),k=k)
    return chosen

def select_random_bins(bin_dict,bridge_id):
    bins_dict=bin_dict[bridge_id]
    k = random.randint(0, len(list(bins_dict.keys())))
    bin_ids = random.sample(list(bins_dict.keys()), k=k)
    return bin_ids

def update_random_bins(bin_dict,publisher_dict):
    chosen=select_random_bridges(bin_dict)
    print(chosen)
    for bridge_id in chosen:
        chosen_types=select_random_bins(bin_dict,bridge_id)
        print(bridge_id)
        print(chosen_types)
        for bin_id in chosen_types:
            update_g_level(publisher_dict,bin_id,bridge_id)
            #TODO add distributed garbage value to be added to bin

def update_g_level(publisher_dict,bin_id,bridge_id):
    single_bin_dic = publisher_dict[bridge_id].bin_handler.getBidoneDict(bin_id)
    g_level = single_bin_dic["garbage_level"]
    publisher_dict[bridge_id].bin_handler.updateBidone(
        {"garbage_level": min([int(g_level + max([0,random.normalvariate(10, 5)])), 100])}, bin_id)

def instantiate_simulation(bin_dict):
    publisher_dict={}
    for bridge_id in bin_dict.keys():
        bin_handler = Bidoni_Handler()
        for bin_id in bin_dict[bridge_id].keys():
            bin_handler.addBidone(bin_dict[bridge_id][bin_id], bin_id)
        pub=MQTT_Publisher(bin_handler)
        publisher_dict[bridge_id] = pub
    return publisher_dict

def update_values_thread(publisher_dict,bin_dict):
    while 1:
        time.sleep(random.randint(1,10))
        update_random_bins(bin_dict,publisher_dict)

if __name__=="__main__":
    with open("dynamic_bin_dic.json") as f:
        b_dict = json.load(f)
    pub_dict=instantiate_simulation(b_dict)
    time.sleep(5)
    t=threading.Thread(target=update_values_thread,args=(pub_dict, b_dict),daemon=True)
    t.start()
    while 1:
        time.sleep(10)


