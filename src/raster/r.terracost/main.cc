/* 

   Copyright (C) 2006 Thomas Hazel, Laura Toma, Jan Vahrenhold and
   Rajiv Wickremesinghe

   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License as
   published by the Free Software Foundation; either version 2 of the
   License, or (at your option) any later version.

   This program is distributed in the hope that it will be useful, but
   WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   General Public License for more details.

*/

#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <errno.h>
#include <unistd.h>
#include <pwd.h>
  
extern "C" {
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/version.h>
}
#include <grass/iostream/ami.h>

#include "main.h"
#include "common.h" /* declares the globals */
#include "sortutils.h"
#include "types.h"
#include "option.h"
#include "input.h"
#include "boundary.h"
#include "tile.h"
#include "distanceType.h"
#include "index.h"
#include "initialize.h"
#include "dijkstra.h"
#include "output.h"
#include "formatNumber.h"
#include "debug.h"

static int debug = 0;
static int info = 0;

//#define DEBUG_LOADGRID

int ijTileCostCompareType::tileSizeRows = 0;
int ijTileCostCompareType::tileSizeCols = 0;
// int MinIOCostCompareType<costSourceType>::tileSizeRows = 0;
// int MinIOCostCompareType<cost_type>::tileSizeRows = 0;
// int MinIOCostCompareType<costSourceType>::tileSizeCols = 0;
// int MinIOCostCompareType<cost_type>::tileSizeCols = 0;
int ijCostCompareType::tileSizeRows = 0;
int ijCostCompareType::tileSizeCols = 0;
static struct  Cell_head *region = NULL; /* header of the region */

#define S0OUT "tileStr"
#define S0OUT_ANS "terracost.tileStr"
#define S0BND "bndStr"
#define S0BND_ANS "terracost.bndStr"
#define S1OUT "bspStr"
#define S1OUT_ANS "terracost.bspStr"
#define S2BOUT "sbspStr"
#define S2BOUT_ANS "terracost.sbspStr"
#define PHASE2BND "phase2Bnd"
#define PHASE2BND_ANS "terracost.phase2Bnd"
#define CONFIG "config" 
#define CONFIG_ANS "terracost.config"
#define STATS "stats"
#define STATS_ANS "terracost.stats"
#define DIST_GRID "terracost-lcp.asc"

const char *description = _("Computes a least-cost surface for a given cost grid and set of start points.");


/* ---------------------------------------------------------------------- */
/* get the args from GRASS */

