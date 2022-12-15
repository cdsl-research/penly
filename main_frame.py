import bmp280
import utime
import network
import machine
import _thread
import socket
import os
from machine import Pin, I2C
import urequests
import ujson
import random

# 自身のAPのSSIDを保持
AP_SSID = ""
# 自身のIPアドレス
IP = ""

# キャッシュデータ(テキストファイル)の削除処理
def deleteCashFile():
    fileList = os.listdir()
    for fileNameOne in fileList:
        if "recv" in fileNameOne:
            os.remove(fileNameOne)

# APを起動する際はこの関数を実行すること
def activate_AP():
    global wifi
    global AP_SSID
    global IP
    
    ap = network.WLAN(network.AP_IF)
    AP_SSID = str(ap.config("essid"))
    print("AP_SSID : ", AP_SSID)
    portBind = 8080 # ソケット通信のポート
    # 192.168.xxx.1のxxxをランダムで設定する
    randomAddress = random.randrange(5,254)
    IP = "192.168." + str(randomAddress) + ".1"
    print(f"設定されるアクセスポイントIP : {IP}")

def init_network():
    activate_AP()
    

def main():    
    # print(" --- キャッシュデータ削除処理 ---")
    # deleteCashFile()
    
    # 初回のトポロジー設定
    init_network()


if __name__ ==  "__main__":
    main()