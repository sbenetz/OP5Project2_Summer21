#!/usr/bin/python3
import sys

file1 = sys.argv[1]
file2 = sys.argv[2]

fileOne = open(file1,'r')
fileTwo = open(file2,'r')

lines1 = fileOne.readlines()
lastInd1 = 0
for line in lines1:
    lastInd1+=1
    if line.find('PSTE') != -1: break
lines1 = lines1[0:lastInd1]
lines1 = list(x[:x.find('\n')] for x in lines1)
lines2 = fileTwo.readlines()
lastInd2 = 0
for line in lines2:
    lastInd2+=1
    if line.find('PSTE') != -1: break
lines2 = lines2[0:lastInd2]
lines2 = list(x[:x.find('\n')] for x in lines2)
print('In ',file1,' but not in',file2)
print('   ','\n    '.join(sorted(list(set(lines1) - set(lines2)))))
print('In ',file2,' but not in',file1)
print('   ','\n    '.join(sorted(list(set(lines2) - set(lines1)))))
fileOne.close()
fileTwo.close()