#!/usr/bin/env python

############################################################################
#
# MODULE:       m.printws
#
# AUTHOR(S):    Robert Kuszinger
#
# PURPOSE:      Creates carographic-like map sheet page from
#               a workspace composition
#
# COPYRIGHT:    (C) 2016 by GRASS development team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

#%module
#% description: Opens a workspace file and creates a map sheet according to its visible contents.
#% keyword: map
#% keyword: print
#% keyword: layout
#% keyword: workspace
#%end
#%option G_OPT_F_BIN_INPUT
#% key: input
#% description: Name of workspace file to process
#% required: YES
#% gisprompt: old,bin,file
#% guisection: Input
#%end
#%option
#% key: dpi
#% type: integer
#% answer: 150
#% multiple: no
#% description: DPI for the generated page
#% guisection: Output
#%end
#%option G_OPT_F_OUTPUT
#% description: Name of output file without extension
#% key: output
#% gisprompt: new,file,file
#% guisection: Output
#%end
#%option
#% key: page
#% type: string
#% options: A4landscape,A4portrait,LETTERlandscape,LETTERportrait,A3landscape,A3portrait
#% answer: A4landscape
#% description: Output map page size
#% guisection: Output
#%end
#%option
#% key: format
#% type: string
#% options: jpg,png,bmp,pdf,ppm
#% answer: pdf
#% description: Output file format
#% guisection: Output
#%end
#%option
#% key: maintitle
#% type: string
#% answer: %DISPLAY%
#% description: Main title of map sheet
#% guisection: Titles
#%end
#%option
#% key: titlefont
#% type: string
#% description: Font for title and postscript under the map
#% guisection: Titles
#%end
#%option G_OPT_C
#% key: titlecolor
#% type: string
#% description: Title text color
#% guisection: Titles
#%end
#%option
#% key: maintitlesize
#% type: integer
#% description: Main title font size in layout units
#% guisection: Titles
#%end
#%option
#% key: subtitle
#% type: string
#% description: Subtitle text above the map sheet in the middle
#% guisection: Titles
#%end
#%option
#% key: subtitlesize
#% type: integer
#% description: Main title font size in layout units
#% guisection: Titles
#%end
#%option
#% key: psunderleft
#% type: string
#% description: Postscript text under the map sheet on the left
#% guisection: Titles
#%end
#%option
#% key: psunderright
#% type: string
#% description: Postscript text under the map sheet on the right
#% guisection: Titles
#%end
#%option
#% key: psundercentral
#% type: string
#% description: Postscript text under the map sheet, centered
#% guisection: Titles
#%end
#%option
#% key: pssize
#% type: integer
#% description: Postscript text font size in layout units
#% guisection: Titles
#%end
#%option G_OPT_M_REGION
#% key:region
#% description: Name of region to use - uses workspace displayed area if empty
#% required: NO
#% gisprompt: old,windows,region
#% guisection: Input
#%end
#%flag
#% key: d
#% description: Debug - Leave temp files as is for alternative usage or checkup
#% guisection: Optional
#% suppress_required: yes
#%end
#%option
#% key: layunits
#% type: string
#% options: cm,mm,inch
#% answer: mm
#% description: Unit used for layout specification
#% guisection: Layout
#%end
#%option
#% key: pagemargin
#% type: string
#% description: Margins in layout units left,right,top,bottom
#% guisection: Layout
#%end
#%option
#% key: mapupperleft
#% type: string
#% answer: -1,-1
#% description: Map frame upper left coordinates - negative means centering
#% guisection: Layout
#%end
#%option
#% key: mapsize
#% type: string
#% answer: 1000
#% description: Map frame size in layout units as width,height
#% guisection: Layout
#%end
#%option
#% key: screendpi
#% type: integer
#% answer: 100
#% description: The DPI of your monitor
#% guisection: Layout
#%end


import sys
import os
import pwd
import atexit
import re
#from subprocess import call
import tempfile

import grass.script as grass
from grass.exceptions import CalledModuleError
from grass.script.utils import try_rmdir
import copy
import time

# initialize global vars
TMPFORMAT = 'BMP'
TMPLOC = None
SRCGISRC = None
GISDBASE = None
LAYERCOUNT = 10
# temp dir
REMOVE_TMPDIR = True
PROXIES = {}


