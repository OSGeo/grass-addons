#include <string.h>
#include <unistd.h>
#include <math.h>
#include <stdlib.h>
#include <grass/raster.h>
#include "globals.h"
#include "local_proto.h"
#define NLINES 18
struct box
{
    int top, bottom, left,right;
};

static int uparrow ( struct box *,int);
static int downarrow ( struct box *,int) ;
static int pick(int,int);
static int done(void);
static int cancel_which(void);
static int inbox (struct box *,int,int);
static int dotext (char *,int,int,int,int,int,int);
static int compute_transformation(void);
static int to_file(void);
static int askfile(void);
static int to_printer(void);
static int do_report ( FILE *);
static int printcentered(FILE *,char *,int);
static int show_point(int,int);
static int offsetx, offsety;
static int n_old;
static int which;
static struct box more, less, report,box_lines, box_points;
static int height, size, edge, nlines;
static int curp, first_point;
static double rms,l_rms;
static double *xres, *yres, *gnd, *tres, *ures, *lgnd;
static int pager;
static int xmax, ymax, gmax;
static int tmax, umax, lgmax;
static char buf[300];
int new_control_line (Lines *ln,double t1,double u1,double t2,double u2,int status);
Lines lines;               /* contiene t ed u delle rette inserite */
int  use_points=1;
int top, bottom, left, right, width, middle, nums;
int count =0, first_line=0;
#define FMT0(buf,n) \
	sprintf (buf, "%3d ", n)
#define FMT1(buf,xres,yres,gnd) \
	sprintf (buf, "%5.1f %5.1f %6.1f ", xres,yres,gnd)
#define LHEAD1 "        error          "
#define LHEAD2 "  #   col   row  target"
#define LLINEHEAD2 "  #   dt    du   target"

#define FMT2(buf,e1,n1,e2,n2) \
	sprintf (buf, "%9.1f %9.1f %9.1f %9.1f ", e1,n1,e2,n2)
#define RHEAD1 "         image              target"
#define RHEAD2 "    east     north      east     north"
#define RLINEHEAD2 "    t1       u1         t2       u2  "

#define BACKGROUND GREY

