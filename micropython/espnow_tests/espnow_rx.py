"""
Filename: espnow_rx.py
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
timeout_s = 1
timeout_ms = int(timeout_s*10**3)

"""
rate: (ESP32 only, IDF>=4.3.0 only) Set the transmission speed for ESPNow
packets. Must be set to a number from the allowed numeric values in enum wifi_phy_rate_t.
https://docs.espressif.com/projects/esp-idf/en/v4.4.1/esp32/api-reference/network/esp_wifi.html#_CPPv415wifi_phy_rate_t
"""
# CONFIG #################################################################
############################################################################
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
rate = wifi_phy_rates["MCS7_SGI"]

sta = None  # Global reference to WLAN interface
e = None    # Global reference to ESPNow object

def print_results(results):
    if len(results) == 0:
        return
    print("#"*100)
    longest_key = sorted(results.keys())[-1]
    for k,v in results.items():
        delta = len(longest_key) - len(k)
        print(k,"."*delta,v)
    best_rate = sorted(results.keys(), key=lambda x:results[x]["data_rate_kB_s"], reverse=True)[0]
    print("best data rate:", best_rate, results[best_rate]["data_rate_kB_s"], "kB/s")
    best_rssi = sorted(results.keys(), key=lambda x:results[x]["init_RSSI"], reverse=True)[0]
    print("best RSSI:", best_rssi, results[best_rssi]["init_RSSI"])
    print("#"*100)

def main():
    global sta, e, wifi_phy_rates, reverse_wifi_phy_rates, wifi_phy_rate_iterator
    
    # A WLAN interface must be active to send()/recv()
    sta = network.WLAN(network.WLAN.IF_STA)  # Or network.WLAN.IF_AP
    assert sta.active(True) == True
    
    e = espnow.ESPNow()
    e.config(rxbuf=rxbuf, timeout_ms=timeout_ms, rate=rate)
    e.active(True)

    print("rx test")
    print(f"receiving on {sta.config('mac')}")
    print(f"rxbuf: {rxbuf}, timeout_ms: {timeout_ms}, wifi_phy_rate: {reverse_wifi_phy_rates[rate]}")

    results = {}
    while True:
        peer, msg = e.recv()# blocking receive
        
        if msg:
            peer_wifi_phy_rate = msg[-10:].decode().replace("x","")
            if peer_wifi_phy_rate not in results:
                results[peer_wifi_phy_rate] = {"packet_count":0, "total_bytes":0, "start_time_ms":0, "data_rate_kB_s":0, "init_RSSI":e.peers_table[peer][0]}
            results[peer_wifi_phy_rate]["start_time_ms"] = time.ticks_ms() if results[peer_wifi_phy_rate]["start_time_ms"] == 0 else results[peer_wifi_phy_rate]["start_time_ms"]
            results[peer_wifi_phy_rate]["total_bytes"] += len(msg)
            results[peer_wifi_phy_rate]["packet_count"] += 1
            delta_t = time.ticks_ms() - results[peer_wifi_phy_rate]["start_time_ms"]
            if delta_t != 0:
                data_rate_kB_s = (results[peer_wifi_phy_rate]["total_bytes"] / delta_t)
                results[peer_wifi_phy_rate]["data_rate_kB_s"] = data_rate_kB_s
                
        # e.recv timed out
        elif len(results) == 0:
            pass
        else:
            print_results(results)
            exit(0)
            
        
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
