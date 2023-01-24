#ifdef POPS_TEST

/*
 * Simple compilation test for the PoPS Raster class.
 *
 * Copyright (C) 2018 by the authors.
 *
 * Authors: Vaclav Petras <wenzeslaus gmail com>
 *
 * This file is part of PoPS.

 * PoPS is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.

 * PoPS is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.

 * You should have received a copy of the GNU General Public License
 * along with PoPS. If not, see <https://www.gnu.org/licenses/>.
 */

#include <pops/raster.hpp>
#include <pops/simulation.hpp>

#include <map>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

using std::cerr;
using std::cout;
using std::endl;
using std::string;

using pops::Raster;

static void test_constructor_by_type()
{
    Raster<int> a(10, 10);
    Raster<float> b(10, 10);
    Raster<double> c(10, 10);
}

static void test_constructor_dimensions()
{
    int x = 5;
    int y = 3;
    // new based on dimensions, with zeros, one value in the corner
    Raster<int> a(x, y);
    a.zero();
    a(x - 1, y - 1) = 2;
    std::cout << x << "x" << y << ":" << std::endl << a;
    // same as above, but with the dimensions swapped
    Raster<int> b(y, x);
    b.zero();
    b(y - 1, x - 1) = 2;
    std::cout << y << "x" << x << ":" << std::endl << b;
}

static void test_initializer_and_output()
{
    Raster<int> a = {{1, 2}, {3, 4}, {5, 6}};
    std::cout << "3x2:" << std::endl << a;

    Raster<int> b = {{0, 0, 0, 5, 5}, {0, 0, 0, 5, 5}, {0, 0, 0, 10, 0}};
    std::cout << "3x5:" << std::endl << b;
}

static void test_equal_operator()
{
    Raster<int> a = {{1, 2}, {3, 4}, {5, 6}};
    Raster<int> b = {{1, 2}, {3, 4}, {5, 6}};
    if (a == b)
        std::cout << "Operator equal works" << std::endl;
    else
        std::cout << "Operator equal does not work" << std::endl;
}

static void test_not_equal_operator()
{
    Raster<int> a = {{1, 2}, {3, 4}, {5, 6}};
    Raster<int> b = {{1, 2}, {3, 5}, {5, 6}};
    if (a != b)
        std::cout << "Operator not-equal works" << std::endl;
    else
        std::cout << "Operator not-equal does not work" << std::endl;
}

static int test_plus_operator()
{
    Raster<int> d = {{1, 2}, {3, 4}, {5, 6}};
    Raster<int> e = {{8, 9}, {10, 11}, {12, 13}};
    Raster<int> f = {{9, 11}, {13, 15}, {17, 19}};
    if (d + e == f) {
        std::cout << "Operator plus works" << std::endl;
        return 0;
    }
    else {
        std::cout << "Operator plus does not work" << std::endl;
        return 1;
    }
}

static int test_multiply_in_place_operator()
{
    Raster<double> d = {{1.1, 2}, {3.84, 4}, {5, 6}};
    Raster<double> e = {{8, 9.5}, {10, 11}, {12, 13}};
    Raster<double> f = e;
    Raster<double> g = {{8.8, 19}, {38.4, 44}, {60, 78}};
    d *= e;
    if (e == f && d == g) {
        std::cout << "Operator *= works" << std::endl;
        return 0;
    }
    else {
        std::cout << "Operator *= does not work" << std::endl;
        return 1;
    }
}

static void test_sqrt()
{
    Raster<int> a = {{16, 25}, {4, 9}};
    Raster<int> b = {{4, 5}, {2, 3}};
    auto c = sqrt(a);
    std::cout << "sqrt function: ";
    if (b == c)
        std::cout << "OK" << std::endl;
    else
        std::cout << "\n" << a << "!=\n" << b << std::endl;
}

template <typename T, typename U, typename V>
static void test_diff_types_const()
{
    Raster<T> a = {{1, 2}, {3, 4}, {5, 6}};
    Raster<U> b = {{1, 2}, {3, 4}, {5, 6}};
    Raster<V> c = a + b;
    c = a - b;
    c = a * b;
    c = a / b;
}

