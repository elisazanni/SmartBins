from .bidone import Bidone
import configparser
import paho.mqtt.client as mqtt
import re


class Bidoni_Handler():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.bidoni = dict()
        self.project_name="pattumi"
    def getBridgeTopic(self):
        bidone_dict = self.bidoni[list(self.bidoni.keys())[0]].getAll()
        return f"{self.project_name}/{bidone_dict['city']}/{bidone_dict['address']}/{bidone_dict['civ']}"

    def getTopics(self):
        return list(self.bidoni.keys())

    def constructTopic(self, bidone_dict):
        try:
            return f"{self.project_name}/{bidone_dict['city']}/{bidone_dict['address']}/{bidone_dict['civ']}/{bidone_dict['type']}"
        except KeyError:
            print("couldn't construct bidone id as needed parameters are missing or undefined")
            return None

    def getValuesDict(self, id):
        return {
            f"{id}/light": self.bidoni[id].light,
            f"{id}/garbage_level": self.bidoni[id].garbage_level,
            f"{id}/battery": self.bidoni[id].battery
        }
    def get_super_complete_garbage_dict(self):
        bin_d = {}
        for bin in self.bidoni.keys():
            bin_d[bin] = self.getBidoneDict(bin)
        return bin_d

    def get_garbage_types(self):
        return list(self.bidoni.keys())
    def get_complete_garbage_dict(self):
        bin_d={}
        for bin in self.bidoni.keys():
            bin_d[bin]=self.getValuesDict(bin)
        return bin_d

    def toggleLight(self, id):
        self.bidoni[id].toggle()

    def getBidone(self, id):
        return self.bidoni[id]

    def getBidoneDict(self, id):
        return self.bidoni[id].getAll()

    def updateBidone(self, bidone_dict=None,id=None):
        if bidone_dict is None:
            return
        if id is None:
              bid = self.constructTopic(bidone_dict)
        else:
            bid=id
        self.bidoni[bid].update(bidone_dict)

    def removeBidone(self, id):
        self.bidoni.pop(id)

    def addBidone(self, bidone_dict,id=None):
        if id is None:
            bid = self.constructTopic(bidone_dict)
        else:
            bid=id
        if bid is None:
            return
        self.bidoni[bid] = Bidone(bidone_dict)
    def check_bidone(self,id):
        return id in self.bidoni.keys()
