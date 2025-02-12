import machine
import time

sleep_duration_ms = 50
uart_baudrate = 115200
spi_baudrate = 1*10**6

# Safe GPIO pins to test
safe_gpio_pins = [
    0, 2, 4, 5, 12, 13, 14, 15,
    16, 17, 18, 19, 21, 22, 23,
    25, 26, 27, 32, 33, 34, 35, 36, 39
]

def test_gpio():
    """Test GPIO pins"""
    global safe_gpio_pins
    for pin_num in safe_gpio_pins:  
        try:
            pin = machine.Pin(pin_num, machine.Pin.OUT)  
            pin.on()
            time.sleep_ms(sleep_duration_ms)  
            pin.off()
            #print(f"GPIO{pin_num} test successful")
        except ValueError: 
            print(f"GPIO{pin_num} not available or reserved")
        except Exception as e:  
            print(f"An error occurred with GPIO{pin_num}: {e}")

def test_uart(id):
    """Test UART"""
    # Test UART0
    uart = machine.UART(id, uart_baudrate)
    uart.write(b"Hello, UART")
    time.sleep_ms(sleep_duration_ms)
    if uart.read() == b"Hello, UART":
        print("UART",id,"test successful")
    else:
        print("UART",id,"test failed")
    uart.deinit()

def test_spi(id, hardware=True):
    """Test SPI loopback by ID."""
    sck=machine.Pin(14)
    mosi=machine.Pin(13)
    miso=machine.Pin(12)
    cs = machine.Pin(18, machine.Pin.OUT)  # Add a Chip Select pin
    if id == 2:
        sck=machine.Pin(18)
        mosi=machine.Pin(23)
        miso=machine.Pin(19)
        cs = machine.Pin(23, machine.Pin.OUT)  # Add a Chip Select pin
        
    try:
        spi = machine.SPI(id, baudrate=spi_baudrate) if hardware else machine.SoftSPI(baudrate=spi_baudrate, sck=sck, mosi=mosi, miso=miso)
        test_data = b"Hello, SPI " + str(id).encode() + b"!"
        cs.value(0)  # Activate the "slave" (loopback) - Important!
        spi.write(test_data)
        received_data = spi.read(len(test_data)) # Read the same amount of data sent
        cs.value(1)  # Deactivate the "slave"
        if received_data == test_data:
            print(f"SPI {id} test successful")
        else:
            print(f"SPI {id} test failed. Sent: {test_data}, Received: {received_data}")
        spi.deinit()
    except Exception as e:
        print(f"Error testing SPI {id}: {e}")

def main():
    while True:
        test_gpio()
        time.sleep_ms(1000)  
        #test_uart(2)
        time.sleep_ms(1000)
        test_spi(2, True)

if __name__ == "__main__":
    main()


