#include "local_proto.h"
#include "macros.h"
#include "mbb.h"

/*******************************
These functions are mostly taken from the module v.hull (Aime, A., Neteler, M.,
Ducke, B., Landa, M.)

Minimum Bounding Block (MBB)
 - obtain vertices of 3D convex hull,
 - transform coordinates of vertices into coordinate system with axes parallel
to hull's edges,
 - find extents,
 - compute volumes and find minimum of them.
 *******************************
 */

/* Release all memory allocated for edges, faces and vertices */
void freeMem(void)
{
    tEdge e; /* Primary index into edge list. */
    tFace f; /* Primary pointer into face list. */
    tVertex v;
    tEdge te;   /* Temporary edge pointer. */
    tFace tf;   /* Temporary face pointer. */
    tVertex tv; /* Temporary vertex pointer. */

    e = edges;
    do {
        te = e;
        e = e->next;
        DELETE(edges, te);
    } while (e != edges);

    f = faces;
    do {
        tf = f;
        f = f->next;
        DELETE(faces, tf);
    } while (f != faces);

    v = vertices;
    do {
        tv = v;
        v = v->next;
        DELETE(vertices, tv);
    } while (v != vertices);

    FREE(te);
    FREE(tf);
    FREE(tv);

    DELETE(edges, e);
    DELETE(faces, f);
    DELETE(vertices, v);

    FREE(edges);
    FREE(faces);
    FREE(vertices);

    return;
}

/*-------------------------------------------------------------------*/
int make3DHull(struct points *pnts, struct convex *hull)
{
    int error;

    ReadVertices(pnts);

    error = DoubleTriangle();
    if (error < 0) {
        G_fatal_error("All points of 3D input map are in the same plane.\n  "
                      "Cannot create a 3D hull.");
    }

    ConstructHull();

    write_coord_faces(pnts, hull);

    freeMem();

    return (0);
}

/*---------------------------------------------------------------------
  MakeNullVertex: Makes a vertex, nulls out fields.
  ---------------------------------------------------------------------*/
tVertex MakeNullVertex(void)
{
    tVertex v;

    NEW(v, tsVertex); /* If memory not allocated => out of memory */
    v->duplicate = NULL;
    v->onhull = !ONHULL;
    v->mark = !PROCESSED;
    ADD(vertices, v);

    return v;
}

/*---------------------------------------------------------------------
  ReadVertices: Reads in the vertices, and links them into a circular
  list with MakeNullVertex.  There is no need for the # of vertices to be
  the first line: the function looks for EOF instead.  Sets the global
  variable vertices via the ADD macro.
  ---------------------------------------------------------------------*/
void ReadVertices(struct points *pnts)
{
    tVertex v;
    int vnum = 0;
    int i;

    double *r;

    r = &pnts->r[0];

    G_message(_("Reading 3D vertices..."));
    for (i = 0; i < pnts->n; i++) {
        v = MakeNullVertex();
        v->v[X] = *r;
        v->v[Y] = *(r + 1);
        v->v[Z] = *(r + 2);
        v->vnum = vnum++;
        r += 3;
        G_percent(i, (pnts->n - 1), 1);
    }
    fflush(stdout);
}

/*---------------------------------------------------------------------
  Outputs coordinates of 3D hull to matrix [n x 3]
  ---------------------------------------------------------------------*/