template <typename T, typename U>
static void test_diff_types_modify()
{
    Raster<T> a = {{1, 2}, {3, 4}, {5, 6}};
    Raster<U> b = {{1, 2}, {3, 4}, {5, 6}};
    a += b;
    a -= b;
    a *= b;
    a /= b;
}

template <typename T>
static void test_op_int()
{
    Raster<T> a = {{1, 2}, {3, 4}, {5, 6}};
    a += 1;
    a -= 10;
    a *= 6;
    a /= 2;
}

template <typename T>
static void test_op_double()
{
    Raster<T> a = {{1, 2}, {3, 4}, {5, 6}};
    a += 1.1;
    a -= 10.3;
    a *= 7.5;
    a /= 2.5;
}

template <typename T>
static void test_op_order()
{
    Raster<T> a = {{1, 2}, {3, 4}, {5, 6}};
    a + 1.1;
    a - 10.3;
    a * 75;
    a / 25;
    1 + a;
    10 - a;
    6.2 * a;
    2.1 / a;
}

template <typename T, typename U>
static int test_op_plus(U value)
{
    int errors = 0;
    Raster<T> a = {{1, 2}, {3, 4}, {5, 6}};
    Raster<T> b = {
        {1 + value, 2 + value}, {3 + value, 4 + value}, {5 + value, 6 + value}};
    if (a + value != b) {
        std::cout << "Operator raster + scalar broken:\n"
                  << a << b << std::endl;
        ++errors;
    }
    if (value + a != b) {
        std::cout << "Operator scalar + raster broken:\n"
                  << a << b << std::endl;
        ++errors;
    }
    a += value;
    if (a != b) {
        std::cout << "Operator raster += scalar broken:\n"
                  << a << b << std::endl;
        ++errors;
    }
    if (!errors)
        std::cout << "Operator raster and scalar + OK for raster "
                  << typeid(T).name() << " and scalar " << typeid(U).name()
                  << std::endl;
    return errors;
}

template <typename T, typename U>
static int test_op_times(U value)
{
    int errors = 0;
    Raster<T> a = {{1, 2}, {3, 4}, {5, 6}};
    Raster<T> b = {
        {1 * value, 2 * value}, {3 * value, 4 * value}, {5 * value, 6 * value}};
    if (a * value != b) {
        std::cout << "Operator raster * scalar broken:\n"
                  << a << b << std::endl;
        ++errors;
    }
    if (value * a != b) {
        std::cout << "Operator scalar * raster broken:\n"
                  << a << b << std::endl;
        ++errors;
    }
    a *= value;
    if (a != b) {
        std::cout << "Operator raster *= scalar broken:\n"
                  << a << b << std::endl;
        ++errors;
    }
    if (!errors)
        std::cout << "Operator raster and scalar * OK for raster "
                  << typeid(T).name() << " and scalar " << typeid(U).name()
                  << std::endl;
    return errors;
}

template <typename T, typename U>
static int test_op_minus(U value)
{
    int errors = 0;
    Raster<T> a = {{1, 2}, {3, 4}, {5, 6}};
    Raster<T> b = {
        {1 - value, 2 - value}, {3 - value, 4 - value}, {5 - value, 6 - value}};
    Raster<T> c = {
        {value - 1, value - 2}, {value - 3, value - 4}, {value - 5, value - 6}};
    if (a - value != b) {
        std::cout << "Operator raster - scalar broken:\n"
                  << a << b << std::endl;
        ++errors;
    }
    if (value - a != c) {
        std::cout << "Operator scalar - raster broken:\n"
                  << a << b << std::endl;
        ++errors;
    }
    a -= value;
    if (a != b) {
        std::cout << "Operator raster -= scalar broken:\n"
                  << a << b << std::endl;
        ++errors;
    }
    if (!errors)
        std::cout << "Operator raster and scalar - OK for raster "
                  << typeid(T).name() << " and scalar " << typeid(U).name()
                  << std::endl;
    return errors;
}

