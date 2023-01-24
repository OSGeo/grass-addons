#include <math.h>

double ndvimin, ndvimax;
/*Biome Type Configuration variables*/
double tclosemin, topenmax;
double vpdclose, vpdopen;
double topt, beta, k;
double ga, gtot, gch;
double b1, b2, b3, b4;
/*Biome Type Configuration is valid=1, is invalid=0*/
int valid_conf;

/*Variables*/
double e_sat, b, t;
double gs, g0, mtday;
double rh, vpd, mvpd;
double fracveg, latent, MaMw;
double Cp, psi, gtotc, Delta;
double rho, Esoil, Ecanopy;

double fc(double ndvi)
{
    /*Fraction of vegetation cover*/
    ndvimin = 0.05;
    ndvimax = 0.95;
    double fc;
    if (ndvi < 0.05)
        fc = 0.0;
    if (ndvi > 0.95)
        fc = 1.0;
    if (ndvi > 0.05 && ndvi < 0.95)
        fc = ((ndvi - ndvimin) / (ndvimax - ndvimin));
    return fc;
}

double bdpc(double ndvi, double b1, double b2, double b3, double b4)
{
    /*Biome dependent potential conductance (g0 in Zhang et al, 2010. WRR)*/
    return (1.0 / (b1 + b2 * exp(-b3 * ndvi)) + b4);
}

double mTday(double tday, double tclosemin, double topenmax, double topt,
             double beta)
{
    /*Temperature dependent reduction function of the biome dependent potential
     * conductance*/
    if (tday <= tclosemin)
        return 0.01;
    else if (tday >= topenmax)
        return 0.01;
    else
        return (exp(-((tday - topt) / beta) * ((tday - topt) / beta)));
}

double mVPD(double vpd, double vpdclose, double vpdopen)
{
    /*VPD dependent reduction function of the biome dependent potential
     * conductance*/
    if (vpd <= vpdopen)
        return 1.0;
    else if (vpd >= vpdclose)
        return 1.0;
    else
        return ((vpdclose - vpd) / (vpdclose - vpdopen));
}

double esat(tday)
{
    /*From FAO56, output is in [Pa]*/
    return (1000 * 0.6108 * exp(17.27 * tday / (tday + 237.3)));
}

double vpdeficit(double rh, double tday)
{
    /*From FAO56, vpd is esat - eact*/
    e_sat = esat(tday);
    return ((1.0 - rh) * e_sat);
}

double rhumidity(double sh, double tday, double patm)
{
    /*http://en.wikipedia.org/wiki/Humidity#Specific_humidity
    Output  [0.0-1.0]*/
    e_sat = esat(tday);
    /*printf("e_sat\t=%f\t[Pa]\n",e_sat);*/
    b = (0.622 + sh) * e_sat;
    return (sh * patm / b);
}

double slopesvpcurve(double tday)
{
    /*From FAO56, output is in [Pa/C]*/
    e_sat = esat(tday);
    return (4098.0 * e_sat / pow(tday + 237.3, 2));
}

double rhoair(double dem, double tday)
{
    /*Requires T in Kelvin*/
    t = tday + 273.15;
    b = ((t - (0.00627 * dem)) / t);
    return (349.467 * pow(b, 5.26) / t);
}

