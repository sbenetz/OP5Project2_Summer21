#!/usr/bin/python3
#################################################################
#                     stil_to_config                        	#
#################################################################
#                                                               #
#   This script takes in info from converted .stil and netlist  #
#   csv files and compares/ combines them to make a config file #
#   for the 93k advantest ATE                                   #d
#                                                               #
#################################################################
# Version 0.0                                                   #
# By Shane Benetz                                               #
# Date: 09.10.2021                                              #
#################################################################
#################################################################
# Version 0.0 is first release 09.10.2021                       #
#################################################################

version = '0.0'

import argparse
import sys
import os
import re
import glob
from netlist_assignments_csv import netlist_to_csv
from stil_assignments_csv import stil_to_csv
# first in tuple is S2(A)Pogo Block, second is S1(D) Pogo Block
# 1 indexed list to represnt pin number(e.g. first position is pin 1)
conversionTable = [['DD-','HH-'],['DD+','HH+'],['CC-','GG-'],['CC+','GG+'],\
    ['BB-','FF-'],['BB+','FF+'],['AA-','EE-'],['AA+','EE+'],['D-','H-'],\
    ['D+','H+'],['C-','G-'],['C+','G+'],['B-','F-'],['B+','F+'],\
    ['A-','E-'],['A+','E+'],['CT1','CT2']]

PS9G = ['31701-32416', '30101-30216', '30501-30616']
DCS_DPS128HC = ['22501-22516','42501-42516','22901-22916','42901-42916']
PS1600 = ['12501-13216', '11701-12416', '10101-10816', '20101-20816', '40101-40816',\
    '10901-11616', '20901-21616', '40901-41616', '21701-22416', '41701-42416']
DCS_UHC4T = ['22701-22704', '23001-23004']

