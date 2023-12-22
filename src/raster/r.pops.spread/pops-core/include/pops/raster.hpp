#ifndef POPS_RASTER_HPP
#define POPS_RASTER_HPP

/*
 * PoPS model - native raster manipulation
 *
 * Copyright (C) 2015-2020 by the authors.
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
#include <cmath>
#include <algorithm>
#include <stdexcept>
#include <initializer_list>
#include <type_traits>

namespace pops {

/*! Iterate over two ranges and apply a binary function which modifies
 *  the first parameter.
 */
template <class InputIt1, class InputIt2, class BinaryOperation>
BinaryOperation for_each_zip(InputIt1 first1, InputIt1 last1, InputIt2 first2,
                             BinaryOperation f)
{
    for (; first1 != last1; ++first1, ++first2) {
        f(*first1, *first2);
    }
    return f;
}

/*! Representation of a raster image.
 *
 * The object support raster algebra operations:
 *
 * ```
 * Raster<int> a = {{1, 2}, {3, 4}};
 * auto b = 2 * (a + 1);
 * ```
 *
 * The raster algebra operations sometimes overlap with matrix
 * operations, e.g. for plus operator or multiplication by scalar.
 * However, in some cases, the behavior is different, e.g.,
 * multiplication of the rasters results in a new raster with cell
 * values which are result of multiplying cell values in the relevant
 * positions of the two raster.
 *
 * ```
 * Raster<int> a = {{1, 2}, {3, 4}};
 * auto b = 2 * (a + 1);
 * ```
 *
 * The template parameter Number is the numerical type of the raster,
 * typically int, float, or double.
 *
 * The internal storage is directly accessible which comes with a great
 * responsibility. Although for the computations themselves, direct
 * access is not needed, it gives a lot of advantages when
 * initializing the values as well as when putting them to some storage
 * when the computation is done. The values need to be stored in
 * one liner array with row-major oder, i.e. individual value can be
 * accessed using the following:
 *
 * ```
 * row * total_number_of_columns + column
 * ```
 *
 * Operations involving raster and scalar preserve the type of the
 * raster and don't produce a new type of raster based on the scalar
 * type, i.e., `a * 0.5` where `a` is an integral raster type results
 * in the same integral raster type, not floating point raster type.
 * This makes perations such as `*` and `*=` behave the same for
 * scalars.
 *
 * On the other hand, operations involving two rasters of different type
 * resolve to their common type, specifically the common type of their
 * scalars using `std::common_type`, i.e. `a * b` where `a` is an
 * integral raster type and `b` is a floating raster type produce
 * a floating raster type.
 *
 * The Index template parameter is an signed or unsigned integer used for
 * indexing of rows and columns. The default value is int because signed
 * indices is the modern C++ practice and int is used in Rcpp.
 */
template <typename Number, typename Index = int>
class Raster {
protected:
    Index rows_;
    Index cols_;
    Number *data_;
    // owning is true for any state which is not using someone's data
    bool owns_;

public:
    typedef Number NumberType;
    typedef Index IndexType;

    Raster() : owns_(true)
    {
        cols_ = 0;
        rows_ = 0;
        data_ = NULL;
    }

    Raster(const Raster &other) : owns_(true)
    {
        cols_ = other.cols_;
        rows_ = other.rows_;
        data_ = new Number[cols_ * rows_];
        std::copy(other.data_, other.data_ + (cols_ * rows_), data_);
    }

    /*! Initialize size using another raster, but use given value
     *
     * The values in the other raster are not used.
     */
    Raster(const Raster &other, Number value) : owns_(true)
    {
        cols_ = other.cols_;
        rows_ = other.rows_;
        data_ = new Number[cols_ * rows_]{value};
    }

    Raster(Raster &&other) : owns_(other.owns_)
    {
        cols_ = other.cols_;
        rows_ = other.rows_;
        data_ = other.data_;
        other.data_ = nullptr;
    }

    Raster(Index rows, Index cols) : owns_(true)
    {
        this->cols_ = cols;
        this->rows_ = rows;
        this->data_ = new Number[cols_ * rows_];
    }

    Raster(Index rows, Index cols, Number value) : owns_(true)
    {
        this->cols_ = cols;
        this->rows_ = rows;
        this->data_ = new Number[cols_ * rows_]{value};
    }