double zk_daily_et(double biome_type, double ndvi, double tday, double sh,
                   double patm, double rnetd, double soilHF, double dem)
{
    /*ETa global model from Zhang et al 2010. A continuous satellite derived
     * global record of land surface evapotranspiration from 1983 to 2006. WRR
     * 46*/
    b4 = 0.0; /*except for WSV with NDVI > 0.64*/
    if (biome_type == 0) {
        /*BENF*/
        tclosemin = -8.0;
        topenmax = 40.0;
        vpdclose = 2800.0;
        vpdopen = 500.0;
        topt = 12.0;
        beta = 25.0;
        k = 150.0;
        ga = 0.03;
        gtot = 0.002;
        gch = 0.08;
        b1 = 208.3;
        b2 = 8333.3;
        b3 = 10.0;
        /* Configuration is valid*/
        valid_conf = 1;
    }
    else if (biome_type == 1) {
        /*TENF*/
        tclosemin = -8.0;
        topenmax = 40.0;
        vpdclose = 2800.0;
        vpdopen = 500.0;
        topt = 25.0;
        beta = 25.0;
        k = 200.0;
        ga = 0.03;
        gtot = 0.004;
        gch = 0.08;
        b1 = 133.3;
        b2 = 888.9;
        b3 = 6.0;
        /* Configuration is valid*/
        valid_conf = 1;
    }
    else if (biome_type == 2) {
        /*EBF*/
        tclosemin = -8.0;
        topenmax = 50.0;
        vpdclose = 4000.0;
        vpdopen = 500.0;
        topt = 40.0;
        beta = 40.0;
        k = 300.0;
        ga = 0.03;
        gtot = 0.006;
        gch = 0.01;
        b1 = 57.7;
        b2 = 769.2;
        b3 = 4.5;
        /* Configuration is valid*/
        valid_conf = 1;
    }
    else if (biome_type == 4) {
        /*DBF*/
        tclosemin = -6.0;
        topenmax = 45.0;
        vpdclose = 2800.0;
        vpdopen = 650.0;
        topt = 28.0;
        beta = 25.0;
        k = 200.0;
        ga = 0.04;
        gtot = 0.002;
        gch = 0.01;
        b1 = 85.8;
        b2 = 694.7;
        b3 = 4;
        /* Configuration is valid*/
        valid_conf = 1;
    }
    else if (biome_type == 6) {
        /*CSH*/
        tclosemin = -8.0;
        topenmax = 45.0;
        vpdclose = 3300.0;
        vpdopen = 500.0;
        topt = 19.0;
        beta = 20.0;
        k = 400.0;
        ga = 0.01;
        gtot = 0.001;
        gch = 0.04;
        b1 = 202.0;
        b2 = 4040.4;
        b3 = 6.5;
        /* Configuration is valid*/
        valid_conf = 1;
    }
    else if (biome_type == 7) {
        /*OSH*/
        tclosemin = -8.0;
        topenmax = 40.0;
        vpdclose = 3700.0;
        vpdopen = 500.0;
        topt = 10.0;
        beta = 30.0;
        k = 50.0;
        ga = 0.005;
        gtot = 0.012;
        gch = 0.04;
        b1 = 178.6;
        b2 = 178.6;
        b3 = 8;
        /* Configuration is valid*/
        valid_conf = 1;
    }
    else if (biome_type == 8 && ndvi < 0.64) {
        /*WSV && ndvi < 0.64*/
        tclosemin = -8.0;
        topenmax = 50.0;
        vpdclose = 3200.0;
        vpdopen = 500.0;
        topt = 32.0;
        beta = 28.0;
        k = 900.0;
        ga = 0.002;
        gtot = 0.0018;
        gch = 0.04;
        b1 = 0.2;
        b2 = 24000;
        b3 = 6.5;
        /* Configuration is valid*/
        valid_conf = 1;
    }
    else if (biome_type == 8 && ndvi > 0.64) {
        /*WSV && ndvi > 0.64*/
        tclosemin = -8.0;
        topenmax = 50.0;
        vpdclose = 3200.0;
        vpdopen = 500.0;
        topt = 32.0;
        beta = 28.0;
        k = 900.0;
        ga = 0.002;
        gtot = 0.0018;
        gch = 0.04;
        b1 = 57.1;
        b2 = 3333.3;
        b3 = 8.0;
        b4 = -0.01035;
        /* Configuration is valid*/
        valid_conf = 1;
    }
    else if (biome_type == 9) {
        /*SV*/
        tclosemin = -8.0;
        topenmax = 40.0;
        vpdclose = 5000.0;
        vpdopen = 650.0;
        topt = 32.0;
        beta = 30.0;
        k = 800.0;
        ga = 0.001;
        gtot = 0.001;
        gch = 0.04;
        b1 = 790.9;
        b2 = 8181.8;
        b3 = 10.0;
        /* Configuration is valid*/
        valid_conf = 1;
    }
    else if (biome_type == 10) {
        /*GRS*/
        tclosemin = -8.0;
        topenmax = 40.0;
        vpdclose = 3800.0;
        vpdopen = 650.0;
        topt = 20.0;
        beta = 30.0;
        k = 500.0;
        ga = 0.001;
        gtot = 0.001;
        gch = 0.04;
        b1 = 175.0;
        b2 = 2000;
        b3 = 6.0;
        /* Configuration is valid*/
        valid_conf = 1;
    }
    else if (biome_type == 12) {
        /*CRP*/
        tclosemin = -8.0;
        topenmax = 45.0;
        vpdclose = 3800.0;
        vpdopen = 650.0;
        topt = 20.0;
        beta = 30.0;
        k = 450.0;
        ga = 0.005;
        gtot = 0.003;
        gch = 0.04;
        b1 = 105.0;
        b2 = 300.0;
        b3 = 3.0;
        /* Configuration is valid*/
        valid_conf = 1;
    }
    else {
        /* Configuration is invalid*/
        valid_conf = 0;
    }
    // G_message("Valid Biome type? %i",valid_conf);
    /*Compute potential conductance for this biome and this NDVI*/
    g0 = bdpc(ndvi, b1, b2, b3, b4);
    /*Preprocessing for Surface conductance (gs) in PM (FAO56), gc in this
     * article*/
    mtday = mTday(tday, tclosemin, topenmax, topt, beta);
    /*relative humidity*/
    rh = rhumidity(sh, tday, patm);
    // G_message("rh\t=%f\t[-]",rh);
    vpd = vpdeficit(rh, tday);
    // G_message("vpd\t=%f\t\t[Pa]",vpd);
    mvpd = mVPD(vpd, vpdclose, vpdopen);
    /*Actually computing Surface conductance (gs) in PM (FAO56), gc in this
     * article*/
    gs = g0 * mtday * mvpd;
    // G_message("rs\t=%f\t[s/m]",1/gs);
    /*Fraction of vegetation cover*/
    fracveg = fc(ndvi);
    // G_message("fc\t=%f\t[-]", fracveg);
    /*preprocessing for soil Evaporation*/
    latent = 2.45;                     /*MJ/Kg FAO56*/
    MaMw = 0.622;                      /* - FAO56*/
    Cp = 1.013 * 0.001;                /* MJ/Kg/C FAO56 */
    psi = patm * Cp / (MaMw * latent); /*psi = patm * 0.6647 / 1000*/
    // G_message("psi\t=%f\t[Pa/C]",psi);
    gtotc = gtot * ((273.15 + tday) / 293.13) * (101300.0 / patm);
    Delta = slopesvpcurve(tday); /*slope in Pa/C*/
    // G_message("Delta\t=%f\t[de/dt]",Delta);
    rho = rhoair(dem, tday);
    // G_message("rho\t=%f\t[kg/m3]",rho);
    /*soil Evaporation*/
    Esoil = pow(rh, vpd / k) *
            (Delta * (1 - fracveg) * (rnetd - soilHF) + rho * Cp * vpd * ga) /
            (Delta + psi * ga / gtotc);
    /*Canopy evapotranspiration*/
    Ecanopy = (Delta * fracveg * (rnetd - soilHF) + rho * Cp * vpd * ga) /
              (Delta + psi * (1.0 + ga / gs));
    // G_message("------------------------------------------------------");
    // G_message("Esoil\t=%f\t[mm/d]", Esoil);
    // G_message("Ecanopy\t=%f\t[mm/d]", Ecanopy);
    double out;
    if (valid_conf == 1) {
        out = (1 - fracveg) * Esoil + fracveg * Ecanopy;
    }
    else {
        out = -28768;
    }
    // G_message("E\t=%f\t[mm/d]",out);
    // G_message("------------------------------------------------------");
    return (out);
}
