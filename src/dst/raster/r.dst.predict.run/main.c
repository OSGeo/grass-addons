/* dst.predict */
/* Part of the GRASS Dempster-Shafer Predictive Modelling Toolkit (DST-PMT) */

/* Purpose:  A wrapper program to provide a straight-forward GUI for predictive
        modelling using r.dst.bpa and dst.combine modules.

	This file is licensed under the GPL (version 2 or later at your option)
 	see: http://www.gnu.org/copyleft/gpl.html* /

 	(c) Benjamin Ducke 2006
	benducke@compuserve.de

*/



#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>

#include <grass/gis.h>

#define PROGVERSION 1.5

char *PROG_BPA = "r.dst.bpn";
char *PROG_CREATE = "m.dst.create";
char *PROG_UPDATE = "m.dst.update";
char *PROG_SOURCE = "m.dst.source";
char *PROG_COMBINE = "m.dst.combine";
char *PROG_REMOVE = "g.remove";

int SCRIPTING = 0;
FILE *SCRIPT;

/* executes a GRASS module */
void exec_module (char* module, char *arguments) {

	int error = 0;
	char sysstr [2048]; 
	
	if ( getenv("GISBASE") == NULL ) {
		G_fatal_error ("GISBASE not set. Unable to call GRASS modules.");
	}	
	
	G_strcpy (sysstr, getenv("GISBASE"));
	G_strcat (sysstr, "/bin/");
	G_strcat (sysstr, module);
	G_strcat (sysstr, " ");
	G_strcat (sysstr, arguments);
	
	if ( SCRIPTING ) {
		fprintf ( SCRIPT, "%s\n", sysstr );
	} else {		
		error = system (sysstr);
		if ( error != 0 ) {
			G_fatal_error ("Module '%s' terminated with an error.", module);
		}
	}
	
}


