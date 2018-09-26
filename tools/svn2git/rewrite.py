# Taken from https://lists.osgeo.org/pipermail/gdal-dev/2018-March/048246.html

import sys
import requests
msg = sys.stdin.read()

# Don't touch messages that reference other databases
# if msg.find('MITAB bug ') >= 0 or msg.find('Safe bug ') >= 0 or msg.find('bugzilla') >= 0 or msg.find('Bugzilla') >= 0:
#     sys.stdout.write(msg)
#     sys.exit(0)

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
        if not(msg[newpos+1] >= '1' and msg[newpos+1] <= '9'):
            oldpos = newpos + 1
            continue

        # Skip stacktraces like '#1 0xdeadbeef'
        space_pos = msg.find(' ', newpos)
        if space_pos > 0 and space_pos + 2 < len(msg) and msg[space_pos + 1] == '0' and msg[space_pos + 2] == 'x':
            oldpos = newpos + 1
            continue

        # check if ticket really exists
        url = 'https://trac.osgeo.org/grass/ticket/' + msg[newpos+1:]
        request = requests.get(url)
        if request.status_code != 200:
            # does not exist
            oldpos = newpos + len(msg[newpos+1:])
            continue

        msg = msg[0:newpos] + url
        oldpos = newpos
        continue

    break

if msg != old_msg:
    with open('/tmp/log.txt', 'a') as f:
        f.write('Old message was:\n' + old_msg + 'New message is:\n' + msg + '\n')

sys.stdout.write(msg)