int
analyze (void)
{

    double t_temp1,u_temp1, t_temp2, u_temp2;

    static int use = 1;
    static Objects objects[]=
    {
	MENU("DONE", done, &use),
	MENU("PRINT", to_printer, &use),
	MENU("FILE", to_file, &use),
	INFO(" Double click on point to be included/excluded ", &use),
	OTHER(pick,&use),
	{0}
    };

    int color;
    int tsize;
    int cury;
    int len;
    int line;
    int i;
/* to give user a response of some sort */
    if (group.points.count ==0)
    return 0;


    Menu_msg ("Preparing analysis ...");

/*
 * build a popup window at center of the screen.
 * 35% the height and wide enough to hold the report
 *
 */

  /* height of 1 line, based on NLINES taking up 35% vertical space */
    height = (.35 * (SCREEN_BOTTOM - SCREEN_TOP))/NLINES + 1;
    use_points=1;
/* size of text, 80% of line height */
    tsize = .8 * height;
    size = tsize-2; /* fudge for computing pixels width of text */

/* indent for the text */
    edge = .1 * height + 1;

/* determine the length, in chars, of printed line */
    FMT0 (buf,0);
    nums = strlen(buf) * size;
    FMT1 (buf, 0.0, 0.0, 0.0);
    len = strlen(buf);
    middle = len * size;
    FMT2 (buf, 0.0, 0.0, 0.0, 0.0);
    len += strlen(buf) ;

/* width is for max chars plus sidecar for more/less */
    width = len * size + nums + 2*height;
    if ((SCREEN_RIGHT - SCREEN_LEFT) < width)
	width = SCREEN_RIGHT - SCREEN_LEFT;


/* define the window */
    bottom = VIEW_MENU->top-1;
    top = bottom - height*NLINES;


    left = SCREEN_LEFT;
    right = left + width;
    middle += left + nums;
    nums += left;

/* save what is under this area, so it can be restored */
    R_panel_save (tempfile1, top, bottom, left, right);


/* fill it with white */
    R_standard_color (BACKGROUND);
    R_box_abs (left, top, right, bottom);

    right -= 2*height;	/* reduce it to exclude sidecar */

/* print messages in message area */
    R_text_size (tsize, tsize);


/* setup the more/less boxes in the sidecar */
    R_standard_color (BLACK);
    less.top = top;
    less.bottom = top + 2*height;
    less.left = right;
    less.right = right + 2*height;
    Outline_box (less.top, less.bottom, less.left, less.right);

    more.top = bottom - 2*height;
    more.bottom = bottom;
    more.left = right;
    more.right = right + 2*height;
    Outline_box (more.top, more.bottom, more.left, more.right);

/*
 * top two lines are for column labels
 * last two line is for overall rms error.
 */
    nlines = NLINES - 4;
    first_point = 0;

/* allocate predicted values */
    xres = (double *) G_calloc (group.points.count, sizeof (double));
    yres = (double *) G_calloc (group.points.count, sizeof (double));
    gnd  = (double *) G_calloc (group.points.count, sizeof (double));


   i=0;
  while(group.points.status[i]!=1 && i < group.points.count)
        i++;
  if(i >=group.points.count && group.points.status[i]!=1)
        i=0;
offsetx = group.points.e2[i] - group.points.e1[i];
offsety = group.points.n2[i] - group.points.n1[i];


lines.count=0;
for (i=0; i < group.points.count; i++)
      { if (group.points.status[i] == 2 || group.points.status[i] == -2)
        { points_to_line (group.points.e1[i], group.points.n1[i],group.points.e1[i+1], group.points.n1[i+1],&t_temp1,&u_temp1);
          points_to_line (group.points.e2[i]- offsetx, group.points.n2[i]-offsety,group.points.e2[i+1]-offsetx, group.points.n2[i+1]-offsety,&t_temp2,&u_temp2);

                  sprintf (buf, "t2[0] e u2[0]....   %f  %f   \n",10000*t_temp2,10000*u_temp2 );
	Curses_write_window (INFO_WINDOW, 3+ i, 2, buf);


          new_control_line ( &lines,10000*t_temp1,10000*u_temp1,10000*t_temp2,10000*u_temp2,group.points.status[i]);
         }
      }

   tres = (double *) G_calloc (lines.count, sizeof (double));
   ures = (double *) G_calloc (lines.count, sizeof (double));
   lgnd = (double *) G_calloc (lines.count, sizeof (double));

/* compute transformation for the first time */
    compute_transformation();


/* put head on the report */

    box_points.top=top;
    box_points.bottom=top+height-1;
    box_points.left= left;
    box_points.right=(right-left)/2;
    dotext ("        ANALYZE -> POINTS",top, top+height, left, (right-left)/2, 0, RED);
    Outline_box (box_points.top, box_points.bottom, box_points.left, box_points.right);

    box_lines.top=top;
    box_lines.bottom=top+height-1;
    box_lines.left= ((right- left)/2)+1;
    box_lines.right=right;
    dotext ("        ANALYZE -> LINES",top, top+height, ((right-left)/2)+1, right, 0, BLACK);
   Outline_box (box_lines.top, box_lines.bottom, box_lines.left, box_lines.right);

    cury=top;
    cury = top+height;
    dotext (LHEAD1, cury, cury+height, left, middle, 0, BLACK);
    dotext (RHEAD1, cury, cury+height, middle, right-1, 0, BLACK);
    cury += height;
    dotext (LHEAD2, cury, cury+height, left, middle, 0, BLACK);
    dotext (RHEAD2, cury, cury+height, middle, right-1, 0, BLACK);

    cury += height;
    R_move_abs (left, cury-1);
    R_cont_abs (right, cury-1);

/* isolate the sidecar */
    R_move_abs (right, top);
    R_cont_abs (right, bottom);

/* define report box */
    report.top = cury;
    report.left = left;
    report.right = right;
    count = 0;
    first_line = 0;

/* lets do it */
    pager = 1;
    while(1)
    {
                 R_text_size (tsize, tsize);
	line = 0;
	curp = first_point;
	cury = top + 3*height;
                 count=0;
	while(1)
	{
	    if (line >= nlines || curp >= group.points.count)
		break;
	    if(group.equation_stat > 0 && group.points.status[curp]==1)
	    {
                                   if(use_points){
                                        color = BLACK;
		        FMT1(buf, xres[curp], yres[curp], gnd[curp]);
		        if (curp == xmax || curp == ymax || curp == gmax)
		                color = RED;
		        dotext (buf, cury, cury+height, nums, middle, 0, color);
                                        line++;
                                        cury += height;
                                        }
	    }
                   else if(group.points.status[curp] ==2)
	    {
                                  /* if(group.points.status[curp+1]!=3)
                                        break;*/
                                   if(!use_points)
                                   {
                                        color = BLUE;
                                         if (count+first_line == tmax || count+first_line == umax || count+first_line == lgmax)
		                color = RED;
                                        sprintf (buf, "%5.1f %5.1f %5.1f ", tres[count+ first_line],ures[count+first_line],lgnd[count+first_line]);
                                        dotext (buf, cury, cury+height, nums, middle, 0, color);
                                        line++;
                                        cury += height;
                                   }

                                   curp++;
	    }
	    else if (group.points.status[curp] > 0) {
                                    FMT0 (buf, curp+1-count);
		        dotext (buf, cury, cury+height, left, nums, 0, BLACK);
		        FMT2(buf,
		            group.points.e1[curp],
		            group.points.n1[curp],
		            group.points.e2[curp],
		            group.points.n2[curp]);
		        dotext (buf, cury, cury+height, middle, right-1, 0, BLACK);
		dotext ("?", cury, cury+height, nums, middle, 1, BLACK);
                                   line++;
                                   cury += height;
                                   }

                     else if (group.points.status[curp] == -2 ){
                                 if(group.points.status[curp+1]!=-3)
                                        break;
                                if (!use_points) {
                                        dotext ("not used", cury, cury+height, nums, middle, 1, BLUE);
                                        line++;
                                        cury += height;
                                        }
                                curp++;
                                }
                      else  if (use_points) {
		dotext ("not used", cury, cury+height, nums, middle, 1, BLACK);
                                   line++;
                                   cury += height;
                                   }
     if (pager)
	    {
                                   if(use_points &&( group.points.status[curp]==1 || group.points.status[curp]==0))
                                   {

                                        FMT0 (buf, curp+1-2*(first_line+count));
		        dotext (buf, cury-height, cury, left, nums, 0, BLACK);
		        FMT2(buf,
		            group.points.e1[curp],
		            group.points.n1[curp],
		            group.points.e2[curp],
		            group.points.n2[curp]);
		        dotext (buf, cury-height, cury, middle, right-1, 0, BLACK);
                                  }
                                  if(!use_points &&( group.points.status[curp]>1 ||  group.points.status[curp]<-1))
                                  {
                                          FMT0 (buf, first_line + count);
		        dotext (buf, cury-height, cury, left, nums, 0, BLACK);
		        sprintf (buf, "%9.1f %9.1f %9.1f %9.1f ",
		            lines.t1[first_line+count],
		            lines.u1[first_line+count],
		            lines.t2[first_line+count],
		            lines.u2[first_line+count]);
		        dotext (buf, cury-height, cury, middle, right-1, 0, BLACK);

                                      }
	    }
                      if( group.points.status[curp]>1 ||  group.points.status[curp]<-1)
                                  count++;
	    curp++;
	}
	report.bottom = cury;
                  if(use_points) {
	        downarrow (&more,  ((group.points.count-curp)-2*(lines.count-(count+first_line)))>0 ? BLACK : BACKGROUND);
	        uparrow   (&less, first_point > 0  ? BLACK : BACKGROUND);
                  }
                  if(!use_points) {
	        downarrow (&more,  (lines.count-(count+first_line))>0 ? BLACK : BACKGROUND);
	        uparrow   (&less, first_point > 0  ? BLACK : BACKGROUND);
                  }

	R_standard_color (BACKGROUND);
	R_box_abs (left, cury, right-1, bottom);
                  if(use_points) {
                        if (group.equation_stat < 0)
	        {
	        color = RED;
	        strcpy (buf, "Poorly placed control points");
	        }
	        else if (group.equation_stat == 0)
	        {
	        color = RED;
	        strcpy (buf, "No active control points");
	        }
	        else
	        {
	         color = BLACK;
	        sprintf (buf, "Overall rms error: %.2f", rms);
	        }
                }
                else {
                         if (lines.line_stat < 0)
	        {
	        color = RED;
	        strcpy (buf, "Poorly placed control points");
	        }
	        else if (lines.line_stat == 0)
	        {
	        color = RED;
	        strcpy (buf, "No active control points");
	        }
	        else
	        {
	         color = BLACK;
	        sprintf (buf, "Overall rms error: %.2f", l_rms);
	        }
                  }
                dotext (buf, bottom-height, bottom, left, right-1, 0, color);
	R_standard_color (BLACK);
	R_move_abs (left, bottom-height);
	R_cont_abs (right-1, bottom-height);

	pager = 0;
	which = -1;
	if(Input_pointer(objects) < 0)
		break;



    }

/* all done. restore what was under the window */
    right += 2*height;	/* move it back over the sidecar */
    R_standard_color (BACKGROUND);
    R_box_abs (left, top, right, bottom);
    R_panel_restore (tempfile1);
    R_panel_delete (tempfile1);
    R_flush();

    free (xres); free (yres); free (gnd);
    put_control_points (group.name, &group.points);
    display_points(1);
    return 0; /* return but don't QUIT */
}


