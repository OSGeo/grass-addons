Start GRASS using North Carolina location [nc_spm_08] and landsat mapset (because wx.class is under development)

download wx.class.py
cd path/to/download/dir
python wx.class.py

A mapdisplay window appears with landsat map (lsat7_2002_10).It draws histogram of six satellite images 
lsat7_2002_10, lsat7_2002_20, lsat7_2002_30, lsat7_2002_40, lsat7_2002_50, lsat7_2002_60

Double click left mouse button to select first point and do the same to select next point this will draw a red line using the first and second points
repeat for selecting next points
Double click right mouse button to close the region and draw the histogram on the left  of mapdisplay.

If any error message(maybe ZeroDivisionError: float division) is displayed on GRASS terminal redraw the region as explained above.
