#!/usr/bin/python3

import os, sys
import hashlib

cwd = os.getcwd()
currentFileList = []
currentHashes = []

DATADIR_MAIN = "updates/data"
DATADIR_CITRA = "updates/dataCitra"

FILEDB_PATH = "hashes.txt"
FILEDB_BAK = "hashes-bak.txt"
FILEDIFF_OUT = "filelist.txt"

modeList = ["new", "check", "update","revert"]
MODE_NEW, MODE_CHECK, MODE_UPDATE, MODE_REVERT = range(4)

def usage():
    print("""\
Usage: %s [cmd]

cmd can be one of the following:
    new - disregard database and make a new one
    check - compare and output to console
    update - compare, write output and update database""" % sys.argv[0])
    sys.exit(1)

def appErr(err:int):
    if err == 1:
        print("""\
The directory for the update repo was not found.
Exiting!""")
    sys.exit(2)

def writeHashlist():
    with open(FILEDB_PATH,"w") as f:
        for i in range(len(currentFileList)):
            f.write("{}\t{}\n".format(currentFileList[i],currentHashes[i]))

def sarchash(s, mul=101):
    r = 0
    for i in s:
        r = ((r * mul) + ord(i)) & 0xFFFFFFFF
    return r

if len(sys.argv)<2:
    usage()

try:
    mode = modeList.index(sys.argv[1].lower().strip())
except:
    usage()

if mode == MODE_REVERT:
    if os.path.exists(FILEDB_BAK):
        if os.path.exists(FILEDB_PATH):
            os.remove(FILEDB_PATH)
        os.rename(FILEDB_BAK, FILEDB_PATH)
    else:
        print("Error: Cannot revert")
    sys.exit(0)

wd0 = os.getcwd()
while True:
    if os.path.exists("_cmd") and os.path.exists("updates"): break
    os.chdir("..")
    if os.getcwd()==wd0: appErr(1)
    wd0 = os.getcwd()

s = os.path.join(wd0, DATADIR_CITRA)
if os.path.exists(s):
    os.chdir(s)
    f = os.popen("find -nowarn -type f")
    currentFileList = f.read().replace("./","C/").split(os.linesep)
    f.close()

os.chdir(os.path.join(wd0, DATADIR_MAIN))
f = os.popen("find -nowarn -type f")
currentFileList += f.read().replace("./","M/").split(os.linesep)
f.close()
currentFileList.sort()
while True:
    try: currentFileList.remove("")
    except: break

os.chdir("..")

print(":: Reading hash of files...")
for i in range(len(currentFileList)):
    p = "data"
    if currentFileList[i][0]=="C": p = "dataCitra"
    p += currentFileList[i][1:]
    print("%5.1f%%" % ((i+1)/len(currentFileList)*100), end="\r", flush=True)
    with open(p,"rb") as f:
        hash = hashlib.sha256()
        size = f.seek(0, 2)
        f.seek(0)
        while f.tell()<size:
            hash.update(f.read(65536))
        currentHashes.append(
            hash.digest().hex() +
            int.to_bytes(
                sarchash(currentFileList[i]), 4, "little"
            ).hex()
        )
print()
os.chdir(cwd)

if mode == MODE_NEW or not os.path.exists(FILEDB_PATH):
    if not os.path.exists(FILEDB_PATH):
        print("Hash list did not exist! Creating it.")
    else:
        os.remove(FILEDB_PATH)

    writeHashlist()
    sys.exit(0)

listFiles = []
listHashes = []
listFHashes = []

with open(FILEDB_PATH,"r", encoding="utf-8", errors="ignore") as f:
    size = f.seek(0,2)
    f.seek(0,0)
    while f.tell()<size:
        s = f.readline().strip().split("\t")
        listFiles.append(s[0])
        listHashes.append(s[1][:64])
        listFHashes.append(
            int.to_bytes(
                sarchash(s[0]), 4, "little"
            ).hex() if len(s[1])<=64 else s[1][64:]
        )

addedFiles = []
renamedFilesFrom = []
renamedFilesTo = []
knownFiles = []

for i in range(len(currentFileList)):
    h, fh = currentHashes[i][:64], currentHashes[i][64:]
    fileContentIntact = False
    try:
        fileHashIndex = listFHashes.index(fh)
        fileExistsAllTheTime = True
        knownFiles.append(fileHashIndex)
    except:
        fileHashIndex = -1
        try:
            fileHashIndex = listHashes.index(h)
            fileExistsAllTheTime = None
        except:
            fileExistsAllTheTime = False
    
    if fileExistsAllTheTime:
        if not listHashes[fileHashIndex] == h:
            addedFiles.append(currentFileList[i])
    elif fileExistsAllTheTime is None:
        try:
            print("Potential rename has happened!")
            print(" To: "+currentFileList[i])
            while True:
                fileHashIndex = listHashes.index(h, fileHashIndex)
                if input("From "+listFiles[fileHashIndex]+"?[yN]")[:1].upper()=="Y": break
                fileHashIndex += 1
        except:
            addedFiles.append(currentFileList[i])
        else:
            renamedFilesFrom.append(listFiles[fileHashIndex])
            renamedFilesTo.append(currentFileList[i])
            knownFiles.append(fileHashIndex)
    elif not fileExistsAllTheTime:
        addedFiles.append(currentFileList[i])

knownFiles.sort(reverse=True)
for i in knownFiles:
    listFiles.pop(i)

missingFiles = listFiles

if mode == MODE_CHECK:
    print("Added  :",addedFiles)
    print("Missing:",missingFiles)
    print("Renaming:")
    print("  from ",renamedFilesFrom)
    print("  to   ",renamedFilesTo)

with open(FILEDIFF_OUT,"w",encoding="utf-8",errors="ignore",newline="") as f:
    f.truncate(0)
    for i in missingFiles:
        s = "D"+i[1:]
        f.write("{}\n".format(s))
    for i in range(len(renamedFilesFrom)):
        s = "F"+renamedFilesFrom[i][1:]
        t = "T"+renamedFilesTo[i][1:]
        f.write("{}\n{}\n".format(s, t))
    for i in addedFiles:
        f.write("{}\n".format(i))

if mode == MODE_UPDATE:
    try:
        if os.path.exists(FILEDB_BAK):
            os.remove(FILEDB_BAK)
        os.rename(FILEDB_PATH, FILEDB_BAK)
    except: pass
    writeHashlist()