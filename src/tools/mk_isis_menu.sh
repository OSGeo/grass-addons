#!/bin/bash

############################################################################
#
# MODULE:       mk_isis_menu.sh
# AUTHOR(S):    Yann Chemin
# PURPOSE:      Run through $ISISROOT/Isis/bin/* and 
#               build a wxpython menu toolbox
# COPYRIGHT:    (C) 2014 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#In $GRASS_HOME/gui/wxpython/gis_set.py it will not be appropriate
#if os.getenv('ISISROOT'):
#    os.popen("bash "+os.path.join(globalvar.GUIDIR, "utils", "mk_isis_menu.sh")

#Toolbox
tbfile="$HOME/.grass8/toolboxes/toolboxes.xml"
#Main menu
mmfile="$HOME/.grass8/toolboxes/main_menu.xml"
#Menu tree 
mtfile="$HOME/.grass8/toolboxes/module_tree.xml"
#For building
#tbfile="$ISISROOT/../toolboxes.xml"
#echo $ISISROOT
shopt -s extglob
cd $ISISROOT/bin/
#echo $(ls !(xml)) > isis_bin.txt

#Start building
echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" > $tbfile
echo "<toolboxes>" >> $tbfile
echo "  <toolbox name=\"Isis\">" >> $tbfile
echo "      <label>I&amp;sis</label>" >> $tbfile
echo "      <items>" >> $tbfile
echo "        <menu>" >> $tbfile
#Import Modules
echo "          <label>Import (*2isis)</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep 2isis)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>Converts $(echo $i | sed 's/2isis//') raster maps to Isis .cub</help>" >> $tbfile
	echo "              <keywords>planetary,raster,conversion,Isis,import,$(echo $i | sed 's/2isis//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Export Modules
echo "        <menu>" >> $tbfile
echo "          <label>Export (isis2*)</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep isis2)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>Converts Isis .cub to $(echo $i | sed 's/isis2//') raster maps</help>" >> $tbfile
	echo "              <keywords>planetary,raster,conversion,Isis,export,$(echo $i | sed 's/2isis//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Remaining Converters (*2*)
echo "        <menu>" >> $tbfile
echo "          <label>Other converters (*2*)</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep -v 2isis | grep -v isis2 | grep 2)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>Converts $(echo $i | sed 's/\(.*\)2\(.*\)/\1/') to $(echo $i | sed 's/\(.*\)2\(.*\)/\2/')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,conversion,Isis,$(echo $i | sed 's/\(.*\)2\(.*\)/\1/'),$(echo $i | sed 's/\(.*\)2\(.*\)/\2/')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
echo "      <separator />" >> $tbfile
#Camera
echo "        <menu>" >> $tbfile
echo "          <label>Camera</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep cam)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>Camera $(echo $i | sed 's/cam//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,camera,Isis,$(echo $i | sed 's/cam//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Control network
echo "        <menu>" >> $tbfile
echo "          <label>Control Network</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep -v 2 | grep cnet)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>CNET $(echo $i | sed 's/cnet//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,control network,Isis,$(echo $i | sed 's/cnet//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Image Calibration
echo "        <menu>" >> $tbfile
echo "          <label>Image Calibration</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep -v 2 | grep -v cnet | grep cal)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>CNET $(echo $i | sed 's/cal//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,calibration,Isis,$(echo $i | sed 's/cal//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Image Photometry
echo "        <menu>" >> $tbfile
echo "          <label>Image Photometry</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep pho)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>Photometry $(echo $i | sed 's/pho//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,photometry,Isis,$(echo $i | sed 's/pho//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile

