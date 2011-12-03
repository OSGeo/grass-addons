
#include <string.h>
#include <math.h>
#include "ps_info.h"
#include "scalebar.h"
#include "local_proto.h"
#include "conversion.h"

char *strnumber(double num);


int set_scalebar(void)
{
    int i, j;
    double width, segment;

    if (PS.sbar.length <= 0 || PS.sbar.segments <= 0)
	return 1;

    fprintf(PS.fp, "GS [] 0 LD\n");

    /* width of scalebar in points */
    width = PS.sbar.length;
    switch (PS.sbar.ucode) {
    case SB_UNITS_KM:
	width *= KILOMETERS_TO_METERS;
	break;
    case SB_UNITS_FEET:
	width *= FEET_TO_METERS;
	break;
    case SB_UNITS_MILES:
	width *= MILES_TO_METERS;
	break;
    case SB_UNITS_NMILES:
	width *= NAUT_MILES_TO_METERS;
	break;
    default:
	width *= G_database_units_to_meters_factor();
	break;
    }
    width *= (1000. * MM_TO_POINT / (double)PS.scale);

    if (PS.sbar.subsegs > 0 && PS.sbar.type != 'I') {
	segment = width / (double)PS.sbar.segments;
	width += segment;
    }

    /* adjust to min size */
    set_ps_font(&(PS.sbar.font));

    set_box_orig(&(PS.sbar.box));
    set_box_size(&(PS.sbar.box), width + 2. * PS.sbar.box.margin,	/* cwd real width */
		 PS.sbar.height + 2. * PS.sbar.box.margin);

    /* labels of the scalebar */
    fprintf(PS.fp, "/AR0 [");
    segment = (PS.sbar.length / PS.sbar.segments);
    for (i = 0; i <= PS.sbar.segments; i += PS.sbar.labels) {
	fprintf(PS.fp, "(%s)", strnumber(i * segment));
    }
    fprintf(PS.fp, "] def\n");
    /* sublabels of the scalebar */
    if (PS.sbar.type != 'I') {
	fprintf(PS.fp, "/AR1 [(0)");
	segment = (PS.sbar.length / PS.sbar.segments) / PS.sbar.subsegs;
	for (i = PS.sbar.sublabs; i <= PS.sbar.subsegs; i += PS.sbar.sublabs) {
	    fprintf(PS.fp, "(%s)", strnumber(i * segment));
	}
	fprintf(PS.fp, "] def\n");
    }

    /* The text in PS.sbar.units used to calculate size of text */
    if (PS.sbar.type == 'I') {
	fprintf(PS.fp,
		"/mgy mg def (%s) SWH 2 add /chg XD "
		"chg mg 2 mul add /hg XD 2 add wd add /wd XD\n",
		PS.sbar.units);
    }
    else if (PS.sbar.type == 's' || PS.sbar.type == 'S') {
	fprintf(PS.fp,
		"AR0 dup length -- get SWH "
		"mg add /mgy XD 2 div dup mg add /mgr XD wd add (%s) SW 2 add add /wd XD "
		"/hg mgy 2 add mg add chg add def\n", PS.sbar.units);
    }
    else {
	fprintf(PS.fp,
		"AR0 dup length -- get SWH "
		"mg add /mgy XD 2 div dup mg add /mgr XD wd add /wd XD "
		"/hg mgy 2 mul ++ chg add def\n");
    }
    /* prepare the scalebar */
    if (PS.sbar.subsegs == 0 || PS.sbar.type == 'I') {
	fprintf(PS.fp, "/dx cwd %d div def " "/mgx mg def\n",
		PS.sbar.segments);
    }
    else {
	fprintf(PS.fp,
		"/dx cwd %d div def\n"
		"AR1 dup length -- get SW 2 div dup "
		"mg add dx add /mgx XD wd add /wd XD\n",
		PS.sbar.segments + 1);
    }

    /* do the scalebar */
    set_box_draw(&(PS.sbar.box));
    switch (PS.sbar.type) {
    case 'I':
	fprintf(PS.fp, "/RBAR {{x exch dx mul add y dx dy RF} for} D\n");
	fprintf(PS.fp,
		"/RTXT {{dup x exch dx mul add -- y M AR0 exch get SHR} for} D\n");
	fprintf(PS.fp, "/mgy mg def RESET /dy chg neg def\n");
	set_ps_color(&(PS.sbar.font.color));
	fprintf(PS.fp, "1 LW x y cwd dy RE\n");
	fprintf(PS.fp, "1 2 %d RBAR\n", PS.sbar.segments - 1);
	set_ps_color(&(PS.sbar.fcolor));
	fprintf(PS.fp, "0 2 %d RBAR\n", PS.sbar.segments - 1);
	fprintf(PS.fp, "/y y dy 1 add add def ");
	fprintf(PS.fp, "2 2 %d RTXT ", PS.sbar.segments);
	set_ps_color(&(PS.sbar.font.color));
	fprintf(PS.fp, "1 2 %d RTXT ", PS.sbar.segments);
	fprintf(PS.fp, "(%s) x cwd 2 add add y MS\n", PS.sbar.units);
	break;
    case 'f':
    case 'F':
	fprintf(PS.fp, "/RBAR ");
	if (PS.sbar.type == 'F')
	    fprintf(PS.fp,
		    "{ {x exch dx mul add y chg 2 div sub dx 3 index RF} for pop} D\n");
	else
	    fprintf(PS.fp,
		    "{ {x exch dx mul add y dx 3 index RF} for pop} D\n");
	fprintf(PS.fp,
		"/RTXT {1 2 index length -- "
		"{dup x exch dx mul i mul add y 1 add M"
		" 1 index exch get SHC} for pop} D\n");
	fprintf(PS.fp, "RESET /dy chg neg def\n");
	set_ps_color(&(PS.sbar.fcolor));
	fprintf(PS.fp, "x %s y cwd dy 4 copy RF ",
		(PS.sbar.subsegs > 0 ? "dx sub" : ""));
	set_ps_color(&(PS.sbar.font.color));
	fprintf(PS.fp, ".5 LW RE\n");
	if (PS.sbar.type == 'F') {
	    fprintf(PS.fp, "dy 2 div neg 0 2 %d RBAR ", PS.sbar.segments - 1);
	    fprintf(PS.fp, "dy 2 div 1 2 %d RBAR\n", PS.sbar.segments - 1);
	}
	else {
	    fprintf(PS.fp, "dy 0 2 %d RBAR ", PS.sbar.segments - 1);
	}
	fprintf(PS.fp, "/i %d def AR0 0 RTXT ", PS.sbar.labels);
	if (PS.sbar.subsegs > 0) {
	    fprintf(PS.fp, "/dx dx %d div neg def ", PS.sbar.subsegs);
	    if (PS.sbar.type == 'F') {
		fprintf(PS.fp, "dy 2 div 0 2 %d RBAR ", PS.sbar.subsegs - 1);
		fprintf(PS.fp, "dy 2 neg div 1 2 %d RBAR ",
			PS.sbar.subsegs - 1);
	    }
	    else {
		fprintf(PS.fp, "dy 1 2 %d RBAR ", PS.sbar.subsegs - 1);
	    }
	    fprintf(PS.fp, "/i %d def AR1 1 RTXT\n", PS.sbar.sublabs);
	}
	fprintf(PS.fp, "xo wd add mgr sub yo hg sub mg add M (%s) SHR\n",
		PS.sbar.units);
	break;
    case 's':
    case 'S':
    default:
	fprintf(PS.fp,
		"/RBAR { {x exch dx mul add y M dup 0 exch LRS} for pop} D\n"
		"/RTXT {1 2 index length -- "
		"{dup x exch dx mul i mul add y dy add ++ M"
		" 1 index exch get SHC} for pop} D\n");
	fprintf(PS.fp, "RESET /dy chg 2 div def /y y dy sub def .5 LW\n");
	if (PS.sbar.type == 'S') {
	    set_ps_color(&(PS.sbar.fcolor));
	    fprintf(PS.fp, "x %s y cwd dy neg 4 copy RF ",
		    (PS.sbar.subsegs > 0 ? "dx sub" : ""));
	    set_ps_color(&(PS.sbar.font.color));
	    fprintf(PS.fp, "RE\n", PS.sbar.segments);
	}
	else {
	    set_ps_color(&(PS.sbar.font.color));
	    fprintf(PS.fp, "GS 2 LC x %s y dy sub M cwd 0 LRS GR\n",
		    (PS.sbar.subsegs > 0 ? "dx sub" : ""));
	}
	fprintf(PS.fp, "dy neg 0 1 %d RBAR\n", PS.sbar.segments);
	fprintf(PS.fp, "/i %d def AR0 0 RTXT ", PS.sbar.labels);
	fprintf(PS.fp, "dy 0 %d %d RBAR\n", PS.sbar.labels, PS.sbar.segments);
	if (PS.sbar.subsegs > 0) {
	    fprintf(PS.fp, "/dx dx %d div neg def ", PS.sbar.subsegs);
	    fprintf(PS.fp, "dy neg 1 1 %d RBAR ", PS.sbar.subsegs);
	    fprintf(PS.fp, "/i %d def AR1 1 RTXT\n", PS.sbar.sublabs);
	    fprintf(PS.fp, "dy 0 %d %d RBAR ", PS.sbar.sublabs,
		    PS.sbar.subsegs);
	}
	fprintf(PS.fp, "xo wd add mg sub y dy add ++ M (%s) SHR\n",
		PS.sbar.units);
	break;
    }
    fprintf(PS.fp, "GR\n");
    return 0;
}

char *strnumber(double num)
{
    static char text[50];

    if (num == 0)
	sprintf(text, "0");
    else if (num == (int)num)
	sprintf(text, "%.0f", num);
    else if ((num * 10.) == (int)(num * 10))
	sprintf(text, "%.1f", num);
    else if ((num * 100.) == (int)(num * 100))
	sprintf(text, "%.2f", num);
    else
	sprintf(text, "%.3f", num);

    return text;
}
