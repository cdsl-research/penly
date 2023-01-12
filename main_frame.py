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

#WIFICHECK_THREADのWhile保持関数
FLAG_CHECK_WIFI_ENABLE = True
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
# 宛先までのルート
ROUING_TABLE = {}
# 現在接続されているESP32のIPアドレスとESSIDの辞書
CURRENT_CONNECTED_FROM_ESP32 = {}
# 現在接続しているESP32のIPアドレス
CURRENT_CONNECT_TO_ESP32 = {}
# デフォルトのバッテリー
SET_BATTERY = 10000
# 実験のWHILE文分岐
EXPERIMENT_ENABLE = True

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

def shutdownAP():
    # print("10秒後にアクセスポイントインターフェースを無効化します")
    # utime.sleep(10)
    ap.active(False)
    red.off()
    blue.off()
    processCheckList("check_ap",False)
    print("@@@@@@@@@ アクセスポイントインターフェースを無効化 @@@@@@@@")

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
    global CURRENT_CONNECT_TO_ESP32
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
        # 初期化
        CURRENT_CONNECT_TO_ESP32 = {}
        CURRENT_CONNECT_TO_ESP32[ssid] = True
        print(ssid, 'Connected')
        print(wifi.ifconfig())
        return wifi
    else:
        print(ssid, 'Connection failed!')
        return ''

