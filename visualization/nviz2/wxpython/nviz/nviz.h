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

#define VIEW_DEFAULT_POS_X 0.85
#define VIEW_DEFAULT_POS_Y 0.85
#define VIEW_DEFAULT_PERSP 40.0
#define VIEW_DEFAULT_TWIST 0.0
#define VIEW_DEFAULT_ZEXAG 1.0

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
    float SetViewDefault();
    int SetView(float, float,
		float, float, float);
    int SetZExag(float);

    /* init.cpp */
    int SetDisplay(void *);
    void InitView();
    void Reset();

    /* lights.cpp */
    void SetLightsDefault();

    /* load.cpp */
    int LoadRaster(const char*, const char *, const char *);

    /* draw.cpp */
    void Draw(bool);
    void EraseMap();

    /* surface.cpp */
    void SetSurfaceColor(int, bool, const char *);
};

#endif /* __NVIZ_H__ */