echo "      <separator />" >> $tbfile
#Develop Maps GUIs
echo "        <menu>" >> $tbfile
echo "          <label>Develop Maps GUIs</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep q[vmnt])
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>GUI function for $(echo $i | sed 's/q//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,Voyager,$(echo $i | sed 's/q//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Develop Maps functions
echo "        <menu>" >> $tbfile
echo "          <label>Develop Maps</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep crop)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>crop function for $(echo $i | sed 's/crop//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,crop,$(echo $i | sed 's/crop//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "                <separator />" >> $tbfile
for i in $(ls !(xml) | grep footprint)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>footprint function for $(echo $i | sed 's/footprint//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,footprint,$(echo $i | sed 's/footprint//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "                <separator />" >> $tbfile
for i in $(ls !(xml) | grep gap)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>gap function for $(echo $i | sed 's/gap//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,gap,$(echo $i | sed 's/gap//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "                <separator />" >> $tbfile
for i in $(ls !(xml) | grep gauss)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>gauss function for $(echo $i | sed 's/gauss//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,gauss,$(echo $i | sed 's/gauss//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "                <separator />" >> $tbfile
for i in $(ls !(xml) | grep hist)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>histogram function for $(echo $i | sed 's/hist//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,histogram,$(echo $i | sed 's/hist//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "                <separator />" >> $tbfile
for i in $(ls !(xml) | grep jigsaw)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>jigsaw function for correcting images (needs a spiceinit first)</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,jigsaw</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "                <separator />" >> $tbfile
for i in $(ls !(xml) | grep kernf)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>kernel function for $(echo $i | sed 's/kern//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,kernel,$(echo $i | sed 's/kern//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "                <separator />" >> $tbfile
for i in $(ls !(xml) | grep shadow)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>shadow function for $(echo $i | sed 's/shadow//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,shadow,$(echo $i | sed 's/shadow//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "                <separator />" >> $tbfile
for i in $(ls !(xml) | grep trim)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>trim function for $(echo $i | sed 's/trim//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,trim,$(echo $i | sed 's/trim//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Develop Mosaics
echo "        <menu>" >> $tbfile
echo "          <label>Develop Mosaics</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep mos)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>Mosaic function for $(echo $i | sed 's/mos//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,Mosaic,$(echo $i | sed 's/mos//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
echo "      <separator />" >> $tbfile
#Sensors Apollo
echo "        <menu>" >> $tbfile
echo "          <label>Apollo</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep apollo)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>Apollo $(echo $i | sed 's/apollo//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,$(echo $i | sed 's/apollo//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Sensors Clementine
echo "        <menu>" >> $tbfile
echo "          <label>Clementine</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep clem)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>Clementine $(echo $i | sed 's/clem//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,$(echo $i | sed 's/clem//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Sensors Dawn
echo "        <menu>" >> $tbfile
echo "          <label>Dawn</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep dawn)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>Dawn $(echo $i | sed 's/dawn//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,$(echo $i | sed 's/dawn//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Sensors HiRiSe
echo "        <menu>" >> $tbfile
echo "          <label>hiRiSe</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep -v hist | grep -v clem | grep -v pho | grep -v spec | grep hi)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>hiRiSe $(echo $i | sed 's/hi//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,$(echo $i | sed 's/hi//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Sensors Kaguya
echo "        <menu>" >> $tbfile
echo "          <label>Kaguya</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep kaguya)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>Kaguya $(echo $i | sed 's/kaguya//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,$(echo $i | sed 's/kaguya//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Sensors LRO
echo "        <menu>" >> $tbfile
echo "          <label>LRO</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep lro)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>LRO $(echo $i | sed 's/lro//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,$(echo $i | sed 's/lro//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Sensors Mariner 10
echo "        <menu>" >> $tbfile
echo "          <label>Mariner 10</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep mar10)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>Mariner 10 $(echo $i | sed 's/mar10//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,$(echo $i | sed 's/mar10//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Sensors Messenger
echo "        <menu>" >> $tbfile
echo "          <label>Messenger</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep mdis)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>Messenger $(echo $i | sed 's/mdis//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,Messenger,$(echo $i | sed 's/mdis//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
for i in $(ls !(xml) | grep mess)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>Messenger $(echo $i | sed 's/mess//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,Messenger,$(echo $i | sed 's/mess//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Sensors MOC on MGS
echo "        <menu>" >> $tbfile
echo "          <label>MOC camera (MGS)</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep moc)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>MGS MOC camera $(echo $i | sed 's/moc//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,MGS,$(echo $i | sed 's/moc//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Sensors Themis on Mars Odyssey
echo "        <menu>" >> $tbfile
echo "          <label>Themis (Mars Odyssey)</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep thm)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>MO Themis $(echo $i | sed 's/thm//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,Mars,Odyssey,$(echo $i | sed 's/thm//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Sensors Viking
echo "        <menu>" >> $tbfile
echo "          <label>Viking</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep vik)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>Viking $(echo $i | sed 's/vik//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,Viking,$(echo $i | sed 's/vik//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Sensors VIMS on Cassini
echo "        <menu>" >> $tbfile
echo "          <label>VIMS (Cassini)</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep vims)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>Cassini VIMS $(echo $i | sed 's/vims//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,Cassini,$(echo $i | sed 's/vims//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Sensors Voyager
echo "        <menu>" >> $tbfile
echo "          <label>Voyager</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep moc)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>Voyager $(echo $i | sed 's/voy//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,Voyager,$(echo $i | sed 's/voy//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
#Next set
echo "      <separator />" >> $tbfile
#Report Labels and History 
echo "        <menu>" >> $tbfile
echo "          <label>Report Label and History</label>" >> $tbfile
echo "          <items>" >> $tbfile
for i in $(ls !(xml) | grep cat)
do
	echo "            <menuitem>" >> $tbfile
	echo "              <label>$i</label>" >> $tbfile
	echo "              <command>$i</command>" >> $tbfile
	echo "              <help>function for $(echo $i | sed 's/cat//')</help>" >> $tbfile
	echo "              <keywords>planetary,raster,sensor,Isis,catalog,$(echo $i | sed 's/cat//')</keywords>" >> $tbfile
	echo "              <handler>RunMenuCmd</handler>" >> $tbfile
	echo "            </menuitem>" >> $tbfile
done
echo "          </items>" >> $tbfile
echo "        </menu>" >> $tbfile
echo "      </items>" >> $tbfile
echo "  </toolbox>" >> $tbfile
echo "</toolboxes>" >> $tbfile

#For testing
#cp -f $tbfile ~/.grass8/toolboxes/

#Missing
#ctx
#cube
#dem
#sky
#ring (Cassini images of Saturn rings)
#socet
#spec
#spice (+spk)

#Once the whole menu is made
#Attach it to GRASS main menu
echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" > $mmfile
echo "<!DOCTYPE toolbox SYSTEM \"main_menu.dtd\">" >> $mmfile
echo "<toolbox name=\"DefaultMainMenu\">" >> $mmfile
echo "  <label>GRASS GIS main menu bar with Isis3</label>" >> $mmfile
echo "  <items>" >> $mmfile
echo "    <subtoolbox name=\"File\"/>" >> $mmfile
echo "    <subtoolbox name=\"Settings\"/>" >> $mmfile
echo "    <subtoolbox name=\"Raster\"/>" >> $mmfile
echo "    <subtoolbox name=\"Vector\"/>" >> $mmfile
echo "    <subtoolbox name=\"Imagery\"/>" >> $mmfile
echo "    <subtoolbox name=\"Isis\"/>" >> $mmfile
echo "    <subtoolbox name=\"Volumes\"/>" >> $mmfile
echo "    <subtoolbox name=\"Database\"/>" >> $mmfile
echo "    <subtoolbox name=\"Temporal\"/>" >> $mmfile
echo "    <subtoolbox name=\"Help\"/>" >> $mmfile
echo "  </items>" >> $mmfile
echo "</toolbox>" >> $mmfile

#And...
#Attach it to GRASS menu tree
echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" > $mtfile
echo "<!DOCTYPE toolbox SYSTEM \"main_menu.dtd\">" >> $mtfile
echo "<toolbox name=\"DefaultModuleTree\">" >> $mtfile
echo "  <label>GRASS GIS module tree with Isis</label>" >> $mtfile
echo "  <items>" >> $mtfile
echo "    <subtoolbox name=\"ImportExportLink\"/>" >> $mtfile
echo "    <subtoolbox name=\"ManageMaps\"/>" >> $mtfile
echo "    <subtoolbox name=\"Raster\"/>" >> $mtfile
echo "    <subtoolbox name=\"Vector\"/>" >> $mtfile
echo "    <subtoolbox name=\"Imagery\"/>" >> $mtfile
echo "    <subtoolbox name=\"Isis\"/>" >> $mtfile
echo "    <subtoolbox name=\"Volumes\"/>" >> $mtfile
echo "    <subtoolbox name=\"Database\"/>" >> $mtfile
echo "    <subtoolbox name=\"Temporal\"/>" >> $mtfile
echo "    <subtoolbox name=\"GuiTools\"/>" >> $mtfile
echo "    <user-toolboxes-list/>" >> $mtfile
echo "    <addons/>" >> $mtfile
echo "  </items>" >> $mtfile
echo "</toolbox>" >> $mtfile


