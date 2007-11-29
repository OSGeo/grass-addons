/*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@                                                                       
@@@  Copyleft 1994 by B. Saghafian and F. L. Ogden
@@@
@@@  This program is primarily based on the two-dimensional 
@@@  rainfall-runoff model called CASC2D originally developed
@@@  by Prof. Julien in APL and later reworked and enhanced in 
@@@  Fortran by Bahram Saghafian while at Colorado State University. 
@@@  For references, see:
@@@
@@@      Julien, P. Y., and B. Saghafian, 1991, CASC2D user manual:
@@@      A two-dimensional watershed rainfall-runoff model, Civil
@@@      Engineeing Report No. CER90-91PYJ-BS-12, Colorado State
@@@      University, Fort Collins, CO.
@@@ 
@@@  and
@@@
@@@      Julien, P. Y., Saghafian, B., and F. L. Ogden, 1995, "Raster-Based 
@@@      Hydrologic Modeling of Spatially-Varied Surface Runoff", Water
@@@      Resources Bulletin, AWRA, Vol. 31, NO. 3, pp. 523-536.
@@@
@@@  The following C program has been reformulated by Bahram Saghafian based
@@@  on the original Fortran version to become part of the GRASS GIS for 
@@@  hydrologic simulations. Numerous enhancements have been added in the
@@@  transition from the original code to the current one. The implicit channel 
@@@  routing code has been developed and contributed by Dr. Fred L. Ogden, 
@@@  formerly at Colorado State University and The University of Iowa, 
@@@  now Assistant Professor of Civil and Environmental Engineering 
@@@  at the University of Connecticut, Storrs, CT.
@@@
@@@  Use of this program is allowed as long as above information is retained 
@@@  and properly acknowledged. Modifications are permitted at own risk 
@@@  provided that original developers are mentioned.
@@@  
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@*/


#include "all.h"

/*!!!!!!!!!!!!!!!!!!!!!!!!!
@@
@@ GLOBAL Common Variables
@@
@@!!!!!!!!!!!!!!!!!!!!!!!*/

int   nrows,ncols;
int   GNUM,TNUM;
double w;

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
@@
@@ GLOBAL Channel Routing Variables
@@
@@!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

int   *con_vect, *con_link, *con_node;
int   nlinks,maxnodes;
int   NODES,LINKS,NUM,NUMBPTS,NUMTBL,TBNUM;
float *qlat;

char  *channel_file,*chn_link_map,*chn_node_map;
int   chn_link_fd,chn_node_fd;
CELL  *chn_link_tmp,*chn_node_tmp;

/*!!!!!!!!!!!!!!!!!!!!!!!
@@
@@ GLOBAL Lake Variables
@@
@@!!!!!!!!!!!!!!!!!!!!!!*/

int   *lake_cat,*lake_cells;
double *lake_el, *qtolake;



/*@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@                                                          @@@@@
@@@@@                  MAIN program begins.                    @@@@@
@@@@@                                                          @@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@*/

