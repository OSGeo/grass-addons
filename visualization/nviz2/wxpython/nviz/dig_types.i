/* extracted from include/vect/dig_defines.h */

#define GV_POINT      0x01
#define GV_LINE       0x02
#define GV_BOUNDARY   0x04
#define GV_CENTROID   0x08
#define GV_FACE       0x10
#define GV_KERNEL     0x20
#define GV_AREA       0x40
#define GV_VOLUME     0x80

#define GV_POINTS (GV_POINT | GV_CENTROID )
#define GV_LINES (GV_LINE | GV_BOUNDARY )

#define PORT_DOUBLE_MAX 1.7976931348623157e+308

/* extracted from gui/wxpython/nviz/nviz.h */

#define VIEW_DEFAULT_POS_X 0.85
#define VIEW_DEFAULT_POS_Y 0.85
#define VIEW_DEFAULT_PERSP 40.0
#define VIEW_DEFAULT_TWIST 0.0
#define VIEW_DEFAULT_ZEXAG 1.0
