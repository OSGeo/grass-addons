#include "r_pi.h"

DCELL average(DCELL *vals, int count)
{
    int i;
    DCELL res = 0;

    if (count <= 0)
        return 0;

    for (i = 0; i < count; i++)
        res += vals[i];

    return res / count;
}

DCELL variance(DCELL *vals, int count)
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

    mean = s / (DCELL)count;

    return ss / count - mean * mean;
}

DCELL std_deviat(DCELL *vals, int count)
{
    if (count <= 0)
        return 0;

    return sqrt(variance(vals, count));
}

DCELL median(DCELL *vals, int count)
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

void quicksort(DCELL *vals, int begin, int end)
{
    int i, j;
    DCELL pivot, tmp;

    if (end <= begin)
        return;

    i = begin;
    j = end - 1;
    pivot = vals[end];

    while (i <= j) {
        while (i <= j && vals[i] < pivot)
            i++;
        while (i <= j && vals[j] >= pivot)
            j--;

        if (i < j) {
            tmp = vals[i];
            vals[i] = vals[j];
            vals[j] = tmp;
            i++;
            j--;
        }
    }

    tmp = vals[i];
    vals[i] = vals[end];
    vals[end] = tmp;
    i++;

    quicksort(vals, begin, j);
    quicksort(vals, i, end);
}

DCELL mode(DCELL *vals, int count)
{
    DCELL actval, maxval;
    int actcnt, maxcnt;
    int actpos;

    if (count <= 0)
        return 0;

    quicksort(vals, 0, count - 1);

    /*
    fprintf(stderr, "vals = (%0.2f", vals[0]);
    for (i = 1; i < count; i++)
        fprintf(stderr, ",%0.2f", vals[i]);
    fprintf(stderr, ")\n\n");
    */

    maxval = 0;
    maxcnt = 0;
    actpos = 0;
    while (actpos < count) {
        actcnt = 0;
        actval = vals[actpos];
        while (actpos < count && actval == vals[actpos]) {
            actcnt++;
            actpos++;
        }
        if (actcnt > maxcnt) {
            maxcnt = actcnt;
            maxval = actval;
        }
    }

    return maxval;
}

DCELL min(DCELL *vals, int count)
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

DCELL max(DCELL *vals, int count)
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

DCELL sum(DCELL *vals, int count)
{
    int i;
    DCELL res = 0;

    if (count <= 0)
        return 0;

    for (i = 0; i < count; i++)
        res += vals[i];

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