    /*! Use existing data storage
     *
     * Uses existing data and storage as is. No memory allocation is
     * performed. The Raster object does not take ownership of the
     * memory, so it can and must be managed in an appropriate way
     * by the caller.
     */
    Raster(Number *data, Index rows, Index cols)
        : rows_(rows), cols_(cols), data_(data), owns_(false)
    {
    }

    // maybe remove from the class, or make it optional together with
    // a reference
    Raster(std::initializer_list<std::initializer_list<Number>> l)
        : Raster(l.size(), l.begin()->size())
    {
        Index i = 0;
        Index j = 0;
        for (const auto &subl : l) {
            for (const auto &value : subl) {
                data_[cols_ * i + j] = value;
                ++j;
            }
            j = 0;
            ++i;
        }
    }

    ~Raster()
    {
        if (data_ && owns_) {
            delete[] data_;
        }
    }

    Index cols() const { return cols_; }

    Index rows() const { return rows_; }

    /*! Returns pointer for direct access the underlying array.
     *
     * The values are stored in row-major order.
     * See the class description for details.
     */
    Number *data() noexcept { return data_; }

    /*! Returns pointer for direct access the underlying array.
     *
     * Same as the non-const version but used when the object is const.
     */
    const Number *data() const noexcept { return data_; }

    void fill(Number value)
    {
        std::fill(data_, data_ + (cols_ * rows_), value);
    }

    void zero() { std::fill(data_, data_ + (cols_ * rows_), 0); }

    template <class UnaryOperation>
    void for_each(UnaryOperation op)
    {
        std::for_each(data_, data_ + (cols_ * rows_), op);
    }

    const Number &operator()(Index row, Index col) const
    {
        return data_[row * cols_ + col];
    }

    Number &operator()(Index row, Index col)
    {
        return data_[row * cols_ + col];
    }

    Raster &operator=(const Raster &other)
    {
        if (this != &other) {
            if (data_ && owns_)
                delete[] data_;
            cols_ = other.cols_;
            rows_ = other.rows_;
            data_ = new Number[cols_ * rows_];
            std::copy(other.data_, other.data_ + (cols_ * rows_), data_);
        }
        return *this;
    }

    Raster &operator=(Raster &&other)
    {
        if (this != &other) {
            if (data_ && owns_)
                delete[] data_;
            cols_ = other.cols_;
            rows_ = other.rows_;
            data_ = other.data_;
            owns_ = other.owns_;
            other.data_ = nullptr;
        }
        return *this;
    }

    template <typename OtherNumber>
    Raster &operator+=(OtherNumber value)
    {
        std::for_each(data_, data_ + (cols_ * rows_),
                      [&value](Number &a) { a += value; });
        return *this;
    }

    template <typename OtherNumber>
    Raster &operator-=(OtherNumber value)
    {
        std::for_each(data_, data_ + (cols_ * rows_),
                      [&value](Number &a) { a -= value; });
        return *this;
    }

    template <typename OtherNumber>
    Raster &operator*=(OtherNumber value)
    {
        std::for_each(data_, data_ + (cols_ * rows_),
                      [&value](Number &a) { a *= value; });
        return *this;
    }

    template <typename OtherNumber>
    Raster &operator/=(OtherNumber value)
    {
        std::for_each(data_, data_ + (cols_ * rows_),
                      [&value](Number &a) { a /= value; });
        return *this;
    }

    template <typename OtherNumber>
    typename std::enable_if<std::is_floating_point<Number>::value ||
                                std::is_same<Number, OtherNumber>::value,
                            Raster &>::type
    operator+=(const Raster<OtherNumber> &image)
    {
        for_each_zip(data_, data_ + (cols_ * rows_), image.data(),
                     [](Number &a, const OtherNumber &b) { a += b; });
        return *this;
    }

    template <typename OtherNumber>
    typename std::enable_if<std::is_floating_point<Number>::value ||
                                std::is_same<Number, OtherNumber>::value,
                            Raster &>::type
    operator-=(const Raster<OtherNumber> &image)
    {
        for_each_zip(data_, data_ + (cols_ * rows_), image.data(),
                     [](Number &a, const OtherNumber &b) { a -= b; });
        return *this;
    }

