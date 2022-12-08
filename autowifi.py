

import webrepl
from machine import Pin
import machine
import network
import utime
SSID_NAME_AUTO = ["CDSL-A910-11n"]
SSID_PASS_AUTO = {"CDSL-A910-11n": SSID_PASS}


N = ''

p2 = Pin(2, Pin.OUT)
red = Pin(13, Pin.OUT)
blue = Pin(4, Pin.OUT)
green = Pin(5, Pin.OUT)

esp_list = ["ESP_27B055", "ESP_7B0B85", "ESP_A97611","ESP_2C3AC5"]
#esp_list = ["27B055","7B0B85","A97611","A974B5","A966F1"]


wifiStatus = True

wifi = network.WLAN(network.STA_IF)
wifi.active(True)

# アクセスポイントの検索


def wifiscan():
    global AP_ROOT
    global wifi
    global CHECK_CONNECT_ESP
    wifiList = wifi.scan()
    wifiAPList = []
    wifiRSSIList = []
    wifiAPDict = {}
    for wl in wifiList:
        if wl[0].decode("utf-8") != "":
            wifiAPDict.update([(wl[0].decode("utf-8"), int(wl[3]))])

    if any(wifiAPDict) == False:
        return ""

    apCount = 0
    wifiAPDictTrue = {}
    wifiESPDictTrue = {}
    ApInList = False
    for ak, av in wifiAPDict.items():
        if ak in SSID_NAME_AUTO:
            ApInList = True
            apCount += 1
            wifiAPDictTrue.update([(ak, av)])

    if ApInList == True:
        AP_ROOT = 1
        COST = 1
        wifiAPDictTrueSorted = sorted(
            wifiAPDictTrue.items(), key=lambda x: x[1], reverse=True)
        print("##### ESP以外のWi-Fiアクセスポイントのリストアップ #####")
        print(wifiAPDictTrueSorted)

        return wifiAPDictTrueSorted[0][0]
    else:
        AP_ROOT = 0
        for ak, av in wifiAPDict.items():
            if ak in esp_list:
                wifiESPDictTrue.update([(ak, av)])

        wifiESPDictTrueSorted = sorted(
            wifiESPDictTrue.items(), key=lambda x: x[1], reverse=True)
        print("##### ESPのセットアップ #####")
        print(wifiESPDictTrueSorted)

        for ak, av in wifiESPDictTrueSorted.items():
            CHECK_CONNECT_ESP.update([(ak, 0)])

        return wifiESPDictTrueSorted[0][0]


# APに接続する場合
def connect_wifi(ssid, passkey, timeout=10):
    count = 0
    while count < 3:
        try:
            wifi.connect(ssid, passkey)
            break
        except:
            utime.sleep(3)
            count += 1
    while not wifi.isconnected() and timeout > 0:
        print('.')
        utime.sleep(1)
        timeout -= 1

    if wifi.isconnected():
        p2.on()
        print(ssid, 'Connected')
        webrepl.start(password='cdsl')
        return wifi
    else:
        print(ssid, 'Connection failed!')
        return ''

# ESPに接続する場合(PASSなし)
def esp_connect_wifi(ssid, timeout=10):
    count = 0
    while count < 3:
        try:
            wifi.connect(ssid)
            CHECK_CONNECT_ESP[ssid] = 1
            break
        except:
            utime.sleep(3)
            count += 1
    while not wifi.isconnected() and timeout > 0:
        print('.')
        utime.sleep(1)
        timeout -= 1

    if wifi.isconnected():
        p2.on()
        print(ssid, 'Connected')
        print(wifi.ifconfig())
        return wifi
    else:
        print(ssid, 'Connection failed!')
        return ''


while True:
    wifiName = wifiscan()
    if "CDSL" in wifiName:
        break
    else:
        print("Wi-Fiが見つからなかったため再度Wi-Fiをスキャンします")
while True:
    if "ESP" not in wifiName:
        print(wifiName, "founded and Connecting")
        wifi = connect_wifi(wifiName, SSID_PASS_AUTO[wifiName])
    elif "ESP" in wifiName:
        print(wifiName, "founded and Connecting")
        wifi = esp_connect_wifi(wifiName)
    if wifi != None:
        break