# set upsize "constants"

UPSD = {}
ALLTASKDIC = {}
ALLTASKDIC['width'] = 1.0  # 1 by 1 correction if any
ALLTASKDIC['fontsize'] = 1.0  # 1 by 1 correction if any
UPSD['*'] = ALLTASKDIC

DVECTDIC = {}
DVECTDIC['size'] = 1.0  # 1 by 1 correction if any
UPSD['d.vect'] = DVECTDIC


# PAGE dictionary

PAGEDIC = {}
PAGEDIC['A4portrait'] = (210.0, 297.0, '', 'A4')
PAGEDIC['A4landscape'] = (297.0, 210.0, '', 'A4')
PAGEDIC['A3portrait'] = (297.0, 420.0, '', 'A3')
PAGEDIC['A3landscape'] = (420.0, 297.0, '', 'A3')
PAGEDIC['LETTERportrait'] = (215.9, 297.4, '', 'Letter')
PAGEDIC['LETTERlandscape'] = (297.4, 215.9, '', 'Letter')

# HTML DECODE
HTMLDIC = {}
HTMLDIC['&gt;'] = '>'
HTMLDIC['&lt;'] = '<'
HTMLDIC['&amp;'] = '&'
HTMLDIC['&quot;'] = '"'


def cleanup():

    # No cleanup is done here
    # see end of main()
    # kept for later
    grass.verbose(_("Module cleanup"))


def upsizeifnecessary(task, lastparam, value, upsize):
    val = UPSD.get('*').get(lastparam, 0.0)
    if val > 0:
        return str(float(value) * val * upsize)
    val = UPSD.get(task, {}).get(lastparam, 0.0)
    if val > 0:
        return str(float(value) * val * upsize)
    return value


def htmldecode(str):
    dic = HTMLDIC
    answer = str
    for key in dic:
        answer = answer.replace(key, dic[key])
    return answer


def readworkspace(wspname, upsize):
    # READS WORKSPACE FILE
    # Anyone familiar with XML please replace to a well formed parser
    # returns an array of two element arrays, where the two elements are:
    # opacity as string, being '1' for opacity 1 and
    # grass command reconstructed as a string from the worskpace definition
    # the bottommost layer should be first on the list, meanwhile any overlays (barscale
    # etc) should be last. The algorythm below does this exactly but using
    # regex

    searchmode = 'display'
    extents = []
    startnew = False
    parameters = ''    # working method
    flag = ''
    displaydic = {}    # adding support for more displays
    paramdic = {}      # migrating to grass.run calls / done 2016.07.30
    flagdic = {}
    task = ''
    layers = []
    grass.verbose(_("Layers: "))
    f = open(wspname, 'r')
    for line in f:

        if searchmode == 'display':
            # grass.message("  DISPLAY:"+line)    #was debug message
            # NEED TO HANDLE more displays...!
            m = re.search(
                '(display name="([a-zA-Z\ 0-9]+)".+dim="([0-9\,]+)".+extent="([0-9\.\-\,]+)")', line)
            if m:
                display = m.group(2)
                extentall = m.group(4)
                extents = extentall.split(",")
                dimall = m.group(3)
                dims = dimall.split(",")
                extents.extend(dims)
                searchmode = 'layer'
        if searchmode == 'layer':
            m = re.search(
                '(layer type="([a-zA-Z]+)".+checked="1"\ opacity="([0-9\.]+)"|overlay name="([a-zA-Z\.]+)")', line)
            if m:
                if m.group(2):
                    layer = m.group(2)
                    # if it is an overly, opacity is 100..... handle this
                    opacity = m.group(3)
                    startnew = True
                    if m.group(3).startswith('1'):
                        startnew = False
                    searchmode = 'task'
                elif m.group(4):
                    opactiy = '1'
                    task = m.group(4)
                    paramdic['task'] = task
                    startnew = False
                    searchmode = 'parameters'
            # in layer mode a /display could also come
            m = re.search('</display>', line)
            if m:
                # storing layers under display in a dictionary
                layers.insert(0, extents)
                displaydic[display] = copy.deepcopy(layers)
                layers = []
                searchmode = 'display'
        elif searchmode == 'task':
            m = re.search('task name="(.+)"', line)
            if m:
                task = m.group(1)
                searchmode = 'parameters'
                paramdic['task'] = task
        elif searchmode == 'parameters':
            m = re.search('(parameter) name="(.+)"|(flag) name="(.+)"', line)
            if m:
                if m.group(1) == 'parameter':
                    parameters = parameters + ' ' + m.group(2) + '="'
                    lastparam = m.group(2)
                else:  # adding flags handling
                    flag = flag + ' -' + m.group(4)
                    flagdic[m.group(4)] = m.group(4)
                    # grass.message("FLAG: "+m.group(4))    # was debug message
            else:
                m = re.search('<value>(.*)</value>', line)
                if m:
                    htmldecoded = htmldecode(m.group(1))
                    upsized = upsizeifnecessary(
                        task, lastparam, htmldecoded, upsize)
                    parameters = parameters + '' + str(upsized) + '"'
                    paramdic[lastparam] = str(upsized)
                else:
                    m = re.search('(</layer>)|(</overlay>)', line)
                    if m:
                        if startnew:
                            if m.group(1):
                                layers.insert(
                                    0, (opacity, task + flag + parameters, paramdic, flagdic))
                            else:
                                layers.append(
                                    (opacity, task + flag + parameters, paramdic, flagdic))
                            grass.verbose(_(opacity + ' >> ' + str(display) + " >> " + task +
                                            flag + parameters + " pd:" + str(paramdic) + " fd:" + str(flagdic)))
                        else:
                            if m.group(1):
                                layers.insert(
                                    0, ('1', task + flag + parameters, paramdic, flagdic))
                            else:
                                layers.append(
                                    ('1', task + flag + parameters, paramdic, flagdic))
                            grass.verbose(_('1 >> ' + str(display) + " >> " + task + flag +
                                            parameters + " pd:" + str(paramdic) + " fd:" + str(flagdic)))
                        parameters = ''
                        paramdic = {}
                        flag = ''
                        flagdic = {}
                        searchmode = 'layer'
    f.close()
    return displaydic


