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

threadingNum = 200
threads = []

vmessQueue = queue.Queue()

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
        thread = vmessPingThread(vmess)
        threads.append(thread)
        thread.start()
        vmess.clear()

for index, thread in enumerate(threads):
    print('waitting for: ', index)
    thread.join()

print("finished")

while vmessQueue.empty() is not True:
    print(vmessQueue.get())

