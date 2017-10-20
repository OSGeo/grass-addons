#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 10:29:51 2017

@author: lucadelu
"""

import argparse
import glob
import os
import fnmatch

modules = ['d.', 'db.', 'g.', 'i.', 'm.', 'r3.', 'r.', 't.', 'v.', 'wxGUI.']

def is_module(name):
    """Check if html page is refering to a module or not"""
    right = False
    for mod in modules:
        if name.startswith(mod):
            right = True
    return right

def check_file(fil, example=False, screen=False):
    """check if HTML file contain EXAMPLE word and more then one <img> tag
    (one <img> tag is in all pages since there is GRASS logo)
    """
    f = open(fil)
    lines = f.read()
    output = [False, False]
    if example:
        if 'EXAMPLE' in lines:
            output[0] = True
    else:
        output[0] = True
    if screen:
        if lines.count('<img') > 1:
            output[1] = True
    else:
        output[1] = True
    return output

def main(args):
    """Main function"""
    examples = []
    screens = []
    if not args['r']:
        files = glob.glob('*.html')
        for fil in files:
            name = fil.replace('.html','')
            right = is_module(fil)
            if not right:
                continue
            res = check_file(fil, args['e'], args['s'])
            if not res[0]:
                examples.append(name)
            if not res[1]:
                screens.append(name)
    else:
        for root, dirnames, filenames in os.walk('.'):
            for name in fnmatch.filter(filenames, '*.html'):
                right = is_module(name)
                if not right:
                    continue
                fil = os.path.join(root, name)
                res = check_file(fil, args['e'], args['s'])
                if not res[0]:
                    examples.append(name)
                if not res[1]:
                    screens.append(name)
    if args['e']:
        examples.sort()
        print("Modules missing examples:\n{lis}".format(lis='\n'.join(examples)))
    if args['s']:
        screens.sort()
        print("Modules missing screenshots:\n{lis}".format(lis='\n'.join(screens)))
            

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Check modules without '
                                     ' examples or screenshots',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog="Run into docs/html"
                                     " folder to get modules without examples:"
                                     "\n check_examples_screenshots.py -e"
                                     "\nRun into grass7 folder in grass-addons"
                                     " to get modules without screenshots:"
                                     "\n check_examples_screenshots.py -s -r")
    parser.add_argument('-e', dest='e', action='store_true',
                        default=False, help='Check for examples')
    parser.add_argument('-s', dest='s', action='store_true',
                        default=False, help='Check for screenshots')
    parser.add_argument('-r', dest='r', action='store_true',
                        default=False, help='Check recursively')
    
    args = parser.parse_args()
    main(args.__dict__)