static int uparrow (struct box *box, int color)
{
    R_standard_color (color);
    Uparrow (box->top+edge, box->bottom-edge, box->left+edge, box->right-edge);

    return 0;
}

static int downarrow(struct box *box, int color)
{
    R_standard_color (color);
    Downarrow (box->top+edge, box->bottom-edge, box->left+edge, box->right-edge);

    return 0;
}

static int pick(int x,int y)
{
    int n;
    int cur;
    int i;

    cur = which;
    cancel_which();
    if (inbox(&more,x,y))
    {
	if (use_points && ((group.points.count-curp)-2*(lines.count-(count+first_line)))<=0)
	    return 0;
                  if(!use_points && (lines.count-(count+first_line))<=0)
                      return 0;
	first_point = curp;
                 first_line +=count;
        	pager = 1;
	return 1;
    }
    if (inbox(&box_points,x,y))
    {
                 R_text_size (.8*height, .8*height);
                 use_points=1;
                 dotext ("        ANALYZE -> POINTS",top, top+height, left, (right-left)/2, 0, RED);
                 dotext ("        ANALYZE -> LINES",top, top+height,((right-left)/2)+1, right, 0, BLACK);
                 Outline_box (box_points.top, box_points.bottom, box_points.left, box_points.right);
                 Outline_box (box_lines.top, box_lines.bottom, box_lines.left, box_lines.right);
                 dotext (LHEAD2, top+2*height, top+3*height, left, middle, 0, BLACK);
                 dotext (RHEAD2, top+2*height, top+3*height, middle, right-1, 0, BLACK);
                 first_point = 0;
                 first_line = 0;
                 pager = 1;
	return 1;
    }
    if (inbox(&box_lines,x,y))
    {
                 R_text_size (.8*height, .8*height);
                 use_points=0;
                 dotext ("        ANALYZE -> LINES",top, top+height, ((right-left)/2)+1, right, 0, RED);
                 dotext ("        ANALYZE -> POINTS",top, top+height, left, (right-left)/2, 0, BLACK);
                 Outline_box (box_points.top, box_points.bottom, box_points.left, box_points.right);
                 Outline_box (box_lines.top, box_lines.bottom, box_lines.left, box_lines.right);
                 dotext (LLINEHEAD2, top+2*height, top+3*height, left, middle, 0, BLACK);
                 dotext (RLINEHEAD2, top+2*height, top+3*height, middle, right-1, 0, BLACK);
                 first_point = 0;
                 first_line = 0;
                 pager = 1;
	return 1;
    }
    if (inbox(&less,x,y))
    {
	if (first_point == 0)
	    return 0;
	first_point = 0;
                 first_line = 0;
	pager = 1;
	return 1;
    }
    if (!inbox (&report,x,y))
    {
      return 0;
    }

   n_old = n = (y - report.top)/height;
    i=0;
    if(use_points){
        for (i; i<=n;  i++)
                if (group.points.status[first_point + i]==2||group.points.status[first_point + i]==-2) n+=2;
        }
    else { while (n>=0) {
                        if (group.points.status[first_point + i]==2||group.points.status[first_point + i]==-2)  {
                                                                          n--;
                                                                          i++;
                                                                          }
                          i++;
                                    }
              n=i-2;
              }
    if (n == cur) /* second click! */
    {
                 if  (group.points.status[first_point +n]==2||group.points.status[first_point +n]==-2) {
                         group.points.status[first_point+n] = -group.points.status[first_point+n];
                         group.points.status[first_point+(n+1)] = -group.points.status[first_point+(n+1)];
                         lines.status[first_line + n_old] = - lines.status[first_line + n_old];
                                                 }

                   else
                         group.points.status[first_point+n] = !group.points.status[first_point+n];
                 compute_transformation();
	show_point (first_point+n, 1);


           return 1;
    }
    which = n;
    show_point (first_point+n, 0);
    R_standard_color (RED);
    Outline_box (report.top + n*height, report.top +(n+1)*height,
		         report.left, report.right-1);
    return 0; /* ignore first click */

}

