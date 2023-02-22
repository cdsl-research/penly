import utime
import network
import machine
import _thread
import socket
import os
import urequests
import random

#WIFICHECK_THREADのWhile保持関数だ
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
# 送信できなかった(CURRENT_CONNECTTED_FROM_ESP32にあるのに)ESP32のリストアップ
ERROR_CONNECT_ESP32 = {}
# 切断前のスリープ秒
WIFI_DISCONNECTION_TIME = 2
# 再起動時, 実験を継続するか?
# fff = open("reboot_experiment.txt","r")
# ddd = fff.read()
# if ddd == "False":
#     REBOOT_EXPERIMENT_JUDGE = False
# elif ddd == "True":
#     REBOOT_EXPERIMENT_JUDGE = True
# fff.close()
REBOOT_EXPERIMENT_JUDGE = False

# 再起動時, APを起動するか?
fff = open("reboot_ap.txt","r")
ddd = fff.read()
if ddd == "False":
    REBOOT_AP = False
elif ddd == "True":
    REBOOT_AP = True
fff.close()

def rewrite_reboot_experiment(judge):
    if judge:
        file = open("reboot_experiment.txt","w")
        file.write("True")
        file.close()
    else:
        file = open("reboot_experiment.txt","w")
        file.write("False")
        file.close()

def rewrite_reboot_ap(judge):
    if judge:
        file = open("reboot_ap.txt","w")
        file.write("True")
        file.close()
    else:
        file = open("reboot_ap.txt","w")
        file.write("False")
        file.close()
        
# キャッシュデータ(テキストファイル)の削除処理
def deleteCashFile():
    fileList = os.listdir()
    for fl in fileList:
        if "recv" in fl:
            os.remove(fl)
        if "battery.csv" == fl:
            os.remove(fl)
        if "current.csv" == fl:
            os.remove(fl)

def randomAddressGenerator():
    NNN = random.randrange(5,254)
    return NNN

# APを起動する際はこの関数を実行すること
def activate_AP():
    global wifi
    global AP_SSID
    global IP
    global ap
    print("\n --- {Access point startup sequence} --- ")
    ap = network.WLAN(network.AP_IF)
    AP_SSID = str(ap.config("essid"))
    print("AP_SSID : ", AP_SSID)
    portBind = 8080 # ソケット通信のポート
    # 192.168.xxx.1のxxxをランダムで設定する
    randomAddress = randomAddressGenerator()
    IP = "192.168." + str(randomAddress) + ".1"
    print(f"設定されるアクセスポイントIP : {IP}")
    if randomAddress == wifi.ifconfig()[0].split(".")[2]:
        while randomAddress == wifi.ifconfig()[0].split(".")[2]:
            print(f"現在接続中のIP : {wifi.ifconfig()[0]} と競合が発生したため再度IPアドレスを設定します")
            randomAddress = randomAddressGenerator()
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
        p2.on()
        print('.')
        utime.sleep(0.5)
        p2.off()
        utime.sleep(0.5)
        timeout -= 1

    if wifi.isconnected():
        p2.on()
        print(ssid, 'Connected')
        webrepl.start(password='cdsl')
        return wifi
    else:
        print(ssid, 'Connection failed!')
        return ''


def update_needing_connect_esp32():
    global NEEDING_CONNECT_ESP32
    ### NEEDING_CONNECT_ESP32を更新
    print("will update NEEDING_CONNECT_ESP32")
    NEEDING_CONNECT_ESP32 = {wl: False for wl in wifiSsidList if wl in ENABLE_CONNECT_ESP32}
    print(f"NEEDING_CONNECT_ESP32 : {NEEDING_CONNECT_ESP32}")