void 
parse_args(int argc, char *argv[]) {

  /* input elevation grid  */
  struct Option *input_cost;
  input_cost = G_define_standard_option(G_OPT_R_INPUT);
  input_cost->description= _("Name of raster map containing grid cell cost information");

  /* source point raster */
  struct Option *source_grid;
  source_grid = G_define_standard_option(G_OPT_R_INPUT);
  source_grid->key        = "start_raster";
  source_grid->description= _("Name of starting raster points map");
  source_grid->guisection = _("Start");

  /* output direction  grid */
  struct Option *output_cost;
  output_cost = G_define_standard_option(G_OPT_R_OUTPUT);
  output_cost->description= _("Output distance grid raster map");

  /* Number of tiles */  
  struct Option *numtiles;
  numtiles = G_define_option() ;
  numtiles->key = "numtiles";
  numtiles->type       = TYPE_INTEGER;
  numtiles->required   = NO;
  numtiles->description= _("Number of tiles (default: 1)");
  numtiles->answer     = G_store("1");

  /* main memory */
  struct Option *mem;
  mem = G_define_option() ;
  mem->key         = "memory";
  mem->type        = TYPE_INTEGER;
  mem->required    = NO;
  mem->answer      = G_store("400"); /* 400MB default value */
  mem->description = _("Main memory size (in MB)");

  /* temporary STREAM path */
  struct Option *streamdir;
  streamdir = G_define_option() ;
  streamdir->key        = "STREAM_DIR";
  streamdir->type       = TYPE_STRING;
  streamdir->required   = NO;
  streamdir->answer     = G_store("/var/tmp");
  streamdir->description= _("Location of temporary STREAMs");

  /* temporary VTMPDIR path */
  struct Option *vtmpdir;
  vtmpdir = G_define_option() ;
  vtmpdir->key        = VTMPDIR;
  vtmpdir->type       = TYPE_STRING;
  vtmpdir->required   = NO;
  char vtmpdirbuf[BUFSIZ];
  /* the default answer is /var/tmp/userid */
  struct passwd *pw;        /* TODO: is this really needed? */
  if((pw = getpwuid(getuid())) != NULL) {
	sprintf(vtmpdirbuf, "/var/tmp/%s", pw->pw_name);
  } else {
	sprintf(vtmpdirbuf, "/var/tmp/%d", getuid());
  }
  vtmpdir->answer     = strdup(vtmpdirbuf);
  vtmpdir->description= _("Location of intermediate STREAMs");

  struct Flag *help_f;
  help_f = G_define_flag();
  help_f->key         = 'h' ; 
  help_f->description  = _("Help");

  /* verbose flag */
  /* please, remove before GRASS 7 released */
  struct Flag *quiet;
  quiet = G_define_flag() ;
  quiet->key         = 'q' ;
  quiet->description = _("Quiet") ;

  struct Flag *info_f;
  info_f = G_define_flag();
  info_f->key         = 'i' ; 
  info_f->description  = _("Info (print suggested numtiles information and exit)");

  /* save ascii grid flag */
  struct Flag *ascii; 
  ascii = G_define_flag() ;
  ascii->key         = 's' ;
  ascii->description = _("Dbg: Save output to ASCII file \"DIST_GRID\"");
  ascii->guisection = _("Debug");

  struct Flag *debug_f;
  debug_f = G_define_flag();
  debug_f->key         = 'd' ; 
  debug_f->description  = _("Dbg: Print (a lot of) debug info (developer use)");
  debug_f->guisection = _("Debug");

  /* Run step0 only flag */
  struct Flag *step0;
  step0 = G_define_flag();
  step0->key         = '0' ; 
  step0->description  = _("Dbg: Step 0 only (default: run all)");
  step0->guisection = _("Debug");

  /* Run step 1 only flag*/
  struct Flag *step1;
  step1 = G_define_flag() ;
  step1->key         = '1' ;
  step1->description = _("Dbg: Step 1 only (default: run all)");
  step1->guisection = _("Debug");

  /* Run step 2 and 3 only flags */
  struct Flag *step2;
  step2 = G_define_flag();
  step2->key         = '2' ; 
  step2->description  = _("Dbg: Step 2 only (default: run all)");
  step2->guisection = _("Debug");

  struct Flag *step3;
  step3 = G_define_flag();
  step3->key         = '3' ; 
  step3->description  = _("Dbg: Step 3 only (default: run all)");
  step3->guisection = _("Debug");
  
  struct Flag *step4;
  step4 = G_define_flag();
  step4->key         = '4' ; 
  step4->description  = _("Dbg: Step 4 only (default: run all)");
  step4->guisection = _("Debug");

  /* Stem name for stream outputs; used in conjunction with step0 flag */  
  struct Option *s0out;
  s0out = G_define_option() ;
  s0out->key = S0OUT;
  s0out->type       = TYPE_STRING;
  s0out->required   = NO;
  s0out->description= _("Dbg: Stream name stem for step 0 output");
  s0out->answer     = G_store(S0OUT_ANS);
  s0out->guisection = _("Debug");

  struct Option *s0bnd;
  s0bnd = G_define_option() ;
  s0bnd->key = S0BND;
  s0bnd->type       = TYPE_STRING;
  s0bnd->required   = NO;
  s0bnd->description= _("Dbg: Stream name for boundary data structure");
  s0bnd->answer     = G_store(S0BND_ANS);
  s0bnd->guisection = _("Debug");

  /* Name for config file output */  
  struct Option *s1out;
  s1out = G_define_option() ;
  s1out->key = S1OUT;
  s1out->type       = TYPE_STRING;
  s1out->required   = NO;
  s1out->description= _("Dbg: Output file for step 1");
  s1out->answer     = G_store(S1OUT_ANS);
  s1out->guisection = _("Debug");

  /* Name for config file output */  
  struct Option *s2bout;
  s2bout = G_define_option() ;
  s2bout->key = S2BOUT;
  s2bout->type       = TYPE_STRING;
  s2bout->required   = NO;
  s2bout->description= _("Dbg: Output file for source to boundary stream");
  s2bout->answer     = G_store(S2BOUT_ANS);
  s2bout->guisection = _("Debug");

  /* Name for config file output */  
  struct Option *config;
  config = G_define_option() ;
  config->key = CONFIG;
  config->type       = TYPE_STRING;
  config->required   = NO;
  config->description= _("Dbg: Name for config file");
  config->answer     = G_store(CONFIG_ANS);
  config->guisection = _("Debug");

 /* Name for config file output */  
  struct Option *phaseBnd;
  phaseBnd = G_define_option() ;
  phaseBnd->key = PHASE2BND;
  phaseBnd->type       = TYPE_STRING;
  phaseBnd->required   = NO;
  phaseBnd->description= _("Dbg: Name for phase2Bnd file");
  phaseBnd->answer     = G_store(PHASE2BND_ANS);
  phaseBnd->guisection = _("Debug");

  /* stats file */
  struct Option *stats_opt;
  stats_opt = G_define_option() ;
  stats_opt->key = "stats";
  stats_opt->type       = TYPE_STRING;
  stats_opt->required   = NO;
  stats_opt->description= _("Dbg: Stats file");
  stats_opt->answer     = G_store(STATS_ANS);
  stats_opt->guisection = _("Debug");

  struct Option *tilesAreSorted;
  tilesAreSorted =  G_define_option();
  tilesAreSorted->key         = "tilesAreSorted" ; 
  tilesAreSorted->type       = TYPE_STRING;
  tilesAreSorted->required   = NO;
  tilesAreSorted->description  = _("Dbg: Tiles are sorted (used in grid version) (y/n)");
  tilesAreSorted->answer = G_store("no");
  tilesAreSorted->guisection = _("Debug");

  /* ************************* */
  if (G_parser(argc, argv)) {
    exit (EXIT_FAILURE);
  }
  
  /* all user parameters are collected in a global opt */
  assert(opt);
  opt->cost_grid = input_cost->answer;
  opt->out_grid = output_cost->answer;
  opt->source_grid = source_grid->answer;
  opt->mem = atoi(mem->answer);
  opt->streamdir= streamdir->answer;
  opt->vtmpdir= vtmpdir->answer;
  opt->verbose= (!quiet->answer);
  opt->ascii = ascii->answer; 
  opt->stats= stats_opt->answer;
  opt->runMode = RUN_NONE;
  if(step0->answer) {
    opt->runMode |= RUN_S0;
  }
  if(step1->answer) {
    opt->runMode |= RUN_S1;
  }
  if(step2->answer) {
    opt->runMode |= RUN_S2;
  }
  if(step3->answer) {
    opt->runMode |= RUN_S3;
  }
  if(step4->answer) {
	opt->runMode |= RUN_S4;
  }
  //if the user does not specify any step, then run all steps
  if(opt->runMode == RUN_NONE) {
    opt->runMode = RUN_ALL;
  }
  opt->tilesAreSorted = (tilesAreSorted->answer[0] == 'y');
  opt->numtiles = atoi(numtiles->answer);
  opt->s0out = s0out->answer;
  opt->s1out = s1out->answer;
  opt->s0bnd = s0bnd->answer;
  opt->s2bout = s2bout->answer;
  opt->config = config->answer;
  opt->phase2Bnd = phaseBnd->answer; 
  opt->s1fd = 0;

  debug = (debug_f->answer ? 1 : 0);
  info = (info_f->answer ? 1 : 0);

  if(help_f->answer) {
	G_usage();
	printf(description);
	exit(EXIT_SUCCESS);
  }
}



