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
import itertools

def create_config(inputFiles,outputDir):
    print(inputFiles)

if __name__ == '__main__' :
    parser = argparse.ArgumentParser(description=\
    ''' ''', \
    formatter_class = argparse.RawTextHelpFormatter, epilog = 'usage examples:\n'\
        '   \n\n'\
        '   ')
    parser.add_argument('-v', '-V', '--version', dest='version', action='store_true',\
        default=False, help='get version of script and exit')
    parser.add_argument('-i', '--input', nargs='+', dest='inputs', default=None, \
        help='path of excel file and .stil file to convert or the already converted'\
            'csv version of both, if none found, looks in output directory')
    parser.add_argument('-o', '--output', dest='outputDir', default='.', \
        help='output folder path. creates output path if DNE. DEFAULT current folder')
    args = parser.parse_args()
    if args.version: print('Version '+version); sys.exit()
    try:
        create_config(args.inputs, args.outputDir)
    except KeyboardInterrupt:
        print('\n Keyboard Interrupt: Process Killed')
    except: print('Cannot convert given file')