#!/usr/bin/env python3

from lxml import etree
from io import StringIO
import subprocess
import threading
from time import sleep
import queue
import re

from concurrent.futures import ThreadPoolExecutor as TPE

parser = etree.HTMLParser()

fileName_echoOut = "vmOut.txt"
fileNameRead = "youneedwind.html"
vpingName = "./vping_c3_o5"
vspeedName = './vspeed_10s'

maxPingThreadNum = 170
maxSpeedTestNum = 20
pLQ = 0     # ping listener quit
sLQ = 0     # speedTest listener quit

vmQueue = queue.Queue()    # Transfering String data type
vmPingQueue = queue.Queue() # Transfering String data type
vmTestQueue = queue.Queue() # Transfering List data type

def runPing():
    vmStr = vmQueue.get()
    pingCmd = [vpingName, vmStr]
    runPing = subprocess.run(pingCmd, capture_output=True, text=True)
    try:
        avgPing = re.findall(r"\d+\/(\d+)\/\d+",runPing.stdout.split('\n')[15])
        if int(avgPing[0]) != 0:
            vmPingQueue.put(vmStr)
            print('ping got one!')
    except Exception as e:
        pass

def runSpeedTest():
    vmStr = vmPingQueue.get()
    print('st in run')
    testCmd = [vspeedName, vmStr]
    runTest = subprocess.run(testCmd, capture_output=True, text=True)
    try: 
        downStr = runTest.stdout.split('\n')[13]
        downSpeed = re.findall(r"\d+.\d+", downStr)
        upStr = runTest.stdout.split('\n')[14]
        upSpeed = re.findall(r"\d+.\d+", upStr)
        vmTestQueue.put([vmStr, float(downSpeed[0]), float(upSpeed[0])])
        print("st got one")
    except Exception as e: 
        pass
    print('st end')


def readFromYou():
    with open(fileNameRead, 'r') as f:
        data = f.read()
        tree = etree.parse(StringIO(data), parser)
        parent = tree.xpath('//*[@id="post-box"]/div/section/div[2]/table/tbody')
        trs = parent[0].xpath('tr')
        for _tr in trs:
            vStr = (_tr.xpath('td/a')[0].attrib['data-raw'])
            vmQueue.put(vStr)

def pingListener():
    print('pingListener start')
    global pLQ
    executor = TPE(max_workers = maxPingThreadNum) 
    while True:
        if vmQueue.empty() is not True:
            pThread = executor.submit(runPing)
            sleep(0.05)
        else:
            print("ping is shutting down...")
            executor.shutdown(wait = True)
            break
    pLQ = 1
    print('pingListener stop')

def speedTestListener():
    print('speedTestListener start')
    global pLQ, sLQ
    executor = TPE(maxSpeedTestNum) 
    while True:
        if vmPingQueue.empty() is not True:
            sThread = executor.submit(runSpeedTest)
            sleep(2)
        else:
            if pLQ == 1:
                print('st is shutting down...')
                executor.shutdown(wait = True)
                break
            sleep(3)
    sLQ = 1
    print('speedTestListener stop')

def subscriptionDecoding():
    pass

def sorting():
    vmessWithSpeed.sort(key=lambda down: down[1], reverse = True)

def echoOut(fil):
    vmLst = vmTestQueue.get()
    vmStrWithDownUp = vmLst[0] + '\nDown: ' +str(vmLst[1]) + ' Up: ' + str(vmLst[2]) + '\n'
    print(vmStrWithDownUp)
    fil.write(vmStrWithDownUp)


if __name__ == '__main__':

    readFromYou()

    pListenerEx = TPE(1)
    pL = pListenerEx.submit(pingListener)

    sListenerEx = TPE(1)
    sL = sListenerEx.submit(speedTestListener)

    try:
        echoOutFil = open(fileName_echoOut, 'a')
        while True:
            if vmTestQueue.empty() is not True:
                echoOut(echoOutFil)
                sleep(5)
            else:
                if sLQ == 1:
                    pListenerEx.shutdown()
                    sListenerEx.shutdown()
                    break
                sleep(5)
        echoOutFil.close()
    except Exception as e:
        print("Error: echo file: ", e)

