#include<stdio.h>
#include<math.h>
#include<stdlib.h>

    /* Chen et al., 2005. IJRS 26(8):1755-1762.
     * Estimation of daily evapotranspiration using a two-layer remote sensing model.
     * 
     * d = zero plane displacement (m)
     * z0 = surface roughness length gouverning heat and vapour transfers (m)
     * h = vegetation height (m)
     * z = reference height of air temperature and humidity measurements (m)
     * u_z = wind speed at reference height z (m/s)
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
double ra(double d, double z0, double h, double z, double u_z,
	   double tempk_a, double tempk_v) 
{
    double ra_0, molength, u_star, psi, result;

    double vonKarman = 0.41;	/*von Karman constant */

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
    ra_0 = pow(log((z - d) / z0), 2) / (pow(vonKarman, 2) * u_z);
    
	/* psi, molength, u_star: Ambast S.K., Keshari A.K., Gosain A.K. 2002.
	 * An operational model for estimating evapotranspiration 
	 * through Surface Energy Partitioning (RESEP).
	 * International Journal of Remote Sensing, 23, pp. 4917-4930.
	 */ 
	u_star = vonKarman * u_z / log((z - d) / z0);
    molength =
	u_star * ((tempk_v + tempk_a) / 2) / (vonKarman * g *
					      (tempk_a - tempk_v) / u_z);
    if (((z - d) / molength) < -0.03) {
	psi = pow((1 - 16 * ((z - d) / molength)), 0.5);
    }
    else {
	psi = (1 + 5 * ((z - d) / molength));
    }
    
	/* psi & ra: Wang, C.Y., Niu Z., Tang H.J. 2002. 
	 * Technology of Earth Observation and Precision agriculture
	 * (Beijing: Science Press)
	 */ 
	result = ra_0 * (1 + (psi * (z - d) / z0));
    return result;
}


