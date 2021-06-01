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
    int i, j;
    double d;

    /* PostScript header */
    fprintf(PS.fp, "%%!PS-Adobe-3.0 %s\n", PS.level == 0 ? "EPS 1.2" : "");
    fprintf(PS.fp, "%%%%BoundingBox: 0 0 %d %d\n", (int)(PS.page.width),
	    (int)(PS.page.height));
    fprintf(PS.fp,
	    "%%%%Title: \n" "%%%%Creator: \n" "%%%%CreationDate: %s\n"
	    "%%%%Programming: E. Jorge Tizado, Spain 2009\n"
	    "%%%%EndComments\n\n", G_date());
    /* BEGIN NO EMBEBED EPS file */
    if (PS.level > 0) {
	fprintf(PS.fp, "%%%%BeginProlog\n");
	fprintf(PS.fp, "/D {bind def} bind def\n");
	fprintf(PS.fp, "/XD {exch def} D\n");
	fprintf(PS.fp, "/str 20 string def\n");
	fprintf(PS.fp, "/i2s {str cvs} D\n");
	fprintf(PS.fp,
		"/c2s {/charcode exch def /thechar ( ) dup 0 charcode put def thechar} D\n");
	fprintf(PS.fp,
		"/adds { exch dup length 2 index length add string dup dup 4 2 roll copy length "
		"4 -1 roll putinterval} D\n");
	fprintf(PS.fp,
		"/FN { % (FontName) FN -\n"
		"    dup (-ISOLatin1) adds dup /F0 exch cvn def exch cvn\n"
		"    currentdict F0 known {pop pop}\n"
		"    {findfont dup length dict begin {1 index /FID ne {def} {pop pop} ifelse } forall\n"
		"        /Encoding ISOLatin1Encoding def\n"
		"        /FontName 0 index def\n"
		"        currentdict end definefont pop} ifelse} D\n");
	fprintf(PS.fp,
		"/FS {/FS0 exch def F0 findfont FS0 scalefont setfont} D\n");
	fprintf(PS.fp,
		"/FE {F0 findfont 3 1 roll 1 index dup /FS0 exch def mul 0 0 4 -1 roll 0 0 6 packedarray makefont setfont} D\n");
	fprintf(PS.fp,
		"/FA {currentfont [1 0 0 1.25 0 0] makefont setfont} D\n");
	fprintf(PS.fp,
		"/FR {currentfont [1 0 0 .707 0 %d] makefont setfont} D\n",
		((PS.flag & 2) ? 0 : 2));
	fprintf(PS.fp, "/++ {1 add} D\n");
	fprintf(PS.fp, "/-- {1 sub} D\n");
	fprintf(PS.fp, "/mm {360 mul 127 div} D\n");
	fprintf(PS.fp, "/inch {72 mul} D\n");
	fprintf(PS.fp,
		"/B {4 1 roll 2 copy 5 index 5 index 8 1 roll newpath moveto lineto lineto lineto closepath} D\n");
	fprintf(PS.fp, "/C {setrgbcolor} D\n");
	fprintf(PS.fp, "/cLW {currentlinewidth} D\n");
	fprintf(PS.fp, "/cP {currentpoint} D\n");
	fprintf(PS.fp, "/CP {closepath} D\n");
	fprintf(PS.fp, "/CS {closepath stroke} D\n");
	fprintf(PS.fp, "/F {gsave fill grestore} D\n");
	fprintf(PS.fp, "/G {setgray} D\n");
	fprintf(PS.fp, "/GET {get aload pop} D\n");
	fprintf(PS.fp,
		"/CG {0.11 mul exch 0.59 mul add exch 0.30 mul add setgray} D\n");
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
	fprintf(PS.fp, "/O {%s} D\n",
		((PS.flag & 1) ? ".setopacityalpha" : "pop"));
	fprintf(PS.fp, "/RE {rectstroke} D\n");
	fprintf(PS.fp, "/Re {currentpoint 4 2 roll rectstroke} D\n");
	fprintf(PS.fp,
		"/RES {gsave newpath false charpath flattenpath pathbbox grestore} D\n");
	fprintf(PS.fp, "/RF {rectfill} D\n");
	fprintf(PS.fp, "/Rf {currentpoint 4 2 roll rectfill} D\n");
	fprintf(PS.fp, "/RC {rectclip} D\n");
	fprintf(PS.fp, "/ROT {rotate} D\n");
	fprintf(PS.fp, "/S {stroke} D\n");
	fprintf(PS.fp, "/SC {scale} D\n");
	fprintf(PS.fp, "/SW {stringwidth pop} D\n");
	fprintf(PS.fp,
		"/SWH {gsave newpath 0 0 moveto false charpath flattenpath pathbbox "
		"4 2 roll pop pop grestore} D\n");
	fprintf(PS.fp, "/SHL {show} D\n");
	fprintf(PS.fp, "/SHR {dup SW neg 0 rmoveto show} D\n");
	fprintf(PS.fp, "/SHC {dup SW -2 div 0 rmoveto show} D\n");
	fprintf(PS.fp, "/SHLC {dup SWH -2 div 0 exch rmoveto pop show} D\n");
	fprintf(PS.fp,
		"/SHRC {dup SWH -2 div exch neg exch rmoveto show} D\n");
	fprintf(PS.fp,
		"/SHCC {dup SWH -2 div exch 2 div neg exch rmoveto show} D\n");
	fprintf(PS.fp,
		"/SHS {(:) anchorsearch {pop exch 0 rmoveto SHR} {(.) anchorsearch {pop exch 2 div 0 rmoveto SHC} {exch pop SHL} ifelse} ifelse} D\n");
	fprintf(PS.fp,
		"/COOR {(º) search {GS SHL SHL FR SHL GR} {dup length /n XD {c2s GS n 4 lt n 5 gt or {FR} if show cP GR M n -- /n XD} forall} ifelse} D\n");
	fprintf(PS.fp, "/SVC {{c2s GS SHC GR 0 FS0 neg MR} forall} D\n");
	fprintf(PS.fp,
		"/SWx {0 exch {SW 2 copy lt {exch} if pop} forall} D\n");
	fprintf(PS.fp, "/TR {translate} D\n");
	fprintf(PS.fp,
		"/TSEL {(:) anchorsearch {pop SHR} {(.) anchorsearch {pop SHC} {SHL} ifelse} ifelse} D\n");
	fprintf(PS.fp,
		"/TXT {(|) search {GS TSEL GR pop 0 FS0 -1.2 mul rmoveto TXT} {TSEL} ifelse} D\n");
	fprintf(PS.fp,
		"/TCIR {SWH 2 copy gt {pop} {exch pop} ifelse 2 div 2 add cP 3 -1 roll 0 360 NP arc CP S} D\n");
	fprintf(PS.fp,
		"/RO {GS dup cLW exch 0 lt {neg} if add exch cLW add exch cLW -2 div dup 2 index 0 lt {neg} if TR RE GR} D\n");
	fprintf(PS.fp,
		"/RESET {/x xo mgx add def /y yo mgy sub def /col 0 def /row 0 def} def\n");
	fprintf(PS.fp,
		"/READJUST {SWH mg add dup hg add /hg XD mg add /mgy XD mgx 2 mul add dup wd gt {/wd XD} {pop} ifelse} def\n");
	fprintf(PS.fp,
		"/COL {/col XD xo mgx add 0 1 col -- {ARw exch get dx add add} for /x XD} def\n");
	fprintf(PS.fp,
		"/ROW {/row XD yo mgy sub 0 1 row -- {ARh exch get dy add sub} for /y XD} def\n");
	/* end */
	fprintf(PS.fp, "%%%%EndProlog\n");
	/* Page specifications */
	fprintf(PS.fp, "<< /PageSize [%d %d] >> setpagedevice\n",
		(int)(PS.page.width), (int)(PS.page.height));
    }
    /* END NO EPS file */
    /* Prepare the map */
    start_map();
    if (!PS.page.fcolor.none) {
	set_ps_color(&(PS.page.fcolor));
	fprintf(PS.fp, "0 0 %d %d RF\n", (int)(PS.page.width),
		(int)(PS.page.height));
    }
    if (PS.draft) {		/* print a reticule as watermark on page */
	fprintf(PS.fp,
		"GS .5 LW 0.9 G /Helvetica findfont 7 scalefont setfont\n");
	fprintf(PS.fp,
		"0 0 10 mm %d {0 M GS 0.5 G 1 1 MR dup i2s show ++ GR 0 %d LRS} for pop\n",
		(int)(PS.page.width), (int)(PS.page.height));
	fprintf(PS.fp,
		"0 %d -10 mm 0 {0 exch M GS 0.5 G 1 1 MR dup i2s show ++ GR %d 0 LRS} for pop\n",
		(int)(PS.page.height), (int)(PS.page.width));
	fprintf(PS.fp, "[1 2] 0 LD \n");
	fprintf(PS.fp, "5 mm 10 mm %d {0 M 0 %d LRS} for\n",
		(int)(PS.page.width), (int)(PS.page.height));
	fprintf(PS.fp, "%d 5 mm sub -10 mm 0 {0 exch M %d 0 LRS} for\n",
		(int)(PS.page.height), (int)(PS.page.width));
	fprintf(PS.fp, "GR\n");
    }
    /* PAPER CUSTOM DRAWS */
    if (PS.n_draws > 0) {
	for (i = 0; i < PS.n_draws; i++) {
	    if (PS.draw.flag[i] == 2)
		set_draw(PS.draw.key[i], PS.draw.data[i]);
	}
    }
    /* CLIP to MAP AREA */
    fprintf(PS.fp, "gsave 0 0 0 C ");
    fprintf(PS.fp, "%.4f %.4f %.4f %.4f rectclip\n", PS.map_x, PS.map_y,
	    PS.map_w, PS.map_h);
    if (!PS.fcolor.none) {
	set_ps_color(&(PS.fcolor));
	fprintf(PS.fp, "%.4f %.4f %.4f %.4f RF\n", PS.map_x, PS.map_y,
		PS.map_w, PS.map_h);
    }
    /* needed by uncolored patterns */
    fprintf(PS.fp, "[/Pattern /DeviceRGB] setcolorspace\n");
    /* RASTER */
    if (PS.rst.files != 0) {
	set_raster();
	/* outline, if requested */
	if (PS.rst.outline.width > 0.) {
	    if (!G_raster_map_is_fp(PS.rst.name[0], PS.rst.mapset[0]))
		set_outline();
	    else
		G_warning("Outline is not to float maps!, ignored");
	}
    }
    /* VECTOR (masked) */
    if (PS.vct_files != 0) {
	set_vector(MASKED, AREAS);
	set_vector(MASKED, LINES);
	set_vector(MASKED, POINTS);
	set_vector(MASKED, LABELS);
    }
    /* RASTER MASK */
    if (PS.need_mask && PS.rst.do_mask) {
	set_mask();
    }
    /* VECTOR-LINES/AREAS under grids (unmasked) */
    if (PS.vct_files != 0) {
	set_vector(UNMASKED, AREAS);
	set_vector(UNMASKED, LINES);
    }
    /* CLIPED CUSTOM DRAWS */
    if (PS.n_draws > 0) {
	/* fprintf(PS.fp, "0 0 0 C "); // default color */
	for (i = 0; i < PS.n_draws; i++) {
	    if (PS.draw.flag[i] == 0)
		set_draw(PS.draw.key[i], PS.draw.data[i]);
	}
    }
    /* GRIDS LINES INSIDE OF BORDER  */
    if (PS.grid.sep > 0) {
	set_lines_grid();
    }
    if (PS.geogrid.sep > 0) {
	set_lines_geogrid();
    }
    /* VECTOR-POINTS/LABELS on grids (unmasked) */
    if (PS.vct_files != 0) {
	set_vector(UNMASKED, POINTS);
	set_vector(UNMASKED, LABELS);
    }
    /* CLIPED CUSTOM DRAWS ONTO ALL MAP ITEMS */
    if (PS.n_draws > 0) {
	/* fprintf(PS.fp, "0 0 0 C "); // default color */
	for (i = 0; i < PS.n_draws; i++) {
	    if (PS.draw.flag[i] == 3)
		set_draw(PS.draw.key[i], PS.draw.data[i]);
	}
    }
    /* no more work in the map area */

    /********************************/
    fprintf(PS.fp, "grestore\n");
    /* BORDER */
    if (PS.do_border && PS.brd.width > 0 && !PS.brd.color.none) {
	set_ps_line(&(PS.brd));
	set_ps_rect(PS.map_x, PS.map_y, PS.map_w, PS.map_h);
    }
    /* GRID NUMBER, OUTSIDE OF BORDER */
    if (PS.geogrid.sep > 0) {
	set_numbers_geogrid();
    }
    if (PS.grid.sep > 0) {
	set_numbers_grid();
    }
    /* LEGENDS */
    if (PS.do_rlegend) {
	if (G_raster_map_is_fp(PS.rl.name, PS.rl.mapset) || PS.rl.do_gradient) {
	    set_rlegend_gradient();
	}
	else {
	    set_rlegend_cats();
	}
    }
    if (PS.do_vlegend) {
	set_vlegend();
    }
    /* NOTES */
    for (i = 0; i < PS.n_notes; i++) {
	set_note(i);
    }
    /* SCALEBAR */
    if (PS.sbar.segments > 0 && PS.sbar.length > 0) {
	set_scalebar();
    }
    /* FREE CUSTOM DRAWS */
    if (PS.n_draws > 0) {
	for (i = 0; i < PS.n_draws; i++) {
	    if (PS.draw.flag[i] == 1)
		set_draw(PS.draw.key[i], PS.draw.data[i]);
	}
    }
    /* END */

    /* BEGIN NO EPS file */
    if (PS.level > 0) {
	fprintf(PS.fp, "showpage\n");
	fprintf(PS.fp, "%%%%Trailer\n");
	fprintf(PS.fp, "%%%%EOF\n");
	fclose(PS.fp);
    }
    /* FREE ALLOCATED POINTERS */
    for (i = 0; i < PS.vct_files; i++) {
	G_free(PS.vct[i].data);
	G_free(PS.vct[i].item);
	/*
	   for (j=0; j < PS.vct[i].n_rule; j++)
	   G_free(PS.vct[i].rule->val_list);
	 */
	G_free(PS.vct[i].rule);
    }
    G_free(PS.vct);
    G_free(Palette);
    /*
       if (Palette != NULL) {
       G_free(Palette);
       }
     */

    return 0;
}