def converttommfrom(value, fromunit):
    #converting some basic units to mm
    d = {'mm': 1, 'cm': 10, 'inch': 25.4}
    return (value * d[fromunit])


def getpagemargins(option, unit):
    # we live on mm so convert user input as specified by unit
    d = {}
    if len(option) < 1:
        d['l'] = 25.0
        d['r'] = 25.0
        d['t'] = 25.0
        d['b'] = 25.0
        return d
    temp = option.split(",")
    d['l'] = converttommfrom(float(temp[0]), unit)
    if len(temp) < 4:
        d['r'] = d['l']
        d['t'] = d['l']
        d['b'] = d['l']
        return d
    d['r'] = converttommfrom(float(temp[1]), unit)
    d['t'] = converttommfrom(float(temp[2]), unit)
    d['b'] = converttommfrom(float(temp[3]), unit)
    return d


def getpagedata(page):
    # returns page description data dictionary for the selected page
    d = PAGEDIC
    w = d[page][0]
    h = d[page][1]
    return {'width': w, 'w': w, 'height': h, 'h': h, 'page': d[page][3], 'parameters': d[page][2]}


def getpagesizes(page):
    # return page sizes only in dictionary
    d = PAGEDIC
    w = d[page][0]
    h = d[page][1]
    return {'width': w, 'w': w, 'height': h, 'h': h}


def dictodots(dic, dpi):
    # takes all values from a dictionary and returns another dic with
    # incoming mm values converted to dots
    d2 = {}
    for key in dic:
        d2[key] = int(round(dic[key] / 25.4 * dpi))
    return d2


def dictomm(dic, dpi):
    # takes all values from a dictionary and returns another dic with
    # incoming dot values converted to mm
    d2 = {}
    for key in dic:
        d2[key] = dic[key] * 25.4 / dpi
    return d2


def getmaxframeindots(marginsindots, pagesizesindots):
    #returns available area on page in print dots (=pixels)
    l = marginsindots['l']
    r = pagesizesindots['w'] - marginsindots['r']
    t = marginsindots['t']
    b = pagesizesindots['h'] - marginsindots['b']
    return {'t': t, 'b': b, 'l': l, 'r': r}


