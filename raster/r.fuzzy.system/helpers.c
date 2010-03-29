#include "local_proto.h"

int get_nsets(FILE* fd, fpos_t position) {
	
	int nsets=0;
	fsetpos (fd, &position);
	char buf[500];

	fgetpos (fd, &position);

	
	while (fgets(buf, sizeof buf, fd)) {
			G_strip(buf);

			if (*buf == '#' || *buf == 0 || *buf=='\n')
		continue;	
		
			if (*buf == '$')
		nsets++;
	
			if (*buf == '%')
		break;	
	}
	fsetpos (fd, &position);	
	return nsets;	
}


int char_strip(char *buf, char rem)
{
	register char *a, *b;
		for (a = b = buf; *a == rem || *a == ' ' || *a == ' \t'; a++) ;
			if (a != b)
	while ((*b++ = *a++)) ;
     
  return 0;
}

int char_copy(const char *buf, char *res, int start, int stop)
{
	register int i,j;
		for(i=start,j=0;i<stop;res[j++] = buf[i++]);
			res[j]='\0';

  return 0;
}


int get_universe (void) {
	int i,j;
	float min=100000000., max=0;

	resolution +=1;
	
			for (i=0;i<nmaps;++i) {
		if (s_maps[i].output)
			break;
		}
	output_index=i;	
		
		for (j=0;j<s_maps[i].nsets;++j) {
	
	min = (s_maps[i].sets[j].points[0]<min) ? 
		s_maps[i].sets[j].points[0] : min;
	
		if (s_maps[i].sets[j].side)
	max = (s_maps[i].sets[j].points[1]>max) ? 
		s_maps[i].sets[j].points[1] : max;	
		else
	max = (s_maps[i].sets[j].points[3]>max) ? 
	s_maps[i].sets[j].points[3] : max;		
		}
 
	 
	 	universe =(float*) G_calloc(resolution, sizeof(float));
		for (i=0;i<resolution;++i)
	universe[i]= min + ((max-min)/resolution) * i;

	return 0; 
}

