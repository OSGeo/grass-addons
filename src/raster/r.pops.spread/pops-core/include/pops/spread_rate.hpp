/*
 * PoPS model - Spread rate computation
 *
 * Copyright (C) 2015-2020 by the authors.
 *
 * Authors: Anna Petrasova <akratoc gmail com>
 *
 * The code contained herein is licensed under the GNU General Public
 * License. You may obtain a copy of the GNU General Public License
 * Version 2 or later at the following locations:
 *
 * http://www.opensource.org/licenses/gpl-license.html
 * http://www.gnu.org/copyleft/gpl.html
 */

#ifndef POPS_SPREAD_RATE_HPP
#define POPS_SPREAD_RATE_HPP

#include <tuple>
#include <vector>
#include <cmath>

namespace pops {

typedef std::tuple<int, int, int, int> BBoxInt;
typedef std::tuple<double, double, double, double> BBoxFloat;
typedef std::tuple<bool, bool, bool, bool> BBoxBool;

/**
 * Class storing and computing step spread rate for one simulation.
 */
template <typename Raster>
class SpreadRate {
private:
    int width;
    int height;
    // the west-east resolution of the pixel
    double west_east_resolution;
    // the north-south resolution of the pixel
    double north_south_resolution;
    unsigned num_steps;
    std::vector<BBoxInt> boundaries;
    std::vector<BBoxFloat> rates;

    /**
     * Return tuple of bools indicating
     * wheather the infection touched the edge cells
     * in each direction, indicating the infection is out of bounds.
     */
    BBoxBool is_out_of_bounds(const BBoxInt bbox)
    {
        int n, s, e, w;
        bool bn = false, bs = false, be = false, bw = false;
        std::tie(n, s, e, w) = bbox;
        if (n == 0)
            bn = true;
        if (s == (height - 1))
            bs = true;
        if (w == 0)
            bw = true;
        if (e == (width - 1))
            be = true;

        return std::make_tuple(bn, bs, be, bw);
    }
    /**
     * Finds bbox of infections and returns
     * north, south, east, west coordinates (as number of rows/cols),
     * If there is no infection, sets -1 to all directions.
     */
    BBoxInt infection_boundary(const Raster &raster)
    {
        int n = height - 1;
        int s = 0;
        int e = 0;
        int w = width - 1;
        bool found = false;
        for (int i = 0; i < height; i++) {
            for (int j = 0; j < width; j++) {
                auto value = raster(i, j);
                if (value > 0) {
                    found = true;
                    if (i < n)
                        n = i;
                    if (i > s)
                        s = i;
                    if (j > e)
                        e = j;
                    if (j < w)
                        w = j;
                }
            }
        }
        if (found)
            return std::make_tuple(n, s, e, w);
        else
            return std::make_tuple(-1, -1, -1, -1);
    }

    /**
     * Checks if boundary is valid, if not,
     * it means there is no infection at all.
     */
    bool is_boundary_valid(const BBoxInt bbox)
    {
        int n, s, e, w;
        std::tie(n, s, e, w) = bbox;
        if (n == -1)
            return false;
        return true;
    }

public:
    SpreadRate(const Raster &raster, double ew_res, double ns_res,
               unsigned num_steps)
        : width(raster.cols()), height(raster.rows()),
          west_east_resolution(ew_res), north_south_resolution(ns_res),
          num_steps(num_steps),
          boundaries(num_steps + 1, std::make_tuple(0, 0, 0, 0)),
          rates(num_steps, std::make_tuple(std::nan(""), std::nan(""),
                                           std::nan(""), std::nan("")))
    {
        boundaries.at(0) = infection_boundary(raster);
    }

    SpreadRate() = delete;

    /**
     * Returns rate for certain year of simulation
     */
    const BBoxFloat &step_rate(unsigned step) const { return rates[step]; }

    /**
     * Computes spread rate in n, s, e, w directions
     * for certain simulation year based on provided
     * infection raster and bbox of infection in previous year.
     * Unit is distance (map units) per year.
     * If spread rate is zero and the bbox is touching the edge,
     * that means spread is out of bounds and rate is set to NaN.
     */
    void compute_step_spread_rate(const Raster &raster, unsigned step)
    {
        BBoxInt bbox = infection_boundary(raster);
        boundaries.at(step + 1) = bbox;
        if (!is_boundary_valid(bbox)) {
            rates.at(step) = std::make_tuple(std::nan(""), std::nan(""),
                                             std::nan(""), std::nan(""));
            return;
        }
        int n1, n2, s1, s2, e1, e2, w1, w2;
        std::tie(n1, s1, e1, w1) = boundaries.at(step);
        std::tie(n2, s2, e2, w2) = bbox;
        double n_rate = ((n1 - n2) * north_south_resolution);
        double s_rate = ((s2 - s1) * north_south_resolution);
        double e_rate = ((e2 - e1) * west_east_resolution);
        double w_rate = ((w1 - w2) * west_east_resolution);

        bool bn, bs, be, bw;
        std::tie(bn, bs, be, bw) = is_out_of_bounds(bbox);
        if (n_rate == 0 && bn)
            n_rate = std::nan("");
        if (s_rate == 0 && bs)
            s_rate = std::nan("");
        if (e_rate == 0 && be)
            e_rate = std::nan("");
        if (w_rate == 0 && bw)
            w_rate = std::nan("");

        rates.at(step) = std::make_tuple(n_rate, s_rate, e_rate, w_rate);
    }
};

/**
 * Computes average spread rate in n, s, e, w directions
 * from vector of spread rates.
 * Checks if any rate is nan to not include it in the average.
 */
template <typename Raster>
BBoxFloat average_spread_rate(const std::vector<SpreadRate<Raster>> &rates,
                              unsigned step)
{
    // loop through stochastic runs
    double n, s, e, w;
    int size_n = 0, size_s = 0, size_e = 0, size_w = 0;
    double avg_n = 0, avg_s = 0, avg_e = 0, avg_w = 0;
    for (unsigned i = 0; i < rates.size(); i++) {
        std::tie(n, s, e, w) = rates[i].step_rate(step);
        if (!std::isnan(n)) {
            avg_n += n;
            size_n++;
        }
        if (!std::isnan(s)) {
            avg_s += s;
            size_s++;
        }
        if (!std::isnan(e)) {
            avg_e += e;
            size_e++;
        }
        if (!std::isnan(w)) {
            avg_w += w;
            size_w++;
        }
    }
    avg_n = size_n ? avg_n / size_n : std::nan("");
    avg_s = size_s ? avg_s / size_s : std::nan("");
    avg_e = size_e ? avg_e / size_e : std::nan("");
    avg_w = size_w ? avg_w / size_w : std::nan("");

    return std::make_tuple(avg_n, avg_s, avg_e, avg_w);
}

} // namespace pops
#endif // POPS_SPREAD_RATE_HPP
