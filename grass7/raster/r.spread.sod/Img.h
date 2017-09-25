/*
 * SOD model - raster manipulation
 *
 * Copyright (C) 2015-2017 by the authors.
 *
 * Authors: Zexi Chen (zchen22 ncsu edu)
 *          Vaclav Petras (wenzeslaus gmail com)
 *
 * The code contained herein is licensed under the GNU General Public
 * License. You may obtain a copy of the GNU General Public License
 * Version 2 or later at the following locations:
 *
 * http://www.opensource.org/licenses/gpl-license.html
 * http://www.gnu.org/copyleft/gpl.html
 */


#ifndef IMG_H
#define IMG_H

#include <iostream>
#include <string>
#include <cmath>
#include <algorithm>
#include <stdlib.h>


enum Direction
{
    N = 0, NE = 45, E = 90, SE = 135, S = 180, SW = 225, W = 270, NW = 315, NONE  // NO means that there is no wind
};

class Img
{
private:
    int width;
    int height;
    // the west-east resolution of the pixel
    int w_e_res;
    // the north-south resolution of the pixel
    int n_s_res;
    int *data;
public:
    Img();
    Img(Img&& other);
    Img(const Img& other);
    //Img(int width,int height);
    Img(const char *fileName);
    Img(int width, int height, int w_e_res, int n_s_res);
    Img(int width, int height, int w_e_res, int n_s_res, int value);
    Img& operator=(Img&& other);
    Img& operator=(const Img& other);

    int getWidth() const
    {
        return width;
    }

    int getHeight() const
    {
        return height;
    }

    int getWEResolution() const
    {
        return w_e_res;
    }

    int getNSResolution() const
    {
        return n_s_res;
    }

    void fill(int value)
    {
        std::fill(data, data + (width * height), value);
    }

    void zero()
    {
        std::fill(data, data + (width * height), 0);
    }

    template<class UnaryOperation>
    void for_each(UnaryOperation op)
    {
        std::for_each(data, data + (width * height), op);
    }

    const int& operator()(unsigned row, unsigned col) const
    {
        return data[row * width + col];
    }

    int& operator()(unsigned row, unsigned col)
    {
        return data[row * width + col];
    }

    Img operator+(const Img& image) const;
    Img operator-(const Img& image) const;
    Img operator*(const Img& image) const;
    Img operator/(const Img& image) const;
    Img operator*(double factor) const;
    Img operator/(double value) const;
    Img& operator+=(int value);
    Img& operator-=(int value);
    Img& operator*=(double value);
    Img& operator/=(double value);
    Img& operator+=(const Img& image);
    Img& operator-=(const Img& image);
    Img& operator*=(const Img& image);
    Img& operator/=(const Img& image);
    ~Img();

    void toGrassRaster(const char *name);
    void toGdal(const char *name, const char *ref_name);

    static Img fromGrassRaster(const char *name);
};

#endif
