#define P_MEAN     0x001
#define P_MEDIAN   0x002
#define P_MEDIAN_P 0x004
#define L_MID      0x008
#define L_MEAN     0x010
#define L_MEDIAN   0x020
#define A_MEAN     0x040
#define A_MEDIAN   0x080
#define A_MEDIAN_B 0x100

int points_center(struct Map_info *, struct Map_info *, int, struct cat_list *,
                  int, int);
double d_ulp(double);

int lines_center(struct Map_info *, struct Map_info *, int, struct cat_list *,
                 int, int);

int areas_center(struct Map_info *, struct Map_info *, int, struct cat_list *,
                 int);