void write_coord_faces(struct points *pnts, struct convex *hull)
{
    int n = pnts->n;

    /* Pointers to vertices, edges, faces. */
    tVertex v;
    tFace f;
    int nv = 0, nf = 0;
    double *hc, *hf;

    hull->coord = (double *)malloc(n * 3 * sizeof(double));
    hull->faces = (double *)malloc(3 * n * 3 * sizeof(double));
    hc = &hull->coord[0];
    hf = &hull->faces[0];

    v = vertices;
    f = faces;

    do {
        /* Write vertex coordinates */
        *hc = ((double)(v->v[X]));
        *(hc + 1) = ((double)(v->v[Y]));
        *(hc + 2) = ((double)(v->v[Z]));

        v = v->next;
        hc += 3;
        nv += 3;

    } while (v != vertices);

    do {
        /* write one triangular face */
        *hf = ((double)(f->vertex[0]->v[X]));
        *(hf + 1) = ((double)(f->vertex[0]->v[Y]));
        *(hf + 2) = ((double)(f->vertex[0]->v[Z]));

        *(hf + 3) = ((double)(f->vertex[1]->v[X]));
        *(hf + 4) = ((double)(f->vertex[1]->v[Y]));
        *(hf + 5) = ((double)(f->vertex[1]->v[Z]));

        *(hf + 6) = ((double)(f->vertex[2]->v[X]));
        *(hf + 7) = ((double)(f->vertex[2]->v[Y]));
        *(hf + 8) = ((double)(f->vertex[2]->v[Z]));

        f = f->next;
        hf += 9;
        nf += 9;

    } while (f != faces);

    /* reclaim uneeded memory */
    hull->n = nv;
    hull->n_faces = nf;
    hull->coord = (double *)G_realloc(hull->coord, nv * 3 * sizeof(double));
    hull->faces = (double *)G_realloc(hull->faces, nf * 3 * sizeof(double));

    fflush(stdout);
}

/*---------------------------------------------------------------------
  DoubleTriangle builds the initial double triangle.  It first finds 3
  noncollinear points and makes two faces out of them, in opposite order.
  It then finds a fourth point that is not coplanar with that face.  The
  vertices are stored in the face structure in counterclockwise order so
  that the volume between the face and the point is negative. Lastly, the
  3 newfaces to the fourth point are constructed and the data structures
  are cleaned up.
  ---------------------------------------------------------------------*/

/* RETURN:      0 if OK */
/*              -1 if all points collinear */
/*              -2 if all points coplanar */

int DoubleTriangle(void)
{
    tVertex v0, v1, v2, v3;
    tFace f0, f1 = NULL;
    long int vol;

    /* Find 3 noncollinear points. */
    v0 = vertices;
    while (Collinear(v0, v0->next, v0->next->next)) {
        if ((v0 = v0->next) == vertices) {
            G_warning("DoubleTriangle:  All points are collinear!\n");
            return (-1);
        }
    }
    v1 = v0->next;
    v2 = v1->next;

    /* Mark the vertices as processed. */
    v0->mark = PROCESSED;
    v1->mark = PROCESSED;
    v2->mark = PROCESSED;

    /* Create the two "twin" faces. */
    f0 = MakeFace(v0, v1, v2, f1);
    f1 = MakeFace(v2, v1, v0, f0);

    /* Link adjacent face fields. */
    f0->edge[0]->adjface[1] = f1;
    f0->edge[1]->adjface[1] = f1;
    f0->edge[2]->adjface[1] = f1;
    f1->edge[0]->adjface[1] = f0;
    f1->edge[1]->adjface[1] = f0;
    f1->edge[2]->adjface[1] = f0;

    /* Find a fourth, noncoplanar point to form tetrahedron. */
    v3 = v2->next;
    vol = VolumeSign(f0, v3);
    while (!vol) {
        if ((v3 = v3->next) == v0) {
            G_warning("DoubleTriangle:  All points are coplanar!\n");
            return (-2);
        }
        vol = VolumeSign(f0, v3);
    }

    /* Insure that v3 will be the first added. */
    vertices = v3;

    return (0);
}

/*---------------------------------------------------------------------
  ConstructHull adds the vertices to the hull one at a time.  The hull
  vertices are those in the list marked as onhull.
  ---------------------------------------------------------------------*/
