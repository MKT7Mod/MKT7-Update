#!/usr/bin/python3

import os, sys, math

def roundUpBlock(x:int, unit:int):
    return math.ceil(x / unit) * unit

DATADIR_MAIN = "updates/data"
DATADIR_CITRA = "updates/dataCitra"

cwd = wd0 = os.getcwd()

while True:
    if os.path.exists("_cmd") and os.path.exists("updates"): break
    os.chdir("..")
    if os.getcwd() == wd0: sys.exit(2)
    wd0 = os.getcwd()

l = []
s = os.path.join(wd0, DATADIR_CITRA)
if os.path.exists(s):
    f = os.popen("find -nowarn -type f")
    l = f.read().replace("./","C/").split(os.linesep)
    f.close()

os.chdir(os.path.join(wd0, DATADIR_MAIN))
f = os.popen("find -nowarn -type f")
l += f.read().replace("./","M/").split(os.linesep)
f.close()
l.sort()
while True:
    try: l.remove("")
    except: break

totalSize = 0
for i in l:
    i = "./"+i[2:]
    totalSize += roundUpBlock(os.stat(i).st_size, 131072) # 1 Nintendo Block

installInfoPath = "../installInfo.txt"
if os.path.exists(installInfoPath):
    os.remove(installInfoPath)

with open(installInfoPath,"wb") as f:
    f.write(b"S/%d\n"%totalSize)
    for i in l:
        i = i.replace("\\","/")
        f.write("{}\n".format(i).encode())