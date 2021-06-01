#include "local_proto.h"

/* globals */

int global_progress = 0;
int pickpos_count;
int perception_count;
WeightedCoords *pos_arr;
Displacement *displacements;
Displacement *perception;

/*
   output raster with current simulation state
 */
void test_output(int *map, int patch, int step, int n)
{
    int out_fd;
    int row, col, i;
    char outname[GNAME_MAX];
    DCELL *outmap = (DCELL *) G_malloc(sx * sy * sizeof(DCELL));

    /* open the new cellfile  */
    sprintf(outname, "%s_patch%d_step%d", newname, patch, step);

    out_fd = G_open_raster_new(outname, DCELL_TYPE);
    if (out_fd < 0) {
	G_fatal_error(_("can't create new cell file <%s> in mapset %s\n"),
		      outname, newmapset);
	exit(EXIT_FAILURE);
    }

    /* write map */

    for (i = 0; i < sx * sy; i++) {
	outmap[i] = 0;
    }

    for (i = 0; i < n; i++) {
	int x, y;
	Individual *indi = indi_array + i;

	x = indi->x;
	y = indi->y;

	//              fprintf(stderr, "indi%d: (%d, %d)\n", i, x, y);

	outmap[x + y * sx]++;
    }

    for (i = 0; i < sx * sy; i++) {
	if (map[i] != TYPE_NOTHING && outmap[i] == 0) {
	    outmap[i] = -1;
	}
    }

    /*      for(row = 0; row < sy; row++) {
       for(col = 0; col < sx; col++) {
       fprintf(stderr, "%0.0f", outmap[row * sx + col]);
       }
       fprintf(stderr, "\n");
       } */

    /* write output */
    for (row = 0; row < sy; row++) {
	G_put_d_raster_row(out_fd, outmap + row * sx);
    }

    /* close output */
    G_close_cell(out_fd);
    G_free(outmap);
}

/*
   sorts cells in a fragment, so that border cells come first
 */
int sort_frag(Coords * frag, int size)
{
    int i, j;
    Coords temp;

    i = 0;
    j = size - 1;

    while (i <= j) {
	while (frag[i].neighbors < 4 && i < size)
	    i++;
	while (frag[j].neighbors == 4 && j >= 0)
	    j--;

	if (i < j) {
	    temp = frag[i];
	    frag[i] = frag[j];
	    frag[j] = temp;
	}
    }

    /*      fprintf(stderr, "Sorted fragment: (%d, %d: %d)", frag->x, frag->y, frag->neighbors);
       for(j = 1; j < size; j++) {
       fprintf(stderr, " (%d, %d: %d)", frag[j].x, frag[j].y, frag[j].neighbors);
       }
       fprintf(stderr, "\n"); */

    return i;
}

/*
   picks a random direction pointing outwards a patch
 */
double pick_dir(int *map, Coords * frag)
{
    double dirs[4];
    int i;
    double pick;

    int x = frag->x;
    int y = frag->y;
    int count = 0;

    if (x >= sx || map[x + 1 + y * sx] == TYPE_NOTHING)
	dirs[count++] = 0.0;
    if (y <= 0 || map[x + (y + 1) * sx] == TYPE_NOTHING)
	dirs[count++] = 0.25;
    if (x <= 0 || map[x - 1 + y * sx] == TYPE_NOTHING)
	dirs[count++] = 0.5;
    if (y >= sy || map[x + (y - 1) * sx] == TYPE_NOTHING)
	dirs[count++] = 0.75;

    //      G_message("Picks for (%d, %d): %0.2f, %0.2f, %0.2f, %0.2f, cnt=%d", x, y, dirs[0], dirs[1], dirs[2], dirs[3], count);

    pick = count * Randomf();

    for (i = count - 1; i >= 0; i--) {
	if (pick > i) {
	    double res = 0.25 * (pick - i) + dirs[i] - 0.125;

	    if (res < 0) {
		res++;
	    }
	    //                      res = res < 0 ? 2 * M_PI + res : res;
	    //                      G_message("dir = %0.2f", res);
	    return res;
	}
    }

    return -1;			// error
}

