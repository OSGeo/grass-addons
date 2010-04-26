#include "local_proto.h"

int get_nsets(FILE * fd, fpos_t position)
{

    int nsets = 0;

    fsetpos(fd, &position);
    char buf[500];

    fgetpos(fd, &position);


    while (fgets(buf, sizeof buf, fd)) {
	G_strip(buf);

	if (*buf == '#' || *buf == 0 || *buf == '\n')
	    continue;

	if (*buf == '$')
	    nsets++;

	if (*buf == '%')
	    break;
    }
    fsetpos(fd, &position);
    return nsets;
}


int char_strip(char *buf, char rem)
{
    register char *a, *b;

    for (a = b = buf; *a == rem || *a == ' ' || *a == '\t'; a++) ;
    if (a != b)
	while ((*b++ = *a++)) ;

    return 0;
}

int char_copy(const char *buf, char *res, int start, int stop)
{
    register int i, j;

    for (i = start, j = 0; i < stop; res[j++] = buf[i++]) ;
    res[j] = '\0';

    return 0;
}


int get_universe(void)
{
    int i, j;
    float min = 100000000., max = 0;

    resolution += 1;

    for (i = 0; i < nmaps; ++i) {
	if (s_maps[i].output)
	    break;
    }
    output_index = i;

    for (j = 0; j < s_maps[i].nsets; ++j) {

	min = (s_maps[i].sets[j].points[0] < min) ?
	    s_maps[i].sets[j].points[0] : min;

	if (s_maps[i].sets[j].side)
	    max = (s_maps[i].sets[j].points[1] > max) ?
		s_maps[i].sets[j].points[1] : max;
	else
	    max = (s_maps[i].sets[j].points[3] > max) ?
		s_maps[i].sets[j].points[3] : max;
    }


    universe = (float *)G_calloc(resolution, sizeof(float));
    for (i = 0; i < resolution; ++i)
	universe[i] = min + ((max - min) / resolution) * i;

    return 0;
}

void process_coors(char *answer)
{

    struct Cell_head window;
    double x, y;
    int i, j;
    int r, c;
    int num_points;
    float result;

    G_get_window(&window);
    num_points = sscanf(answer, "%lf,%lf", &x, &y);

    r = (int)G_easting_to_col(x, &window);
    c = (int)G_northing_to_row(y, &window);
    
		get_rows(r);
    get_cells(c);
    result = implicate(); /* jump to different function */

    for (i = 0; i < nrules; ++i)
	fprintf(stdout, "ANTECEDENT %s: %5.3f\n", s_rules[i].outname,
		antecedents[i]);

  fprintf(stdout, "RESULT (deffuzified):  %5.3f\n", result);
  
  fprintf(stdout, "UNIVERSE,");
    for (i = 0; i < nrules; ++i)
	fprintf(stdout, "%s,", s_rules[i].outname);
    fprintf(stdout, "AGREGATE \n");

    for (i = 0; i < resolution; ++i)
	for (j = 0; j < nrules + 2; ++j) {
	    fprintf(stdout, "%5.3f", visual_output[i][j]);
	    if (j < nrules + 1)
		fprintf(stdout, ",");
	    else
		fprintf(stdout, "\n");
	}

			for (i = 0; i < nmaps; ++i) {
	G_free(s_maps[i].sets);
	if (s_maps[i].output)
	    continue;
		G_free(s_maps[i].in_buf);
	G_close_cell(s_maps[i].cfd);
    }

    G_free(antecedents);
    G_free(s_maps);
    G_free(s_rules);
   
    exit(EXIT_SUCCESS);
}


void show_membership(void) {
	int i,j,k;
	STRING cur_mapset;
	struct FPRange map_range;
	DCELL min, max;
	float* map_universe;
	
	resolution=resolution+1;
	map_universe = (float *)G_calloc(resolution, sizeof(float));

	for(i=0;i<nmaps;++i) {
		
		if(s_maps[i].output)
			continue;
		G_init_fp_range(&map_range);
		cur_mapset = G_find_cell2(s_maps[i].name, "");
		G_read_fp_range(s_maps[i].name,cur_mapset,&map_range);
		G_get_fp_range_min_max(&map_range,&min, &max);
		
			for (k = 0; k < resolution; ++k)
		map_universe[k] = min + ((max - min) / resolution) * k;
		
		fprintf(stdout,"#MAP: %s \n",s_maps[i].name);
		
		fprintf(stdout,"value,");
			for(j=0;j<s_maps[i].nsets;++j) {
		fprintf(stdout,"%s",s_maps[i].sets[j].setname);
				if (j < s_maps[i].nsets-1)
			fprintf(stdout, ",");
				else
			fprintf(stdout, "\n");
			}
			
			for(k=0;k<resolution;++k) { 
				fprintf(stdout,"%5.3f,",map_universe[k]);
				for(j=0;j<s_maps[i].nsets;++j) {
					fprintf(stdout,"%5.3f",
					fuzzy(map_universe[k],&s_maps[i].sets[j]));
						if (j < s_maps[i].nsets-1)
							fprintf(stdout, ",");
						else
							fprintf(stdout, "\n");
				}
			}
	}

	G_free(map_universe);

    for (i = 0; i < nmaps; ++i)
	G_free(s_maps[i].sets);

    G_free(s_maps);
    G_free(s_rules);

		exit(EXIT_SUCCESS);
	
}
