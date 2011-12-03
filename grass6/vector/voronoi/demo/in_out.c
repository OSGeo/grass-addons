#include "data_types.h"
#include "memory.h"
#include "edge.h"
#include "geom_primitives.h"

#include <stdio.h>
#include <stdlib.h>

#include <cairo.h>
#include <math.h>

cairo_surface_t *surface;
cairo_t *cr;

static void print_edges(unsigned int n);
static void print_triangles(unsigned int n);

void read_points(unsigned int n){
    int i;
    for (i = 0; i < n; i++)
        if (scanf("%f %f", &sites[i].x, &sites[i].y) != 2)
            problem("Error reading sites.");

}

void print_results(unsigned int n, char option){
    /* Print either triangles or edges */
    if (option == 't')
        print_triangles(n);
    else
        print_edges(n);
}

/* 
 *  Print the ring of edges about each vertex.
 */
static void print_edges(unsigned int n){
    struct edge *e_start, *e;
    struct vertex *u, *v;
    unsigned int i;

    for (i = 0; i < n; i++) {
        u = &sites[i];
        e_start = e = u->entry_pt;
        do{
            v = OTHER_VERTEX(e, u);
            if (u < v)
                if (printf("%d %d\n", u - sites, v - sites) == EOF)
                    problem("Error printing results\n");
            e = NEXT(e, u);
        } while (!SAME_EDGE(e, e_start));
    }
}

/* draw triangulation */
void draw_sites(int n){
    int i;

    surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, 1280, 800);

    cr = cairo_create(surface);
/*    for (i = 0; i < n; i++) {
        cairo_arc(cr, sites[i].x, sites[i].y, 1, 0, 2 * M_PI);
        cairo_stroke (cr);
    }*/
}

void draw(unsigned int n){
    struct edge *e_start, *e;
    struct vertex *u, *v;
    unsigned int i;

    draw_sites(n);
    cairo_set_line_width (cr, 1);

    int x1, y1, x2, y2;
    for (i = 0; i < n; i++) {
        u = &sites[i];
        e_start = e = u->entry_pt;
        do{
            v = OTHER_VERTEX(e, u);
            if (u < v) {
                x1 = (int) sites[u - sites].x;
                y1 = (int) sites[u - sites].y;
                x2 = (int) sites[v - sites].x;
                y2 = (int) sites[v - sites].y;

                cairo_move_to (cr, x1, y1);
                cairo_line_to (cr, x2, y2);
                cairo_stroke (cr);
          /*      printf("e1=%d e2=%d\n", u - sites, v - sites);
                printf("%3d %3d %3d %3d \n", x1, y1, x2, y2);
                */
            }
            e = NEXT(e, u);
        } while (!SAME_EDGE(e, e_start));
    }
    cairo_destroy (cr);
    cairo_surface_write_to_png (surface, "dt.png");
    cairo_surface_destroy (surface);
}

/* 
 *  Print the ring of triangles about each vertex.
 */
static void print_triangles(unsigned int n)
{
    struct edge *e_start, *e, *next;
    struct vertex *u, *v, *w;
    unsigned int i;
    struct vertex *temp;

    for (i = 0; i < n; i++) {
        u = &sites[i];
        e_start = e = u->entry_pt;
        do {
            v = OTHER_VERTEX(e, u);
            if (u < v) {
                next = NEXT(e, u);
                w = OTHER_VERTEX(next, u);
                if (u < w)
                    if (SAME_EDGE(NEXT(next, w), PREV(e, v))) {  
                        /* Triangle. */
                        if (v > w) { 
                            temp = v; 
                            v = w; 
                            w = temp;
                        }
                        if (printf("%d %d %d\n", u - sites, v - sites, w - sites) == EOF)
                            problem("Error printing results\n");
                    }
            }
            /* Next edge around u. */
            e = NEXT(e, u);
        } while (!SAME_EDGE(e, e_start));
    }
}