# ESPに接続する場合(PASSなし)
def esp_connect_wifi(ssid, timeout=20):
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
        p2.on()
        print('.')
        utime.sleep(0.5)
        p2.off()
        utime.sleep(0.5)
        timeout -= 1

    if wifi.isconnected():
        p2.on()
        NEEDING_CONNECT_ESP32[ssid] = True
        # 初期化
        CURRENT_CONNECT_TO_ESP32 = {}
        CURRENT_CONNECT_TO_ESP32[ssid] = True
        print(ssid, 'Connected')
        print(wifi.ifconfig())
        ### NEEDING_CONNECT_ESP32を更新
        update_needing_connect_esp32()
        return wifi
    else:
        print(ssid, 'Connection failed!')
        ### NEEDING_CONNECT_ESP32を更新
        update_needing_connect_esp32()
        return ''

def check_wifi_thread():
    try:
        print(" - - - Wi-Fiの接続確認開始 - - - - ")
        processCheckList("check_thread_checkWifi",True)
        global wifi
        global CURRENT_CONNECT_TO_ESP32
        global NEEDING_CONNECT_ESP32
        ERROR_COUNT = 0
        GREEN_ERROR_COUNT = 0
        while FLAG_CHECK_WIFI_ENABLE:
            if wifi.isconnected() == False:
                print(" ----- Wi-Fiの切断を検知  再接続試行----- ")
                red.on()
                disconnect_report()
                utime.sleep(WIFI_DISCONNECTION_TIME)
                wifi.disconnect()
                print("--- Wi-Fi 切断完了 ---")
                utime.sleep(0.5)
                if DEFAULT_LAB_CONNECT == False:
                    print("----- 接続可能先が他にないかチェック ------")
                    endFlag = False
                    disconnect_report()
                    utime.sleep(WIFI_DISCONNECTION_TIME)
                    wifi.disconnect()
                    print("--- Wi-Fi 切断完了 ---")
                    for k,v in CURRENT_CONNECT_TO_ESP32.items():
                        CURRENT_CONNECT_TO_ESP32[k] = False
                    wifiList = wifi.scan()
                    wifiSsidList = list()
                    for wl in wifiList:
                        wifiSsidList.append(wl[0].decode("utf-8"))
                    print(wifiSsidList)
                    
                    ### NEEDING_CONNECT_ESP32を更新
                    update_needing_connect_esp32()
                    
                    for k in wifiSsidList:
                        if k in NEEDING_CONNECT_ESP32:
                            print(f"[{k}]に接続",end="")
                            #wifi = esp_connect_wifi("w")
                            wifi = network.WLAN(network.STA_IF)
                            wifi.active(True)
                            wifi.connect(k)
                            for _ in range(10):
                                if wifi.isconnected():
                                    NEEDING_CONNECT_ESP32[k] = True
                                    p2.on()
                                    print(f"接続完了\n>>>>>>{wifi.ifconfig()}")
                                    sendIpAdress = wifi.ifconfig()[2]
                                    sendData = f"id={AP_SSID}&command_origin=resist&id_origin={AP_SSID}&route={AP_SSID}"
                                    resistSendSocket(sendIpAdress ,sendData)
                                    CURRENT_CONNECT_TO_ESP32[k] = True
                                    endFlag = True
                                    break
                                else:
                                    print(" . ",end="")
                                    utime.sleep(0.5)
                        if endFlag == True:
                            break
            
            if green.value() == 1:
                GREEN_ERROR_COUNT += 1
                if GREEN_ERROR_COUNT > 10:
                    p2.off()
                    blue.off()
                    red.off()
                    green.off()
                    machine.reset()
            else:
                GREEN_ERROR_COUNT = 0
            utime.sleep(2)
    except Exception as e:
        print(e)
        print(f"""
            !!!!!!! THREAD check_wifi()!!!!!
            再起動します
            """)
        
        p2.off()
        blue.off()
        red.off()
        green.off()
        machine.reset()


