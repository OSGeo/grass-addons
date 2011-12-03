
/*********************************************/
/*This program converts day/month/year to doy */

/*********************************************/

/*********************************************/

int date2doy(int day, int month, int year)
{
    int leap = 0;

    int day_month_tot = 0;

    int doy;

    doy = 0;

    /*printf("Date is %i/%i/%i\n", day, month, year); */

    if (month == 1) {
	day_month_tot = 0;
    }
    else if (month == 2) {
	day_month_tot = 31;
    }
    else if (month == 3) {
	day_month_tot = 59;
    }
    else if (month == 4) {
	day_month_tot = 90;
    }
    else if (month == 5) {
	day_month_tot = 120;
    }
    else if (month == 6) {
	day_month_tot = 151;
    }
    else if (month == 7) {
	day_month_tot = 181;
    }
    else if (month == 8) {
	day_month_tot = 212;
    }
    else if (month == 9) {
	day_month_tot = 243;
    }
    else if (month == 10) {
	day_month_tot = 273;
    }
    else if (month == 11) {
	day_month_tot = 304;
    }
    else if (month == 12) {
	day_month_tot = 334;
    }

    /* Leap year if dividing by 4 leads % 0.0 */

    if (year / 4 * 4 == year) {
	leap = 1;
    }

    doy = day_month_tot + day;
    if (doy > 59) {
	doy = day_month_tot + day + leap;
    }

    return (doy);
}
