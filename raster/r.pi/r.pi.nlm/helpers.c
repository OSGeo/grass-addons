#include "local_proto.h"

int Round(double d)
{
    return d < 0 ? d - 0.5 : d + 0.5;
}

int Random(int max)
{
    return max <=
	RAND_MAX ? rand() % max : floor((double)rand() /
					(double)(RAND_MAX + 1) * max);
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
		fprintf(stderr, " * ", TYPE_NOTHING);
		break;
	    case TYPE_NOGO:
		fprintf(stderr, " X ", TYPE_NOGO);
		break;
	    default:
		if (buffer[x + y * sx] < 0) {
		    fprintf(stderr, "%d ", buffer[x + y * sx]);
		}
		else {
		    fprintf(stderr, " %d ", buffer[x + y * sx]);
		}
		break;
	    }
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