# Wi-Fiスキャン
# 研究室Wi-Fiに繋げられるなら繋げる
# 繋げられない場合はESP32を探す
def wifi_scan(CONTINUE_EXPETIMENT=False):
    if CONTINUE_EXPETIMENT == False:
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
            # if not ap.active():
            #     activate_AP()
            common_el = list()
            for el in wifiSsidList:
                if el in ENABLE_CONNECT_ESP32 and el in NEEDING_CONNECT_ESP32:
                    common_el.append(el)
                    print(f"接続可能なESP32を検知 ---> {el}")
            
            if common_el:
                for c_el in common_el:
                    if NEEDING_CONNECT_ESP32[c_el] == False:
                        print(f"Disconnect from currently connected {wifi.ifconfig()[0]}")
                        p2.off()
                        disconnect_report()
                        utime.sleep(WIFI_DISCONNECTION_TIME)
                        wifi.disconnect()
                        print("--- Wi-Fi 切断完了 ---")
                        utime.sleep(1)
                        esp_connect_wifi(c_el)
                        if check_thread_received_socket != True:
                            _thread.start_new_thread(received_socket,())
                            if DEFAULT_LAB_CONNECT:
                                _thread.start_new_thread(received_udp_socket,())
                        if check_thread_processRecv != True:
                            _thread.start_new_thread(processRecv,())
                        return False
            else:
                return 0
    else:
        wifiList = wifi.scan()
        wifiSsidList = list()
        for wl in wifiList:
            wifiSsidList.append(wl[0].decode("utf-8"))
        print(wifiSsidList)

        return wifiSsidList


### Wi-Fiを切断する際にESP32へ切断メッセージを送る ###
def disconnect_report():
    if not DEFAULT_LAB_CONNECT:
        ipAdress = wifi.ifconfig()[2]
        if ipAdress.split(".")[1] != "0" or ipAdress.split(".")[1] != 0:
            print(f" --- Sends a disconnect report to {wifi.ifconfig()[2]} during connection ---")
            
            sendData = f"id={AP_SSID}&command_origin=disconnect_report&id_origin={AP_SSID}"
            result = sendSocket(ipAdress,sendData,1)
            if result:
                print("!!!! --- Transmission completed >>> Start Wi-Fi disconnection process ---!!!!!")
            else:
                print("---Transmission failure >>> Start Wi-Fi disconnection process ---")