int
main (int argc, char *argv[])
{
	struct GModule *module;
	struct
	{
		struct Option *input;
		struct Option *sites;
		struct Option *vals;
		struct Option *s_bias_atts;
		struct Option *n_bias_maps;
		struct Option *output;			
		struct Option *logfile;
		struct Option *script;
		struct Option *cachesize;
	}
	parm;
	
	struct
	{
		struct Flag *quiet;
		struct Flag *remove;
	}
	flag;
	
	char *sysstr;
	char *biasmaps;
	int i, num_evidences;
	
	/* setup some basic GIS stuff */
	G_gisinit (argv[0]);
	module = G_define_module ();
	module->description = "Dempster-Shafer Theory predictive modelling";
	/* do not pause after a warning message was displayed */
	G_sleep_on_error (0);

	/* Parameters: */
	/* input = a map that shows the natural (complete) distribution */
	/* of a feature. */
	parm.input = G_define_standard_option (G_OPT_R_INPUT);
	parm.input->key = "raster";
	parm.input->type = TYPE_STRING;
	parm.input->required = YES;
	parm.input->multiple = YES;
	parm.input->gisprompt = "old,cell,raster";
	parm.input->description = "Raster evidence map(s)";

	/* site map with known sites */
	parm.sites = G_define_standard_option (G_OPT_V_INPUT);
	parm.sites->key = "sites";
	parm.sites->type = TYPE_STRING;
	parm.sites->required = YES;
	parm.sites->description = "Vector map with site points";
		
	parm.vals = G_define_option ();
	parm.vals->key = "values";
	parm.vals->type = TYPE_STRING;
	parm.vals->required = NO;
	parm.vals->multiple = YES;
	parm.vals->options = "bel,pl,doubt,common,bint,woc,maxbpa,minbpa,maxsrc,minsrc";
	parm.vals->answer = "bel";
	parm.vals->description = "Dempster-Shafer values to map";		

	parm.n_bias_maps = G_define_standard_option (G_OPT_R_INPUT);
	parm.n_bias_maps->key = "nbias";
	parm.n_bias_maps->required  = NO;
	parm.n_bias_maps->multiple = YES;
	parm.n_bias_maps->gisprompt = "old,fcell,raster";	
	parm.n_bias_maps->description = "Raster map(s) with 'NO SITE' bias [0..1]";
		
	/*
	parm.s_bias_atts = G_define_option ();
	parm.s_bias_atts->key = "sbias";
	parm.s_bias_atts->required  = NO;
	parm.s_bias_atts->multiple = YES;
	parm.s_bias_atts->description = "Vector attributes with 'SITE' bias [0..1]";
	*/

	/* name of output maps/files */
	parm.output = G_define_option ();
	parm.output->key = "output";
	parm.output->type = TYPE_STRING;
	parm.output->required = YES;
	parm.output->description = "Prefix for result maps and logfiles";

	/* Name of logfile. If given, output will be logged */
	/* to this file. */
	parm.logfile = G_define_option ();
	parm.logfile->key = "logfile";
	parm.logfile->type = TYPE_STRING;
	parm.logfile->required = NO;
	parm.logfile->description = "ASCII file for log";

	/* if this filename is given, dump model building command lines
	   to a script instead of executing directly */
	parm.script = G_define_option ();
	parm.script->key = "script";
	parm.script->type = TYPE_STRING;
	parm.script->required = NO;
	parm.script->description = "Dump model commands to shell script";
	
	/* quiet operation? */
	flag.quiet = G_define_flag ();
	flag.quiet->key = 'q';
	flag.quiet->description = "Disable on-screen progress display";
	
	/* append output to existing logfile ? */
	flag.remove = G_define_flag ();
	flag.remove->key = 'r';
	flag.remove->description = "Remove NULL hypothesis maps";
	
	/* parse command line */
	if (G_parser (argc, argv))
	{
		exit (-1);
	}
	
	/* see if user wants to create a script instead of executing directly */
	if ( parm.script->answer != NULL ) {
		SCRIPT = fopen ( parm.script->answer, "w+" );
		if ( SCRIPT == NULL ) {
			G_fatal_error ("Unable to create script file: %s.", strerror (errno));
		}
		SCRIPTING = 1;
		fprintf ( SCRIPT, "#!/bin/sh\n" );
	}
		
	/* check how many evidence maps the user has supplied */	
	num_evidences = 0;
	while (parm.input->answers[num_evidences] != NULL) {
		num_evidences ++;
	}
		
	/* now call external programs to do the job! */
	sysstr = G_calloc (2048, sizeof(char));
	biasmaps = G_calloc (2048, sizeof(char));
	
	/* create BPA maps */
	if (parm.n_bias_maps->answers != NULL) {
		i = 0;	
		while (parm.n_bias_maps->answers[i] != NULL) {
			if (i>0) {
				G_strcat (biasmaps,",");
			}
			G_strcat (biasmaps,parm.n_bias_maps->answers[i]);
			i ++;
		}
	}
		
	for (i=0; i<num_evidences; i++) {
		fprintf ( stderr, "Generating BPNs for evidence %i\n", i );
		sprintf (sysstr,"raster=%s sites=%s output=%s.bpa.%s", 	parm.input->answers[i],
									parm.sites->answer,
									parm.output->answer,
									strtok(parm.input->answers[i],"@"));
		if (parm.n_bias_maps->answers != NULL) {
			G_strcat (sysstr, " nbias=");
			G_strcat (sysstr, biasmaps);
		}
		if (parm.logfile->answer != NULL) {
			if (i == 0) {
				G_strcat (sysstr, " log=");
			} else {
				G_strcat (sysstr, " -a log=");
			}
			G_strcat (sysstr, parm.logfile->answer);
		}
		
		if (flag.quiet->answer) {
			G_strcat (sysstr, " -q");
		}
		exec_module (PROG_BPA,sysstr);
	}
	/* END (create BPA mapse) */
	
	
	/* create DST knowledge base file and add entries */
	sprintf (sysstr,"%s", parm.output->answer);
	exec_module (PROG_CREATE,sysstr);
	sprintf (sysstr,"%s add=SITE",parm.output->answer);	
	exec_module (PROG_UPDATE,sysstr);
	sprintf (sysstr,"%s add=NOSITE",parm.output->answer);	
	exec_module (PROG_UPDATE,sysstr);
	for (i=0; i<num_evidences; i++) {
		sprintf (sysstr,"%s rast=%s.bpa.%s.SITE hyp=SITE",
						parm.output->answer,
						parm.output->answer,
						strtok(parm.input->answers[i],"@"));
		exec_module (PROG_UPDATE,sysstr);

		sprintf (sysstr,"%s rast=%s.bpa.%s.NOSITE hyp=NOSITE",
						parm.output->answer,
						parm.output->answer,
						strtok(parm.input->answers[i],"@"));
		exec_module (PROG_UPDATE,sysstr);

		sprintf (sysstr,"%s rast=%s.bpa.%s.SITE.NOSITE hyp=SITE,NOSITE",
						parm.output->answer,
						parm.output->answer,
						strtok(parm.input->answers[i],"@"));
		exec_module (PROG_UPDATE,sysstr);

		sprintf (sysstr,"%s add=%s",
						parm.output->answer,
						strtok(parm.input->answers[i],"@"));
		exec_module (PROG_SOURCE,sysstr);

		sprintf (sysstr,"%s source=%s rast=%s.bpa.%s.SITE hyp=SITE",		
						parm.output->answer,
						strtok(parm.input->answers[i],"@"),
						parm.output->answer,
						strtok(parm.input->answers[i],"@"));
		exec_module (PROG_SOURCE,sysstr);

		sprintf (sysstr,"%s source=%s rast=%s.bpa.%s.NOSITE hyp=NOSITE",		
						parm.output->answer,
						strtok(parm.input->answers[i],"@"),
						parm.output->answer,
						strtok(parm.input->answers[i],"@"));
		exec_module (PROG_SOURCE,sysstr);

		sprintf (sysstr,"%s source=%s rast=%s.bpa.%s.SITE.NOSITE hyp=SITE,NOSITE",		
						parm.output->answer,
						strtok(parm.input->answers[i],"@"),
						parm.output->answer,
						strtok(parm.input->answers[i],"@"));
		exec_module (PROG_SOURCE,sysstr);
	}
	/* END (build knowledge base file) */
	
	
	/* now combine evidences into result maps */	
	sprintf (sysstr,"%s output=%s.dst",
					parm.output->answer,
					parm.output->answer);
	
	if (parm.vals->answers != NULL) {
		G_strcat (sysstr," values=");
		i=0;
		while (parm.vals->answers[i] != NULL) {
			if (i>0) {
				G_strcat (sysstr, ",");
			}
			G_strcat (sysstr, parm.vals->answers[i]);
			i++;
		}
	}
	
	if (parm.logfile->answer != NULL) {
		G_strcat (sysstr, " -a log=");
		G_strcat (sysstr, parm.logfile->answer);
	}
	exec_module (PROG_COMBINE,sysstr);
	/* END (DST combination) */
	
	/* get rid of NULL hypothesis maps */
	if (flag.remove->answer) {
		sprintf (sysstr,"%s.dst.NULL.bel",parm.output->answer);
		G_remove ("fcell",sysstr);
		G_remove ("cell",sysstr);
		G_remove ("cats",sysstr);
		G_remove ("cellhd",sysstr);
		G_remove ("cell_misc",sysstr);
		G_remove ("colr",sysstr);
		G_remove ("colr2",sysstr);
		G_remove ("hist",sysstr);

		sprintf (sysstr,"%s.dst.NULL.pl",parm.output->answer);
		G_remove ("fcell",sysstr);
		G_remove ("cell",sysstr);
		G_remove ("cats",sysstr);
		G_remove ("cellhd",sysstr);
		G_remove ("cell_misc",sysstr);
		G_remove ("colr",sysstr);
		G_remove ("colr2",sysstr);
		G_remove ("hist",sysstr);

		sprintf (sysstr,"%s.dst.NULL.doubt",parm.output->answer);
		G_remove ("fcell",sysstr);
		G_remove ("cell",sysstr);
		G_remove ("cats",sysstr);
		G_remove ("cellhd",sysstr);
		G_remove ("cell_misc",sysstr);
		G_remove ("colr",sysstr);
		G_remove ("colr2",sysstr);
		G_remove ("hist",sysstr);

		sprintf (sysstr,"%s.dst.NULL.common",parm.output->answer);
		G_remove ("fcell",sysstr);
		G_remove ("cell",sysstr);
		G_remove ("cats",sysstr);
		G_remove ("cellhd",sysstr);
		G_remove ("cell_misc",sysstr);
		G_remove ("colr",sysstr);
		G_remove ("colr2",sysstr);
		G_remove ("hist",sysstr);

		sprintf (sysstr,"%s.dst.NULL.bint",parm.output->answer);
		G_remove ("fcell",sysstr);
		G_remove ("cell",sysstr);
		G_remove ("cats",sysstr);
		G_remove ("cellhd",sysstr);
		G_remove ("cell_misc",sysstr);
		G_remove ("colr",sysstr);
		G_remove ("colr2",sysstr);
		G_remove ("hist",sysstr);

		sprintf (sysstr,"%s.dst.NULL.maxbpa",parm.output->answer);
		G_remove ("fcell",sysstr);
		G_remove ("cell",sysstr);
		G_remove ("cats",sysstr);
		G_remove ("cellhd",sysstr);
		G_remove ("cell_misc",sysstr);
		G_remove ("colr",sysstr);
		G_remove ("colr2",sysstr);
		G_remove ("hist",sysstr);

		sprintf (sysstr,"%s.dst.NULL.minbpa",parm.output->answer);
		G_remove ("fcell",sysstr);
		G_remove ("cell",sysstr);
		G_remove ("cats",sysstr);
		G_remove ("cellhd",sysstr);
		G_remove ("cell_misc",sysstr);
		G_remove ("colr",sysstr);
		G_remove ("colr2",sysstr);
		G_remove ("hist",sysstr);

		sprintf (sysstr,"%s.dst.NULL.maxsrc",parm.output->answer);
		G_remove ("fcell",sysstr);
		G_remove ("cell",sysstr);
		G_remove ("cats",sysstr);
		G_remove ("cellhd",sysstr);
		G_remove ("cell_misc",sysstr);
		G_remove ("colr",sysstr);
		G_remove ("colr2",sysstr);
		G_remove ("hist",sysstr);

		sprintf (sysstr,"%s.dst.NULL.minsrc",parm.output->answer);
		G_remove ("fcell",sysstr);
		G_remove ("cell",sysstr);
		G_remove ("cats",sysstr);
		G_remove ("cellhd",sysstr);
		G_remove ("cell_misc",sysstr);
		G_remove ("colr",sysstr);
		G_remove ("colr2",sysstr);
		G_remove ("hist",sysstr);
	}
	/* END (delete NULL hypothesis maps) */
	
	G_free (sysstr);
	
	if ( SCRIPTING ) {
		fclose ( SCRIPT );
	}
	
	return (EXIT_SUCCESS);
}