    template <typename OtherNumber>
    typename std::enable_if<std::is_floating_point<Number>::value ||
                                std::is_same<Number, OtherNumber>::value,
                            Raster &>::type
    operator*=(const Raster<OtherNumber> &image)
    {
        for_each_zip(data_, data_ + (cols_ * rows_), image.data(),
                     [](Number &a, const OtherNumber &b) { a *= b; });
        return *this;
    }

    template <typename OtherNumber>
    typename std::enable_if<std::is_floating_point<Number>::value ||
                                std::is_same<Number, OtherNumber>::value,
                            Raster &>::type
    operator/=(const Raster<OtherNumber> &image)
    {
        for_each_zip(data_, data_ + (cols_ * rows_), image.data(),
                     [](Number &a, const OtherNumber &b) { a /= b; });
        return *this;
    }

    bool operator==(const Raster &other) const
    {
        // TODO: assumes same sizes
        for (Index i = 0; i < cols_; i++) {
            for (Index j = 0; j < cols_; j++) {
                if (this->data_[i * cols_ + j] != other.data_[i * cols_ + j])
                    return false;
            }
        }
        return true;
    }

    bool operator!=(const Raster &other) const
    {
        // TODO: assumes same sizes
        for (Index i = 0; i < cols_; i++) {
            for (Index j = 0; j < cols_; j++) {
                if (this->data_[i * cols_ + j] != other.data_[i * cols_ + j])
                    return true;
            }
        }
        return false;
    }

    template <typename OtherNumber>
    friend inline
        typename std::enable_if<std::is_arithmetic<OtherNumber>::value,
                                Raster>::type
        operator+(const Raster &raster, OtherNumber value)
    {
        auto out = Raster(raster.rows(), raster.cols());

        std::transform(
            raster.data(), raster.data() + (raster.cols() * raster.rows()),
            out.data(), [&value](const Number &a) { return a + value; });
        return out;
    }

    template <typename OtherNumber>
    friend inline
        typename std::enable_if<std::is_arithmetic<OtherNumber>::value,
                                Raster>::type
        operator-(const Raster &raster, OtherNumber value)
    {
        auto out = Raster(raster.rows(), raster.cols());

        std::transform(
            raster.data(), raster.data() + (raster.cols() * raster.rows()),
            out.data(), [&value](const Number &a) { return a - value; });
        return out;
    }

    template <typename OtherNumber>
    friend inline
        typename std::enable_if<std::is_arithmetic<OtherNumber>::value,
                                Raster>::type
        operator*(const Raster &raster, OtherNumber value)
    {
        auto out = Raster(raster.rows(), raster.cols());

        std::transform(
            raster.data(), raster.data() + (raster.cols() * raster.rows()),
            out.data(), [&value](const Number &a) { return a * value; });
        return out;
    }

    template <typename OtherNumber>
    friend inline
        typename std::enable_if<std::is_arithmetic<OtherNumber>::value,
                                Raster>::type
        operator/(const Raster &raster, OtherNumber value)
    {
        auto out = Raster(raster.rows(), raster.cols());

        std::transform(
            raster.data(), raster.data() + (raster.cols() * raster.rows()),
            out.data(), [&value](const Number &a) { return a / value; });
        return out;
    }

    template <typename OtherNumber>
    friend inline
        typename std::enable_if<std::is_arithmetic<OtherNumber>::value,
                                Raster>::type
        operator+(OtherNumber value, const Raster &raster)
    {
        return raster + value;
    }

    template <typename OtherNumber>
    friend inline
        typename std::enable_if<std::is_arithmetic<OtherNumber>::value,
                                Raster>::type
        operator-(OtherNumber value, const Raster &raster)
    {
        auto out = Raster(raster.rows(), raster.cols());

        std::transform(
            raster.data(), raster.data() + (raster.cols() * raster.rows()),
            out.data(), [&value](const Number &a) { return value - a; });
        return out;
    }

    template <typename OtherNumber>
    friend inline
        typename std::enable_if<std::is_arithmetic<OtherNumber>::value,
                                Raster>::type
        operator*(OtherNumber value, const Raster &raster)
    {
        return raster * value;
    }