static int done (void)
{
    cancel_which();
    return -1;
}

static int cancel_which (void)
{
    if (which >= 0)
    {
	R_standard_color (BACKGROUND);
	Outline_box (report.top + which*height, report.top +(which+1)*height,
		         report.left, report.right-1);
	show_point (first_point+which, 1);
    }
    which = -1;

    return 0;
}

static int inbox (struct box *box,int x,int y)
{
    return (x>box->left && x <box->right && y>box->top && y<box->bottom);
}

static int dotext (char *text,
       int top,int bottom,int left,int right,int centered,int color)
{
    R_standard_color (BACKGROUND);
    R_box_abs (left, top, right, bottom);
    R_standard_color (color);
    R_move_abs (left+1+edge, bottom-1-edge);
    if (centered)
	R_move_rel ((right-left-strlen(text)*size)/2,0);
    R_set_window (top, bottom, left, right);	/* for text clipping */
    R_text (text);
    R_set_window (SCREEN_TOP, SCREEN_BOTTOM, SCREEN_LEFT, SCREEN_RIGHT);

    return 0;
}

static int compute_transformation (void)
{
    int n, count;
    double d,d1,d2,sum;
    double e1, e2, n1, n2;
    double t1, t2, u1, u2;
    double xval, yval, gval;
    double tval, uval, lgval;

    xmax = ymax = gmax = 0;
    xval = yval = gval = 0.0;

    Compute_equation();     /*trova gli A,B,C che legano punti dell'image a punti del ltarget  */
     lines.line_stat = compute_georef_equations_lp(&lines);

    if (group.equation_stat <= 0 && lines.line_stat<=0) return 1;

/* compute the row,col error plus ground error
 * keep track of largest and second largest error
 */
    sum = 0.0;
    rms = 0.0;
    count = 0;
    for (n = 0; n < group.points.count && group.equation_stat>0; n++)
    {
	if (group.points.status[n] !=1) continue;
	count++;
	georef (group.points.e2[n], group.points.n2[n], &e1, &n1, group.E21, group.N21);
	georef (group.points.e1[n], group.points.n1[n], &e2, &n2, group.E12, group.N12);

	if((d = xres[n] = e1-group.points.e1[n]) < 0)
	    d = -d;
	if (d > xval)
	{
	    xmax = n;
	    xval = d;
	}

	if ((d = yres[n] = n1-group.points.n1[n]) < 0)
	    d = -d;
	if (d > yval)
	{
	    ymax = n;
	    yval = d;
	}

/* compute ground error (ie along diagonal) */
	d1 = e2 - group.points.e2[n];
	d2 = n2 - group.points.n2[n];
	d = d1*d1 + d2*d2;
	sum += d;                 /* add it to rms sum, before taking sqrt */
	d = sqrt(d);
	gnd[n] = d;
	if (d > gval)             /* is this one the max? */
	{
	    gmax = n;
	    gval = d;
	}

    }
/* compute overall rms error */
     if (count)
	rms = sqrt (sum/count);

     count =0;
     tmax = umax = lgmax = 0;
     tval = uval = lgval = 0.0;
     sum = 0.0;
    l_rms = 0.0;
    for (n = 0; n < lines.count && lines.line_stat>0 ; n++)
    {
	if (lines.status[n] !=2) continue;
	count++;
	georef (lines.t2[n], lines.u2[n], &t1, &u1, lines.E21, lines.N21);
	georef (lines.t1[n], lines.u1[n], &t2, &u2, lines.E12, lines.N12);
	if((d = tres[n] = t1- lines.t1[n]) < 0)
	    d = -d;
	if (d > tval)
	{
	    tmax = n;
	    tval = d;
	}

	if ((d = ures[n] = u1- lines.u1[n]) < 0)
	    d = -d;
	if (d > uval)
	{
	    umax = n;
	    uval = d;
	}

/* compute ground error (ie along diagonal) */
	d1 = t2 - lines.t2[n];
	d2 = u2 - lines.u2[n];
	d = d1*d1 + d2*d2;
	sum += d;                 /* add it to rms sum, before taking sqrt */
	d = sqrt(d);
	lgnd[n] = d;
	if (d > lgval)             /* is this one the max? */
	{
	    lgmax = n;
	    lgval = d;
	}

    }
     if (count)
	l_rms = sqrt (sum/count);



    return 0;
}