#### ソケット受信時のキューシステム ####
def writeRecvFile(writeData):
    global WRITE_FILE_COUNTER
    fileName = "recv" + str(WRITE_FILE_COUNTER) + ".txt"
    print(f"Write data : {writeData} ---> Write file name : {fileName}")
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
    iText = "Read file name : " + fileName
    
    if fileName in fileList:
            print("\n--- Detect incoming files == Start reading ---")
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
    ## 複数回同じ処理をしないようにするためのロック処理を実施
    lock_def_name = ""
    
    processCheckList("check_thread_processRecv",True)
    while True:
        try:
            fileData = readRecvFile()
            if fileData == 0:
                utime.sleep(0.5)
                continue
            fileDataSplit = fileData.split("?")
            fileData = fileDataSplit[0]
            addr = fileDataSplit[1]
            print(f"Processed data : {fileData} ,Received IP address[ = addr] : {addr}\n")
            
            fileDataProcessData = fileData.split("&")
            recvEsp32Id = ""
            command_origin = None
            id_origin = ""
            temporaryRoute = ""
            toSending = ""
            option = ""
            timeStamp = ""
            for fspd in fileDataProcessData:
                if fspd == " " or fspd == "":
                        pass
                else:
                    fspdSplit = fspd.split("=")
                    proKey = fspdSplit[0]
                    proValue = fspdSplit[1]
                    print(f"Process Data KEY : {proKey} VALUE : {proValue}")
                    if proKey == "id":
                        recvEsp32Id = proValue
                        print(f"ID of incoming ESP32 == {proValue}")
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
                        toSendingOriginal = proValue
                        pV = toSendingOriginal.split("+")
                        if ESP32_ID in pV:
                            toSending = ESP32_ID
                    if proKey == "weight":
                        weight = proValue
                    if proKey == "option":
                        option = proValue
                    if proKey == "timestamp":
                        timeStamp = proValue
            
            if id_origin != "server":
                if command_origin == "autowifi":
                    print(" ********** Emergency Processing : : : Propagate autowifi to other ESP32s ************")
                    for ipAdressN in CURRENT_CONNECTED_FROM_ESP32.values():
                        sendText = f"id={AP_SSID}&command_origin=autowifi"
                        sendSocket(ipAdressN,sendText)
                    print(" ********** Emergency processing : : : : Starts autowifi.py ************")
                    execfile("autowifi.py")
                if id_origin != recvEsp32Id:
                    ROUING_TABLE[id_origin] = recvEsp32Id
                    print(f" - - - Update routing table  - - - ")
                    for rk,rv in ROUING_TABLE.items():
                        print(f"To : {rk} <- - - To : {rv}")
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
                    print(" --- command_origin : translateの処理に入ります ---")
                    if toSendingOriginal == "server":
                        print(""" 
                            --- toSendingOriginal : enter server processing ---
                                --- Here you will perform the transfer process to the server on your own ---
                            """)
                        if DEFAULT_LAB_CONNECT:
                            httpBatteryPost(id_origin,battery,weight,timeStamp)
                        else:
                            msg = f"id={AP_SSID}&command_origin=translate&battery={str(battery)}&to=server&weight={str(weight)}&id_origin={id_origin}&timestamp={timeStamp}"
                            sendIpAdress = wifi.ifconfig()[2]
                            sendSocket(sendIpAdress,msg,refresh=True)
                if command_origin == "disconnect_report":
                    print(f"###  Disconnection report detection from {recvEsp32Id} ###")
                    if recvEsp32Id in CURRENT_CONNECTED_FROM_ESP32:
                        del CURRENT_CONNECTED_FROM_ESP32[recvEsp32Id]
                        print(f"""     Deletion execution complete
                            {CURRENT_CONNECTED_FROM_ESP32}""")
                    else:
                        print("CURRENT_CONNECTION_FROM_ESP32に {recvEsp32Id}は存在しません")
            else:
                # サーバから送信された場合の処理
                print("大変！！！サーバから接続されちゃった！！！！")
                if command_origin == "autowifi" and lock_def_name != "autowifi":
                    lock_def_name = "autowifi"
                    print(" ********** 緊急処理 : : : : 他のESP32にautowifiを伝搬します ************")
                    EXPERIMENT_ENABLE = False
                    print("******* EXPERIMATATIONを停止します ********")
                    # for ipAdressN in CURRENT_CONNECTED_FROM_ESP32.values():
                    #     sendText = f"id={AP_SSID}&command_origin=autowifi"
                    #     sendSocket(ipAdressN,sendText)
                    sendText = f"id={AP_SSID}&command_origin=autowifi&id_origin={id_origin}"
                    tcp_broadcast_send(sendText)
                    print(" ********** 緊急処理 : : : : autowifi.pyを起動します ************")
                    execfile("autowifi.py")
                elif command_origin == "experiment_start":
                    rewrite_reboot_experiment(True)
                    if toSending == "" or toSending == ESP32_ID:
                        if not check_thread_experiment:
                            print("\n- - - - 実験を開始します - - - - -")
                            sendText = f"id={AP_SSID}&command_origin={command_origin}&id_origin={id_origin}"
                            print("実験スタートを各ESP32に転送します")
                            # all_translate_to_ESP32(recvEsp32Id,sendText)1
                            tcp_broadcast_send(sendText)
                            EXPERIMENT_ENABLE = True
                            if not check_thread_experiment:
                                processCheckList("check_thread_experiment",True)
                                _thread.start_new_thread(measureCurrent,())
                        else:
                            print("---** 既にEXPETIMENTIONは起動しています **---")
                    else:
                        print("実験スタートを各ESP32に転送します")
                        tcp_broadcast_send(sendText)
                        
                elif command_origin == "experiment_stop":
                    rewrite_reboot_experiment(False)
                    if EXPERIMENT_ENABLE:
                        print("\n- - - - 実験を***停止***します - - - - -")
                        sendText = f"id={AP_SSID}&command_origin={command_origin}&id_origin={id_origin}"
                        tcp_broadcast_send(sendText)
                        EXPERIMENT_ENABLE = False
                        processCheckList("check_thread_experiment",False)
                    else:
                        print("- - - 既に実験は停止されているためスキップします - - - ")
                elif command_origin == "reboot":
                    print(" ********** 再起動 ************")
                    sendText = f"id={AP_SSID}&command_origin={command_origin}&id_origin={id_origin}"
                    if option != "force":
                        tcp_broadcast_send(sendText)
                    utime.sleep(2)
                    EXPERIMENT_ENABLE = False
                    p2.off()
                    blue.off()
                    red.off()
                    green.off()
                    machine.reset()
                elif command_origin == "reset_battery":
                    writeFileResetBatteryAmount()
                    lock_def_name = "reset_battery"
                    sendText = f"id={AP_SSID}&command_origin={command_origin}&id_origin={id_origin}"
                    tcp_broadcast_send(sendText)
                elif command_origin == "startAP":
                    print("--- AP 起動指令 ---")
                    lock_def_name = "startAP"
                    rewrite_reboot_ap(True)
                    if toSending == ESP32_ID:
                        # activate_AP()
                        ap.active(True)
                        red.on()
                    sendText = f"id={AP_SSID}&command_origin={command_origin}&id_origin={id_origin}&to={toSendingOriginal}"
                    tcp_broadcast_send(sendText)
                elif command_origin == "stopAP":
                    lock_def_name = "stopAP"
                    rewrite_reboot_ap(False)
                    sendText = f"id={AP_SSID}&command_origin={command_origin}&id_origin={id_origin}&to={toSendingOriginal}"
                    tcp_broadcast_send(sendText)
                    if toSending == ESP32_ID:
                        print("--- AP 停止指令 --- 三秒後にAPモードを停止します ---")
                        utime.sleep(3)
                        shutdownAP()
            utime.sleep(0.5)
        except Exception as e:
            print(f"""
            !!!!!!! THREAD process()にて問題発生 !!!!!!
            ======= {e} ========
            """)
            
    # except Exception as e:
    #     print(e)
    #     print(f"""
    #         !!!!!!! THREAD process()にて問題発生 !!!!!!
    #         再起動します
    #         """)
        
    #     p2.off()
    #     blue.off()
    #     red.off()
    #     green.off()
    #     machine.reset()

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
        print(" **** サーバへの送信が失敗しました (関数名 : resist_ESP32_httpPost) ****")
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
        print(" **** ERROR  (関数名 : httpPost) ****")
        print(e)
        print(" **** Repeat 3 s ****")
        utime.sleep(3)
        httpPost(url,sendText)

