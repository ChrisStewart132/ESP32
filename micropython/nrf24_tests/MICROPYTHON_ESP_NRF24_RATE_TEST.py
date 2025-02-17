'''
    Author: Christopher Stewart
    Date: 08022025
    Description: NRF24L01 rpi pico micropython MICROPYTHON_NRF24_DRIVER example program,
 	setup 2 nrf24l01's (cfg0 and cfg1) and test Auto ACK enabled stream data rate
'''
import utime, machine
from MICROPYTHON_NRF24_DRIVER import *

def send_msg(cfg, msg):
    data = b'msg:' + str(msg)
    n = len(data)
    data += (P0_PACKET_SIZE-n) * b'.'
    return nrf24_tx(cfg, data)


BAUDRATE = 8*10**6



# Initialize HSPI 
hspi = SPI(1, baudrate=BAUDRATE, polarity=0, phase=0, bits=8, firstbit=0,
           sck=Pin(14), mosi=Pin(13), miso=Pin(12))  # Example HSPI pins - adjust to your wiring

# Initialize VSPI 
vspi = SPI(2, baudrate=BAUDRATE, polarity=0, phase=0, bits=8, firstbit=0,
           sck=Pin(18), mosi=Pin(23), miso=Pin(19))  # Example VSPI pins - adjust to your wiring

cfg0 = {"spi": hspi, "csn": Pin(26, mode=Pin.OUT, value=1) , "ce": Pin(27, mode=Pin.OUT, value=0)}
cfg1 = {"spi": vspi, "csn": Pin(5, mode=Pin.OUT, value=1) , "ce": Pin(16, mode=Pin.OUT, value=0)}

def main():
    # driver sends and rcvs  on P0 addr, overwrite if needed
    #RX_ADDR_P0_BUFFER = [0x22, 0xaa, 0x88]+[0xc4]*(2*AW_5_BYTES + 1*AW_4_BYTES)#	p0 addr
    print(cfg0)
    nrf24_init(cfg0)
    print(cfg1)
    nrf24_init(cfg1)

    i,j,t0 =0,0,utime.ticks_us()
    while True:
        i+=1

        # blocking send (MAX RT ATTEMPTS) cfg1
        res = send_msg(cfg0, i-j-1)
     
        if not res:# no ACK received so re-transmit
            j+=1
            continue
    
        packet = nrf24_read(cfg1, TIMEOUT=0.1)
        #
        # print
        if (i+j) % 200 == 0:
            seconds=(utime.ticks_us()-t0)/1000000
            data = i*32/1000
            success = (i/(i+j))*100
            print(f"success {success:.2f}%:", f"data: {data:.2f}kB", f"t: {seconds:.2f}s", f"rate: {data/seconds:.2f}kB/s")
            print(packet)
                 
try:
    led = machine.Pin(2, machine.Pin.OUT)
    led.on()
    main()
except KeyboardInterrupt:
    pass
except Exception as e:
    print(e)
finally:
    nrf24_disable(cfg0)
    nrf24_disable(cfg1)
    led.off()




