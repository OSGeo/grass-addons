/* MEM */
BOOL **garbage_init ( void );
void garbage_free ( BOOL **garbage );
void garbage_throw ( BOOL **garbage, int k, BOOL *item );
void garbage_print ( BOOL **garbage );
long garbage_size ( void );
