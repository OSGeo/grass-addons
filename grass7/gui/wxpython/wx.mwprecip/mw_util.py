#!/usr/bin/env python
import re
import os
import sys
import random
import string
import wx
import csv
from datetime import timedelta
import wx.lib.filebrowsebutton as filebrowse
import codecs
from core.gcmd          import GMessage, GError
from grass.script       import core as grass
import grass.script as grass

import time
from datetime import datetime
import logging


class StaticContext():
    def __init__(self):
        gisenvDict = grass.gisenv()
        pathToMapset = os.path.join(gisenvDict['GISDBASE'], gisenvDict['LOCATION_NAME'], gisenvDict['MAPSET'])
        self.tmp_mapset_path = os.path.join(pathToMapset, "mwprecip_data")


    def getTmpPath(self):
        return self.tmp_mapset_path

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
    # def __init__(self, parent, label,key, cats=False):
    def __init__(self, parent, label, style=0):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        statText = wx.StaticText(self, id=wx.ID_ANY, label=label)
        #if cats:
        #self.ctrl = gselect.VectorCategorySelect(parent=self, giface=self._giface)  # TODO gifece
        #else:
        self.text = wx.TextCtrl(self, id=wx.ID_ANY, style=style)
        #self.key=key
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(statText, flag=wx.EXPAND)
        sizer.Add(self.text, flag=wx.EXPAND)
        self.SetSizer(sizer)

    def GetKey(self):
        return self.key

    def GetValue(self):
        value = self.text.GetValue()
        if value == '':
            return None
        else:
            return value

    def SetValue(self, value):
        self.text.SetValue((str(value)))
'''
class TextInput1(wx.Panel):
    def __init__(self, parent, label, tmpPath=None):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.sizer=wx.BoxSizer(wx.VERTICAL)
        fExt = None
        if not fExt:
            fMask = '*'
        else:
            fMask = '%s files (*%s)|*%s|Files (*)|*' % (fExt[1:].upper(), fExt, fExt)
        fbb = filebrowse.FileBrowseButton(parent = self, id = wx.ID_ANY, fileMask = fMask,
                                           labelText = '',
                                          dialogTitle = 'Choose file',
                                          buttonText = 'Browse',
                                          startDirectory = os.getcwd(), fileMode = 'file',
                                          changeCallback = self.OnSetValue)

        self.sizer.Add(item = fbb, proportion = 0,
                        flag = wx.EXPAND | wx.RIGHT, border = 5)

        # A file browse button is a combobox with two children:
        # a textctl and a button;
        # we have to target the button here
            # widget for interactive input
        ifbb = wx.TextCtrl(parent = self, id = wx.ID_ANY,
                           style = wx.TE_MULTILINE,
                           size = (-1, 75))
        #if p.get('value', '') and os.path.isfile(p['value']):
        #    f = open(p['value'])
         #   ifbb.SetValue(''.join(f.readlines()))
         #   f.close()

        ifbb.Bind(wx.EVT_TEXT, self.OnFileText)

        btnLoad = wx.Button(parent = self, id = wx.ID_ANY, label = _("&Load"))
        btnLoad.SetToolTipString(_("Load and edit content of a file"))
        btnLoad.Bind(wx.EVT_BUTTON, self.OnFileLoad)
        btnSave = wx.Button(parent = self, id = wx.ID_ANY, label = _("&Save as"))
        btnSave.SetToolTipString(_("Save content to a file for further use"))
        btnSave.Bind(wx.EVT_BUTTON, self.OnFileSave)

        fileContentLabel = wx.StaticText(parent=self,
            id=wx.ID_ANY,
            label=_('or enter values directly:'))
        fileContentLabel.SetToolTipString(
            _("Enter file content directly instead of specifying"
              " a file."
              " Temporary file will be automatically created."))
        self.sizer.Add(item=fileContentLabel,
                        proportion = 0,
                        flag = wx.EXPAND | wx.RIGHT | wx.LEFT | wx.BOTTOM, border = 5)
        self.sizer.Add(item = ifbb, proportion = 1,
                        flag = wx.EXPAND | wx.RIGHT | wx.LEFT, border = 5)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add(item = btnLoad, proportion = 0,
                     flag = wx.ALIGN_RIGHT | wx.RIGHT, border = 10)
        btnSizer.Add(item = btnSave, proportion = 0,
                     flag = wx.ALIGN_RIGHT)
        self.sizer.Add(item = btnSizer, proportion = 0,
                        flag = wx.ALIGN_RIGHT | wx.RIGHT | wx.TOP, border = 5)

    def OnFileText(self, event):
        """File input interactively entered"""
        text = event.GetString()
        #p = self.task.get_param(value = event.GetId(), element = 'wxId', raiseError = False)
        #if not p:
        #    return # should not happen
        #win = self.FindWindowById(p['wxId'][0])
        if text:
        #    filename = win.GetValue()
            if not filename :  # m.proj has - as default
        #        filename = grass.tempfile()
        #        win.SetValue(filename)

        #    enc = locale.getdefaultlocale()[1]
            f = codecs.open(filename, encoding = enc, mode = 'w', errors='replace')
            try:
                f.write(text)
                if text[-1] != os.linesep:
                    f.write(os.linesep)
            finally:
                f.close()
        else:
        #    win.SetValue('')

    def OnFileSave(self, event):
        """Save interactive input to the file"""
        wId = event.GetId()
        win = {}
        for p in self.task.params:
            if wId in p.get('wxId', []):
                win['file'] = self.FindWindowById(p['wxId'][0])
                win['text'] = self.FindWindowById(p['wxId'][1])
                break

        if not win:
            return

        text = win['text'].GetValue()
        if not text:
            GMessage(parent = self,
                          message = _("Nothing to save."))
            return

        dlg = wx.FileDialog(parent = self,
                            message = "Save input as...",
                            defaultDir = os.getcwd(),
                            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            #enc = locale.getdefaultlocale()[1]
            f = codecs.open(path, mode = 'w', errors='replace')
            try:
                f.write(text + os.linesep)
            finally:
                f.close()

            win['file'].SetValue(path)

        dlg.Destroy()

    def OnFileLoad(self, event):
        """Load file to interactive input"""
        me = event.GetId()
        win = dict()
        for p in self.task.params:
            if 'wxId' in p and me in p['wxId']:
                win['file'] = self.FindWindowById(p['wxId'][0])
                win['text'] = self.FindWindowById(p['wxId'][1])
                break

        if not win:
            return

        path = win['file'].GetValue()
        if not path:
            gcmd.GMessage(parent = self,
                          message = _("Nothing to load."))
            return

        data = ''
        try:
            f = open(path, "r")
        except IOError as e:
            gcmd.GError(parent = self, showTraceback = False,
                        message = _("Unable to load file.\n\nReason: %s") % e)
            return

        try:
            data = f.read()
        finally:
            f.close()

        win['text'].SetValue(data)

    def OnSetValue(self, event):
        """Retrieve the widget value and set the task value field
        accordingly.

        Use for widgets that have a proper GetValue() method, i.e. not
        for selectors.
        """
        myId = event.GetId()
        me = wx.FindWindowById(myId)
        name = me.GetName()

        found = False
        for porf in self.task.params + self.task.flags:
            if 'wxId' not in porf:
                continue
            if myId in porf['wxId']:
                found = True
                break

        if not found:
            return

        if name == 'GdalSelect':
            porf['value'] = event.dsn
        elif name == 'ModelParam':
            porf['parameterized'] = me.IsChecked()
        else:
            if isinstance(me, wx.SpinCtrl):
                porf['value'] = str(me.GetValue())
            else:
                porf['value'] = me.GetValue()

        self.OnUpdateValues(event)

        event.Skip()
'''
class TextInput(wx.Panel):
    def __init__(self, parent, label ):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.context=StaticContext()

        self.tmpPath = None
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
        if self.firstDirInp is False: #intitialization
            self.firstDirInp = True
            if self.tmpPath is None:
                self.tmpPath = os.path.join(self.context.getTmpPath(), 'tmp%s'%randomWord(3))
                self.pathInput.SetValue(self.tmpPath)

        io=open(self.tmpPath,'w')
        io.writelines(self.directInp.GetValue())
        io.close()

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
        if not os.path.isfile(self.pathInput.GetValue()):
            return -1
        io = open(self.pathInput.GetValue(), 'r')
        str = io.read()
        try:
            self.directInp.SetValue(str)
            return 1
        except IOError as e:
            print("I/O error({}): {}".format(e.errno, e.strerror))
            return -1
        except ValueError:
            print("Could not decode text")
            return -1
        except:
            print("Unexpected error: {}".format(sys.exc_info()[0]))
            raise
            return -1

        io.close()

    def GetPath(self):
        path=self.pathInput.GetValue()
        if path=='':
            return None
        else:
            return path

    def SetPath(self, value):
        if value is None:
            return
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
        # GError('canot find folder%s'%fpath)
        return 0
    tmp = []
    for path in lis:
        if path.find('~') == -1:
            if full:
                tmp.append(os.path.join(fpath, path))
            else:

                tmp.append(path)

    return tmp


