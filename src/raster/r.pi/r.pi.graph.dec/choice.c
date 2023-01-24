#include "local_proto.h"

int f_smallest_first(int cluster_index, Cluster *cluster_list,
                     int cluster_count, int *adjacency_matrix, Patch *fragments,
                     int fragcount, DCELL *distmatrix)
{
    int i;
    int min_area = MAX_INT;
    int min_index = -1;

    int begin = cluster_index >= 0 ? cluster_index : 0;
    int end = cluster_index >= 0 ? cluster_index : cluster_count - 1;
    int c;

    for (c = begin; c <= end; c++) {
        Cluster cluster = cluster_list[c];

        for (i = 0; i < cluster.count; i++) {
            int patch_index = cluster.first_patch[i];
            int area = fragments[patch_index].count;

            if (area < min_area) {
                min_area = area;
                min_index = i;

                if (cluster_index < 0) {
                    min_index = cluster.first_patch[min_index];
                }
            }
        }
    }

    return min_index;
}

int f_biggest_first(int cluster_index, Cluster *cluster_list, int cluster_count,
                    int *adjacency_matrix, Patch *fragments, int fragcount,
                    DCELL *distmatrix)
{
    int i;
    int max_area = -1;
    int max_index = -1;

    int begin = cluster_index >= 0 ? cluster_index : 0;
    int end = cluster_index >= 0 ? cluster_index : cluster_count - 1;
    int c;

    for (c = begin; c <= end; c++) {
        Cluster cluster = cluster_list[c];

        for (i = 0; i < cluster.count; i++) {
            int patch_index = cluster.first_patch[i];
            int area = fragments[patch_index].count;

            if (area > max_area) {
                max_area = area;
                max_index = i;

                if (cluster_index < 0) {
                    max_index = cluster.first_patch[max_index];
                }
            }
        }
    }

    return max_index;
}

int f_random(int cluster_index, Cluster *cluster_list, int cluster_count,
             int *adjacency_matrix, Patch *fragments, int fragcount,
             DCELL *distmatrix)
{

    int begin = cluster_index >= 0 ? cluster_index : 0;
    int end = cluster_index >= 0 ? cluster_index : cluster_count - 1;

    int patchcount = 0;
    int r, c;

    for (c = begin; c <= end; c++) {
        Cluster cluster = cluster_list[c];

        patchcount += cluster.count;
    }

    r = rand() % patchcount;

    for (c = begin; c <= end; c++) {
        int i;

        Cluster cluster = cluster_list[c];

        for (i = 0; i < cluster.count; i++) {
            if (r == 0) {
                if (cluster_index < 0) {
                    return cluster.first_patch[i];
                }
                else {
                    return i;
                }
            }

            r--;
        }
    }

    return -1;
}

int f_link_min(int cluster_index, Cluster *cluster_list, int cluster_count,
               int *adjacency_matrix, Patch *fragments, int fragcount,
               DCELL *distmatrix)
{
    int min_links = MAX_INT;
    int min_index = -1;

    int begin = cluster_index >= 0 ? cluster_index : 0;
    int end = cluster_index >= 0 ? cluster_index : cluster_count - 1;
    int c;

    for (c = begin; c <= end; c++) {
        int i;

        Cluster cluster = cluster_list[c];

        for (i = 0; i < cluster.count; i++) {
            int links = 0;
            int j;
            int patch_index = cluster.first_patch[i];

            for (j = 0; j < fragcount; j++) {
                if (adjacency_matrix[patch_index * fragcount + j]) {
                    links++;
                }
            }

            if (links < min_links) {
                min_links = links;
                min_index = i;

                if (cluster_index < 0) {
                    min_index = cluster.first_patch[min_index];
                }
            }
        }
    }

    return min_index;
}

int f_link_max(int cluster_index, Cluster *cluster_list, int cluster_count,
               int *adjacency_matrix, Patch *fragments, int fragcount,
               DCELL *distmatrix)
{
    int max_links = -1;
    int max_index = -1;

    int begin = cluster_index >= 0 ? cluster_index : 0;
    int end = cluster_index >= 0 ? cluster_index : cluster_count - 1;
    int c;

    for (c = begin; c <= end; c++) {
        int i;

        Cluster cluster = cluster_list[c];

        for (i = 0; i < cluster.count; i++) {
            int links = 0;
            int j;
            int patch_index = cluster.first_patch[i];

            for (j = 0; j < fragcount; j++) {
                if (adjacency_matrix[patch_index * fragcount + j]) {
                    links++;
                }
            }

            if (links > max_links) {
                max_links = links;
                max_index = i;

                if (cluster_index < 0) {
                    max_index = cluster.first_patch[max_index];
                }
            }
        }
    }

    return max_index;
}
