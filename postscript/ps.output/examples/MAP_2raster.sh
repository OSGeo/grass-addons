#!/bin/bash

g.region rast=elevation -a

ps.output out=MAP_2raster.ps << EOF
paper A4
 landscape y
end

maparea
 height 12cm
 border .8mm
 color yellow
end

grid
 major 20000
  width .2mm
  color blue
 end
 minor 5000
  width .2mm
  color blue
  style 1
 end
 font
  name Univers
  size 6
  extend 1.2
  color black
 end
 fcolor black
 format +out
 trim 3
end

raster elevation.3d
 maskcolor red
 maskcell urban_mask elevation.3d
end

rlegend
 raster elevation
 cols 5 0
 swidth 8mm
 frame
  where 100% 0%
  ref right upper
  offset 0 -10
  margin 8
  border 1
  fcolor 220:220:220
  color black
 end
 font
  name Univers
  size 8
  color black
 end
end

note :file ps_output_2raster
 font
  name Courier
  size 6
 end
 frame
  where 110% 110%
  ref left upper
 end
end
EOF

ps2pdf14 MAP_2raster.ps MAP_2raster.pdf