int main (int argc, char *argv[])
{

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!
 Overland & General Variables 
!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     CELL   *init_depth_cell,
	    *mask_tmp,
	    *elev_tmp, 
	    *roughness_tmp,
	    *radar_tmp;
     int    mask_fd, elev_fd, init_depth_fd, roughness_fd;
     int    row,col,rowout,colout;
     int    itime,niter,nitrn,jj,kk,l;
     int    rindex;
     int    yes_rg_mmhr;
     int    yes_mask;
     int    yes_dist_rough;
     int    yes_flow_out,set_flow_out_basin;
     int    yes_quiet,yes_english_unit;
     int    yes_gage,yes_radar,yes_thiessen,nread,rread,igage,nrg,icall;
     int    dtt,gdt,radt,totime,raintime;
     int    coindex;

     double dt;
     double rman,crain,eastout,northout,sout,hov;    
     double vin,dvin,vsur1,vsur2,vout,vintercep,vinftot,qoutov,vout_region;
     double alfaovout,hout,elunit;
     double wunit,uvol;
     double sqrt(),pow(),base,power;
     double tmpeast,tmpnorth;
     double dmin;

     int    **mask;
     float  *elev,*rough;
     float  *h,*dqov;
     float  *rint,rainrate;
     int    *grow,*gcol;
     double *rgint;
     char   *mask_map, *elev_map, *init_depth_map, *roughness_map,
            *discharge_file,*raingage_file;
     char   *mapset;
     char   buf[256];
     FILE   *discharge_fd,*rain_fd;

     int    **space;
     int    vect,vect2,vectout;
     double tpeak,qpeak;

     struct Cell_head window;
      
/*!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Infiltration Variables 
!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     CELL   *soil_K_cell,
	    *soil_H_cell,
	    *soil_P_cell,
            *soil_M_cell,
	    *soil_LN_cell,
	    *soil_RS_cell;
     int    soil_K_fd, soil_H_fd, soil_P_fd, soil_M_fd;
     int    soil_LN_fd, soil_RS_fd;
     int    yes_inf, yes_redist_cons, yes_redist_vary;
     float  *vinf;   
     int    *iter_pond_1,*iter_n,*no_wat_prof;
     int    *iter_i_less_k; 
     float  *frate;
     float  *teta_n,*vinf_n,*surf_moist;
     char   *soil_K_map, *soil_H_map,*soil_P_map,*soil_M_map,
	    *soil_LN_map,*soil_RS_map;
     float  *K,*H,*M,*P,*LN,*RS;

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Interception Variables
!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     CELL   *storage_cap_cell,*intercep_exp_cell;
     int    yes_intercep;
     int    storage_cap_fd,intercep_exp_fd;
     float  *Inter,*sv,*exp,intrate;
     char   *storage_cap_map,*intercep_exp_map;

                        /* sv=storage capacity of vegetation
                         * exp=interception coefficient in interception 
                         * equation */

/*!!!!!!!!!!!!!!!!!!!!!!!!!
  Lake Variables
!!!!!!!!!!!!!!!!!!!!!!!!!*/

     CELL   *lake_tmp, *lake_el_tmp;
     int    yes_lake,lake_cat_fd,lake_el_fd,nlake,ilake;
     double *check;
     double lake_elunit,vlake1,vlake2;
     char   *lake_cat_map, *lake_el_map;
     int    *lake_type;

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Map-Writing/Reading Variables 
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     CELL   *depth_tmp,
	    *inf_tmp,
	    *surf_moist_tmp,
	    *inf_rate_tmp,
	    *dis_rain_tmp;
     int    *radar_fd;
     int    *depth_fd,*inf_fd,*surf_moist_fd,*inf_rate_fd,*dis_rain_fd;
     int    yes_write,yes_w_surf_dep,yes_w_inf_dep;
     int    yes_w_inf_rate,yes_w_surf_moist;
     int    yes_w_dis_rain,writime,num_w,nfile,ndigit,rdigit;
     int    windex;
     char   *depth_file[2000], *inf_dep_file[2000], *surf_moist_file[2000],
	    *inf_rate_file[2000],*dis_rain_file[2000];
     char   *radar_file[10000];

     struct Colors colors;

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Explicit Channel Variables 
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     int    link,node;
     int    yes_channel,yes_chn_unif;
     int    row1,col1,row2,col2,linkout,nodeout;
     float  *dqch,*hch;
     int    *chn_row;
     int    *chn_col;
     double wid,depth,z,dhch,qtoch,htop;
     double elev1,elev2;
     double manout,wetpout,areaout,qoutch,qout;

     int    itmp,nodetmp;
     double dummy;

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Implicit (Priessman) Channel Variables 
  Some are shared between Implicit and explicit
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     int   yes_priess,yes_drain,yes_bkwater,yes_table=0;
     float flowd,D;
     float grav,theta,delt,delx;
     float tt;
     int   iter;
     int   *ndep;

     float *yp,*qp;

     float yfirst = 0.0,ystep = 0.0;
     float *bottom,*bel,*sslope,*sslope2,
	   alpha,beta,*strick;
     float *marea0,*parea0,*mtw0,*ptw0,*mk0,*pk0;
     float *marea1,*parea1,*mtw1,*ptw1,*mk1,*pk1;
     int   *depend,*backdep,*ltype;
     int   *nx1;

     FILE  *iunit = NULL,*yunit = NULL,*qunit = NULL;
     FILE  *iunit9 = NULL,*phydunit = NULL;
     char  *phyd_file,*hydout_file,*qprof_file,*yprof_file;
     char  *table_file;
     int   eocheck;

     float *chn_dep;

     int   yes_phyd,*plink,*pnode,ptot;

     int   *numqpipe;      /* These are added for riser 
			    * pipe reservoir outlets
			    */
     /* these variables were added to accomodate break point channel
	cross section description.  F.L. Ogden 10-8-94          */

     float *xarea,*xtw,*xk,*ht_spc;
     int *numhts,maxtab,*table_num;
     FILE *tunit;

     /* these were added as dummy vectors for mass balance computations
        when calling section subroutine directly. BS 6-5-94 */

     float *farea,*dum1,*dum2,*dum3;

     /* these variables were added to incorporate drain function */

     float highspot,lowspot,tdrain,qmin,normout;

/*!!!!!!!!!!!!!!!!!!!!!!!!!!
  GRASS Options and Flags
!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     struct
     {
          struct Option *mask_wat, *elevation, *init_depth, 
	  *roughness, *soil_K, *soil_H, *soil_P, *soil_M, 
	  *soil_LN, *soil_RS, *lake_map_name, *lake_elevation, 
	  *chn_link, *chn_node, *channel,*discharge, *raingage, 
	  *depth, *inf, *moist, *rate, *dis_rain, *time_step, 
	  *Manning_n, *unif_rain, *outlet, *num_time,*num_rain, 
	  *gage_time_step, *radar_map, *radar_time_step, 
	  *num_raingage, *num_write, *elevation_unit,
	  *lake_unit, *threshold, *space_unit, *storage_cap, 
	  *intercep_exp, *phyd, *qprof, *yprof, *hydout, *table;
       }  parm;

     struct
     {
	  struct Flag  *s,*m,*o,*t,*e,*i,*p,*u,*q,*d,*b;
     }  flag;
     struct GModule *module;

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  DEFINING GRASS COMMAND LINE PARAMETERS
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     G_gisinit (argv[0]);
     
     /* Set description */
     module              = G_define_module();
     module->description = ""\
     "Fully integrated distributed cascaded 2D hydrologic modeling.";
     
     parm.mask_wat=G_define_option();
     parm.mask_wat-> key       ="watershed_mask";
     parm.mask_wat-> type      = TYPE_STRING;
     parm.mask_wat-> required  = NO;
     parm.mask_wat-> gisprompt ="old,cell,raster";
     parm.mask_wat-> description="map of watershed boundary (or mask); recommended";
    
     parm.elevation=G_define_option();
     parm.elevation-> key       ="elevation";
     parm.elevation-> type      = TYPE_STRING;
     parm.elevation-> required  = YES;
     parm.elevation-> gisprompt ="old,cell,raster";
     parm.elevation-> description="map of elevation";

     parm.init_depth=G_define_option();
     parm.init_depth-> key       ="initial_depth";
     parm.init_depth-> type      = TYPE_STRING;
     parm.init_depth-> required  = NO;
     parm.init_depth-> gisprompt ="old,cell,raster";
     parm.init_depth-> description="map of initial overland (not lakes) depth in mm";    

     parm.storage_cap=G_define_option();
     parm.storage_cap-> key       ="storage_capacity";
     parm.storage_cap-> type      = TYPE_STRING;
     parm.storage_cap-> required  = NO;
     parm.storage_cap-> gisprompt ="old,cell,raster";
     parm.storage_cap-> description="map of vegetation storage capacity in tenths of mm";    

     parm.intercep_exp=G_define_option();
     parm.intercep_exp-> key       ="interception_coefficient";
     parm.intercep_exp-> type      = TYPE_STRING;
     parm.intercep_exp-> required  = NO;
     parm.intercep_exp-> gisprompt ="old,cell,raster";
     parm.intercep_exp-> description="map of interception coefficient (values in 1000*actual coefficient)";    

     parm.roughness=G_define_option();
     parm.roughness-> key       ="roughness_map";
     parm.roughness-> type      = TYPE_STRING;
     parm.roughness-> required  = NO;
     parm.roughness-> gisprompt ="old,cell,raster";
     parm.roughness-> description="map of surface roughness coefficient (values in 1000*Manning n)";

     parm.soil_K=G_define_option();
     parm.soil_K-> key       ="conductivity";
     parm.soil_K-> type      = TYPE_STRING;
     parm.soil_K-> required  = NO;
     parm.soil_K-> gisprompt ="old,cell,raster";
     parm.soil_K-> description="map of soil saturated hydraulic conductivity in tenths of mm/hr";    

     parm.soil_H=G_define_option();
     parm.soil_H-> key       ="capillary";
     parm.soil_H-> type      = TYPE_STRING;
     parm.soil_H-> required  = NO;
     parm.soil_H-> gisprompt ="old,cell,raster";
     parm.soil_H-> description="map of soil capillary pressure head at the wetting front in tenths of mm";    

     parm.soil_P=G_define_option();
     parm.soil_P-> key       ="porosity";
     parm.soil_P-> type      = TYPE_STRING;
     parm.soil_P-> required  = NO;
     parm.soil_P-> gisprompt ="old,cell,raster";
     parm.soil_P-> description="map of soil effective porosity (values in 1000*porosirty)";    

     parm.soil_M=G_define_option();
     parm.soil_M-> key       ="moisture";
     parm.soil_M-> type      = TYPE_STRING;
     parm.soil_M-> required  = NO;
     parm.soil_M-> gisprompt ="old,cell,raster";
     parm.soil_M-> description="map of soil initial moisture (values in 1000*moisture)";    
     parm.soil_LN=G_define_option();
     parm.soil_LN-> key       ="pore_index";
     parm.soil_LN-> type      = TYPE_STRING;
     parm.soil_LN-> required  = NO;
     parm.soil_LN-> gisprompt ="old,cell,raster";
     parm.soil_LN-> description="map of soil pore-size distribution index (Brooks-Corey lambda) in 1000*index";    

     parm.soil_RS=G_define_option();
     parm.soil_RS-> key       ="residual_sat";
     parm.soil_RS-> type      = TYPE_STRING;
     parm.soil_RS-> required  = NO;
     parm.soil_RS-> gisprompt ="old,cell,raster";
     parm.soil_RS-> description="map of soil residual saturation (values in 1000*residual saturation)";    

     parm.lake_map_name=G_define_option();
     parm.lake_map_name-> key       ="lake_map";
     parm.lake_map_name-> type      = TYPE_STRING;
     parm.lake_map_name-> required  = NO;
     parm.lake_map_name-> gisprompt ="old,cell,raster";
     parm.lake_map_name-> description="map of lakes categories";    

     parm.lake_elevation=G_define_option();
     parm.lake_elevation-> key       ="lake_elev";
     parm.lake_elevation-> type      = TYPE_STRING;
     parm.lake_elevation-> required  = NO;
     parm.lake_elevation-> gisprompt ="old,cell,raster";
     parm.lake_elevation-> description="map of lakes initial water surface elevation (for unit see unit_lake)";    

     parm.radar_map=G_define_option();
     parm.radar_map-> key       ="radar_intensity_map";
     parm.radar_map-> type      = TYPE_STRING;
     parm.radar_map-> required  = NO;
     parm.radar_map-> gisprompt ="old,cell,raster";
     parm.radar_map-> description="map of radar- (or otherwise-) generated time series of rainfall intensity in mm/hr";    

     parm.chn_link=G_define_option();
     parm.chn_link-> key       ="links_map";
     parm.chn_link-> type      = TYPE_STRING;
     parm.chn_link-> required  = NO;
     parm.chn_link-> gisprompt ="old,cell,raster";
     parm.chn_link-> description="map of channel network link numbers";    

     parm.chn_node=G_define_option();
     parm.chn_node-> key       ="nodes_map";
     parm.chn_node-> type      = TYPE_STRING;
     parm.chn_node-> required  = NO;
     parm.chn_node-> gisprompt ="old,cell,raster";
     parm.chn_node-> description="map of channel network node numbers";    

     parm.channel=G_define_option();
     parm.channel-> key       ="channel_input";
     parm.channel-> type      = TYPE_STRING;
     parm.channel-> required  = NO;
     parm.channel-> description="channel input data file name (ASCII)";    

     parm.table=G_define_option();
     parm.table-> key       ="table_input";
     parm.table-> type      = TYPE_STRING;
     parm.table-> required  = NO;
     parm.table-> description="look-up table file for links with breakpoint cross section (ASCII)";

     parm.qprof=G_define_option();
     parm.qprof-> key       ="dis_profile";
     parm.qprof-> type      = TYPE_STRING;
     parm.qprof-> required  = NO;
     parm.qprof-> description="channel initial discharge profile file name (ASCII)";    

     parm.yprof=G_define_option();
     parm.yprof-> key       ="wat_surf_profile";
     parm.yprof-> type      = TYPE_STRING;
     parm.yprof-> required  = NO;
     parm.yprof-> description="channel intial water surface profile file name (ASCII)";    

     parm.phyd=G_define_option();
     parm.phyd-> key       ="hyd_location";
     parm.phyd-> type      = TYPE_STRING;
     parm.phyd-> required  = NO;
     parm.phyd-> description="file name containing link and node addresses of internal locations where discharge hydrographs are to be saved (ASCII)";

     parm.raingage=G_define_option();
     parm.raingage-> key       ="r_gage_file";
     parm.raingage-> type      = TYPE_STRING;
     parm.raingage-> required  = NO;
     parm.raingage-> description="raingage rainfall input file name (ASCII), intensities in in/hr";

     parm.outlet=G_define_option();
     /* removed & in parameter definition, Andreas Lange, 11/2000 */
     parm.outlet-> key       ="outlet_eastNnorthNslope";
     parm.outlet-> type      = TYPE_DOUBLE;
     parm.outlet-> required  = YES;
     parm.outlet-> key_desc  ="east,north,bedslope";  
     parm.outlet-> description="easting, northing, and bed slope at the outlet cell";

     parm.Manning_n=G_define_option();
     parm.Manning_n-> key       ="Manning_n";
     parm.Manning_n-> type      = TYPE_DOUBLE;
     parm.Manning_n-> required  = NO;
     parm.Manning_n-> description="spatially uniform overland Manning n roughness value";

     parm.unif_rain=G_define_option();
     parm.unif_rain-> key       ="unif_rain_int";
     parm.unif_rain-> type      = TYPE_DOUBLE;
     parm.unif_rain-> required  = NO;
     parm.unif_rain-> description="spatially uniform rainfall intensity in mm/hr";

     parm.num_raingage=G_define_option();
     parm.num_raingage-> key       ="num_of_raingages";
     parm.num_raingage-> type      = TYPE_INTEGER;
     parm.num_raingage-> required  = NO;
     parm.num_raingage-> description="number of recording raingages";

     parm.time_step=G_define_option();
     parm.time_step-> key       ="time_step";
     parm.time_step-> type      = TYPE_INTEGER;
     parm.time_step-> required  = YES;
     parm.time_step-> description="computational time step duration in sec";

     parm.gage_time_step=G_define_option();
     parm.gage_time_step-> key       ="gage_time_step";
     parm.gage_time_step-> type      = TYPE_INTEGER;
     parm.gage_time_step-> required  = NO;
     parm.gage_time_step-> description= "time step of recorded raingage data in sec";

     parm.radar_time_step=G_define_option();
     parm.radar_time_step-> key       ="radar_time_step";
     parm.radar_time_step-> type      = TYPE_INTEGER;
     parm.radar_time_step-> required  = NO;
     parm.radar_time_step-> description= "time increment between radar- (or otherwise) generated rainfall maps in sec";

     parm.num_rain=G_define_option();
     parm.num_rain-> key       ="rain_duration";
     parm.num_rain-> type      = TYPE_INTEGER;
     parm.num_rain-> required  = YES;
     parm.num_rain-> description= "total rainfall duration in sec";

     parm.num_time=G_define_option();
     parm.num_time-> key       ="tot_time";
     parm.num_time-> type      = TYPE_INTEGER;
     parm.num_time-> required  = YES;
     parm.num_time-> description="total simulation time or channel drainage time (-d option) in sec";

     parm.num_write=G_define_option();
     parm.num_write-> key       ="write_time_step";
     parm.num_write-> type      = TYPE_INTEGER;
     parm.num_write-> required  = NO;
     parm.num_write-> description="time increment for writing output raster maps in sec";

     parm.elevation_unit=G_define_option();
     parm.elevation_unit-> key       ="unit_el_conv";
     parm.elevation_unit-> type      = TYPE_DOUBLE;
     parm.elevation_unit-> required  = NO;
     parm.elevation_unit-> description="unit convertion factor by which the values in elevation map must be DIVIDED to convert them into meters";

     parm.lake_unit=G_define_option();
     parm.lake_unit-> key       ="unit_lake";
     parm.lake_unit-> type      = TYPE_DOUBLE;
     parm.lake_unit-> required  = NO;
     parm.lake_unit-> description="unit convertion factor by which the values in lake surface elevation map must be DIVIDED to convert them into meters";

     parm.space_unit=G_define_option();
     parm.space_unit-> key       ="unit_space";
     parm.space_unit-> type      = TYPE_DOUBLE;
     parm.space_unit-> required  = NO;
     parm.space_unit-> description="unit convertion factor by which the region easting and northing values must be DIVIDED to convert them into meters";

     parm.threshold=G_define_option();
     parm.threshold-> key       ="d_thresh";
     parm.threshold-> type      = TYPE_DOUBLE;
     parm.threshold-> required  = NO;
     parm.threshold-> description="threshold overland depth, in meters, below which overland routing will not be performed (i.e. average depression storage)";

     parm.discharge=G_define_option();
     parm.discharge-> key       ="discharge";
     parm.discharge-> type      = TYPE_STRING;
     parm.discharge-> required  = YES;
     parm.discharge-> description="outflow discharge output file name (ASCII)";

     parm.hydout=G_define_option();
     parm.hydout-> key       ="dis_hyd_location";
     parm.hydout-> type      = TYPE_STRING;
     parm.hydout-> required  = NO;
     parm.hydout-> description="output file name for discharge hydrograph at internal locations (ASCII)";

     parm.depth=G_define_option();
     parm.depth-> key       ="depth_map";
     parm.depth-> type      = TYPE_STRING;
     parm.depth-> required  = NO;
     parm.depth-> description="output map of surface depth in mm";

     parm.inf=G_define_option();
     parm.inf-> key       ="inf_depth_map";
     parm.inf-> type      = TYPE_STRING;
     parm.inf-> required  = NO;
     parm.inf-> description="output map of cumulative infiltration depth in tenth of mm";

     parm.moist=G_define_option();
     parm.moist-> key       ="surf_moist_map";
     parm.moist-> type      = TYPE_STRING;
     parm.moist-> required  = NO;
     parm.moist-> description="output map of surface soil moisture in number of fractions of a thousand";

     parm.rate=G_define_option();
     parm.rate-> key       ="rate_of_infil_map";
     parm.rate-> type      = TYPE_STRING;
     parm.rate-> required  = NO;
     parm.rate-> description="output map of infiltration rate in mm/hr";

     parm.dis_rain=G_define_option();
     parm.dis_rain-> key       ="dis_rain_map";
     parm.dis_rain-> type      = TYPE_STRING;
     parm.dis_rain-> required  = NO;
     parm.dis_rain-> description="output map of distributed rainfall intensity in mm/hr";

/*!!!!!!!!!!!!!!!!!!!
  DEFINING FLAGS 
!!!!!!!!!!!!!!!!!!!*/

     flag.s=G_define_flag();
     flag.s->key         = 's';
     flag.s->description ="do not check square tolerance";

     flag.m=G_define_flag();
     flag.m->key         = 'm';
     flag.m->description ="r_gage_file units in mm/hr";

     flag.t=G_define_flag();
     flag.t->key         = 't';
     flag.t->description ="interpolates raingage rainfall intensities using Thiessen polygon technique (default: inverse square distance)";

     flag.o=G_define_flag();
     flag.o->key         = 'o';
     flag.o->description ="routes edge-accmulated overland flow out of active region (ONLY when no mask is specified)";

     flag.e=G_define_flag();
     flag.e->key         = 'e';
     flag.e->description ="performs explicit channel routing";

     flag.p=G_define_flag();
     flag.p->key         = 'p';
     flag.p->description ="assumes uniform channel geometry in each link (needs -e option)";

     flag.i=G_define_flag();
     flag.i->key         = 'i';
     flag.i->description ="performs Priessman double sweep implicit channel routing";

     flag.d=G_define_flag();
     flag.d->key         = 'd';
     flag.d->description ="performs only drainage of the basin for implicit routing by flooding the basin";

     flag.b=G_define_flag();
     flag.b->key         = 'b';
     flag.b->description ="determines initial flow depths for implicit routing by  performinf standard step backwater computations";

     flag.u=G_define_flag();
     flag.u->key         = 'u';
     flag.u->description ="print discharges in cfs and volumes in cubic ft";

     flag.q=G_define_flag();
     flag.q->key         = 'q';
     flag.q->description ="skips printing iteration, time, and discharge values to the screen";

     if(G_parser(argc,argv)) exit(1);

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  READING COMMAND LINE VARIABLES
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     fprintf(stderr,"     r.hydro.CASC2D \n     Version 1.00 8/1995 Copyleft by B. Saghafian and F. L. Ogden \n\n");

     sscanf(parm.outlet->answer,"%lf,%lf,%lf", &eastout, &northout, &sout);
     sscanf(parm.time_step->answer,"%i", &dtt);
     sscanf(parm.num_rain->answer,"%i", &raintime);
     sscanf(parm.num_time->answer,"%i", &totime);

     if(parm.elevation_unit->answer == NULL) 
     {
	elunit=1.0;
     }
     else 
     {
        sscanf(parm.elevation_unit->answer,"%lf", &elunit);
     }

     if(parm.lake_unit->answer == NULL) 
     {
	lake_elunit=1.0;
     }
     else 
     {
        sscanf(parm.lake_unit->answer,"%lf", &lake_elunit);
     }

     if(parm.threshold->answer == NULL) 
     {
	dmin=0.0;
     }
     else 
     {
        sscanf(parm.threshold->answer,"%lf", &dmin);
     }

     if(parm.space_unit->answer == NULL) 
     {
	wunit=1.0;
     }
     else 
     {
        sscanf(parm.space_unit->answer,"%lf", &wunit);
     }

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  PROCESSING FLAGS and/or OTHER OPTIONS
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     yes_radar=FALSE;
     if(parm.radar_map->answer != NULL) 
     {
	yes_radar=TRUE;
        if(parm.radar_time_step->answer == NULL) 
	{
	   sprintf(buf,"radar time step is not specified\n");
	   G_fatal_error(buf);
	   exit(1);
        }
	else
	{
	   sscanf(parm.radar_time_step->answer,"%d", &radt); 
        }
     }

     yes_gage=FALSE;
     if(parm.raingage->answer != NULL) yes_gage=TRUE;
     yes_thiessen=flag.t->answer;
     if(!yes_radar)
     {
     if(!yes_gage) 
     {
        if(parm.unif_rain->answer == NULL) 
	{
          sprintf(buf,"ERROR: Niether raingage rainfall file nor constant rainfall intensity is provided\n");
          G_fatal_error(buf);
          exit(1);
        }
        sscanf(parm.unif_rain->answer,"%lf", &crain);
	crain=crain/(1000.*3600.);   /* change unit from mm/hr to m/sec */
     }
     else 
     {
	if(parm.gage_time_step->answer == NULL) 
	{
          sprintf(buf,"raingage rainfall time interval is not provided\n");
          G_fatal_error(buf);
          exit(1);
	}
	if(parm.num_raingage->answer == NULL) 
	{
          sprintf(buf,"number of raingages is not provided\n");
          G_fatal_error(buf);
          exit(1);
        }
        sscanf(parm.gage_time_step->answer,"%d", &gdt);
        sscanf(parm.num_raingage->answer,"%d", &nrg);
     }
     }

     if(yes_radar)
     {
	if(yes_gage)
	{
	   sprintf(buf,"ERROR: Either raingage or radar rainfall can be simulated not both\n");
	   G_fatal_error(buf);
	   exit(1);
        }
	else
	{
	   if(parm.unif_rain->answer != NULL)
	   {
	      sprintf(buf,"ERROR: Either radar or uniform rainfall can be simulated ot both\n");
	      G_fatal_error(buf);
	      exit(1);
           }
        }
     }

     yes_write=FALSE;
     if(parm.num_write->answer != NULL) 
     {
	yes_write=TRUE;
	sscanf(parm.num_write->answer,"%i", &writime);
     }

     yes_rg_mmhr=flag.m->answer;

     yes_flow_out=flag.o->answer;

     yes_channel=flag.e->answer;

     yes_priess=flag.i->answer;

     yes_drain=flag.d->answer;

     yes_bkwater=flag.b->answer;

     yes_chn_unif=flag.p->answer;

     yes_english_unit=flag.u->answer;

     yes_quiet=flag.q->answer;

     if(yes_drain && yes_bkwater) 
     {
       fprintf(stderr,"Either -d or -b flags may be set not both.\n");
       exit(-2);
     }

     if((yes_drain || yes_bkwater) && !yes_priess)
     {
       fprintf(stderr,"You must use flag -i with either -d or -b flags.\n");
       exit(-2);
     }

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Checking Main Maps
!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

/* 
 * mask map
 */

     yes_mask=FALSE;
     if( (mask_map = parm.mask_wat->answer) != NULL) 
     {
	yes_mask=TRUE;
        mapset = G_find_cell(mask_map,"");
        if(!mapset)
        {
        sprintf(buf,"watershed mask map [%s] not found\n", mask_map);
        G_fatal_error(buf);
        exit(1);
        }

        if((mask_fd=G_open_cell_old(mask_map,mapset))<0)
        {
           sprintf(buf,"cannot open watershed map file\n");
           G_fatal_error(buf);
           exit(1);
        }
     }
     if(yes_mask && yes_flow_out) 
     {
	fprintf(stderr, "ERROR: The -o flag may ONLY be used when the watershed boundary map (mask) is NOT specified.\n");
	exit(1);
     }

/*
 * elevation map
 */

     elev_map = parm.elevation->answer;
     mapset = G_find_cell(elev_map,"");
     if(!mapset)
     {
       sprintf(buf,"elevation map file [%s] not found\n", elev_map);
       G_fatal_error(buf);
       exit(1);
     }
     if((elev_fd=G_open_cell_old(elev_map,mapset))<0)      
     {
        sprintf(buf,"cannot open elevation file\n");
        G_fatal_error(buf);
        exit(1);
     }

     if(yes_mask) mask_tmp=G_allocate_cell_buf();

     elev_tmp=G_allocate_cell_buf();

/* 
 * initial depth map
 */

     init_depth_map=parm.init_depth->answer;
     if(init_depth_map != NULL)
     {
          mapset=G_find_cell(init_depth_map,"");

          if((init_depth_fd=G_open_cell_old(init_depth_map,mapset))<0)
          {
             sprintf(buf,"cannot open initial depth file\n");
             G_fatal_error(buf);
	     exit(1);
          }

          init_depth_cell=G_allocate_cell_buf();
     }
     else
     {
          init_depth_fd = -1;
     }

/*
 * Checking for either roughness map or uniform roughness value 
 */

     if(parm.roughness->answer != NULL && parm.Manning_n->answer != NULL) 
     {
        sprintf(buf,"Provide EITHER the overland roughness map OR the overland uniform Manning n value, NOT both.\n");
        G_fatal_error(buf);
        exit(1);
     }
     if(parm.roughness->answer == NULL && parm.Manning_n->answer == NULL) 
     {
        sprintf(buf,"You must provide EITHER the roughness map OR the uniform Manning n value.\n");
        G_fatal_error(buf);
        exit(1);
     }
	
     yes_dist_rough=FALSE;
     if(parm.roughness->answer != NULL) 
     {
	yes_dist_rough=TRUE;
        roughness_map = parm.roughness->answer;
        mapset = G_find_cell(roughness_map,"");
        if(!mapset) 
	{
           sprintf(buf," roughness map [%s] not found\n", roughness_map);
           G_fatal_error(buf);
           exit(1);
        }

        if((roughness_fd=G_open_cell_old(roughness_map,mapset))<0)
        {
           sprintf(buf,"cannot open [%s] map\n",roughness_map);
           G_fatal_error(buf);
           exit(1);
        }

        roughness_tmp=G_allocate_cell_buf();
	fprintf(stderr,"Spatially distributed roughness from [%s] map is modeled.\n",roughness_map);
     }
     else 
     {
	sscanf(parm.Manning_n->answer,"%lf", &rman);
	fprintf(stderr,"Uniform roughness value of [%f] is modeled.\n",rman);
     }

/*
 * Checking for the raingage ascii file 
 */

     if(yes_gage) 
     {
        raingage_file=parm.raingage->answer;
        if((rain_fd=fopen(raingage_file,"r")) == NULL) 
	{
          sprintf(buf,"cannot open [%s] ascii file\n",raingage_file);
          G_fatal_error(buf);
          exit(1);
        }
        grow=(int*) malloc(nrg*sizeof(int));
        gcol=(int*) malloc(nrg*sizeof(int));
	if((rgint=(double*) malloc(nrg*sizeof(double))) == NULL) fprintf(stderr,"cannot allocate memory for intensity array of raingage rainfall");
        fprintf(stderr,"Raingage rainfall intensities is modeled.\n");
     }

/*
 * Checking for interception maps 
 */
     
     yes_intercep=FALSE;
     storage_cap_map=parm.storage_cap->answer;
     intercep_exp_map=parm.intercep_exp->answer;
     if(storage_cap_map != NULL || intercep_exp_map != NULL) yes_intercep=TRUE;
     if(yes_intercep)
     {
	fprintf(stderr,"Interception losses will be computed\n");
	if(storage_cap_map == NULL) 
	{
           sprintf(buf,"vegetation's storage capacity file name is not provided");
	   G_fatal_error(buf);
	   exit(1);
        }
	if(intercep_exp_map == NULL)
	{
	   sprintf(buf,"interception exponent file name is not provided");
	   G_fatal_error(buf);
	   exit(1);
        }

	mapset=G_find_cell(storage_cap_map,"");
	if(!mapset) 
	{
	   sprintf(buf,"vegetation's storage capacity map [%s] not found\n",storage_cap_map);
	   G_fatal_error(buf);
	   exit(1);
	}
        if((storage_cap_fd=G_open_cell_old(storage_cap_map, mapset))<0) 
	{
	   sprintf(buf,"cannot open [%s] file\n",storage_cap_map);
           G_fatal_error(buf);
	   exit(1);
	}

	mapset=G_find_cell(intercep_exp_map,"");
	if(!mapset) 
	{
	   sprintf(buf,"interception exponent map [%s] not found\n",intercep_exp_map);
	   G_fatal_error(buf);
	   exit(1);
        }
        if((intercep_exp_fd=G_open_cell_old(intercep_exp_map, mapset))<0) 
	{
	   sprintf(buf,"cannot open [%s] file\n",intercep_exp_map);
           G_fatal_error(buf);
	   exit(1);
	}

	storage_cap_cell=G_allocate_cell_buf();
	intercep_exp_cell=G_allocate_cell_buf();
     }

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!                                !!!!
!!!!  Checking for the SOIL maps    !!!!
!!!!                                !!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     yes_inf=FALSE;
     soil_K_map=parm.soil_K->answer;
     soil_H_map=parm.soil_H->answer;
     soil_P_map=parm.soil_P->answer;
     soil_M_map=parm.soil_M->answer;

     if(soil_K_map!=NULL || soil_H_map!=NULL || soil_P_map!=NULL ||
	soil_M_map!=NULL) yes_inf=TRUE;
     if(yes_inf) 
     {
       fprintf(stderr,"Infiltration losses will be computed\n");
       if(soil_K_map == NULL) 
       { 
	 sprintf(buf,"soil saturated hydraulic conductivity map name is not provided");
         G_fatal_error(buf);
	 exit(1);
       }
       if(soil_H_map == NULL) 
       { 
  	 sprintf(buf,"soil capillary pressure map name is not provided");
         G_fatal_error(buf);
         exit(1);
       }
       if(soil_P_map == NULL) 
       { 
         sprintf(buf,"soil effective porosity map name is not provided");
         G_fatal_error(buf);
         exit(1);
       }
       if(soil_M_map == NULL) 
       { 
         sprintf(buf,"soil moisture map name is not provided");
         G_fatal_error(buf);
         exit(1);
       }

       mapset=G_find_cell(soil_K_map,"");
       if(!mapset) 
       {
         sprintf(buf,"saturated hydraulic conductivity map [%s] not found\n", soil_K_map);
         G_fatal_error(buf);
         exit(1);
       }

       if((soil_K_fd=G_open_cell_old(soil_K_map, mapset))<0) 
       {
         sprintf(buf,"cannot open [%s] map\n",soil_K_map);
         G_fatal_error(buf);
         exit(1);
       }

       mapset=G_find_cell(soil_H_map,"");
       if(!mapset) 
       {
         sprintf(buf,"capillary pressure head map [%s] not found\n", soil_H_map);
         G_fatal_error(buf);
         exit(1);
       }
       if((soil_H_fd=G_open_cell_old(soil_H_map, mapset))<0) 
       {
         sprintf(buf,"cannot open [%s] map\n",soil_H_map);
         G_fatal_error(buf);
         exit(1);
       }

       mapset=G_find_cell(soil_P_map,"");
       if(!mapset) 
       {
         sprintf(buf,"effective porosity map [%s] not found\n", soil_P_map);
         G_fatal_error(buf);
         exit(1);
       }
       if((soil_P_fd=G_open_cell_old(soil_P_map, mapset))<0) 
       {
         sprintf(buf,"cannot open [%s] map\n",soil_P_map);
         G_fatal_error(buf);
         exit(1);
       }

       mapset=G_find_cell(soil_M_map,"");
       if(!mapset) 
       {
         sprintf(buf,"initial soil moisture map [%s] not found\n", soil_M_map);
         G_fatal_error(buf);
         exit(1);
       }
       if((soil_M_fd=G_open_cell_old(soil_M_map, mapset))<0) 
       {
         sprintf(buf,"cannot open [%s] map\n",soil_M_map);
         G_fatal_error(buf);
         exit(1);
       }

       soil_K_cell=G_allocate_cell_buf();
       soil_H_cell=G_allocate_cell_buf();
       soil_P_cell=G_allocate_cell_buf();
       soil_M_cell=G_allocate_cell_buf();
     }

/*
 *  Checking for the other soil parameter files 
 *  when redistribution is modeled.
 */

     yes_redist_vary=FALSE;
     soil_LN_map=parm.soil_LN->answer;
     soil_RS_map=parm.soil_RS->answer;
     if(soil_LN_map!=NULL || soil_RS_map!=NULL) 
     {
	yes_redist_vary=TRUE;
	if(yes_inf == FALSE) sprintf(buf,"ERROR: While soil moisture redistribution is sought other infiltration maps are not provided.\n");
	G_fatal_error(buf);
	exit(1);
     }

     if(yes_redist_vary) 
     {
       fprintf(stderr,"Soil moisture redistribution based on soil pore-size distribution index and soil residual saturation maps will be modeled\n");

       if(soil_LN_map == NULL) 
       { 
         sprintf(buf,"soil pore-size distribution index map name is not provided");
         G_fatal_error(buf);
         exit(1);
       }
  
       if(soil_RS_map == NULL) 
       { 
         sprintf(buf,"soil residual saturation file name is not provided");
         G_fatal_error(buf);
         exit(1);
       }
  
       mapset=G_find_cell(soil_LN_map,"");
       if(!mapset) 
       {
         sprintf(buf,"pore-size distribution index map [%s] not found\n", soil_LN_map);
         G_fatal_error(buf);
         exit(1);
       }
       if((soil_LN_fd=G_open_cell_old(soil_LN_map, mapset))<0) 
       {
         sprintf(buf,"cannot open [%s] map\n",soil_LN_map);
         G_fatal_error(buf);
         exit(1);
       }

       mapset=G_find_cell(soil_RS_map,"");
       if(!mapset) 
       {
         sprintf(buf,"residual saturation map [%s] not found\n", soil_RS_map);
         G_fatal_error(buf);
         exit(1);
       }
       if((soil_RS_fd=G_open_cell_old(soil_RS_map, mapset))<0) 
       {
         sprintf(buf,"cannot open [%s] map\n",soil_RS_map);
         G_fatal_error(buf);
         exit(1);
       }

       soil_LN_cell=G_allocate_cell_buf();
       soil_RS_cell=G_allocate_cell_buf();
     }

/*
 * Checking for lake maps 
 */

     yes_lake=FALSE;
     lake_cat_map=parm.lake_map_name->answer;
     if(lake_cat_map!=NULL)  yes_lake=TRUE;
     if(yes_lake) 
     {
       mapset=G_find_cell(lake_cat_map,"");
       if(!mapset) 
       {
         sprintf(buf,"lake category map [%s] not found\n", lake_cat_map);
         G_fatal_error(buf);
         exit(1);
       }
       if((lake_cat_fd=G_open_cell_old(lake_cat_map,mapset))<0)
       {
         sprintf(buf,"cannot open [%s]\n", lake_cat_map);
         G_fatal_error(buf);
	 exit(1);
       }
       lake_tmp=G_allocate_cell_buf();

       lake_el_map=parm.lake_elevation->answer;
       if(lake_el_map==NULL) 
       {
         sprintf(buf,"lake initial water surface elevation map [%s] not provided\n", lake_el_map);
         G_fatal_error(buf);
	 exit(1);
       }

       mapset=G_find_cell(lake_el_map,"");
       if(!mapset) 
       {
         sprintf(buf,"lake initial water surface elevation map [%s] not found\n",                lake_el_map);
         G_fatal_error(buf);
         exit(1);
       }
       if((lake_el_fd=G_open_cell_old(lake_el_map,mapset))<0)
       {
         sprintf(buf,"cannot open [%s]\n", lake_el_map);
         G_fatal_error(buf);
         exit(1);
       }
       lake_el_tmp=G_allocate_cell_buf();

     }

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!                                                         !!!!
!!!!  Checking for EXPLICIT or IMPLICIT channel input files  !!!!
!!!!                                                         !!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     if(yes_channel || yes_priess)
     {
        channel_file=parm.channel->answer;
	if(channel_file==NULL)
	{
	   sprintf(buf,"channel input datafile is not specified\n");
           G_fatal_error(buf);
	   exit(1);
	}

        chn_link_map=parm.chn_link->answer;
        if(chn_link_map==NULL) 
	{
	   sprintf(buf,"channel link map [%s] not provided\n", chn_link_map);
           G_fatal_error(buf);
	   exit(1);
        }
        mapset=G_find_cell(chn_link_map,"");
        if(!mapset) 
	{
           sprintf(buf,"channel link map [%s] not found\n",chn_link_map);
           G_fatal_error(buf);
           exit(1);
        }
        if((chn_link_fd=G_open_cell_old(chn_link_map,mapset))<0)
        {
           sprintf(buf,"cannot open [%s]\n",chn_link_map);
           G_fatal_error(buf);
           exit(1);
        }
        chn_link_tmp=G_allocate_cell_buf();

        chn_node_map=parm.chn_node->answer;
        if(chn_node_map==NULL) 
	{
	   sprintf(buf,"channel node map [%s] not provided\n", chn_node_map);
           G_fatal_error(buf);
	   exit(1);
        }
        mapset=G_find_cell(chn_node_map,"");
        if(!mapset) 
	{
           sprintf(buf,"channel node map [%s] not found\n",chn_node_map);
           G_fatal_error(buf);
           exit(1);
        }
        if((chn_node_fd=G_open_cell_old(chn_node_map,mapset))<0)
        {
           sprintf(buf,"cannot open [%s]\n",chn_node_map);
           G_fatal_error(buf);
           exit(1);
        }
        chn_node_tmp=G_allocate_cell_buf();

     }

     if(yes_priess)
     {
        qprof_file=parm.qprof->answer;
	if(qprof_file==NULL)
	{
	   sprintf(buf,"discharge profile file is not specified\n");
           G_fatal_error(buf);
	   exit(1);
	}
        yprof_file=parm.yprof->answer;
	if(yprof_file==NULL)
	{
	   sprintf(buf,"water surface profile file is not specified\n");
           G_fatal_error(buf);
	   exit(1);
	}

        phyd_file=parm.phyd->answer;
        hydout_file=parm.hydout->answer;
        yes_phyd=FALSE;
        if(phyd_file != NULL) yes_phyd=TRUE;
 
        table_file=parm.table->answer;
     }

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Region (window) Call & Setup
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     G_get_set_window(&window);
     nrows=G_window_rows();
     ncols=G_window_cols();
     fprintf(stderr, "\n   The following is the region of your analysis (active region). Make sure it is correct.\n");
     fprintf(stderr, "   north: %f\n   south: %f\n   east: %f\n   west: %f\n   n_s resolution in meters: %f\n   e_w resolution in meters: %f\n   number of rows: %d\n   number of columns: %d \n\n", window.north,window.south,window.east,window.west, window.ns_res/wunit,window.ew_res/wunit,nrows,ncols);


     if(abs(1.-window.ew_res/window.ns_res) > 1e-3 && !flag.s->answer) 
     {
       fprintf(stderr, "The cells are not square within a tolerance of 0.1 percent\n ew_res=%f ns_res=%f\n",window.ew_res,window.ns_res);
       exit(1);
     }

     w=window.ew_res;
     w=w/wunit;

     rowout=G_northing_to_row(northout,&window);
     colout=G_easting_to_col(eastout,&window);
     if(rowout<0 || rowout>nrows || colout<0 || colout>ncols)
     {
       fprintf(stderr," ERROR: specified outlet is outside current region.\n");
       exit(1);
     }

/*!!!!!!!!!!!!!!!!!!!
   Time variables
!!!!!!!!!!!!!!!!!!!*/
  
     if(dtt==0)
     {
	sprintf(buf,"The computational time step (in seconds) must be an integer greater than or equal to one\n");
        G_fatal_error(buf);
        exit(1);
     }

     niter=totime/dtt;
     nitrn=raintime/dtt;

     if(yes_write) 
     {
	num_w=writime/dtt;
        if( (niter/num_w)+1 > 2000) 
	{
	     fprintf(stderr, "Too many output raster depth maps \n");
             exit(1);
        }               
	     /* 2000 in the maximum number of output raster files */
	ndigit=1;
        if((niter/num_w) >= 10) ndigit=2;
        if((niter/num_w) >= 100) ndigit=3;
        if((niter/num_w) >= 1000) ndigit=4;
     }

     if(yes_radar) 
     {
	rread=radt/dtt;
        if( (nitrn/rread)+1 > 10000) 
	{
	     fprintf(stderr, "Too many rainfall maps \n");
             exit(1);
        }               
	     /* 10000 in the maximum number of readable rainfall maps */
	rdigit=1;
        if((nitrn/rread) >= 10) rdigit=2;
        if((nitrn/rread) >= 100) rdigit=3;
        if((nitrn/rread) >= 1000) rdigit=4;
     }
     if(yes_gage) nread=gdt/dtt;
     dt=(double)dtt;

     if(totime%dtt !=0) fprintf(stderr,"Warning: Total simulation time is not divisible by the computational time step. \n"); 
     if(raintime%dtt !=0) fprintf(stderr,"Warning: Duration of rainfall is not divisible by the computational time step. \n");
     if(yes_gage && gdt%dtt !=0) fprintf(stderr,"Warning: Raingage time increment is not divisible by the computational time step. \n");
     if(yes_radar && radt%dtt !=0) fprintf(stderr,"Warning: Rainfall map time increment is not divisible by the computational time step. \n");

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   Processing output: ascii files & GRASS raster maps 
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     discharge_file=parm.discharge->answer;
     if((discharge_fd=fopen(discharge_file,"w")) == NULL)
     {
        sprintf(buf,"cannot open [%s] ascii output file\n",discharge_file);
        G_fatal_error(buf);
        exit(1);
     }

     yes_w_surf_dep=FALSE;
     if(yes_write) 
     {
       if(parm.depth->answer != NULL) 
       {
       yes_w_surf_dep=TRUE;
       depth_tmp=G_allocate_cell_buf();
       depth_fd=(int*) malloc((1+niter/num_w)*sizeof(int));
       for (nfile=0; nfile<=(niter/num_w); nfile++)
       {
          sprintf(buf,"%s.%.*d",parm.depth->answer,ndigit,nfile);
	  depth_file[nfile]=G_store(buf);  
       }
       }
     }

     yes_w_inf_dep=FALSE;
     if(yes_inf && yes_write) 
     {
       if(parm.inf->answer != NULL) 
       {
       yes_w_inf_dep=TRUE;
       inf_tmp=G_allocate_cell_buf();
       inf_fd=(int*) malloc((1+niter/num_w)*sizeof(int));
       for (nfile=0; nfile<=(niter/num_w); nfile++)
       {
          sprintf(buf,"%s.%.*d",parm.inf->answer,ndigit,nfile);
	  inf_dep_file[nfile]=G_store(buf);  
       }
       }
     }

     yes_w_surf_moist=FALSE;
     if(yes_inf && yes_write) 
     {
       if(parm.moist->answer != NULL) 
       {
       yes_w_surf_moist=TRUE;
       surf_moist_tmp=G_allocate_cell_buf();
       surf_moist_fd=(int*) malloc((1+niter/num_w)*sizeof(int));
       for (nfile=0; nfile<=(niter/num_w); nfile++)
       {
          sprintf(buf,"%s.%.*d",parm.moist->answer,ndigit,nfile);
	  surf_moist_file[nfile]=G_store(buf);  
       }
       }
     }

     yes_w_inf_rate=FALSE;
     if(yes_inf && yes_write) 
     {
       if(parm.rate->answer != NULL) 
       {
       yes_w_inf_rate=TRUE;
       inf_rate_tmp=G_allocate_cell_buf();
       inf_rate_fd=(int*) malloc((1+niter/num_w)*sizeof(int));
       for (nfile=0; nfile<=(niter/num_w); nfile++)
       {
          sprintf(buf,"%s.%.*d",parm.rate->answer,ndigit,nfile);
	  inf_rate_file[nfile]=G_store(buf);  
       }
       }
     }

     yes_w_dis_rain=FALSE;
     if((yes_gage || yes_radar) && yes_write) 
     {
     if(parm.dis_rain->answer != NULL) 
     {
       yes_w_dis_rain=TRUE;
       dis_rain_tmp=G_allocate_cell_buf();
       dis_rain_fd=(int*) malloc((1+niter/num_w)*sizeof(int));
       for (nfile=0; nfile<=(niter/num_w); nfile++)
       {
          sprintf(buf,"%s.%.*d",parm.dis_rain->answer,ndigit,nfile);
	  dis_rain_file[nfile]=G_store(buf);  
       }
       }
     }

/*!!!!!!!!!!!!!!!!!
   Rainfall maps 
!!!!!!!!!!!!!!!!!*/

     if(yes_radar)
     {
	radar_tmp=G_allocate_cell_buf();
	radar_fd=(int*) malloc((1+nitrn/rread)*sizeof(int));
	for (nfile=1; nfile<=(nitrn/rread); nfile++)
	{
		  /* The rainfall maps should start from *.1 */
	    sprintf(buf,"%s.%.*d",parm.radar_map->answer,rdigit,nfile);
	    radar_file[nfile]=G_store(buf);  

            mapset=G_find_cell(radar_file[nfile],"");
            if(!mapset) 
	    {
              sprintf(buf,"rainfall map [%s] not found\n", radar_file[nfile]);
              G_fatal_error(buf);
              exit(1);
            }
            if((radar_fd[nfile]=G_open_cell_old(radar_file[nfile],mapset))<0)
            {
              sprintf(buf,"cannot open [%s]\n", radar_file[nfile]);
              G_fatal_error(buf);
	      exit(1);
            }
	}
     }

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   Setup mask and space matrices 
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     if( (mask=G_alloc_imatrix(nrows,ncols)) == NULL) fprintf(stderr,
	  "cannot allocate memory for watershed mask matrix");
     if( (space=G_alloc_imatrix(nrows,ncols)) == NULL) fprintf(stderr,
	  "cannot allocate memory for watershed space matrix");
     GNUM=0;
     for(row=0; row<nrows; row++)
     {
	if(yes_mask) 
	{
          if(G_get_map_row(mask_fd,mask_tmp,row)<0) 
	  { 
	    sprintf(buf,"cannot get row # [%d] of [%s]",row,mask_map);
	    exit(1);
          }
        }

	for(col=0; col<ncols; col++)
	{
	   if(yes_mask) mask[row][col]=mask_tmp[col];
           if(!yes_mask) mask[row][col]=1;
	   if(mask[row][col]==0) 
	   {
	      space[row][col]=0; 
	      continue;
           }
	   else
	   {
	      space[row][col]=GNUM+1;
	      GNUM++;
	      if(row==rowout && col==colout) vectout=space[row][col];
           }
         }
      }

/*!!!!!!!!!!!!!!!!!!!!!!!!
  MEMORY ALLOCATION 
!!!!!!!!!!!!!!!!!!!!!!!!*/

     fprintf(stderr, "allocating memory for the arrays\n");

     TNUM=GNUM+1;
     if( (elev=(float*) malloc(TNUM*sizeof(float))) == NULL) fprintf(stderr,
	  "cannot allocate memory for elevation array");

     if( (h=(float*) malloc(TNUM*sizeof(float))) == NULL) fprintf(stderr,
	  "cannot allocate memory for surface depth array");

     if( (dqov=(float*) malloc(TNUM*sizeof(float))) == NULL) fprintf(stderr,
	  "cannot allocate memory for increment overland discharge array");

     if(yes_dist_rough) 
     {
        if( (rough=(float*) malloc(TNUM*sizeof(float))) == NULL) fprintf(stderr,
	     "cannot allocate memory for distributed roughness array"); 
     }

     if(yes_gage || yes_radar) 
     {
        if( (rint=(float*) malloc(TNUM*sizeof(float))) == NULL) fprintf(stderr,
	     "cannot allocate memory for rainfall intensity array"); 
     }

     if(yes_lake) 
     {
	if( (lake_cat=(int*) malloc(TNUM*sizeof(int))) == NULL) fprintf(stderr, 
	     "cannot allocate memory for lake category array");
     }

     if(yes_intercep)
     {
	if( (Inter=(float*) malloc(TNUM*sizeof(float))) == NULL) fprintf(stderr,
	     "cannot allocate memory for cumulative interception array");
	if( (sv=(float*) malloc(TNUM*sizeof(float))) == NULL) fprintf(stderr,
	     "cannot allocate memory for storage capacity array");
	if( (exp=(float*) malloc(TNUM*sizeof(float))) == NULL) fprintf(stderr,
	     "cannot allocate memory for interception exponent array");
     }

     if(yes_inf)  
     {
        if( (K=(float*) malloc(TNUM*sizeof(float))) == NULL) fprintf(stderr,
	     "cannot allocate memory for hydraulic conductivity array"); 
        if( (H=(float*) malloc(TNUM*sizeof(float))) == NULL) fprintf(stderr,
	     "cannot allocate memory for capillary suction head array"); 
        if( (P=(float*) malloc(TNUM*sizeof(float))) == NULL) fprintf(stderr,
	     "cannot allocate memory for effective porosity array"); 
        if( (M=(float*) malloc(TNUM*sizeof(float))) == NULL) fprintf(stderr,
	     "cannot allocate memory for antecedent soil moisture array"); 
        if( (vinf=(float*) malloc(TNUM*sizeof(float))) == NULL) fprintf(stderr,
	     "cannot allocate memory for infiltration depth array"); 
	if(yes_w_inf_rate) 
	{
	   if( (frate=(float*) malloc(TNUM*sizeof(float))) == NULL) 
	   fprintf(stderr, "cannot allocate memory for arrray of infil rate");
	}

        if(yes_redist_cons || yes_redist_vary) 
        {
          if(yes_redist_vary) 
	  {
	     if((LN=(float*) malloc(TNUM*sizeof(float)))==NULL) fprintf(stderr,
             "cannot allocate memory for pore size distribution array"); 
             if((RS=(float*) malloc(TNUM*sizeof(float)))==NULL) fprintf(stderr,
             "cannot allocate memory for residual saturation array"); 
          }

          if((teta_n=(float*)malloc(TNUM*sizeof(float)))==NULL) fprintf(stderr,
          "cannot allocate memory for surface soil moisture array"); 
          if((vinf_n=(float*)malloc(TNUM*sizeof(float)))==NULL) fprintf(stderr,
          "cannot alloc mem. for accum. infil dep. of 1st miost. prof. array"); 
	  if( (iter_pond_1=(int*) malloc(TNUM*sizeof(int))) == NULL) fprintf
	  (stderr, "cannot allocate memory for ponding time array");
	  if( (iter_n=(int*) malloc(TNUM*sizeof(int))) == NULL) fprintf(stderr,
	  "cannot allocate memory for array of end-of-redistribution time");

	  if((no_wat_prof=(int*)malloc(TNUM*sizeof(int)))==NULL)fprintf(stderr,
          "cannot allocate memory for array of number of soil water profiles");
	  if( (iter_i_less_k = (int*) malloc(TNUM*sizeof(int))) == NULL) 
	  fprintf(stderr,"cannot allocate memory for iteration array of when very initial rainfall intensity at some cell is less than hydraulic conductivity");
	  if(yes_w_surf_moist) 
	  {
	    if( (surf_moist=(float*) malloc(TNUM*sizeof(float))) == NULL) 
	    fprintf(stderr, "cannot alloc mem. for arrray of suface moisture");
          }
       }
     }


/*!!!!!!!!!!!!!!!!!!!!!
  INITIALIZATION
!!!!!!!!!!!!!!!!!!!!!*/

     for(row=0; row<nrows; row++)
     {

        if(G_get_map_row(elev_fd,elev_tmp,row)<0) 
	{ 
	   sprintf(buf,"cannot get row # [%d] of [%s]",row,elev_map);
	   exit(1);
        }

	if(yes_dist_rough) 
	{
          if(G_get_map_row(roughness_fd,roughness_tmp,row)<0) 
	  { 
	    sprintf(buf,"cannot get row # [%d] of [%s]",row,roughness_map);
	    exit(1);
          }
        }

        if(init_depth_fd!=-1) 
	{
           if(G_get_map_row(init_depth_fd,init_depth_cell,row)<0) 
	   {
	      sprintf(buf,"cannot get row # [%d] of [%s]",row,init_depth_map);
	      exit(1);
           }
        }

        if(yes_intercep)
	{
	   if(G_get_map_row(storage_cap_fd,storage_cap_cell,row)<0) 
	   {
              sprintf(buf,"cannot get row # [%d] of [%s]",row,storage_cap_map);
	      exit(1);
	   }
	   if(G_get_map_row(intercep_exp_fd,intercep_exp_cell,row)<0) 
	   {
              sprintf(buf,"cannot get row # [%d] of [%s]",row,intercep_exp_map);
	      exit(1);
	   }
        }

        if(yes_inf) 
	{
           if(G_get_map_row(soil_K_fd,soil_K_cell,row)<0) 
	   { 
	      sprintf(buf,"cannot get row # [%d] of [%s]",row,soil_K_map);
	      exit(1);
           }
           if(G_get_map_row(soil_H_fd,soil_H_cell,row)<0) 
	   { 
	      sprintf(buf,"cannot get row # [%d] of [%s]",row,soil_H_map);
	      exit(1);
           }
           if(G_get_map_row(soil_P_fd,soil_P_cell,row)<0) 
	   { 
	      sprintf(buf,"cannot get row # [%d] of [%s]",row,soil_P_map);
	      exit(1);
           }
           if(G_get_map_row(soil_M_fd,soil_M_cell,row)<0) 
	   { 
	      sprintf(buf,"cannot get row # [%d] of [%s]",row,soil_M_map);
	      exit(1);
           }

          if(yes_redist_vary) 
	  {
             if(G_get_map_row(soil_LN_fd,soil_LN_cell,row)<0) 
	     { 
	       sprintf(buf,"cannot get row # [%d] of [%s]",row,soil_LN_map);
	       exit(1);
             }
             if(G_get_map_row(soil_RS_fd,soil_RS_cell,row)<0) 
	     { 
	       sprintf(buf,"cannot get row # [%d] of [%s]",row,soil_RS_map);
	       exit(1);
             }
          }
        }

	for(col=0; col<ncols; col++)
	{
	  vect=space[row][col];
	  if(vect==0) continue;
	  elev[vect]=elev_tmp[col]/elunit;
	  h[vect]=0;
	  if(yes_dist_rough) rough[vect]=(float)roughness_tmp[col]/1000.;

				    /* The original roughness map must
				       have been multiplied by 1000 */

          if(init_depth_fd != -1) h[vect]=(float)init_depth_cell[col]/1000.;

	  dqov[vect]=0;
	  if(yes_gage || yes_radar) rint[vect]=0;

	  if(yes_intercep)
	  {
	     Inter[vect]=0;
	     sv[vect]=(float)storage_cap_cell[col]/10000.;
					 /* sv is in tenths of mm */
	     exp[vect]=(float)intercep_exp_cell[col]/1000.;
          }

	  if(yes_inf) 
	  {
	     K[vect]=(float)soil_K_cell[col]/(10000.*3600.);
	     H[vect]=(float)soil_H_cell[col]/10000.;
	     P[vect]=(float)soil_P_cell[col]/1000.;
	     M[vect]=(float)soil_M_cell[col]/1000.;
				/* The integer maps of soil parameters
				 * are converted back to the original 
				 * real (float) values.  */
	     if(M[vect]>P[vect])
	     {
		fprintf(stderr, "DATA ERROR: The initial soil moisture content is greater than the effective porosity at row=%d and col=%d.\n", row,col);
		exit(1);
             }
	     vinf[vect]=0;

	     if(yes_w_inf_rate) frate[vect]=0;
	     if(yes_redist_cons || yes_redist_vary) 
	     {
	        if(yes_redist_vary) 
		{
				             /* pore-size distribution index
					      * input had been multiplied by 
					      * a thousand */
		   LN[vect]=(float)soil_LN_cell[col]/1000.;    
				             /* residual saturation input*/
                   RS[vect]=(float)soil_RS_cell[col]/1000.;    
	           if(RS[vect] >  M[vect]) 
	           {
		      fprintf(stderr, "Data Error: The residual saturation at %d th row and % d th column must be less than the initial moisture\n", row, col);
		      exit(1);
                   }
                }

	        teta_n[vect]=(float)soil_M_cell[col]/1000.;
	        vinf_n[vect]=0.;
	        iter_i_less_k[vect]=0;
	        iter_pond_1[vect]=0;
	        iter_n[vect]=0;
	        no_wat_prof[vect]=0;
	        if(yes_w_surf_moist) 
		   surf_moist[vect]=(float)soil_M_cell[col]/1000.;
	     }
          }
        }
     }


/* 
 * Lake/Reservoir memory allocation & initialization
 */

     vlake1=0;
     if(yes_lake) 
     {
	nlake=0;
        for(row=0; row<nrows; row++)
        {
           if(G_get_map_row(lake_cat_fd,lake_tmp,row)<0) 
	   { 
	      sprintf(buf,"cannot get row # [%d] of [%s]",row,lake_cat_map);
	      exit(1);
           }

	   for(col=0; col<ncols; col++)
	   {
	      vect=space[row][col];
	      if(vect==0) continue;
              lake_cat[vect]=lake_tmp[col];
	      if(lake_cat[vect]==0) continue;
	      if(lake_cat[vect]>nlake) nlake=lake_cat[vect];
           }
        }

        if((lake_cells=(int*) malloc((nlake+1)*sizeof(int))) == NULL) fprintf(stderr,"cannot allocate memory for array of lake's number of cells");
        if((lake_el=(double*) malloc((nlake+1)*sizeof(double))) == NULL) fprintf(stderr,"cannot allocate memory for array of lake water surface elevtion");
        if((lake_type=(int*) malloc((nlake+1)*sizeof(int))) == NULL) fprintf(stderr,"cannot allocate memory for array of lake type");
        if((qtolake=(double*) malloc((nlake+1)*sizeof(double))) == NULL) fprintf(stderr,"cannot allocate memory for array of discharge to lake");
         
        if( (check=(double*) malloc(TNUM*sizeof(double))) == NULL) fprintf(stderr, "cannot allocate memory for check array");

        for(row=0; row<nrows; row++)
	{
           if(G_get_map_row(lake_el_fd,lake_el_tmp,row)<0) 
	   { 
	      sprintf(buf,"cannot get row # [%d] of [%s]",row,lake_el_map);
	      exit(1);
           }

	   for(col=0; col<ncols; col++)
	   {
	      vect=space[row][col];
	      if(lake_cat[vect]==0) continue;
	      lake_cells[lake_cat[vect]]=lake_cells[lake_cat[vect]]+1;
	      lake_type[lake_cat[vect]]=1;

	      check[vect]=lake_el_tmp[col]/lake_elunit;

              lake_el[lake_cat[vect]]=lake_el_tmp[col]/lake_elunit; 
	      if(((float)lake_el[lake_cat[vect]] - elev[vect]) < 0) 
	      { 
                fprintf(stderr, "SERIOUS WARNING/POSSIBLE ERROR: The inintial water surface elevation value of [%f] at lake category [%d] is lower than the bed elevation value of [%f] at row= [%d] and col=[%d]. Islands cannot be simulated.\n", lake_el[lake_cat[vect]],lake_cat[vect],elev[vect],row,col); 
	      }	
              else
              {
	         vlake1=vlake1+((float)lake_el[lake_cat[vect]]-elev[vect])*w*w;
              }

           } 
        }

	for(vect=1; vect<=GNUM; vect++)
	{
	   if(lake_cat[vect]==0) continue;
	   if(check[vect] != lake_el[lake_cat[vect]])
	   {
	      fprintf(stderr, "ERROR: The elevations of water surface at cells of lake category [%d] are not the same. \n",lake_cat[vect]);
	      exit(1);
           }
        }

     }

/*!!!!!!!!!!!!!!!!!!!!!!!!!
  Free unwanted memory
!!!!!!!!!!!!!!!!!!!!!!!!!*/

     if(yes_mask) free(mask_tmp);
     free(elev_tmp);
     if(yes_dist_rough) free(roughness_tmp);
     if(yes_inf) 
     {  
	free(soil_K_cell);
	free(soil_H_cell);
	free(soil_P_cell);
	free(soil_M_cell);
	if(yes_redist_vary) 
        {
	   free(soil_LN_cell);
	   free(soil_RS_cell);
        }
     }
     if(yes_lake) 
     {
	free(lake_tmp);
        free(lake_el_tmp);
        free(check);
     }

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
     RAINGAGE RAINFALL DATA 
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     if(yes_gage) 
     {
	tmpeast=0;
	tmpnorth=0;
        for(igage=0; igage<nrg; igage++)
        {
	   grow[igage]=0;
	   gcol[igage]=0;
	   rgint[igage]=0;
        } 
       
	fprintf(stderr," reading easting and northing of raingages\n");
        for(igage=0; igage<nrg; igage++)
        {
	   fscanf(rain_fd, "%lf %lf\n", &tmpeast, &tmpnorth);
	   grow[igage]=G_northing_to_row(tmpnorth,&window);
	   gcol[igage]=G_easting_to_col(tmpeast,&window);
        }
     }

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  IMPLICIT OR EXPLICIT CHANNEL DATA 
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     vsur1=0.;
     if(yes_priess || yes_channel)
     {
        if((iunit=fopen(channel_file,"r")) == NULL)
        {
           fprintf (stdout,"Can't open [%s]",channel_file);
           return(-2);
        }

	if(!yes_drain && !yes_bkwater)  /* OPEN FILES FOR READING */ 
        {
           if((yunit=fopen(yprof_file,"r"))==NULL)
	   {
              fprintf (stdout,"Can't open [%s]",yprof_file);
              return(-2);
           }
           if((qunit=fopen(qprof_file,"r"))==NULL)
	   {
              fprintf (stdout,"Can't open [%s]",qprof_file);
              return(-2);
           }
           if(yes_phyd)
	   {
	      if((phydunit=fopen(phyd_file,"r"))==NULL)
	      {
	         fprintf (stdout,"Can't open [%s]",phyd_file);
	         return(-2);
	      }
	      if((iunit9=fopen(hydout_file,"w"))==NULL)
	         {
	         fprintf (stdout,"Can't open [%s]",hydout_file);
	         return(-2);
                 }
	   }
        }
	else         /* OPEN FLIES FOR WRITING IN DRAINAGE MODE */
	{
	   if((yunit=fopen(yprof_file,"w"))==NULL)
	   {
               fprintf (stdout,"Can't open [%s]",yprof_file);
               return(-2);
           }
	   if((qunit=fopen(qprof_file,"w"))==NULL)
	   {
               fprintf (stdout,"Can't open [%s]",qprof_file);
               return(-2);
           }
        }

	/*
	 *   READ THE INPUT FILE
	 */

	 read_input(iunit,yunit,qunit,&grav,&alpha,&beta,
	     &theta,&delx,&delt,&tt,&nlinks,&LINKS,&NODES,&NUM,
             &depend,&backdep,&nx1,&strick,&bottom,
             &sslope,&sslope2,&bel,&qp,&yp,&ltype,&ndep,
	     &maxnodes,&chn_dep,&marea0,&parea0,&mtw0,&ptw0,&mk0,&pk0,
	     &marea1,&parea1,&mtw1,&ptw1,&mk1,&pk1,&numqpipe,
             yes_drain,yes_bkwater,&yes_table,&table_num,&highspot,
             &lowspot,&qmin);

         if(yes_table==1)
         {
            /* there are some link type 8, or break-point cross-sectional
	       data.  So read the table file.  */

            if(table_file == NULL) 
            {
               sprintf(buf,"channel look-up table file is not specified\n");
               G_fatal_error(buf);
               exit(1);
            }
            if((tunit=fopen(table_file,"r"))==NULL)
	    {
               fprintf(stderr,"Can't open file [%s]\n",table_file);
               return(-2);
            }

	    read_table(tunit,&NUMTBL,&NUMBPTS,&TBNUM,&xarea,&xtw,
		       &xk,&numhts,&ht_spc,&maxtab);
         }   

         /* For mass balance computation */
         
         if((dum1=(float*) malloc(NUM*sizeof(float))) == NULL) 
         {
           fprintf(stderr,"cannot allocate memory for dum1 array");
           exit(-2);
         }
         if((dum2=(float*) malloc(NUM*sizeof(float))) == NULL) 
         {
           fprintf(stderr,"cannot allocate memory for dum2 array");
           exit(-2);
         }
         if((dum3=(float*) malloc(NUM*sizeof(float))) == NULL) 
         {
           fprintf(stderr,"cannot allocate memory for dum3 array");
           exit(-2);
         }
         if((farea=(float*) malloc(NUM*sizeof(float))) == NULL) 
         {
           fprintf(stderr,"cannot allocate memory for farea array");
           exit(-2);
         }
         

 	 if(abs(delt-(float)dt)>1e-3) 
	 {
	    fprintf(stderr,"ERROR: The time step %f in [%s] is not equal to the computational overland time step %f\n",delt,channel_file,dt);
            exit(1);
         }

	 delt=delt/60.;   /* delt for implicit channel routing 
                           * must change to min 
                           */

                          /* These are for overland/channel
                           * connectivity arrays
                           */

         if((qlat=(float*) malloc(NUM*sizeof(float))) == NULL)
	 {
	    fprintf(stderr,"cannot allocate memory for qlat array");
	    exit(-2);
         }
	 if((con_vect=(int*) malloc(NUM*sizeof(int))) == NULL)
	 {
	    fprintf(stderr,"cannot allocate memory for con_vect array");
	    exit(-2);
         }
	 if((con_link=(int*) malloc((GNUM+1)*sizeof(int))) == NULL)
	 {
	    fprintf(stderr,"cannot allocate memory for con_link array");
	    exit(-2);
         }
	 if((con_node=(int*) malloc((GNUM+1)*sizeof(int))) == NULL)
	 {
	    fprintf(stderr,"cannot allocate memory for con_node array");
	    exit(-2);
         }

         if(yes_phyd)
	 {
	    eocheck=22;
	    ptot=0;
	    while(eocheck!=EOF)
	    {
	       eocheck=fscanf(phydunit,"%d %d\n",&itmp,&itmp);
	       ptot++;
            }
	    fclose(phydunit);
	    ptot=ptot-1;
	    if( (plink=(int*) malloc((1+ptot)*sizeof(int))) == NULL)
	    fprintf(stderr,"cannot allocate memory for plink array");
	    if( (pnode=(int*) malloc((1+ptot)*sizeof(int))) == NULL)
	    fprintf(stderr,"cannot allocate memory for pnode array");
	    fopen(phyd_file,"r");
	    for(node=1; node<=ptot; node++)
	    {
	        fscanf(phydunit,"%d %d\n", &plink[node], &pnode[node]);
		if(plink[node]>nlinks)
		{
		   fprintf(stderr,
		   "a link number %d in [%s] file is greater than total number of links.\n",plink[node],phyd_file);
		    return(-2);
		}
		if(pnode[node]>nx1[plink[node]])
		{
		   fprintf(stderr,
		   "a node number %d of link %d in [%s] is greater than the number if nodes of that link\n",pnode[node],plink[node],phyd_file);
		   return(-2);
                }
	    }
         }

	 /*
	  *    INITIALIZE NEEDED QUANTITIES
	  */

	  /*
	   *   qmin is the minimum inflow on 1st order streams to prevent
	   *   dry bed conditions from developing.
	   */

	 iter=2;    /* This is the number of internal iterations
                     * for implicit channel routing
                     */

         tdrain=(float)(totime/60);  /* tdrain in minutes */

	   /* if draining, we need to know the normal depth at the outlet
	      of the channel network.   */
 
         if(yes_drain || yes_bkwater)
         {
	    norm_calc(nlinks,nx1,ltype,backdep,yp,qp,bel,
	              xarea,xtw,xk,numhts,ht_spc,table_num,
	              delx,NUMBPTS,&normout,sslope,bottom,
                      strick,yes_bkwater,grav);
            fprintf(stderr,"Normal depth at outlet= %f\n",normout);
            if(yes_bkwater) goto DRAIN;
         }
     }

/*   
 *   The following if only for EXPLICIT scheme.
 */

     if(yes_channel)
     {
        if((hch=(float*) malloc(NUM*sizeof(float))) == NULL) fprintf(stderr,
	"cannot allocate memory for array of channel depth");
        if((dqch=(float*) malloc(NUM*sizeof(float))) == NULL) fprintf(stderr,
	"cannot allocate memory for array of channel net discharge");
        if((chn_row=(int*) malloc(NUM*sizeof(int))) == NULL) fprintf(stderr,
	"cannot allocate memory for array of channel network row addresses");
        if((chn_col=(int*) malloc(NUM*sizeof(int))) == NULL) fprintf(stderr,
	"cannot allocate memory for array of channel network column addresses");
     }

/*   
 *   READING CHANNEL/OVERLAND CONNECTIVITY
 */

     if(yes_priess || yes_channel)
     {
        for(row=0; row<nrows; row++)
	{
	    if(G_get_map_row(chn_link_fd,chn_link_tmp,row)<0) 
	    {
	       sprintf(buf,"cannot get row # [%d] of [%s]",row,chn_link_map);
	       exit(1);
            }
	    if(G_get_map_row(chn_node_fd,chn_node_tmp,row)<0) 
	    {
	       sprintf(buf,"cannot get row # [%d] of [%s]",row,chn_node_map);
	       exit(1);
            }
            
	    for(col=0; col<ncols; col++)
	    {
                vect=space[row][col];
		if(vect==0) continue;
		con_link[vect]=chn_link_tmp[col];
		con_node[vect]=chn_node_tmp[col];
		if(con_link[vect]!=0)
		   con_vect[con_node[vect]+con_link[vect]*NODES]=vect;

		/* ONLY FOR EXPLICIT */
		if(yes_channel)
		{
		   chn_row[con_node[vect]+con_link[vect]*NODES]=row;
		   chn_col[con_node[vect]+con_link[vect]*NODES]=col;
		   hch[con_node[vect]+con_link[vect]*NODES]=0;
		   dqch[con_node[vect]+con_link[vect]*NODES]=0;
	           if(vect==vectout) 
		   {
	              linkout=con_link[vect];
		      nodeout=con_node[vect];
                   }

                }

             }
         }
     }

     if(yes_priess)
     {
	for(link=0; link<=nlinks; link++)
	{
	    if(ltype[link]!=4) continue;
	    /* Lake type 1 are those NOT in the link map and type 2 are those
	     * part of the IMPLICIT stream network in the link map. */
	    lake_type[lake_cat[con_vect[1+link*NODES]]]=2;
        }
     }

/* 
 * Initial channel water surface volume
 */

     if(yes_priess)
     {

        /* Initial mass computations, BS 6-5-95 */
        section(bottom,sslope,sslope2,strick,yp,bel,farea,
                dum1,dum2,dum3,nx1,ltype,chn_dep,
                marea0,parea0,mtw0,ptw0,mk0,pk0,
                marea1,parea1,mtw1,ptw1,mk1,pk1,
                xarea,xtw,xk,numhts,ht_spc,maxtab,
                table_num,NUMBPTS);
        for(link=1; link<=nlinks; link++)
	{
	  for(node=1; node<=NODES; node++)
	  {
	     if(ltype[link]==1 || ltype[link]==8)
	     {
		if(node<nx1[link] || (node<=nx1[link] && link==nlinks)
		   || (node<=nx1[link] && ltype[backdep[link]]==4))
		{

                       vsur1=vsur1+farea[node+link*NODES]*w;

                }
             }
          }
       }
       
     }

/*!!!!!!!!!!!!!!!!!!!!
  END CHANNEL DATA
!!!!!!!!!!!!!!!!!!!*/

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  BEGIN WRITE DISCHARGE FILE HEADER
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     fprintf(discharge_fd,"     r.hydro.CASC2D output \n     Version 1.00 8/1995  Copyleft by B. Saghafian and F. L. Ogden \n\n");
     fprintf(discharge_fd,"number of rows, number of columns, cell size: %d  %d  %f\n",nrows,ncols,w);
     fprintf(discharge_fd,"outlet row number, outlet column number , outlet bed slopesout: %d  %d  %f\n",rowout,colout,sout);

     if(!yes_dist_rough) fprintf(discharge_fd,"uniform Manning n: %f\n",rman);
     if(yes_dist_rough) fprintf(discharge_fd,"simulating spatially distributed roughness\n");

     if(!yes_gage && !yes_radar) fprintf(discharge_fd,"uniform rainfall intensity in mm/hr: %f\n",1000*3600*crain);
     if(yes_gage) fprintf(discharge_fd,"simulating spatially distributed raingage rainfall data\n");
     if(yes_radar) fprintf(discharge_fd,"simulating spatially distributed rainfall maps\n");
     if(yes_inf) fprintf(discharge_fd,"infiltration is computed\n");
     fprintf(discharge_fd,"computational time step (sec), total simulation time (sec), and rainfall duration (sec): %6.2f  %i  %i\n",dt,totime,raintime);

     if(!yes_english_unit) 
     {
	 uvol=1.0;
	 fprintf(discharge_fd,"\n  Time (min)   Discharge (cms)\n");
     }
     else
     {
	 uvol=3.28*3.28*3.28;
	 fprintf(discharge_fd,"\n  Time (min)   Discharge (cfs)\n");
     }

     vin=0;
     dvin=0;
     vsur2=vsur1;
     vinftot=0;
     vout=0;
     vintercep=0;
     vout_region=0;
     vlake2=vlake1;
     rindex=1;
     tpeak=0;
     qpeak=0;
     rainrate=0;
     intrate=0;        /*set interception rate to zero */

/* 
 *  Calculation of Stationary Variables 
 */

     if(vectout != '\0')
     {
        if(yes_dist_rough)
        { 
	   alfaovout=sqrt(sout)/rough[vectout]; 
	}
        else
        { 
	   alfaovout=sqrt(sout)/rman; 
	}
     }


/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!                                              !!!!!
!!!!!              TIME LOOP BEGINS                !!!!!
!!!!!                                              !!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/


for ( itime=1; itime<=niter+1; itime++ )
{

     if(yes_drain)    /* only drain if yes_drain is set */
     {
       flow_route(iter,itime,delt,delx,alpha,beta,theta,grav,
		  depend,backdep,nx1,bel,yp,qp,strick,bottom,
                  chn_dep,sslope,sslope2,ltype,ndep,yfirst,
                  ystep,qmin,marea0,parea0,mtw0,ptw0,mk0,pk0,
		  marea1,parea1,mtw1,ptw1,mk1,pk1,numqpipe,yes_drain,
		  /*  the following were added FLO 10-8-94 to 
		      accomod break-point x-sect. description */
                  xarea,xtw,xk,numhts,ht_spc,maxtab,table_num,
                  NUMBPTS,lowspot,highspot,normout,tdrain);

       fprintf(stderr,"iteration= %d \n",itime);
       if(itime==niter) goto DRAIN;

       /* the following lines write to the discharge file */
       fprintf(discharge_fd,"%8.2f  %9.2f cms   %7.4f  m\n", 
               (float)itime*dt/60.0,
               qp[nx1[nlinks]+nlinks*NODES],
               yp[nx1[nlinks]+nlinks*NODES]-bel[nx1[nlinks]+nlinks*NODES]);

       continue;
     }

     if(yes_write) 
     {
	if( ((itime-1)%num_w) == 0 ) 
	{
           WRITE_FILES(buf,windex=1,itime,dt,num_w,yes_w_surf_dep,depth_fd,
		 depth_file,yes_w_inf_dep,inf_fd,inf_dep_file,yes_w_surf_moist,
		 surf_moist_fd,surf_moist_file,yes_w_inf_rate,inf_rate_fd,
		 inf_rate_file,yes_w_dis_rain,rindex,
		 dis_rain_fd,dis_rain_file,h,yes_channel,
		 yes_priess,ltype,nx1,chn_row,chn_col,hch,yp,bel,
		 depth_tmp,inf_tmp,surf_moist_tmp,inf_rate_tmp,
		 dis_rain_tmp,nitrn,vinf,surf_moist,frate,rint,space,
		 yes_lake,elev,&colors);
        }
     }

     if(itime>niter) break;
     icall=0;
     if(itime>nitrn)  rindex=0;
     if(itime<=nitrn && yes_gage) 
     {
        if( ((itime-1)%nread) == 0 ) 
	{
           icall=1;
           READ_GAGE_FILE(rgint,nrg,rain_fd);
           if(!yes_thiessen) RAIN_SQ_DIS(yes_rg_mmhr,
			   			space,nrg,grow,gcol,rgint,rint);
           if(yes_thiessen) RAIN_THIESSEN(yes_rg_mmhr,
			   			space,nrg,grow,gcol,rgint,rint);
	}
     }

     if(itime<=nitrn && yes_radar) 
     {
	if( ((itime-1)%rread) == 0 )
	{
           itmp=1+itime/rread;
	   for(row=0; row<nrows; row++) 
           {
               if(G_get_map_row(radar_fd[itmp],radar_tmp,row)<0)
	       { 
		  sprintf(buf,"cannot get row # [%d] of [%s]",
			  row,radar_file[itmp]); 
		  exit(1); 
	       }
	       for(col=0; col<ncols; col++) 
	       {
		   if(space[row][col]==0) continue;
	           vect=space[row][col];
	           rint[vect]=radar_tmp[col]; 
	           rint[vect]=rint[vect]/(1000*3600); 
	       } 
            }
	 }
     }	

/*!!!!!!!!!!!!!!!!!!
  LAKES RESET
!!!!!!!!!!!!!!!!!!*/

			       /* Lakes could exist without channel network. 
                                * If channel routing is also performed then
				* the lakes are implicit channel LINK type 4 
				* but LAKE type 2. If, however, explicit
                                * channel routing is performed or there are
                                * isolated pond area, then such lakes are
                                * of type 1 lakes. (confused yet?)
                                */
     if(yes_lake) 
     {
        for(ilake=1; ilake<=nlake; ilake++)
        {
            vlake2=vlake2+(float)qtolake[ilake]*dt;

            /* For all lakes in explicit routing OR lakes which are not 
	     * part of implicit link numbering */
	    if(lake_type[ilake]!=2) lake_el[ilake]=lake_el[ilake] + 
			   qtolake[ilake]*dt/(w*w*(double)lake_cells[ilake]);

            qtolake[ilake]=0;  
        }
     }


/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  OVERLAND DEPTH UPDATE & INTERCEPTION & INFILTRATION
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     for(vect=1; vect<=GNUM; vect++)
     {

	  if(yes_gage || yes_radar) 
	  {
	     rainrate=rindex*rint[vect];
	  }
          else 
	  {
             rainrate=rindex*crain;
          }

          dvin=dvin+rainrate*dt*w*w;

	  if(yes_lake && lake_cat[vect] !=0)
          {
	     qtolake[lake_cat[vect]]=qtolake[lake_cat[vect]]+
			rainrate*w*w;
	  }
          else
	  {
             hov=dqov[vect]*dt/(w*w);
	     if(yes_intercep && rindex==1) 
		INTERCEPTION(vect,dt,Inter,sv,exp,rainrate,&intrate);
             hov=hov+h[vect]+rindex*(rainrate-intrate)*dt;

             if(hov<0) 
	     {        

               CRASH(discharge_fd,coindex=1,vect,link=0,node=0,
		     itime,space,dt,window,Inter,h,vinf,yes_intercep,
		     yes_inf,&vintercep,&vsur2,yes_lake,&vlake2,elev,&vinftot);

               if(yes_write) 
		   WRITE_FILES(buf,windex=2,itime,dt,num_w,yes_w_surf_dep,
		   depth_fd,depth_file,yes_w_inf_dep,inf_fd,inf_dep_file,
		   yes_w_surf_moist,surf_moist_fd,surf_moist_file,
		   yes_w_inf_rate,inf_rate_fd,inf_rate_file,yes_w_dis_rain,
		   rindex,dis_rain_fd,dis_rain_file,h,yes_channel,
		   yes_priess,ltype,nx1,chn_row,chn_col,hch,yp,bel,
		   depth_tmp,inf_tmp,surf_moist_tmp,inf_rate_tmp,
		   dis_rain_tmp,nitrn,vinf,surf_moist,frate,rint,space,
		   yes_lake,elev,&colors);
	       goto PRINT;
             }

	     if(yes_inf && !yes_redist_cons && !yes_redist_vary) 
	     { 
	        if(K[vect] >0 && (hov/dt)>1e-9) 
                   INF_NODIST(itime,vect,dt,vinf,frate,
                              yes_w_inf_rate,K,H,P,M,&hov);
             }

	     if(yes_inf && (yes_redist_cons || yes_redist_vary)) 
	     {
	        if(K[vect] >0) 
                   INF_REDIST(yes_redist_vary,vect,dt,vinf,itime,
	           iter_pond_1,iter_i_less_k,teta_n,vinf_n,yes_w_surf_moist,
	           surf_moist, yes_w_inf_rate,frate,no_wat_prof, 
	           iter_n,K,H,P,M,LN,RS,&hov);
             }
	  
	     h[vect]=hov; 
	     dqov[vect]=0;
          }

	  if(yes_intercep && itime == niter) vintercep=vintercep+Inter[vect]*w*w;
          if(itime == niter && h[vect] != 0) vsur2=vsur2+h[vect]*w*w;
          if(itime == niter && yes_inf) vinftot=vinftot+vinf[vect]*w*w;

     }
     
     vin=vin+dvin;
     dvin=0;

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  EXPLICIT CHANNEL DEPTH UPDATE
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     if(yes_channel) 
     {
          for(link=1; link<=nlinks; link++)
          {
	     if(ltype[link]==4) continue;  /* Lakes are processed separately */
             for(node=1; node<=nx1[link]; node++)
	     {
	        row=chn_row[node+link*NODES];
	        col=chn_col[node+link*NODES];
	        vect=space[row][col];
	        wid=bottom[node+link*NODES];
	        depth=chn_dep[node+link*NODES];
	        z=sslope[node+link*NODES];

		dhch=0;
		qtoch=dqch[node+link*NODES];
                if(qtoch!=0)
		{
		   CH_DEPTH(link,node,discharge_fd,dt,z,depth,wid,
                            qtoch,hch,&dhch);
		   hch[node+link*NODES]=hch[node+link*NODES]+dhch;
                }
		dqch[node+link*NODES]=0;
		dhch=0;

                htop=depth + h[vect];
		if(htop>hch[node+link*NODES])
		{
                   qtoch=3.27*w*pow((base=h[vect]),(power=1.5));
		/* To force qtoch < current flow: cho
		   if(qtoch > h[vect]*w*w/dt)
			   qtoch = h[vect]*w*w/dt;
		*/
                   h[vect]=h[vect]-qtoch*dt/(w*w);
                }
		else
		{
                   qtoch=-1.*(hch[node+link*NODES]-htop)*(wid+2.*z*depth)*w/dt;
		/* To force qtoch < current flow: cho
		   if(qtoch > h[vect]*w*(w+wid+2.*z*depth)/dt)
			   qtoch = h[vect]*w*(w+wid+2.*z*depth)/dt;
		*/
                   h[vect]=h[vect]-qtoch*dt/(w*(w+wid+2.*z*depth));
                }   

		if(qtoch!=0)
		{
		   CH_DEPTH(link,node,discharge_fd,dt,z,depth,wid,qtoch,hch,&dhch);
		   hch[node+link*NODES]=hch[node+link*NODES]+dhch;
                }

	        if(hch[node+link*NODES] <0) 
		{ 
		   CRASH(discharge_fd,2,vect,link,node,itime,
			 space,dt,window,Inter,h,vinf,yes_intercep,
			 yes_inf,&vintercep,&vsur2,yes_lake,&vlake2,elev,
			 &vinftot);

                   if(yes_write) 
		   WRITE_FILES(buf,windex=2,itime,dt,num_w,yes_w_surf_dep,
		   depth_fd,depth_file,yes_w_inf_dep,inf_fd,inf_dep_file,
		   yes_w_surf_moist,surf_moist_fd,surf_moist_file,
		   yes_w_inf_rate,inf_rate_fd,inf_rate_file,yes_w_dis_rain,
		   rindex,dis_rain_fd,dis_rain_file,h,yes_channel,
		   yes_priess,ltype,nx1,chn_row,chn_col,hch,yp,bel,
		   depth_tmp,inf_tmp,surf_moist_tmp,inf_rate_tmp,
		   dis_rain_tmp,nitrn,vinf,surf_moist,frate,rint,space,
		   yes_lake,elev,&colors);

		   goto PRINT; 

		}

		if(itime == niter) 
		{
		   if(hch[node+link*NODES]<depth) 
		   {
		       vsur2=vsur2+(wid+z*hch[node+link*NODES])* 
		       hch[node+link*NODES]*w;
		   }
                   else
		   {   
		       vsur2=vsur2+(wid+z*depth)*depth*w+
		       (hch[node+link*NODES]-depth)*(wid+2.*z*depth)*w;
		   }
                }
          }
       }
     }


/*!!!!!!!!!!!!!!!!!!!!!!!!
  OVERLAND ROUTING
!!!!!!!!!!!!!!!!!!!!!!!!*/

      for(row=0; row<nrows; row++)
      {
        for(col=0; col<ncols; col++)
        {
	  vect=space[row][col];
          if(vect==0) continue;

          for(l = -1; l <= 0; l++)
          {
            jj=row+l+1;
            kk=col-l;
            if(jj>nrows-1 || kk>ncols-1) continue;
	    vect2=space[jj][kk];
            if(vect2==0) continue;

	    if(yes_flow_out) 
	    {
	       set_flow_out_basin=0;
	       if(l==-1 && col==0)        set_flow_out_basin=1; 
	       if(l==-1 && col==ncols-2)  set_flow_out_basin=2; 
	       if(l==0  && row==0)        set_flow_out_basin=3; 
	       if(l==0  && row==nrows-2)  set_flow_out_basin=4; 
            }

	    if(yes_lake && lake_cat[vect] !=0 &&  lake_cat[vect2] !=0) continue;
	    if(yes_lake && (lake_cat[vect] != 0 || lake_cat[vect2] !=0))
	    {
               OV_LAKE(rman,vect,vect2,dmin,yes_dist_rough,elev,rough,h,dqov); 
	    }
	    else
	    {
               if(h[vect]>=dmin || h[vect2]>=dmin) 
	       OV_FLOW(dt,rman,row,col,vect,vect2,dmin,vectout,yes_dist_rough,
	       yes_flow_out,set_flow_out_basin,elev,rough,h,dqov,space,
	       &vout_region); 
            }

          }
        }
      }

/*!!!!!!!!!!!!!!!!!!!!!!!!!!
  EXPLICIT CHANNEL ROUTING
!!!!!!!!!!!!!!!!!!!!!!!!!!*/

     if(yes_channel) 
     { 
       for(link=1; link<=nlinks; link++)
       {
	 nodetmp=nx1[link]-1;
	 if(ltype[link]==4) nodetmp=nx1[link];
         for(node=1; node<=nodetmp; node++)
         {
	    row1=chn_row[node+link*NODES];
	    col1=chn_col[node+link*NODES];
	    if(node<nodetmp || link==linkout)
	    {
	       row2=chn_row[node+link*NODES+1];
	       col2=chn_col[node+link*NODES+1];
	       itmp=link;
            }
	    else
	    {
	       row2=chn_row[1+backdep[link]*NODES];
	       col2=chn_col[1+backdep[link]*NODES];
	       itmp=backdep[link];
            }
	    vect=space[row1][col1];
	    vect2=space[row2][col2];

	    elev1=(double)elev[vect];
	    elev2=(double)elev[vect2];

					      /* within the lake links */
            if(ltype[link]==4 && itmp==link)  continue;  
	    if(ltype[link]==4 && itmp!=link)  /* at outlet of lake links */
	    {
	       if(lake_el[lake_cat[vect]]-bel[node+link*NODES] > 0)
	       {
		  /* chn_dep represents spillway coefficient for lakes */
	          dummy=sqrt(2.0*9.81)*sqrt(1./3.)*(2./3.)*
	          pow((double)(lake_el[lake_cat[vect]]-bel[node+link*NODES]),
		  (double)1.5)*chn_dep[node+link*NODES]*
		  bottom[node+link*NODES];
	          qtolake[lake_cat[vect]]=qtolake[lake_cat[vect]]-dummy;
		  dqch[1+itmp*NODES]=dqch[1+itmp*NODES]+dummy;
		  continue;
               }
            }
	    else
	    {
	       CH_FLOW(link,node,itmp,vect,vect2,ltype,elev1,elev2,
		    yes_chn_unif,bottom,chn_dep,sslope,strick,hch,dqch,dt);
            }
         }

       }
     }

/*!!!!!!!!!!!!!!!!!!!!!!!!!!
  IMPLICIT CHANNEL ROUTING
!!!!!!!!!!!!!!!!!!!!!!!!!!*/

    if(yes_priess)
       {
       for(link=1; link<LINKS; link++)
          {
	  for(node=1; node<nx1[link]; node++)
	     {

             qlat[node+link*NODES]=0.0;
	     htop=chn_dep[node+link*NODES] + h[con_vect[node+link*NODES]];
	     flowd=yp[node+link*NODES]-bel[node+link*NODES];
	     D=flowd - chn_dep[node+link*NODES];

             qtoch=2.0*w*(2.0/3.0)*sqrt((double)(2.0*9.81/3.0))*pow((double)
                   (h[con_vect[node+link*NODES]]),(double)(3.0/2.0));
	  /* To force qtoch < current flow: cho
	     if(qtoch > h[con_vect[node+link*NODES]]*w*w/dt)
		   qtoch = h[con_vect[node+link*NODES]]*w*w/dt;
	  */
             qlat[node+link*NODES]=qtoch/w;
	     h[con_vect[node+link*NODES]]=h[con_vect[node+link*NODES]]
		        		     -qtoch*dt/(w*w);

          }
       }


       flow_route(iter,itime,delt,delx,alpha,beta,theta,grav,
		  depend,backdep,nx1,bel,yp,qp,strick,bottom,
                  chn_dep,sslope,sslope2,ltype,ndep,yfirst,
                  ystep,qmin,marea0,parea0,mtw0,ptw0,mk0,pk0,
		  marea1,parea1,mtw1,ptw1,mk1,pk1,numqpipe,yes_drain,
		  /* the following were added by FLO 10-8-94 to 
		  allow breakpoint description of x-sections */
		  xarea,xtw,xk,numhts,ht_spc,maxtab,table_num,NUMBPTS,
		  lowspot,highspot,normout,tdrain);

       if(yes_phyd)
       {
	  fprintf(iunit9,"\n %7.2f ",(float)itime*delt);
	  for(node=1; node<=ptot; node++)
	  {
	     fprintf(iunit9,"%9.2f ",qp[pnode[node]+plink[node]*NODES]);
          }
       }

       /* Mass balance computation  */

       if(itime==niter)
       {
          section(bottom,sslope,sslope2,strick,yp,bel,farea,
                  dum1,dum2,dum3,nx1,ltype,chn_dep,
                  marea0,parea0,mtw0,ptw0,mk0,pk0,
                  marea1,parea1,mtw1,ptw1,mk1,pk1,
                  xarea,xtw,xk,numhts,ht_spc,maxtab,
                  table_num,NUMBPTS);

          for(link=1; link<LINKS; link++)
             {
	     for(node=1; node<=NODES; node++)
	        {
                if(ltype[link]==1 || ltype[link]==8)
	          {
		  if(node<nx1[link] || (node<=nx1[link] && link==nlinks)
                     || (node<=nx1[link] && ltype[backdep[link]]==4))
		    {

                       /* COMMENTED OUT: THE OLD WAY
		        * vsur2=vsur2+w*(yp[node+link*NODES]-
                        * bel[node+link*NODES])*
			* ((yp[node+link*NODES]-bel[node+link*NODES])*sslope
			* [node+link*NODES]+bottom[node+link*NODES]);
                        */

                       vsur2=vsur2+farea[node+link*NODES]*w;

                    }
                  }
                }
             }
         }

     }

/*!!!!!!!!!!!!!!!!!!!!!!!!
  OUTFLOW DISCHARGE
!!!!!!!!!!!!!!!!!!!!!!!!*/

     qout=0;
     if(vectout != '\0' && !yes_priess)
     {
        hout=h[vectout]; 
        qoutov=w*alfaovout*pow((base=hout),(power=1.667));
     /* To force qoutov < current flow: cho
	if(qoutov > h[vectout]*w*w/dt)
	   qoutov = h[vectout]*w*w/dt;
     */
        h[vectout]=h[vectout]-qoutov*dt/(w*w);
        qout=qoutov;
     }
     vout=vout+qoutov*dt;

     if(yes_channel && linkout!='\0') 
     {
        hout=hch[nodeout+linkout*NODES];
        depth=chn_dep[nodeout+linkout*NODES];
        wid=bottom[nodeout+linkout*NODES];
        z=sslope[nodeout+linkout*NODES];
        manout=1./strick[nodeout+linkout*NODES];
        if(hout <= depth) 
        {
           wetpout=wid+2.*hout*sqrt((double)(1.+z*z));
           areaout=hout*(wid+z*hout);
        }
        else 
        {
           wetpout=wid+2.*depth*sqrt((double)(1.+z*z));
           areaout=depth*(wid+z*depth)+(hout-depth)*(wid+2.*z*depth);
        }
        qoutch=(1./manout)*pow(base=areaout,power=1.667)*
      	       pow(base=(1./wetpout),power=0.667)*sqrt(sout);
        dhch=0;
        qtoch=-1.0*qoutch;
        if(qtoch!=0)
        {
          CH_DEPTH(linkout,nodeout,discharge_fd,dt,z,depth,wid,qtoch,hch,&dhch);
          hch[nodeout+linkout*NODES]=hch[nodeout+linkout*NODES]+dhch;
        }
     }


     if(yes_priess)
     {
	qoutch=qp[nx1[nlinks]+nlinks*NODES];
     }

     qout=qoutov+qoutch;  /* this is the total outflow discharge. */
     vout=vout+qoutch*dt; /* we have added overland outflow already. */

     if(qout > qpeak) 
     {
       qpeak=qout;
       tpeak=itime*dt/60.;       /* time to peak in minutes   */
     }

     if(!yes_quiet) fprintf(stderr,
                    "iteration, time (min), & discharge : %d  %f   %f\n",
                    itime,(float)(itime*dt/60),qout*uvol);
 
     fprintf(discharge_fd,"%8.2f  %9.2f \n", (float)itime*dt/60.,qout*uvol);

}

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!                                              !!!!!
!!!!!          TIME LOOP CLOSES HERE               !!!!!
!!!!!                                              !!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/


PRINT: 

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Writing the end of discharge file 
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

if(!yes_english_unit)       /* write in SI units */
{
   fprintf(discharge_fd,
           "\n time to peak= %9.3f (min) \n peak discharge (cms)= %9.2f \n",
           tpeak,qpeak*uvol);

   fprintf(discharge_fd," rainfall volume (cu. m)= %20.2f\n",vin*uvol);

   if(yes_lake) fprintf(discharge_fd,
                " initial volume of lake (cu. m)= %20.2f\n", vlake1*uvol);
   if(yes_lake) fprintf(discharge_fd,
   " change in lake volume (cu. m)= %20.2f  percent of total mass= %10.7f\n", 
   (vlake2-vlake1)*uvol,100.*(vlake2-vlake1)/vin); 

   if(yes_intercep) fprintf(discharge_fd,
   " interception volume (cu. m)= %20.2f   percent of total mass= %10.7f\n",
   vintercep*uvol,100.*vintercep/vin);

   /*
   fprintf(discharge_fd," initial surface volume (cu. m)= %20.2f \n end-of-simulation surface volume (cu. m)= %20.2f\n", vsur1*uvol,vsur2*uvol); 
   fprintf(discharge_fd,
   " percent of change in surface volume (cu. m)= %10.7f\n", 
   (vsur2-vsur1)*100./vin); 
   */

   fprintf(discharge_fd,
   " outflow volume (cu. m)= %20.2f    percent of total mass= %10.7f\n", 
   vout*uvol, 100.*vout/vin); 

   if(yes_inf) fprintf(discharge_fd,
   "infiltration volume (cu. m)= %20.2f    percent of total mass= %10.7f\n", 
   vinftot*uvol,100.*vinftot/vin); 

   if(yes_flow_out) fprintf(discharge_fd, 
   "volume flowing out of region (cu. m)= %20.2f  percent of total mass= %10.7f\n", vout_region*uvol,100*vout_region/vin); 
}
else
{                         /* write in english unit */
   fprintf(discharge_fd,
           "\n time to peak= %9.3f (min) \n peak discharge (cfs)= %9.2f \n",
           tpeak,qpeak*uvol);

   fprintf(discharge_fd," rainfall volume (cu. ft)= %20.2f\n",vin*uvol);

   if(yes_lake) fprintf(discharge_fd,
                " initial volume of lake (cu. ft)= %20.2f\n", vlake1*uvol);
   if(yes_lake) fprintf(discharge_fd,
   " change in lake volume (cu. ft)= %20.2f  percent of total mass= %10.7f\n", 
   (vlake2-vlake1)*uvol,100.*(vlake2-vlake1)/vin); 

   if(yes_intercep) fprintf(discharge_fd,
   " interception volume (cu. ft)= %20.2f   percent of total mass= %10.7f\n",
   vintercep*uvol,100.*vintercep/vin);

   /*
   fprintf(discharge_fd," initial surface volume (cu. ft)= %20.2f \n end-of-simulation surface volume (cu. ft)= %20.2f\n", vsur1*uvol,vsur2*uvol); 
   fprintf(discharge_fd,
   " percent of change in surface volume (cu. ft)= %10.7f\n", 
   (vsur2-vsur1)*100./vin); 
   */

   fprintf(discharge_fd,
   " outflow volume (cu. ft)= %20.2f    percent of total mass= %10.7f\n", 
   vout*uvol, 100.*vout/vin); 

   if(yes_inf) fprintf(discharge_fd,
   " infiltration volume (cu. ft)= %20.2f    percent of total mass= %10.7f\n", 
   vinftot*uvol,100.*vinftot/vin); 

   if(yes_flow_out) fprintf(discharge_fd, 
   "volume flowing out of region (cu. ft)= %20.2f  percent of total mass= %10.7f\n", vout_region*uvol,100*vout_region/vin); 

}

/*
fprintf(discharge_fd,"\n percent of total mass conservation= %12.7f\n",100.*(vsur2-vsur1+vlake2-vlake1+vout+vinftot+vintercep+vout_region)/vin);

if( abs(1.-(vsur2-vsur1+vlake2-vlake1+vout+vinftot+vintercep+vout_region)/vin) > 0.01)
fprintf(discharge_fd,"\n WARNNING: The mass nonconservation exceeds 1 percent. This may be due to oscillating discharge hydrograph. If so, keep doing the same run with halving the time step a few times. If the problem still persists, report this as a bug.\n");
*/

/*!!!!!!!!!!!!!!!!!!!!!!!!!
  Closing maps & files
!!!!!!!!!!!!!!!!!!!!!!!!!*/

if(yes_mask) G_close_cell(mask_fd);
G_close_cell(elev_fd);
if(yes_dist_rough) G_close_cell(roughness_fd);
if(yes_inf) {
   G_close_cell(soil_K_fd);
   G_close_cell(soil_H_fd);
   G_close_cell(soil_P_fd);
   G_close_cell(soil_M_fd);
}
if(yes_redist_vary) {
   G_close_cell(soil_LN_fd);
   G_close_cell(soil_RS_fd);
}
fclose(discharge_fd);
if(yes_gage) fclose(rain_fd);
if(yes_channel || yes_priess) fclose(iunit);

DRAIN:

/*!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Writing water discharge & surface profile when draining
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!*/

if(yes_drain || yes_bkwater)
{
   for(link=1; link<=nlinks; link++)
   {
      for(node=1; node<=nx1[link]; node++)
      {
	 if(ltype[link]!=4)      /* for link types 1, 8, and 2 */
	 {
	    fprintf(yunit,"%d %d %f\n",link,node,
		    yp[node+link*NODES]-bel[node+link*NODES]);
         }
	 else                    /* link type 4, reservoirs  */
	 {
	    fprintf(yunit,"%d %d %f\n",link,node,sslope[node+link*NODES]);
         }

	 fprintf(qunit,"%d %d %f\n",link,node,qp[node+link*NODES]);
      }
   }
}

return 0;

}

/*EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
NNNN                                    NNNN
NNNN       END OF MAIN PROGRAM          NNNN
NNNN                                    NNNN
DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD*/