def getmapUL(option, unit):
    # processes user entered option for map area upper left corner
    # r - right d - down from top left of page
    d = {}
    if len(option) < 1:
        d['r'] = 0.0
        d['d'] = 0.0
        return d
    temp = option.split(",")
    d['r'] = converttommfrom(float(temp[0]), unit)
    if len(temp) < 2:
        d['d'] = d['r']
        return d
    d['d'] = converttommfrom(float(temp[1]), unit)
    return d


def getmapsizes(option, unit):
    # processes user entered option for map size
    # width and height
    d = {}
    if len(option) < 1:
        d['w'] = 1000.0
        d['h'] = 1000.0
        return d
    temp = option.split(",")
    d['w'] = converttommfrom(float(temp[0]), unit)
    if len(temp) < 2:
        d['h'] = d['w']
        return d
    d['h'] = converttommfrom(float(temp[1]), unit)
    return d


def getmapframeindots(mapulindots, mapsizesindots, mxfd):
    d = {}
    # if map frame is bigger then area between margins it is
    # shrinked to fit
    mirrorwidth = abs(mxfd['r'] - mxfd['l']) + 1
    mirrorheight = abs(mxfd['b'] - mxfd['t']) + 1
    if mirrorwidth < mapsizesindots['w']:
        wr = float(mirrorwidth) / mapsizesindots['w']
        mapsizesindots['w'] = int(round(mapsizesindots['w'] * wr))
        mapsizesindots['h'] = int(round(mapsizesindots['h'] * wr))
    if mirrorheight < mapsizesindots['h']:
        hr = float(mirrorheight) / mapsizesindots['h']
        mapsizesindots['w'] = int(round(mapsizesindots['w'] * hr))
        mapsizesindots['h'] = int(round(mapsizesindots['h'] * hr))
    if mapulindots['r'] < 0:
        realw = min(mirrorwidth, mapsizesindots['w'])
        unusedhalf = int(round((mirrorwidth - realw) / 2))
        d['l'] = mxfd['l'] + unusedhalf
        d['r'] = mxfd['r'] - unusedhalf
    else:
        d['l'] = max(mxfd['l'], mapulindots['r'])
        d['r'] = min(mxfd['r'], mapulindots['r'] + mapsizesindots['w'])
    if mapulindots['d'] < 0:
        realh = min(mirrorheight, mapsizesindots['h'])
        unusedhalf = int(round((mirrorheight - realh) / 2))
        d['t'] = mxfd['t'] + unusedhalf
        d['b'] = mxfd['b'] - unusedhalf
    else:
        d['t'] = max(mxfd['t'], mapulindots['d'])
        d['b'] = min(mxfd['b'], mapulindots['d'] + mapsizesindots['h'])
    d['h'] = d['b'] - d['t'] + 1
    d['w'] = d['r'] - d['l'] + 1
    return d


def render(astring, pdic, fdic):
    grass.verbose(_("printws: Rendering into - BASE: " + LASTFILE))
    grass.verbose(_("printws: Rendering command: " + astring))

    pdic = copy.deepcopy(pdic)  # parameters
    fdic = copy.deepcopy(fdic)  # flags

    flags = ''
    for key in fdic:
        if key:
            # grass.message(" KEY:"+str(key))  #was debug message
            flags = flags + key
    pdic['flags'] = flags

    task = pdic['task']
    del pdic['task']
    # it should be replaced by grass.* API calls
    # os.system(astring)
    grass.run_command(task, **pdic)  # migration is going on


def getfontbypattern(kindpattern):
    # truetype and others which are likely utf8 start with capital font names
    # also some fonts with _ in names seemed to be utf8 for sure
    # fonts with space and : and without capital letter are excluded from
    # randomization
    s = grass.read_command("d.fontlist")
    safe = 'romans'
    split = s.splitlines()
    for l in split:
        # check if it has : or space.
        m = re.search('[\:\ ]+', l, re.IGNORECASE)
        if not m:
            m = re.search('(.*' + kindpattern + '.*)', l, re.IGNORECASE)
            if m:
                if (safe == 'romans') or (len(safe) > len(l)):
                    # change only to simpler variant
                    # simpler variant names are usually shorter
                    safe = l
    if safe == 'romans':
        for l in split:
            # check if it has : or space.
            m = re.search('[\:\ ]+', l, re.IGNORECASE)
            if not m:
                m = re.search('[A-Z].+[_].+', l, re.IGNORECASE)
                if m:
                    safe = l
                    return safe     # returns first suitable font, won't run through all of them
    return safe
    # print "printws: Selected font: " + safe


