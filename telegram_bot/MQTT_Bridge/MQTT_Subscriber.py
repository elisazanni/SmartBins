
import configparser
from .bridge import Bidoni_Handler
import paho.mqtt.client as mqtt
import time
import statistics
from threading import Thread
# constants
RED_LIGHT = 2
GREEN_LIGHT = 1
LIGHT_OFF = 0


class MQTT_Subscriber():
    def __init__(self, observed_topic):
        self.topic = observed_topic
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.virtual_bins = {}
        self.setupMQTT()


    def get_bins(self):
        return self.virtual_bins

    def print_bins(self):

        for item in self.virtual_bins:
            print(f"bridge: {item}")
            for pattume in self.virtual_bins[item].bidoni.keys():
                print(f"\tpattume: {pattume}")
                print(f"\t\t{self.virtual_bins[item].getBidoneDict(pattume)}")

    def set_light(self, light_value, bin_id):
        print(bin_id)
        bin_id_list=bin_id.split("/")
        bridge_id=str("/").join([bin_id_list[i] for i in range(0,4)])
        print(self.virtual_bins[bridge_id])
        self.virtual_bins[bridge_id].updateBidone({"wanted_light":light_value,"light":light_value},bin_id)
        self.clientMQTT.publish(bin_id + "/set_light", payload=light_value)

    def set_address_light(self, light_value, address, city):
        for item in self.virtual_bins:
            item_list = item.split("/")
            if item_list[2] == address and item_list[1]==city:
                print(f"found pattume at address {item_list[2]}")
                for pattume in self.virtual_bins[item].bidoni.keys():
                    self.set_light(light_value, pattume)
                    print(f"\tsetting light to {light_value} for pattume: {pattume}")

    def update_bin(self, bin_id):
        self.clientMQTT.publish(bin_id + "/update", payload="the connection is so unspeakably shitty you're having a "
                                                            "hard time even holding it")

    def update_all(self):
        for item in self.virtual_bins:
            print(f"bridge: {item}")
            for pattume in self.virtual_bins[item].bidoni.keys():
                print(pattume)
                self.update_bin(pattume)

    def garbage_median(self):
        address_dic = {}
        for item in self.virtual_bins:
            item_list = item.split("/")
            address = item_list[2]
            city=item_list[1]
            if city not in list(address_dic.keys()):
                address_dic[city]={}
            if address not in list(address_dic[city].keys()):
                address_dic[city][address] = {}
            for pattume in self.virtual_bins[item].bidoni.keys():
                big_dic = self.virtual_bins[item].getBidoneDict(pattume)
                pattume_list = pattume.split("/")
                bin_type = pattume_list[4]
                if bin_type not in list(address_dic[city][address].keys()):
                    address_dic[city][address][bin_type] = []
                address_dic[city][address][bin_type].append(big_dic["garbage_level"])
        for city in address_dic.keys():
            for address in address_dic[city].keys():
                for g_type in address_dic[city][address].keys():
                    address_dic[city][address][g_type] = statistics.median(address_dic[city][address][g_type])

        return address_dic
    def empty_bin(self,pattume):
        self.clientMQTT.publish(f"{pattume}/empty_bin",0)
    def empty_address_bins(self,address,city,g_type):
        for item in self.virtual_bins.keys():
            item_list = item.split("/")
            if item_list[2] == address and item_list[1] == city :
                print(f"found pattume at address {item_list[2]}")
                for pattume in self.virtual_bins[item].bidoni.keys():
                    pattume_list=pattume.split("/")
                    if pattume_list[4]==g_type:
                        self.empty_bin(pattume)
    def setupMQTT(self):
        self.clientMQTT = mqtt.Client()
        self.clientMQTT.on_connect = self.on_connect
        self.clientMQTT.on_message = self.on_message
        print("Connecting to MQTT broker...")
        self.clientMQTT.connect(
            self.config.get("MQTT", "Server"),  # , fallback="localhost"
            self.config.getint("MQTT", "Port", fallback=1883),
            60)
        self.clientMQTT.loop_start()
        self.publish_thread=Thread(target=self.loop,daemon=True)
        self.publish_thread.start()
        print("Successfully connected!")


    def loop(self):
        while 1:
            time.sleep(1)
            for bridge_id in self.virtual_bins.keys():
                bin_handler=self.virtual_bins[bridge_id]
                garbage_dict=bin_handler.get_super_complete_garbage_dict()
                for bin_id in garbage_dict.keys():
                    if garbage_dict[bin_id]["wanted_light"]!=garbage_dict[bin_id]["light"] \
                            and garbage_dict[bin_id]["wanted_light"] is not None:
                        self.clientMQTT.publish(bin_id + "/set_light", payload=garbage_dict[bin_id]["wanted_light"])

    def on_connect(self, client, userdata, flags, rc):
        self.clientMQTT.subscribe(f"{self.topic}/#")

    def on_message(self, client, userdata, msg):
        #print("received message from: " + msg.topic + " : " + str(msg.payload))
        topic_list = list(msg.topic.split("/"))
        item = topic_list[5]
        typ = topic_list[4]
        key = f"{topic_list[0]}/{topic_list[1]}/{topic_list[2]}/{topic_list[3]}"

        if item == "garbage_level":
            try:
                payload = int(msg.payload)
            except ValueError:
                payload = None
        elif item == "light":
            try:
                payload = int(msg.payload)
                if payload not in [0, 1, 2]:
                    payload = 0
            except ValueError:
                payload = 0
        elif item == "battery":
            try:
                payload = int(msg.payload)
            except ValueError:
                payload = None
        else:
            payload = str(msg.payload)
        update_dict = {item: payload,
                       'type': typ,
                       'address': topic_list[2],
                       'city': topic_list[1],
                       'civ': topic_list[3]}

        if key in self.virtual_bins.keys():
            if self.virtual_bins[key].check_bidone(f"{key}/{typ}"):
                self.virtual_bins[key].updateBidone(update_dict, f"{key}/{typ}")
            else:
                self.virtual_bins[key].addBidone(update_dict, f"{key}/{typ}")
        else:
            self.virtual_bins[key] = Bidoni_Handler()
            self.virtual_bins[key].addBidone(update_dict, f"{key}/{typ}")


if __name__ == '__main__':
    sub = MQTT_Subscriber("pattumi")
    bins = sub.get_bins()
    counter=0
    while 1:
        time.sleep(5)
        sub.print_bins()
        if counter == 5:
            sub.set_address_light(GREEN_LIGHT,"Viale Vittorio Veneto","Modena")
        counter+=1


