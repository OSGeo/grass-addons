#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
############################################################################
#
# MODULE:       ssh_session.py
# AUTHOR(S):    Eric S. Raymond
#
#               Greatly modified by Nigel W. Moriarty, April 2003
#               Modified by Luca Delucchi 2011
#
# PURPOSE:      establish a SSH session to a remote system
#
# COPYRIGHT:    (C) 2011 by Eric S. Raymond, Nigel W. Moriarty, Luca Delucchi
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

from pexpect import *
import os, sys, subprocess
import getpass
import time

class ssh_session:

    """Session with extra state including the password to be used"""

    def __init__(self, user, host, gsession, password=None, verbose=0):

        self.user = user
        self.host = host
        self.verbose = verbose
        self.password = password
        self.gsession = gsession
        self.openagent = False
        self.keys = [
            'authenticity',
            'password:',
            'Enter passphrase',
            '@@@@@@@@@@@@',
            'Command not found.',
            EOF,
            ]
        # set the home path
        home = os.path.expanduser('~')
        logfile = os.path.join(home, self.gsession,'g.cloud','ssh.log')
        self.f = open(logfile,'w')

    def __repr__(self):
        outl = 'class :'+self.__class__.__name__
        for attr in self.__dict__:
            if attr == 'password':
                outl += '\n\t'+attr+' : '+'*'*len(self.password)
            else:
                outl += '\n\t'+attr+' : '+str(getattr(self, attr))
        return outl

    def __exec(self, command):
        """Execute a command on the remote host. Return the output."""
        
        child = spawn(command #, timeout=10
                      )
        if self.verbose:
            sys.stderr.write("-> " + command + "\n")
        seen = child.expect(self.keys)
        self.f.write(str(child.before) + str(child.after)+'\n')
        if seen == 0:
            child.sendline('yes')
            seen = child.expect(self.keys)
        if seen == 1 or seen == 2:
            if not self.password:
                self.password = getpass.getpass('Remote password: ')
            child.sendline(self.password)
            child.readline()
            time.sleep(5)
            # Added to allow the background running of remote process
            if not child.isalive():
                seen = child.expect(self.keys)
        if seen == 3:
            lines = child.readlines()
            self.f.write(lines)
        if self.verbose:
            sys.stderr.write("<- " + child.before + "|\n")
        try:
            self.f.write(str(child.before) + str(child.after)+'\n')
        except:
            pass
        #self.f.close()
        return child.before

    def ssh(self, command):
	"""Function to launch command with ssh"""
        return self.__exec("ssh -Y -l %s %s \"%s\"" % (self.user,self.host,command))

    def scp(self, src, dst):
	"""Function to move data from client to server"""
        return self.__exec("scp %s %s@%s:%s" % (src, self.user, self.host, dst))

    def pcs(self, src, dst):
	"""Function to move data from server to client"""
        return self.__exec("scp %s@%s:%s %s" % (self.user, self.host, src, dst))

    def add(self):
	"""Function to launch ssh-add"""
	sess = self.__exec("ssh-add")
	if sess.find('Could not open') == -1:
	    return 0
	else:
	    self.openagent = True
	    proc = subprocess.Popen(['ssh-agent', '-s'], stdout=subprocess.PIPE)
	    output = proc.stdout.read()
	    vari = output.split('\n')
	    sshauth = vari[0].split(';')[0].split('=')
	    sshpid = vari[1].split(';')[0].split('=')
	    os.putenv(sshauth[0],sshauth[1])
	    os.putenv(sshpid[0],sshpid[1])
	    self.add()

    def close(self):
	"""Close connection"""
	if self.openagent:
	    subprocess.Popen(['ssh-agent', '-k'], stdout=subprocess.PIPE )
        return self.f.close()
