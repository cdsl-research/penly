import sys
import subprocess

args = sys.argv

espIpList = ["192.168.100.158","192.168.100.164","192.168.100.177","192.168.100.130"]
espIpDict = {
    "B" : "192.168.100.158",
    "A1" : "192.168.100.164",
    "A2" : "192.168.100.177",
    "A3" : "192.168.100.130",
    "A4" : "192.168.100.66",
    "A5" : "192.168.100.122",
    "N" : "192.168.100.234",
    "N2" : "192.168.100.178",
    "L" : "192.168.100.65",
    "sA" : "192.168.100.138",
    "sB" : "192.168.100.124",
    "sC" : "192.168.100.173",
    "sD" : "192.168.100.147",
    "sE" : "192.168.100.46",
    "sF" : "192.168.100.55"
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
    toSendID = str(args[1])
    
    
    ipAddress = espIpDict[toSendID]
    print(f"{ipAddress}へ送信します")
    setIpCode = "upydev config -t " + ipAddress + " -p cdsl"
    for fileName in fileList:
        programFile = fileName
        print(f"送信ファイルは[{programFile}]です")
        setSendProgramCode = "upydev put -rst f -f " + programFile
        cp = subprocess.run(setIpCode, shell=True)
        print("returncode:", cp.returncode)
        cp = subprocess.run(setSendProgramCode,shell=True)
        print("returncode:", cp.returncode)
    
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