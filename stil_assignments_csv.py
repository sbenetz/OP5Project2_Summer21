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

def stil_to_csv(inputFiles,outputDir, name):
    if name == None: #get everything up until the first period or underscore
        name = re.match('^(.*?)(?=(\.|_))',os.path.basename(inputFiles[0])).group(0)
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
    outputFile = os.path.join(outputDir,name+'_stil_assignments.csv')
    writeFile = open(outputFile, 'w')
    writeFile.write('Pin Name,In/Out/InOut\n')
    for signal in sorted(signalList,key=lambda x: x[-4:]) : 
        if signal == '':continue
        writeFile.write(signal.replace(' ',',')+'\n')

    writeFile.write('\n#Groups#\n')
    writeFile.write('\n(In): ')
    In =  [x[:x.find(' ')] for x in signalList if x.endswith(' In')]
    for signal in In: writeFile.write(signal+',')
    writeFile.write('\n(Out): ')
    Out =  [x[:x.find(' ')] for x in signalList if x.endswith(' Out')]
    print(Out)
    for signal in Out: writeFile.write(signal+',')
    writeFile.write('\n(InOut): ')
    InOut =  [x[:x.find(' ')] for x in signalList if x.endswith(' InOut')]
    for signal in InOut: writeFile.write(signal+',')
    i = 0
    directs = ['I','O','IO']
    groupDict = {}
    for lists in [In, Out, InOut]:
        groups = []
        iterator = itertools.groupby(lists, lambda string: string[0:5])
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
                if key1!=key2 and key1[:key1.find(')')] in key2[:key2.find(')')] :
                    groupDict[key1]+=groupDict[key2]
                    del groupDict[key2]
    for name in groupDict.keys():
        if len(groupDict[name])>1:
            groupLine = '\nDFGP '+name.replace('-',(',(%s),'%','.join(groupDict[name])))             
            writeFile.write(groupLine)  
    stilFile.close()
    writeFile.close()
    return signalList


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