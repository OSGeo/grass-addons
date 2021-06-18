xmlDocPtr stat_XML ( char *file, int *no_singletons, int *n );
char **get_groups_XML ( int n, xmlDocPtr doc );
Sfp_struct* test_rast_XML ( char **groups, xmlDocPtr doc );
char **get_hyp_names_XML ( int *no_all_hyps, xmlDocPtr doc );
Shypothesis *get_const_samples_XML ( char* group, int norm, BOOL **garbage, xmlDocPtr doc );
Shypothesis *get_rast_samples_XML ( char* group, int group_idx, int norm, Uint *nsets, BOOL **garbage, xmlDocPtr doc, Sfp_struct* file_pointers );
void close_rasters ( Sfp_struct* file_pointers );
