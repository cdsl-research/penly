import sys
import subprocess

args = sys.argv

espIpList = ["192.168.100.158","192.168.100.164","192.168.100.177","192.168.100.130"]

# espIpDict = {
#     "B" : "192.168.100.158",
#     "A1" : "192.168.100.164",
#     "A2" : "192.168.100.177",
#     "A3" : "192.168.100.130",
#     "A4" : "192.168.100.92",
#     "A5" : "192.168.100.122",
#     "sA" : "192.168.100.138",
#     "sB" : "192.168.100.124",
#     "sC" : "192.168.100.173",
#     "sD" : "192.168.100.147",
#     "sE" : "192.168.100.46",
#     "sF" : "192.168.100.55"
# }

espIpDict = {
    "A" : "192.168.100.158",
    "B" : "192.168.100.164",
    "C" : "192.168.100.177",
    "D" : "192.168.100.130",
    "E" : "192.168.100.92",
    "F" : "192.168.100.122",
    "G" : "192.168.100.138",
    "H" : "192.168.100.124",
    "I" : "192.168.100.173",
    "J" : "192.168.100.147",
    "K" : "192.168.100.46",
    "L" : "192.168.100.55"
}

fileList = [
    "boot.py",
    "autowifi.py",
    "wifi-password.py",
    "battery.txt",
    "init_flag.py",
    "main_frame.py",
    "ctime.py"
]


def main():
    # toSendID = str(args[1])
    
    for k ,v in espIpDict.items():
        print(f"送信先 : {k}")
        toSendID = k
        ipAddress = espIpDict[toSendID]
        print(f"{ipAddress}へ送信します")
        setIpCode = "upydev config -t " + ipAddress + " -p cdsl"
        programFile = f"original_id/{toSendID}/id.py"
        print(f"送信ファイルは[{programFile}]です")
        setSendProgramCode = "upydev put -rst f -f " + programFile
        cp = subprocess.run(setIpCode, shell=True)
        print("returncode:", cp.returncode)
        cp = subprocess.run(setSendProgramCode,shell=True)
        # print("returncode:", cp.returncode)
        
        print("---- 完了 ----")
if __name__ == "__main__":
    main()