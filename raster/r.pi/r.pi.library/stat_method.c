#include "r_pi.h"

DCELL average(DCELL * vals, int count)
{
    int i;
    DCELL res = 0;

    if (count <= 0)
	return 0;

    for (i = 0; i < count; i++)
	res += vals[i];

    return res / count;
}

DCELL variance(DCELL * vals, int count)
{
    int i;
    DCELL mean;
    DCELL s = 0;
    DCELL ss = 0;

    if (count <= 0)
	return 0;

    for (i = 0; i < count; i++) {
	DCELL val = vals[i];

	s += val;
	ss += val * val;
    }

    mean = s / (DCELL) count;
    return ss / count - mean * mean;
}

DCELL std_deviat(DCELL * vals, int count)
{
    if (count <= 0)
	return 0;

    return sqrt(variance(vals, count));
}

DCELL median(DCELL * vals, int count)
{
    int k = (count - 1) / 2;
    int l = 0;
    int h = count - 1;
    DCELL pivot, tmp;
    int i, j;

    if (count <= 0)
	return 0;

    while (l < h) {
	pivot = vals[k];
	i = l;
	j = h;

	do {
	    while (vals[i] < pivot)
		i++;
	    while (vals[j] > pivot)
		j--;
	    if (i <= j) {
		tmp = vals[i];
		vals[i] = vals[j];
		vals[j] = tmp;
		i++;
		j--;
	    }
	} while (i <= j);

	if (j < k)
	    l = i;
	if (i > k)
	    h = j;
    }

    return vals[k];
}

DCELL min(DCELL * vals, int count)
{
    int i;
    DCELL res = 0;

    if (count <= 0)
	return 0;

    res = vals[0];
    for (i = 0; i < count; i++)
	if (vals[i] < res)
	    res = vals[i];

    return res;
}

DCELL max(DCELL * vals, int count)
{
    int i;
    DCELL res = 0;

    if (count <= 0)
	return 0;

    res = vals[0];
    for (i = 0; i < count; i++)
	if (vals[i] > res)
	    res = vals[i];

    return res;
}

DCELL linear(DCELL value, DCELL propcost)
{
    value -= propcost;
    return value >= 0.0 ? value : 0.0;
}

DCELL exponential(DCELL value, DCELL propcost)
{
    if (propcost == 0.0) {
	return MAX_DOUBLE;
    }
    else {
	return value / propcost;
    }
}
