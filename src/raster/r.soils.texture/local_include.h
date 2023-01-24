/****************************************************************************
 *
 * MODULE:       r.soils.texture
 * AUTHOR(S):    Gianluca Massei (g_massa@libero.it)
 * PURPOSE:      Intended to define soil texture from sand and clay grid.
 *                 Require texture scheme supplied in scheme directory
 *
 * COPYRIGHT:    (C) 2008 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with
 *               GRASS for details.
 *
 *****************************************************************************/

/* for gettext macros - i18N localization */
#define MAX_POINT 15
#define MAX_LABEL 50

/*///////List element prototipe/////////////////////////////// */
struct TextureTriangleCoord {
    int numVertex; // polygons vertex of texture triangle
    float xSand[MAX_POINT],
        yClay[MAX_POINT]; // coordinate vector polygons in triangle
    int codeTexture;      // code for identify textural type
    struct TextureTriangleCoord *PointToNext; // pointer to next element
};

struct label_struct {
    int id;
    char etichetta[1024];
};

/*
 * function prototype
 */

struct TextureTriangleCoord *
ReadTriangle(int *, char *); // read texture file criteria (es. USDA.DAT)
int ReadList(struct TextureTriangleCoord *, int *, float,
             float); // read all list of texture criteria
int DefineTexture(int numVert, float *xSand, float *yClay, float SandVal,
                  float ClayVal,
                  int codeTxt); /*define texture for each point */
void reclassTexture(char *SchemeName,
                    char *result); // reclass texture file with label
