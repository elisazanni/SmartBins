import serial
import serial.tools.list_ports
import configparser
from lib_nrf24 import NRF24
from bridge import Bidoni_Handler

import struct
import spidev
import time
import RPi.GPIO as GPIO
import RPi.GPIO as GPIO  # import gpio

import time  # import time library
from multiprocessing import Process
import multiprocessing as mp
import spidev

from lib_nrf24 import NRF24

light_status_dict = {
    0: b"\x0a",
    1: b"\x0b",
    2: b"\x0c"
}
get_garbage = b"\x14"
get_battery = b"\x1e"


class WiFi_Interface(Process):
    def __init__(self, bin_handler: Bidoni_Handler):
        super().__init__()
        self.bin_handler = bin_handler
        self.pipe_dict = {
            "umido": [0x02, 0x02, 0x02, 0x02, 0x02],
            "vetro": [0x01, 0x00, 0x00, 0x00, 0x02],
            "carta": [0x01, 0x00, 0x00, 0x00, 0x03],
            "plastica": [0x01, 0x00, 0x00, 0x00, 0x04],

        }
        self.radio_address = [0x01, 0x01, 0x01, 0x01, 0x01]
        self.queue = mp.Queue()
        self.return_queue=mp.Queue()
        self.setup("ciao")


    def run(self):
        while 1:
            bin_obj = self.queue.get()
            self.bin_handler.updateBidone(bin_obj[1],bin_obj[0])
            self.update_single_bin(bin_obj[0])

    def get_input(self):
        self.radio.startListening()
        start = time.monotonic()
        received_message = []
        while time.monotonic() - start < 2:
            if self.radio.available(0):
                self.radio.read(received_message, self.radio.getDynamicPayloadSize())
                print(f"Received message: holy fuck non ci credo: {received_message}")
                break
            time.sleep(1 / 100)
        self.radio.stopListening()
        return received_message

    def setup(self, s):
        GPIO.setmode(GPIO.BCM)  # set the gpio mode

        # set the pipe address. this address shoeld be entered on the receiver alo

        radio = NRF24(GPIO, spidev.SpiDev())  # use the gpio pins
        radio.begin(0, 17, 4000000)  # start the radio and set the ce,csn pin ce= GPIO08, csn= GPIO25
        radio.setPayloadSize(32)  # set the payload size as 32 bytes
        radio.setChannel(76)  # set the channel as 76 hex
        radio.setDataRate(NRF24.BR_1MBPS)  # set radio data rate
        radio.setPALevel(NRF24.PA_LOW)  # set PA level
        radio.setAutoAck(True)  # set acknowledgement as true
        radio.enableDynamicPayloads()
        radio.enableAckPayload()
        radio.openReadingPipe(1, self.radio_address)
        radio.printDetails()  # print basic detals of radio
        self.radio = radio


    def update_single_bin(self, bid):
        self.radio.stopListening()
        time.sleep(0.1)
        bin_dict = self.bin_handler.getBidoneDict(bid)
        self.radio.openWritingPipe(self.pipe_dict[bin_dict["type"]])
        self.radio.write(light_status_dict[bin_dict["light"]])
        self.radio.write(get_garbage)
        g_level = self.get_input()
        time.sleep(0.1)
        self.radio.write(get_battery)
        battery = self.get_input()
        if len(g_level) == 0:
            g_level.append(bin_dict["garbage_level"])
        if len(battery) == 0:
            battery.append(bin_dict["battery"])

        self.bin_handler.updateBidone({"garbage_level":g_level[0],
                                       "battery":battery[0]
                                       },bid)
        bin_dict=self.bin_handler.getBidoneDict(bid)
        bin_found = [bid, bin_dict]
        self.return_queue.put(bin_found)
        self.radio.flush_rx()
        self.radio.flush_tx()

    def loop(self):
        for bid in self.bin_handler.bidoni.keys():
            bin_dict = self.bin_handler.getBidoneDict(bid)
            light = bin_dict["light"]
            type = bin_dict[f"type"]
            print(f"evaluating bin {bid} of address {self.pipe_dict[type]}")
            self.radio.stopListening()
            self.radio.openWritingPipe(self.pipe_dict[type])
            self.radio.write(light_status_dict[light])
            self.radio.write(get_garbage)
            garbage_level = self.get_input()
            print(f"garbage level: {garbage_level}")
            time.sleep(0.5)
            self.radio.write(get_battery)
            battery = self.get_input()
            print(f"battery: {battery}")
            if len(garbage_level) == 0:
                garbage_level.append(bin_dict["garbage_level"])
            if len(battery) == 0:
                battery.append(bin_dict["battery"])

            dict = {
                "garbage_level": garbage_level[0],
                "battery": battery[0]
            }
            print(dict)
            self.bin_handler.updateBidone(dict, bid)
            self.radio.flush_rx()
            time.sleep(1)

    def getBidone(self, id):
        pass

    def setLight(self, id):
        pass
