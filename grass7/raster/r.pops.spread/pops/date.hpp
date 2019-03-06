/*
 * SOD model - date manipulation
 *
 * Copyright (C) 2015-2017 by the authors.
 *
 * Authors: Zexi Chen (zchen22 ncsu edu)
 *          Anna Petrasova
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

namespace pops {

/*! Representation and manipulation of a date for the simulation.
 *
 * This class represents and manipulates dates in way which is most
 * useful for the PoPS simulation, i.e. by weeks and months.
 */
class Date
{

private:
    int year_;
    int month_;
    int day_;
    int day_in_month[2][13] = {
        {0,31,28,31,30,31,30,31,31,30,31,30,31},
        {0,31,29,31,30,31,30,31,31,30,31,30,31}
    };

public:
    Date(const Date& d): year_(d.year_), month_(d.month_), day_(d.day_) {}
    Date(int y, int m, int d): year_(y), month_(m), day_(d) {}
    inline void increased_by_week();
    inline void increased_by_month();
    inline Date get_year_end();
    inline Date get_next_year_end();
    inline bool is_last_week_of_year();
    inline bool is_last_month_of_year();
    int month() const { return month_; }
    int year() const { return year_; }
    int day() const { return day_; }
    inline int weeks_from_date(Date start);
    inline friend std::ostream& operator<<(std::ostream& os, const Date &d);
    inline friend bool operator> (const Date &d1, const Date &d2);
    inline friend bool operator>= (const Date &d1, const Date &d2);
    inline friend bool operator< (const Date &d1, const Date &d2);
    inline friend bool operator<= (const Date &d1, const Date &d2);
};

std::ostream& operator<<(std::ostream& os, const Date &d)
{
    os << d.year_ << '-' << d.month_ << '-' << d.day_;
    return os;
}

Date Date::get_year_end()
{
    return Date(year_, 12, 31);
}

bool Date::is_last_week_of_year()
{
    if (month_ == 12 && (day_ + 7) > 31)
        return true;
    return false;
}

bool Date::is_last_month_of_year()
{
    if (month_ == 12)
        return true;
    return false;
}

Date Date::get_next_year_end()
{
    if (month_ == 1)
        return Date(year_, 12, 31);
    else
        return Date(year_ + 1, 12, 31);
}

bool operator> (const Date &d1, const Date &d2)
{
    if(d1.year_ < d2.year_)
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

bool operator<= (const Date &d1, const Date &d2)
{
    return !(d1 > d2);
}

bool operator< (const Date &d1, const Date &d2)
{
    if(d1.year_ > d2.year_)
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

bool operator>= (const Date &d1, const Date &d2)
{
    return !(d1 < d2);
}

void Date::increased_by_week()
{
    day_ += 7;
    if (year_ % 4 == 0 && (year_ % 100 != 0 || year_ % 400 == 0)) {
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
    if (year_ % 4 == 0 && (year_ % 100 != 0 || year_ % 400 == 0)) {
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
class Season
{
public:
    Season(int start, int end)
        : start_month_(start), end_month_(end)
    {}
    /*!
     * \brief Decides if a month is in season or not
     * \param month A month in year (1-12)
     * \return true if in season, false otherwise
     */
    inline bool month_in_season(int month)
    {
        return month >= start_month_ && month <= end_month_;
    }
private:
    int start_month_;
    int end_month_;
};

} // namespace pops

#endif // POPS_DATE_HPP
