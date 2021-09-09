#!/usr/bin/python3
#################################################################
#                         get_timing                    		#
#################################################################
#                                                               #
#   This script takes in a folder/file and goes through all the #
#   subfolders or through fileto get the spec period for each   #
#   equation set (eg. EQNSET 1). Outputs file: timingSpecs.txt  #
#                                                               #
#################################################################
# Version 0.1                                                   #
# By Shane Benetz                                               #
# Date: 08.19.2021                                              #
#################################################################
#################################################################
# Version 0.0 is first release 08.06.2021                       #
# Version 0.1 updated path reading and usage info 08.19.2021    #
#################################################################

import pandas as pd
import argparse
import os
import re
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def convert_to_csv(inputFile,outputDir):
    # check inputs
    if not os.path.isfile : 
        return print(inputFile+' is not a file')
    if not os.path.isdir(outputDir) :
        os.makedirs(outputDir)
        print('Output folder created: ' + outputDir)
    #list out excel worksheets to select from
    workbook = pd.ExcelFile(inputFile)
    print('\nSelect worksheet names by typing corresponding numbers separated by spaces')
    i=0
    for name in workbook.sheet_names:
        print('    ' + str(i) + '. ' + name)
        i += 1
    print('    ' + str(i) + '. ALL SHEETS')
    numbers = input("Selected Numbers: ").split(' ')
    names= []
    for i in range(0,len(numbers)):
        try : 
            num = int(numbers[i])
            if num == len(workbook.sheet_names) : names = None;break
            if not (num >= 0 and num < len(workbook.sheet_names)): 
                raise Exception
        except: print('Please enter only integers in above range'); return
        names.append(workbook.sheet_names[num])
    # pull chosen sheets from excel into raw csv files 
    read_file = pd.read_excel(inputFile, sheet_name=names, header=None,index_col=None)
    sheets = []
    for file in read_file.keys() :
        outputFileRaw = os.path.join(outputDir,file+'_raw.csv')
        read_file[file].to_csv(outputFileRaw)
        sheets.append(outputFileRaw)
    pNames = {}
    for sheet in sheets :
        readFile = open(sheet, 'r') 
        contents = readFile.readlines()
        nameIdxs = []
        pinNumIdx = [] 
        channelIdx = []
        badColNames = ['length', 'len','coord']
        badCols = []
        firstFound = False
        # try to get pin name, channel number, and ball number from line 
        for line in contents:
            name = None; pinNum = None; channelNum = None
            data = line.split(',')
            if name == None :
                    for col in nameIdxs:
                        if data[col].isupper() : name = data[col]; break
            for entry in data :
                
                updated = False
                ind = data.index(entry)
                if ind in badCols : continue
                if any(x in entry for x in badColNames): 
                    if not ind in badCols: badCols.append(ind)
                if 'name' in entry.lower() : 
                    nameIdxs.append(ind) # 'Name' in col header
                # look for pin number (1-3upper case letters followed by 1-3#s)
                if (not firstFound) or ind in pinNumIdx :
                    pin = re.match('([A-Z]{1,2}[0-9]{1,2})(\Z|\s|\b)',entry)
                    if pin: 
                        pinNum = pin.group(0).strip()
                        if not ind in pinNumIdx : pinNumIdx.append(ind)
                        updated = True
                if (not firstFound) or ind in channelIdx:
                    try: 
                        entry = entry.replace('.','').replace('TC','').replace('CH','')
                        entry = round(float(entry),0); entry = str(entry).replace('.0','')
                    except : pass
                    if not firstFound : print(entry)
                    # 12345 or 12345-6
                    channel = re.match('([0-9]{5}|([0-9]{5}-[0-9]{1,2}))(\Z|\s|\b)',entry)
                    if channel: 
                        channelNum = channel.group(0).strip()
                        updated = True
                    else:
                        #123-P4 or 123-P45 or 123-P4-P5
                        channel = re.match('[0-9]{3}-P[0-9]{1,2}(-P[0-9]{1,2})?(\Z|\s|\b)',entry)
                        if channel: 
                            channelNum = channel.group(0).strip()
                            updated = True
                        else:
                            #123A+ or 123HH-
                            channel = re.match('[0-9]{3}[A-Z]{1,2}[+|-](\Z|\s|\b)',entry)
                            if channel: 
                                channelNum = channel.group(0).strip()
                                updated = True
                    if not ind in pinNumIdx and updated : channelIdx.append(ind)
                # if its a new set of assignments   
                if name and pinNum and channelNum and updated and name!= pinNum: 
                    if name in pNames.keys() :
                        if channelNum in pNames[name] and not pinNum in pNames[name]:
                            pNames[name] += [pinNum]
                        if pinNum in pNames[name] and not channelNum in pNames[name]:
                            pNames[name].insert(1,channelNum)
                        elif not channelNum in pNames[name] and not pinNum in pNames[name]: 
                            pNames[name] += [channelNum, pinNum]
                    else: pNames[name] = [channelNum, pinNum]
            if len(pNames.keys()) > 0 : firstFound = True
        readFile.close()
        os.remove(sheet)
            # what to do with columns that dont have name label
            # consider what to do for multiple sites
    if len(pNames.keys()) == 0 : return
    filename =  os.path.basename(inputFile)
    outputFile =filename[:filename.rfind('.')]+'_assignments.csv'
    writeFile = open(outputFile,'w')
    chHeader = 'Channel Number'
    testLine = pNames[list(pNames.keys())[0]]
    for i in range(0,len(testLine)):
        if re.search('[A-OQ-Z]',testLine[i]): break
        if i == 1 : chHeader = 'Channel Site-1,Channel Site-2'
        elif i > 1: chHeader += ',Channel Site-'+str(i+1)
        
    writeFile.write('Pin Name,%s,Ball Number(s)\n'%chHeader)
    for key in pNames:
        writeFile.write(key+','+','.join(pNames[key])+'\n')
    writeFile.close()

def csv_to_conf(csvFile):
    #helo
    print('')




if __name__ == '__main__' :
    parser = argparse.ArgumentParser(description='Analyze a shmoo plot files', \
        formatter_class = argparse.RawTextHelpFormatter, epilog = 'usage examples:\n'\
        '  '\
        ' ')
    parser.add_argument('-v', '-V', '--version', dest='version', action='store_true',\
        default=False, help='get version of script and exit')
    parser.add_argument('-i', '--input', dest='input', default=None, \
        help='path of excel file to convert')
    parser.add_argument('-o', '--output', dest='outputDir', default='.', \
        help='output folder path. creates output path if DNE. DEFAULT current folder')
    args = parser.parse_args()
#try:
    convert_to_csv(args.input, args.outputDir)
    # except KeyboardInterrupt:
    #     print('\n Keyboard Interrupt: Process Killed')
    # except: print('Cannot convert given file')
