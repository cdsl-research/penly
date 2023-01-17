import sys
import subprocess

args = sys.argv

espIpList = ["192.168.100.158","192.168.100.164","192.168.100.177","192.168.100.130"]
# espIpDict = {
#     "B" : "192.168.100.158",
#     "A1" : "192.168.100.164",
#     "A2" : "192.168.100.177",
#     "A3" : "192.168.100.130",
#     "A4" : "192.168.100.66",
#     "A5" : "192.168.100.122",
#     "N" : "192.168.100.234",
#     "N2" : "192.168.100.178",
#     "L" : "192.168.100.65",
#     "sA" : "192.168.100.138",
#     "sB" : "192.168.100.124",
#     "sC" : "192.168.100.173",
#     "sD" : "192.168.100.147",
#     "sE" : "192.168.100.46",
#     "sF" : "192.168.100.55"
# }

espIpDict = {
    "B" : "192.168.100.158",
    "A1" : "192.168.100.164",
    "A2" : "192.168.100.177",
    "A3" : "192.168.100.130",
    "A4" : "192.168.100.92",
    "A5" : "192.168.100.122",
    "sA" : "192.168.100.138",
    "sB" : "192.168.100.124",
    "sC" : "192.168.100.173",
    "sD" : "192.168.100.147",
    "sE" : "192.168.100.46",
    "sF" : "192.168.100.55"
}

# espIpDict = {
#     "B" : "192.168.100.158",
#     "A1" : "192.168.100.164",
#     "A2" : "192.168.100.177",
#     "A5" : "192.168.100.122",
#     "sA" : "192.168.100.138"
# }



#subprocess.run("ls -l", shell=True)

SEND_CHECK_LIST = dict()

def init_checklist():
    for k, v in espIpDict.items():
        SEND_CHECK_LIST[k] = False

def print_checklist():
    print("---")
    for k, v in SEND_CHECK_LIST.items():
        print(f"{k} : {v}")
    print("---")

def allSendProgram():
    init_checklist()
    programFile = str(args[1])
    print(f"送信ファイルは[{programFile}]です")
    # for espName in espIpList:
    for k,espName in espIpDict.items():
        print("\n\n",espName,"へ送信します")
        try:
            setIpCode = "upydev config -t " + str(espName) + " -p cdsl"
            setSendProgramCode = "upydev put -rst f -f " + programFile
            cp = subprocess.run(setIpCode, shell=True)
            print("returncode:", cp.returncode)
            cp = subprocess.run(setSendProgramCode,shell=True)
            print("returncode:", cp.returncode)
            SEND_CHECK_LIST[k] = True
            print_checklist()
        except:
            print("error")
            print_checklist()

def yamamotoSend(flagSelect):
    ipAddress = "192.168.100.88"
    programFile = str(args[1])
    print(f"送信ファイルは[{programFile}]です")
    print(f"{ipAddress}へ送信します")
    setIpCode = "upydev config -t " + str(ipAddress) + " -p 1202"
    setSendProgramCode = "upydev put -rst f -f " + programFile
    cp = subprocess.run(setIpCode, shell=True)
    print("returncode:", cp.returncode)
    cp = subprocess.run(setSendProgramCode,shell=True)
    print("returncode:", cp.returncode)
    
def saboSend(flagSelect):
    ipAddress = "192.168.100.196"
    programFile = str(args[1])
    print(f"送信ファイルは[{programFile}]です")
    print(f"{ipAddress}へ送信します")
    setIpCode = "upydev config -t " + str(ipAddress) + " -p cdsl"
    setSendProgramCode = "upydev put -rst f -f " + programFile
    cp = subprocess.run(setIpCode, shell=True)
    print("returncode:", cp.returncode)
    cp = subprocess.run(setSendProgramCode,shell=True)
    print("returncode:", cp.returncode)
    
def freeSend():
    ipInput = input("192.168.xxx.xxx >>> ")
    ipAddress = "192.168." + ipInput
    programFile = str(args[1])
    print(f"送信ファイルは[{programFile}]です")
    print(f"{ipAddress}へ送信します")
    setIpCode = "upydev config -t " + str(ipAddress) + " -p cdsl"
    setSendProgramCode = "upydev put " + programFile
    cp = subprocess.run(setIpCode, shell=True)
    print("returncode:", cp.returncode)
    cp = subprocess.run(setSendProgramCode,shell=True)
    print("returncode:", cp.returncode)

def selectSendProgram():
    selectQ = """
    - B
    - A1
    - A2
    - A3
    - A4
    - A5
    - N
    - N2
    - L
    - sE
    - 山本 : 5
    - sabo : 6
    - free : 7
    """
    print(selectQ)
    flagSelect = input(">>> ")
    
    if flagSelect == "5":
        yamamotoSend(int(flagSelect))
    elif flagSelect == "6":
        saboSend(int(flagSelect))
    elif flagSelect == "7":
        freeSend()
    else:
        ipAddress = espIpDict[flagSelect]
        programFile = str(args[1])
        print(f"送信ファイルは[{programFile}]です")
        print(f"{ipAddress}へ送信します")
        setIpCode = "upydev config -t " + ipAddress + " -p cdsl"
        setSendProgramCode = "upydev put -rst f -f " + programFile
        cp = subprocess.run(setIpCode, shell=True)
        print("returncode:", cp.returncode)
        cp = subprocess.run(setSendProgramCode,shell=True)
        print("returncode:", cp.returncode)
        
        
if __name__ == "__main__":
    Q = """
    全てのデバイスへの送信 : 1
    個別のデバイスへの送信 : 2
    """
    print(Q)
    flag = int(input(">>> "))
    if flag == 1:
        allSendProgram()
    elif flag == 2:
        selectSendProgram()
    