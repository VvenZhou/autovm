#!/usr/bin/env python3

from lxml import etree
from io import StringIO
import subprocess
import threading
import time
import queue

parser = etree.HTMLParser()

fileNameWrite = "nodes_youneedwind.txt"
fileNameRead = "youneedwind.html"
vpingName = "./vping_c3_o5"
vspeedName = './vspeed_10s'

threadingNum = 200
pingThreads = []

vmessQueue = queue.Queue()
vmessFinalOutQueue = queue.Queue()

class vmessPingThread(threading.Thread):
    def __init__(self, vmessPart):
        threading.Thread.__init__(self)
        self.vmessPart = vmessPart

    def run(self):
        vmessGood = []
        for _vm in self.vmessPart:
            pingCmd = [vpingName, _vm]
            runPing = subprocess.run(pingCmd, capture_output=True, text=True)
            if runPing.stdout.split('\n')[-2] != 'rtt min/avg/max = 0/0/0 ms' and len(runPing.stdout.split('\n')) > 5:
                vmessGood.append(_vm)
            for _vm in vmessGood:
                vmessQueue.put(_vm)

class vmessSpeedTestThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        if vmessQueue.empty() is not True:
            vm = vmessQueue.get()
            print("\n")
            print(vm)
            testCmd = [vspeedName, vm]
            runTest = subprocess.run(testCmd, capture_output=True, text=True)
            try: 
                down = runTest.stdout.split('\n')[13]
                up = runTest.stdout.split('\n')[14]
                print(down)
                print(up)
            except Exception as e: 
                print(e)

with open(fileNameRead, 'r') as f:
    data = f.read()
    tree = etree.parse(StringIO(data), parser)
    parent = tree.xpath('//*[@id="post-box"]/div/section/div[2]/table/tbody')
    trs = parent[0].xpath('tr')
    vmess = []
    for _tr in trs:
        while(threading.activeCount() >= threadingNum):
            time.sleep(3)
        vmess.append(_tr.xpath('td/a')[0].attrib['data-raw'] + '\n')
        pingThread = vmessPingThread(vmess)
        pingThreads.append(pingThread)
        pingThread.start()
        vmess.clear()

for index, thread in enumerate(pingThreads):
    # print('waitting for: ', index)
    thread.join()

print("finished quiring!")
print('start speed testing')

while vmessQueue.empty() is not True:
    speedThread = vmessSpeedTestThread()
    speedThread.start()
    speedThread.join()

