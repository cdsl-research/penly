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

SET_AP = True

# メインプログラムでエラーが起きた場合、強制再起動
try:
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

    ###### Wi-Fi各種設定 #####
    espIpList = ["192.168.100.87","192.168.100.164","192.168.100.218","192.168.100.82","192.168.100.228"]
    espSsidList = ["ESP_7B0B85", "ESP_27B055"]
    #espSsidList = ["ESP_27B055","ESP_7B0B85","ESP_A97611","ESP_A974B5","ESP_A966F1"]

    print("boot is ok")
    utime.sleep(1)


    # execfile("ina219.py")
    # execfile("ina219_get.py")
    execfile("ctime.py")
    # autowifi.pyはap.pyをコメントアウトしている代わりに入れている
    # execfile("autowifi.py")
    execfile("main_frame.py")
except Exception as e:
    print(e)
    p2.off()
    blue.off()
    red.off()
    green.off()
    machine.reset()

# try:
#     execfile("ina219.py")
#     execfile("ina219_get.py")
#     execfile("ctime.py")
#     # autowifi.pyはap.pyをコメントアウトしている代わりに入れている
#     # execfile("autowifi.py")
#     execfile("main_flame.py")
# except KeyboardInterrupt:
#     print("KeyBoardInterrupt Ctrl + C")
# except Exception as e:
#     print(e)
#     p2.off()
#     blue.off()
#     red.off()
#     green.off()
#     machine.reset()