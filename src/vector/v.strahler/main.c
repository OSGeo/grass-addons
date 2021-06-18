
/****************************************************************************
 * 
 *  MODULE:       v.strahler
 *  
 *  AUTHOR(S):    Florian Kindl, Norbert Pfeifer, The GRASS development team
 *		  Modified by: Ivan Marchesini <marchesini unipg.it> and 
		  Annalisa Minelli <annapatri tiscali.it>
 *                
 *  PURPOSE:      Assign Strahler order to dendritic network
 *                
 *  COPYRIGHT:    (C) 2006 by the Authors
 * 
 *                This program is free software under the 
 *                GNU General Public License (v2). 
 *                Read the file COPYING that comes with GRASS
 *                for details.
 * 
 ****************************************************************************/

/*! \file main.c
   \brief Assign Strahler order to dendritic network
   \author Florian Kindl

   \todo Deal with poor topology 
   \li implemement sloppy mode or
   \li force clean topology
   \todo ...
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <search.h>
#include <time.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/dgl.h>
#include <grass/dbmi.h>
#include <grass/glocale.h>
#include "strahler.h"

#define COPYBLAH 1
#define DDFIELDBLAH 1
#define BADDCOLUMNBLAH 1
#define RITEDBLAH 1
#define EBUG 1
#define REATEDBLAH 1

int ret, type;			/* return and type related to Vect_read_line and Vect_write_line */
int fdrast;			/* file descriptor for raster file is int */
int ntrees;			/* number of trees in dataset, returned by StrahForestToTrees */
double sloppy;

int main(int argc, char **argv)
{
    int line, node;
    char buf[1024];
    int nnodes, nlines, tlines;
    DBBUF *dbbuf;
    NODEV *nodev;
    struct Option *input, *output, *dem_opt, *txout_opt, *sloppy_opt,
	*field_opt;
    struct GModule *module;
    char *inputset, *demset;
    struct Map_info In, Out;
    struct Map_info Trees;
    FILE *txout;
    struct Cell_head window;	/* for cell sampling */

    extern int ntrees;		/* number of trees calculated by StrahForestToTrees */
    extern int fdrast;
    extern double sloppy;

    /* Attribute table (from v.net.path/path.c) */

    struct line_cats *Cats;	/* introduced and initialized the structures line_cats and line_pnts */
    static struct line_pnts *Points;

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();
    dbString sql;
    dbDriver *driver;
    dbColumn *column;

    struct field_info *Fi;
    int field;

    /* Initialize the GIS calls */

    G_gisinit(argv[0]);

    input = G_define_standard_option(G_OPT_V_INPUT);
    output = G_define_standard_option(G_OPT_V_OUTPUT);

    module = G_define_module();
    module->description = _("Strahler order");

    dem_opt = G_define_standard_option(G_OPT_R_INPUT);
    dem_opt->key = "dem";
    dem_opt->description = _("Underlying DEM");

    txout_opt = G_define_option();
    txout_opt->key = "txout";
    txout_opt->type = TYPE_STRING;
    txout_opt->required = NO;
    txout_opt->multiple = NO;
    txout_opt->gisprompt = "new_file,file,output";
    txout_opt->description =
	_("Path to ASCII file where results will be written");

    /* option sloppy for bad topology */
    sloppy_opt = G_define_option();
    sloppy_opt->key = "sloppy";
    sloppy_opt->type = TYPE_DOUBLE;
    sloppy_opt->required = NO;
    sloppy_opt->answer = "0.0";
    sloppy_opt->multiple = NO;
    sloppy_opt->description =
	_("Threshold for distance within different nodes are considered the same node - may not work");

    field_opt = G_define_standard_option(G_OPT_V_FIELD);
    field = atoi(field_opt->answer);

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);


    Vect_check_input_output_name(input->answer, output->answer,
				 GV_FATAL_EXIT);

    inputset = G_find_vector2(input->answer, NULL);
    if (inputset == NULL) {
	G_fatal_error(_("Could not find input input <%s>"), input->answer);
    }

    /* open datasets at topology level 2 */

    Vect_set_open_level(2);
    Vect_open_old(&In, input->answer, inputset);

    G_debug(1, "Input vector opened");

    /* Open new vector, make 3D if input is 3D */

    if (1 > Vect_open_new(&Out, output->answer, Vect_is_3d(&In))) {
	Vect_close(&In);
	G_fatal_error("Failed opening output vector file %s", output->answer);
    }

    /* Open DEM */

    demset = G_find_cell2(dem_opt->answer, NULL);
    if (demset == NULL) {
	G_fatal_error("DEM file %s not found", dem_opt->answer);
    }
    if (1 > (fdrast = G_open_cell_old(dem_opt->answer, demset))) {
	G_fatal_error("Failed opening DEM file %s", dem_opt->answer);
    }

    /* Open text file for results if given */

    if (txout_opt->answer) {
	txout = fopen(txout_opt->answer, "w");
	if (txout == NULL)
	    G_fatal_error(_("Cannot open file %s"), txout_opt->answer);
    }

    sloppy = atof(sloppy_opt->answer);
    /* printf("blah %f", sloppy*2.4 ); */


    /* write history */
    /*Vect_copy_head_data( &In, &Out );
       Vect_hist_copy( &In, &Out );
       Vect_hist_command( &Out ); */

