#include "local_proto.h"

void variogram_type(int code, char *type)
{
  switch (code) {
  case 0:
    strcpy(type, "horizontal");
    break;
  case 1:
    strcpy(type, "vertical");
    break;
  case 2:
    strcpy(type, "bivariate");
    break;
  case 3:
    strcpy(type, "anisotropic");
    break;
  }
}

void write2file_basics(struct int_par *xD, struct opts *opt)
{
  struct write *report = &xD->report;

  fprintf(report->fp, "************************************************\n");
  fprintf(report->fp, "*** Input ***\n\n");
  fprintf(report->fp, "- vector layer: %s\n", opt->input->answer);
  switch (xD->v3) {
  case TRUE:
    fprintf(report->fp, "- is 3D: yes\n");
    break;
  case FALSE:
    fprintf(report->fp, "- is 3D: no\n");
    break;
  }
  // todo: move to end
  fprintf(report->fp, "\n");
  fprintf(report->fp, "*** Output *** \n\n");
  switch (xD->i3) {
  case FALSE:
    fprintf(report->fp, "- raster layer: %s\n", opt->output->answer);
    fprintf(report->fp, "- is 3D: no\n");
    break;
  case TRUE:
    fprintf(report->fp, "- volume layer: %s\n", opt->output->answer);
    fprintf(report->fp, "- is 3D: yes\n");
    break;
  }    
}

void write2file_vector( struct int_par *xD, struct points *pnts)
{
  struct select in_reg = pnts->in_reg;
  struct write *report = &xD->report;
  fprintf(report->fp, "\n");
  fprintf(report->fp, "************************************************\n");
  fprintf(report->fp, "*** Input vector layer properties ***\n\n");
  fprintf(report->fp, "# of points (total): %d\n", in_reg.total);
  fprintf(report->fp, "# of points (in region): %d\n", in_reg.n);
  fprintf(report->fp, "# of points (out of region): %d\n\n", in_reg.out);
  fprintf(report->fp, "- extent:\n");
  switch (xD->i3) {
  case TRUE:
    fprintf(report->fp, "xmin=%f   ymin=%f   zmin=%f\n", pnts->r_min[0], pnts->r_min[1], pnts->r_min[2]);
    fprintf(report->fp, "xmax=%f   ymax=%f   zmax=%f\n", pnts->r_max[0], pnts->r_max[1], pnts->r_max[2]);
    break;
  case FALSE:
    fprintf(report->fp, "xmin=%f   ymin=%f\n", pnts->r_min[0], pnts->r_min[1]);
    fprintf(report->fp, "xmax=%f   ymax=%f\n", pnts->r_max[0], pnts->r_max[1]);
    break;
  }
}

void write2file_values(struct write *report, const char *column)
{
  fprintf(report->fp, "\n");
  fprintf(report->fp, "************************************************\n");
  fprintf(report->fp, "*** Values to be interpolated ***\n\n");
  fprintf(report->fp, "- attribute column: %s\n", column); 
}

void write2file_varSetsIntro(int code, struct write *report)
{
  char type[12];
  variogram_type(code, type);

  fprintf(report->fp, "\n************************************************\n");
  fprintf(report->fp, "*** Variogram settings - %s ***\n\n", type); 
}

void write2file_varSets(struct write *report, struct parameters *var_par)
{
  char type[12];
  variogram_type(var_par->type, type);

  fprintf(report->fp, "- number of lags in %s direction: %d\n", type, var_par->nLag);
  fprintf(report->fp, "- lag distance (%s): %f\n", type, var_par->lag);

  if (var_par->function == 5) {
    fprintf(report->fp, "- number of lags in vertical direction: %d\n", var_par->nLag_vert);
    fprintf(report->fp, "- lag distance (vertical): %f\n", var_par->lag);
  }  

  fprintf(report->fp, "- azimuth: %f°\n", RAD2DEG(var_par->dir));
  fprintf(report->fp, "- angular tolerance: %f°\n", RAD2DEG(var_par->td));
  //fprintf(report->fp, "- variogram plotted: %s\n", );
    
  switch (var_par->function) {
  case 5:
    fprintf(report->fp, "- maximum distance in horizontal direction (1/3): %f\n", var_par->max_dist);
    break;
  default:
    fprintf(report->fp, "- maximum distance (1/3): %f\n", var_par->max_dist);
    break;
  }
}

void write2file_variogram_E(struct int_par *xD, struct parameters *var_par)
{
  int i, j;
  int fction = var_par->function;
  double *h, *vert;
  double *c = var_par->c->vals;
  double *gamma = var_par->gamma->vals;
  struct write *report = &xD->report;

  char type[12];
  variogram_type(var_par->type, type);

  fprintf(report->fp, "\n************************************************\n");
  fprintf(report->fp, "*** Experimental variogram - %s ***\n\n", type);
  
  if (fction == 5) { // if variogram is bivariate
    vert = &var_par->vert[0]; // use vertical variable
    for (i=0; i<var_par->nLag_vert; i++) { // write header - verts
      if (i == 0)
	fprintf(report->fp, "  lagV  ||"); // column for h
      fprintf(report->fp, " %f ||", *vert);
      //fprintf(report->fp, " # of pairs | average ||");
      //fprintf(report->fp, "------------------------");
      vert++;
    }
    fprintf(report->fp, "\n");

    for (i=0; i<var_par->nLag_vert; i++) { // write header - h c gamma
      if (i == 0)
	fprintf(report->fp, "  lagHZ ||"); // column for h
      fprintf(report->fp, " c | ave ||", *vert);
    }
    fprintf(report->fp, "\n");

    for (i=0; i<var_par->nLag_vert; i++) { // write header - h c gamma
      if (i == 0)
	fprintf(report->fp, "--------||"); // column for h
      fprintf(report->fp, "-----------", *vert);
    }
    fprintf(report->fp, "\n");
  }
  else {
    fprintf(report->fp, " lag ||  # of pairs | average\n");
    fprintf(report->fp, "------------------------------------\n");
  }

  // Write values
  h = &var_par->h[0];
  for (i=0; i<var_par->nLag; i++) {
    fprintf(report->fp, "%f ||", *h);
    if (fction == 5) {
      //for (j=0; j<var_par->nZ; j++) {
	fprintf(report->fp, " %d | %f ||", (int) *c, *gamma);	  
	c++;
	gamma++;
	//} // end for j
      fprintf(report->fp, "\n");
      //for (j=0; j<var_par->nZ; j++)
	fprintf(report->fp, "-----------", (int) *c, *gamma);	  
      fprintf(report->fp, "\n");
    }
    else {
      fprintf(report->fp, " %d | %f\n", (int) *c, *gamma);
      c++;
      gamma++;
    }
    h++;
  }
  fprintf(report->fp, "------------------------------------\n");
}

