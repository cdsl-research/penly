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
    processCheckList("check_ap",True)

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
        NEEDING_CONNECT_ESP32[ssid] = True
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
    global NEEDING_CONNECT_ESP32
    wifiList = wifi.scan()
    wifiSsidList = list()
    for wl in wifiList:
        wifiSsidList.append(wl[0].decode("utf-8"))
    print(wifiSsidList)
    update_init_remaining_esp32(wifiSsidList)
    connected_wifi = False
    if LAB_SSID in wifiSsidList and DEFAULT_LAB_CONNECT == True:
        # 研究室へ接続
        print(f"{LAB_SSID}のSSID検知 ---> 接続処理開始")
        connect_wifi(LAB_SSID,SSID_PASS)
        return True
    else:
        # 研究室に繋げないと分かったらとにあえずAP起動する
        activate_AP()
        common_el = list()
        for el in wifiSsidList:
            if el in ENABLE_CONNECT_ESP32 and el in NEEDING_CONNECT_ESP32:
                common_el.append(el)
                print(f"接続可能なESP32を検知 ---> {el}")
        
        if common_el:
            for c_el in common_el:
                esp_connect_wifi(c_el)
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
                READ_FILE_COUNTER += 1
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
            continue
        fileDataSplit = fileData.split("?")
        fileData = fileDataSplit[0]
        addr = fileDataSplit[1]
        print(f"処理データ : {fileData} ,受信IPアドレス[ = addr] :  {addr}\n")
        
        fileDataProcessData = fileData.split("&")
        recvEsp32Id = ""
        command = None
        for fspd in fileDataProcessData:
            fspdSplit = fspd.split("=")
            proKey = fspdSplit[0]
            proValue = fspdSplit[1]
            print(f"処理データ KEY : {proKey}     VALUE : {proValue}")
            if proKey == "id":
                recvEsp32Id = proValue
                print(f"受信ESP32のID == {proValue}")
            if proKey == "command":
                command = proValue
        
        if command == "resist":
            REQUIRE_CONNECTED_ESP32[recvEsp32Id] = True
            # 研究室Wi-Fiに接続している場合はサーバへ通知をする
            url = "http://192.168.100.236:5000/init_network_recieve"
            sendText = "connected"
            resist_ESP32_httpPost(url,sendText,recvEsp32Id)
            update_connected_from_esp32()
            check_connected_from_esp32()
        utime.sleep(0.5)



# サーバへ転送用
def resist_ESP32_httpPost(url,sendText,transfer_espid):
    global AP_SSID
    if AP_SSID != "":
        # 再度SSIDの取得
        AP_SSID = str(ap.config("essid"))
    blue.on()
    print(f"転送元ESP32 : {transfer_espid}  ---> サーバへ送信するデータ： {sendText}")
        
    sendData = {
        "data" : sendText,
        "espid" : AP_SSID,
        "transfer_espid" : transfer_espid
    }
    
    url += "?"
    
    for sdk,sdv in sendData.items():
        url += sdk + "=" + sdv + "&"
    print(url)
    res = urequests.get(url)
    print("サーバからのステータスコード：", res.status_code)
    res.close()
    blue.off()

# サーバにHTTPリクエストを送信
def httpPost(url,sendText):
    global AP_SSID
    blue.on()
    print(f"サーバへ送信するデータ： {sendText}")
    
    if AP_SSID != "":
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

def sendSocket(ipAdress,sendData):
    print(f"送信データ : {sendData} ---> 送信先 : {ipAdress}")
    blue.on()
    s = socket.socket()
    s.connect(socket.getaddrinfo(ipAdress,PORT)[0][-1])
    s.send(sendData)
    s.close()
    blue.off()
    print("Sending Complete!")
    
def received_socket():
    listenSocket = socket.socket()
    listenSocket.bind(('', PORT))
    listenSocket.listen(5)
    listenSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print('tcp waiting...')
    while True:
        print("accepting.....ソケット通信待機中......")
        conn, addr = listenSocket.accept()
        green.on()
        addr = addr[0]
        data = conn.recv(1024)
        conn.close()
        str_data = data.decode()
        print(f"{addr} より接続 ---> 受信データ : {str_data}")
        str_data += "?" + addr
        writeRecvFile(str_data)
        green.off()
        

### 接続できるESP32の候補を制限する

### 接続が必要なESP32のチェックリスト,全てTrueになればOK
NEEDING_CONNECT_ESP32 = {}
### 初回で，接続できるESP32を全て洗い出す
def update_init_remaining_esp32(wifiList=None):
    global wifi
    global NEEDING_CONNECT_ESP32
    
    # もし引数に何も与えられなかったらここでスキャンする
    if wifiList == None:
        wifiList = wifi.scan()
        wifiSsidList = list()
        for wl in wifiList:
            wifiSsidList.append(wl[0].decode("utf-8"))
        wifiList = wifiSsidList

    if DEFAULT_LAB_CONNECT == False:
        for wl in wifiList:
            for wl2 in ENABLE_CONNECT_ESP32:
                if wl2 == wl:
                    if wl in NEEDING_CONNECT_ESP32:
                        if NEEDING_CONNECT_ESP32[wl] == False:
                            NEEDING_CONNECT_ESP32[wl] = False
                    else:
                        NEEDING_CONNECT_ESP32[wl] = False
        
        print("接続可能ESP32  ---↓")
        for k,v in NEEDING_CONNECT_ESP32.items():
            print(f"{k} : {v}")