def udp_broadcast_send(sendData,timeout = 3):
    try:
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
    except Exception as e:
        blue.off()
        print(" **** UDP BROUAD-CAST ERROR ****")
        print(e)

def tcp_broadcast_send(sendData,timeout = 3):
    global CURRENT_CONNECTED_FROM_ESP32
    print(f"SENDING ALL ESP32")
    for k,v in CURRENT_CONNECTED_FROM_ESP32.items():
        try:
            print("----")
            print(f"送信先 : {k} ({v})")
            sendSocket_tcp_broadcast(v,sendData)
        except Exception as e:
            blue.off()
            # 送信できない場合エラーを送信
            ERROR_CONNECT_ESP32[k] = True
            print(f" **** ERROR >>> {k} ({v}) ****")
            del CURRENT_CONNECTED_FROM_ESP32[k]
            print(e)

def sendSocket_tcp_broadcast(ipAdress,sendData):
    print(f"SEND DATA : {sendData} ---> SEND ADDRESS : {ipAdress}")
    blue.on()
    s = socket.socket()
    s.connect(socket.getaddrinfo(ipAdress,PORT)[0][-1])
    s.send(sendData)
    s.close()
    blue.off()
    print("Sending Complete!")

def sendSocket(ipAdress,sendData,timeout = 3,refresh=False):
    count = 0
    if ipAdress.split(".")[1] == "0" or ipAdress.split(".")[1] == 0:
        print(f"IPアドレス {ipAdress}が定義されていないためスキップ")
        return "IP_NOT DEFINE"
    while count < timeout:
        try:
            print(f"SEND DATA : {sendData} ---> SEND ADDRESS : {ipAdress}")
            blue.on()
            s = socket.socket()
            s.connect(socket.getaddrinfo(ipAdress,PORT)[0][-1])
            s.send(sendData)
            s.close()
            blue.off()
            print("Sending Complete!")
            return True
        except Exception as e:
            count += 1
            print("\n **** ERROR (関数名 : sendSocket) ****")
            print(e)
            print(" **** Repeat 5 s ****")
            if refresh:
                ipAdress = wifi.ifconfig()[2]
            utime.sleep(5)
    return False

