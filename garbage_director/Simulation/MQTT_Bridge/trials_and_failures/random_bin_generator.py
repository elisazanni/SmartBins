import json
from bridge import Bidoni_Handler
from bidone import Bidone
import paho.mqtt.client as mqtt
import configparser

class Random_Publisher():
    def __init__(self):
        self.setupMQTT()
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.virtual_bins = {}
    def setupMQTT(self):
        self.clientMQTT = mqtt.Client()
        self.clientMQTT.on_connect = self.on_connect
        #self.clientMQTT.on_message = self.on_message
        print("connecting to MQTT broker...")
        self.clientMQTT.connect(
            self.config.get("MQTT", "Server"),  # , fallback="localhost"
            self.config.getint("MQTT", "Port", fallback=1883),
            60)
        self.clientMQTT.loop_start()


    def print_bins(self):
        print("\n")
        for item in self.virtual_bins:
            print(f"bridge: {item}")
            for pattume in self.virtual_bins[item].bidoni.keys():
                print(f"\tpattume: {pattume}")
                print(f"\t\t{self.virtual_bins[item].getBidoneDict(pattume)}")
        print("\n")
    def publish_loop(self):
        while 1:
            for bridge_topic in self.virtual_bins.keys():
                bin_handler=self.virtual_bins[bridge_topic]
                for bid in bin_handler.bidoni.keys():
                    bid_dict = bin_handler.getValuesDict(bid)
                    for item in bid_dict.keys():
                        self.clientMQTT.publish(item, bid_dict[item])
                        print(f"published {bid_dict[item]} to {item}")
    def on_connect(self, client, userdata, flags, rc):
        self.clientMQTT.subscribe(f"Pattumi/#")

if __name__=="__main__":
    address=[

    ]
    topic="Pattumi"
    types=[
        "umido",
        "vetro",
        "plastica",
        "carta"
    ]
    esempio=Bidone()
    bin_keys=list(esempio.getAll().keys())

