#ifndef __NVIZ_H__
#define __NVIZ_H__

extern "C" {
#include <grass/gsurf.h>
#include <grass/gstypes.h>
}

class Nviz
{
private:
    void swap_gl();
  
public:
    /* constructor */
    Nviz();
};

#endif /* __NVIZ_H__ */
