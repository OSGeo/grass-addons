#ifndef MISC_H_
#define MISC_H_

/* denotes the range [from,to] of integers */
typedef struct
{
    int from, to;
} RANGE;

/* verifies whether given string is valid (category) range
 * either "number-number" where first <= second or "number"
 * return 1 on success, 0 otherwise
 */
int check_range(char *s);
/* sets the array of category ranges. Return 1 on success 
 * this function expects the valid ranges. i.e already checked 
 * and count is the number of ranges 
 */
int get_ranges(char **s, RANGE ** out, int *count);

/* tests whether at least one cetagory number lies in at least
 * one range. Where n is the number of ranges in r.
 * return 1 on success, 0 otherwise
 */
int cat_test(struct line_cats *Cats, RANGE * r, int n);

#endif
