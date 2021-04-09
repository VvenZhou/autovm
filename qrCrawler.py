#!/usr/bin/env python3

from lxml import etree
from io import StringIO
import subprocess
import threading
import time
import queue
import re

parser = etree.HTMLParser()

fileNameWrite = "nodes_youneedwind.txt"
fileNameRead = "youneedwind.html"
vpingName = "./vping_c3_o5"
vspeedName = './vspeed_10s'

threadingNum = 200
pingThreads = []

vmessQueue = queue.Queue()
vmessWithSpeed = []
vmessFinalOutQueue = queue.Queue()

class vmessPingThread(threading.Thread):
    def __init__(self, vm):
        threading.Thread.__init__(self)
        self.vm = vm

    def run(self):
        pingCmd = [vpingName, self.vm]
        runPing = subprocess.run(pingCmd, capture_output=True, text=True)
        try:
            avgPing = re.findall(r"\d+\/(\d+)\/\d+",runPing.stdout.split('\n')[15])
            if int(avgPing[0]) != 0:
                vmessQueue.put(self.vm)
        except Exception as e:
            pass

class vmessSpeedTestThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        if vmessQueue.empty() is not True:
            vm = vmessQueue.get()
            print(vm)
            testCmd = [vspeedName, vm]
            runTest = subprocess.run(testCmd, capture_output=True, text=True)
            try: 
                downStr = runTest.stdout.split('\n')[13]
                downSpeed = re.findall(r"\d+.\d+", downStr)
                upStr = runTest.stdout.split('\n')[14]
                upSpeed = re.findall(r"\d+.\d+", upStr)
                vmessWithSpeed.append([vm, float(downSpeed[0]), float(upSpeed[0])])
                print(downStr)
                print(upStr)
            except Exception as e: 
                print(e)

def subscriptionDecoding():
    pass

def sorting():
    vmessWithSpeed.sort(key=lambda down: down[1], reverse = True)

with open(fileNameRead, 'r') as f:
    data = f.read()
    tree = etree.parse(StringIO(data), parser)
    parent = tree.xpath('//*[@id="post-box"]/div/section/div[2]/table/tbody')
    trs = parent[0].xpath('tr')
    vmess = ""
    for _tr in trs:
        while(threading.activeCount() >= threadingNum):
            time.sleep(3)
        vmess = (_tr.xpath('td/a')[0].attrib['data-raw'])
        pingThread = vmessPingThread(vmess)
        pingThreads.append(pingThread)
        pingThread.start()

for index, thread in enumerate(pingThreads):
    # print('waitting for: ', index)
    thread.join()

print("\nFinished quiring!")
print("There are ", len(pingThreads), "vmesses")
print('\nStart speed testing')

while vmessQueue.empty() is not True:
    speedThread = vmessSpeedTestThread()
    speedThread.start()
    speedThread.join()

print('speed testing finished')

sorting()

for vmWithS in vmessWithSpeed:
    print(vmWithS[0])
    print("down: ", vmWithS[1], "  ", "up: ", vmWithS[2])

with open("sorted.txt", 'w') as f:
    for vm in vmessWithSpeed:
        f.write(vm[0])