static int to_file (void)
{
    FILE *fd;
    char msg[1024];

    cancel_which();
    if (Input_other (askfile, "Keyboard") < 0)
    {
	return 0;
    }

    fd = fopen (buf, "w");
    if (fd == NULL)
    {
	sprintf (msg, "** Unable to create file %s\n", buf);
	Beep();
	Curses_write_window (PROMPT_WINDOW, 2, 1, msg);
    }
    else
    {
	do_report (fd);
	fclose (fd);
	sprintf (msg, "Report saved in file %s\n", buf);
	Curses_write_window (PROMPT_WINDOW, 2, 1, msg);
    }
    return 0;
}

static int askfile (void)
{
    char file[100];

    while (1)
    {
	Curses_prompt_gets ("Enter file to hold report: ", file);
	G_strip (file);
	if (*file == 0) return -1;
	if (G_index (file, '/'))
	    strcpy (buf, file);
	else
	    sprintf (buf, "%s/%s", G_home(), file);
	if (access (buf, 0) != 0)
	    return 1;
	sprintf (buf, "** %s already exists. choose another file", file);
	Beep();
	Curses_write_window (PROMPT_WINDOW, 2, 1, buf);
    }

    return 0;
}

static int to_printer (void)
{
    FILE *fd;
    cancel_which();
    Menu_msg ("sending report to printer ...");

    fd = popen ("lpr", "w");
    do_report (fd);
    pclose (fd);
    return 0;
}

