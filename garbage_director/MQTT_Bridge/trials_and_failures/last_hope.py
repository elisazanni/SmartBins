from lib_nrf24 import NRF24
import RPi.GPIO as GPIO
import spidev
import time
GPIO.setmode(GPIO.BCM)
pipes=[[0x02,0x02,0x02,0x02,0x02],[0xF0,0xF0,0xF0,0xF0,0xE1]]
radio=NRF24(GPIO,spidev.SpiDev())
radio.begin(0,17,4000000)
radio.setChannel(76)
radio.setDataRate(NRF24.BR_1MBPS)
radio.setPALevel(NRF24.PA_HIGH)
radio.setAutoAck(True)
radio.enableDynamicPayloads()
radio.enableAckPayload()
#radio.openReadingPipe(1,pipes[1])
radio.openWritingPipe(pipes[0])
radio.printDetails()
radio.startListening()
while True:
    radio.write(b"\x0a")
    time.sleep(0.5)
    radio.write(b"\x0b")
    time.sleep(0.5)
    radio.write(b"\x0c")
    time.sleep(0.5)
"""
while True:
    while not radio.available(0):
        time.sleep(1/100)
    received_m=[]
    radio.read(received_m,radio.getDynamicPayloadSize())
    print(received_m)
    print(str(received_m))
    print(str(bytearray(received_m)))
"""