def create_config(inputFiles, outputDir, productName, card):
    stilFiles = []
    netlistFile = None
    netlistCSV = None; stilCSV = None
    if productName == None and inputFiles: #get everything up until the first period or underscore
        productName = re.match('^(.*?)(?=(\.|_))',os.path.basename(inputFiles[0])).group(0)
        productName = productName.replace(' ','_')
    for file in inputFiles:
        file = os.path.realpath(re.sub('["\']','',file))
        if not os.path.isfile(file):
            print(file+' is not a file'); continue
        if file.endswith('.stil'): stilFiles.append(file)
        elif file.endswith('stil_assignments.csv'): stilCSV = file
        elif file.endswith('netlist_assignments.csv'): netlistCSV = file
        elif re.search('.xslx|.xls|.xlsm',file): netlistFile = file
    outputDir = os.path.realpath(re.sub('["\']','',outputDir))
    if not os.path.isdir(outputDir) :
        os.makedirs(outputDir)
        print('Output folder created: ' + outputDir)
    # get files from outputDir if they are not provided
    outputDirFiles = glob.glob(outputDir+ '/*.*')
    if len(stilFiles) == 0 and stilCSV == None : stilFilesNeeded = True
    else: stilFilesNeeded = False
    if netlistFile == None and netlistCSV == None : netNeeded = True
    else : netNeeded = False
    for file in outputDirFiles:
        if stilFilesNeeded and file.endswith('.stil'): stilFiles.append(file)
        elif stilFilesNeeded and file.endswith('stil_assignments.csv'): stilCSV=file
        elif netNeeded and file.endswith('netlist_assignments.csv'): netlistCSV=file
        elif netNeeded and re.search('.xslx|.xls|.xlsm',file): netlistFile = file
    # get list/dictionary from each file
    # get .stil assignments
    stilList = None
    if stilCSV == None and len(stilFiles)>0:
        stilList, stilCSV = stil_to_csv(stilFiles,outputDir,productName)
    if stilCSV and stilList == None:
        with open(stilCSV,'r') as stil:
            lines = stil.readlines()
            if not 'Pin Name,In/Out/InOut' in lines[0]:
                return print('Cannot find valid stil assignments')
            tempList = []
            for line in lines[1:]:
                if len(line) < 4: break
                tempList.append(line[:line.find('\n')])
            stilList = tempList
    if stilList == None or stilCSV == None : 
        return print('Cannot find valid stil assignments')
    if productName == None:
        productName = re.match('^(.*?)(?=(\.|_))',os.path.basename(stilCSV)).group(0)
        productName = productName.replace(' ','_')
    # get netlist assignments
    netDict = None
    if netlistCSV == None and netlistFile :
        netDict, netlistCSV = netlist_to_csv(netlistFile,outputDir,productName,[None])
    if netlistCSV and netDict == None:
        with open(netlistCSV,'r') as netlist:
            lines = netlist.readlines()
            if not 'Pin Name,Channel' in lines[0]:
                return print('Cannot find valid netlist assignments')
            tempDict = {}
            for line in lines[1:]:
                if len(line) < 4 or line.count(',')<2: break
                try:
                    data = line.replace('\n','').split(',')
                    tempDict[data[0]] = data[1:]
                except: pass
            netDict = tempDict
    if netDict == None or netlistCSV == None : 
        return print('Cannot find valid netlist assignments')
    #get number of sits from the netlist CSV header
    with open(netlistCSV,'r') as net:
        topLine = net.readline()
        numbers = re.findall(r'\d+',topLine) # get biggest integer on top line
        if len(numbers) == 0: sites = 1
        else: sites = int(max(numbers))
    #print differences to error log
    differences = get_diff(netDict,stilList)
    if len(differences) > 2: 
        errlogFile = os.path.join(outputDir,productName+'_config_error_log.txt')
        with open(errlogFile,'w') as err:
            err.write('\n'.join(differences))

    configFile = open(os.path.join(outputDir,productName+'.conf'),'w')
    configFile.write('hp93000,config,0.1\n')
    extraCONFI = []
    try:
        extraInNet = differences[differences.index('\nIn netlist but not in .stil:')+1:]  
        for net in extraInNet:
            if '""' in netDict[net] : 
                stilList.append(net+',I'); extraCONFI.append(net)
                differences.remove(net)
    except:pass  
    entries = []
    names = [*netDict.keys()]
    names += stilList
    for pinName in names:
        io=None; stilName = None
        if pinName.find(',')>0: 
            stilName = pinName
            pinName = pinName[:pinName.find(',')]
            io = pinName[pinName.find(',')+1:]
        if not pinName in netDict.keys(): continue
        pinData = netDict[pinName]
        pins = pinData[sites:]
        channels = pinData[0:sites]
        for i in range(0,len(channels)):
            channel = channels[i]
            if re.match('[0-9]{3}(([A-Z]{1,2}[+|-])|CT1|CT2)(\Z|\s|\b)',channel):
                for sublist in conversionTable:
                    for item in sublist:
                        if item in channel:
                            replacement = '%02d' % (conversionTable.index(sublist)+1)
                            channelTemp = channel[0:3] + replacement
                            channels[i] = [channelTemp]
            elif re.match('[0-9]{3}-P[0-9]{1,2}(\Z|\s|\b)',channel):
                channelTemp = channel[0:3] + '%02d' % int(channel[5:])
                channels[i] = [channelTemp]
            elif re.match('[0-9]{3}-P[0-9]{1,2}-P[0-9]{1,2}(\Z|\s|\b)',channel) :
                start = int(channel[channel.find('P')+1:channel.rfind('-')])
                end = int(channel[channel.rfind('P')+1:])
                channelTemp = []
                for j in range(start, end+1):
                    channelTemp.append(channel[0:3]+'%02d' % j)
                channels[i] = channelTemp
            elif re.match('[0-9]{5}-[0-9]{1,2}(\Z|\s|\b)',channel) :
                start = int(channel[3:5])
                end = int(channel[channel.find('-')+1:])
                channelTemp = []
                for j in range(start, end+1):
                    channelTemp.append(channel[0:3]+'%02d' % j)
                channels[i] = channelTemp 
            else: channels[i] = [channel]
        i=0
        isPS = False
        for chs in channels:
            i+=1
            for ch in chs:
                if not(ch.isdigit() and len(ch) == 5): continue
            if len(chs) ==1: chnlString = chs[0]
            else: chnlString = '(%s)'%','.join(chs)
            if i == 1: 
                if len(pins) > 1 : 
                    entry = 'DFPS ' + chnlString +',POS,('+pinName +')'
                    entries.append(entry); isPS = True
                elif len(chs) > 1: 
                    entry = 'DFPS ' + chnlString +',POS,('+pinName +')'
                    entries.append(entry); isPS = True
                else:
                    lists = [DCS_DPS128HC,DCS_UHC4T]
                    if 'PS9G' in card: lists.append(PS9G)
                    if 'PS1600' in card: lists.append(PS1600)
                    for list in lists:
                        if isPS : break
                        for ranges in list:
                            low = int(ranges[:ranges.find('-')])
                            high = int(ranges[ranges.find('-')+1:])
                            firstCh = int(chs[0])
                            if firstCh < high and firstCh > low : #if in PS range
                                entry = 'DFPS ' + chnlString +',POS,('+pinName +')'
                                entries.append(entry)
                                isPS = True; break
                if not isPS and stilName and stilName in stilList: 
                    entry = 'DFPN %s,"%s",(%s)'%(chnlString,pins[0],pinName)
                    entry = entry.replace('""""','""')
                    entries.append(entry)
            if i>1 :  
                entry = 'PALS %d,%s,,(%s)'%(i,chnlString,pinName)
                if not entry in entries:
                    entries.append(entry)
    entries.append('PSTE '+str(sites))
    with open(stilCSV,'r') as groupsFile:
        content = groupsFile.read()
        groups = content[content.find('#'):]
        for netName in differences:
            groups = groups.replace(','+netName+',',',')
            groups = groups.replace(','+netName+')',')')
            groups = groups.replace('('+netName+',','(')
    groups = groups.splitlines()
    #if len(extraCONFI) > 0: entries.append('CONF I,F160,(%s)'%)
    for group in groups:
        if group.startswith('CONF I') and len(extraCONFI) > 0:
            group = group[:group.rfind(')')]+','+','.join(extraCONFI)+')'
        if (group.startswith('CONF') or group.startswith('DFGP')) and \
            group[group.find('('):group.rfind(')')].count(',')>1 :
            entries.append(group)      
    order = ['DFPN','DFPS','DFAN','PALS','PSTE','CONF','DFGP']
    entries = sorted(entries,key=lambda x:(order.index(x[0:4]),x[x.rfind('('):]))
    configFile.write('\n'.join(entries))
    configFile.write('\nNOOP "7.4.2",,,')
    configFile.close()


