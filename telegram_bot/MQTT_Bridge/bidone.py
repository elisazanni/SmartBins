"""
{
    type="umido"
    light=True
    sensor_value=5
    id="12345"
    address="address1"
    City="Modena"
    civ="1"

}
"""


class Bidone():
    def __init__(self, bidone_dict: dict=None):
        self.type = None
        self.light = 0
        self.garbage_level = 0
        self.address = None
        self.city = None
        self.civ = None
        if bidone_dict is not None:
            self.update(bidone_dict)
        self.wanted_light=None
        self.battery=None
    def setLight(self, status=False):
        self.light = status
    def setBattery(self,battery):
        self.battery=battery
    def getAddress(self):
        return self.address

    def getType(self):
        return self.type

    def toggle(self):
        self.light = not self.light

    def getValue(self):
        return self.garbage_level

    def getAll(self):
        return {name: self.__dict__[name] for name in self.__dict__.keys()}

    def update(self, update_dict: dict):
        for attribute in update_dict:
            if attribute in self.__dict__:
                self.__dict__[attribute] = update_dict[attribute]
