# Taken from https://lists.osgeo.org/pipermail/gdal-dev/2018-March/048246.html

import os
import sys
import requests
import re
msg = sys.stdin.read()

def untouched(msg):
     with open('/tmp/log_untouched.txt', 'a') as f:
          f.write('Message is:\n' + msg + '\n')

# Don't touch messages that reference other databases
if msg.find('RT bug ') >= 0 or \
   msg.find('RT #') >= 0 or \
   msg.find('RT#') >= 0 or \
   msg.find('r3 bug') >= 0 or \
   msg.find('r2 calc') >= 0:     
     sys.stdout.write(msg)
     untouched(msg)
     sys.exit(0)
# trac migration date set 2007-12-09 (25479)
rev = 25479
m = re.compile(r".*git-svn-id.*@([0-9]{1,5}).*", re.DOTALL)
if int(m.match(msg).groups()[0]) <= rev:
     untouched(msg)
     sys.exit(0)

# Fix '#1234'
oldpos = 0
old_msg = msg
while True:
    # # We already have reference to github pull requests written like
    # # 'github #1234', so skip them
    # newpos = msg.find('github #', oldpos)
    # if newpos >= 0:
    #     oldpos = newpos + len('github #')
    #     continue

    # # Exception...
    # newpos = msg.find('patch #1 ', oldpos)
    # if newpos >= 0:
    #     oldpos = newpos + len('patch #1 ')
    #     continue

    # # Exception...
    # newpos = msg.find('bug 1 ', oldpos)
    # if newpos >= 0:
    #     oldpos = newpos + len('bug 1 ')
    #     continue

    # # Fix 'bug 1234'
    # newpos = msg.find('bug ', oldpos)
    # if newpos >= 0:
    #     if newpos == len(msg) - 4:
    #         break
    #     if not(msg[newpos+4] >= '1' and msg[newpos+4] <= '9'):
    #         oldpos = newpos + 4
    #         continue

    #     msg = msg[0:newpos] + 'https://trac.osgeo.org/grass/ticket/' + msg[newpos+4:]
    #     oldpos = newpos
    #     continue

    # # Fix 'ticket 1234'
    # newpos = msg.find('ticket ', oldpos)
    # if newpos >= 0:
    #     if newpos == len(msg) - 7:
    #         break
    #     if not(msg[newpos+7] >= '1' and msg[newpos+7] <= '9'):
    #         oldpos = newpos + 7
    #         continue

    #     msg = msg[0:newpos] + 'https://trac.osgeo.org/grass/ticket/' + msg[newpos+7:]
    #     oldpos = newpos
    #     continue

    # Fix '#1234'
    newpos = msg.find('#', oldpos)
    if newpos >= 0:
        if newpos == len(msg) - 1:
            break
        if not(msg[newpos+1] >= '0' and msg[newpos+1] <= '9'):
            oldpos = newpos + 1
            continue

        # Skip stacktraces like '#1 0xdeadbeef'
        space_pos = msg.find(' ', newpos)
        if space_pos > 0 and space_pos + 2 < len(msg) and msg[space_pos + 1] == '0' and msg[space_pos + 2] == 'x':
            oldpos = newpos + 1
            continue

        # check if ticket really exists
        # num = ''
        # while True:
        #     if not(msg[newpos+1] >= '0' and msg[newpos+1] <= '9'):
        #         break
        #     num += msg[newpos+1]
        #     newpos += 1
        
        # url = 'https://trac.osgeo.org/grass/ticket/' + num
        # request = requests.get(url)
        # if request.status_code != 200:
        #     # does not exist
        #     oldpos = newpos + len(msg[newpos+1:])
        #     continue

        msg = msg[0:newpos-len(num)] + url + msg[newpos+1:]
        oldpos = newpos
        continue

    break

# Fix 'r1234'
oldpos = 0
old_msg = msg
while True:
    newpos = msg.find('r', oldpos)
    if newpos >= 0:
        if newpos == len(msg) - 1:
            break
        if (newpos > 0 and msg[newpos-1] != ' ') or \
           not(msg[newpos+1] >= '0' and msg[newpos+1] <= '9'):
            oldpos = newpos + 1
            continue

        num = ''
        while True:
            if not(msg[newpos+1] >= '0' and msg[newpos+1] <= '9'):
                break
            num += msg[newpos+1]
            newpos += 1

        if newpos+1 <= len(msg)-1 and msg[newpos+1] not in (' ', '\n'):
             oldpos = newpos + 1
             continue
        
        url = 'https://trac.osgeo.org/grass/changeset/' + num            
        msg = msg[0:newpos-len(num)] + url + msg[newpos+1:]
        oldpos = newpos
        continue
    break

if msg != old_msg:
    with open('/tmp/log_touched.txt', 'a') as f:
        f.write('Old message was:\n' + old_msg + 'New message is:\n' + msg + '\n')
else:
     untouched(msg)

sys.stdout.write(msg)