template <typename T, typename U>
static int test_op_divide(U value)
{
    int errors = 0;
    Raster<T> a = {{1, 2}, {3, 4}, {5, 6}};
    Raster<T> b = {
        {1 / value, 2 / value}, {3 / value, 4 / value}, {5 / value, 6 / value}};
    Raster<T> c = {
        {value / 1, value / 2}, {value / 3, value / 4}, {value / 5, value / 6}};
    if (a / value != b) {
        std::cout << "Operator raster / scalar broken:\n"
                  << a << b << std::endl;
        ++errors;
    }
    if (value / a != c) {
        std::cout << "Operator scalar / raster broken:\n"
                  << a << b << std::endl;
        ++errors;
    }
    a /= value;
    if (a != b) {
        std::cout << "Operator raster /= scalar broken:\n"
                  << a << b << std::endl;
        ++errors;
    }
    if (!errors)
        std::cout << "Operator raster and scalar / OK for raster "
                  << typeid(T).name() << " and scalar " << typeid(U).name()
                  << std::endl;
    return errors;
}

template <typename T>
static int test_times_scalar()
{
    int errors = 0;
    Raster<T> a = {{1, 2}, {3, 4}, {5, 6}};
    auto b = a * 0.4;
    T sum = 0;
    b.for_each([&sum](T &v) { sum += v; });
    if (sum == 0) {
        ++errors;
        std::cout << "Operator 'raster * scalar' does not work" << std::endl;
    }
    a *= 0.4;
    sum = 0;
    a.for_each([&sum](T &v) { sum += v; });
    if (sum == 0) {
        ++errors;
        std::cout << "Operator 'raster *= scalar' does not work" << std::endl;
    }
    if (!errors)
        std::cout << "Operators time for scalars OK" << std::endl;
    return errors;
}

template <typename T, typename I>
static int test_index()
{
    int errors = 0;
    Raster<T, I> a = {{11, 12, 13, 14}, {21, 22, 23, 24}, {31, 32, 33, 34}};
    I row = 0;
    I col = 3;
    if (a(row, col) != 14) {
        std::cout << "Not reading the right value, but: " << a(row, col)
                  << std::endl;
        return ++errors;
    }
    T value = 20;
    a(row, col) = value;
    if (a(row, col) != value) {
        std::cout << "Not reading the right value after assignment, but: "
                  << a(row, col) << std::endl;
        return ++errors;
    }
    if (!errors)
        std::cout << "Index with custom template parameter value works"
                  << std::endl;
    return errors;
}

template <typename T, typename I>
static int test_non_owner()
{
    int errors = 0;
    const I rows = 3;
    const I cols = 4;
    T x[rows * cols] = {11, 12, 13, 14, 21, 22, 23, 24, 31, 32, 33, 34};
    Raster<T> a(x, rows, cols);
    I row = 2;
    I col = 3;
    if (a(row, col) != 34) {
        std::cout << "Not reading from raster the value in array, but: "
                  << a(row, col) << std::endl;
        return ++errors;
    }
    T value = 40;
    a(row, col) = value;
    if (a(row, col) != value) {
        std::cout << "Not reading from raster what was written, but: "
                  << a(row, col) << std::endl;
        return ++errors;
    }
    value = 50;
    x[row * cols + col] = value;
    if (a(row, col) != value) {
        std::cout << "Not reading from array what was written, but: "
                  << a(row, col) << std::endl;
        return ++errors;
    }
    // no delete should be called here
    a = {{100, 200}, {300, 400}};
    a(1, 0) = 1000;
    if (a(1, 0) != 1000) {
        std::cout << "Not reading correctly after assignment, but: " << a(1, 0)
                  << std::endl;
        return ++errors;
    }
    if (x[cols] != 21) {
        std::cout << "Array is broken, reading: " << x[cols] << std::endl;
        return ++errors;
    }
    if (!errors)
        std::cout << "Raster non-owning the data works" << std::endl;
    return errors;
}

template <typename T, typename I>
std::vector<Raster<T>> return_vector_of_rasters(int num_rasters)
{
    std::vector<Raster<T>> rasters;
    for (int i = 0; i < num_rasters; ++i) {
        rasters.push_back(Raster<T>(100, 200, 42));
    }
    return rasters;
}

