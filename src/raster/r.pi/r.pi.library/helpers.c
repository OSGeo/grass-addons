#include "r_pi.h"

int Round(double d)
{
    return d < 0 ? d - 0.5 : d + 0.5;
}

int Random(int max)
{
    return max <= RAND_MAX
               ? rand() % max
               : floor((((double)RAND_MAX + 1) / ((double)rand())) * max);
}

double Randomf()
{
    return ((double)rand()) / ((double)RAND_MAX);
}

void print_buffer(int *buffer, int sx, int sy)
{
    int x, y;

    fprintf(stderr, "buffer:\n");
    for (y = 0; y < sy; y++) {
        for (x = 0; x < sx; x++) {
            switch (buffer[x + y * sx]) {
            case TYPE_NOTHING:
                fprintf(stderr, "*");
                break;
            default:
                if (buffer[x + y * sx] < 0) {
                    fprintf(stderr, "%d", buffer[x + y * sx]);
                }
                else {
                    fprintf(stderr, "%d", buffer[x + y * sx]);
                }
                break;
            }
        }
        fprintf(stderr, "\n");
    }
}

void print_d_buffer(DCELL *buffer, int sx, int sy)
{
    int x, y;

    fprintf(stderr, "buffer:\n");
    for (y = 0; y < sy; y++) {
        for (x = 0; x < sx; x++) {
            fprintf(stderr, "%0.2f ", buffer[y * sx + x]);
        }
        fprintf(stderr, "\n");
    }
}

void print_array(DCELL *buffer, int size)
{
    int i;

    for (i = 0; i < size; i++) {
        fprintf(stderr, "%0.2f ", buffer[i]);
    }
    fprintf(stderr, "\n");
}

void print_fragments(Coords **fragments, int fragcount)
{
    int f;
    Coords *p;

    for (f = 0; f < fragcount; f++) {
        fprintf(stderr, "frag%d: ", f);
        for (p = fragments[f]; p < fragments[f + 1]; p++) {
            fprintf(stderr, "(%d,%d), n=%d, val=%0.2f;", p->x, p->y,
                    p->neighbors, p->value);
        }
        fprintf(stderr, "\n");
    }
}

void print_map(double *map, int size)
{
    int x, y;

    fprintf(stderr, "map:\n");
    for (y = 0; y < size; y++) {
        for (x = 0; x < size; x++) {
            fprintf(stderr, "%0.0f ", map[x + y * size]);
        }
        fprintf(stderr, "\n");
    }
}
