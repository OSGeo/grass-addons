#!/bin/bash

RASTER=zipcodes_wake

g.region rast=$RASTER res=60 -a

g.region n=n+1000 s=s-1000 w=w-1000 e=e+1000

ps.output out=MAP_raster.ps << EOF
paper A4
 landscape n
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
  format out
  trim 3
end

raster $RASTER
 gray n
 maskcolor brown
 maskcell $RASTER elev_state_500m
 outline
  width .2
  color black
 end
 setcolor 25 black
end

rlegend
 title .Zip Codes (wake)
  name Univers-Bold
  size 10
  extend 1.5
  color black
 end
 raster $RASTER
 cols 5 0
 swidth 8mm
 order 20,10,30,22,34
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

note :file ps_output_raster
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

ps2pdf14 MAP_raster.ps MAP_raster.pdf

