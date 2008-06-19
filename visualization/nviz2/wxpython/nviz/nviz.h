#ifndef __NVIZ_H__
#define __NVIZ_H__

extern "C" {
#include <grass/gis.h>
#include <grass/gsurf.h>
#include <grass/gstypes.h>
#include <grass/nviz.h>
}

class Nviz
{
private:
    // struct render_window *rwind;
    struct render_window *rwind;

public:
    /* constructor */
    Nviz();

    /* destructor */
    ~Nviz();

    /* set */
    int SetDisplay(void *, int, int);
};

#endif /* __NVIZ_H__ */
