#include "local_proto.h"
using namespace std;
using namespace pcl;

int nn_average_distance_real(struct points *pnts, struct nearest *nna)
{
  int i, n = pnts->n, k=2, ind0 = 0;
  double sum_r;

  double *r;
  pcl::PointXYZ *pcl_r;
  
  r = (double *) G_malloc(n*3 * sizeof(double));
  memcpy(r, pnts->r, n*3 * sizeof(double));

  /* create new vector of 3D points (use template PointCloud from namespace pcl) */
  pcl::PointCloud<pcl::PointXYZ>::Ptr pcl_pnts (new pcl::PointCloud<pcl::PointXYZ>);
  pcl_pnts->width = n;
  pcl_pnts->height = 1;
  pcl_pnts->points.resize (pcl_pnts->width * pcl_pnts->height);

  pcl_r = &pcl_pnts->points[0];
  
  for (i=0; i<n; i++) {
    pcl_r->x = *r;
    pcl_r->y = *(r+1);
    pcl_r->z = *(r+2);
    pcl_r++;
    r += 3;
  }

  pcl::KdTreeFLANN<pcl::PointXYZ> kd_tree; /* create kd-tree */
  kd_tree.setInputCloud(pcl_pnts);

  std::vector<int> ind(k);
  std::vector<float> sqDist(k);

  double dx, dy, dz, dist;
  double *ri, *r0, *rk;

  /* Average distance to NN */
  sum_r = 0.;
  ri = &pnts->r[0];
  r0 = &pnts->r[0];
  for (size_t i=0; i < pcl_pnts->points.size (); i++) {
    if (kd_tree.nearestKSearch(pcl_pnts->points[i], k, ind, sqDist) > 0) {
      /* sqDist not used because double precision is needed (in PCL not supported yet) */
      rk = r0 + 3*ind[1];
      //dist = distance(ri, rk);
      dx = *rk - *ri;
      dy = *(rk+1) - *(ri+1);
      dz = *(rk+2) - *(ri+2);
      dist = sqrt(dx*dx + dy*dy + dz*dz);
      sum_r += dist;
    } // end nearestKSearch
    ri+=3;
  } // end i
  nna->rA = sum_r / pcl_pnts->points.size ();
  int pass=1;
  return pass;
}

extern "C" {
  void density(struct points *pnts, struct nna_par *xD, const char *Acol, struct nearest *nna)
  {
    if (xD->i3 == TRUE) { /* Minimum Enclosing Block */
      nna->A = Acol != NULL ? atof(Acol) : MBB(pnts); /* set volume specified by user or MBB volume */
      if (nna->A <= 0.)
	G_fatal_error(_("Volume must be greater than 0."));
    }

    if (xD->i3 == FALSE) { /* Minimum Enclosing Rectangle */
      nna->A = Acol != NULL ? atof(Acol) : MBR(pnts); /* set area specified by user or MBR area */
      if (nna->A <= 0.)
	G_fatal_error(_("Area must be greater than 0."));
    }
  
    nna->rho = pnts->n / nna->A; /* number of points per area/volume unit */
  }

  void nn_average_distance_expected(struct nna_par *xD, struct nearest *nna)
  {
    if (xD->i3 == TRUE) /* 3D */
      nna->rE = 0.55396/pow(nna->rho,1./3.); /* according to Chandrasekhar */
    if (xD->i3 == FALSE) /* 2D */
      nna->rE = 0.5/sqrt(nna->rho); /* according to Clark & Evans */
  }

  /* ---------------------------------
   * Two-tailed Student's test of significance of the mean
   * ---------------------------------*/

  void nn_results(struct points *pnts, struct nearest *nna)
  {
    G_message(_("\nNearest Neighbour Analysis results\n"));
    G_message(_("Number of points .......... %d\nArea/Volume .......... %f\nDensity of points ............ %f"), pnts->n, nna->A, nna->rho);
    G_message(_("Average distance between the nearest neighbours ............ %f m\nAverage expected distance between the nearest neighbours ... %f m\n Ratio rA/rE ... %f\n\nResults of two-tailed test of the mean\nNull hypothesis: Point set is randomly distributed within the region.\nStandard variate of the normal curve> c = %f"), nna->rA, nna->rE, nna->R, nna->c);

    /* two-tailed test of the mean */
    if (-1.96 < nna->c && nna->c < 1.96)
      G_message(_("Null hypothesis IS NOT REJECTED at the significance level alpha = 0.05"));
    if (-2.58 < nna->c && nna->c <= -1.96)
      G_message(_("Null hypothesis IS NOT REJECTED at the significance level alpha = 0.01 => point set is clustered.\nNull hypothesis CAN BE REJECTED at the significance level alpha = 0.05 => point set is randomly distributed."));
    if (1.96 <= nna->c && nna->c < 2.58)
      G_message(_("Null hypothesis IS NOT REJECTED at the significance level alpha = 0.01 => point set is dispersed.\nNull hypothesis CAN BE REJECTED at the significance level alpha = 0.05 => point set is randomly distributed."));
    if (nna->c <= -2.58)
      G_message(_("Null hypothesis CAN BE REJECTED at the significance levels alpha = 0.05 and alpha = 0.01 => point set is clustered."));
    if (nna->c >= 2.58)
      G_message(_("Null hypothesis CAN BE REJECTED at the significance levels alpha = 0.05 and alpha = 0.01 => point set is dispersed. %f"), nna->c);
  }

  void nn_statistics(struct points *pnts, struct nna_par *xD, struct nearest *nna)
  {
    double disp_rE, var_rE, sig_rE;

    if (xD->i3 == TRUE) { /* 3D */
      disp_rE = 0.347407742479038/pow(nna->rho,2./3.); /* disperzia, odvodene */
      var_rE = 0.0405357524727094/pow(nna->rho,2./3.); /* variancia, odvodene */
    }
    if (xD->i3 == FALSE) { /* 2D */
      disp_rE = 1./(nna->rho*PI); /* disperzia */
      var_rE = (4.0 - PI)/(4.0 * PI * pnts->n * nna->rho); /* variancia */
    }

    sig_rE = sqrt(var_rE); /* standard error of the mean distance */
    nna->c = (nna->rA - nna->rE) / sig_rE; /* standard variate of the normal curve */

    nn_results(pnts, nna);
  }
}
