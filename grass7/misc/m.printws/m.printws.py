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
import tempfile
import grass.script as grass
from grass.exceptions import CalledModuleError
from grass.script.utils import try_rmdir
import copy
import time
import unicodedata

# workspace file is XML so we use an XML parser
import xml.dom.minidom

# initialize global vars
TMPFORMAT = 'BMP'
TMPLOC = None
SRCGISRC = None
GISDBASE = None
LAYERCOUNT = 10
# temp dir
REMOVE_TMPDIR = True
PROXIES = {}

# UPSIZE is better global as it is universal at a moment
# an we save a lot of parameter passing when parsing xml
global UPSIZE
UPSIZE = 1.0

# set upsize "constants"

UPSD = {}
ALLTASKDIC = {}
ALLTASKDIC['width'] = 1.0  # 1 by 1 correction if any
UPSD['*'] = ALLTASKDIC

DVECTDIC = {}
DVECTDIC['size'] = 1.0  # symbol size
DVECTDIC['label_size'] = 1.5  # label size
UPSD['d.vect'] = DVECTDIC

DGRIDDIC = {}
DGRIDDIC['size'] = 0.0  # force not touching grid line distance
DGRIDDIC['fontsize'] = 1.0  # 1 by 1 correction if any
UPSD['d.grid'] = DGRIDDIC



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




# test
# m.printws.py --overwrite input=/home/kuszi/grassdata/workspaces_7/EURASEAA.gxw dpi=100 output=/home/kuszi/grassdata/mapdefs/euraseeaa.bmp page=A4portrait maintitle=$DISPLAY pagemargin=0

def upsizeifnecessary(task, lastparam, value, upsize):
    val = UPSD.get('*').get(lastparam, 0.0)
    print task + " " + lastparam + " " + str(value) + " " + str(upsize)
    if val > 0:
        print "## " + task + " " + lastparam + " " + str(value) + " " + str(upsize) + " > " + str(float(value) * val * upsize)
        return str(float(value) * val * UPSIZE)
    val = UPSD.get(task, {}).get(lastparam, 0.0)
    if val > 0:
        print "## " + task + " " + lastparam + " " + str(value) + " " + str(upsize) + " > " + str(float(value) * val * upsize)
        return str(float(value) * val * UPSIZE)
    return value


def htmldecode(str):
    dic = HTMLDIC
    answer = str
    for key in dic:
        answer = answer.replace(key, dic[key])
    return answer



def processlayer(dom,flagdic,paramdic):
    task = dom.getElementsByTagName("task")[0]
    command = task.getAttribute('name')
    params = task.getElementsByTagName("parameter")
    paramdic['task'] = command
    for p in params:
        paramdic[p.getAttribute('name')] = upsizeifnecessary(paramdic['task'],p.getAttribute('name'),p.getElementsByTagName("value")[0].childNodes[0].data,UPSIZE)
    
    flags = task.getElementsByTagName("flag")
    for f in flags:
        if (f.getAttribute('name') <> 'verbose') and (f.getAttribute('name') <> 'overwrite') and (f.getAttribute('name') <> 'quiet'):
            flagdic [f.getAttribute('name')] = f.getAttribute('name')


def processoverlay(dom,flagdic,paramdic):
    params = dom.getElementsByTagName("parameter")
    for p in params:
        paramdic[p.getAttribute('name')] = upsizeifnecessary(paramdic['task'],p.getAttribute('name'),p.getElementsByTagName("value")[0].childNodes[0].data,UPSIZE)
    
    flags = dom.getElementsByTagName("flag")
    for f in flags:
        if (f.getAttribute('name') <> 'verbose') and (f.getAttribute('name') <> 'overwrite') and (f.getAttribute('name') <> 'quiet'):
            flagdic [f.getAttribute('name')] = f.getAttribute('name')


def processlayers(dom,l):
    # processing layers of a display. Layers are returned in the l array
    for lay in dom:
        if lay.getAttribute('checked') == '1':
            paramdic = {}
            flagdic = {}
            opacity = lay.getAttribute('opacity')
            if opacity.startswith('1'):
                opacity = '1'
            processlayer(lay,flagdic,paramdic)
            l.insert(
                0, (opacity, paramdic['task'] , paramdic, flagdic))

def processoverlays(dom,l):
    # processing layers of a display. Layers are returned in the l array
    for lay in dom:
        paramdic = {}
        flagdic = {}
        task = lay.getAttribute('name')
        paramdic['task'] = task
        opacity = '1'
        processoverlay(lay,flagdic,paramdic)
        l.append((opacity, paramdic['task'] , paramdic, flagdic))