static int do_report ( FILE *fd)
{
    char buf[100];
    int n;
    int width;

    fprintf (fd, "LOCATION: %-20s GROUP: %-20s MAPSET: %s\n\n",
	G_location(), group.name, G_mapset());
    fprintf (fd, "%15sAnalysis of control point registration\n\n", "");
    fprintf (fd, "%s   %s\n", LHEAD1, RHEAD1);
    fprintf (fd, "%s   %s\n", LHEAD2, RHEAD2);

    FMT1 (buf,0.0,0.0,0.0);
    width = strlen (buf);

    for (n = 0; n < group.points.count; n++)
    {
	FMT0(buf,n+1);
	fprintf (fd, "%s", buf);
	if(group.equation_stat > 0 && group.points.status[n] > 0)
	{
	    FMT1(buf, xres[n], yres[n], gnd[n]);
	    fprintf (fd, "%s", buf);
	}
	else if (group.points.status[n] > 0)
	    printcentered (fd, "?", width);
	else
	    printcentered (fd, "not used", width);
	FMT2(buf,
	    group.points.e1[n],
	    group.points.n1[n],
	    group.points.e2[n],
	    group.points.n2[n]);
	fprintf (fd, "   %s\n", buf);
    }
    fprintf (fd, "\n");
    if (group.equation_stat < 0)
	fprintf (fd, "Poorly place control points\n");
    else if (group.equation_stat == 0)
	fprintf (fd, "No active control points\n");
    else
	fprintf (fd, "Overall rms error: %.2f\n", rms);

    return 0;
}

