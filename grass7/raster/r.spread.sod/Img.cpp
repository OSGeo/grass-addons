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


#include "Img.h"

extern "C" {
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>
}

#include <gdal/gdal.h>
#include <gdal/gdal_priv.h>

#include <algorithm>

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

Img::Img()
{
    width = 0;
    height = 0;
    w_e_res = 0;
    n_s_res = 0;
    data = NULL;
}

Img::Img(const Img& other)
{
    width = other.width;
    height = other.height;
    w_e_res = other.w_e_res;
    n_s_res = other.n_s_res;
    data = new int[width * height];
    std::copy(other.data, other.data + (width * height), data);
}

Img::Img(Img&& other)
{
    width = other.width;
    height = other.height;
    w_e_res = other.w_e_res;
    n_s_res = other.n_s_res;
    data = other.data;
    other.data = nullptr;
}

Img::Img(int width, int height, int w_e_res, int n_s_res)
{
    this->width = width;
    this->height = height;
    this->w_e_res = w_e_res;
    this->n_s_res = n_s_res;
    this->data = new int[width * height];
}

Img::Img(int width, int height, int w_e_res, int n_s_res, int value)
{
    this->width = width;
    this->height = height;
    this->w_e_res = w_e_res;
    this->n_s_res = n_s_res;
    this->data = new int[width * height]{value};
}

Img::Img(const char *fileName)
{
    GDALDataset *dataset;
    GDALRasterBand *dataBand;

    GDALAllRegister();
    dataset = (GDALDataset *) GDALOpen(fileName, GA_ReadOnly);
    double adfGeoTransform[6];

    if (!dataset) {
        cerr << "Can not open the image!" << endl;
    }
    else {
        width = dataset->GetRasterXSize();
        height = dataset->GetRasterYSize();

        if (dataset->GetGeoTransform(adfGeoTransform) == CE_None) {
            w_e_res = abs(adfGeoTransform[1]);
            n_s_res = abs(adfGeoTransform[5]);
        }

        //cout << width << "x" << height <<endl;
        //cout << w_e_res << "X" << n_s_res << endl;

        dataBand = dataset->GetRasterBand(1);
        data = new int[width * height];

        CPLErr error = dataBand->RasterIO(GF_Read, 0, 0, width, height,
                                          data, width, height,
                                          GDT_Int32, 0, 0);
        if (error == CE_Failure)
            throw std::runtime_error(string("Reading raster failed"
                                            " in GDAL RasterIO: ")
                                     + CPLGetLastErrorMsg());
        GDALClose((GDALDatasetH) dataset);
    }
}


