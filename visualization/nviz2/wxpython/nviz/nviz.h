#ifndef __NVIZ_H__
#define __NVIZ_H__

#include <vector>

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
    nv_data *data;
    wxGLCanvas *glCanvas;

public:
    /* constructor */
    Nviz();

    /* destructor */
    ~Nviz();

    /* change_view.cpp */
    int ResizeWindow(int, int);

    /* set */
    /* init.cpp */
    int SetDisplay(void *);
    void Reset();

    /* lights */
    /* lights.cpp */
    void SetLightsDefault();
    
    /* viewport */
    /* change_view.cpp */
    float SetViewDefault();
    int SetView(float, float,
		float, float, float);

    /* init.cpp */
    void InitView();

    /* load data */
    /* load.cpp */
    int LoadRaster(const char*, const char *, const char *);

    /* draw */
    /* draw.cpp */
    void Draw();
    void EraseMap();
};

#endif /* __NVIZ_H__ */
