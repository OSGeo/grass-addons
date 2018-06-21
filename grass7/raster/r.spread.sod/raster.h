#ifndef RASTER_H
#define RASTER_H

/*
 * SOD model - raster manipulation
 *
 * Copyright (C) 2015-2018 by the authors.
 *
 * Authors: Vaclav Petras <wenzeslaus gmail com>
 *          Completely rewritten by Vaclav Petras based on
 *          version by Zexi Chen <zchen22 ncsu edu>.
 *
 * The code contained herein is licensed under the GNU General Public
 * License. You may obtain a copy of the GNU General Public License
 * Version 2 or later at the following locations:
 *
 * http://www.opensource.org/licenses/gpl-license.html
 * http://www.gnu.org/copyleft/gpl.html
 */

#include <iostream>
#include <string>
#include <cmath>
#include <algorithm>
#include <stdlib.h>

extern "C" {
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>
}

#include <algorithm>
#include <stdexcept>

using std::string;
using std::cerr;
using std::endl;

/* Iterate over two ranges and apply a binary function which modifies
 * the first parameter.
 */
template<class InputIt1, class InputIt2, class BinaryOperation>
BinaryOperation for_each_zip(InputIt1 first1, InputIt1 last1, InputIt2 first2, BinaryOperation f) {
    for (; first1 != last1; ++first1, ++first2) {
        f(*first1, *first2);
    }
    return f;
}

template<typename Number>
class Raster
{
private:
    unsigned width;
    unsigned height;
    // the west-east resolution of the pixel
    double w_e_res;
    // the north-south resolution of the pixel
    double n_s_res;
    Number *data;
public:
    Raster()
    {
        width = 0;
        height = 0;
        w_e_res = 0;
        n_s_res = 0;
        data = NULL;
    }

    Raster(const Raster& other)
    {
        width = other.width;
        height = other.height;
        w_e_res = other.w_e_res;
        n_s_res = other.n_s_res;
        data = new Number[width * height];
        std::copy(other.data, other.data + (width * height), data);
    }

    Raster(const Raster& other, Number value)
    {
        width = other.width;
        height = other.height;
        w_e_res = other.w_e_res;
        n_s_res = other.n_s_res;
        data = new Number[width * height]{value};
    }

    Raster(Raster&& other)
    {
        width = other.width;
        height = other.height;
        w_e_res = other.w_e_res;
        n_s_res = other.n_s_res;
        data = other.data;
        other.data = nullptr;
    }

    Raster(int width, int height, int w_e_res, int n_s_res)
    {
        this->width = width;
        this->height = height;
        this->w_e_res = w_e_res;
        this->n_s_res = n_s_res;
        this->data = new Number[width * height];
    }

    // TODO: res are doubles
    // TODO: size is unsigned?
    Raster(int width, int height, int w_e_res, int n_s_res, int value)
    {
        this->width = width;
        this->height = height;
        this->w_e_res = w_e_res;
        this->n_s_res = n_s_res;
        this->data = new Number[width * height]{value};
    }

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

    void fill(Number value)
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

    const Number& operator()(unsigned row, unsigned col) const
    {
        return data[row * width + col];
    }

    Number& operator()(unsigned row, unsigned col)
    {
        return data[row * width + col];
    }

    Raster& operator=(const Raster& other)
    {
        if (this != &other)
        {
            if (data)
                delete[] data;
            width = other.width;
            height = other.height;
            w_e_res = other.w_e_res;
            n_s_res = other.n_s_res;
            data = new Number[width * height];
            std::copy(other.data, other.data + (width * height), data);
        }
        return *this;
    }

    Raster& operator=(Raster&& other)
    {
        if (this != &other)
        {
            if (data)
                delete[] data;
            width = other.width;
            height = other.height;
            w_e_res = other.w_e_res;
            n_s_res = other.n_s_res;
            data = other.data;
            other.data = nullptr;
        }
        return *this;
    }

    Raster operator+(const Raster& image) const
    {
        if (this->width != image.getWidth() || this->height != image.getHeight()) {
            cerr << "The height or width of one image do not match with that of the other one!" << endl;
            return Raster();
        }
        else {
            auto re_width = this->width;
            auto re_height = this->height;
            auto out = Raster(re_width, re_height, this->w_e_res, this->n_s_res);

            for (int i = 0; i < re_height; i++) {
                for (int j = 0; j < re_width; j++) {
                    out.data[i * width + j] = this->data[i * width + j] + image.data[i * width + j];
                }
            }
            return out;
        }
    }

    Raster operator-(const Raster& image) const
    {
        if (this->width != image.getWidth() || this->height != image.getHeight()) {
            cerr << "The height or width of one image do not match with that of the other one!" << endl;
            return Raster();
        }
        else {
            auto re_width = this->width;
            auto re_height = this->height;
            auto out = Raster(re_width, re_height, this->w_e_res, this->n_s_res);

            for (int i = 0; i < re_height; i++) {
                for (int j = 0; j < re_width; j++) {
                    out.data[i * width + j] = this->data[i * width + j] - image.data[i * width + j];
                }
            }
            return out;
        }
    }

