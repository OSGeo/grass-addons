/* File: ps_map3.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <stdio.h>
#include <unistd.h>
#include "palettes.h"
#include "ps_info.h"
#include "local_proto.h"

#define UNMASKED    0
#define MASKED      1

#define INSIDE      0
#define OUTSIDE     1

int PS3_map(void)
{
    int i;
    double d;

    /* PostScript header */
    fprintf(PS.fp, "%%!PS-Adobe-3.0\n");
    fprintf(PS.fp, "%%%%BoundingBox: 0 0 %d %d\n",
            (int)(PS.page.width),
            (int)(PS.page.height));
    fprintf(PS.fp, "%%%%Title: \n");
    fprintf(PS.fp, "%%%%Creator: \n");
    fprintf(PS.fp, "%%%%CreationDate: %s\n", G_date());
    fprintf(PS.fp, "%%%%Programming: E. Jorge Tizado, Spain 2009\n");
    fprintf(PS.fp, "%%%%EndComments\n\n");
    fprintf(PS.fp, "%%%%BeginProlog\n");
    fprintf(PS.fp, "/D {bind def} bind def\n");
    fprintf(PS.fp, "/XD {exch def} D\n");

    /* STRING MANIPULATION */
    fprintf(PS.fp, "/str 20 string def\n");
    fprintf(PS.fp, "/to_s {str cvs} D\n");
    /* (a) (b) -> (ab) */
    fprintf(PS.fp, "/adds { "
            "exch dup length "
            "2 index length add string dup dup 4 2 roll copy length "
            "4 -1 roll putinterval} D\n");

    /* Orden alfabetico */
    fprintf(PS.fp, "/++ {1 add} D\n");
    fprintf(PS.fp, "/-- {1 sub} D\n");
    fprintf(PS.fp, "/mm {360 mul 127 div} D\n");
    fprintf(PS.fp, "/inch {72 mul} D\n");

    fprintf(PS.fp, "/B {4 1 roll 2 copy 5 index 5 index 8 1 roll newpath moveto lineto lineto lineto closepath} D\n");
    fprintf(PS.fp, "/C {setrgbcolor} D\n");
    fprintf(PS.fp, "/cLW {currentlinewidth} D\n");
    fprintf(PS.fp, "/cP {currentpoint} D\n");
    fprintf(PS.fp, "/CP {closepath} D\n");
    fprintf(PS.fp, "/CS {closepath stroke} D\n");
    fprintf(PS.fp, "/F {gsave fill grestore} D\n");
    fprintf(PS.fp, "/G {setgray} D\n");
    fprintf(PS.fp, "/GET {get aload pop} D\n");
    fprintf(PS.fp, "/CG {0.11 mul exch 0.59 mul add exch 0.30 mul add setgray} D\n");
    fprintf(PS.fp, "/GS {gsave} D\n");
    fprintf(PS.fp, "/GR {grestore} D\n");
    fprintf(PS.fp, "/LC {setlinecap} D\n");
    fprintf(PS.fp, "/LD {setdash} D\n");
    fprintf(PS.fp, "/LJ {setlinejoin} D\n");
    fprintf(PS.fp, "/L {lineto} D\n");
    fprintf(PS.fp, "/LS {lineto stroke} D\n");
    fprintf(PS.fp, "/LR {rlineto} D\n");
    fprintf(PS.fp, "/LRS {rlineto stroke} D\n");
    fprintf(PS.fp, "/LW {setlinewidth} D\n");
    fprintf(PS.fp, "/M {moveto} D\n");
    fprintf(PS.fp, "/ML {moveto lineto stroke} D\n");
    fprintf(PS.fp, "/MR {rmoveto} D\n");
    fprintf(PS.fp, "/MS {moveto show} D\n");
    fprintf(PS.fp, "/NM {newpath moveto} D\n");
    fprintf(PS.fp, "/NP {newpath} D\n");
    fprintf(PS.fp, "/RE {rectstroke} D\n");
    fprintf(PS.fp, "/Re {currentpoint 4 2 roll rectstroke} D\n");   /* stack: w h */
    fprintf(PS.fp, "/RES {gsave newpath false charpath flattenpath pathbbox grestore} D\n"); /* llx lly urx ury of a string: stack string */
    fprintf(PS.fp, "/RF {rectfill} D\n");
    fprintf(PS.fp, "/Rf {currentpoint 4 2 roll rectfill} D\n");   /* stack: w h */
    fprintf(PS.fp, "/RC {rectclip} D\n");
    fprintf(PS.fp, "/ROT {rotate} D\n");
    fprintf(PS.fp, "/S {stroke} D\n");
    fprintf(PS.fp, "/SC {scale} D\n");
    fprintf(PS.fp, "/SHL {show} D\n");
    fprintf(PS.fp, "/SHR {dup stringwidth pop neg 0 rmoveto show} D\n");
    fprintf(PS.fp, "/SHC {dup stringwidth pop 2 div neg 0 rmoveto show} D\n");
    fprintf(PS.fp, "/SHCC {dup SWH 2 div neg exch 2 div neg exch rmoveto show} D\n");
    fprintf(PS.fp, "/SW {stringwidth pop} D\n");
    /* w h of a string: stack string */
    fprintf(PS.fp, "/SWH {gsave newpath 0 0 moveto false charpath flattenpath pathbbox "
                   "4 2 roll pop pop grestore} D\n");
    /* max string width of an array of string: stack array */
    fprintf(PS.fp, "/SWx {0 exch {stringwidth pop dup 2 index gt {exch} if pop} forall} def\n");
    fprintf(PS.fp, "/TR {translate} D\n");
    fprintf(PS.fp, /* borde exterior del rectangulo: x y w h RO */
            "/RO {gsave dup cLW exch 0 lt {neg} if add exch cLW add exch "
            "cLW -2 div dup 2 index 0 lt {neg} if TR RE grestore} D\n");
    /* stack none */
    fprintf(PS.fp, "/RESET {/x xo mgx add def /y yo mgy sub def /col 0 def /row 0 def} def\n");
    /* stack number of col/row 0...n-1 */
    fprintf(PS.fp, "/COL {/col XD xo mgx add 0 1 col -- {ARw exch get dx add add} for /x XD} def\n");
    fprintf(PS.fp, "/ROW {/row XD yo mgy sub 0 1 row -- {ARh exch get dy add sub} for /y XD} def\n");
    /* set fontname with re-encoding */
    fprintf(PS.fp,
            "/FN { % (FontName) FN -\n"
            "    dup (-ISOLatin1) adds dup /F0 exch cvn def exch cvn\n"
            "    currentdict F0 known {pop pop}\n"
            "    {findfont dup length dict begin {1 index /FID ne {def} {pop pop} ifelse } forall\n"
            "        /Encoding ISOLatin1Encoding def\n"
            "        /FontName 0 index def\n"
            "        currentdict end definefont pop} ifelse} D\n");
    /* set fontsize */
    fprintf(PS.fp, "/FS {/F0S exch def F0 findfont F0S scalefont setfont} D\n");
    /* set fontsize */
    fprintf(PS.fp, "/FE {F0 findfont 3 1 roll 1 index mul 0 0 4 -1 roll 0 0 6 packedarray makefont setfont} D\n");
    /* trying transparency compatibility */
    /* fprintf(PS.fp, "/pdfmark where {pop} {userdict /pdfmark /cleartomark load put} ifelse\n"); */
    /* end */
    fprintf(PS.fp, "%%%%EndProlog\n");

    /* Page specifications */
    fprintf(PS.fp, "<< /PageSize [%d %d] >> setpagedevice\n",
            (int)(PS.page.width), (int)(PS.page.height));

    /* Prepare the map */
    start_map();
    if (PS.draft) /* print a reticule as watermark of page */
    {
        fprintf(PS.fp, ".5 LW 0.9 G\n");
        fprintf(PS.fp, "0 28.35 %d {0 M 0 %d LR S} for\n",
                (int)(PS.page.width), (int)(PS.page.height));
        fprintf(PS.fp, "%d -28.35 0 {0 exch M %d 0 LR S} for\n",
                (int)(PS.page.height), (int)(PS.page.width));
    }
    /* CLIP the MAP AREA */
    fprintf(PS.fp, "gsave ");
    fprintf(PS.fp, "%.4f %.4f %.4f %.4f rectclip\n",
            PS.map_x, PS.map_y, PS.map_w, PS.map_h);
    if (!PS.fcolor.none)
    {
        set_ps_color(&(PS.fcolor));
        fprintf(PS.fp, "%.4f %.4f %.4f %.4f RF\n",
            PS.map_x, PS.map_y, PS.map_w, PS.map_h);
    }
    /* needed by uncolored patterns */
    fprintf(PS.fp, "[/Pattern /DeviceRGB] setcolorspace NP\n");

    /* RASTER */
    if (PS.rst.files != 0)
    {
        set_raster();
        /* outline, if requested */
        if (PS.rst.outline.width > 0.)
        {
            if (!G_raster_map_is_fp(PS.rst.name[0], PS.rst.mapset[0]))
                set_outline();
            else
                G_warning("Outline is not to float maps!, ignored");
        }
    }
    /* VECTOR (masked) */
    if (PS.vct_files != 0)
    {
        set_vector(MASKED, AREAS);
        set_vector(MASKED, LINES);
        set_vector(MASKED, POINTS);
    }
    /* LABELS (masked) */
