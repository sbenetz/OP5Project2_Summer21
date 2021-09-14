#!/usr/bin/python3
#################################################################
#                     stil_assignments_csv                    	#
#################################################################
#                                                               #
#   This script takes a .stil file that contains a list of pin  #
#   names and in/out assignments and converts to a csv          #  
#   in the format Net Name, In/Out Assignment                   #    
#                                                               #
#################################################################
# Version 0.0                                                   #
# By Shane Benetz                                               #
# Date: 09.09.2021                                              #
#################################################################
#################################################################
# Version 0.0 is first release 09.09.2021                       #
#################################################################

version = '0.0'

import argparse
import os
import re
import sys
import itertools

def stil_to_csv(inputFiles,outputDir, productName):
    if productName == None: #get everything up until the first period or underscore
        productName = re.match('^(.*?)(?=(\.|_))',os.path.basename(inputFiles[0])).group(0)
    productName = productName.replace(' ','_')
    outputDir = os.path.realpath(re.sub('["\']','',outputDir))
    if not os.path.isdir(outputDir) :
        os.makedirs(outputDir)
        print('Output folder created: ' + outputDir)
    signalList=[]
    for file in inputFiles: 
        # check inputs
        inputFile = os.path.realpath(re.sub('["\']','',file))
        if not os.path.isfile(inputFile) or not inputFile.endswith('.stil'): 
            return print(inputFile+' is not a file')
        stilFile = open(inputFile, 'r')
        contents = stilFile.read()
        # get block of signal names
        sigStartInd = contents.find('Signals {')+9
        signals = contents[sigStartInd:sigStartInd+contents[sigStartInd:].find('}')]
        signals = re.sub(' +', ' ', re.sub('(\n|")','',signals)).strip()+' '
        signalList += list(set(signals.split('; '))- set(signalList)) #join non repeats 
    # write all signals to csv
    outputFile = os.path.join(outputDir,productName+'_stil_assignments.csv')
    writeFile = open(outputFile, 'w')
    writeFile.write('Pin Name,In/Out/InOut\n')
    typeOrder = [' In',' Out',' InOut','']
    #sort list first in above order then alphabetically
    signalList = sorted(signalList,key=lambda x:(typeOrder.index(x[x.find(' '):]),x))
    updatedSignalList = []
    for signal in signalList: 
        if signal == '':continue
        updatedSignalList.append(signal.replace(' ',','))
        writeFile.write(signal.replace(' ',',')+'\n')
    signalList = updatedSignalList
    #group definitions
    writeFile.write('\n#IN/OUTS#')
    writeFile.write('\nCONF I,F160,(')
    In =  [x[:x.find(',')] for x in signalList if x.endswith(',In')]
    writeFile.write(','.join(In)+')')
    writeFile.write('\nCONF O,F160,(')
    Out =  [x[:x.find(',')] for x in signalList if x.endswith(',Out')]
    writeFile.write(','.join(Out)+')')
    writeFile.write('\nCONF IO,F160,(')
    InOut =  [x[:x.find(',')] for x in signalList if x.endswith(',InOut')]
    writeFile.write(','.join(InOut)+')')
    writeFile.write('\n\n#Groups#')
    i = 0
    directs = ['I','O','IO']
    groupDict = {}
    for lists in [In, Out, InOut]:
        groups = []
        iterator = itertools.groupby(lists, lambda string: string[0:4])
        # number of chars to match by right here -------------------^
        for lists, group in iterator:
            groups.append(list(group))
        for group in groups:
            name = (os.path.commonprefix(group)).lower()
            if name.endswith('_') or name.endswith('['): 
                name = name[0:len(name)-1]
            name = directs[i]+'-'+'(%s)'%name
            if i == 2:
                names = [name[0]+name[2:],name[1:len(name)]]
                for name in names:
                    if name in groupDict.keys(): groupDict[name]+= group
                    else: groupDict[name] = group
            else:
                if name in groupDict.keys(): groupDict[name]+= group
                else: groupDict[name] = group
        i+=1
    for key1 in list(groupDict.keys()): # expand groups with common substring in name
        for key2 in list(groupDict.keys()):
            if key1 in groupDict.keys() and key2 in groupDict.keys():
                k1 = key1[3:]; k2 = key2[3:]
                if k1!=k2 and k1[:k1.find(')')] in k2[:k2.find(')')] or\
                    sum(k1[i] != k2[i] for i in range(min(len(k1),len(k2))))==1 :# 1 char difference
                    groupDict[key1]+=groupDict[key2]
                    del groupDict[key2]
    for name in groupDict.keys():
        if len(groupDict[name])>1:
            groupLine = '\nDFGP '+name.replace('-',(',(%s),'%','.join(groupDict[name])))             
            writeFile.write(groupLine)  
    stilFile.close()
    writeFile.close()
    return [signalList,os.path.abspath(outputFile)]


if __name__ == '__main__' :
    parser = argparse.ArgumentParser(description=\
    '''Convert a .stil file into csv listing the Input/Output status of each pin and
    grouping together similar pins ''', \
    formatter_class = argparse.RawTextHelpFormatter, epilog = 'usage examples:\n'\
        '   \n\n'\
        '   ')
    parser.add_argument('-v', '-V', '--version', dest='version', action='store_true',\
        default=False, help='get version of script and exit')
    parser.add_argument('-i', '--input', dest='inputs', nargs = '+', required=True, \
        help='path of .stil file(s) to convert')
    parser.add_argument('-o', '--output', dest='outputDir', default='.', \
        help='output folder path. creates output path if DNE. DEFAULT current folder')
    parser.add_argument('-n', '--name', dest='name', default=None, \
        help='name of product and product version (e.g. fulda_B0')
    args = parser.parse_args()
    if args.version: print('Version '+version); sys.exit()
    try:
        stil_to_csv(args.inputs, args.outputDir, args.name)
    except KeyboardInterrupt:
        print('\n Keyboard Interrupt: Process Killed')
    #except: print('Cannot convert given file')