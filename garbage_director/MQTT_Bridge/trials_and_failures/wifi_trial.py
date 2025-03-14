import RPi.GPIO as GPIO  # import gpio

import time  # import time library

import spidev

from lib_nrf24 import NRF24 # import NRF24 library

GPIO.setmode(GPIO.BCM)  # set the gpio mode

# set the pipe address. this address shoeld be entered on the receiver alo

pipes = [[0x01, 0x01, 0x01, 0x01, 0x01], [0x01, 0x00, 0x00, 0x00, 0xFF]]

radio = NRF24(GPIO, spidev.SpiDev())  # use the gpio pins

radio.begin(0, 17,4000000)  # start the radio and set the ce,csn pin ce= GPIO08, csn= GPIO25

radio.setPayloadSize(32)  # set the payload size as 32 bytes

radio.setChannel(76)  # set the channel as 76 hex

radio.setDataRate(NRF24.BR_1MBPS)  # set radio data rate

radio.setPALevel(NRF24.PA_HIGH)  # set PA level

radio.setAutoAck(True)  # set acknowledgement as true

radio.enableDynamicPayloads()
radio.openReadingPipe(1,pipes[0])

radio.enableAckPayload()
#radio.openReadingPipe(1,pipes[1])
radio.startListening()
radio.printDetails()  # print basic detals of radio
"""while True:
    radio.write(b"\x14")
    radio.startListening()
    start = time.monotonic()
    received_message = []
    while time.monotonic() - start < 2:
        if radio.available(0):
            radio.read(received_message, radio.getDynamicPayloadSize())
            print(f"Received message: holy fuck non ci credo: {received_message}")
            break
        time.sleep(0.1)
    radio.stopListening()
    time.sleep(0.5)
    radio.write(b"\x1e")
    radio.startListening()
    start = time.monotonic()
    received_message = []
    while time.monotonic() - start < 2:
        if radio.available(0):
            radio.read(received_message, radio.getDynamicPayloadSize())
            print(f"Received message: holy fuck non ci credo: {received_message}")
            break
        time.sleep(0.1)
    radio.stopListening()"""
    #time.sleep(0.5)

#radio.startListening()
"""
while True:
    radio.write(b"\x0b")
    time.sleep(0.1)
    radio.write(b"\x0a")
    time.sleep(0.1)
    radio.write(b"\x0c")
    time.sleep(0.1)
    radio.write(b"\20")
    """


while True:
     # Start listening the radio
    
    while not radio.available(0):

        time.sleep(1 / 100)
    received_message=[]
    radio.read(received_message,radio.getDynamicPayloadSize())
    print(f"Received message: holy fuck non ci credo: {received_message}")

    time.sleep(3)
    print(str(received_message))
