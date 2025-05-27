# Import necessary modules
from machine import Pin, ADC
import time

# Initialise heart sensor and potentiometer ADCs
heart_sensor = ADC(26)      # GP26 = ADC0
potentiometer = ADC(27)     # GP27 = ADC1

# Initialise digital inputs for L0+ and L0-
L0_plus = Pin(10, Pin.IN)   # GP10 for L0+
L0_minus = Pin(11, Pin.IN)  # GP11 for L0-

# Initialise LED pin as an output
led = Pin(20, Pin.OUT)

# Initialise three variables for moving window
value_1 = 0
value_2 = 0
value_3 = 0


while True:
    # Check if any lead is off
    if L0_plus.value() == 1 or L0_minus.value() == 1:
        print("Lead off detected! Check ECG electrodes")
        led.off()
    else:
        # Shift the variables
        value_1 = value_2
        value_2 = value_3
        value_3 = heart_sensor.read_u16()

    # Read the signal from the heart monitor and potentiometer as u16

        potentiometer_reading = potentiometer.read_u16()

# Compare readings to control LED
if value_3 > potentiometer_reading:
    led.on()

else:
    led.off()

# Peak detection
if value_2 > peak_threshold and value_2 > value_1 and value_2 > value_3:
    now = time.ticks_ms()
    time_since_last = time.ticks_diff(now, last_peak_time)

if time_since_last > min_interval:
    last_peak_time = now
    bpm = int(60000 / time_since_last)
    print(" ❤️ Beat detected!")

if heart_reading > 100:
    print("stress: heart beating too fast, (tachycardia?)")

else:
    heart_reading < 60
    print("heart beating too slow, (bradycardia?)")

# Print the heart reading and potentiometer on the same line
print(" BPM: {}".format(bpm))

# Insert 0.005s sleep to slow down the printing rate
time.sleep(0.005)# --- Import required modules ---
from machine import Pin, SPI, ADC
import time
import os
import sdcard

# --- Initialize ECG Sensor on ADC pin ---
ecg = ADC(26)  # ADC0 (GPIO26) is used for ECG analog input