def resistSendSocket(ipAdress,sendData,timeout = 3):
    count = 0
    # if ipAdress.split(".")[1] != "0" or ipAdress.split(".")[1] != 0:
    #     print(f"IPアドレス {ipAdress}が定義されていないためスキップ")
    #     return "IP_NOT DEFINE"
    while count < timeout:
        try:
            print(f"SEND DATA : {sendData} ---> SEND ADDRESS : {ipAdress}")
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
            print("\n **** ERROR (関数名 : resistSendSocket) ****")
            print(e)
            print(" **** Repeat 5 s ****")
            utime.sleep(5)
            ipAdress = wifi.ifconfig()[2]

def transfer_sendSocket(ipAdress,sendData,timeout = 1):
    count = 0
    if ipAdress.split(".")[1] == "0" or ipAdress.split(".")[1] == 0:
        print(f"IPアドレス {ipAdress}が定義されていないためスキップ")
        return "IP_NOT DEFINE"
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
            print("\n **** ソケット送信で問題が発生 (関数名 : transfer_sendSocket) ****")
            print(e)
            print(" **** ３秒後に再度やり直します ****")
            utime.sleep(3)
            

def received_socket():
    beforeReceivedData = ""
    listenSocket = socket.socket()
    listenSocket.bind(('', PORT))
    listenSocket.listen(5)
    listenSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listenSocket.settimeout(10)
    processCheckList("check_thread_received_socket",True)
    print('tcp waiting...')
    while True:
        try:
            
            conn, addr = listenSocket.accept()
            print("accepting.........")
            green.on()
            print("green.on()")
            addr = addr[0]
            print("addr = addr[0]")
            data = conn.recv(1024)
            print("data = conn.recv(1024)")
            conn.close()
            print("conn.close()")
            str_data = data.decode()
            if beforeReceivedData != str_data:
                beforeReceivedData = str_data
                print(f"{addr} より接続 ---> 受信データ : {str_data}")
                str_data += "?" + addr
                writeRecvFile(str_data)
                green.off()
            else:
                print(f"-- - Skip command because it is the same as the last connected data ({beforeReceivedData}) - --")
                green.off()
        except OSError as e:
            if e.args[0] == 116: # 110 is the error code for timeout
                print("""
                    Timeout occurred, no connection was made
                    """)
            else:
                print(e)
            green.off()
        except Exception as ea:
            print(ea)
            print(f"""
                !!!!!!! THREAD Received_socket()!!!!!
                """)
            green.off()
            
        # if wifi.ifconfig()[0].split(".")[2] != "100":
        #     print("!!!!!!! CDSLへの接続を確認できず !!!!!!")
        #     p2.off()
        #     blue.off()
        #     red.off()
        #     green.off()
        #     machine.reset()
        

