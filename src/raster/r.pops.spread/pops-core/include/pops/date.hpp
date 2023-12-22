/*
 * PoPS model - date manipulation
 *
 * Copyright (C) 2015-2020 by the authors.
 *
 * Authors: Zexi Chen (zchen22 ncsu edu)
 *          Anna Petrasova
 *          Chris Jones
 *
 * The code contained herein is licensed under the GNU General Public
 * License. You may obtain a copy of the GNU General Public License
 * Version 2 or later at the following locations:
 *
 * http://www.opensource.org/licenses/gpl-license.html
 * http://www.gnu.org/copyleft/gpl.html
 */

#ifndef POPS_DATE_HPP
#define POPS_DATE_HPP

#include <iostream>
#include <string>
#include <stdexcept>

namespace pops {

/*! Representation and manipulation of a date for the simulation.
 *
 * This class represents and manipulates dates in way which is most
 * useful for the PoPS simulation, i.e. by weeks and months.
 */
class Date {

private:
    int year_;
    int month_;
    int day_;
    int day_in_month[2][13] = {
        {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31},
        {0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31}};

public:
    Date(const Date &d) : year_(d.year_), month_(d.month_), day_(d.day_) {}
    Date(int y, int m, int d) : year_(y), month_(m), day_(d) {}
    Date(std::string date);
    Date &operator=(const Date &) = default;
    inline void increased_by_days(int num_days);
    inline void increased_by_week();
    inline void increased_by_month();
    inline void add_day();
    inline void add_days(unsigned n);
    inline void subtract_day();
    inline void subtract_days(unsigned n);
    inline Date get_year_end();
    inline Date get_next_year_end();
    inline Date get_last_day_of_week();
    inline Date get_last_day_of_month();
    inline bool is_last_week_of_year();
    inline bool is_last_month_of_year();
    inline bool is_last_day_of_year();
    inline bool is_last_day_of_month();
    inline bool is_last_week_of_month();
    inline bool is_leap_year();
    int month() const { return month_; }
    int year() const { return year_; }
    int day() const { return day_; }
    inline int weeks_from_date(Date start);
    inline friend std::ostream &operator<<(std::ostream &os, const Date &d);
    inline friend bool operator>(const Date &d1, const Date &d2);
    inline friend bool operator>=(const Date &d1, const Date &d2);
    inline friend bool operator<(const Date &d1, const Date &d2);
    inline friend bool operator<=(const Date &d1, const Date &d2);
    inline friend bool operator==(const Date &d1, const Date &d2);
    inline friend bool operator!=(const Date &d1, const Date &d2);
};

/*!
 * \brief Construct date from string
 *
 * Checks if months and days are in proper range
 * (ignores Feb leap year), throws invalid_argument exception
 *
 * \param date in the format YYYY-MM-DD (or Y-M-D)
 */
Date::Date(std::string date)
{
    size_t pos = date.find("-");
    year_ = std::stoi(date.substr(0, pos));
    date.erase(0, pos + 1);
    pos = date.find("-");
    month_ = std::stoi(date.substr(0, pos));
    date.erase(0, pos + 1);
    day_ = std::stoi(date);
    if (month_ <= 0 || month_ > 12 || day_ > day_in_month[1][month_])
        throw std::invalid_argument("Invalid date specified");
}

std::ostream &operator<<(std::ostream &os, const Date &d)
{
    os << d.year_ << '-' << d.month_ << '-' << d.day_;
    return os;
}

Date Date::get_year_end()
{
    return Date(year_, 12, 31);
}
/*!
 * Assumes we call it on the first day of a week.
 * Weeks always start 1/1.
 * Advances date by week and subtracts 1 day to work
 * correctly at the end of the year.
 */
Date Date::get_last_day_of_week()
{
    Date d = Date(*this);
    d.increased_by_week();
    d.day_--;
    if (d.day_ == 0) {
        d.month_--;
        if (d.month_ == 0) {
            d.year_--;
            d.month_ = 12;
        }
        d.day_ = day_in_month[is_leap_year()][d.month_];
    }
    return d;
}

/*!
 * Compute the last day of a month.
 */
Date Date::get_last_day_of_month()
{
    if (this->is_leap_year())
        return Date(year_, month_, day_in_month[1][month_]);
    return Date(year_, month_, day_in_month[0][month_]);
}

bool Date::is_last_week_of_year()
{
    if (month_ == 12 && (day_ + 9) > 31)
        return true;
    return false;
}

bool Date::is_last_month_of_year()
{
    if (month_ == 12)
        return true;
    return false;
}

bool Date::is_last_day_of_year()
{
    if (month_ == 12 && day_ == 31)
        return true;
    return false;
}

bool Date::is_last_week_of_month()
{
    if (this->is_leap_year()) {
        if ((day_ + 7) >= day_in_month[1][month_])
            return true;
        return false;
    }
    else {
        if ((day_ + 7) >= day_in_month[0][month_])
            return true;
        return false;
    }
}

bool Date::is_last_day_of_month()
{
    if (this->is_leap_year()) {
        if (day_ == day_in_month[1][month_])
            return true;
        return false;
    }
    else {
        if (day_ == day_in_month[0][month_])
            return true;
        return false;
    }
}

Date Date::get_next_year_end()
{
    if (month_ == 1)
        return Date(year_, 12, 31);
    else
        return Date(year_ + 1, 12, 31);
}

bool Date::is_leap_year()
{
    if (year_ % 4 == 0 && (year_ % 100 != 0 || year_ % 400 == 0))
        return true;
    return false;
}

bool operator>(const Date &d1, const Date &d2)
{
    if (d1.year_ < d2.year_)
        return false;
    else if (d1.year_ > d2.year_)
        return true;
    else {
        if (d1.month_ < d2.month_)
            return false;
        else if (d1.month_ > d2.month_)
            return true;
        else {
            if (d1.day_ <= d2.day_)
                return false;
            else
                return true;
        }
    }
}

bool operator<=(const Date &d1, const Date &d2)
{
    return !(d1 > d2);
}

bool operator<(const Date &d1, const Date &d2)
{
    if (d1.year_ > d2.year_)
        return false;
    else if (d1.year_ < d2.year_)
        return true;
    else {
        if (d1.month_ > d2.month_)
            return false;
        else if (d1.month_ < d2.month_)
            return true;
        else {
            if (d1.day_ >= d2.day_)
                return false;
            else
                return true;
        }
    }
}

bool operator>=(const Date &d1, const Date &d2)
{
    return !(d1 < d2);
}

bool operator==(const Date &d1, const Date &d2)
{
    if (d1.year_ == d2.year_ && d1.month_ == d2.month_ && d1.day_ == d2.day_)
        return true;
    return false;
}

bool operator!=(const Date &d1, const Date &d2)
{
    if (d1 == d2)
        return false;
    return true;
}
/*!
 * Increases the date by the num_days (specified by the user) except on
 * the last timestep of the year, which is increased by num_days
 * plus the number of  days left in the year that are less
 * than num_days (e.g. if the num_days = 28 the last time step is 29
 * or 30 (if leap year), if num_days = 23 that last time step is 43
 * or 44 (if leap year) days). This ensures that each year of the
 * forecast starts on January 1st.
 */
void Date::increased_by_days(int num_days)
{
    day_ += num_days;
    if (this->is_leap_year()) {
        if (month_ == 12 && day_ > (31 - (num_days + 1))) {
            year_++;
            month_ = 1;
            day_ = 1;
        }
        if (day_ > day_in_month[1][month_]) {
            day_ = day_ - day_in_month[1][month_];
            month_++;
            if (month_ > 12) {
                year_++;
                month_ = 1;
            }
        }
    }
    else {
        if (month_ == 12 && day_ > (31 - num_days)) {
            year_++;
            month_ = 1;
            day_ = 1;
        }
        if (day_ > day_in_month[0][month_]) {
            day_ = day_ - day_in_month[0][month_];
            month_++;
            if (month_ > 12) {
                year_++;
                month_ = 1;
            }
        }
    }
}

/*!
 * Increases the date by one week (7 days) except on the last week
 * of the year, which is increased by 8 or 9 days if a leap year.
 * This ensures that each year of the forecast starts on January 1st.
 */
void Date::increased_by_week()
{
    day_ += 7;
    if (this->is_leap_year()) {
        if (month_ == 12 && day_ > 23) {
            year_++;
            month_ = 1;
            day_ = 1;
        }
        if (day_ > day_in_month[1][month_]) {
            day_ = day_ - day_in_month[1][month_];
            month_++;
            if (month_ > 12) {
                year_++;
                month_ = 1;
            }
        }
    }
    else {
        if (month_ == 12 && day_ > 24) {
            year_++;
            month_ = 1;
            day_ = 1;
        }
        if (day_ > day_in_month[0][month_]) {
            day_ = day_ - day_in_month[0][month_];
            month_++;
            if (month_ > 12) {
                year_++;
                month_ = 1;
            }
        }
    }
}

void Date::increased_by_month()
{
    month_ += 1;
    if (month_ > 12) {
        year_++;
        month_ = 1;
    }
    if (this->is_leap_year()) {
        if (day_ > day_in_month[1][month_]) {
            day_ = day_in_month[1][month_];
        }
    }
    else {
        if (day_ > day_in_month[0][month_]) {
            day_ = day_in_month[0][month_];
        }
    }
}
/*!
 * \brief Adds 1 day to a date
 */
void Date::add_day()
{
    day_++;
    if (day_ > day_in_month[is_leap_year()][month_]) {
        day_ = 1;
        month_++;
        if (month_ > 12) {
            year_++;
            month_ = 1;
        }
    }
}
/*!
 * \brief Subtract 1 day from a date
 */
void Date::subtract_day()
{
    day_--;
    if (day_ == 0) {
        month_--;
        if (month_ == 0) {
            year_--;
            month_ = 12;
        }
        day_ = day_in_month[is_leap_year()][month_];
    }
}
/*!
 * \brief Adds N days to a date
 */
void Date::add_days(unsigned n)
{
    for (unsigned i = 0; i < n; i++)
        this->add_day();
}

/*!
 * \brief Subtract N days from a date
 */
void Date::subtract_days(unsigned n)
{
    for (unsigned i = 0; i < n; i++)
        this->subtract_day();
}

/*!
 * Gets number of weeks between start date and this date.
 *
 * The parameter is copied and untouched.
 *
 * \param start date to start from
 * \return Number of weeks
 */
int Date::weeks_from_date(Date start)
{

    int week = 0;
    while (start <= *this) {
        week++;
        start.increased_by_week();
    }
    return week - 1;
}

/*!
 * Holds begining and end of a season and decides what is in season
 */
class Season {
public:
    Season(int start, int end) : start_month_(start), end_month_(end) {}
    /*!
     * \brief Decides if a month is in season or not
     * \param month A month in year (1-12)
     * \return true if in season, false otherwise
     */
    inline bool month_in_season(int month) const
    {
        return month >= start_month_ && month <= end_month_;
    }

private:
    int start_month_;
    int end_month_;
};

} // namespace pops

#endif // POPS_DATE_HPP