/*
   initializes all individuals for a fragment
 */
void init_individuals(int *map, Coords * frag, int size, int n)
{
    int i, border_count, index;
    Coords *cell;

    border_count = sort_frag(frag, size);

    //      G_message("Initializing");

    for (i = 0; i < n; i++) {
	//              G_message("border_count = %d", border_count);

	/* pick border cell */
	index = Random(border_count);
	cell = frag + index;

	indi_array[i].x = cell->x + 0.5;
	indi_array[i].y = cell->y + 0.5;
	indi_array[i].dir = pick_dir(map, cell);	//2 * M_PI * Randomf();
	indi_array[i].path = 0;
	indi_array[i].finished = 0;

	//              fprintf(stderr, "indi%d: ", i);
	//              fprintf(stderr, "x=%0.2f, y=%0.2f, dir=%0.2f, finished=%d\n",
	//                              indi_array[i].x, indi_array[i].y, indi_array[i].dir, indi_array[i].finished);
    }
    //      G_message("End initialization");
}

/*
   sets back an individual, when position is illegal
 */
void set_back(int *map, int indi, int frag)
{
    int index;
    Coords *cell;
    int border_count =
	sort_frag(fragments[frag], fragments[frag + 1] - fragments[frag]);

    /* pick border cell */
    index = Random(border_count);
    cell = fragments[frag] + index;

    indi_array[indi].x = cell->x;
    indi_array[indi].y = cell->y;
    indi_array[indi].dir = pick_dir(map, cell);
    indi_array[indi].finished = 0;
}

/*
   sets displacement pixels taking advantage of symmetry
 */
void set_pixels(Displacement * values, int x, int y, int r)
{
    if (y == 0) {
	values[0].x = x;
	values[0].y = 0;
	values[2 * r].x = 0;
	values[2 * r].y = x;
	values[4 * r].x = -x;
	values[4 * r].y = 0;
	values[6 * r].x = 0;
	values[6 * r].y = -x;
    }
    else if (y == x) {
	values[r].x = y;
	values[r].y = y;
	values[3 * r].x = -y;
	values[3 * r].y = y;
	values[5 * r].x = -y;
	values[5 * r].y = -y;
	values[7 * r].x = y;
	values[7 * r].y = -y;
    }
    else if (y < x) {
	values[r - x + y].x = x;
	values[r - x + y].y = y;
	values[r + x - y].x = y;
	values[r + x - y].y = x;
	values[3 * r - x + y].x = -y;
	values[3 * r - x + y].y = x;
	values[3 * r + x - y].x = -x;
	values[3 * r + x - y].y = y;
	values[5 * r - x + y].x = -x;
	values[5 * r - x + y].y = -y;
	values[5 * r + x - y].x = -y;
	values[5 * r + x - y].y = -x;
	values[7 * r - x + y].x = y;
	values[7 * r - x + y].y = -x;
	values[7 * r + x - y].x = x;
	values[7 * r + x - y].y = -y;
    }
}

/*
   calculates displacements for a circle of given radius
 */
void calculate_displacement(Displacement * values, int radius)
{
    int dx = radius;
    int dy = 0;
    float dx_ = (float)dx - 0.5f;
    float dy_ = (float)dy + 0.5f;
    float f = 0.5f - (float)radius;

    set_pixels(values, dx, dy, radius);

    while (dx > dy) {
	if (f < 0) {
	    f += 2 * dy_ + 1;
	    dy_++;
	    dy++;
	}
	else {
	    f += 1 - 2 * dx_;
	    dx_--;
	    dx--;
	}

	set_pixels(values, dx, dy, radius);
    }
}

/*
   fills a weighted array with possible next positions
 */
