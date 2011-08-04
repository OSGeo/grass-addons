def loadConfigFile(self):
    try:
        f=open('config','r')
        lines = f.readlines()
        f.close()
        self.name_url_delimiter = lines[0].split()[1]
        print "config file loaded successfully"
        print self.name_url_delimiter
        return True
    except:
        return False
