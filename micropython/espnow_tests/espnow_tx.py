"""
Filename: espnow_tx.py
Description: micropython espnow tx and rx test programs, tx alternates phy_wifi_rate modes sending a stream of data, rx listens and records metrics waiting for the stream of data to end to present the results.
Author: Christopher Stewart
Date: 07/02/2025
"""
import network
import espnow
import time
from sys import exit

############################################################################
# CONFIG #################################################################
peer = b'\xa0\xb7e,\x84\xe8'   # MAC address of peer's wifi interface

""" 
rxbuf: (default=526) Get/set the size in bytes of the internal buffer used to
store incoming ESPNow packet data. The default size is selected to fit two
max-sized ESPNow packets (250 bytes) with associated mac_address (6 bytes),
a message byte count (1 byte) and RSSI data plus buffer overhead. Increase
this if you expect to receive a lot of large packets or expect bursty incoming traffic.
"""
rxbuf = (263)*100

"""
timeout_ms: (default=300,000) Default timeout (in milliseconds) for receiving
ESPNow messages. If timeout_ms is less than zero, then wait forever
The timeout can also be provided as arg to recv()/irecv()/recvinto().
"""
timeout_s = 0.1
timeout_ms = int(timeout_s*10**6)

"""
send(...sync):
    True: (default) send msg to the peer(s) and wait for a response (or not).
    False send msg and return immediately. Responses from the peers will be discarded
"""
sync = False
# CONFIG #################################################################
############################################################################
"""
rate: (ESP32 only, IDF>=4.3.0 only) Set the transmission speed for ESPNow
packets. Must be set to a number from the allowed numeric values in enum wifi_phy_rate_t.
https://docs.espressif.com/projects/esp-idf/en/v4.4.1/esp32/api-reference/network/esp_wifi.html#_CPPv415wifi_phy_rate_t
"""
wifi_phy_rates = {
    "1M_L": 0x00,
    "11M_L": 0x03,
    "2M_S": 0x05,
    "11M_S": 0x07,
    "6M": 0x0B,
    "54M": 0x0C,
    "MCS0_LGI": 0x10,
    "MCS7_LGI": 0x17,
    "MCS0_SGI": 0x18,
    "MCS7_SGI": 0x1F
}
reverse_wifi_phy_rates = {value: key for key, value in wifi_phy_rates.items()}
wifi_phy_rate_iterator = iter(wifi_phy_rates.keys())


sta = None
e = None

def main():
    global sta, e, wifi_phy_rates, reverse_wifi_phy_rates, wifi_phy_rate_iterator
    print("tx test")
    print(f"sending to {peer}")

    # A WLAN interface must be active to send()/recv()
    sta = network.WLAN(network.WLAN.IF_STA)  # Or network.WLAN.IF_AP
    assert sta.active(True) == True

    mac = sta.config('mac')
    print(mac)

    e = espnow.ESPNow()
    e.active(True)
    e.add_peer(peer)      # Must add_peer() before send()
    
    msg = b"x"*250
    packets_sent = 0
    packets_received = 0
    
    while True:
        if packets_sent % 256 == 0:# change wifi_phy_rate
            try:
                rate = wifi_phy_rates[next(wifi_phy_rate_iterator)]
            except StopIteration :
                exit(1)# all wifi_phy_rates iterated, so end test
                wifi_phy_rate_iterator = iter(wifi_phy_rates.keys())
                rate = wifi_phy_rates[next(wifi_phy_rate_iterator)]
            print(f"changing wifi_phy_rate to {reverse_wifi_phy_rates[rate]}")
            e.config(rxbuf=rxbuf, timeout_ms=timeout_ms, rate=rate)
            time.sleep(0.2)
            
        # prepare msg
        data = f"{packets_sent},".encode()
        wifi_phy_rate = reverse_wifi_phy_rates[rate].encode()
        msg = data + msg[len(data):]# insert packets_sent into msg
        msg = msg[:-10] + b"."*10
        msg = msg[:-len(wifi_phy_rate)] + wifi_phy_rate
        
        response = e.send(peer, msg, sync)
        if sync and response:
            packets_received += 1
        packets_sent += 1
              
        if packets_sent % 256 == 0:
            print(f"packets_sent: {packets_sent}, packets_received: {packets_received} success_rate: {packets_received*100/packets_sent} %")
        time.sleep(0.000001)

try:
    main()
except KeyboardInterrupt:  # Explicitly catch Ctrl+C
    print("\nCtrl+C pressed. Exiting...")
except Exception as e:
    print(f"Error: {e}")
finally:
    if e:  # Deactivate ESPNow if initialized
        e.active(False)
        print("ESPNow deactivated")
    if sta:  # Disable WiFi interface
        sta.active(False)
        print("WiFi deactivated") 