# --- Setup SPI and SD card interface ---
# SPI0: SCK=GP2, MOSI=GP3, MISO=GP4
spi = SPI(0, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
cs = Pin(5, Pin.OUT)  # Chip Select (CS) for SD card module

# --- Try to mount the SD card safely ---
try:
    os.umount("/sd")
except OSError:
    pass  # If not mounted yet, continue

try:
    sd = sdcard.SDCard(spi, cs)
    vfs = os.VfsFat(sd)
    os.mount(vfs, "/sd")
    print("SD card mounted successfully.")
except OSError as e:
    print("Failed to mount SD card:", e)
    raise SystemExit  # Stop the program if mount fails

# --- Test write to ensure functionality ---
try:
    with open("/sd/test.txt", "w") as testfile:
        testfile.write("SD card test successful.\n")
except Exception as e:
    print("Failed to write to SD card:", e)
    raise SystemExit

# --- File Handling Parameters ---
file_interval = 5 * 60  # 5 minutes (in seconds)
samples_per_second = 100
sample_interval = 1 / samples_per_second
last_file_time = time.time()

# --- Function to generate a dashcam-style filename ---
def get_filename():
    t = time.localtime()
    return "/sd/ECG_{:02d}{:02d}{:02d}_{:02d}{:02d}.csv".format(
        t[0] % 100, t[1], t[2], t[3], t[4]
    )

# --- Start ECG Logging ---
filename = get_filename()
logfile = open(filename, "w")
logfile.write("Timestamp_ms,ECG_Value\n")

print("📈 Starting ECG recording...")

try:
    while True:
        # Rotate file every 5 minutes
        if time.time() - last_file_time >= file_interval:
            logfile.close()
            filename = get_filename()
            logfile = open(filename, "w")
            logfile.write("Timestamp_ms,ECG_Value\n")
            last_file_time = time.time()

        # Read ECG value and log with timestamp
        timestamp = time.ticks_ms()
        ecg_value = ecg.read_u16()  # 16-bit ADC value (0–65535)
        logfile.write("{},{}\n".format(timestamp, ecg_value))
        logfile.flush()  # Force write immediately

        time.sleep(sample_interval)

except KeyboardInterrupt:
    logfile.close()
    print("Logging stopped by user.")

from micropython import const
import asyncio
import aioble
import bluetooth
import struct
from machine import Pin
from time import sleep

# Init LED
led = Pin(2, Pin.OUT)
led.value(0)

# Init random value
value = 0



_BLE_SERVICE_UUID = bluetooth.UUID('16c85d3a-c399-4228-a2ea-a70d2ae30263')
_BLE_SENSOR_CHAR_UUID = bluetooth.UUID('16c85d3b-c399-4228-a2ea-a70d2ae30263')
_BLE_LED_UUID = bluetooth.UUID('16c85d3c-c399-4228-a2ea-a70d2ae30263')
# How frequently to send advertising beacons.
_ADV_INTERVAL_MS = 250_000

# Register GATT server, the service and characteristics
ble_service = aioble.Service(_BLE_SERVICE_UUID)
sensor_characteristic = aioble.Characteristic(ble_service, _BLE_SENSOR_CHAR_UUID, read=True, notify=True)
led_characteristic = aioble.Characteristic(ble_service, _BLE_LED_UUID, read=True, write=True, notify=True, capture=True)

# Register service(s)
aioble.register_services(ble_service)


# Helper to encode the data characteristic UTF-8
def _encode_data(data):
    return str(data).encode('utf-8')


# Helper to decode the LED characteristic encoding (bytes).
def _decode_data(data):
    try:
        if data is not None:
            # Decode the UTF-8 data
            number = int.from_bytes(data, 'big')
            return number
    except Exception as e:
        print("Error decoding temperature:", e)
        return None


# Get sensor readings
#def get_random_value():
   # return randint(0, 100)

heart_sensor = ADC(26) # ADC0
potentiometer = ADC(27) # ADC1
led : Pin = Pin(20, Pin.OUT) # GP20


# Get new value and update characteristic
async def sensor_task():
    while True:
        heart_reading = heart_sensor.read_u16()
        potentiometer_reading = potentiometer.read_u16()

        if heart_reading > potentiometer_reading:
            led.value(1)
        else:
            led.value(0)

        print(str(heart_reading) + ", " + str(potentiometer_reading))
        sleep(0.005)
        sensor_characteristic.write(_encode_data(value), send_update=True)
        print('Heart beat: ', value)
        await asyncio.sleep_ms(1000)


# Serially wait for connections. Don't advertise while a central is connected.
async def peripheral_task():
    while True:
        try:
            async with await aioble.advertise(
                    _ADV_INTERVAL_MS,
                    name="ESP32",
                    services=[_BLE_SERVICE_UUID],
            ) as connection:
                print("Connection from", connection.device)
                await connection.disconnected()
        except asyncio.CancelledError:
            # Catch the CancelledError
            print("Peripheral task cancelled")
        except Exception as e:
            print("Error in peripheral_task:", e)
        finally:
            # Ensure the loop continues to the next iteration
            await asyncio.sleep_ms(100)


async def wait_for_write():
    while True:
        try:
            connection, data = await led_characteristic.written()
            print(data)
            print(type)
            data = _decode_data(data)
            print('Connection: ', connection)
            print('Data: ', data)
            if data == 1:
                print('Turning LED ON')
                led.value(1)
            elif data == 0:
                print('Turning LED OFF')
                led.value(0)
            else:
                print('Unknown command')
        except asyncio.CancelledError:
            # Catch the CancelledError
            print("Peripheral task cancelled")
        except Exception as e:
            print("Error in peripheral_task:", e)
        finally:
            # Ensure the loop continues to the next iteration
            await asyncio.sleep_ms(100)


# Run tasks
async def main():
    t1 = asyncio.create_task(sensor_task())
    t2 = asyncio.create_task(peripheral_task())
    t3 = asyncio.create_task(wait_for_write())
    await asyncio.gather(t1, t2)


asyncio.run(main())