# UDPソケット受信
def received_udp_socket():
    beforeReceivedData = ""
    # UDPソケットを作成する
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # ブロードキャストアドレスを受信するためにバインドする
    sock.bind(('0.0.0.0', 8888))
    errorCount = 0
    while True:
        try:
            print("accepting..........")
            # データを受信する
            conn, addr = sock.recvfrom(1024)
            green.on()
            addr = addr[0]
            data = conn
            str_data = data.decode()
            print(f"Connect from {addr} ---> Received data : {str_data}")
            str_data += "?" + addr
            writeRecvFile(str_data)
            green.off()
            # if beforeReceivedData != str_data:
            #     beforeReceivedData = str_data
            #     print(f"{addr} より接続 ---> 受信データ : {str_data}")
            #     str_data += "?" + addr
            #     writeRecvFile(str_data)
            #     green.off()
            # else:
            #     print(f"-- - 前回接続されたデータ ({beforeReceivedData})と同じためコマンドをスキップします - --")
            #     green.off()
            utime.sleep(1)
            errorCount = 0
        except Exception as e:
            green.off()
            errorCount += 1
            print(e)
            print("ERROR")
            if errorCount > 3:
                break
    # except Exception as e:
    #     print(e)
    #     print(f"""
    #         !!!!!!! THREAD received_udp_socket()にて問題発生 !!!!!!
    #         再起動します
    #         """)
        
    #     p2.off()
    #     blue.off()
    #     red.off()
    #     green.off()
    #     machine.reset()

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
        print("\nComplete all ESP32 connections and updates")
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

    print("----- Update ESP32 list of scheduled connections -----")
    for k,v in REQUIRE_CONNECTED_ESP32.items():
        print(f"{k}  :   {v}")

def check_connected_from_esp32():
    global REQUIRE_CONNECTED_ESP32
    if False not in REQUIRE_CONNECTED_ESP32.values():
        print("\nConfirm connection with all ESP32s to be connected")
        if not check_esp_connected:
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
                if DEFAULT_LAB_CONNECT:
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
            resistSendSocket(sendIpAdress,sendData)
            processCheckList("check_resist",True)
            update_init_remaining_esp32()
            check_init_remaing_esp32()
        else:
            print("処理せず")
    else:
        init_network()


def httpBatteryPost(idName,sendingData,weight,timeStamp):
    global BATTERY
    url = "http://192.168.100.236:5000/battery_recieve"
    try:
        blue.on()
        print(f" --- Send the remaining battery data to the server >>>> ESP32 : {idName} , remaining battery data : {sendingData} , weight : {weight}---")
                
        sendData = {
            "transfer_espid" : idName,
            "data" : sendingData,
            "espid" : AP_SSID,
            "weight" : str(weight),
            "timestamp" : str(timeStamp)
        }
        
        url += "?"
        
        for sdk,sdv in sendData.items():
            url += sdk + "=" + sdv + "&"
        print(url)
        res = urequests.get(url)
        print("Status code from server：", res.status_code)
        res.close()
        blue.off()
    except Exception as e:
        print(e)
        print("@@@@@ Failed to send to server. Skipping. @@@@@")

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

# 積層重み
LAMI_COST = 0
def measureCurrent():
    global BATTERY
    MEASURE_SLEEP_TIMER = 60
    count_timestamp = 0
    try:
        while EXPERIMENT_ENABLE:
            count = 0
            sumCurrent = 0
            while count < MEASURE_SLEEP_TIMER and EXPERIMENT_ENABLE:
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
                        calibrationN = -20 * randomNumber
                    else:
                        calibrationN = 20 * randomNumber / 2
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
                # f = open('current.csv', 'a')
                # f.write(str(currentData))
                # f.close() 
                count += 1
                utime.sleep(1)
                
            sumCurrent /= MEASURE_SLEEP_TIMER
            
            print(f"---- Average power consumption during 60 seconds : {sumCurrent}[mA] Remaining battery power : {battery - sumCurrent}[mAh] ----")
            
            battery -= sumCurrent
            if battery < 0.0:
                battery = 0.0
            batteryData = "%.3f" % battery
            batteryData += "\n"
            if DEFAULT_LAB_CONNECT == True:
                httpBatteryPost(AP_SSID,str(battery) ,str(LAMI_COST),str(count_timestamp))
            else:
                msg = f"id={AP_SSID}&command_origin=translate&battery={str(battery)}&to=server&weight={str(LAMI_COST)}&id_origin={AP_SSID}&timestamp={str(count_timestamp)}"
                sendIpAdress = wifi.ifconfig()[2]
                sendSocket(sendIpAdress,msg,refresh=True)
            writeFileBattery(str(battery))
            count_timestamp += 1
            # f = open('battery.csv', 'a')
            # f.write(str(batteryData))
            # f.close()
    except Exception as e:
        print(e)
        print(f"""
            !!!!!!! THREAD measureCurrent()にて問題発生 !!!!!!
            再起動します
            """)
        
        p2.off()
        blue.off()
        red.off()
        green.off()
        machine.reset()