static int printcentered (FILE *fd, char *buf,int width)
{
    int len;
    int n;
    int i;

    len = strlen (buf);
    n = (width -len)/2;

    for (i = 0; i < n; i++)
	fprintf (fd, " ");
    fprintf (fd, "%s", buf);
    i += len;
    while (i++ < width)
	fprintf (fd, " ");

    return 0;
}

static int show_point(int n,int true_color)
{
   int  x_temp[2], y_temp[2];
   int row,col;

    if (!true_color)
	R_standard_color (ORANGE);
    else if(group.points.status[n]>0)
	R_standard_color (GREEN);
    else
	R_standard_color (RED);
     if (group.points.status[n]==0 || group.points.status[n] == 1 )
                display_one_point (VIEW_MAP1, group.points.e1[n], group.points.n1[n]);
     else {
                 display_one_point (VIEW_MAP1, group.points.e1[n], group.points.n1[n]);
                 display_one_point (VIEW_MAP1, group.points.e1[n+1], group.points.n1[n+1]);
                 row = northing_to_row (&VIEW_MAP1->cell.head, group.points.n1[n]) + .5;
                 col = easting_to_col  (&VIEW_MAP1->cell.head, group.points.e1[n]) + .5;
                 y_temp[0] = row_to_view (VIEW_MAP1, row);
                 x_temp[0] = col_to_view (VIEW_MAP1, col);

                 row = northing_to_row (&VIEW_MAP1->cell.head, group.points.n1[n+1]) + .5;
                 col = easting_to_col  (&VIEW_MAP1->cell.head,group.points.e1[n+1]) + .5;
                 y_temp[1] = row_to_view (VIEW_MAP1, row);
                 x_temp[1] = col_to_view (VIEW_MAP1, col);

                 R_polyline_abs (x_temp,y_temp,2);
                 R_flush();

     }
    return 0;
}


int points_to_line (double e1, double n1, double e2, double n2, double *t, double *u)
{
        double a,b,c;
        a=-(n2 - n1);
        b= (e2 - e1);
        c= (n2*e1 - n1*e2);
        *t= a/c;
        *u=b/c;
  }

int new_control_line ( Lines *ln,
    double t1,double u1,double t2,double u2,int status)
{
    int i;
    unsigned int size;

    i = (ln->count)++ ;
    size =  ln->count * sizeof(double) ;
    ln->t1 = (double *) G_realloc (ln->t1, size);
    ln->t2 = (double *) G_realloc (ln->t2, size);
    ln->u1 = (double *) G_realloc (ln->u1, size);
    ln->u2 = (double *) G_realloc (ln->u2, size);
    size =  ln->count * sizeof(int) ;
    ln->status = (int *) G_realloc (ln->status, size);

    ln->t1[i] = t1;
    ln->t2[i] = t2;
    ln->u1[i] = u1;
    ln->u2[i] = u2;
    ln->status[i] = status;

    return 0;
}
