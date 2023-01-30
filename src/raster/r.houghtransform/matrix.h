#ifndef MATRIX_H
#define MATRIX_H

#include <vector>
#include <algorithm>
#include <limits>
#include <cmath>

/* mimics Octave matrices and other classes */

namespace matrix {

template <typename T>
class Matrix {
public:
    typedef T value_type;

    Matrix(size_t r, size_t c, value_type val = 0) : mRows(r), mCols(c)
    {
        resize(r, c, val);
    }
    Matrix() : mRows(0), mCols(0) {}

    void resize(size_t r, size_t c, value_type val = 0)
    {
        mRows = r;
        mCols = c;
        std::vector<value_type> row;
        row.resize(c, val);
        mat.resize(r, row);
    }

    /**

      if (r > rows() || c > columns()) error;
      */
    value_type &operator()(size_t r, size_t c) { return mat[r][c]; }
    /**

      if (r > rows() || c > columns()) error;
      */
    const value_type &operator()(size_t r, size_t c) const { return mat[r][c]; }
    size_t rows() const { return mRows; }
    size_t columns() const { return mCols; }

    std::vector<value_type> row_max(std::vector<size_t> &colIndexes) const
    {
        std::vector<value_type> ret;
        ret.reserve(rows());
        colIndexes.reserve(rows());
        for (size_t i = 0; i < rows(); ++i) {
            typename std::vector<value_type>::const_iterator maxe =
                std::max_element(mat[i].begin(), mat[i].end());
            value_type max = *maxe;
            size_t maxi = maxe - mat[i].begin();

            ret.push_back(max);
            colIndexes.push_back(maxi);
        }
        return ret;
    }

private:
    std::vector<std::vector<value_type>> mat;
    size_t mRows;
    size_t mCols;
};

template <typename T>
class ColumnVector {
public:
    typedef T value_type;

    ColumnVector(Matrix<value_type> mat)
    {
        for (size_t i = 0; i < mat.columns(); ++i) {
            vec.push_back(mat(0, i));
        }
    }
    ColumnVector() {}

    value_type &operator()(size_t i) { return vec[i]; }
    const value_type &operator()(size_t i) const { return vec[i]; }
    size_t length() { return vec.size(); }

private:
    std::vector<value_type> vec;
};

template <typename T>
class Range {
public:
    typedef T value_type;

    Range(double b, double l, double i)
        : rng_base(b), rng_limit(l), rng_inc(i), rng_nelem(nelem_internal())
    {
    }

    Range(double b, double l)
        : rng_base(b), rng_limit(l), rng_inc(1), rng_nelem(nelem_internal())
    {
    }

    Matrix<value_type> matrix_value() const
    {
        Matrix<value_type> cache;
        // if (rng_nelem > 0 && cache.nelem () == 0)
        //{
        cache.resize(1, rng_nelem);
        double b = rng_base;
        double increment = rng_inc;
        for (size_t i = 0; i < rng_nelem; i++)
            cache(0, i) = b + i * increment;

        // On some machines (x86 with extended precision floating point
        // arithmetic, for example) it is possible that we can overshoot
        // the limit by approximately the machine precision even though
        // we were very careful in our calculation of the number of
        // elements.

        if ((rng_inc > 0 && cache(0, rng_nelem - 1) > rng_limit) ||
            (rng_inc < 0 && cache(0, rng_nelem - 1) < rng_limit))
            cache(0, rng_nelem - 1) = rng_limit;
        //  }
        return cache;
    }

private:
    /* from Octave source codes */
    size_t nelem_internal() const
    {
        size_t retval = -1;

        if (rng_inc == 0 || (rng_limit > rng_base && rng_inc < 0) ||
            (rng_limit < rng_base && rng_inc > 0)) {
            retval = 0;
        }
        else {
            // double ct = 3.0 * std::numeric_limits<double>::epsilon(); //
            // FIXME: not used was DBL_EPSILON;

            // double tmp = tfloor ((rng_limit - rng_base + rng_inc) / rng_inc,
            // ct); // octave code
            double tmp = floor((rng_limit - rng_base + rng_inc) / rng_inc);

            size_t n_elt = (tmp > 0.0 ? static_cast<size_t>(tmp) : 0);

            // If the final element that we would compute for the range is
            // equal to the limit of the range, or is an adjacent floating
            // point number, accept it.  Otherwise, try a range with one
            // fewer element.  If that fails, try again with one more
            // element.
            //
            // I'm not sure this is very good, but it seems to work better than
            // just using tfloor as above.  For example, without it, the
            // expression 1.8:0.05:1.9 fails to produce the expected result of
            // [1.8, 1.85, 1.9].

            // octave code
            // if (! teq (rng_base + (n_elt - 1) * rng_inc, rng_limit))
            //   {
            //     if (teq (rng_base + (n_elt - 2) * rng_inc, rng_limit))
            //       n_elt--;
            //     else if (teq (rng_base + n_elt * rng_inc, rng_limit))
            //       n_elt++;
            //   }

            retval =
                (n_elt >= std::numeric_limits<size_t>::max() - 1) ? -1 : n_elt;
        }

        return retval;
    }

    double rng_base;
    double rng_limit;
    double rng_inc;
    size_t rng_nelem;
};

} // namespace matrix

#endif // MATRIX_H