class MeasureTime():
    def __init__(self,total_count_step=14):
        self.startLast=None
        self.total_count_step=total_count_step
        self.end=None
        self.start=None
        self.logger = logging.getLogger('mwprecip.MeasureTime')
        self.set_counter=0

    def timeMsg(self,msg,end=False,step=1):
        self.set_counter += 1
        if self.start is None:
            self.start = time.time()
            self.startLast= self.start
            self.logger.info("Measuring time - START: %s "%str(datetime.now()))
            self.logger.info(msg)
        else:
            self.end = time.time()
            elapsedTotal=self.end - self.start
            elapsedLast=self.end-self.startLast
            self.startLast=self.end
            grass.percent(self.set_counter,self.total_count_step,1)

            self.logger.info("TOTAL TIME < %s > : %s"%(msg,elapsedTotal))
            self.logger.info("LAST PART TIME< %s > : %s"%(msg,elapsedLast))

            if end:
                grass.percent(self.total_count_step,self.total_count_step,1)
                self.logger.info("TOTAL TIME e: %s"%(elapsedTotal))
                self.logger.info("Measuring time - END: %s "%str(datetime.now()))

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
    open(new_file, 'w+').writelines(temp_list)


def OnSaveAs(parent):
    saveFileDialog = wx.FileDialog(parent, "Save file", "", "",
                                   "files (*.*)|*.*", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

    if saveFileDialog.ShowModal() == wx.ID_CANCEL:
        return  # the user changed idea...

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
    f = open(fn, 'r')
    dict_rap = {}
    try:
        for key, val in csv.reader(f):
            try:
                dict_rap[key] = eval(val)
            except:
                val = '"' + val + '"'
                dict_rap[key] = eval(val)
        f.close()
        return (dict_rap)
    except IOError as e:
        print("I/O error({}): {}".format(e.errno, e.strerror))




def randomWord(length):
    return ''.join(
        random.choice(string.ascii_lowercase) for i in range(length)
    )


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
