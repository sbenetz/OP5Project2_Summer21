#!/usr/bin/python3
#################################################################
#                     stil_assignments_csv                    	#
#################################################################
#                                                               #
#   This script takes a .stil file that contains a list of pin  #
#   names and in/out assignments and converts to a csv          #  
#   in the format Net Name, In/Out Assignment  #
#                                                               #
#################################################################
# Version 0.0                                                   #
# By Shane Benetz                                               #
# Date: 09.09.2021                                              #
#################################################################
#################################################################
# Version 0.0 is first release 09.09.2021                       #
#################################################################

import argparse
import os
import re
import itertools

def convert_to_csv(inputFile,outputDir,excluded):
    # check inputs
    inputFile = os.path.realpath(re.sub('["\']','',inputFile))
    if not os.path.isfile(inputFile) or not inputFile.endswith('.stil'): 
        return print(inputFile+' is not a file')
    outputDir = os.path.realpath(re.sub('["\']','',outputDir))
    if not os.path.isdir(outputDir) :
        os.makedirs(outputDir)
        print('Output folder created: ' + outputDir)
    
    stilFile = open(inputFile, 'r')
    filename =  os.path.basename(inputFile)
    outputFile = os.path.join(outputDir,filename[:filename.rfind('.')]+'_assignments.csv')
    writeFile = open(outputFile, 'w')
    contents = stilFile.read()
    # get block of signal names
    sigStartInd = contents.find('Signals {')+9
    signals = contents[sigStartInd:sigStartInd+contents[sigStartInd:].find('}')]
    signals = re.sub(' +', ' ', re.sub('(\n|")','',signals)).strip()+' '
    signalList = signals.split('; ')
    # write all signals to csv
    writeFile.write('Pin Name,In/Out/InOut\n')

    for signal in signalList : 
        writeFile.write(signal.replace(' ',',')+'\n')
    writeFile.write('#Groups#\n')
    In = signalList.copy()
    Out = []; InOut = []; unknown = []
    writeFile.write('\n(In): ')
    In =  [x[:x.find(' ')] for x in signalList if x.endswith(' In')]
    for signal in In: writeFile.write(signal+',')
    writeFile.write('\n(Out): ')
    Out =  [x[:x.find(' ')] for x in signalList if x.endswith(' Out')]
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


if __name__ == '__main__' :
    parser = argparse.ArgumentParser(description=\
    '''  ''', \
    formatter_class = argparse.RawTextHelpFormatter, epilog = 'usage examples:\n'\
        '   \n\n'\
        '   ')
    parser.add_argument('-v', '-V', '--version', dest='version', action='store_true',\
        default=False, help='get version of script and exit')
    parser.add_argument('-i', '--input', dest='input', default=None, \
        help='path of excel file to convert')
    parser.add_argument('-o', '--output', dest='outputDir', default='.', \
        help='output folder path. creates output path if DNE. DEFAULT current folder')
    parser.add_argument('-x', '--exclude', nargs='+',dest='exclude', default=[], \
        help='pin names to be excluded/ignored (e.g NC)')
    args = parser.parse_args()
    try:
        convert_to_csv(args.input, args.outputDir, args.exclude)
    except KeyboardInterrupt:
        print('\n Keyboard Interrupt: Process Killed')
    #except: print('Cannot convert given file')