int ConstructHull(void)
{
    tVertex v, vnext;
    bool changed; /* T if addition changes hull; not used. */
    int i;
    int numVertices;

    G_message(_("Constructing 3D hull..."));

    v = vertices;
    i = 0;
    do {
        vnext = v->next;
        v = vnext;
        i++;
    } while (v != vertices);
    numVertices = i;

    v = vertices;
    i = 0;
    do {
        vnext = v->next;
        if (!v->mark) {
            v->mark = PROCESSED;
            changed = AddOne(v);
            CleanUp();
        }
        v = vnext;
        i++;

        G_percent(i, numVertices, 1);

    } while (v != vertices);

    fflush(stdout);

    return numVertices;
}

/*---------------------------------------------------------------------
  AddOne is passed a vertex.  It first determines all faces visible from
  that point.  If none are visible then the point is marked as not
  onhull.  Next is a loop over edges.  If both faces adjacent to an edge
  are visible, then the edge is marked for deletion.  If just one of the
  adjacent faces is visible then a new face is constructed.
  ---------------------------------------------------------------------*/
bool AddOne(tVertex p)
{
    tFace f;
    tEdge e, temp;
    long int vol;
    bool vis = false;

    /* Mark faces visible from p. */
    f = faces;
    do {
        vol = VolumeSign(f, p);

        if (vol < 0) {
            f->visible = VISIBLE;
            vis = true;
        }
        f = f->next;
    } while (f != faces);

    /* If no faces are visible from p, then p is inside the hull. */
    if (!vis) {
        p->onhull = !ONHULL;
        return false;
    }

    /* Mark edges in interior of visible region for deletion.
       Erect a newface based on each border edge. */
    e = edges;
    do {
        temp = e->next;
        if (e->adjface[0]->visible && e->adjface[1]->visible)
            /* e interior: mark for deletion. */
            e->del = REMOVED;
        else if (e->adjface[0]->visible || e->adjface[1]->visible)
            /* e border: make a new face. */
            e->newface = MakeConeFace(e, p);
        e = temp;
    } while (e != edges);
    return true;
}

/*---------------------------------------------------------------------
  VolumeSign returns the sign of the volume of the tetrahedron determined by f
  and p.  VolumeSign is +1 iff p is on the negative side of f,
  where the positive side is determined by the rh-rule.  So the volume
  is positive if the ccw normal to f points outside the tetrahedron.
  The final fewer-multiplications form is due to Bob Williamson.
  ---------------------------------------------------------------------*/
int VolumeSign(tFace f, tVertex p)
{
    double vol;
    double ax, ay, az, bx, by, bz, cx, cy, cz;

    ax = f->vertex[0]->v[X] - p->v[X];
    ay = f->vertex[0]->v[Y] - p->v[Y];
    az = f->vertex[0]->v[Z] - p->v[Z];
    bx = f->vertex[1]->v[X] - p->v[X];
    by = f->vertex[1]->v[Y] - p->v[Y];
    bz = f->vertex[1]->v[Z] - p->v[Z];
    cx = f->vertex[2]->v[X] - p->v[X];
    cy = f->vertex[2]->v[Y] - p->v[Y];
    cz = f->vertex[2]->v[Z] - p->v[Z];

    vol = ax * (by * cz - bz * cy) + ay * (bz * cx - bx * cz) +
          az * (bx * cy - by * cx);

    /* The volume should be an integer. */
    if (vol > 0.0)
        return 1;
    else if (vol < -0.0)
        return -1;
    else
        return 0;
}

/*---------------------------------------------------------------------
  MakeConeFace makes a new face and two new edges between the
  edge and the point that are passed to it. It returns a pointer to
  the new face.
  ---------------------------------------------------------------------*/
