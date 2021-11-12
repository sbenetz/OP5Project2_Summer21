#!/usr/bin/python3
import sys

file1 = sys.argv[1]
file2 = sys.argv[2]

fileOne = open(file1,'r')
fileTwo = open(file2,'r')

lines1 = fileOne.readlines()
types = ['DFPN','DFAN''DFPS','DFAN','PSTE','PALS']
lastInd1 = 0
l1 = []
for line in lines1:
    if any(x in line for x in types) : l1.append(line[:line.find('\n')])
lines2 = fileTwo.readlines()
lastInd2 = 0
l2 = []
for line in lines2:
    if any(x in line for x in types) : l2.append(line[:line.find('\n')])
print('In ',file1,' but not in',file2)
print('   ','\n    '.join(sorted(list(set(l1)-set(l2)),key=lambda x: x[x.rfind('('):])))
print('In ',file2,' but not in',file1)
print('   ','\n    '.join(sorted(list(set(l2)-set(l1)),key=lambda x: x[x.rfind('('):])))
fileOne.close()
fileTwo.close()