/* ---------------------------------------------------------------------- */
void check_args() {

  /* check if cost grid name is  valid */
  if (G_legal_filename (opt->cost_grid) < 0) {
    G_fatal_error ("[%s] is an illegal name", opt->cost_grid);
  }
  /* check if distance grid names is valid */
  if (G_legal_filename (opt->out_grid) < 0) {
    G_fatal_error ("[%s] is an illegal name", opt->out_grid);
  }
  if (G_legal_filename (opt->source_grid) < 0) {
    G_fatal_error ("[%s] is an illegal name", opt->source_grid);
  }
  
}

/* ---------------------------------------------------------------------- */
/* record current configuration to stats file */
void record_args(int argc, char **argv) {

  /* record time stamp */
  time_t t = time(NULL);
  char buf[1000];
  if(t == (time_t)-1) {
    perror("time");
    exit(1);
  }
  ctime_r(&t, buf);
  buf[24] = '\0';
  stats->timestamp(buf);
  //*stats << "Not printing stats." << endl;
  *stats << "Command Line: " << endl;
  for(int i=0; i<argc; i++) {
    *stats << argv[i] << " ";
  }
  *stats << endl;
  
  *stats << "input cost grid: " << opt->cost_grid << "\n";
  *stats << "input source grid: " << opt->source_grid << "\n";
  *stats << "output distance grid: " << opt->out_grid << "\n";
  if (opt->runMode & RUN_S0) *stats << " Step1";
  if (opt->runMode & RUN_S1) *stats << " Step2";
  if (opt->runMode & RUN_S2) *stats << " Step3";
  if (opt->runMode & RUN_S3) *stats << " Step4";
  *stats << "\n";
  /* record memory size */
  size_t mm_size = opt->mem  << 20; /* (in bytes) */
  char tmp[100];
  formatNumber(tmp, mm_size);
  sprintf(buf,"memory size: %s bytes", tmp);
  stats->comment(buf);
}


/* ---------------------------------------------------------------------- */
void printGrid(AMI_STREAM<ijCost> *testStr) {

  statsRecorder *offsetWriter = new statsRecorder("offset.out");

  AMI_err ae;
  // this assert won't work with boundary streams
  //assert(testStr->stream_len() == nrows*ncols);
  ae = testStr->seek(0);
  ijCost *it;
  *offsetWriter << "grid: \n" << "Length: " << testStr->stream_len() << "\n";
  //for (dimension_type i = 0; i<nrows; i++) {
  //  for (dimension_type j=0; j< ncols; j++) {
  while (ae != AMI_ERROR_END_OF_STREAM) {
    ae = testStr->read_item(&it);
    *offsetWriter << *it << "\n";
    //assert(ae == AMI_ERROR_NO_ERROR);
  }
  testStr->seek(0); 
  delete offsetWriter;
}



/* ---------------------------------------------------------------------- */
/* this function computes and returns the optimal tizesize */
void
compute_tilesize(const char *label, int nr, int nc, int mem, 
		 int *tilesize, int *numtiles) {
  
  // we need all the data below to be in memory while we compute sssp
  // on a tile
  int elt = ( sizeof(costSourceType) /* tile */
	      + sizeof(cost_type) /* dist */
	      + sizeof(costStructure) ); /* pq */
  
  printf("%s: avail memory M = %s\n", label, formatNumber(NULL, mem));
  printf("%s: grid size N = %s elements\n", label, formatNumber(NULL, nr*nc));
  printf("%s: sizeof elt = %d\n", label, elt);

 

  int ts = mem / elt; 
  int nt = (nr * nc + ts - 1) / ts;
  printf("%s: max tilesize R = %s elements\n",label, formatNumber(NULL, ts));

  //does it fit into memory? 
  if (nt == 1) { 
    printf("%s: fits in memory, use numtiles=1\n", label); 
  } else { 
    if (nt <4) {
      printf("%s: almost.. fits in memory; try numtiles=1 first\n", label);
    } else {
      printf("%s: does NOT fits in memory\n", label); 
    }
    //optimal tilisize, determined experimentally, is approx. 15,000
    //elements
    ts = 15000; 
    nt = nr*nc/ts;
  }
  
  printf("%s: %s N=%ld elements, M=%d bytes, optimal numtiles=%d\n", 
	 label, G_location(), (long)(nr*nc), mem, nt);
  
  *numtiles = nt;
  *tilesize = ts;
}