#ifdef COPYBLAH
    /* this works, we want to continue here and ADD two columns to the &Out */
    /* Copy input to output (from v.clean/main.c) */
    /*G_debug( 1, "Copying vector lines to Output" ); */

       /* This works for both level 1 and 2 */
    /*Vect_copy_map_lines ( &In, &Out );        */
    /* 0: copy all fields, else field number */
#endif


#ifdef ADDFIELDBLAH		/* Create table (from v.net.path/path.c) */
    /* or: add fields to existing table? */
    /*                                                      *Map, field, field_name, type */

    Fi = Vect_default_field_info(&Out, field, NULL, GV_1TABLE);
    Vect_map_add_dblink(&Out, field, NULL, Fi->table, "cat", Fi->database,
			Fi->driver);

    driver = db_start_driver_open_database(Fi->driver, Fi->database);
    driver =
	db_start_driver_open_database(Fi->driver,
				      Vect_subst_var(Fi->database, &Out));
    /* from v.reclass/main.c :
     */

    if (driver == NULL) {
	G_fatal_error("Cannot open database %s by driver %s", Fi->database,
		      Fi->driver);
    }


    /* store the statement to create a table with category, basin ID and strahler order of the arc */
    sprintf(buf,
	    "CREATE TABLE %s ( cat integer, bsnid integer, sorder integer )",
	    Fi->table);

    /* from v.reclass/main.c : */
    dbString stmt;

    db_init_string(&stmt);
    db_set_string(&stmt, buf);

    if (db_execute_immediate(driver, &stmt) != DB_OK) {
	Vect_close(&Out);
	db_close_database_shutdown_driver(driver);
	G_fatal_error("Cannot create table: %s", db_get_string(&stmt));
    }

    /*
       sprintf ( buf, "ALTER TABLE %s ADD COLUMN cat integer", Fi->table );
       sprintf ( buf, "ALTER TABLE %s ADD COLUMN bsnid integer", Fi->table );
       sprintf ( buf, "ALTER TABLE %s ADD COLUMN sorder integer", Fi->table );
     */
#endif

#ifdef DBADDCOLUMNBLAH
    sprintf(buf, "bsnid");
    db_set_string(&sql, buf);
    column->columnName = sql;
    column->sqlDataType = 1;
    sprintf(buf, "%s", Fi->table);
    /*db_set_string ( &sql, buf ); */
    /* why such complicated arguments for db_add_column???
       dbDriver, dbString, dbColumn */
    if (db_add_column(driver, &sql, column) != DB_OK) {
	db_close_database_shutdown_driver(driver);
	G_fatal_error("Cannot add column column in table %s", Fi->table);
    }
#endif


    /* execute statement */
#ifdef CREATEDBLAH
    sprintf(buf,
	    "CREATE TABLE %s ( cat integer, bsnid integer, sorder integer )",
	    Fi->table);
    db_set_string(&sql, buf);
    G_debug(2, db_get_string(&sql));

    if (db_execute_immediate(driver, &sql) != DB_OK) {
	db_close_database_shutdown_driver(driver);
	G_fatal_error("Cannot create table: %s", db_get_string(&sql));
    }
    else
	printf("table created\n");

    if (db_create_index2(driver, Fi->table, "cat") != DB_OK) {
	G_warning("Cannot create index");
    }
    else
	printf("index created\n");

    if (db_grant_on_table
	(driver, Fi->table, DB_PRIV_SELECT, DB_GROUP | DB_PUBLIC) != DB_OK) {
	G_fatal_error("Cannot grant privileges on table %s", Fi->table);
    }
    else
	printf("privileges granted\n");