//     set_labels(MASKED);
    /* RASTER MASK */
    if (PS.need_mask && PS.rst.do_mask)
    {
    	set_mask();
    }
    /* VECTOR-LINES/AREAS under grids (unmasked) */
    if (PS.vct_files != 0)
    {
        set_vector(UNMASKED, AREAS);
        set_vector(UNMASKED, LINES);
    }
    /* CLIPED CUSTOM DRAWS */
    if (PS.n_draws > 0)
    {
        fprintf(PS.fp, "0 0 0 C "); /* default color */
        for (i = 0; i < PS.n_draws; i++)
            set_draw(PS.draw.key[i], PS.draw.data[i]);
    }
    /* GRIDS LINES INSIDE OF BORDER  */
    if (PS.grid.sep > 0)
    {
        set_lines_grid();
    }
    if (PS.geogrid.sep > 0)
    {
        set_lines_geogrid();
    }
    /* VECTOR-POINTS on grids (unmasked) */
    if (PS.vct_files != 0)
    {
        set_vector(UNMASKED, POINTS);
    }
    /* no more work in the map area */
    fprintf(PS.fp, "grestore\n");
    /* BORDER */
    if (PS.do_border && PS.brd.width > 0 && !PS.brd.color.none)
    {
        set_ps_line(&(PS.brd));
        set_ps_rect(PS.map_x, PS.map_y, PS.map_w, PS.map_h);
    }
    /* GRID NUMBER, OUTSIDE OF BORDER */
    if (PS.geogrid.sep > 0)
    {
        set_numbers_geogrid();
    }
    if (PS.grid.sep > 0)
    {
        set_numbers_grid();
    }
    /* LEGENDS */
    if (PS.do_rlegend)
    {
        if (G_raster_map_is_fp(PS.rl.name, PS.rl.mapset) ||
            PS.rl.do_gradient)
        {
            set_rlegend_gradient();
        }
        else
        {
            set_rlegend_cats();
        }
    }
    if (PS.do_vlegend)
    {
        set_vlegend();
    }
    /* NOTES */
    for (i = 0; i < PS.n_notes; i++)
    {
        set_note(i);
    }
    /* SCALEBAR */
    if (PS.sbar.segments > 0 && PS.sbar.length > 0) {
        set_scalebar();
    }

    /* END */
    fprintf(PS.fp, "showpage\n");
    fprintf(PS.fp, "%%%%Trailer\n");
    fprintf(PS.fp, "%%%%EOF\n");
    fclose(PS.fp);

    /* FREE ALLOCATED POINTERS */
    for (i = 0; i < PS.vct_files; i++)
    {
        G_free(PS.vct[i].data);
    }
    G_free(PS.vct);
    if (Palette != NULL)
        G_free(Palette);

    return 0;
}
