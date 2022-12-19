import sys
import subprocess

args = sys.argv

espIpList = ["192.168.100.87","192.168.100.164","192.168.100.218","192.168.100.82","192.168.100.228"]
espIpDict = {
    "B" : "192.168.100.158",
    "A1" : "192.168.100.164",
    "A2" : "192.168.100.177",
    "A3" : "192.168.100.82",
    "A4" : "192.168.100.66",
    "A5" : "192.168.100.73",
    "N" : "192.168.100.234",
    "N2" : "192.168.100.178",
    "L" : "192.168.100.65"
}

#subprocess.run("ls -l", shell=True)

def allSendProgram():
    programFile = str(args[1])
    print(f"送信ファイルは[{programFile}]です")
    for espName in espIpList:
        print("\n\n",espName,"へ送信します")
        setIpCode = "upydev config -t " + str(espName) + " -p cdsl"
        setSendProgramCode = "upydev put -rst f -f " + programFile
        cp = subprocess.run(setIpCode, shell=True)
        print("returncode:", cp.returncode)
        cp = subprocess.run(setSendProgramCode,shell=True)
        print("returncode:", cp.returncode)

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
    