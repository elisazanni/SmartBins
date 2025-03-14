from pyrf24 import RF24, RF24_PA_LOW
import struct
import spidev
import time
import sys
import argparse

# using the python keyword global is bad practice. Instead we'll use a 1 item
# list to store our float number for the payloads sent
radio = RF24(22, 0)

# using the python keyword global is bad practice. Instead we'll use a 1 item
# list to store our float number for the payloads sent
payload = []

# For this example, we will use different addresses
# An address need to be a buffer protocol object (bytearray)
address = {"send":b"\xE0\xE0\xF1\xF1\xE1", "receive":b"\xE0\xE0\xF1\xF1\xE0"}
# It is very helpful to think of an address as a path instead of as
# an identifying device destination

# to use different addresses on a pair of radios, we need a variable to
# uniquely identify which address this radio will use to transmit
# 0 uses address[0] to transmit, 1 uses address[1] to transmit


# initialize the nRF24L01 on the spi bus
if not radio.begin():
    raise OSError("nRF24L01 hardware isn't responding")

# set the Power Amplifier level to -12 dBm since this test example is
# usually run with nRF24L01 transceivers in close proximity of each other
radio.set_pa_level(RF24_PA_LOW)  # RF24_PA_MAX is default

# set TX address of RX node into the TX pipe
radio.open_tx_pipe(address["send"])  # always uses pipe 0

# set RX address of TX node into an RX pipe
radio.open_rx_pipe(1, address["receive"])  # using pipe 1

# To save time during transmission, we'll set the payload size to be only what
# we need. A float value occupies 4 bytes in memory using struct.calcsize()
# "<f" means a little endian unsigned float
radio.payload_size = 1

# for debugging
radio.print_details()




def slave(timeout: int = 6):
    """Polls the radio and prints the received value. This method expires
    after 6 seconds of no received transmission."""
    radio.listen = True  # put radio into RX mode and power up

    start = time.monotonic()
    while 1:
        has_payload, pipe_number = radio.available_pipe()
        if has_payload:
            length = radio.payload_size  # grab the payload length
            # fetch 1 payload from RX FIFO
            received = radio.read(length)  # also clears radio.irq_dr status flag
            # expecting a little endian float, thus the format string "<f"
            # received[:4] truncates padded 0s in case dynamic payloads are disabled
            payload[0] = struct.unpack("<c", received)[0]
            # print details about the received packet
            print(f"Received {length} bytes on pipe {pipe_number}: {payload[0]}")
            start = time.monotonic()  # reset the timeout timer

    # recommended behavior is to keep in TX mode while idle


if __name__ == "__main__":
    slave()