tFace MakeConeFace(tEdge e, tVertex p)
{
    tEdge new_edge[2];
    tFace new_face;
    int i, j;

    /* Make two new edges (if don't already exist). */
    for (i = 0; i < 2; ++i)
        /* If the edge exists, copy it into new_edge. */
        if (!(new_edge[i] = e->endpts[i]->duplicate)) {
            /* Otherwise (duplicate is NULL), MakeNullEdge. */
            new_edge[i] = MakeNullEdge();
            new_edge[i]->endpts[0] = e->endpts[i];
            new_edge[i]->endpts[1] = p;
            e->endpts[i]->duplicate = new_edge[i];
        }

    /* Make the new face. */
    new_face = MakeNullFace();
    new_face->edge[0] = e;
    new_face->edge[1] = new_edge[0];
    new_face->edge[2] = new_edge[1];
    MakeCcw(new_face, e, p);

    /* Set the adjacent face pointers. */
    for (i = 0; i < 2; ++i)
        for (j = 0; j < 2; ++j)
            /* Only one NULL link should be set to new_face. */
            if (!new_edge[i]->adjface[j]) {
                new_edge[i]->adjface[j] = new_face;
                break;
            }

    return new_face;
}

/*---------------------------------------------------------------------
  MakeCcw puts the vertices in the face structure in counterclock wise
  order.  We want to store the vertices in the same
  order as in the visible face.  The third vertex is always p.
  ---------------------------------------------------------------------*/
void MakeCcw(tFace f, tEdge e, tVertex p)
{
    tFace fv; /* The visible face adjacent to e */
    int i;    /* Index of e->endpoint[0] in fv. */
    tEdge s;  /* Temporary, for swapping */

    if (e->adjface[0]->visible)
        fv = e->adjface[0];
    else
        fv = e->adjface[1];

    /* Set vertex[0] & [1] of f to have the same orientation
       as do the corresponding vertices of fv. */
    for (i = 0; fv->vertex[i] != e->endpts[0]; ++i)
        ;
    /* Orient f the same as fv. */
    if (fv->vertex[(i + 1) % 3] != e->endpts[1]) {
        f->vertex[0] = e->endpts[1];
        f->vertex[1] = e->endpts[0];
    }
    else {
        f->vertex[0] = e->endpts[0];
        f->vertex[1] = e->endpts[1];
        SWAP(s, f->edge[1], f->edge[2]);
    }
    /* This swap is tricky. e is edge[0]. edge[1] is based on endpt[0],
       edge[2] on endpt[1].  So if e is oriented "forwards," we
       need to move edge[1] to follow [0], because it precedes. */

    f->vertex[2] = p;
}

/*---------------------------------------------------------------------
  MakeNullEdge creates a new cell and initializes all pointers to NULL
  and sets all flags to off.  It returns a pointer to the empty cell.
  ---------------------------------------------------------------------*/
tEdge MakeNullEdge(void)
{
    tEdge e;

    NEW(e, tsEdge);
    e->adjface[0] = e->adjface[1] = e->newface = NULL;
    e->endpts[0] = e->endpts[1] = NULL;
    e->del = !REMOVED;
    ADD(edges, e);
    return e;
}

/*--------------------------------------------------------------------
  MakeNullFace creates a new face structure and initializes all of its
  flags to NULL and sets all the flags to off.  It returns a pointer
  to the empty cell.
  ---------------------------------------------------------------------*/
tFace MakeNullFace(void)
{
    tFace f;
    int i;

    NEW(f, tsFace);
    for (i = 0; i < 3; ++i) {
        f->edge[i] = NULL;
        f->vertex[i] = NULL;
    }
    f->visible = !VISIBLE;
    ADD(faces, f);
    return f;
}

/*---------------------------------------------------------------------
  MakeFace creates a new face structure from three vertices (in ccw
  order).  It returns a pointer to the face.
  ---------------------------------------------------------------------*/
