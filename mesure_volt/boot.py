
import network
import machine
from machine import Pin, SoftI2C
import utime
import webrepl

machine.freq(240000000)

# Wi-Fiパスワードを設定
execfile("wifi-password.py")
# ESP32に与えた固有のIDを設定
execfile("id.py")

red = Pin(13, Pin.OUT)
blue = Pin(4, Pin.OUT)
green = Pin(5, Pin.OUT)

p21 = Pin(21, Pin.IN, Pin.PULL_UP)
p22 = Pin(22, Pin.IN, Pin.PULL_UP)
p2 = Pin(2, Pin.OUT)
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))

ID = machine.unique_id()

LAB_SSID = "CDSL-A910-11n"

wifi = network.WLAN(network.STA_IF)
wifi.active(True)

print("boot is ok")
utime.sleep(1)

execfile("autowifi.py")