#!/usr/bin/env python
import re, os, sys
import random
import string
import wx
import csv
from datetime import datetime, timedelta
from gui_core import gselect


class SaveLoad(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        saveBtt = wx.Button(parent=self, label='Save')
        loadBtt = wx.Button(parent=self, label='Load')
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer.Add(saveBtt, flag=wx.EXPAND)
        sizer.Add(loadBtt, flag=wx.EXPAND)
        self.SetSizer(sizer)


class BaseInput(wx.Panel):
    #def __init__(self, parent, label,key, cats=False):
    def __init__(self, parent, label):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        statText = wx.StaticText(self, id=wx.ID_ANY, label=label)
        #if cats:
        #self.ctrl = gselect.VectorCategorySelect(parent=self, giface=self._giface)  # TODO gifece
        #else:
        self.text = wx.TextCtrl(self, id=wx.ID_ANY)
        #self.key=key
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(statText, flag=wx.EXPAND)
        sizer.Add(self.text, flag=wx.EXPAND)
        self.SetSizer(sizer)

    def GetKey(self):
        return self.key

    def GetValue(self):
        value=self.text.GetValue()
        if value=='':
            return None
        else:
            return value

    def SetValue(self, value):
        self.text.SetValue((str(value)))

class TextInput(wx.Panel):
    def __init__(self, parent, label, tmpPath=None):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.tmpPath = tmpPath
        statText = wx.StaticText(self, id=wx.ID_ANY, label=label)
        statText2 = wx.StaticText(self, id=wx.ID_ANY, label='or enter values interactively')

        self.pathInput = wx.TextCtrl(self, id=wx.ID_ANY)
        self.browseBtt = wx.Button(self, id=wx.ID_ANY, label='Browse')
        self.directInp = wx.TextCtrl(self, id=wx.ID_ANY, size=(0, 70), style=wx.TE_MULTILINE | wx.HSCROLL)
        self.saveBtt=wx.Button(self,label='Save to new file')

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.pathInput, flag=wx.EXPAND, proportion=1)
        sizer2.Add(self.browseBtt, flag=wx.EXPAND)


        sizer.Add(statText, flag=wx.EXPAND)
        sizer.Add(sizer2, flag=wx.EXPAND)
        sizer.Add(statText2, flag=wx.EXPAND)
        sizer.Add(self.directInp, flag=wx.EXPAND)
        sizer.Add(self.saveBtt)

        self.SetSizer(sizer)
        self.browseBtt.Bind(wx.EVT_BUTTON, self.onBrowse)
        self.saveBtt.Bind(wx.EVT_BUTTON,self.setTmpPath)
        self.firstDirInp = False

    def setTmpPath(self, event):
        if self.firstDirInp is False:
            self.firstDirInp = True
            if self.tmpPath is None:
                self.tmpPath=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tmp%s' % randomWord(3))
                print self.tmpPath
            self.pathInput.SetValue(str(self.tmpPath))

        io=open(self.tmpPath,'w')
        io.writelines(self.directInp.GetValue())
        io.close()
        print self.directInp.GetValue()

    def onBrowse(self, event):
        openFileDialog = wx.FileDialog(self, "Open text file", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if openFileDialog.ShowModal() == wx.ID_CANCEL:
            return  # the user changed idea...
        path = openFileDialog.GetPath()
        self.firstDirInpActive = False
        self.pathInput.SetValue(path)
        if self.SetValue() == -1:
            # TODO msgbox
            self.pathInput.SetValue('')

    def GetValue(self):
        return self.directInp.GetValue()

    def SetValue(self):
        io = open(self.pathInput.GetValue(), 'r')
        str = io.read()
        try:
            self.directInp.SetValue(str)
            return 1
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)
            return -1
        except ValueError:
            print "Could not decode text"
            return -1
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise
        io.close()

    def GetPath(self):
        path=self.pathInput.GetValue()
        if path=='':
            return None
        else:
            return path

    def SetPath(self, value):
        self.firstDirInpActive = True
        self.pathInput.SetValue(value)
        if self.SetValue() == -1:
            # TODO msgbox
            self.pathInput.SetValue('')