tFace MakeFace(tVertex v0, tVertex v1, tVertex v2, tFace fold)
{
    tFace f;
    tEdge e0, e1, e2;

    /* Create edges of the initial triangle. */
    if (!fold) {
        e0 = MakeNullEdge();
        e1 = MakeNullEdge();
        e2 = MakeNullEdge();
    }
    else { /* Copy from fold, in reverse order. */
        e0 = fold->edge[2];
        e1 = fold->edge[1];
        e2 = fold->edge[0];
    }
    e0->endpts[0] = v0;
    e0->endpts[1] = v1;
    e1->endpts[0] = v1;
    e1->endpts[1] = v2;
    e2->endpts[0] = v2;
    e2->endpts[1] = v0;

    /* Create face for triangle. */
    f = MakeNullFace();
    f->edge[0] = e0;
    f->edge[1] = e1;
    f->edge[2] = e2;
    f->vertex[0] = v0;
    f->vertex[1] = v1;
    f->vertex[2] = v2;

    /* Link edges to face. */
    e0->adjface[0] = e1->adjface[0] = e2->adjface[0] = f;

    return f;
}

/*---------------------------------------------------------------------
  CleanUp goes through each data structure list and clears all
  flags and NULLs out some pointers.  The order of processing
  (edges, faces, vertices) is important.
  ---------------------------------------------------------------------*/
void CleanUp(void)
{
    CleanEdges();
    CleanFaces();
    CleanVertices();

    return;
}

/*---------------------------------------------------------------------
  CleanEdges runs through the edge list and cleans up the structure.
  If there is a newface then it will put that face in place of the
  visible face and NULL out newface. It also deletes so marked edges.
  ---------------------------------------------------------------------*/
void CleanEdges(void)
{
    tEdge e; /* Primary index into edge list. */
    tEdge t; /* Temporary edge pointer. */

    /* Integrate the newface's into the data structure. */
    /* Check every edge. */
    e = edges;
    do {
        if (e->newface) {
            if (e->adjface[0]->visible)
                e->adjface[0] = e->newface;
            else
                e->adjface[1] = e->newface;
            e->newface = NULL;
        }
        e = e->next;
    } while (e != edges);

    /* Delete any edges marked for deletion. */
    while (edges && edges->del) {
        e = edges;
        DELETE(edges, e);
    }
    e = edges->next;
    do {
        if (e->del) {
            t = e;
            e = e->next;
            DELETE(edges, t);
        }
        else
            e = e->next;
    } while (e != edges);

    return;
}

/*---------------------------------------------------------------------
  CleanFaces runs through the face list and deletes any face marked visible.
  ---------------------------------------------------------------------*/
void CleanFaces(void)
{
    tFace f; /* Primary pointer into face list. */
    tFace t; /* Temporary pointer, for deleting. */

    while (faces && faces->visible) {
        f = faces;
        DELETE(faces, f);
    }
    f = faces->next;
    do {
        if (f->visible) {
            t = f;
            f = f->next;
            DELETE(faces, t);
        }
        else
            f = f->next;
    } while (f != faces);

    return;
}

/*---------------------------------------------------------------------
  CleanVertices runs through the vertex list and deletes the
  vertices that are marked as processed but are not incident to any
  undeleted edges.
  ---------------------------------------------------------------------*/
void CleanVertices(void)
{
    tEdge e;
    tVertex v, t;

    /* Mark all vertices incident to some undeleted edge as on the hull. */
    e = edges;
    do {
        e->endpts[0]->onhull = e->endpts[1]->onhull = ONHULL;
        e = e->next;
    } while (e != edges);

    /* Delete all vertices that have been processed but
       are not on the hull. */
    while (vertices && vertices->mark && !vertices->onhull) {
        v = vertices;
        DELETE(vertices, v);
    }
    v = vertices->next;
    do {
        if (v->mark && !v->onhull) {
            t = v;
            v = v->next;
            DELETE(vertices, t)
        }
        else
            v = v->next;
    } while (v != vertices);

    /* Reset flags. */
    v = vertices;
    do {
        v->duplicate = NULL;
        v->onhull = !ONHULL;
        v = v->next;
    } while (v != vertices);

    return;
}

/*---------------------------------------------------------------------
  Collinear checks to see if the three points given are collinear,
  by checking to see if each element of the cross product is zero.
  ---------------------------------------------------------------------*/