void write2file_variogram_T(struct write *report)
{
  fprintf(report->fp, "\n");
  fprintf(report->fp, "************************************************\n");
  fprintf(report->fp, "*** Theoretical variogram ***\n\n");
}

void write_temporary2file(struct int_par *xD, struct parameters *var_par, mat_struct *gammaMT)
{
  // local variables
  int type = var_par->type;
  int nLag = var_par->nLag;
  int nLag_vert;
  double *h = var_par->h;
  double *vert;
  double *c = var_par->c->vals;
  double *gamma = gammaMT->vals;
  double sill = var_par->sill;

  int i, j; // index
  FILE *fp;
  int file_length;
  
  switch (type) {
  case 0: // horizontal variogram
    fp = fopen("variogram_hz_tmp.txt", "w");
    if (xD->report.name) { // write name of report file
      file_length = strlen(xD->report.name);
      if (file_length < 4) // 4 types of variogram
	G_fatal_error(_("File name must contain more than 2 characters...")); // todo: error
      fprintf(fp, "%d 9 %s\n", file_length, xD->report.name);
    }
    fprintf(fp,"%d\n", var_par->type); // write # of lags
    break;
  case 1: // vertical variogram
    fp = fopen("variogram_vert_tmp.txt", "w");
    if (xD->report.name) { // write name of report file
      file_length = strlen(xD->report.name);
      if (file_length < 3)
	G_fatal_error(_("File name must contain more than 2 characters...")); // todo: error
      fprintf(fp, "%d 9 %s\n", file_length, xD->report.name);
    }
    fprintf(fp,"%d\n", var_par->type); // write type
    break;
  case 2:
    fp = fopen("variogram_final_tmp.txt", "w");
    if (xD->report.name) { // write name of report file
      file_length = strlen(xD->report.name);
      if (file_length < 4) // 4 types of variogram
	G_fatal_error(_("File name must contain more than 2 characters...")); // todo: error
      fprintf(fp, "%d 9 %s\n", file_length, xD->report.name);
    }

    fprintf(fp,"%d\n", var_par->type); // write # of lags
    fprintf(fp,"%d\n", var_par->nLag_vert); // write # of lags
    fprintf(fp,"%f\n", var_par->lag_vert);  // write size of lag
    fprintf(fp,"%f\n", var_par->max_dist_vert); // write maximum distance
    break;
  case 3: // anisotropic variogram
    fp = fopen("variogram_final_tmp.txt", "w");
    if (xD->report.name) { // write name of report file
      file_length = strlen(xD->report.name);
      if (file_length < 4) // 4 types of variogram
	G_fatal_error(_("File name must contain more than 4 characters...")); // todo: error
      fprintf(fp, "%d 9 %s\n", file_length, xD->report.name);
    }
    fprintf(fp,"%d\n", var_par->type); // write type
    fprintf(fp,"%f\n", xD->aniso_ratio); // write ratio of anisotropy 
    break;
  }
  
  fprintf(fp,"%d\n", nLag); // write # of lags
  fprintf(fp,"%f\n", var_par->lag);  // write size of lag
  fprintf(fp,"%f\n", var_par->max_dist); // write maximum distance
  if (type != 1)
    fprintf(fp,"%f\n", var_par->td); // write maximum distance

  switch (type) {
  case 2:
    nLag_vert = var_par->nLag_vert;
    // write h
    for (i=0; i<nLag; i++) { // write experimental variogram
      fprintf(fp,"%f\n", *h);
      h++;
    }
    // write vert
    vert = &var_par->vert[0];
    for (i=0; i<nLag_vert; i++) { // write experimental variogram
      fprintf(fp,"%f\n", *vert);
      vert++;
    }
    // write c
    for (i=0; i<nLag * nLag_vert; i++) { // write experimental variogram
      fprintf(fp,"%f\n", *c);
      c++;
    }
    // write gamma
    for (i=0; i<nLag * nLag_vert; i++) { // write experimental variogram
      fprintf(fp,"%f\n", *gamma);
      gamma++;
    }
    fprintf(fp,"%f\n", var_par->horizontal.sill);// write sill
    fprintf(fp,"%f\n", var_par->vertical.sill);// write sill
    break;
  default:
    for (i=0; i<nLag; i++) { // write experimental variogram
      fprintf(fp,"%f %f %f\n", *h, *c, *gamma);
      h++;
      c++;
      gamma++;
    }
    fprintf(fp,"%f", sill);// write sill
    break;
  }

  fclose(fp);
}
