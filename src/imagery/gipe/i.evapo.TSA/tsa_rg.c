#include<stdio.h>
#include<math.h>
#include<stdlib.h>

    /* Chen et al., 2005. IJRS 26(8):1755-1762.
     * Estimation of daily evapotranspiration using a two-layer remote sensing model.
     *
     * d = zero plane displacement (m)
     * z0 = surface roughness length gouverning heat and vapour transfers (m)
     * h = vegetation height (m)
     * w = weight of leaf (g)
     * z = reference height of air temperature and humidity measurements (m)
     * u_z = wind speed at reference height (m/s)
     * u_h = wind speed at plant height (m/s)
     * tempk_a = air temperature (at reference height z?) (K)
     * tempk_v = surface temperature of vegetation (K)
     *
     * If h (vegetation height) is given then d and z0 will be:
     * d = 0.63h
     * z0 = 0.13h
     * If d OR z0 are positive a relationship will find the second one
     * based on the equations above
     * If d AND z0 are positive they are used regardless of h values
     */ 
double rg(double d, double z0, double z0s, double h, double z, double w,
	   double u_z, double tempk_a, double tempk_v) 
{
    double alpha, molength, u_star, k_h, temp, result;

    double vonKarman = 0.41;	/* von Karman constant */

    double g = 9.81;		/*gravitational acceleration (m/s) */

    
	/*Deal with input of vegetation height */ 
	if (h > 0.0) {
	d = 0.63 * h;
	z0 = 0.13 * h;
	
	    /*Deal with input of displacement height */ 
    }
    else if (d > 0.0 && z0 < 0.0) {
	z0 = 0.13 * (d / 0.63);
	
	    /*Deal with input of surface roughness length */ 
    }
    else if (d < 0.0 && z0 > 0.0) {
	d = 0.63 * (z0 / 0.13);
    }
    if (h < 0.0) {
	h = d / 0.63;
    }
    
	/* molength, u_star: Ambast S.K., Keshari A.K., Gosain A.K. 2002.
	 * An operational model for estimating evapotranspiration 
	 * through Surface Energy Partitioning (RESEP).
	 * International Journal of Remote Sensing, 23, pp. 4917-4930.
	 */ 
	u_star = vonKarman * u_z / log((z - d) / z0);
    molength =
	u_star * ((tempk_v + tempk_a) / 2) / (vonKarman * g *
					      (tempk_a - tempk_v) / u_z);
    
	/* rv: Choudhury B.J. and Monteith J.L. 1988. 
	 * A four-layer model for the heat budget of homogeneous land surfaces.
	 * Quarterly Journal of the Royal Meteorological Society,114,pp.373-398.
	 */ 
	k_h = 1.5 * pow(vonKarman, 2) * (h - d) * u_z / (log((z - d) / z0));
    alpha = 1.0 / ((d / h) * log((h - d) / z0));
    temp = h * exp(alpha) / (alpha * k_h);
    result = temp * (exp(-alpha * z0s / h) - exp(-alpha * (d + z0) / h));
    return result;
}