bool Collinear(tVertex a, tVertex b, tVertex c)
{
    return (c->v[Z] - a->v[Z]) * (b->v[Y] - a->v[Y]) -
                   (b->v[Z] - a->v[Z]) * (c->v[Y] - a->v[Y]) ==
               0 &&
           (b->v[Z] - a->v[Z]) * (c->v[X] - a->v[X]) -
                   (b->v[X] - a->v[X]) * (c->v[Z] - a->v[Z]) ==
               0 &&
           (b->v[X] - a->v[X]) * (c->v[Y] - a->v[Y]) -
                   (b->v[Y] - a->v[Y]) * (c->v[X] - a->v[X]) ==
               0;
}

void convexHull3d(struct points *pnts, struct convex *hull)
{
    int error;

    error = make3DHull(pnts, hull); /* make 3D hull */
    if (error < 0) {
        G_fatal_error(_("Simple planar hulls not implemented yet"));
    }

    return;
}

/* ----------------------------
 * MBR area estimation
 */
double MBB(struct points *pnts)
{
    int i, k;
    double usx, usy, cosusx, sinusx, cosusy, sinusy, V, V_min;
    double *hc_k, *hf, *ht; // pointers to hull_trans and hull->faces
    double *r_min, *r_max;

    r_min = (double *)G_malloc(3 * sizeof(double));
    r_max = (double *)G_malloc(3 * sizeof(double));

    double
        *hull_trans; /* Coordinates of hull vertices transformed into coordinate
                        system with axes parallel to hull's edges */

    hull_trans = (double *)malloc(3 * sizeof(double));
    ht = &hull_trans[0];

    struct convex hull;

    convexHull3d(pnts, &hull);
    hc_k = &hull.coord[0];
    hf = &hull.faces[0];

    V_min = (pnts->r_max[0] - pnts->r_min[0]) *
            (pnts->r_max[1] - pnts->r_min[1]) *
            (pnts->r_max[2] - pnts->r_min[2]); /* Volume of extent */

    for (i = 0; i < hull.n_faces - 2;
         i += 3) { /* n = number of vertices (n/3 = number of faces) */
        /* Bearings of hull edges */
        usx = bearing(*(hull.faces + 1), *(hull.faces + 4), *(hull.faces + 2),
                      *(hull.faces + 5));
        usy = bearing(*hull.faces, *(hull.faces + 6), *(hull.faces + 2),
                      *(hull.faces + 8));

        if (usx == -9999 || usy == -9999) /* Identical points */
            continue;
        cosusx = cos(usx);
        sinusx = sin(usx);
        cosusy = cos(usy);
        sinusy = sin(usy);

        hc_k = &hull.coord[0]; // original coords
        for (k = 0; k < hull.n; k++) {
            /* Coordinate transformation */
            *ht = *hc_k * cos(usy) + 0 - *(hc_k + 2) * sin(usy);
            *(ht + 1) = *hc_k * sinusx * sinusy + *(hc_k + 1) * cosusx +
                        *(hc_k + 2) * sinusx * cosusy;
            *(ht + 2) = *hc_k * cosusx * sinusy - *(hc_k + 1) * sinusx +
                        *(hc_k + 2) * cosusx * cosusy;

            /* Transformed extent */
            switch (k) {
            case 0:
                r_min = r_max = triple(*ht, *(ht + 1), *(ht + 2));
                break;
            default:
                r_min = triple(MIN(*ht, *r_min), MIN(*(ht + 1), *(r_min + 1)),
                               MIN(*(ht + 2), *(r_min + 2)));
                r_max = triple(MAX(*ht, *r_max), MAX(*(ht + 1), *(r_max + 1)),
                               MAX(*(ht + 2), *(r_max + 2)));
            }
            hc_k += 3;
        } // end k

        hf += 9;

        V = (*r_max - *r_min) * (*(r_max + 1) - *(r_min + 1)) *
            (*(r_max + 2) - *(r_min + 2)); /* Area of transformed extent */
        V_min = MIN(V, V_min);
    } // end i

    return V_min;
}
