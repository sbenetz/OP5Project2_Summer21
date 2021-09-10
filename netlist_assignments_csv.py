#!/usr/bin/python3
#################################################################
#                     netlist_assignments_csv                   #
#################################################################
#                                                               #
#   This script takes an excel file that contains a loadboard   #
#   netlist within it and converts all the assignment to a csv  #  
#   in the format Net Name,Channel Assignment(s),Pin Number(s)  #
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

import pandas as pd
from openpyxl import load_workbook
import argparse
import os
import re
import sys
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def netlist_to_csv(inputFile,outputDir,excluded):
    '''Searches an excel file for all the tester channel assignments for every net 
    name. The following rules must be followed in formatting excel sheet:
        1. Only one net name/pin name per row
            - Column must be first column to have a header that has "name" in it
            - All letters must be capitalized
        2. Only one ball name/pin number per row
            - Searches for first column with 1-3 letters followed by 1-3 numbers only
            - e.g. AA12 or AB1 or A123 or P13
        3. As many channels as necessary can be added in a row
            - searches all columns in row 
            - accepted channel format examples (no names):
                a. 12345
                b. 12345-6
                c. 123-P4
                d. 123-P4-P5
                e. 123.45
                f. 123A+/123AA-
                g. PF1-PF12_PSNAME_345/P12_PSNAME_345
                h. PF1_PSNAME_234/P1_PSNAME_234
                i. any of the above proceeded by CH/TC
    '''
    # check inputs
    inputFile = os.path.realpath(re.sub('["\']','',inputFile))
    if not os.path.isfile(inputFile) : 
        return print(inputFile+' is not a file')
    outputDir = os.path.realpath(re.sub('["\']','',outputDir))
    if not os.path.isdir(outputDir) :
        os.makedirs(outputDir)
        print('Output folder created: ' + outputDir)

    #list out excel worksheets to select from
    try: 
        print('Loading workbook...',end='\r')
        workbook = load_workbook(filename = inputFile)
    except: return print(os.path.basename(inputFile) + ' is not a valid excel file')
    sheets = workbook.sheetnames
    visibleSheets = []
    for sheet in sheets:
        if workbook[sheet].sheet_state != 'hidden' : 
            visibleSheets.append(sheet)
    print('                       \nSelect worksheet names by typing corresponding'\
        ' numbers separated by spaces')
    i=0
    for name in visibleSheets:
        print('    ' + str(i) + '. ' + name)
        i += 1
    print('    ' + str(i) + '. ALL SHEETS')
    numbers = input("Selected Numbers: ").split(' ')
    names= []
    for i in range(0,len(numbers)):
        try : 
            num = int(numbers[i])
            if num == len(visibleSheets) : names = visibleSheets;break
            if not (num >= 0 and num < len(visibleSheets)): 
                raise Exception
        except: print('Please enter only integers in above range'); return
        names.append(visibleSheets[num])

    # pull chosen sheets from excel into raw csv files 
    read_file = pd.read_excel(inputFile, sheet_name=names, header=None,index_col=None)
    sheets = []
    for file in read_file.keys() :
        outputFileRaw = os.path.join(outputDir,file+'_raw.csv')
        read_file[file].to_csv(outputFileRaw,sep=';')
        sheets.append(outputFileRaw)
    pNames = {}
    for sheet in sheets :
        readFile = open(sheet, 'r') 
        contents = readFile.readlines()
        nameIdxs = []
        badColNames = ['length', 'len','coord']
        badCols = []
        # try to get pin name, channel number, and ball number from line 
        for line in contents:
            name = None; pinNum = None; channelNum = None
            #change all commas in line to ! and change separators to commas
            line = line.replace(',','!').replace(';',',')
            data = line.split(',')
            if name == None :
                    for col in nameIdxs:
                        if data[col].isupper() : name = data[col]; break
            for entry in data :
                updatedC = False; updatedP = False
                ind = data.index(entry)
                if ind in badCols : continue
                if any(x in entry for x in badColNames): 
                    if not ind in badCols: badCols.append(ind)
                if 'name' in entry.lower() : 
                    if not ind in nameIdxs: nameIdxs.append(ind)#'name' in col header
                
                if pinNum == None:
                    # pin number (1-3 upper case letters followed by 1-3#s) AA11
                    pin = re.match('([A-Z]{1,2}[0-9]{1,2})(?=((\Z|\s|\b)|\!))',entry)
                    if pin: 
                        pinNum = pin.group(0).strip()
                        updatedP = True
                try: 
                    # get rid of letters before channel
                    entry = re.sub('TC|CH','', entry).replace('PF','P')
                    #channel formats like PF13-PF16_DPS32_425 
                    entry =  re.sub('_.*_','_', entry)
                    if '_'in entry and re.search('[0-9]{3}',entry): 
                        entry = entry[entry.find('_')+1:]+'-'+entry[:entry.find('_')]
                    if re.search('[0-9]{3}\.[0-9]{2}',entry) != None:
                        entry = entry.replace('.','')
                except : pass
                # 12345 or 12345-6
                channel = re.match('([0-9]{5}|([0-9]{5}-[0-9]{1,2}))(\Z|\s|\b)',entry)
                if channel: 
                    channelNum = channel.group(0).strip()
                    updatedC = True
                else:
                    #123-P4 or 123-P45 or 123-P4-P5
                    channel = re.match('[0-9]{3}-P[0-9]{1,2}(-P[0-9]{1,2})?(\Z|\s|\b)',entry)
                    if channel: 
                        channelNum = channel.group(0).strip()
                        updatedC = True
                    else:
                        #123A+ or 123HH-
                        channel = re.match('[0-9]{3}[A-Z]{1,2}[+|-](\Z|\s|\b)',entry)
                        if channel: 
                            channelNum = channel.group(0).strip()
                            updatedC = True
                
                # if its a new set of assignments   
                if name and pinNum and channelNum and (updatedC or updatedP) and name!= pinNum: 
                    if name in pNames.keys() :
                        if channelNum in pNames[name] and not pinNum in pNames[name]:
                            pNames[name] += [pinNum]
                        if pinNum in pNames[name] and not channelNum in pNames[name]:
                            pNames[name].insert(1,channelNum)
                        elif not channelNum in pNames[name] and not pinNum in pNames[name]: 
                            pNames[name] += [channelNum, pinNum]
                    else: pNames[name] = [channelNum, pinNum]
        readFile.close()
        os.remove(sheet)

    if len(pNames.keys()) < 0 : return
    filename =  os.path.basename(inputFile)
    outputFile = os.path.join(outputDir,filename[:filename.rfind('.')]+'_assignments.csv')
    writeFile = open(outputFile,'w')
    chHeader = 'Channel Number'
    testLine = pNames[list(pNames.keys())[0]]
    for i in range(0,len(testLine)):
        if re.search('[A-OQ-Z]',testLine[i]): break
        if i == 1 : chHeader = 'Channel Site-1,Channel Site-2'
        elif i > 1: chHeader += ',Channel Site-'+str(i+1)
        
    writeFile.write('Pin Name,%s,Ball Number(s)\n'%chHeader)
    for key in pNames:
        if key in excluded: continue
        writeFile.write(key+','+','.join(pNames[key])+'\n')
    writeFile.close()
    return pNames