def check_init_remaing_esp32():
    global NEEDING_CONNECT_ESP32
    if False in NEEDING_CONNECT_ESP32.values():
        init_network()
    else:
        print("\nESP32の全ての接続と更新を完了します")
        processCheckList("check_esp_allconnect",True)
        return True



### 接続されるはずのESP32を列挙し，ちゃんと接続されたかを判別する
REQUIRE_CONNECTED_ESP32 = {}
def update_connected_from_esp32():
    global REQUIRE_CONNECTED_ESP32
    # wifiスキャン
    wifiList = wifi.scan()
    wifiSsidList = list()
    for wl in wifiList:
        wifiSsidList.append(wl[0].decode("utf-8"))
    wifiList = wifiSsidList
    
    for wl in wifiList:
        for wl2 in ENABLE_CONNECT_ESP32:
            if wl == wl2:
                if wl in REQUIRE_CONNECTED_ESP32:
                    if REQUIRE_CONNECTED_ESP32[wl] == False:
                        REQUIRE_CONNECTED_ESP32[wl] = False
                else:
                    REQUIRE_CONNECTED_ESP32[wl] = False

    print("----- 接続予定のESP32リストの更新 -----")
    for k,v in REQUIRE_CONNECTED_ESP32.items():
        print(f"{k}  :   {v}")

def check_connected_from_esp32():
    global REQUIRE_CONNECTED_ESP32
    if False not in REQUIRE_CONNECTED_ESP32.values():
        print("\n接続予定の全てのESP32との接続を確認")
        processCheckList("check_esp_connected",True)
        return True
    else:
        return False

def init_network():
    global AP_SSID
    global ap
    # 研究室Wi-Fiに繋げられるなら繋げる
    # 繋げられない場合はESP32を探す
    labConnectedFlag = wifi_scan()
    
    if wifi.ifconfig()[0].split(".")[0] == "192":
        processCheckList("check_wifi",True)
        if labConnectedFlag == True:
            processCheckList("check_esp_allconnect",True)
            # 研究室Wi-Fiに接続している場合はサーバへ通知をする
            url = "http://192.168.100.236:5000/init_network_recieve"
            sendText = "connected"
            httpPost(url,sendText)
            processCheckList("check_resist",True)
            # 研究室に通知したらアクセスポイントの起動
            activate_AP()
            # ソケット受け取り準備(threadで・・・)
            _thread.start_new_thread(received_socket,())
            _thread.start_new_thread(processRecv,())
            update_connected_from_esp32()
        elif labConnectedFlag == False:
            processCheckList("check_esp_connected",True)
            # ESP32へ接続して登録処理を行う
            # 再度SSIDの取得
            if AP_SSID != "":
                while AP_SSID == "":
                    ap = network.WLAN(network.AP_IF)
                    AP_SSID = str(ap.config("essid"))
            sendIpAdress = wifi.ifconfig()[2]
            sendData = f"id={AP_SSID}&command=resist"
            sendSocket(sendIpAdress,sendData)
            processCheckList("check_resist",True)
            update_init_remaining_esp32()
            check_init_remaing_esp32()
        else:
            print("処理せず")
    else:
        init_network()


####### チェックリスト #######
check_booting = False
check_wifi = False
check_ap = False
check_resist = False
check_esp_allconnect = False # 全てのESP32に接続したか？(CDSLに繋がらない場合)
check_esp_connected = False # 全てのESP32が接続してきたか？ (CDSLに繋げない場合)
def processCheckList(processName,checked):
    global check_booting
    global check_wifi
    global check_ap
    global check_resist
    global check_esp_allconnect
    global check_esp_connected
    
    if processName == "check_booting":
        check_booting = checked
    elif processName == "check_wifi":
        check_wifi = checked
    elif processName == "check_ap":
        check_ap = checked
    elif processName == "check_resist":
        check_resist = checked
    elif processName == "check_esp_allconnect":
        check_esp_allconnect = checked
    elif processName == "check_esp_connected":
        check_esp_connected = checked
    
    checkList = f"""
    booting             :   {check_booting}
    wi-fi               :   {check_wifi}
    eneble AP           :   {check_ap}
    RESIST              :   {check_resist}
    ESP_CONNECT_COMP    :   {check_esp_allconnect}
    CONNECTED_ESP_COMP  :   {check_esp_connected}
    """
    
    print(checkList)
##############


def main():
    processCheckList("check_booting",True)
    #execfile("autowifi.py")
    
    print(" --- キャッシュデータ削除処理 ---")
    deleteCashFile()
    
    # 初回のトポロジー設定
    init_network()


if __name__ ==  "__main__":
    main()