def continue_experiment_network():
    if DEFAULT_LAB_CONNECT:
        _thread.start_new_thread(received_socket,())
        _thread.start_new_thread(received_udp_socket,())
        _thread.start_new_thread(processRecv,())
        
        print("""
            --- スレッド起動シーケンス ---
            """)
        wifi_scan()
        
        if REBOOT_AP:
            activate_AP()
        
        processCheckList("check_thread_experiment",True)
        _thread.start_new_thread(measureCurrent,())
    else:
        print("""
            --- スレッド起動シーケンス ---
            """)
        _thread.start_new_thread(received_socket,())
        _thread.start_new_thread(processRecv,())
        
        
        print("""
            --- Wi-Fi接続シーケンス ---
            """)
        wifiSsidList = wifi_scan(True)
        for i in ENABLE_CONNECT_ESP32:
            for wsl in wifiSsidList:
                if i == wsl:
                    print(f"接続可能なWi-Fi : {i} を発見．接続します")
                    esp_connect_wifi(i)
        
        if REBOOT_AP:
            activate_AP()
        _thread.start_new_thread(check_wifi_thread,())
        
        processCheckList("check_thread_experiment",True)
        _thread.start_new_thread(measureCurrent,())

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
    
    # checkList = f"""
    # booting             :   {check_booting}
    # wi-fi               :   {check_wifi}
    # eneble AP           :   {check_ap}
    # RESIST              :   {check_resist}
    # ESP_CONNECT_COMP    :   {check_esp_allconnect}
    # CONNECTED_ESP_COMP  :   {check_esp_connected}
    
    # =THEAD=
    # receiced_socket()   :   {check_thread_received_socket}
    # processRecv()       :   {check_thread_processRecv}
    # checkWifi()         :   {check_thread_checkWifi}
    # experiment()        :   {check_thread_experiment}
    # """
    
    checkList = ""
    
    print(checkList)
    
##############


def main():
    processCheckList("check_booting",True)
    #execfile("autowifi.py")
    
    print(" --- キャッシュデータ削除処理 ---")
    deleteCashFile()
    
    if REBOOT_EXPERIMENT_JUDGE:
        print("""
            ーーー　実験を再開します　ーーー
            """)
        continue_experiment_network()
    else:
        print("init_flag.pyを実行")
        execfile("init_flag.py")
        init_network()
        # if not check_thread_checkWifi:
        #     _thread.start_new_thread(check_wifi_thread,())
        
        print("\n - - - - ネットワークの初期化完了 - - - - - -")
        if wifi.ifconfig()[0].split(".")[2] != "100":
            sendIpAdress = wifi.ifconfig()[2]
            sendData = f"id={AP_SSID}&command_origin=resist_complete&id_origin={AP_SSID}&route={AP_SSID}"
            sendSocket(sendIpAdress,sendData)
            print(f"""
                --- --- --- RESIST_COMPLETE 送信完了 --- --- ---\n
            """)
        red.off()
        if not ap.active():
            print("--- Wi-Fi access point mode activated ----")
            activate_AP()
        for _ in range(5):
            green.on()
            utime.sleep(0.1)
            green.off()
            utime.sleep(0.1)
        green.off()
        red.off()
    
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