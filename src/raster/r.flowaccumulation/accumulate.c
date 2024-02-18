#include <grass/raster.h>
#include "global.h"

void accumulate(struct raster_map *dir_map, struct raster_map *accum_map,
                int check_overflow, int use_less_memory, int use_zero)
{
    switch (accum_map->type) {
    case CELL_TYPE:
        if (check_overflow) {
            if (use_less_memory) {
                if (use_zero)
                    accumulate_comz(dir_map, accum_map);
                else
                    accumulate_com(dir_map, accum_map);
            }
            else {
                if (use_zero)
                    accumulate_coz(dir_map, accum_map);
                else
                    accumulate_co(dir_map, accum_map);
            }
        }
        else {
            if (use_less_memory) {
                if (use_zero)
                    accumulate_cmz(dir_map, accum_map);
                else
                    accumulate_cm(dir_map, accum_map);
            }
            else {
                if (use_zero)
                    accumulate_cz(dir_map, accum_map);
                else
                    accumulate_c(dir_map, accum_map);
            }
        }
        break;
    case FCELL_TYPE:
        if (check_overflow) {
            if (use_less_memory) {
                if (use_zero)
                    accumulate_fomz(dir_map, accum_map);
                else
                    accumulate_fom(dir_map, accum_map);
            }
            else {
                if (use_zero)
                    accumulate_foz(dir_map, accum_map);
                else
                    accumulate_fo(dir_map, accum_map);
            }
        }
        else {
            if (use_less_memory) {
                if (use_zero)
                    accumulate_fmz(dir_map, accum_map);
                else
                    accumulate_fm(dir_map, accum_map);
            }
            else {
                if (use_zero)
                    accumulate_fz(dir_map, accum_map);
                else
                    accumulate_f(dir_map, accum_map);
            }
        }
        break;
    default:
        if (check_overflow) {
            if (use_less_memory) {
                if (use_zero)
                    accumulate_domz(dir_map, accum_map);
                else
                    accumulate_dom(dir_map, accum_map);
            }
            else {
                if (use_zero)
                    accumulate_doz(dir_map, accum_map);
                else
                    accumulate_do(dir_map, accum_map);
            }
        }
        else {
            if (use_less_memory) {
                if (use_zero)
                    accumulate_dmz(dir_map, accum_map);
                else
                    accumulate_dm(dir_map, accum_map);
            }
            else {
                if (use_zero)
                    accumulate_dz(dir_map, accum_map);
                else
                    accumulate_d(dir_map, accum_map);
            }
        }
        break;
    }
}

void nullify_zero(struct raster_map *accum_map)
{
    switch (accum_map->type) {
    case CELL_TYPE:
        nullify_zero_c(accum_map);
        break;
    case FCELL_TYPE:
        nullify_zero_f(accum_map);
        break;
    default:
        nullify_zero_d(accum_map);
        break;
    }
}
