#include "globals.h"
#include "local_proto.h"

static int cancel();
static int use_zoom_box = 1;
static int use_zoom_pnt = 0;



int zoom()
{
    static int use = 1;
    int cancel();
    /*static int which_zoom();*/

   static Objects objects[]=
    {
      MENU("CANCEL",cancel,&use),
      INFO("Current ZOOM Type.",&use),
      OPTION("BOX",   2, &use_zoom_box),
      OPTION("POINT", 2, &use_zoom_pnt),
      OTHER(which_zoom, &use),
      {0}
 };

  Input_pointer (objects);
  return 0;	/* return, but don't QUIT */
}

static int
which_zoom(int x,int y,int button)
{

  /* Button one to set point, Button 2 & 3 return location */
  if (button != 1)
    return where (x,y);


  if (use_zoom_box == 1)
    zoom_box(x,y);             
  else zoom_pnt(x,y);

  return 0;
}




static int 
cancel (void)
{
    return -1;
}
