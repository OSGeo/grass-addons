"""!
@package LoadConfig.py

@brief Python function to load configuration file for
wmsmenu.py and addserver.py.

(C) 2006-2011 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

Functions:
 - loadConfigFile

@author: Maris Nartiss (maris.nartiss gmail.com)
@author Sudeep Singh Walia (Indian Institute of Technology, Kharagpur , sudeep495@gmail.com)
"""

import os
def loadConfigFile(self):
    try:
        f=open('config','r')
        lines = f.readlines()
        f.close()
        print lines
        #patch4s
        try:
            if(len(lines)!=3):
                print 'Insufficient number of arguments,3 paramters required name_url_delimiter, timeoutValueSeconds, urlLength'
                raise Exception
            self.name_url_delimiter = lines[0].split(':')[1]
            self.timeoutValueSeconds = int(lines[1].split(':')[1])
            self.urlLength = int(lines[2].split(':')[1])
            #self.name_url_delimiter = '\n'
            print self.timeoutValueSeconds
        except Exception, e:
            print e
            print 'Internal exception, config file format error, using default values'
            self.name_url_delimiter = '#'
            self.timeoutValueSeconds = 5
            self.urlLength = 50
        #patch4e
        print "config file loaded successfully"
        print self.name_url_delimiter
        return True
    except:
    	os.system("find ./ -name config")
    	print "Unable to load config file"
        return False
