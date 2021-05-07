#!/usr/bin/env python3

from lxml import etree
from io import StringIO
import subprocess
from time import sleep
import queue
import re
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor as TPE
from concurrent.futures import as_completed
from base64 import b64decode

fileName_echoOut = "vmOut.txt"
fileNameRead = "youneedwind.html"
fileNameJsnOut = 'x.json'
vpingName = "./vping"
vspeedName = './vspeed'

pCount = '3'
pTimeout = '5'
sTimeout = '15'

subscribe_urls = ['https://raw.githubusercontent.com/ssrsub/ssr/master/v2ray',
                    'https://jiang.netlify.com',
                    'https://raw.githubusercontent.com/freefq/free/master/v2']

maxPingThreadNum = 8
maxSpeedTestNum = 2

parser = etree.HTMLParser()

vmQueue = queue.Queue()    # Transfering String data type       subs -> ping
vmPingQueue = queue.Queue() # Transfering String data type      ping -> speedTest
vmTestQueue = queue.Queue() # Transfering List data type        speedTest good

# global status flag, No modifying!
pLS = 0     # ping listener quit status
sLS = 0     # speedTest listener quit status
pLC = 0

vmes = []
vmNoDup = []
vmesOut = []

def dataPipeIsEmpty():
    if vmQueue.empty() and vmPingQueue.empty() and vmTestQueue.empty() is True:
        return True
    else:
        return False

def subsDecoding():
    global vmes
    for url in subscribe_urls: 
        try:
            return_content = urlopen(url).read()
            share_links = b64decode(return_content).decode('utf-8').splitlines()
            for vm in share_links:
                if vm.split("://")[0] == "vmess":
                    vmes.append(vm.strip())
            print('subs ', url)
            print('got ', len(share_links), 'vmesses')
        except Exception as e:
            print('Read subscription fail: ', e)

def readFromYou():
    global vmes
    with open(fileNameRead, 'r') as f:
        data = f.read()
        tree = etree.parse(StringIO(data), parser)
        parent = tree.xpath('//*[@id="post-box"]/div/section/div[2]/table/tbody')
        trs = parent[0].xpath('tr')
        for _tr in trs:
            vStr = (_tr.xpath('td/a')[0].attrib['data-raw'])
            if vStr.split("://")[0] == "vmess":
                vmes.append(vStr.strip())

def runPing(vmStr):
    try:
        pingCmd = [vpingName, '-c', pCount, '-o', pTimeout, vmStr]
        runPing = subprocess.run(pingCmd, capture_output=True, text=True)
        avgPing = re.findall(r"\d+\/(\d+)\/\d+",runPing.stdout.split('\n')[int(pCount) + 12])
        if int(avgPing[0]) != 0 and int(avgPing[0]) <= 2500:
            vmPingQueue.put(vmStr)
            print("ping got one")
            return 0
    except Exception as e:
        print("runPing:", e)
    return 1

def runSpeedTest(vmStr):
    try: 
        testCmd = [vspeedName, '-t', sTimeout, vmStr]
        runTest = subprocess.run(testCmd, capture_output=True, text=True)
        downStr = runTest.stdout.split('\n')[13]
        location = re.findall(r"\((.*)\)", runTest.stdout.split('\n')[11])[0]
        downSpeed = re.findall(r"\d+.\d+", downStr)
        upStr = runTest.stdout.split('\n')[14]
        upSpeed = re.findall(r"\d+.\d+", upStr)
        vmTestQueue.put([vmStr, float(downSpeed[0]), float(upSpeed[0]), location])
        print("st got one")
    except Exception as e: 
        print("runSpeed:", e)

def pingListener():
    print('pingListener start')
    global pLS, pLC
    pLS = 1
    executor = TPE(max_workers = maxPingThreadNum) 
    futures = [executor.submit(runPing, vm) for vm in vmNoDup]
    print([x.result() for x in as_completed(futures)])

#   while True:
#        try:
#            vmStr = vmQueue.get(block = False)
#            vmQueue.task_done()
#            pLC = pLC + 1
#            pThread = executor.submit(runPing, vmStr)
#        except Exception as e:
#            print(e)
#            print('waitting for more vmesses...')
#            break
    executor.shutdown(wait = True)
    pLS = 0
    print('pingListener stop')

