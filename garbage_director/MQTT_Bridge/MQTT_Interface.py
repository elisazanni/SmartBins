
import serial
import serial.tools.list_ports
import multiprocessing as mp
import configparser
from bridge import Bidoni_Handler
import paho.mqtt.client as mqtt
import time
from WiFi_Interface import WiFi_Interface
class MQTT_Publisher():
    def __init__(self,bin_handler:'Bidoni_Handler'):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.bin_handler=bin_handler
        self.connector=WiFi_Interface(bin_handler)
        self.connector.daemon=True
        self.connector.start()
    def setupMQTT(self):
        self.clientMQTT = mqtt.Client()
        self.clientMQTT.on_connect = self.on_connect
        self.clientMQTT.on_message = self.on_message
        print("connecting to MQTT broker...")
        self.clientMQTT.connect(
            self.config.get("MQTT", "Server"),
            self.config.getint("MQTT", "Port", fallback=1883),
            60)

        self.clientMQTT.loop_start()
        self.loop()
    def loop(self):
        counter=0
        while 1:
            if counter==0:
                for bid in self.bin_handler.getTopics():
                    self.connector.queue.put([bid,self.bin_handler.getBidoneDict(bid)])
                    bind_found=self.connector.return_queue.get()
                    print(bind_found)
                    self.bin_handler.updateBidone(bind_found[1],bind_found[0])
            counter+=1
            if counter==10:
                counter=0
            topics=self.bin_handler.getTopics()
            print(topics)
            for bid in topics:
                bid_dict=self.bin_handler.getValuesDict(bid)
                for item in bid_dict.keys():
                    self.clientMQTT.publish(item,bid_dict[item])
                    print(f"published {bid_dict[item]} to {item}")
            time.sleep(5)

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        topics=self.bin_handler.getTopics()
        print(f"subscribing to {self.bin_handler.getBridgeTopic()}/+/set_light")
        self.clientMQTT.subscribe(f"{self.bin_handler.getBridgeTopic()}/+/set_light")
        print(f"subscribing to {self.bin_handler.getBridgeTopic()}/+/update")
        self.clientMQTT.subscribe(f"{self.bin_handler.getBridgeTopic()}/+/update")
        #TODO: access info from client and subscribe to correct bidone id

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        print("received message from: "+msg.topic + " " + str(msg.payload))
        topic_list=list(msg.topic.split("/"))
        item=topic_list.pop(len(topic_list)-1)
        if item=="update":
            topic = "/".join(topic_list)
            self.connector.queue.put([topic, self.bin_handler.getBidoneDict(topic)])
            bin_found = self.connector.return_queue.get()
            self.bin_handler.updateBidone(bin_found[1], bin_found[0])
        if item=="toggle":
            topic="/".join(topic_list)
            self.bin_handler.toggleLight(topic)
            self.connector.queue.put(topic)
        if item=="set_light":
            topic = "/".join(topic_list)
            self.bin_handler.updateBidone({"light":int(msg.payload)},topic)
            self.connector.queue.put([topic,self.bin_handler.getBidoneDict(topic)])
            bin_found=self.connector.return_queue.get()
            self.bin_handler.updateBidone(bin_found[1], bin_found[0])


if __name__ == '__main__':
    b=Bidoni_Handler()

    bidone_trial1={
        "type" : "umido",
        "address" : "address1",
        "city" : "Modena",
        "civ" : "1",
    }
    bidone_trial2 = {
        "type": "vetro",
        "address": "address1",
        "sensor_value":6.0,
        "city": "Modena",
        "civ": "1",
    }
    b.addBidone(bidone_trial1)
    b.addBidone(bidone_trial2)
    print(b.getTopics())
    pub=MQTT_Publisher(b)
    pub.setupMQTT()
    """sub=mqtt.Client()
    sub.connect("broker.hivemq.com")
    sub.subscribe("4567/address1/1/umido/sensor_value")


    def on_mess(client, userdata, message):
        print("received message: ", str(message))

    sub.on_message=on_mess
    sub.loop_start()
    time.sleep(20)
    sub.loop_stop()"""