if __name__ == '__main__' :
    parser = argparse.ArgumentParser(description=\
    '''    Searches an excel file for all the tester channel assignments for every
    net name. The following rules must be followed in formatting excel sheet:
        1. Only one net name/pin name per row
            - Column must be first column to have a header that has "name" in it
            - All letters must be capitalized
        2. Only one ball name/pin number per row
            - Searches for first column with 1-3 letters followed by 1-3 numbers only
            - e.g. AA12 or AB1 or A123 or P13
        3. As many channels as necessary can be added in a row
            - searches all columns in row 
            - accepted channel format examples (no names):
                a. 12345
                b. 12345-6
                c. 123-P4
                d. 123-P4-P5
                e. 123.45
                f. 123A+/123AA-
                g. PF1-PF12_PSNAME_345/P12_PSNAME_345
                h. PF1_PSNAME_234/P1_PSNAME_234
                i. any of the above proceeded by CH/TC''', \
    formatter_class = argparse.RawTextHelpFormatter, epilog = 'usage examples:\n'\
        '   netlist_assignments_csv -i PRODUCT-NETLIST-01.xlsx -o OUTPUTDIR\n\n'\
        '   netlist_assignments_csv -i PRODUCT-NETLIST-01.xlsx -x NC N/A')
    parser.add_argument('-v', '-V', '--version', dest='version', action='store_true',\
        default=False, help='get version of script and exit')
    parser.add_argument('-i', '--input', dest='input', default=None, \
        help='path of excel file to convert')
    parser.add_argument('-o', '--output', dest='outputDir', default='.', \
        help='output folder path. creates output path if DNE. DEFAULT current folder')
    parser.add_argument('-x', '--exclude', nargs='+',dest='exclude', default=[], \
        help='pin names to be excluded/ignored (e.g NC)')
    args = parser.parse_args()
    if args.version: print('Version '+version); sys.exit()
    try:
        netlist_to_csv(args.input, args.outputDir, args.exclude)
    except KeyboardInterrupt:
        print('\n Keyboard Interrupt: Process Killed')
    except: print('Cannot convert given file')
