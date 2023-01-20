

import webrepl
from machine import Pin
import machine
import network
import utime
import urequests
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

FLAG_CHECK_WIFI_ENABLE = False
utime.sleep(2)

# アクセスポイントの検索


def wifiscan():
    global wifi
    wifi_list = wifi.scan()
    wifi_ap_dict = {}
    for wl in wifi_list:
        if wl[0].decode("utf-8") != "":
            wifi_ap_dict[wl[0].decode("utf-8")] = int(wl[3])
    if not wifi_ap_dict:
        return ""
    wifi_ap_dict_filtered = {
        k: v
        for k, v in wifi_ap_dict.items()
        if k in SSID_NAME_AUTO
    }
    if wifi_ap_dict_filtered:
        global AP_ROOT
        global COST
        AP_ROOT = 1
        COST = 1

        strongest_ap = max(wifi_ap_dict_filtered, key=wifi_ap_dict_filtered.get)

        print("##### ESP以外のWi-Fiアクセスポイントのリストアップ #####")
        print(wifi_ap_dict_filtered)

        return strongest_ap

    else:
        global AP_ROOT
        AP_ROOT = 0

        wifi_esp_dict_filtered = {
            k: v
            for k, v in wifi_ap_dict.items()
            if k in esp_list
        }

        strongest_esp = max(wifi_esp_dict_filtered, key=wifi_esp_dict_filtered.get)

        print("##### ESPのセットアップ #####")
        print(wifi_esp_dict_filtered)

        global CHECK_CONNECT_ESP
        CHECK_CONNECT_ESP = {k: 0 for k in wifi_esp_dict_filtered.keys()}

        return strongest_esp


# サーバへ転送用
def CDSL_connection_resist():
    global AP_SSID
    url = "http://192.168.100.236:5000/cdsl_network_connect"
    if AP_SSID != "":
        # 再度SSIDの取得
        AP_SSID = str(ap.config("essid"))
    try:
        blue.on()
        sendData = {
            "data" : "cdsl_connection",
            "espid" : AP_SSID
        }
        
        url += "?"
        
        for sdk,sdv in sendData.items():
            url += sdk + "=" + sdv + "&"
        print(url)
        res = urequests.get(url)
        print("サーバからのステータスコード：", res.status_code)
        res.close()
        blue.off()
    except Exception as e:
        blue.off()
        print(" **** サーバへの送信が失敗しました ****")
        print(e)
        print(" **** ３秒後に再度やり直します ****")
        utime.sleep(3)
        CDSL_connection_resist()


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
        CDSL_connection_resist()
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


#最初から研究室に接続してたら別にやらなくてよい
if not DEFAULT_LAB_CONNECT and wifi.ifconfig()[0].split(".")[2] != "100":
    # 最初に切断処理をしちゃう
    if wifi.ifconfig()[0].split(".")[0] == "192":
        wifi.disconnect()
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

try:
    if not DEFAULT_LAB_CONNECT:
        _thread.start_new_thread(received_udp_socket,())
except:
    print("received_udp_socketエラースキップ")