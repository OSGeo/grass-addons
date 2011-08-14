import os
def loadConfigFile(self):
    try:
        f=open('./config','r')
        lines = f.readlines()
        f.close()
        self.name_url_delimiter = lines[0].split()[1]
        print "config file loaded successfully"
        print self.name_url_delimiter
        return True
    except:
    	os.system("find ./ -name config")
    	print "Unable to load config file"
        return False
