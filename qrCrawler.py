#!/usr/bin/env python3

from lxml import etree
from io import StringIO
import subprocess
from time import sleep
import queue
import re
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor as TPE
from base64 import b64decode

fileName_echoOut = "vmOut.txt"
fileNameRead = "youneedwind.html"
fileNameJsnOut = 'x.json'
vpingName = "./vping"
vspeedName = './vspeed'

pCount = '5'
pTimeout = '5'
sTimeout = '10'

subscribe_urls = ['https://raw.githubusercontent.com/ssrsub/ssr/master/v2ray',
                    'https://jiang.netlify.com',
                    'https://raw.githubusercontent.com/freefq/free/master/v2']

maxPingThreadNum = 100
maxSpeedTestNum = 20

parser = etree.HTMLParser()

vmQueue = queue.Queue()    # Transfering String data type       subs -> ping
vmPingQueue = queue.Queue() # Transfering String data type      ping -> speedTest
vmTestQueue = queue.Queue() # Transfering List data type        speedTest good

# global status flag, No modifying!
pLQ = 0     # ping listener quit status
sLQ = 0     # speedTest listener quit status

vmes = []
vmesOut = []

def subscriptionDecoding():
    for url in subscribe_urls: 
        try:
            return_content = urlopen(url).read()
            share_links = b64decode(return_content).decode('utf-8').splitlines()
            for vm in share_links:
                vmes.append(vm)
            print('subs ', url)
            print('got ', len(share_links), 'vmesses')
        except Exception as e:
            print('Read subscription fail: ', e)

def readFromYou():
    with open(fileNameRead, 'r') as f:
        data = f.read()
        tree = etree.parse(StringIO(data), parser)
        parent = tree.xpath('//*[@id="post-box"]/div/section/div[2]/table/tbody')
        trs = parent[0].xpath('tr')
        for _tr in trs:
            vStr = (_tr.xpath('td/a')[0].attrib['data-raw'])
            vmes.append(vStr)

def runPing(vmStr):
    try:
        pingCmd = [vpingName, '-c', pCount, '-o', pTimeout, vmStr]
        runPing = subprocess.run(pingCmd, capture_output=True, text=True)
        avgPing = re.findall(r"\d+\/(\d+)\/\d+",runPing.stdout.split('\n')[int(pCount) + 12])
        if int(avgPing[0]) != 0:
            vmPingQueue.put(vmStr)
#            print('ping got one!')
    except Exception as e:
        pass

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
        pass

def pingListener():
    print('pingListener start')
    global pLQ
    executor = TPE(max_workers = maxPingThreadNum) 
    while True:
        try:
            vmStr = vmQueue.get(block = False)
            vmQueue.task_done()
            pThread = executor.submit(runPing, vmStr)
        except Exception as e:
            print('waitting for more vmesses...')
            break
    executor.shutdown(wait = True)
    pLQ = 1
    print('pingListener stop')

def speedTestListener():
    print('speedTestListener start')
    global pLQ, sLQ
    executor = TPE(maxSpeedTestNum) 
    while True:
        try:
            vmStr = vmPingQueue.get(block = False)
            vmPingQueue.task_done()
            sThread = executor.submit(runSpeedTest, vmStr)
        except Exception as e:
            if pLQ == 1:
                break
            sleep(3)
    executor.shutdown(wait = True)
    sLQ = 1
    print('speedTestListener stop')


def sorting(vmLst):
    vmLst.sort(key=lambda down: down[1], reverse = False)
    return vmLst

def echoOut():
    vmLst = vmTestQueue.get()
    vmTestQueue.task_done()
    vmesOut.append(vmLst)
    vmStr = vmLst[0] + '\nDown: ' +str(vmLst[1]) + ' Up: ' + str(vmLst[2]) + ' location: ' + vmLst[3]
    print(vmStr)

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


def dataHandler():
    readFromYou()
    subscriptionDecoding()


if __name__ == '__main__':

    readFromYou()
    subscriptionDecoding()
    for vm in vmes:
        vmQueue.put(vm)

    pListenerEx = TPE(1)
    pL = pListenerEx.submit(pingListener)

    sListenerEx = TPE(1)
    sL = sListenerEx.submit(speedTestListener)

    try:
        while True:
            if vmTestQueue.empty() is not True:
                echoOut()
                sleep(5)
            else:
                if sLQ == 1:
#                    print('vmTestQueue is joining')
#                    vmTestQueue.join()
#                    print("vmTestQueu joined")
                    pListenerEx.shutdown(wait = False)
                    sListenerEx.shutdown(wait = False)
                    break
                sleep(5)
    except Exception as e:
        print("Error: echo file: ", e)

    vmesOut = sorting(vmesOut)
    with open(fileName_echoOut, 'w') as f:
        for vmLst in vmesOut:
            f.writelines(vmLst[0] + '\nDown: ' +str(vmLst[1]) + ' Up: ' + str(vmLst[2]) + ' location: ' + vmLst[3] + '\n')
#    vmLst = vmesOut.pop()
#    xrayThread(vmLst[0])