void pick_nextpos(WeightedCoords * result, int indi, int *map,
		  DCELL * costmap, int frag)
{
    int i;
    double ex_step, ex_pos;
    Individual *individual = indi_array + indi;
    int actx = individual->x;
    int acty = individual->y;
    int dir_index = Round(individual->dir * 8.0 * (double)step_length);
    int pos = dir_index - 2 * step_length;

    if (pos < 0) {
	pos += 8 * step_length;
    }

    for (i = 0; i < pickpos_count; i++, pos++) {
	result[i].x = actx + displacements[pos].x;
	result[i].y = acty + displacements[pos].y;
	result[i].dir = (double)pos / (8.0 * (double)step_length);
	if (result[i].dir >= 1) {
	    result[i].dir--;
	}

	/* if out of limits, use weight=1 until better handling */
	if (actx < 0 || actx >= sx || acty < 0 || acty >= sy) {
	    result[i].weight = 1;
	}
	else {
	    /* get weight from costmap */
	    result[i].weight = costmap[(int)acty * sx + (int)actx];
	}
    }

    /* apply perception multiplicator */
    dir_index = Round(individual->dir * 8.0 * (double)perception_range);
    pos = dir_index - 2 * perception_range;
    ex_step = (double)perception_range / (double)step_length;
    ex_pos = (double)pos;
    for (i = 0; i < pickpos_count; i++) {
	int patch_flag = 0;

	ex_pos += ex_step;
	while (pos < ex_pos) {
	    int x = actx + perception[pos].x;
	    int y = acty + perception[pos].y;

	    if (x >= 0 && x < sx && y >= 0 && y < sy) {
		int val = map[x + y * sx];

		patch_flag |= (val > TYPE_NOTHING && val != frag &&
			       !deleted_arr[val]);
	    }
	    pos++;
	}

	if (patch_flag) {
	    result[i].weight *= multiplicator;

	}
    }

    return;
}

/*
   performs a single step for an individual
 */
void indi_step(int indi, int frag, int *map, DCELL * costmap, double step)
{
    int i;
    double sum;
    Individual *individual = indi_array + indi;
    double rnd;
    double newx, newy, newdir;
    int act_cell;

    /* test output */
    //      fprintf(stderr, "actpos: x = %0.2f, y = %0.2f\n", individual->x, individual->y);

    /* write an array with possible next positions */
    pick_nextpos(pos_arr, indi, map, costmap, frag);

    /* test output */
    /*      G_message("Nextpos array:\n");
       for(i = 0; i < pickpos_count; i++) {
       fprintf(stderr, "(x=%d,y=%d,dir=%0.2f,weight=%0.2f)\n", 
       pos_arr[i].x, pos_arr[i].y, pos_arr[i].dir, pos_arr[i].weight);
       } */

    /* if no next position is possible, then set back */
    sum = 0;
    for (i = 0; i < pickpos_count; i++) {
	sum += pos_arr[i].weight;
    }
    if (sum == 0) {
	set_back(map, indi, frag);

	return;
    }

    /* pick a next position randomly, considering the weights */
    pos_arr[0].weight = pos_arr[0].weight / sum;
    for (i = 1; i < pickpos_count; i++) {
	pos_arr[i].weight = pos_arr[i - 1].weight + pos_arr[i].weight / sum;
    }
    rnd = Randomf();
    for (i = 0; i < pickpos_count; i++) {
	if (pos_arr[i].weight > rnd)
	    break;
    }
    newx = pos_arr[i].x;
    newy = pos_arr[i].y;
    newdir = pos_arr[i].dir;

    /* test output */
    //      fprintf(stderr, "pick: x = %0.2f, y = %0.2f\n\n", newx, newy);

    /* if new position is out of limits, then set back */
    if (newx < 0 || newx >= sx || newy < 0 || newy >= sy) {
	set_back(map, indi, frag);

	return;
    }

    /* set new position */
    individual->x = newx;
    individual->y = newy;

    /* count path of the individuum */
    if (include_cost) {
	individual->path += 100 / costmap[(int)newy * sx + (int)newx];
    }
    else {
	individual->path++;
    }
    individual->dir = newdir;

    /* if new position is an other patch and patch is not deleted, then set finished = true */
    act_cell = map[(int)newy * sx + (int)newx];
    if (act_cell > -1 && act_cell != frag && !deleted_arr[act_cell]) {
	/* count patch immigrants for this patch */
	patch_imi[act_cell]++;
	individual->finished = 1;
    }

    return;
}

