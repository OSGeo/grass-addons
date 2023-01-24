#include "local_proto.h"

/* These functions are taken from the module r.quantile (Clemens, G.) */

struct bin {
    unsigned long origin;
    double minimum, maximum;
    int base, count;
};

static double minimum, maximum;
static int num_quants;
static double *quants;
static int num_slots;
static unsigned int *slots;
static double slot_size;
static unsigned long total;
static int num_values;
static unsigned short *slot_bins;
static int num_bins;
static struct bin *bins;
static double *values;

static inline int get_slot(double c)
{
    int i = (int)floor((c - minimum) / slot_size);

    if (i < 0)
        i = 0;
    if (i > num_slots - 1)
        i = num_slots - 1;
    return i;
}

double get_quantile(int n)
{
    return (double)total * quants[n]; // # of lower values
}

void get_slot_counts(int n, double *data)
{
    int i;

    total = 0;
    for (i = 0; i < n; i++) {
        int j;

        // todo nan
        j = get_slot(data[i]);

        slots[j]++; // rise value of j-th slot
        total++;
    }
    // G_percent(i, n, 2);
}

void initialize_bins(void)
{
    int slot;    // index of slot
    double next; // percentile
    int bin = 0; // adjacent bin
    unsigned long accum = 0;
    int quant = 0; // index of percentile

    num_values = 0;
    next = get_quantile(quant); // # of lower values

    for (slot = 0; slot < num_slots; slot++) {
        unsigned int count =
            slots[slot]; // assign # of elements in each slots to the count
        unsigned long accum2 = accum + count; // total # of elements

        if (accum2 > next) { // # of values is greater than percentile
            struct bin *b = &bins[bin]; // make bin

            slot_bins[slot] = ++bin;

            b->origin = accum; // origin of bin = total # of elements
            b->base = num_values;
            b->count = 0;
            b->minimum = minimum + slot_size * slot;
            b->maximum = minimum + slot_size * (slot + 1);

            while (accum2 > next)
                next = get_quantile(++quant);

            num_values += count;
        }

        accum = accum2;
    }

    num_bins = bin;
}

void fill_bins(int n, double *data)
{
    int i;

    for (i = 0; i < n; i++) {
        int j, bin;
        struct bin *b;

        // todo nan

        j = get_slot(data[i]);

        if (!slot_bins[j])
            continue;

        bin = slot_bins[j] - 1;
        b = &bins[bin];

        values[b->base + b->count++] = data[i];
    }

    // G_percent(i, n, 2);
}

int compare(const void *aa, const void *bb)
{
    double a = *(const double *)aa;
    double b = *(const double *)bb;

    if (a < b)
        return -1;
    if (a > b)
        return 1;
    return 0;
}

void sort_bins(void)
{
    int bin;

    for (bin = 0; bin < num_bins; bin++) {
        struct bin *b = &bins[bin];

        qsort(&values[b->base], b->count, sizeof(double), compare);
        // G_percent(bin, num_bins, 2);
    }
    // G_percent(bin, num_bins, 2);
}

void compute_quantiles(int recode, double *quantile, struct write *report)
{
    int bin = 0;
    double prev_v = minimum;
    int quant;

    for (quant = 0; quant < num_quants; quant++) {
        struct bin *b;
        double next = get_quantile(quant);
        double k, v;
        int i0, i1;

        for (; bin < num_bins; bin++) {
            b = &bins[bin];
            if (b->origin + b->count >= next)
                break;
        }

        if (bin < num_bins) {
            k = next - b->origin;
            i0 = (int)floor(k);
            i1 = (int)ceil(k);

            if (i1 > b->count - 1)
                i1 = b->count - 1;

            v = (i0 == i1) ? values[b->base + i0]
                           : values[b->base + i0] * (i1 - k) +
                                 values[b->base + i1] * (k - i0);
        }
        else
            v = maximum;

        *quantile = v;
        prev_v = v;
        if (report != NULL && report->name)
            fprintf(report->fp, "%f:%f:%f\n", prev_v, v, quants[quant]);
    }
}

double quantile(double q, int n, double *data, struct write *report)
{
    int i, recode = FALSE;
    double quantile;

    num_slots = 1000000; // # of slots

    num_quants = 1;
    quants = (double *)G_malloc(num_quants * sizeof(double));
    quants[0] = q; // compute quantile for 0.05

    // initialize list of slots
    slots = (unsigned int *)G_calloc(num_slots, sizeof(unsigned int));
    slot_bins = (unsigned short *)G_calloc(num_slots, sizeof(unsigned short));

    // get min and max of the data
    minimum = data[0];
    maximum = data[0];
    for (i = 0; i < n; i++) {
        minimum = MIN(data[i], minimum);
        maximum = MAX(data[i], maximum);
    }

    slot_size = (maximum - minimum) / num_slots;
    get_slot_counts(n, data); // # of data in each slot

    bins = (struct bin *)G_calloc(num_quants, sizeof(struct bin));
    initialize_bins();
    G_free(slots);

    values = (double *)G_calloc(num_values, sizeof(double));
    fill_bins(n, data);
    G_free(slot_bins);

    sort_bins();
    compute_quantiles(recode, &quantile, report);

    return quantile;
}