def speedTestListener():
    print('speedTestListener start')
    global pLS, sLS
    sLS = 1
    executor = TPE(maxSpeedTestNum) 
    while True:
        try:
            vmStr = vmPingQueue.get(block = False)
            vmPingQueue.task_done()
            sThread = executor.submit(runSpeedTest, vmStr)
        except Exception as e:
            if pLS == 0:
                break
            sleep(5)
    executor.shutdown(wait = True)
    sLS = 0
    print('speedTestListener stop')

def writeOutListener():
    global vmesOut
    try:
        while True:
            if vmTestQueue.empty() is not True:
                vmLst = vmTestQueue.get()
                vmTestQueue.task_done()
                vmesOut.append(vmLst)
                vmStr = vmLst[0] + '\nDown: ' +str(vmLst[1]) + ' Up: ' + str(vmLst[2]) + ' location: ' + vmLst[3]
                print(vmStr)
                sleep(5)
            else:
                if dataPipeIsEmpty() is True:
                    break
                sleep(5)
    except Exception as e:
        print("Error: writeOutListener ", e)
        print("quite")
    print('writeOutListener stop')


def sort(vmLst):
    vmLst.sort(key=lambda down: down[1], reverse = True)
    return vmLst

def vm2str(vmStr):
    j = subprocess.run(['./vm2jsn.py', vmStr], capture_output=True, text=True)
    return str(j.stdout)

def xrayThread(vmStr):
    with open(fileNameJsnOut, 'w') as f:
        vm2jsn = subprocess.run(['./vm2jsn.py', vmStr], capture_output=True, text=True)
        s = str(vm2jsn.stdout) 
        f.write(s)
    print('start xray...')
    xrayCmd = ['./xray', '-c', fileNameJsnOut]
    runXray = subprocess.Popen(xrayCmd, stdout=subprocess.PIPE)
    while True:
        output = runXray.stdout.readline()
        if runXray.poll() is not None:
            print('poll is None')
            break
        if output:
            print(output.strip())
    # runXray.terminate() to terminate the subprocess

def vmFullPullandCheck():
    readFromYou()
    subsDecoding()
    for vm in vmes:
        vmQueue.put(vm)
    while dataPipeIsEmpty() is not True:
        sleep(5)
    print("first crawling done")
    vmGood = sort(vmesOut)
    vmesOut.clear()
    return 0

def checkAvailability(vmLst):
    global vmesOut
    for vm in vmLst:
        vmQueue.put(vmStr)
    while dataPipeIsEmpty() is not True:
        sleep(5)
    vmGood = sort(vmesOut)
    vmesOut.clear()
    return vmGood

def haha():
    global vmesOut
    vmFullPullandCheck()
    vmGood = sort(vmesOut)
    vmesOut.clear()
    vmLst = vmesOut.pop()


if __name__ == '__main__':
    readFromYou()
    subsDecoding()

    with open(fileName_echoOut, 'r') as f:
        for vm in f.readlines():
            if vm.split("://")[0] == "vmess":
                vmes.append(vm.strip())
    print("there are", len(vmes), "vmesses in total")
    vmNoDup = list(set(vmes))
    print(len(vmNoDup), "in no duplicate")
    for vm in vmNoDup:
        vmQueue.put(vm)

    pListenerEx = TPE(1)
    pL = pListenerEx.submit(pingListener)

    sListenerEx = TPE(1)
    sL = sListenerEx.submit(speedTestListener)
#
    sleep(5)
    try:
        while True:
            if vmTestQueue.empty() is not True:
                vmLst = vmTestQueue.get()
                vmTestQueue.task_done()
                vmesOut.append(vmLst)
                vmStr = vmLst[0] + '\nDown: ' +str(vmLst[1]) + ' Up: ' + str(vmLst[2]) + ' location: ' + vmLst[3]
                print(vmStr)
                sleep(5)
            else:
                if sLS == 0:
                    break
                sleep(5)
    except Exception as e:
        print("Error: writeOutListener ", e)
        print("quite")
    print('writeOutListener stop')

    vmesOut = sort(vmesOut)

    for index, vm in enumerate(vmesOut):
        with open("data/" + str(index) + ".json", 'w') as f:
            f.write(vm2str(vm[0]))
    with open(fileName_echoOut, 'w') as f:
        for vmLst in vmesOut:
            f.writelines(vmLst[0] + '\nDown: ' +str(vmLst[1]) + ' Up: ' + str(vmLst[2]) + ' location: ' + vmLst[3] + '\n')
#    vmLst = vmesOut.pop()
#    xrayThread(vmLst[0])