/*
   performs a search run for a single fragment
 */
DCELL frag_run(int *map, DCELL * costmap, int frag)
{
    int i;
    DCELL res = 0;
    int step_cnt = 0;
    int finished_cnt = 0;
    int limit = ceil(n * percent / 100);

    //      fprintf(stderr, "\nstarting run:\n");
    //      fprintf(stderr, "limit = %d\n", limit); 

    init_individuals(map, fragments[frag],
		     fragments[frag + 1] - fragments[frag], n);

    /* perform a step for each individual */
    finished_cnt = 0;
    while (finished_cnt < limit && step_cnt <= maxsteps) {
	if (out_freq > 0 && (step_cnt % out_freq == 0)) {
	    test_output(map, frag, step_cnt, n);
	}

	for (i = 0; i < n; i++) {
	    if (!indi_array[i].finished) {
		indi_step(i, frag, map, costmap, step_length);

		/* test if new individuum finished */
		if (indi_array[i].finished) {
		    finished_cnt++;

		    global_progress++;
		    G_percent(global_progress,
			      (fragcount + 1) * fragcount * limit, 1);

		    if (finished_cnt >= limit)
			break;
		}
	    }
	}

	step_cnt++;
    }

    if (out_freq > 0 && (step_cnt % out_freq == 0)) {
	test_output(map, frag, step_cnt, n);
    }

    //      fprintf(stderr, "stepcnt = %d\n", step_cnt);
    return (DCELL) step_cnt;
}

/*
   performs a search run for each fragment

   output in "values": ( stat1(patch1, patch2, patch3, ...), stat2(patch1, patch2, ...) )
 */
void perform_search(DCELL * values, int *map, DCELL * costmap,
		    f_statmethod **stats, int stat_count)
{
    int fragment, i;
    int steps;
    f_statmethod *func;

    /* allocate paths array */
    DCELL *indi_paths = (DCELL *) G_malloc(n * sizeof(DCELL));

    /* allocate individuals array */
    indi_array = (Individual *) G_malloc(n * sizeof(Individual));

    /* allocate pickpos result array */
    pickpos_count = 4 * step_length + 1;
    pos_arr =
	(WeightedCoords *) G_malloc(pickpos_count * sizeof(WeightedCoords));

    /* allocate displacement arrays */
    displacements =
	(Displacement *) G_malloc(16 * step_length * sizeof(Displacement));
    perception =
	(Displacement *) G_malloc(16 * perception_range *
				  sizeof(Displacement));

    /* calculate displacements */
    calculate_displacement(displacements, step_length);
    memcpy(displacements + 8 * step_length, displacements,
	   8 * step_length * sizeof(Displacement));

    calculate_displacement(perception, perception_range);
    memcpy(perception + 8 * perception_range, perception,
	   8 * perception_range * sizeof(Displacement));

    /*      fprintf(stderr, "Displacements:");
       for(i = 0; i < pickpos_count; i++) {
       fprintf(stderr, " (%d, %d)", displacements[i].x, displacements[i].y);
       } */

    /* initialize patch imigrants array */
    memset(patch_imi, 0, fragcount * sizeof(int));

    /* perform a search run for each fragment */
    for (fragment = 0; fragment < fragcount; fragment++) {
	steps = frag_run(map, costmap, fragment);

	for (i = 0; i < n; i++) {
	    indi_paths[i] = indi_array[i].path;
	}

	for (i = 0; i < stat_count; i++) {
	    func = stats[i];
	    values[i * fragcount + fragment] = func(indi_paths, n);
	}
    }

    /*G_message("Values");
       for(i = 0; i < fragcount * stat_count; i++) {
       fprintf(stderr, "%0.2f ", values[i]);
       }
       G_message(""); */

    G_free(indi_paths);
    G_free(indi_array);
    G_free(pos_arr);
    G_free(displacements);
}
