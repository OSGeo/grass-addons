/*!
  \file render.c
 
  \brief GLX context manipulation
  
  COPYRIGHT: (C) 2008 by the GRASS Development Team

  This program is free software under the GNU General Public
  License (>=v2). Read the file COPYING that comes with GRASS
  for details.

  Based on visualization/nviz/src/togl.c etc.

  \author Updated/modified by Martin Landa <landa.martin gmail.com>

  \date 2008
*/

#include <grass/gis.h>
#include <grass/glocale.h>

#include "render.h"

/*!
  \brief Initialize render window

  \param win pointer to render_window struct
*/
void render_window_init(render_window * win)
{
    win->displayId = NULL;
    win->contextId = NULL;
    win->pixmap = 0;
    win->windowId = 0;
}

/*!
  \brief Create rendew window

  \param win pointer to render_window struct
  \param width window width
  \param height window height

  \return 1
*/
int render_window_create(render_window *win, int width, int height)
{
    XVisualInfo  *v;

    int attributeList[] = { GLX_RGBA, GLX_RED_SIZE, 1,
			    GLX_GREEN_SIZE, 1, GLX_BLUE_SIZE, 1,
			    GLX_DEPTH_SIZE, 1, None };
    /*
    int attributeList[] = { GLX_USE_GL, GLX_RED_SIZE, 1,
			    GLX_GREEN_SIZE, 1, GLX_BLUE_SIZE, 1,
			    GLX_DEPTH_SIZE, 1, GLX_DOUBLEBUFFER,
			    None };
    */
    /* get the default display connection */
    win->displayId = XOpenDisplay((char *) NULL);
    if (!win->displayId) {
	G_fatal_error (_("Bad X server connection"));
    }

    /* get visual info and set up pixmap buffer */
    v = glXChooseVisual(win->displayId,
			DefaultScreen(win->displayId),
			attributeList);

    win->contextId = glXCreateContext(win->displayId,
				      v, NULL, GL_FALSE);
    if (!win->contextId) {
	G_fatal_error (_("Unable to create GLX rendering context"));
    }

    /* create win pixmap to render to (same depth as RootWindow) */
    win->pixmap = XCreatePixmap(win->displayId,
				RootWindow(win->displayId, v->screen),
				width,
				height,
				v->depth);

    /* create an off-screen GLX rendering area */
    win->windowId = glXCreateGLXPixmap(win->displayId,
				       v, win->pixmap);

    if (v) {
	XFree(v);
    }

    /*
    this->MakeCurrent();

    glMatrixMode( GL_MODELVIEW );

    glDepthFunc( GL_LEQUAL );
    glEnable( GL_DEPTH_TEST );
    glTexEnvf( GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE );
    glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );
    glEnable(GL_BLEND);
    glEnable( GL_NORMALIZE );
    glAlphaFunc(GL_GREATER,0);
    this->Mapped = 0; // if its mapped, then it trys windowgetattributes which fails!
    this->SwapBuffers = 0;
    this->DoubleBuffer = 0;
    */

    return 1;
}

/*!
  \brief Free render window

  \param win pointer to render_window struct

  \return 1
*/
int render_window_destroy(render_window *win)
{
    glXDestroyContext(win->displayId, win->contextId);
    XFreePixmap(win->displayId, win->pixmap);

    render_window_init(win);

    return 1;
}

/*!
  \brief Make window current for rendering

  \param win pointer to render_window struct

  \return 1
*/
int render_window_make_current(const render_window *win)
{
    if (!win->displayId || !win->contextId)
	return 0;

    if (win->contextId == glXGetCurrentContext())
	return 1;

    glXMakeCurrent(win->displayId, win->windowId,
		   win->contextId);

    /* TODO: AQUA */

    return 1;
}

void swap_gl()
{
    return;
}
