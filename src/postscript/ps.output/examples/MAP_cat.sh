#!/bin/bash

r.mask input=urban_mask_neg

ps.output -d out=MAP_cat.ps << EOF
palette
 pure red yellow 7 color
end

paper A4
 left 1cm
 right 1cm
 top 1cm
 landscape n
end

maparea
 top 3cm
 border .8mm
 color black
end

raster landclass96
 grey n
 maskcolor 116:66:20
 maskcell urban_mask_neg lsat.543
 outline
  width 0.5
  color black
 end
 setcolor 1 color0
 setcolor 2 color1
 setcolor 3 color2
 setcolor 4 color3
 setcolor 5 color4
 setcolor 6 color5
end

rlegend
 title Land Class 1996
 name Univers Bold
 size 12
 extend 0.85
 color black
end

raster landclass96
 cols 1 0
 frame
  where 100% 100%
  ref right upper
  offset 0 0
  border 2
  color black
  fcolor white
  margin 8
 end
 font
  name Univers
  size 9
  color black
 end
 width 8mm
end
EOF

r.mask -r input=-

ps2pdf14 MAP_cat.ps MAP_cat.pdf

