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


#ifndef DATE
#define DATE

#include <iostream>

class Date{

private:
    int year;
    int month;
    int day;
    int day_in_month[2][13] = {
        {0,31,28,31,30,31,30,31,31,30,31,30,31},
        {0,31,29,31,30,31,30,31,31,30,31,30,31}
    };

public:
    Date(const Date &d): year(d.year), month(d.month), day(d.day){}
    Date(int y, int m, int d): year(y), month(m), day(d){}
    Date(): year(2000), month(1), day(1){}
    inline void increasedByWeek();
    inline void increasedByMonth();
    inline Date getYearEnd();
    inline Date getNextYearEnd();
    inline bool isYearEnd();
    inline bool isLastMonthOfYear();
    int getMonth() const {return month;}
    int getYear() const { return year;}
    int getDay() const {return day;}
    void setMonth(int m){month = m;}
    void setYear(int y){year = y;}
    void setDay(int d){day = d;}
    inline int weeksFromDate(Date start);
    inline friend std::ostream& operator<<(std::ostream& os, const Date &d);
    inline friend bool operator> (const Date &d1, const Date &d2);
    inline friend bool operator>= (const Date &d1, const Date &d2);
    inline friend bool operator< (const Date &d1, const Date &d2);
    inline friend bool operator<= (const Date &d1, const Date &d2);
};

std::ostream& operator<<(std::ostream& os, const Date &d)
{
    os << d.year << '-' << d.month << '-' << d.day;
    return os;
}

Date Date::getYearEnd() {
    return Date(year, 12, 31);
}

bool Date::isYearEnd(){
    if (month == 12 && (day + 7) > 31)
        return true;
    return false;
}

bool Date::isLastMonthOfYear(){
    if (month == 12)
        return true;
    return false;
}

Date Date::getNextYearEnd(){
    if (month == 1)
        return Date(year, 12, 31);
    else
        return Date(year + 1, 12, 31);
}

bool operator> (const Date &d1, const Date &d2)
{
    if(d1.year < d2.year)
        return false;
    else if (d1.year > d2.year)
        return true;
    else {
        if (d1.month < d2.month)
            return false;
        else if (d1.month > d2.month)
            return true;
        else {
            if (d1.day <= d2.day)
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
    if(d1.year > d2.year)
        return false;
    else if (d1.year < d2.year)
        return true;
    else {
        if (d1.month > d2.month)
            return false;
        else if (d1.month < d2.month)
            return true;
        else {
            if (d1.day >= d2.day)
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

void Date::increasedByWeek()
{
    day += 7;
    if (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)) {
        if (day > day_in_month[1][month]) {
            day = day - day_in_month[1][month];
            month++;
            if (month > 12) {
                year++;
                month = 1;
            }
        }
    }
    else {
        if (day > day_in_month[0][month]) {
            day = day - day_in_month[0][month];
            month++;
            if (month > 12) {
                year++;
                month = 1;
            }
        }
    }
}

void Date::increasedByMonth()
{
    month += 1;
    if (month > 12) {
        year++;
        month = 1;
    }
    if (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)) {
        if (day > day_in_month[1][month]) {
            day = day_in_month[1][month];
        }
    }
    else {
        if (day > day_in_month[0][month]) {
            day = day_in_month[0][month];
        }
    }
}

int Date::weeksFromDate(Date start) {

    int week = 0;
    while (start <= *this) {
        week++;
        start.increasedByWeek();
    }
    return week - 1;
}

#endif // DATE