def readworkspace(wspname):
    # READS WORKSPACE FILE
    displaydic = {}    # adding support for more displays
    grass.verbose(_("Layers: "))
    f = open(wspname, 'r')
    text = f.read()
    f.close()
    model = xml.dom.minidom.parseString(text)
    displays = model.getElementsByTagName("display")
    for display in displays:
        extents = []
        layers = []
        displayname = display.getAttribute('name')
        extentall = display.getAttribute('extent')
        extents = extentall.split(",")
        dimall = display.getAttribute('dim')
        dims = dimall.split(",")
        extents.extend(dims)
        layersmodel = display.getElementsByTagName('layer')
        processlayers(layersmodel,layers)
        overlaysmodel = display.getElementsByTagName('overlay')
        processoverlays(overlaysmodel,layers)
        layers.insert(0, extents)
        displaydic[displayname]=layers
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
    # Yes, indeed, macros ARE case sensitive !!!
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
    # %nam% macros are kept for backward compatibility
    textmacros['%TIME24%'] = time.strftime("%H:%M:%S")
    textmacros['%DATEYMD%'] = time.strftime("%Y.%m.%d")
    textmacros['%DATEMDY%'] = time.strftime("%m/%d/%Y")
    textmacros['%USERNAME%'] = pwd.getpwuid(os.getuid())[0]
    # using $ for macros in the future. New items should be created
    # exclusively as $macros later on
    textmacros['\$TIME24'] = textmacros['%TIME24%']
    textmacros['\$DATEYMD'] = textmacros['%DATEYMD%']
    textmacros['\$DATEMDY'] = textmacros['%DATEMDY%']
    textmacros['\$USERNAME'] = textmacros['%USERNAME%']

    textmacros['\$SPC'] = u'\u00A0' #?? d.text won't display at string end hmmm


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

    global UPSIZE
    UPSIZE = float(dpioption) / float(screendpioption)

    if len(options['input']) > 0:
        displays = readworkspace(options['input'])
    else:
        quit()

    textmacros['%GXW%'] = options['input']
    textmacros['\$GXW'] = textmacros['%GXW%']

    displaycounter = 0

    # there could be multiple displays in a workspace so we loop them
    # each display is a whole and independent file assembly
    for key in displays:
        textmacros['%DISPLAY%'] = key
        textmacros['\$DISPLAY'] = key
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

        if len(options['titlefont']) > 0:
            isAsterisk = options['titlefont'].find('*')
            if isAsterisk > 0:
                titlefont = getfontbypattern(
                    options['titlefont'].replace('*', ''))
            else:
                titlefont = options['titlefont']
        else:
            titlefont = getfontbypattern('Open')  # try to find something UTF-8
        grass.verbose(_("printws: titlefont: " + titlefont))

        if len(options['titlecolor']) > 0:
            titlecolor = options['titlecolor']
        else:
            titlecolor = black

        if len(options['maintitlesize']) > 0:
            maintitlesize = converttommfrom(
                float(options['maintitlesize']), options['layunits'])
        else:
            maintitlesize = 10.0

        if len(options['subtitlesize']) > 0:
            subtitlesize = converttommfrom(
                float(options['subtitlesize']), options['layunits'])
        else:
            subtitlesize = 7.0


        if len(options['pssize']) > 0:
            pssize = converttommfrom(
                float(options['pssize']), options['layunits'])
        else:
            pssize = 5.0

        # Please fasten your seatbelts :) Calculations start here.
        # -------------------------------------------------------------------

        pagesizes = getpagesizes(pageoption)
        pagesizesindots = dictodots(pagesizes, dpioption)

        # Leave space for titles up and ps down - still in mm !!
        upperspace = 0
        subtitletop = 0
        titletop = 0
        if len(options['maintitle']) > 0:
            titletop = 0.4 * maintitlesize
            upperspace = upperspace + titletop + maintitlesize
        if len(options['subtitle']) > 0:
            subtitletop = upperspace + 0.4 * subtitlesize
            upperspace = subtitletop + subtitlesize + 1
        lowerspace = 0
        if (len(options['psundercentral']) > 0) or (len(options['psunderright']) > 0) or (len(options['psunderleft']) > 0):
            lowerspace = lowerspace + pssize + 2

        os.environ['GRASS_RENDER_WIDTH'] = str(pagesizesindots['w'])
        os.environ['GRASS_RENDER_HEIGHT'] = str(pagesizesindots['h'])

        pagemargins = getpagemargins(
            options['pagemargin'], options['layunits'])
        pagemarginsindots = dictodots(pagemargins, dpioption)

        # Getting max drawing area in dots
        mxfd = getmaxframeindots(pagemarginsindots, pagesizesindots)
        maxframe = str(mxfd['t']) + ',' + str(mxfd['b']) + \
            ',' + str(mxfd['l']) + ',' + str(mxfd['r'])

        # convert font size in mm to percentage for d.text
        mxfmm = dictomm(mxfd, dpioption)
        maintitlesize = float(maintitlesize) / (mxfmm['b'] - mxfmm['t']) * 100.0
        subtitlesize = float(subtitlesize) / (mxfmm['b'] - mxfmm['t']) * 100.0
        
        pssize = float(pssize) / (mxfmm['r'] - mxfmm['l']) * 100.0
        # subtitle location is another issue
        subtitletoppercent = 100.0 - subtitletop / \
            (mxfmm['b'] - mxfmm['t']) * 100.0
        titletoppercent = 100.0 - titletop / \
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
        # to eliminate unnecessary CPU heating/data transfer
        # so as to make it faster
        # with only invisible detail loss.
        colsregiontomap = mapsizesindots['w'] / regioncols
        rowsregiontomap = mapsizesindots['h'] / regionrows

        newewres = ewres
        newnsres = nsres

        # if colsregiontomap < 1: 
        # CHANGE: also enables raising of resolution to prevent
        # pixelation because of low resolution setting...
        newewres = ewres / colsregiontomap
        # if rowsregiontomap < 1:
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
            dict['at'] = "50," + str(titletoppercent)
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