def check_wifi_thread():
    print(" - - - Wi-Fiの接続確認開始 - - - - ")
    processCheckList("check_thread_checkWifi",True)
    global wifi
    global CURRENT_CONNECT_TO_ESP32
    global NEEDING_CONNECT_ESP32
    ERROR_COUNT = 0
    while FLAG_CHECK_WIFI_ENABLE:
        if wifi.isconnected() == False:
            print(" ----- Wi-Fiの切断を検知  再接続試行----- ")
            red.on()
            wifi.disconnect()
            utime.sleep(0.5)
            # 重さの返信が終わって，まだWi-Fiに接続していないデバイスがあればそちらに接続する
            if DEFAULT_LAB_CONNECT == False:
                print("----- 接続可能先が他にないかチェック ------")
                endFlag = False
                wifi.disconnect()
                for k,v in CURRENT_CONNECT_TO_ESP32.items():
                    CURRENT_CONNECT_TO_ESP32[k] = False
                wifiList = wifi.scan()
                wifiSsidList = list()
                for wl in wifiList:
                    wifiSsidList.append(wl[0].decode("utf-8"))
                print(wifiSsidList)
                for k in wifiSsidList:
                    if k in NEEDING_CONNECT_ESP32:
                        print(f"[{k}]に接続",end="")
                        #wifi = esp_connect_wifi("w")
                        wifi = network.WLAN(network.STA_IF)
                        wifi.active(True)
                        wifi.connect(k)
                        for _ in range(10):
                            if wifi.isconnected():
                                p2.on()
                                print(f"接続完了\n>>>>>>{wifi.ifconfig()}")
                                sendIpAdress = wifi.ifconfig()[2]
                                sendData = f"id={AP_SSID}&command_origin=resist&id_origin={AP_SSID}&route={AP_SSID}"
                                sendSocket(sendIpAdress ,sendData)
                                CURRENT_CONNECT_TO_ESP32[k] = True
                                endFlag = True
                                break
                            else:
                                print(" . ",end="")
                                utime.sleep(0.5)
                    if endFlag == True:
                        break
        utime.sleep(2)


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
        # もしすでに起動している場合は起動せず(IPアドレスが変わっちゃうから)
        if not ap.active():
            activate_AP()
        common_el = list()
        for el in wifiSsidList:
            if el in ENABLE_CONNECT_ESP32 and el in NEEDING_CONNECT_ESP32:
                common_el.append(el)
                print(f"接続可能なESP32を検知 ---> {el}")
        
        if common_el:
            for c_el in common_el:
                if NEEDING_CONNECT_ESP32[c_el] == False:
                    print(f"現在接続されている {wifi.ifconfig()[0]}から切断します")
                    p2.off()
                    wifi.disconnect()
                    utime.sleep(1)
                    esp_connect_wifi(c_el)
                    if check_thread_received_socket != True:
                        _thread.start_new_thread(received_socket,())
                        _thread.start_new_thread(received_udp_socket,())
                    if check_thread_processRecv != True:
                        _thread.start_new_thread(processRecv,())
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
    global CURRENT_CONNECTED_FROM_ESP32
    global ROUING_TABLE
    global EXPERIMENT_ENABLE
    processCheckList("check_thread_processRecv",True)
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
        command_origin = None
        id_origin = ""
        temporaryRoute = ""
        for fspd in fileDataProcessData:
            fspdSplit = fspd.split("=")
            proKey = fspdSplit[0]
            proValue = fspdSplit[1]
            print(f"処理データ KEY : {proKey}     VALUE : {proValue}")
            if proKey == "id":
                recvEsp32Id = proValue
                print(f"受信ESP32のID == {proValue}")
            if proKey == "command_origin":
                command_origin = proValue
            if proKey == "id_origin":
                id_origin = proValue
            if proKey == "route":
                temporaryRoute = proValue
                temporaryRoute += f">{AP_SSID}"
            if proKey == "battery":
                battery = proValue
            if proKey == "to":
                toSending = proValue
            if proKey == "weight":
                weight = proValue
        
        if id_origin != "server":
            if command_origin == "autowifi":
                print(" ********** 緊急処理 : : : : 他のESP32にautowifiを伝搬します ************")
                for ipAdressN in CURRENT_CONNECTED_FROM_ESP32.values():
                    sendText = f"id={AP_SSID}&command_origin=autowifi"
                    sendSocket(ipAdressN,sendText)
                print(" ********** 緊急処理 : : : : autowifi.pyを起動します ************")
                execfile("autowifi.py")
            ROUING_TABLE[id_origin] = recvEsp32Id
            print(f" - - - ルーティングテーブルを更新します  - - - ")
            for rk,rv in ROUING_TABLE.items():
                print(f"宛先 : {rk} <- - -  送り先 : {rv}")
            print(f" - - - - - - - - - - - - - - - - - - - - ")
            if command_origin == "resist":
                CURRENT_CONNECTED_FROM_ESP32[recvEsp32Id] = addr
                REQUIRE_CONNECTED_ESP32[recvEsp32Id] = True
                if DEFAULT_LAB_CONNECT:
                    # 研究室Wi-Fiに接続している場合はサーバへ通知をする
                    url = "http://192.168.100.236:5000/init_network_recieve"
                    sendText = "connected"
                    resist_ESP32_httpPost(url,sendText,id_origin,temporaryRoute)
                    update_connected_from_esp32()
                    check_connected_from_esp32()
                else:
                    sendIpAdress = wifi.ifconfig()[2]
                    # id = 送り元
                    # command_origin = resist (登録)
                    # sub_com = サブコマンド
                    # id_origin = 送り元の紀元
                    # route = たどってきた経路
                    sendDataIndex = {
                        "command_origin" : "resist",
                        "sub_com" : "transfer",
                        "id_origin" : id_origin,
                        "route" : temporaryRoute
                    }
                    sendText = f"id={AP_SSID}"
                    for k ,v in sendDataIndex.items(): 
                        sendText += f"&{k}={v}"
                    sendSocket(sendIpAdress,sendText)
            if command_origin == "resist_complete":
                if DEFAULT_LAB_CONNECT:
                    # 研究室Wi-Fiに接続している場合はサーバへ通知をする
                    url = "http://192.168.100.236:5000/init_network_recieve"
                    sendText = "resist_complete"
                    resist_ESP32_httpPost(url,sendText,id_origin,temporaryRoute)
                    update_connected_from_esp32()
                    check_connected_from_esp32()
                else:
                    sendIpAdress = wifi.ifconfig()[2]
                    # id = 送り元
                    # command_origin = resist (登録)
                    # sub_com = サブコマンド
                    # id_origin = 送り元の紀元
                    # route = たどってきた経路
                    sendDataIndex = {
                        "command_origin" : command_origin,
                        "sub_com" : "transfer",
                        "id_origin" : id_origin,
                        "route" : temporaryRoute
                    }
                    sendText = f"id={AP_SSID}"
                    for k ,v in sendDataIndex.items(): 
                        sendText += f"&{k}={v}"
                    sendSocket(sendIpAdress,sendText)
            if command_origin == "translate":
                if toSending == "server":
                    if DEFAULT_LAB_CONNECT:
                        httpBatteryPost(id_origin,battery,weight)
                    else:
                        msg = f"id={AP_SSID}&command_origin=translate&battery={str(battery)}&to=server&weight={str(weight)}&id_origin={id_origin}"
                        sendIpAdress = wifi.ifconfig()[2]
                        sendSocket(sendIpAdress,msg)
        else:
            # サーバから送信された場合の処理
            print("大変！！！サーバから接続されちゃった！！！！")
            if command_origin == "autowifi":
                print(" ********** 緊急処理 : : : : 他のESP32にautowifiを伝搬します ************")
                EXPERIMENT_ENABLE = False
                print("******* EXPERIMATATIONを停止します ********")
                # for ipAdressN in CURRENT_CONNECTED_FROM_ESP32.values():
                #     sendText = f"id={AP_SSID}&command_origin=autowifi"
                #     sendSocket(ipAdressN,sendText)
                sendText = f"id={AP_SSID}&command_origin=autowifi&id_origin={id_origin}"
                udp_broadcast_send(sendText)
                print(" ********** 緊急処理 : : : : autowifi.pyを起動します ************")
                execfile("autowifi.py")
            elif command_origin == "experiment_start":
                if not check_thread_experiment:
                    print("\n- - - - 実験を開始します - - - - -")
                    sendText = f"id={AP_SSID}&command_origin={command_origin}&id_origin={id_origin}"
                    print("実験スタートを各ESP32に転送します")
                    # all_translate_to_ESP32(recvEsp32Id,sendText)
                    udp_broadcast_send(sendText)
                    EXPERIMENT_ENABLE = True
                    if not check_thread_experiment:
                        processCheckList("check_thread_experiment",True)
                        _thread.start_new_thread(measureCurrent,())
                else:
                    print("---** 既にEXPETIMENTIONは起動しています **---")
            elif command_origin == "experiment_stop":
                print("\n- - - - 実験を***停止***します - - - - -")
                sendText = f"id={AP_SSID}&command_origin={command_origin}&id_origin={id_origin}"
                udp_broadcast_send(sendText)
                EXPERIMENT_ENABLE = False
                processCheckList("check_thread_experiment",False)
            elif command_origin == "reboot":
                print(" ********** 再起動 ************")
                sendText = f"id={AP_SSID}&command_origin={command_origin}&id_origin={id_origin}"
                udp_broadcast_send(sendText)
                utime.sleep(2)
                EXPERIMENT_ENABLE = False
                p2.off()
                blue.off()
                red.off()
                green.off()
                machine.reset()
            elif command_origin == "reset_battery":
                writeFileResetBatteryAmount()
                sendText = f"id={AP_SSID}&command_origin={command_origin}&id_origin={id_origin}"
                udp_broadcast_send(sendText)
            elif command_origin == "startAP":
                if toSending == ESP32_ID:
                    activate_AP()
                else:
                    sendText = f"id={AP_SSID}&command_origin={command_origin}&id_origin={id_origin}&to={toSending}"
                    udp_broadcast_send(sendText)
            elif command_origin == "stopAP":
                if toSending == ESP32_ID:
                    shutdownAP()
                else:
                    sendText = f"id={AP_SSID}&command_origin={command_origin}&id_origin={id_origin}&to={toSending}"
                    udp_broadcast_send(sendText)
        utime.sleep(0.5)