class FileInput(wx.Panel):
    def __init__(self, parent, label, dir=False, tmpPath=None):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.dir = dir
        self.tmpPath = tmpPath
        statText = wx.StaticText(self, id=wx.ID_ANY, label=label)

        self.pathInput = wx.TextCtrl(self, id=wx.ID_ANY)
        self.browseBtt = wx.Button(self, id=wx.ID_ANY, label='Browse')

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.pathInput, flag=wx.EXPAND, proportion=1)
        sizer2.Add(self.browseBtt, flag=wx.EXPAND)

        sizer.Add(statText, flag=wx.EXPAND)
        sizer.Add(sizer2, flag=wx.EXPAND)

        self.SetSizer(sizer)
        self.browseBtt.Bind(wx.EVT_BUTTON, self.onBrowse)

    def onBrowse(self, event):
        if self.dir:
            openFileDialog = wx.DirDialog(self, "Choose a directory:",
                                          style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST | wx.DD_CHANGE_DIR)
            if openFileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed idea...
            path = openFileDialog.GetPath()
            self.pathInput.SetValue(path)


        else:
            openFileDialog = wx.FileDialog(self, "Choose a file:", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
            if openFileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed idea...
            path = openFileDialog.GetPath()
            self.pathInput.SetValue(path)


    def GetPath(self):
        path=self.pathInput.GetValue()
        if len(path)!=0:
            return path
        else:
            return None

    def SetPath(self, value):
        self.pathInput.SetValue(value)


def YesNo(parent, question, caption='Yes or no?'):
    dlg = wx.MessageDialog(parent, question, caption, wx.YES_NO | wx.ICON_QUESTION)
    result = dlg.ShowModal() == wx.ID_YES
    dlg.Destroy()
    return result


def getFilesInFoldr(fpath, full=False):
    try:
        lis = os.listdir(fpath)
    except:
        #GError('canot find folder%s'%fpath)
        return 0
    tmp = []
    for path in lis:
        if path.find('~') == -1:
            if full:
                tmp.append(os.path.join(fpath, path))
            else:
                tmp.append(path)
    if len(tmp) > 0:
        return tmp
    else:
        return 0


def isAttributExist(connection, schema, table, columns):
    sql = "SELECT EXISTS( SELECT * FROM information_schema.columns WHERE \
          table_schema = '%s' AND \
          table_name = '%s' AND\
          column_name='%s');" % (schema, table, columns)
    return connection.executeSql(sql, True, True)[0][0]


def isTableExist(connection, schema, table):
    sql = "SELECT EXISTS( SELECT * \
          FROM information_schema.tables \
          WHERE table_schema = '%s' AND \
          table_name = '%s');" % (schema, table)
    return connection.executeSql(sql, True, True)[0][0]


def removeLines(old_file, new_file, start, end):
    '''remove lines between two lines by line number and create new file '''
    data_list = open(old_file, 'r').readlines()
    temp_list = data_list[0:start]
    temp_list[len(temp_list):] = data_list[end:len(data_list)]
    open(new_file, 'wr').writelines(temp_list)

def OnSaveAs(parent):
    saveFileDialog = wx.FileDialog(parent, "Save file","", "",
                                       "files (*.*)|*.*", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

    if saveFileDialog.ShowModal() == wx.ID_CANCEL:
        return     # the user changed idea...

    # save the current contents in the file
    # this can be done with e.g. wxPython output streams:
    output_stream = (saveFileDialog.GetPath())
    return output_stream

def saveDict(fn, dict_rap):
    f = open(fn, "wb")
    w = csv.writer(f)
    for key, val in dict_rap.items():
        if val is None or val == '':
            continue
        w.writerow([key, val])
    f.close()


def readDict(fn):
    f = open(fn, 'rb')
    dict_rap = {}
    for key, val in csv.reader(f):
        try:
            dict_rap[key] = eval(val)
        except:
            val = '"' + val + '"'
            dict_rap[key] = eval(val)
    f.close()
    return (dict_rap)


def randomWord(length):
    return ''.join(random.choice(string.lowercase) for i in range(length))


def isTimeValid(time):
    RE = re.compile(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}$')
    return bool(RE.search(time))


def roundTime(dt, roundTo=60):
    """Round a datetime object to any time laps in seconds
    dt : datetime.datetime object, default now.
    roundTo : Closest number of seconds to round to, default 1 minute.
    Author: Thierry Husson 2012 - Use it as you want but don't blame me.
    """
    # if dt == None : dt = datetime.datetime.now()
    seconds = (dt - dt.min).seconds
    # // is a floor division, not a comment on following line:
    rounding = (seconds + roundTo / 2) // roundTo * roundTo  # rounding floor
    return dt + timedelta(0, rounding - seconds, -dt.microsecond)