def get_diff(netDict,stilList):
    differ = ['In .stil but not in netlist:']
    stilListNames = []
    for assignment in stilList :
        stilListNames.append(assignment[:assignment.find(',')])
    netDictNames = netDict.keys()
    for name in stilListNames:
        if name not in netDictNames: differ.append(name)
    differ.append('\nIn netlist but not in .stil:')
    for name in netDictNames:
        if name not in stilListNames: differ.append(name)
    return differ

    
    
    
if __name__ == '__main__' :
    parser = argparse.ArgumentParser(description=\
    ''' ''', \
    formatter_class = argparse.RawTextHelpFormatter, epilog = 'usage examples:\n'\
        '   \n\n'\
        '   ')
    parser.add_argument('-v', '-V', '--version', dest='version', action='store_true',\
        default=False, help='get version of script and exit')
    parser.add_argument('-i', '--input', nargs='+', dest='inputs', default=[], \
        help='path of excel file and .stil file(s) to convert or the already converted'\
            ' csv version of both, if none found, looks in output directory')
    parser.add_argument('-o', '--output', dest='outputDir', default='.', \
        help='output folder path. creates output path if DNE. DEFAULT current folder')
    parser.add_argument('-n', '--name', dest='name', default=None, \
        help='name of product and product version (e.g. fulda_B0')
    parser.add_argument('-c', '--cards', dest='psCard', default=['PS9G'],\
        choices=['PS9G', 'PS1600'], nargs='+',
        help='name of product and product version (e.g. fulda_B0')
    args = parser.parse_args()
    if args.version: print('Version '+version); sys.exit()
    try:
        create_config(args.inputs, args.outputDir, args.name, args.psCard)
    except KeyboardInterrupt:
        print('\n Keyboard Interrupt: Process Killed')
    #except: print('Cannot convert given file')