    Raster operator*(const Raster& image) const
    {
        if (width != image.getWidth() || height != image.getHeight()) {
            throw std::runtime_error("The height or width of one image do"
                                     " not match with that of the other one.");
        }
        auto out = Raster(width, height, w_e_res, n_s_res);

        std::transform(data, data + (width * height), image.data, out.data,
                       [](const Number& a, const Number& b) { return a * b; });
        return out;
    }

    Raster operator/(const Raster& image) const
    {
        if (width != image.getWidth() || height != image.getHeight()) {
            throw std::runtime_error("The height or width of one image do"
                                     " not match with that of the other one.");
        }
        auto out = Raster(width, height, w_e_res, n_s_res);

        std::transform(data, data + (width * height), image.data, out.data,
                       [](const Number& a, const Number& b) { return a / b; });
        return out;
    }

    Raster operator*(double value) const
    {
        auto out = Raster(width, height, w_e_res, n_s_res);

        std::transform(data, data + (width * height), out.data,
                       [&value](const Number& a) { return a * value; });
        return out;
    }

    Raster operator/(double value) const
    {
        auto out = Raster(width, height, w_e_res, n_s_res);

        std::transform(data, data + (width * height), out.data,
                       [&value](const Number& a) { return a / value; });
        return out;
    }

    Raster& operator+=(Number value)
    {
        std::for_each(data, data + (width * height),
                      [&value](Number& a) { a += value; });
        return *this;
    }

    Raster& operator-=(Number value)
    {
        std::for_each(data, data + (width * height),
                      [&value](Number& a) { a -= value; });
        return *this;
    }

    Raster& operator*=(double value)
    {
        std::for_each(data, data + (width * height),
                      [&value](Number& a) { a *= value; });
        return *this;
    }

    Raster& operator/=(double value)
    {
        std::for_each(data, data + (width * height),
                      [&value](Number& a) { a /= value; });
        return *this;
    }

    Raster& operator+=(const Raster& image)
    {
        for_each_zip(data, data + (width * height), image.data,
                     [](Number& a, Number& b) { a += b; });
        return *this;
    }

    Raster& operator-=(const Raster& image)
    {
        for_each_zip(data, data + (width * height), image.data,
                     [](Number& a, Number& b) { a -= b; });
        return *this;
    }

    Raster& operator*=(const Raster& image)
    {
        for_each_zip(data, data + (width * height), image.data,
                     [](Number& a, Number& b) { a *= b; });
        return *this;
    }

    Raster& operator/=(const Raster& image)
    {
        for_each_zip(data, data + (width * height), image.data,
                     [](Number& a, Number& b) { a /= b; });
        return *this;
    }

    friend inline Raster operator*(double factor, const Raster& image)
    {
        return image * factor;
    }

    friend inline Raster pow(Raster image, double value) {
        image.for_each([value](Number& a){a = std::pow(a, value);});
        return image;
    }
    friend inline Raster sqrt(Raster image) {
        image.for_each([](Number& a){a = std::sqrt(a);});
        return image;
    }


    ~Raster()
    {
        if (data) {
            delete[] data;
        }
    }

    static inline Raster fromGrassRaster(const char *name)
    {
        int fd = Rast_open_old(name, "");

        Raster img;

        img.width = Rast_window_cols();
        img.height = Rast_window_rows();

        Cell_head region;
        Rast_get_window(&region);
        img.w_e_res = region.ew_res;
        img.n_s_res = region.ns_res;

        img.data = new Number[img.height * img.width];

        for (int row = 0; row < img.height; row++) {
            Rast_get_d_row(fd, img.data + (row * img.width), row);
        }

        Rast_close(fd);
        return img;
    }

    void inline toGrassRaster(const char *name)
    {
        int fd = Rast_open_new(name, DCELL_TYPE);
        for (int i = 0; i < height; i++)
            Rast_put_d_row(fd, data + (i * width));
        Rast_close(fd);
    }

};

template <>
inline Raster<int> Raster<int>::fromGrassRaster(const char *name)
{
    int fd = Rast_open_old(name, "");

    Raster img;

    img.width = Rast_window_cols();
    img.height = Rast_window_rows();

    Cell_head region;
    Rast_get_window(&region);
    img.w_e_res = region.ew_res;
    img.n_s_res = region.ns_res;

    img.data = new int[img.height * img.width];

    for (int row = 0; row < img.height; row++) {
        Rast_get_c_row(fd, img.data + (row * img.width), row);
    }

    Rast_close(fd);
    return img;
}

template <>
inline void Raster<int>::toGrassRaster(const char *name)
{
    int fd = Rast_open_new(name, CELL_TYPE);
    for (int i = 0; i < height; i++)
        Rast_put_c_row(fd, data + (i * width));
    Rast_close(fd);
}

// convenient definitions, names for backwards compatibility
typedef Raster<int> Img;
typedef Raster<double> DImg;

#endif