// TODO: add move constuctor
Img Img::fromGrassRaster(const char *name)
{
    int fd = Rast_open_old(name, "");

    Img img;

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

/*
   const int ** Img::getData(){
   return this->data;
   }
 */

Img& Img::operator=(const Img& other)
{
    if (this != &other)
    {
        if (data)
            delete[] data;
        width = other.width;
        height = other.height;
        w_e_res = other.w_e_res;
        n_s_res = other.n_s_res;
        data = new int[width * height];
        std::copy(other.data, other.data + (width * height), data);
    }
    return *this;
}

Img& Img::operator=(Img&& other)
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

Img Img::operator+(const Img& image) const
{
    if (this->width != image.getWidth() || this->height != image.getHeight()) {
        cerr << "The height or width of one image do not match with that of the other one!" << endl;
        return Img();
    }
    else {
        auto re_width = this->width;
        auto re_height = this->height;
        auto out = Img(re_width, re_height, this->w_e_res, this->n_s_res);

        for (int i = 0; i < re_height; i++) {
            for (int j = 0; j < re_width; j++) {
                out.data[i * width + j] = this->data[i * width + j] + image.data[i * width + j];
            }
        }
        return out;
    }
}

Img Img::operator-(const Img& image) const
{
    if (this->width != image.getWidth() || this->height != image.getHeight()) {
        cerr << "The height or width of one image do not match with that of the other one!" << endl;
        return Img();
    }
    else {
        auto re_width = this->width;
        auto re_height = this->height;
        auto out = Img(re_width, re_height, this->w_e_res, this->n_s_res);

        for (int i = 0; i < re_height; i++) {
            for (int j = 0; j < re_width; j++) {
                out.data[i * width + j] = this->data[i * width + j] - image.data[i * width + j];
            }
        }
        return out;
    }
}

Img Img::operator*(const Img& image) const
{
    if (width != image.getWidth() || height != image.getHeight()) {
        throw std::runtime_error("The height or width of one image do"
                                 " not match with that of the other one.");
    }
    auto out = Img(width, height, w_e_res, n_s_res);

    std::transform(data, data + (width * height), image.data, out.data,
                   [](const int& a, const int& b) { return a * b; });
    return out;
}

Img Img::operator/(const Img& image) const
{
    if (width != image.getWidth() || height != image.getHeight()) {
        throw std::runtime_error("The height or width of one image do"
                                 " not match with that of the other one.");
    }
    auto out = Img(width, height, w_e_res, n_s_res);

    std::transform(data, data + (width * height), image.data, out.data,
                   [](const int& a, const int& b) { return a / b; });
    return out;
}

Img Img::operator*(double factor) const
{
    auto re_width = this->width;
    auto re_height = this->height;
    auto out = Img(re_width, re_height, this->w_e_res, this->n_s_res);

    for (int i = 0; i < re_height; i++) {
        for (int j = 0; j < re_width; j++) {
            out.data[i * width + j] = this->data[i * width + j] * factor;
        }
    }
    return out;
}

Img Img::operator/(double value) const
{
    auto out = Img(width, height, w_e_res, n_s_res);

    std::transform(data, data + (width * height), out.data,
                   [&value](const int& a) { return a / value; });
    return out;
}

Img& Img::operator+=(int value)
{
    std::for_each(data, data + (width * height),
                  [&value](int& a) { a += value; });
    return *this;
}

Img& Img::operator-=(int value)
{
    std::for_each(data, data + (width * height),
                  [&value](int& a) { a -= value; });
    return *this;
}

Img& Img::operator*=(double value)
{
    std::for_each(data, data + (width * height),
                  [&value](int& a) { a *= value; });
    return *this;
}

Img& Img::operator/=(double value)
{
    std::for_each(data, data + (width * height),
                  [&value](int& a) { a /= value; });
    return *this;
}

Img& Img::operator+=(const Img& image)
{
    for_each_zip(data, data + (width * height), image.data,
                 [](int& a, int& b) { a += b; });
    return *this;
}

Img& Img::operator-=(const Img& image)
{
    for_each_zip(data, data + (width * height), image.data,
                 [](int& a, int& b) { a -= b; });
    return *this;
}

Img& Img::operator*=(const Img& image)
{
    for_each_zip(data, data + (width * height), image.data,
                 [](int& a, int& b) { a *= b; });
    return *this;
}

Img& Img::operator/=(const Img& image)
{
    for_each_zip(data, data + (width * height), image.data,
                 [](int& a, int& b) { a /= b; });
    return *this;
}

Img::~Img()
{
    if (data) {
        delete[] data;
    }
}

void Img::toGrassRaster(const char *name)
{
    int fd = Rast_open_new(name, CELL_TYPE);
    for (int i = 0; i < height; i++)
        Rast_put_c_row(fd, data + (i * width));
    Rast_close(fd);
}

// ref_name file is used to retrieve transformation and projection
// information from the known (input) file
void Img::toGdal(const char *name, const char *ref_name)
{
    const char *format = "GTiff";

    GDALAllRegister();

    // obtain information for output Geotiff images
    GDALDataset *inputDataset = (GDALDataset *) GDALOpen(ref_name,
                                                         GA_ReadOnly);
    double inputAdfGeoTransform[6];
    inputDataset->GetGeoTransform(inputAdfGeoTransform);

    // setup driver
    GDALDriver *gdalDriver = GetGDALDriverManager()->GetDriverByName(format);

    // set output Dataset and create output geotiff
    char **papszOptions = NULL;
    GDALDataset *outDataset = gdalDriver->Create(name, width, height, 1,
                                                 GDT_Byte, papszOptions);
    outDataset->SetGeoTransform(inputAdfGeoTransform);
    outDataset->SetProjection(inputDataset->GetProjectionRef());
    GDALRasterBand *outBand = outDataset->GetRasterBand(1);
    CPLErr error = outBand->RasterIO(GF_Write, 0, 0, width, height,
                                     data, width, height,
                                     GDT_Int32, 0, 0);
    if (error == CE_Failure)
        throw std::runtime_error(string("Writing raster failed"
                                        " in GDAL RasterIO: ")
                                 + CPLGetLastErrorMsg());
    GDALClose((GDALDatasetH) outDataset);
    GDALClose((GDALDatasetH) inputDataset);
    CSLDestroy(papszOptions);
}