    template <typename OtherNumber>
    friend inline
        typename std::enable_if<std::is_arithmetic<OtherNumber>::value,
                                Raster>::type
        operator/(OtherNumber value, const Raster &raster)
    {
        auto out = Raster(raster.rows(), raster.cols());

        std::transform(
            raster.data(), raster.data() + (raster.cols() * raster.rows()),
            out.data(), [&value](const Number &a) { return value / a; });
        return out;
    }

    friend inline Raster pow(Raster image, double value)
    {
        image.for_each([value](Number &a) { a = std::pow(a, value); });
        return image;
    }
    friend inline Raster sqrt(Raster image)
    {
        image.for_each([](Number &a) { a = std::sqrt(a); });
        return image;
    }

    friend inline std::ostream &operator<<(std::ostream &stream,
                                           const Raster &image)
    {
        stream << "[[";
        for (Index i = 0; i < image.rows_; i++) {
            if (i != 0)
                stream << "],\n [";
            for (Index j = 0; j < image.cols_; j++) {
                if (j != 0)
                    stream << ", ";
                stream << image.data_[i * image.cols_ + j];
            }
        }
        stream << "]]\n";
        return stream;
    }
};

template <typename LeftNumber, typename RightNumber,
          typename ResultNumber =
              typename std::common_type<LeftNumber, RightNumber>::type>
Raster<ResultNumber> operator+(const Raster<LeftNumber> &lhs,
                               const Raster<RightNumber> &rhs)
{
    if (lhs.cols() != rhs.cols() || lhs.rows() != rhs.rows()) {
        throw std::invalid_argument(
            "Raster::operator+: The number of rows or columns does not match");
    }
    auto out = Raster<ResultNumber>(lhs.rows(), lhs.cols());

    std::transform(
        lhs.data(), lhs.data() + (lhs.cols() * lhs.rows()), rhs.data(),
        out.data(),
        [](const LeftNumber &a, const RightNumber &b) { return a + b; });
    return out;
}

template <typename LeftNumber, typename RightNumber,
          typename ResultNumber =
              typename std::common_type<LeftNumber, RightNumber>::type>
Raster<ResultNumber> operator-(const Raster<LeftNumber> &lhs,
                               const Raster<RightNumber> &rhs)
{
    if (lhs.cols() != rhs.cols() || lhs.rows() != rhs.rows()) {
        throw std::invalid_argument(
            "Raster::operator-: The number of rows or columns does not match");
    }
    auto out = Raster<ResultNumber>(lhs.rows(), lhs.cols());

    std::transform(
        lhs.data(), lhs.data() + (lhs.cols() * lhs.rows()), rhs.data(),
        out.data(),
        [](const LeftNumber &a, const RightNumber &b) { return a - b; });
    return out;
}

template <typename LeftNumber, typename RightNumber,
          typename ResultNumber =
              typename std::common_type<LeftNumber, RightNumber>::type>
Raster<ResultNumber> operator*(const Raster<LeftNumber> &lhs,
                               const Raster<RightNumber> &rhs)
{
    if (lhs.cols() != rhs.cols() || lhs.rows() != rhs.rows()) {
        throw std::invalid_argument(
            "Raster::operator*: The number of rows or columns does not match");
    }
    auto out = Raster<ResultNumber>(lhs.rows(), lhs.cols());

    std::transform(
        lhs.data(), lhs.data() + (lhs.cols() * lhs.rows()), rhs.data(),
        out.data(),
        [](const LeftNumber &a, const RightNumber &b) { return a * b; });
    return out;
}

template <typename LeftNumber, typename RightNumber,
          typename ResultNumber =
              typename std::common_type<LeftNumber, RightNumber>::type>
Raster<ResultNumber> operator/(const Raster<LeftNumber> &lhs,
                               const Raster<RightNumber> &rhs)
{
    if (lhs.cols() != rhs.cols() || lhs.rows() != rhs.rows()) {
        throw std::invalid_argument(
            "Raster::operator/: The number of rows or columns does not match");
    }
    auto out = Raster<ResultNumber>(lhs.rows(), lhs.cols());

    std::transform(
        lhs.data(), lhs.data() + (lhs.cols() * lhs.rows()), rhs.data(),
        out.data(),
        [](const LeftNumber &a, const RightNumber &b) { return a / b; });
    return out;
}

} // namespace pops

#endif // POPS_RASTER_HPP
