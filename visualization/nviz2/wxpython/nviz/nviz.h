#ifndef __NVIZ_H__
#define __NVIZ_H__

extern "C" {
#include <grass/gis.h>
#include <grass/gsurf.h>
#include <grass/gstypes.h>
#include <grass/nviz.h>
}

// For compilers that support precompilation, includes "wx.h".
#include <wx/wxprec.h>

#ifdef __BORLANDC__
#pragma hdrstop
#endif

#ifndef WX_PRECOMP
// Include your minimal set of headers here, or wx.h
#include <wx/wx.h>
#endif

#include <wx/glcanvas.h>

class Nviz
{
private:
    struct render_window *rwind;
    wxGLCanvas *glCanvas;

public:
    /* constructor */
    Nviz();

    /* destructor */
    ~Nviz();

    /* set */
    int SetDisplay(void *);
    int ResizeWindow(int, int);
};

#endif /* __NVIZ_H__ */