/* ---------------------------------------------------------------------- */
int
main(int argc, char *argv[]) {
  
  struct GModule *module;
  char buf[1000];
  
  /* initialize GIS library */
  G_gisinit(argv[0]);
  module = G_define_module();
  module->keywords = _("raster, cost surface, cumulative costs");
  module->description = description;
 
  /* get the current region and dimensions */  
  region = (struct Cell_head*)malloc(sizeof(struct Cell_head));
  assert(region);
#if defined(GRASS_VERSION_MAJOR) && (GRASS_VERSION_MAJOR > 6)
  G_get_set_window(region);
#else
  if (G_get_set_window(region) == -1) {
      G_fatal_error(_("Unable to get current region"));
  }
#endif
  int nr = G_window_rows();
  int nc = G_window_cols();
  if ((nr > dimension_type_max) || (nc > dimension_type_max)) {
    printf("[nrows=%d, ncols=%d] dimension_type overflow--change dimension_type and recompile\n",nr,nc);
    G_fatal_error("[nrows=%d, ncols=%d] dimension_type overflow--change dimension_type and recompile\n",nr,nc);
  } else {
    nrows = (dimension_type)nr;
    ncols = (dimension_type)nc;
    nrowsPad = (dimension_type)nr;
    ncolsPad = (dimension_type)nc;
  }
  
  /* read user options; fill in global variable opt */  
  opt = (userOptions*)malloc(sizeof(userOptions));
  assert(opt);
  parse_args(argc, argv);
  
  
  /* setup STREAM_DIR */
  sprintf(buf, "%s=%s", STREAM_TMPDIR, opt->streamdir);
  if(getenv(STREAM_TMPDIR) == NULL) {
    printf("setenv %s\n", buf);
    if (putenv(G_store(buf)) != 0) {
      printf("cannot setenv %s\n",buf);
      exit(1); 
    }
  }
  if (getenv(STREAM_TMPDIR) == NULL) {
    G_fatal_error("STREAM_TMPDIR not set");
    exit(1); 
  } else {
    fprintf(stdout, "STREAM temporary files in %s\n", getenv(STREAM_TMPDIR)); 
    fprintf(stdout, "\t!!!THESE TEMPORARY STREAMS WILL NOT BE DELETED "
	    "IN CASE OF ABNORMAL TERMINATION OF THE PROGRAM.\n"); 
    fprintf(stdout, "\t!!!TO SAVE SPACE PLEASE DELETE THESE FILES MANUALLY!\n");
  }
  

  /* setup VTMPDIR */
  sprintf(buf, "%s=%s", VTMPDIR, opt->vtmpdir);
  if (getenv(VTMPDIR) == NULL) {
    /* if not already set  */
    printf("setenv %s\n", buf);
    if(putenv(G_store(buf)) !=0) {
      printf("cannot setenv %s\n",buf);
      exit(1); 
    }
  }
  if (getenv(VTMPDIR) == NULL) {
    fprintf(stdout, "%s: environment not set", VTMPDIR);
    exit(1);
  } else {
    fprintf(stdout, "terracost intermediate files in %s\n", getenv(VTMPDIR)); 
  }
  
  /* DOES VTMPDIR exist? If not, create it */
  struct stat sb;
  if(stat(opt->vtmpdir, &sb) < 0) {
    perror(opt->vtmpdir);
    fprintf(stderr, "trying to create %s\n", opt->vtmpdir);
    if(mkdir(opt->vtmpdir, 0777)) {
      if(errno != EEXIST) {
	perror(opt->vtmpdir);
	// this might not be a fatal error (maybe we dont use it)?
	exit(1);
      }
    }
  }
  
  /* if info mode, print tileseze and exit */
  if(info) {
	printf("\n"); 
	printf("STREAM_TMPDIR=%s\n", getenv(STREAM_TMPDIR));
	printf("VTMPDIR=%s\n", getenv(VTMPDIR));

	int tilesize, numtiles;
	compute_tilesize("TILESIZE", nrows, ncols, opt->mem << 20, 
			 &tilesize, &numtiles);
	return 0; 
  }//info


  if(opt->verbose) {
    printf("region size is %d x %d\n", nrows, ncols);
  }
  
  
  /* quick check for (some) required args */
  if( (opt->runMode & RUN_S0) && (!opt->cost_grid || !opt->source_grid) ) {
    fprintf(stderr, "ERROR: required input argument missing\n");
    G_usage();
    printf(description);
    exit(1);
  }
  if( (opt->runMode & RUN_S4) && (!opt->out_grid)) {
    fprintf(stderr, "ERROR: required output argument missing\n");
    G_usage();
    printf(description);
    exit(1);
  }
  
  
  // CHECK NUMBER OF TILES 
  if(opt->numtiles < 1) {
    fprintf(stderr, "ERROR: numtiles must be >= 1\n");
    exit(1);
  }
  
  
  /* open the stats file */
  {
    // note: this is a hack. the default should be set earlier, and just used here -RW
    if(opt->stats[0] != '/') {	// relative path
      char location[BUFSIZ];
      //sprintf(location, "%s-%s", G_location(), opt->stats);
      sprintf(location, "%s", resolvePath(opt->stats));
      stats = new statsRecorder(location);
    } else {					// absolute path; dont mess with name
      stats = new statsRecorder(opt->stats);
    }
  }
  
  /* record some info in stats file */
  record_args(argc, argv);
  {
    char buf[BUFSIZ];
    long grid_size = nrows * ncols;
    *stats << "region size = " <<  formatNumber(buf, grid_size) << " elts "
	   << "(" << nrows << " rows x " << ncols << " cols)\n";
    
    stats->flush();
  }
  
  
  /* set up STREAM memory manager */
  size_t mm_size = opt->mem << 20; /* opt->mem is in MB */
  MM_manager.set_memory_limit(mm_size);
  if (opt->verbose) {
    MM_manager.warn_memory_limit();
  } else {
    MM_manager.ignore_memory_limit();
  }
  MM_manager.print_limit_mode();
  
  /* initializes values used in update.cc */
  Cell_head window;
#if defined(GRASS_VERSION_MAJOR) && (GRASS_VERSION_MAJOR > 6)
  G_get_window(&window);
#else
  int ok = G_get_window(&window);
  assert(ok >= 0);
#endif
  opt->EW_fac = 1.0 ;
  opt->NS_fac = window.ns_res/window.ew_res ;
  opt->DIAG_fac = (double)sqrt((double)(opt->NS_fac*opt->NS_fac + 
					opt->EW_fac*opt->EW_fac));
  opt->V_DIAG_fac = (double)sqrt((double)(4*opt->NS_fac*opt->NS_fac + 
					  opt->EW_fac*opt->EW_fac)); 
  opt->H_DIAG_fac = (double)sqrt((double)(opt->NS_fac*opt->NS_fac + 
					  4*opt->EW_fac*opt->EW_fac));
  update_init(opt->EW_fac, opt->NS_fac, opt->DIAG_fac);
  



  /* start timing */
  Rtimer rtTotal;   
  rt_start(rtTotal);
  
  
  /////////////////////////////////////////////////////////////////////////
  /////////////////////////////////////////////////////////////////////////
  
  /* ************************************************** */
  size_t availmem1;
  availmem1 = MM_manager.memory_available();
  char memBuf [100] = "";
  formatNumber(memBuf, availmem1);
  long nodata_count;

  //*stats << "numtiles = " << opt->numtiles << endl;
  // we don't really know yet, since we might read it from config...


  /* ------------------------------------------------------------ */
  //size_t mem = memForNormalDijkstra(nrows, ncols);
  if (opt->numtiles == 1) {
    printf("Using normal Dijkstra");
    stats->comment("Using normal Dijkstra");
    normalDijkstra(opt->cost_grid,opt->source_grid, &nodata_count);

    /* CLEAN up */
    cout << "cleaning up\n"; cout.flush();
    free(region);
    free(opt);
    delete stats;
    cout << "r.terracost done\n"; cout.flush();
    return 0; 
  }


 /* ------------------------------------------------------------ */
  //this is executed if numtiles>1: STEP 0, 1, 2, 3, 4
  

  /* ************************************************** */
  /* STEP 0: set up tile size, padded grid size and load cost grid and
     compute substitute graph  */
  
  TileFactory *tf=NULL;
  dimension_type tileSizeRows, tileSizeCols;
  AMI_STREAM<distanceType> *b2bstr = NULL;
  AMI_STREAM<ijCost> *s2bstr = NULL;
  size_t tilemem;   /* how much memory we want for a tile */
  size_t tfmem; /* how much memory we want for the tile factory */
  size_t bndmem; /* how much memory we want for the bnd dsrt in STEP 2 */
  
  /* 
     normally we would set the tile size such that :
     tilesize*sizeof<ijCostType> + tilesize*sizeof(<costType) = avail,
     which gives tilesize = avail/(sizeof(ijCostType) +
     sizeof(<costType>)). in this case the tile factory tf
     (i.e. bndpoints) will be stored as a stream on disk and use no
     memory.
       
     we can compromise for a smaller tile and save part of the
     memory to store the tile factory (boundary points) in memory as
     well. For small N (grid size) the bnd dstrs may fit completely
     in memory and will be faster than if it was on disk.
  */
  
  /*   normally tilemem = availmem; tfmem = 0;bndmem = 0; */
  tilemem = availmem1 / 2;
  tfmem   = availmem1 / 4;
  bndmem  = availmem1 / 4;
  

  if(opt->runMode & RUN_S0) {
    stats->comment("----------------------------------------"); 
    stats->comment("STEP 0:  COMPUTE SUBSTITUTE GRAPH");
    *stats << endl;
    *stats << "Memory Available: " << memBuf << "bytes\n";
    
    /* in STEP 0/1 memory is used for: 
       - a tile<ijCostType>
       - a tileFactory structure, which is a boundary dstr of
       <costSourceType> (if ARRAY) or <ijCostType> (if STRREAM)
       - a PQ for bnd 2 bnd Dijkstra in a tile 
       - a PQ for source 2 bnd Dijkstra in a tile
       - a tile<costType>
       
       - are we forgetting anything?
    */
    
    
    /* dimension of a tile: sets tileSizeRows and tileSizeCols based
       on a user defined number of tiles */
    initializeTileSize(&tileSizeRows, &tileSizeCols, opt->numtiles);
    tsr = tileSizeRows;
    tsc = tileSizeCols;
    
    /* create a tileFactory structure that will know how to extract a
       tile from a a grid and how to iterate on tiles. */
    tf = new TileFactory(tileSizeRows, tileSizeCols, 0);
    g.ntiles = tf->getNumTiles();
    printf("Original Grid Size: (%d, %d)\n", nrows, ncols);
    printf("TF #Tiles: %d\n", g.ntiles); cout.flush();
     
    
    
    /* read input cost grid and populate tf  */
    loadGrid(opt->cost_grid,opt->source_grid, &nodata_count, tf);
    *stats <<"Total elements read=" << formatNumber(NULL, (long)nrows*ncols);
    *stats <<", nodata elements=" << formatNumber(NULL, nodata_count) <<endl;
    
    
    /* since we work internally with a padded grid, we need to add the
       padded values to bndCost and intCost */
    tf->pad();
    
    if(opt->runMode != RUN_ALL) {
      tf->serialize(resolvePath(opt->s0bnd));
      writeConfigFile(resolvePath(opt->config));
    }
  }
    
  
  /* STEP 1 */
  if(opt->runMode & RUN_S1) {
    stats->comment("----------------------------------------"); 
    stats->comment("STEP 1");
    Rtimer rtStep;   
    rt_start(rtStep);
    
    if(!(opt->runMode & RUN_S0)) {
      //step 1 was not run: restore data from disk 
      stats->comment("restoring data structures...");
      readConfigFile(resolvePath(opt->config));
      AMI_STREAM<ijCostSource> *dataStream;
      if(opt->s1fd > 0) {
	assert(0);
	//not sure what to do here; PEARL used to be
	//defined. but s1fd seems to never be set.  #ifdef
	//PEARL dataStream = new
	//AMI_STREAM<ijCostSource>(opt->s1fd,
	//AMI_READ_STREAM); #else 
	dataStream = NULL;
	//dataStream = new AMI_STREAM<ijCostSource>(opt->s1fd, AMI_READ_STREAM);
	//#endif
      } else {
	dataStream = new AMI_STREAM<ijCostSource>(resolvePath(opt->s0out), AMI_READ_STREAM);
      }
      tf = new TileFactory(tsr, tsc, dataStream, resolvePath(opt->s0bnd));
    }	// end exclusively-step1 init
    
	  
      /* this sort is a permute to get the tiles in order.  in
       * parallel version, we want to just split here; we will get the
       * sort for free within a tile.  (each tile is a separate file)
       * -RW */
    if(! opt->tilesAreSorted) {
      tf->sortTF();
    }
    if(opt->tilesAreSorted) {	// maybe this sould be a different option...
      tf->markBoundaryAsSorted();
    }
    
    /* Run Dijkstra on each tile and compute bnd2bnd SP; these will be
       stored in b2bstr; also, for each point on the bnd of
       the tile, compute SP to any source point in the tile;
       store this in s2bstr.
    */
     // set up the output streams of Step2
    if(opt->runMode != RUN_ALL) {
      b2bstr = new AMI_STREAM<distanceType>(resolvePath(opt->s1out),AMI_WRITE_STREAM);
      s2bstr = new AMI_STREAM<ijCost>(resolvePath(opt->s2bout),AMI_WRITE_STREAM);
    } else {
      b2bstr = new AMI_STREAM<distanceType>();
      s2bstr = new AMI_STREAM<ijCost>();
    }
          
    tf->reset();
    assert(s2bstr && b2bstr);
    computeSubstituteGraph(tf, b2bstr, s2bstr);
    
    // 	  if(debug) {
    // 		dump_file(b2bstr->name(), "/tmp/s1out.dump", distanceType());
    // 		dump_file(s2bstr->name(), "/tmp/s2bout.dump", ijCost());
    // 	  }
    
    //printStream(b2bstr);
    //printStream(s2bstr);
    //if(opt->runMode == RUN_S1) {
    //exit(0);
    //}
    
    rt_stop(rtStep);
    stats->recordTime("STEP1", rtStep);
  }
    
  




    /* ************************************************** */
    /* @S2 STEP 2: compute for each boundary point, the SP to any
       source. These will be stored in phase2Bnd.
       
       memory in step 2 is used to store: 
       - a boundaryClass dstr that stores SP to all bnd vertices
       - the PQ
       - an array that stores whether a point has been settled or not
       - are we forgetting anything??check !!! 
    */
  if(opt->runMode & RUN_S2) {
    stats->comment("----------------------------------------"); 
    stats->comment("STEP 2");
    Rtimer rtStep;   
    rt_start(rtStep);
    
    if(!(opt->runMode & RUN_S1)) {
      stats->comment("restoring data structures...");
      readConfigFile(resolvePath(opt->config));
      // 		tileSizeRows = tsr;
      // 		tileSizeCols = tsc;
      
      b2bstr = new AMI_STREAM<distanceType>(resolvePath(opt->s1out));
      b2bstr->persist(PERSIST_PERSISTENT);
      //cout << "b2bLen: " << b2bstr->stream_len() << endl;cout.flush();
      stats->recordLength("b2bstr ", b2bstr);
    }
    
    /* sort and rename */
    /* in the parallel version, this could be just a merge of runs. */
    cout << "Sorting b2b stream"  << endl; cout.flush();
    stats->comment("Sorting b2bstr");
    distanceIJCompareType srtFun;
    char *b2bstrname;
    b2bstr->name(&b2bstrname);
    
    if(opt->runMode == RUN_ALL) {
      sort(&b2bstr, srtFun);
    } else {
      AMI_STREAM<distanceType> *sortedStr;
      int deleteInput = 1;
      //AMI_sort(b2bstr, &sortedStr, &srtFun, deleteInput, b2bstrname);
      AMI_sort(b2bstr, &sortedStr, &srtFun, deleteInput);
      b2bstr = sortedStr;
      b2bstr->seek(0);
    }
    delete b2bstrname;
    
    rt_stop(rtStep);
    stats->recordTime("STEP2", rtStep);    
  }
  
  BoundaryType<cost_type> *phase2Bnd = NULL;
    
    
    
  /* ************************************************************ */
  /* STEP 3 */
  /* ************************************************************ */
  /* step3 = old step2 (sans big sort) and old step3 */
    if(opt->runMode & RUN_S3) {
      stats->comment("----------------------------------------"); 
      stats->comment("STEP 3");
      Rtimer rtStep;   
      rt_start(rtStep);

      if(!(opt->runMode & RUN_S2)) {
		stats->comment("restoring data structures...");
		readConfigFile(resolvePath(opt->config));
 		tileSizeRows = tsr;
 		tileSizeCols = tsc;

		AMI_STREAM<ijCostSource> *dataStream;
		dataStream = new AMI_STREAM<ijCostSource>(resolvePath(opt->s0out), AMI_READ_STREAM);
		stats->recordLength("dataStream ", dataStream);

		tf = new TileFactory(tsr, tsc, dataStream, resolvePath(opt->s0bnd));
		tf->sortTF();

		s2bstr = new AMI_STREAM<ijCost>(resolvePath(opt->s2bout));
		assert(s2bstr);
		s2bstr->persist(PERSIST_PERSISTENT);
		stats->recordLength("s2bstr ", s2bstr);
		
		b2bstr = new AMI_STREAM<distanceType>(resolvePath(opt->s1out));
		b2bstr->persist(PERSIST_PERSISTENT);
		// *stats << "b2bLen: " << b2bstr->stream_len() << endl;
		stats->recordLength("b2bstr ", b2bstr);
		
	  }
	  if(debug) {
		dump_file(b2bstr->name(), "/tmp/s1out.dump", distanceType());
		dump_file(s2bstr->name(), "/tmp/s2bout.dump", ijCost());
	  }
	
	  // ************INTER-TILE ************
	  Rtimer rtInterTile;   
	  rt_start(rtInterTile);
	  size_t availmem2, availmem3;
	  availmem2 = MM_manager.memory_available();
	  formatNumber(memBuf, availmem2);
	  stats->comment("----------------------------------------"); 
	  stats->comment("INTER TILE DIJKSTRA");
	  *stats << "Memory Available: " << memBuf << " bytes\n";
	  
	  cout << "nrowsPad: " << nrowsPad << " ncolsPad: " << ncolsPad << endl;
	  cout << "tsr: " << tsr << " tsc: " << tsc << endl;
	  cout << "tileSizeRows: " << tf->getRows() << " tileSizeCols: " 
		   << tf->getCols() << endl;
	  cout.flush();
	  
	  cerr << "creating phase2Bnd" << endl; cout.flush();
	  //the dstr to handle the distances from each boundary to a
	  //source point
	  phase2Bnd = 
		new BoundaryType<cost_type>(tileSizeRows, tileSizeCols, BND_ARRAY);

	  cout << "initializing phase2Bnd" << endl; cout.flush();
	  /* since we are using an in-memory boundary, we consult the values
	   * in updateInterNeighbors (interTileDijkstra) */
	  phase2Bnd->initialize(cost_type_max);
	  cout << "initializing phase2Bnd." << endl; cout.flush();
	  
	  *stats << "tileFactory uses " << tf->memoryUsage() << " bytes\n"; 
	  *stats << "phase2Bnd uses "<< phase2Bnd->memoryUsage()<<" bytes\n";
	  
	  availmem3 = MM_manager.memory_available();
	  formatNumber(memBuf, availmem3);
	  *stats << "Memory Available for pqueue " << memBuf << " bytes\n;";
	  assert(s2bstr);
	  cout << "inter-tile dijkstra" << endl; cout.flush();
	  interTileDijkstra(s2bstr, b2bstr, phase2Bnd, tf);
	  delete s2bstr;
      delete b2bstr;
      rt_stop(rtInterTile);
	  stats->recordTime("INTER-TILE DIJKSTRA:end", rtInterTile);
      //cerr << "main: after interTileDijkstra: phase2Bnd len=" <<
      //phase2Bnd->length() << endl;
      
	  //save structure for next step 
	  if (!(opt->runMode & RUN_S4)) {
		cout << "saving phase2Bnd\n"; cout.flush();
		phase2Bnd->serialize(resolvePath(opt->phase2Bnd));
	  }

      rt_stop(rtStep);
      stats->recordTime("STEP3", rtStep);    
	} //step3     
	
	
	
	/* ************************************************************ */
	/* STEP 4 */
	/* ************************************************************ */
	if(opt->runMode & RUN_S4) {
	  
	  //printf("runMode=%d run_s4=%d\n", opt->runMode, RUN_S4);
	  stats->comment("----------------------------------------"); 
	  stats->comment("STEP 4");
	  Rtimer rtStep;   
	  rt_start(rtStep);
	  
      /* ************************************************** */
      /* compute for each tile the SP to each point inside the
		 tile and write resulting distances to finalstr
		 
		 memory is used to store: 
		 - a tile <ijCostType>
		 - a tile <costType>
		 - a PQ
		 - a tileFactory structure, which is a boundary dstr of <ijCostType> 
		 - phase2Bnd, that is a boundary dstr of <ijCostType> 
		 
      */
	  
	  if(!(opt->runMode & RUN_S3)) {
		stats->comment("restoring data structures...");
		readConfigFile(resolvePath(opt->config));
 		tileSizeRows = tsr;
 		tileSizeCols = tsc;
		
		AMI_STREAM<ijCostSource> *dataStream;
		dataStream = new AMI_STREAM<ijCostSource>(resolvePath(opt->s0out), AMI_READ_STREAM);
		tf = new TileFactory(tsr, tsc, dataStream, resolvePath(opt->s0bnd));
		
		if(! opt->tilesAreSorted) {
		  tf->sortTF();
		}
		if(opt->tilesAreSorted) { // maybe this sould be a different option...
		  tf->markBoundaryAsSorted();
		}
		
		//phase2Bnd
		phase2Bnd = 
		  new BoundaryType<cost_type>(tileSizeRows, tileSizeCols, BND_ARRAY);
		cerr << "restoring phase2Bnd" << endl;
		phase2Bnd->reconstruct(resolvePath(opt->phase2Bnd));
		
	  } else {
		//if step3 was run just before this, then phase2Bnd should be
		//still around
		assert(phase2Bnd); 
	  }//end reconstruct

	  //this should be known at this point (either form step3 or
	  //reconstructed)
	  assert(phase2Bnd); 
	  
	  size_t availmem_i;
	  availmem_i = MM_manager.memory_available();
	  formatNumber(memBuf, availmem_i);
	  //cout << "Memory Available: " << memBuf << "\n";
	  stats->comment("----------------------------------------"); 
	  stats->comment("IN-TILE FINAL DIJKSTRA");
	  *stats << "Memory Available: " << memBuf << " bytes\n";
	  
	  
	  /* the SP(s, internal points) are dumped to finalstr */
	  AMI_STREAM<ijCost> *finalstr = new AMI_STREAM<ijCost>();
	  cerr << "finalstr = " << finalstr->name() << endl;
	  
	  Rtimer rtFinalDijkstra;
	  rt_start(rtFinalDijkstra); 
	  finalDijkstra(tf, phase2Bnd, finalstr);
	  assert(tf);
	  delete tf;
	  
	  /* sort finalstr in (i,j) order */
	  ijCostCompareType normalSort;;
	  normalSort.setTileSize(tileSizeRows,tileSizeCols);
	  sort(&finalstr, normalSort);
	  //printStream(finalstr);
	  rt_stop(rtFinalDijkstra);
	  stats->recordTime("FINAL DIJSKTRA", rtFinalDijkstra);
	  //phase2Bnd->print();
	  
	  /* write to grass grid */
	  writeToGrassFile(finalstr, phase2Bnd);
	  
	  //save to ascii file
	  if (opt->ascii) {
		stream2ascii(finalstr, phase2Bnd, resolvePath(DIST_GRID) );
	  }
	  
	  delete finalstr;
	  delete phase2Bnd;
	  size_t availmem4;
	  availmem4 = MM_manager.memory_available();
	  formatNumber(memBuf, availmem4);
	  /* note: availmem4 should be availmem1 */
	  cout << "Memory Available: " << memBuf << "\n"; cout.flush();
	  *stats << "Memory Available: " << memBuf << " bytes\n";
	  
	  rt_stop(rtStep);
	  stats->recordTime("STEP4", rtStep);    
	  
	} //step 4
	
	rt_stop(rtTotal);
	stats->recordTime("Total running time", rtTotal);
	stats->timestamp("end");
	
	
	
	/* CLEAN up */
	cout << "cleaning up\n"; cout.flush();
	free(region);
	free(opt);
	delete stats;
	cout << "r.terracost done\n"; cout.flush();
	
	return 0;
}


    
  
  

