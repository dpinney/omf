'''
Put me in a directory with all the TMY3s and run me to convert them to TMY2 format.

Requires NREL's TMY3 to TMY2 exe and windows.
'''

import os, csv, re, shutil

pathToExe ='"C:\\Program Files (x86)\\TMY3toTMY2_CMD\\TMY3toTMY2_CMD.exe"'
testFolder = "./tmy3 full dataset/"
os.chdir(testFolder)

def renameTmy2s():
    allNames = [x for x in os.listdir('.') if x.endswith('.txt')]
    for fName in allNames:
        with open(fName,'r') as inFile:
            code, city, state = inFile.readline().split()[0:3]
            print(city, state)
        shutil.copyfile(fName, state + '-' + city + '.tmy2')

def convertTmy3(csvPath):
    readFile = open(csvPath, newline='')
    reader = csv.reader(readFile)
    firstRow = next(reader)
    origName = str(firstRow[1])
    newName = re.sub(r'\W', '', origName.replace(" ", "_"))
    firstRow[1] = '"' + newName + '"'
    outName = firstRow[2] + "-" + newName + "-V3.tmy2.txt"
    writeFile = open(outName, "w", newline='')
    writeFile.write(",".join(firstRow))     
    writer = csv.writer(writeFile, quotechar="'")
    for row in reader:
        writer.writerow(row)
    # Now convert.
    readFile.close()
    writeFile.close()
    os.system(pathToExe + " " + outName + " >" + outName[0:-4])

def convertAll():
    # Now for everything:
    allPaths = [x for x in os.listdir(".") if x.endswith(".csv")]
    for fName in allPaths:
        convertTmy3(fName)

convertAll()
