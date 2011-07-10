This is a GSOC Project to add WMS GetCapabilites functionality support for Grass.

Aim of the project-

This project aims to introduce several features that make WXGUI more user-friendly. These include adding WMS layer support for WXGUI. The selection features will be displayed as per the based on service GetCapabilities response. The parameters and the layers are to be displayed are extracted out of the xml response.

State of the art-

The project uses WMS service to fetch images of the maps. The Get Feature service of WMS services provides a GML based interface to access the information about various layers available. The WMS layer knowledge is used to update the GUI of the GRASS according to the available features for a particular layer. Thw WX-GUI is to be modified and to be integrated with the WMS services. 

Libraries to be installed

1.  BeautifulSoup 3.2 , an XML, HTML Parser ( http://www.crummy.com/software/BeautifulSoup/ )


How to run the add-on
1) Copy files wmsmenu.py , parse.py to gui/wxpython/gui_modules/
2) Patch wxgui.py and toolbars.py with command "cd path/to/sourceroot && cat core.diff | patch -p0"
3) make the source code
3) Now run it , when launched , a new button shall appear in Main GUI window beside 'New Display button'
4) Click on it, and a new wms window shall be launched. 
5) Enter url of WMS 
6) Click on Get Capabilites. 



Author - 
Sudeep Singh Walia
