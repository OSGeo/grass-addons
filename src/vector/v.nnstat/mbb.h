#include "local_proto.h"

/*
  These functions are mostly taken from the module v.hull (Aime, A., Neteler,
  M., Ducke, B., Landa, M.)
*/

/* Define vertex indices. */
#define X 0
#define Y 1
#define Z 2

/* Define structures for vertices, edges and faces */
typedef struct tVertexStructure tsVertex;
typedef tsVertex *tVertex;

typedef struct tEdgeStructure tsEdge;
typedef tsEdge *tEdge;

typedef struct tFaceStructure tsFace;
typedef tsFace *tFace;

struct tVertexStructure {
    double v[3];
    int vnum;
    tEdge duplicate; /* pointer to incident cone edge (or NULL) */
    bool onhull;     /* T iff point on hull. */
    bool mark;       /* T iff point already processed. */
    tVertex next, prev;
};

struct tEdgeStructure {
    tFace adjface[2];
    tVertex endpts[2];
    tFace newface; /* pointer to incident cone face. */
    bool del;      /* T iff edge should be delete. */
    tEdge next, prev;
};

struct tFaceStructure {
    tEdge edge[3];
    tVertex vertex[3];
    bool visible; /* T iff face visible from new point. */
    tFace next, prev;
};

/* Define flags */
#define ONHULL    true
#define REMOVED   true
#define VISIBLE   true
#define PROCESSED true

/* Global variable definitions */
tVertex vertices = NULL;
tEdge edges = NULL;
tFace faces = NULL;

/* Function declarations */
tVertex MakeNullVertex(void);
void ReadVertices(struct points *);
void writeVertices(struct Map_info *Map);
void write_coord_faces(struct points *, struct convex *);
int DoubleTriangle(void);
int ConstructHull(void);
bool AddOne(tVertex p);
int VolumeSign(tFace f, tVertex p);
tFace MakeConeFace(tEdge e, tVertex p);
void MakeCcw(tFace f, tEdge e, tVertex p);
tEdge MakeNullEdge(void);
tFace MakeNullFace(void);
tFace MakeFace(tVertex v0, tVertex v1, tVertex v2, tFace f);
void CleanUp(void);
void CleanEdges(void);
void CleanFaces(void);
void CleanVertices(void);
bool Collinear(tVertex a, tVertex b, tVertex c);