#endif

    nnodes = Vect_get_num_nodes(&In);
    nlines = Vect_get_num_lines(&In);
    G_debug(1, "Number of lines: %d", nlines);
    G_debug(1, "Number of nodes: %d", nnodes);

    /* Create table to store ordering */
    dbbuf = (DBBUF *) G_malloc((nlines + 1) * ((int)sizeof(DBBUF)));
    nodev = (NODEV *) G_malloc((nnodes + 1) * ((int)sizeof(NODEV)));

    /* initialize properly */
    for (line = 1; line <= nlines; line++) {
	dbbuf[line].category = dbbuf[line].line = dbbuf[line].bsnid =
	    dbbuf[line].sorder = 0;
    }
    for (node = 1; node <= nnodes; node++) {
	nodev[node].node = nodev[node].degree = nodev[node].visited = 0;
    }

    ntrees = (int)StrahForestToTrees(&In, &Out, dbbuf);
    G_debug(1, "Number of trees: %d", ntrees);

    StrahFindLeaves(&In, dbbuf, nodev, ntrees, fdrast);

    G_debug(2, "dbbuf after FindLeaves:\nline\tbsnid\tsorder");
    for (line = 1; line <= nlines; line++) {
	sprintf(buf, "%d\t%d\t%d\n", dbbuf[line].line, dbbuf[line].bsnid,
		dbbuf[line].sorder);
	G_debug(2, "%s", buf);
    }
    G_debug(2, "nodev after FindLeaves:\nnode\tdegree\tvisited");
    for (node = 1; node <= nnodes; node++) {
	sprintf(buf, "%d\t%d\t%d\n", (int)nodev[node].node,
		nodev[node].degree, nodev[node].visited);
	G_debug(2, "%s", buf);
    }

    StrahOrder(&In, dbbuf, nodev);

    G_debug(2, "dbbuf after StrahOrder:\nline\tbsnid\tsorder\n");
    for (line = 1; line <= nlines; line++) {
	sprintf(buf, "%d\t%d\t%d\n", dbbuf[line].line, dbbuf[line].bsnid,
		dbbuf[line].sorder);
	G_debug(2, "%s", buf);
    }
    G_debug(2, "nodev after StrahOrder:\nnode\tdegree\tvisited\n");
    for (node = 1; node <= nnodes; node++) {
	sprintf(buf, "%d\t%d\t%d\n", (int)nodev[node].node,
		nodev[node].degree, nodev[node].visited);
	G_debug(2, "%s", buf);
    }

#ifdef WRITEDBLAH
    /* and write DB records */
    db_begin_transaction(driver);

    for (line = 1; line <= nlines; line++) {
	sprintf(buf, "insert into %s values ( %d, %d, %d )", Fi->table, line,
		dbbuf[line].bsnid, dbbuf[line].sorder);
	db_set_string(&sql, buf);
	/* G_debug ( 3, db_get_string ( &sql ) ); */
	if (db_execute_immediate(driver, &sql) != DB_OK) {
	    db_close_database_shutdown_driver(driver);
	    G_fatal_error("Insert new row: %s", db_get_string(&sql));
	}
    }

    db_commit_transaction(driver);

    db_close_database_shutdown_driver(driver);
#endif

    /* writing StrahOrder instead of category in the output */

    for (line = 1; line <= nlines; line++) {
	type = Vect_read_line(&In, Points, Cats, line);
	ret = Vect_cat_del(Cats, field);
	G_debug(4, "deleted categories, ret=%d", ret);
	Vect_cat_set(Cats, field, dbbuf[line].sorder);
	Vect_write_line(&Out, type, Points, Cats);
	G_debug(4, "category written for line %d", line);
    }

    /* assign category values */

    for (line = 1; line <= nlines; line++) {
	dbbuf[line].category = Vect_get_line_cat(&In, line, field);
	G_debug(4, "added category %d for line %d", dbbuf[line].category,
		dbbuf[line].line);
    }

    /* Write text file for results if given */

    if (txout_opt->answer)
	StrahWriteToFile(dbbuf, nlines, txout);

    Vect_close(&In);
    G_close_cell(fdrast);

    Vect_build(&Out);
    Vect_close(&Out);

    if (txout_opt->answer)
	fclose(txout);

    return (EXIT_SUCCESS);
}
