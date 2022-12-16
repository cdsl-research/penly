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
# APの初期化
ap = network.WLAN(network.AP_IF)
# 受け取りポート
PORT = 8080
# 書き込みファイルカウンター
WRITE_FILE_COUNTER = 0
# 読み込みファイルカウンター
READ_FILE_COUNTER = 0

# キャッシュデータ(テキストファイル)の削除処理
def deleteCashFile():
    fileList = os.listdir()
    for fl in fileList:
        if "recv" in fl:
            os.remove(fl)

# APを起動する際はこの関数を実行すること
def activate_AP():
    global wifi
    global AP_SSID
    global IP
    global ap
    print("\n --- {アクセスポイントの起動シークエンス} --- ")
    ap = network.WLAN(network.AP_IF)
    AP_SSID = str(ap.config("essid"))
    print("AP_SSID : ", AP_SSID)
    portBind = 8080 # ソケット通信のポート
    # 192.168.xxx.1のxxxをランダムで設定する
    randomAddress = random.randrange(5,254)
    IP = "192.168." + str(randomAddress) + ".1"
    print(f"設定されるアクセスポイントIP : {IP}")
    count_local = 0
    while count_local < 100:
        try:
            ap.config()
            break
        except:
            count_local += 1
            print('.', end="")
    # IP,'255.255.255.0',IP,'8.8.8.8'
    print("\n")
    ap.ifconfig((IP, '255.255.255.0', IP, '8.8.8.8'))
    red.on()
    print("(ip,netmask,gw,dns)=" + str(ap.ifconfig()))
    ap.active(True)

# 研究室Wi-Fiに接続する場合
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
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    
    while count < 3:
        try:
            wifi.connect(ssid)
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


# Wi-Fiスキャン
# 研究室Wi-Fiに繋げられるなら繋げる
# 繋げられない場合はESP32を探す
def wifi_scan():
    print("\n --- {Wi-Fiスキャン & コネクションシークエンス} --- ")
    global wifi
    wifiList = wifi.scan()
    wifiSsidList = list()
    for wl in wifiList:
        wifiSsidList.append(wl[0].decode("utf-8"))
    print(wifiSsidList)
    if LAB_SSID in wifiSsidList:
        # 研究室へ接続
        print(f"{LAB_SSID}のSSID検知 ---> 接続処理開始")
        connect_wifi(LAB_SSID,SSID_PASS)
        return True
    elif "ESP_7B0B85" in wifiSsidList:
        # ESP32へ接続
        print("EPS32のSSID検知 ---> 接続処理開始")
        esp_connect_wifi("ESP_7B0B85")
        return False
    else:
        print("接続できるネットワーク環境がありません")
        return 0



#### ソケット受信時のキューシステム ####
def writeRecvFile(writeData):
    global WRITE_FILE_COUNTER
    fileName = "recv" + str(WRITE_FILE_COUNTER) + ".txt"
    print(f"書き込みデータ : {writeData}  ---> 書き込みファイル名 : {fileName}")
    try:
        file = open(fileName,"w")
        file.write(writeData)
    except Exception as e:
        print(f"writeRecvFile ERROR : {e}")
    finally:
        file.close()
        WRITE_FILE_COUNTER += 1

def readRecvFile():
    global READ_FILE_COUNTER
    fileList = os.listdir()
    
    fileName = "recv" + str(READ_FILE_COUNTER) + ".txt"
    iText = "読み込みファイル名：" + fileName
    print("\r"+str(iText),end="")
    
    if fileName in fileList:
            print("\n--- 受信ファイルを検知 == 読み込みスタート ---")
            try:
                file = open(fileName)
                data = file.read()
            except Exception as e:
                print(f"writeRecvFile ERROR : {e}")
            finally:
                file.close()
                # FILE_COUNTを読み込んだら該当ファイルを削除する
                os.remove(fileName)
                # ファイルを生成したらFILE_COUNTを１上げる
                READ_FILE_COUNT += 1
                print(f"読み込みファイル : {data}")
                return data
    else:
        return 0

# 受信データの読み込んで処理をする
def processRecv():
    while True:
        fileData = readRecvFile()
        if fileData == 0:
            utime.sleep(0.5)
        else:
            fileDataSplit = fileData.split("?")
            fileData = fileDataSplit[0]
            addr = fileDataSplit[1]
            print(f"\処理データ : {fileData} ,受信IPアドレス[ = addr] :  {addr}\n")
            utime.sleep(0.5)


# サーバにHTTPリクエストを送信
def httpPost(url,sendText):
    global AP_SSID
    blue.on()
    print(f"サーバへ送信するデータ： {sendText}")
    
    # 再度SSIDの取得
    AP_SSID = str(ap.config("essid"))
    
    sendData = {
        "data" : sendText,
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

def received_socket():
    listenSocket = socket.socket()
    listenSocket.bind(('', PORT))
    listenSocket.listen(5)
    listenSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print('tcp waiting...')
    print("accepting.....ソケット通信待機中......")
    conn, addr = listenSocket.accept()
    conn.close()
    green.on()
    addr = addr[0]
    data = conn.recv(1024)
    str_data = data.decode()
    print(f"{addr} より接続 ---> 受信データ : {str_data}")
    str_data += "?" + addr
    writeRecvFile(str_data)
    green.off()

def init_network():
    # 研究室Wi-Fiに繋げられるなら繋げる
    # 繋げられない場合はESP32を探す
    labConnectedFlag = wifi_scan()
    
    
    if labConnectedFlag == True:
        # 研究室Wi-Fiに接続している場合はサーバへ通知をする
        url = "http://192.168.100.236:5000/init_network_recieve"
        sendText = "connected"
        httpPost(url,sendText)
        
        # 研究室に通知したらアクセスポイントの起動
        activate_AP()
        # ソケット受け取り準備(threadで・・・)
        _thread.start_new_thread(received_socket,())
        _thread.start_new_thread(processRecv,())
    elif labConnectedFlag == False:
        # ESP32へ接続して色々と処理をする
        pass
    else:
        print("処理せず")
def main():
    
    #execfile("autowifi.py")
    
    print(" --- キャッシュデータ削除処理 ---")
    deleteCashFile()
    
    # 初回のトポロジー設定
    init_network()


if __name__ ==  "__main__":
    main()