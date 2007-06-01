#include <grass/gis.h>
#include "global.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>



int main(argc,argv)
int argc;
char *argv[];
{
  struct Option *opt1;
  struct Option *opt2;
  struct Option *opt3;
  struct Option *opt4;
  struct Option *opt5;
  char tempbuf[500];
  char *mapset;
  struct Cell_head cellhd;
  double **matrix ;
  DCELL *rowbuf;
  DCELL *tf;
  int fd;
  double minv,maxv;
  int minp,maxp;
  int i,j;
  Blob *blobs;
  int nblobs,npoints;
  BlobSites *sites;



  char gisrc[500];
  
  if(getenv("GISBASE")==NULL)
      setenv("GISBASE",
	     "/mpa_sw/ssi/BIO/software/GRASS5.0.0/grass5bin_cvs/grass5",1);
  if(getenv("GISRC")==NULL){
    sprintf(gisrc,"/ssi0/ssi/%s/.grassrc5",getenv("LOGNAME"));
    setenv("GISRC",gisrc,1);
  }
  
  /* Define the different options */

  opt1              = G_define_option();
  opt1->key         = "input_map";
  opt1->type        = TYPE_STRING;
  opt1->required    = YES;
  opt1->gisprompt   = "old,cell,raster" ;
  opt1->description = "Input raster map for searching for blobs.";

  opt2 = G_define_option() ;
  opt2->key        = "min_pixels";
  opt2->type       = TYPE_INTEGER;
  opt2->required   = YES;
  opt2->description= "minimum number of pixels defining a blob";

  opt3              = G_define_option();
  opt3->key         = "max_pixels";
  opt3->type        = TYPE_INTEGER;
  opt3->required    = YES;
  opt3->description = "maximum number of pixels defining a blob";

  opt4              = G_define_option();
  opt4->key         = "min_value";
  opt4->type        = TYPE_DOUBLE;
  opt4->required    = YES;
  opt4->description = "minimum value of the map for defining a blob";

  opt5              = G_define_option();
  opt5->key         = "max_value";
  opt5->type        = TYPE_DOUBLE;
  opt5->required    = YES;
  opt5->description = "maximum value of the map for defining a blob\n\n\tThe output is a site file, BUT it will be printed to standard output.";

  /***** Start of main *****/
  G_gisinit(argv[0]);

  if (G_parser(argc, argv) < 0)
    exit(-1);

  sscanf(opt2->answer,"%d",&minp);
  sscanf(opt3->answer,"%d",&maxp);
  sscanf(opt4->answer,"%lf",&minv);
  sscanf(opt5->answer,"%lf",&maxv);


  if((mapset = G_find_cell2(opt1->answer, "")) == NULL){
    sprintf(tempbuf,"can't open raster map <%s> for reading",opt1->answer);
    G_fatal_error(tempbuf);
  }

  if((fd = G_open_cell_old(opt1->answer, mapset)) < 0){
    sprintf(tempbuf,"error opening raster map <%s>", opt1->answer);
    G_fatal_error(tempbuf);
  }

  G_get_window (&cellhd);

  rowbuf = (DCELL *)G_calloc(cellhd.cols * cellhd.rows,sizeof(DCELL));
  tf=rowbuf;
  matrix = (double **) G_calloc(cellhd.rows,sizeof(double *));
  for(i=0;i<cellhd.rows;i++)
    matrix[i] = (double *) G_calloc(cellhd.cols,sizeof(double));

  for(i = 0; i < cellhd.rows; i++){
    G_get_d_raster_row(fd, tf, i);
    for(j = 0; j < cellhd.cols; j++){
      if (G_is_d_null_value (tf)) 
        *tf = maxv+1.0;
      matrix[i][j] = *tf;
      tf++;
    }
  }
  G_close_cell(fd);

  nblobs=0;
  npoints=0;
  find_blob(matrix,cellhd.rows,cellhd.cols,&blobs,&npoints,&nblobs,minv,maxv);
  sites=(BlobSites *)calloc(nblobs,sizeof(BlobSites));

  extract_sites_from_blob(blobs,npoints,nblobs,&cellhd,sites,matrix);

  for(i=0;i<nblobs;i++)
    if((sites[i].n>=minp) && (sites[i].n<=maxp))
      fprintf(stdout,"%f|%f|#%d%s%f\n",sites[i].east,sites[i].north,
	      sites[i].n, "%",sites[i].min);
  

  return 0;
}