# 実験開始を接続しているESP32へと伝達している
# 引数には送信したいデータを格納する
def all_translate_to_ESP32(recvEsp32Id,sendData):
    global CURRENT_CONNECTED_FROM_ESP32
    
    if CURRENT_CONNECTED_FROM_ESP32:
        for espName, ipAdress in CURRENT_CONNECTED_FROM_ESP32.items():
            if espName != "server" or recvEsp32Id != espName:
                print(f"{espName} : {ipAdress} にデータを送信します")
                transfer_sendSocket(ipAdress,sendData)

# サーバへ転送用
def resist_ESP32_httpPost(url,sendText,transfer_espid,temporaryRoute):
    global AP_SSID
    if AP_SSID != "":
        # 再度SSIDの取得
        AP_SSID = str(ap.config("essid"))
    try:
        blue.on()
        print(f"転送元ESP32 : {transfer_espid}  ---> サーバへ送信するデータ： {sendText}")
            
        sendData = {
            "data" : sendText,
            "espid" : AP_SSID,
            "transfer_espid" : transfer_espid,
            "route" : temporaryRoute
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
        resist_ESP32_httpPost(url,sendText,transfer_espid,temporaryRoute)

# サーバにHTTPリクエストを送信
def httpPost(url,sendText):
    global AP_SSID
    try:
        blue.on()
        print(f"サーバへ送信するデータ： {sendText}")
        ap = network.WLAN(network.AP_IF)
        if AP_SSID == "":
            while AP_SSID == "":
                AP_SSID = str(ap.config("essid"))
        
        print(f"""
            ==== HTTPPOSTの送信前確認 ====
            AP_SSID : {AP_SSID}
        """)
        
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
    except Exception as e:
        blue.off()
        print(" **** サーバへの送信が失敗しました ****")
        print(e)
        print(" **** ３秒後に再度やり直します ****")
        utime.sleep(3)
        httpPost(url,sendText)

def udp_broadcast_send(sendData):
    # UDPソケットを作成する
    socksock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # ブロードキャストアドレスを指定する
    #broadcast_addr = '255.255.255.255'
    broadcast_addr = ap.ifconfig()[0][:-1] + str(255)

    print(f"データ: {sendData} をブロードキャストにて一斉送信")
    blue.on()
    # ブロードキャストアドレスにデータを送信する
    socksock.sendto(sendData, (broadcast_addr, 8888))
    blue.off()
    blue.on()
    # ブロードキャストアドレスにデータを送信する
    socksock.sendto(sendData, (broadcast_addr, 8888))
    blue.off()
    blue.on()
    # ブロードキャストアドレスにデータを送信する
    socksock.sendto(sendData, (broadcast_addr, 8888))
    blue.off()


def sendSocket(ipAdress,sendData,timeout = 3):
    count = 0
    while count < timeout:
        try:
            print(f"送信データ : {sendData} ---> 送信先 : {ipAdress}")
            blue.on()
            s = socket.socket()
            s.connect(socket.getaddrinfo(ipAdress,PORT)[0][-1])
            s.send(sendData)
            s.close()
            blue.off()
            print("Sending Complete!")
            break
        except Exception as e:
            count += 1
            print("\n **** ソケット送信で問題が発生 ****")
            print(e)
            print(" **** ３秒後に再度やり直します ****")
            utime.sleep(3)
            ipAdress = wifi.ifconfig()[2]

def transfer_sendSocket(ipAdress,sendData,timeout = 1):
    count = 0
    while count < timeout:
        try:
            print(f"送信データ : {sendData} ---> 送信先 : {ipAdress}")
            blue.on()
            s = socket.socket()
            s.connect(socket.getaddrinfo(ipAdress,PORT)[0][-1])
            s.send(sendData)
            s.close()
            blue.off()
            print("Sending Complete!")
            break
        except Exception as e:
            count += 1
            print("\n **** ソケット送信で問題が発生 ****")
            print(e)
            print(" **** ３秒後に再度やり直します ****")
            utime.sleep(3)
            

def received_socket():
    listenSocket = socket.socket()
    listenSocket.bind(('', PORT))
    listenSocket.listen(5)
    listenSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    processCheckList("check_thread_received_socket",True)
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

# UDPソケット受信
def received_udp_socket():
    # UDPソケットを作成する
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # ブロードキャストアドレスを受信するためにバインドする
    sock.bind(('0.0.0.0', 8888))

    while True:
        print("accepting.....UDPソケット通信待機中......")
        # データを受信する
        conn, addr = sock.recvfrom(1024)
        green.on()
        addr = addr[0]
        data = conn
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
        #危険なのでコメントアウト
        _thread.start_new_thread(check_wifi_thread,())
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
            if wl == wl2 and wl2 != "":
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
            if check_thread_received_socket != True:
                _thread.start_new_thread(received_socket,())
                _thread.start_new_thread(received_udp_socket,())
            if check_thread_processRecv != True:
                _thread.start_new_thread(processRecv,())
            update_connected_from_esp32()
        elif labConnectedFlag == False:
            processCheckList("check_esp_connected",True)
            # ESP32へ接続して登録処理を行う
            # 再度SSIDの取得
            if AP_SSID == "":
                while AP_SSID == "":
                    ap = network.WLAN(network.AP_IF)
                    AP_SSID = str(ap.config("essid"))
            sendIpAdress = wifi.ifconfig()[2]
            sendData = f"id={AP_SSID}&command_origin=resist&id_origin={AP_SSID}&route={AP_SSID}"
            sendSocket(sendIpAdress,sendData)
            processCheckList("check_resist",True)
            update_init_remaining_esp32()
            check_init_remaing_esp32()
        else:
            print("処理せず")
    else:
        init_network()


def httpBatteryPost(idName,sendingData,weight):
    global BATTERY
    url = "http://192.168.100.236:5000/battery_recieve"
    try:
        blue.on()
        print(f" --- サーバへ電池残量を送信 >>> ESP32 : {idName} , 電池残量 : {sendingData} , 重み : {weight}---")
        
        print(f"""
            ==== HTTPPOSTの送信前確認 ====
            AP_SSID : {AP_SSID}
        """)
        
        sendData = {
            "transfer_espid" : idName,
            "data" : sendingData,
            "espid" : AP_SSID,
            "weight" : str(weight)
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
        print(e)
        print("@@@@@ サーバへの送信が失敗．スキップします @@@@@")

# 電池残量のデータ送信間隔[秒]
BATTERY_SLEEP_INTERVAL = 10
def getCurrent():
    ## デバッグが完了したらコメントアウトを外す
    # current = ina.current()
    # current = abs(current)
    # while True:
    #     if current < 170:
    #         break
    #     current = current - (current / 5)
    
    ## INA219を指していない場合のデバッグよう
    if ap.active():
        current = 150
        randomNumber = random.random()
        if randomNumber < 0.5:
            calibrationN = -10 * randomNumber
        else:
            calibrationN = 10 * randomNumber / 2
        current += calibrationN
    
    print("Current: %.3f mA" % current)
    return current

# サーバに電池残量を送信
# その際に必ず電池残量から測定した電流を引くこと
def currentAverageMeasure():
    currentSum = 0.0
    currentAverage = 0.0
    countSum = 0.0
    while countSum < BATTERY_SLEEP_INTERVAL:
        green.on()
        current = getCurrent()
        current = abs(current)
        currentSum += current
        countSum += 1.0
        green.off()
        utime.sleep(1)

    currentAverage = currentSum / countSum
    return currentAverage

def readFileBattery():
    # 読込むファイルのパスを宣言する
    file_name = "battery.txt"
    try:
        file = open(file_name)
        data = file.read()
        return data
    except Exception as e:
        print(e)
    finally:
        file.close()

def writeFileBattery(writeData):
    # 書き込むファイルのパスを宣言する
    file_name = "battery.txt"
    writeData = str(writeData)
    try:
        file = open(file_name, 'w')
        file.write(writeData)
    except Exception as e:
        print(e)
    finally:
        file.close()

# バッテリーをリセットする
SET_BATTERY = 10000
def writeFileResetBatteryAmount():
    # 書き込むファイルのパスを宣言する
    print("バッテリー残量を",str(SET_BATTERY),"へリセットしました")
    file_name = "battery.txt"
    writeData = str(SET_BATTERY)
    try:
        file = open(file_name, 'w')
        file.write(writeData)
    except Exception as e:
        print(e)
    finally:
        file.close()

# battery.txtの値をデフォルトに修正する
def writeFileResetBatteryAmount():
    # 書き込むファイルのパスを宣言する
    print("バッテリー残量を",str(SET_BATTERY),"へリセットしました")
    file_name = "battery.txt"
    writeData = str(SET_BATTERY)
    try:
        file = open(file_name, 'w')
        file.write(writeData)
    except Exception as e:
        print(e)
    finally:
        file.close()

# 積層重み
LAMI_COST = 0
def measureCurrent():
    global BATTERY
    while EXPERIMENT_ENABLE:
        count = 0
        sumCurrent = 0
        while count < 30:
            battery = readFileBattery()
            battery = float(battery)
            ## デバッグが終わり次第コメントアウトを外す
            # current = ina.current()
            # current = abs(current)
            # while True:
            #     if current < 170:
            #         break
            #     current = current - (current / 5)
            
            ### 一時的
            if ap.active():
                current = 150
                randomNumber = random.random()
                if randomNumber < 0.5:
                    calibrationN = -10 * randomNumber
                else:
                    calibrationN = 10 * randomNumber / 2
                current += calibrationN
            else:
                current = 55
                randomNumber = random.random()
                if randomNumber < 0.5:
                    calibrationN = -10 * randomNumber
                else:
                    calibrationN = 10 * randomNumber / 2
                current += calibrationN
            ###ここまで
            sumCurrent += current
            iText = "Current: %.3f mA" % current
            currentData = "%.3f" % current
            currentData += "\n"
            print("\r" + str(iText),end="")
            f = open('current.csv', 'a')
            f.write(str(currentData))
            f.close() 
            count += 1
            utime.sleep(1)
            
        sumCurrent /= 30
        
        print(f"---- 60秒間の平均消費電力 : {sumCurrent}[mA]   電池残量残量 : {battery - sumCurrent}[mAh] ----")
        
        battery -= sumCurrent
        batteryData = "%.3f" % battery
        batteryData += "\n"
        if DEFAULT_LAB_CONNECT == True:
            httpBatteryPost(AP_SSID,str(battery) ,str(LAMI_COST))
        else:
            msg = f"id={AP_SSID}&command_origin=translate&battery={str(battery)}&to=server&weight={str(LAMI_COST)}&id_origin={AP_SSID}"
            sendIpAdress = wifi.ifconfig()[2]
            sendSocket(sendIpAdress,msg)
        writeFileBattery(str(battery))
        f = open('battery.csv', 'a')
        f.write(str(batteryData))
        f.close()

####### チェックリスト #######
check_booting = False
check_wifi = False
check_ap = False
check_resist = False
check_esp_allconnect = False # 全てのESP32に接続したか？(CDSLに繋がらない場合)
check_esp_connected = False # 全てのESP32が接続してきたか？ (CDSLに繋げない場合)
check_thread_received_socket = False
check_thread_processRecv = False
check_thread_checkWifi = False
check_thread_experiment = False
def processCheckList(processName,checked):
    global check_booting
    global check_wifi
    global check_ap
    global check_resist
    global check_esp_allconnect
    global check_esp_connected
    global check_thread_processRecv
    global check_thread_received_socket
    global check_thread_checkWifi
    global check_thread_experiment
    
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
    elif processName == "check_thread_received_socket":
        check_thread_received_socket = checked
    elif processName == "check_thread_processRecv":
        check_thread_processRecv = checked
    elif processName == "check_thread_checkWifi":
        check_thread_checkWifi = checked
    elif processName == "check_thread_experiment":
        check_thread_experiment = checked
    
    checkList = f"""
    booting             :   {check_booting}
    wi-fi               :   {check_wifi}
    eneble AP           :   {check_ap}
    RESIST              :   {check_resist}
    ESP_CONNECT_COMP    :   {check_esp_allconnect}
    CONNECTED_ESP_COMP  :   {check_esp_connected}
    
    =THEAD=
    receiced_socket()   :   {check_thread_received_socket}
    processRecv()       :   {check_thread_processRecv}
    checkWifi()         :   {check_thread_checkWifi}
    experiment()        :   {check_thread_experiment}
    """
    
    print(checkList)
    
##############


def main():
    processCheckList("check_booting",True)
    #execfile("autowifi.py")
    
    print(" --- キャッシュデータ削除処理 ---")
    deleteCashFile()
    
    print("init_flag.pyを実行")
    execfile("init_flag.py")
    init_network()
    
    print("\n - - - - ネットワークの初期化完了 - - - - - -")
    if wifi.ifconfig()[0].split(".")[2] != "100":
        sendIpAdress = wifi.ifconfig()[2]
        sendData = f"id={AP_SSID}&command_origin=resist_complete&id_origin={AP_SSID}&route={AP_SSID}"
        sendSocket(sendIpAdress,sendData)
    red.off()
    for _ in range(10):
        green.on()
        utime.sleep(0.1)
        green.off()
        utime.sleep(0.1)
    
    # if INIT_FLAG == False:
    #     print(": : : : : 未初期化 = 初期化開始 : : : : : ")
    #     # 初回のトポロジー設定
    #     init_network()
    #     try:
    #         file = open("init_flag.py","w")
    #         file.write("INIT_FLAG = True")
    #         print(" * * * * INIT_FLAGをTrueに変更 * * * * ")
    #     except Exception as e:
    #         print(f"INIT_FLAG.py ERROR : {e}")
    #     finally:
    #         file.close()
    # else:
    #     print(": : : : : 初期化済み : : : : : ")
        


if __name__ ==  "__main__":
    main()