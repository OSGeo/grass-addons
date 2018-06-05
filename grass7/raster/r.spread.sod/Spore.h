/*
 * SOD model - spore simulation
 *
 * Copyright (C) 2015-2017 by the authors.
 *
 * Authors: Zexi Chen (zchen22 ncsu edu)
 *          Vaclav Petras (wenzeslaus gmail com)
 *          Anna Petrasova (kratochanna gmail com)
 *
 * The code contained herein is licensed under the GNU General Public
 * License. You may obtain a copy of the GNU General Public License
 * Version 2 or later at the following locations:
 *
 * http://www.opensource.org/licenses/gpl-license.html
 * http://www.gnu.org/copyleft/gpl.html
 */


#ifndef SPORE_H
#define SPORE_H

#include "Img.h"

#include <random>


enum Rtype
{
    CAUCHY, CAUCHY_MIX          // NO means that there is no wind
};

class Sporulation
{
private:
    int width;
    int height;
    // the west-east resolution of the pixel
    int w_e_res;
    // the north-south resolution of the pixel
    int n_s_res;
    Img sp;
    std::default_random_engine generator;
public:
    Sporulation(unsigned random_seed, const Img &size);
    void SporeGen(const Img& I, const double *weather,
                  double weather_value, double rate);
    void SporeSpreadDisp_singleSpecies(Img& S, Img& I, Img& I2,
                                       const Img& lvtree_rast, std::vector<std::tuple<int, int> > &outside_spores, Rtype rtype,
                                       const double *weather, double weather_value,
                                       double scale1, double kappa = 2,
                                       Direction wdir = NONE, double scale2 = 0.0,
                                       double gamma = 0.0);
    void SporeSpreadDisp(Img& S_umca, Img& S_oaks, Img& I_umca,
                         Img& I_oaks, const Img& lvtree_rast, Rtype rtype,
                         const double *weather, double weather_value,
                         double scale1, double kappa = 2,
                         Direction wdir = NONE, double scale2 = 0.0,
                         double gamma = 0.0);
};

#endif