template <typename T, typename I>
std::vector<Raster<T>> return_vector_of_rasters(T **data, int num_rasters,
                                                I rows, I cols)
{
    std::vector<Raster<T>> rasters;
    for (int i = 0; i < num_rasters; ++i) {
        rasters.push_back(Raster<T>(data[i], rows, cols));
    }
    return rasters;
}

template <typename T, typename I>
int test_return_from_function(int num_rasters)
{
    int errors = 0;
    auto rasters = return_vector_of_rasters<T, I>(num_rasters);
    for (const auto &raster : rasters)
        if (raster(0, 0) != 42) {
            ++errors;
            break;
        }
    if (!errors)
        std::cout << "Returning owning raster from function works (value: "
                  << typeid(T).name() << ", index: " << typeid(I).name() << ")"
                  << std::endl;
    return errors;
}

template <typename T, typename I>
int test_return_from_function_non_owner()
{
    int errors = 0;
    const I rows = 3;
    const I cols = 4;
    const int num_rasters = 3;
    T x[rows * cols] = {11, 12, 13, 14, 21, 22, 23, 24, 31, 32, 33, 34};
    T y[rows * cols] = {11, 12, 13, 14, 21, 22, 23, 24, 31, 32, 33, 34};
    T z[rows * cols] = {11, 12, 13, 14, 21, 22, 23, 24, 31, 32, 33, 34};
    T *data[num_rasters] = {x, y, z};
    auto rasters = return_vector_of_rasters<T>(data, num_rasters, rows, cols);
    for (const auto &raster : rasters) {
        if (raster(0, 0) != 11) {
            ++errors;
            break;
        }
    }
    if (!errors)
        std::cout << "Returning non-owning raster from function works (value: "
                  << typeid(T).name() << ", index: " << typeid(I).name() << ")"
                  << std::endl;
    return errors;
}

int main()
{
    test_constructor_by_type();
    test_constructor_dimensions();
    test_initializer_and_output();
    test_equal_operator();
    test_not_equal_operator();

    test_plus_operator();
    test_multiply_in_place_operator();

    test_sqrt();

    // all doubles, no problem
    test_diff_types_const<double, double, double>();
    // operation on ints gives ints
    test_diff_types_const<int, int, int>();
    // combining int and double gives double
    test_diff_types_const<double, int, double>();
    test_diff_types_const<int, double, double>();
    // undefined: we don't define promotion
    // test_diff_types_const<int, int, double>();
    // undefined: we don't allow demotion
    // test_diff_types_const<double, double, int>();

    // all doubles, no problem
    test_diff_types_modify<double, double>();
    // operation on ints gives ints
    test_diff_types_modify<int, int>();
    // operation on double gives double
    test_diff_types_modify<double, int>();
    // undefined: modifying int with double not allowed
    // test_diff_types_modify<int, double>();

    test_op_double<double>();
    test_op_int<double>();
    test_op_int<int>();
    test_op_double<int>();

    test_op_order<double>();
    test_op_order<int>();

    test_op_plus<int>(5);
    test_op_plus<double>(5.5);
    test_op_minus<int>(5);
    test_op_minus<double>(5.5);
    test_op_times<int>(5);
    test_op_times<double>(5.5);
    test_op_divide<int>(5);
    test_op_divide<double>(5.5);

    test_times_scalar<int>();
    test_times_scalar<double>();

    test_index<int, int>();
    test_index<int, unsigned>();
    test_index<int, size_t>();

    test_non_owner<int, size_t>();

    test_return_from_function<int, long>(10);
    test_return_from_function<long, int>(10);
    test_return_from_function<float, long>(10);
    test_return_from_function<double, int>(10);
    test_return_from_function_non_owner<int, long>();
    test_return_from_function_non_owner<long, int>();
    test_return_from_function_non_owner<float, long>();
    test_return_from_function_non_owner<double, int>();

    return 0;
}

#endif // POPS_TEST