def decodetextmacros(text, dic):
    result = text
    for key in dic:
        result = re.sub(key, dic[key], result)
    return result

#-----------------------------------------------------
#-----------------------------------------------------
#-----------------------------------------------------
#------------------- MAIN ---------------------------
#-----------------------------------------------------
#-----------------------------------------------------
#-----------------------------------------------------
#-----------------------------------------------------


def main():

    global GISDBASE, LAYERCOUNT, LASTFILE
    textmacros = {}
    textmacros['%TIME24%'] = time.strftime("%H:%M:%S")
    textmacros['%DATEYMD%'] = time.strftime("%Y.%m.%d")
    textmacros['%DATEMDY%'] = time.strftime("%m/%d/%Y")
    textmacros['%USERNAME%'] = pwd.getpwuid(os.getuid())[0]

    # saves region for restoring at end
    savedregionname = "tmp.%s.%d" % (
        os.path.basename(sys.argv[0]), os.getpid())
    grass.run_command("g.region", save=savedregionname, overwrite=True)

    # getting/setting screen/print dpi ratio

    if len(options['dpi']) > 0:
        dpioption = float(options['dpi'])
    else:
        dpioption = 150.0

    if len(options['screendpi']) > 0:
        screendpioption = float(options['screendpi'])
    else:
        screendpioption = 100.0

    upsize = dpioption / screendpioption

    if len(options['input']) > 0:
        displays = readworkspace(options['input'], upsize)
    else:
        quit()

    textmacros['%GXW%'] = options['input']

    displaycounter = 0

    # there could be multiple displays in a workspace so we loop them
    # each display is a whole and independent file assembly
    for key in displays:
        textmacros['%DISPLAY%'] = key
        grass.verbose(_('printws: rendering display: ' + key))
        displaycounter = displaycounter + 1
        layers = copy.deepcopy(displays[key])

        # extracting extent information from layers dic and erase the item
        # extents[0-5] w s e n minz maxz ;  extents [6-9] window x y w h
        extents = layers[0]
        grass.verbose("m.printws: EXTENTS from workspace:" +
                      str(extents))  # was debug message
        del layers[0]

        regionmode = ''
        if len(options['region']) > 0:
            grass.run_command("g.region", region=options['region'])
            regionmode = 'region'
        else:
            grass.run_command("g.region", "", w=extents[0], s=extents[
                              1], e=extents[2], n=extents[3])
            regionmode = 'window'

        # setting GRASS rendering environment
        
        # dummy file name is defined since the following lines
        # when switching on the cairo driver would create
        # an empty map.png in the current directory
        os.environ['GRASS_RENDER_FILE'] = os.path.join(TMPDIR, str(os.getpid(
                    )) + '_DIS_' + str(00) + '_GEN_' + str(00) + '.png')
        os.environ['GRASS_RENDER_IMMEDIATE'] = 'cairo'
        os.environ['GRASS_RENDER_FILE_READ'] = 'TRUE'
        os.environ['GRASS_RENDER_TRANSPARENT'] = 'TRUE'
        os.environ['GRASS_RENDER_FILE_COMPRESSION'] = '0'
        os.environ['GRASS_RENDER_FILE_MAPPED'] = 'TRUE'

        # reading further options and setting defaults
        
        if len(options['page']) > 0:
            pageoption = options['page']
        else:
            pageoption = 'A4landscape'
        # parsing titles, etc.

        if len(options['titlefont']) > 1:
            isAsterisk = options['titlefont'].find('*')
            if isAsterisk > 0:
                titlefont = getfontbypattern(
                    options['titlefont'].replace('*', ''))
            else:
                titlefont = options['titlefont']
        else:
            titlefont = getfontbypattern('Open')  # try to find something UTF-8
        grass.verbose(_("printws: titlefont: " + titlefont))

        if len(options['titlecolor']) > 1:
            titlecolor = options['titlecolor']
        else:
            titlecolor = black

        if len(options['maintitlesize']) > 1:
            maintitlesize = converttommfrom(
                float(options['maintitlesize']), options['layunits'])
        else:
            maintitlesize = 10.0

        if len(options['subtitlesize']) > 1:
            subtitlesize = converttommfrom(
                float(options['subtitlesize']), options['layunits'])
        else:
            subtitlesize = 7.0

        if len(options['pssize']) > 1:
            pssize = converttommfrom(
                float(options['pssize']), options['layunits'])
        else:
            pssize = 5.0

        # Please fasten your seatbelts :) Calculations start here.
        # -------------------------------------------------------------------

        pagesizes = getpagesizes(pageoption)
        pagesizesindots = dictodots(pagesizes, dpioption)

        # Leave space for titles up and ps down
        upperspace = 0
        subtitletop = 0
        if len(options['maintitle']) > 0:
            upperspace = upperspace + maintitlesize * 1.2
            subtitletop = maintitlesize * 1.2
        if len(options['subtitle']) > 0:
            upperspace = upperspace + subtitlesize * 1.2
        lowerspace = 0
        if (len(options['psundercentral']) > 0) or (len(options['psunderright']) > 0) or (len(options['psunderleft']) > 0):
            lowerspace = lowerspace + pssize * 1.2

        os.environ['GRASS_RENDER_WIDTH'] = str(pagesizesindots['w'])
        os.environ['GRASS_RENDER_HEIGHT'] = str(pagesizesindots['h'])

        pagemargins = getpagemargins(
            options['pagemargin'], options['layunits'])
        pagemarginsindots = dictodots(pagemargins, dpioption)

        # Getting max drawing area in dots
        mxfd = getmaxframeindots(pagemarginsindots, pagesizesindots)
        maxframe = str(mxfd['t']) + ',' + str(mxfd['b']) + \
            ',' + str(mxfd['l']) + ',' + str(mxfd['r'])

        # convert font size to percentage for d.text
        mxfmm = dictomm(mxfd, dpioption)
        maintitlesize = maintitlesize / (mxfmm['b'] - mxfmm['t']) * 100.0
        subtitlesize = subtitlesize / (mxfmm['b'] - mxfmm['t']) * 100.0
        pssize = pssize / (mxfmm['r'] - mxfmm['l']) * 100.0
        # subtitle location is another issue
        subtitletoppercent = 100.0 - subtitletop / \
            (mxfmm['b'] - mxfmm['t']) * 100.0

        mapul = getmapUL(options['mapupperleft'], options['layunits'])
        mapulindots = dictodots(mapul, dpioption)

        mapsizes = getmapsizes(options['mapsize'], options['layunits'])
        mapsizesindots = dictodots(mapsizes, dpioption)

        # Correcting map area ratio to ratio of region edges
        # OR screen window edges depeding on "regionmode"
        # for later:     grass.use_temp_region()
        s = grass.read_command("g.region", flags='p')
        kv = grass.parse_key_val(s, sep=':')
        regioncols = float(kv['cols'].strip())
        regionrows = float(kv['rows'].strip())
        ewres = float(kv['ewres'].strip())
        nsres = float(kv['nsres'].strip())
        sizex = regioncols * ewres
        sizey = regionrows * nsres

        if regionmode == 'region':
            hregionratio = sizex / sizey
            grass.verbose(_("printws: REGION MODE - region "))
        else:  # surprisingly doing the SAME
            # using screen window ratio for map area
            # next line was a test for this but didn't help on gadgets positioning
            #hregionratio = float(extents[8]) / float(extents[9])
            hregionratio = sizex / sizey
            grass.verbose(_("printws: REGION MODE - window"))
        hmapratio = mapsizes['w'] / mapsizes['h']

        grass.verbose(_("printws: raw mapsizes: " + str(mapsizesindots)))
        grass.verbose(_("printws: hr: " + str(hregionratio)))
        grass.verbose(_("printws: hm: " + str(hmapratio)))
        if hregionratio > hmapratio:
            grass.verbose(
                _("printws: Map area height correction / " + str(hregionratio)))
            mapsizes['h'] = mapsizes['w'] / hregionratio
        elif hregionratio < hmapratio:
            grass.verbose(
                _("printws: Map area width correction * " + str(hregionratio)))
            mapsizes['w'] = mapsizes['h'] * hregionratio
        mapsizesindots = dictodots(mapsizes, dpioption)

        # changing region resolution to match print resolution
        # to eliminate unnecessary CPU/data transfer (make it faster
        # with invisible detail loss only). Does only downscale.
        colsregiontomap = mapsizesindots['w'] / regioncols
        rowsregiontomap = mapsizesindots['h'] / regionrows

        newewres = ewres
        newnsres = nsres

        if colsregiontomap < 1:
            newewres = ewres / colsregiontomap
        if rowsregiontomap < 1:
            newnsres = nsres / rowsregiontomap

        grass.run_command("g.region", ewres=str(newewres), nsres=str(newnsres))

        # Getting mapping area in dots
        # Correcting mxfd to leave space for title and subscript
        pagemarginstitles = copy.deepcopy(pagemargins)
        pagemarginstitles['t'] = pagemarginstitles['t'] + upperspace
        pagemarginstitles['b'] = pagemarginstitles['b'] + lowerspace
        pagemarginsindotstitles = dictodots(pagemarginstitles, dpioption)
        mxfdtitles = getmaxframeindots(
            pagemarginsindotstitles, pagesizesindots)

        mpfd = getmapframeindots(mapulindots, mapsizesindots, mxfdtitles)
        mapframe = str(mpfd['t']) + ',' + str(mpfd['b']) + \
            ',' + str(mpfd['l']) + ',' + str(mpfd['r'])

        grass.verbose(_("printws: DOT VALUES ARE:"))
        grass.verbose(_("printws: maxframe: " + str(mxfd)))
        grass.verbose(_("printws: maxframe: " + maxframe))
        grass.verbose(_("printws: mapframe: " + str(mpfd)))
        grass.verbose(_("printws: mapframe: " + mapframe))
        grass.verbose(_("printws: page: " + str(pagesizesindots)))
        grass.verbose(_("printws: margins: " + str(pagemarginsindots)))
        grass.verbose(_("printws: mapUL: " + str(mapulindots)))
        grass.verbose(
            _("printws: mapsizes (corrected): " + str(mapsizesindots)))
        grass.verbose(_("printws: ewres (corrected): " + str(newewres)))
        grass.verbose(_("printws: nsres (corrected): " + str(newnsres)))

        # quit()

        # ------------------- INMAP -------------------

        imcommand = 'convert  -limit memory 720000000 -limit map 720000000 -units PixelsPerInch -density ' + \
            str(int(dpioption)) + ' '

        if os.name == 'nt':
            imcommand = 'magick ' + imcommand

        os.environ['GRASS_RENDER_FRAME'] = mapframe

        grass.verbose(_("printws: Rendering: the following layers: "))
        lastopacity = '-1'

        for lay in layers:
            grass.verbose(_(lay[1] + ' at: ' + lay[0] + ' opacity'))
            if lay[0] == '1':
                if lastopacity <> '1':
                    LASTFILE = os.path.join(TMPDIR, str(os.getpid(
                    )) + '_DIS_' + str(displaycounter) + '_GEN_' + str(LAYERCOUNT) + '.' + TMPFORMAT)
                    os.environ['GRASS_RENDER_FILE'] = LASTFILE
                    LAYERCOUNT = LAYERCOUNT + 2
                    imcommand = imcommand + ' ' + LASTFILE
                    lastopacity = '1'
                render(lay[1], lay[2], lay[3])
            else:
                lastopacity = lay[0]
                LASTFILE = os.path.join(TMPDIR, str(os.getpid(
                )) + '_DIS_' + str(displaycounter) + '_GEN_' + str(LAYERCOUNT) + '.' + TMPFORMAT)
                LAYERCOUNT = LAYERCOUNT + 2
                os.environ['GRASS_RENDER_FILE'] = LASTFILE
                grass.verbose("LAY: " + str(lay))
                render(lay[1], lay[2], lay[3])
                imcommand = imcommand + \
                    ' \( ' + LASTFILE + ' -channel a -evaluate multiply ' + \
                    lay[0] + ' +channel \)'

        # setting resolution back to pre-script state since map rendering is
        # finished

        grass.run_command("g.region", ewres=str(newewres), nsres=str(newnsres))

        # ------------------- OUTSIDE MAP texts, etc -------------------
        os.environ['GRASS_RENDER_FRAME'] = maxframe

        dict = {}
        dict['task'] = "d.text"
        dict['color'] = titlecolor
        dict['font'] = titlefont
        dict['charset'] = "UTF-8"

        if len(options['maintitle']) > 1:
            dict['text'] = decodetextmacros(options['maintitle'], textmacros)
            dict['at'] = "50,99"
            dict['align'] = "uc"
            dict['size'] = str(maintitlesize)
            render(str(dict), dict, {})

        if len(options['subtitle']) > 1:
            dict['text'] = decodetextmacros(options['subtitle'], textmacros)
            dict['at'] = "50," + str(subtitletoppercent)
            dict['align'] = "uc"
            dict['size'] = str(subtitlesize)
            render(str(dict), dict, {})

        dict['size'] = str(pssize)

        if len(options['psundercentral']) > 1:
            dict['text'] = decodetextmacros(
                options['psundercentral'], textmacros)
            dict['at'] = "50,1"
            dict['align'] = "lc"
            render(str(dict), dict, {})
        if len(options['psunderleft']) > 1:
            dict['text'] = decodetextmacros(options['psunderleft'], textmacros)
            dict['at'] = "0,1"
            dict['align'] = "ll"
            render(str(dict), dict, {})
        if len(options['psunderright']) > 1:
            dict['text'] = decodetextmacros(
                options['psunderright'], textmacros)
            dict['at'] = "100,1"
            dict['align'] = "lr"
            render(str(dict), dict, {})

        # ------------------- GENERATING OUTPUT FILE -------------------

        if len(options['output']) > 1:
            output = options['output']
        else:
            output = 'map_' + str(os.getpid())

        # remove extension AND display number and naming if any
        output = os.path.splitext(output)[0]
        output = re.sub('_DISPLAY_[0-9]+_.*', '', output)

        if len(options['format']) > 1:
            extension = options['format']
        else:
            extension = 'pdf'

        displaypart = ''
        if len(displays) > 1:
            displaypart = '_DISPLAY_' + str(displaycounter) + '_' + key

        pagedata = getpagedata(pageoption)
        #params= ' -extent '+str(pagesizesindots['w'])+'x'+str(pagesizesindots['h'])+' -gravity center -compress jpeg -page '+pagedata['page']+' '+pagedata['parameters']+' -units PixelsPerInch -density '+str(dpioption)+'x'+str(dpioption)+' '
        params = ' -compress jpeg -quality 92 ' + \
            pagedata['parameters'] + ' -units PixelsPerInch -density ' + \
            str(int(dpioption)) + ' '

        imcommand = imcommand + ' -layers flatten ' + params + \
            '"' + output + displaypart + '.' + extension + '"'

        grass.verbose(
            _('printws: And the imagemagick command is... ' + imcommand))
        os.system(imcommand)

    if not flags['d']:
        grass.verbose(_('printws: Doing graceful cleanup...'))
        os.system('rm ' + os.path.join(TMPDIR, str(os.getpid()) + '*_GEN_*'))
        if REMOVE_TMPDIR:
            try_rmdir(TMPDIR)
        else:
            grass.message("\n%s\n" % _(
                "printws: Temp dir remove failed. Do it yourself, please:"))
            sys.stderr.write('%s\n' % TMPDIR % ' <---- this')

    # restoring pre-script region
    grass.run_command("g.region", region=savedregionname, overwrite=True)
    grass.run_command('g.remove', flags="f", type="region",
                      pattern=savedregionname)

    return 0

if __name__ == "__main__":
    options, flags = grass.parser()
    global TMPDIR
    TMPDIR = tempfile.mkdtemp()
    atexit.register(cleanup)
    sys.exit(main())
