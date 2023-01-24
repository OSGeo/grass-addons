/* args.c */
void parse_args(int, char **, char **, char **, int *, int *, char **, char ***,
                int *);

/* body.c */
int write_ply_body_ascii(FILE *, struct Map_info *, int, int, int,
                         const char **, struct bound_box *);

/* header.c */
void write_ply_header(FILE *, const struct Map_info *, const char *,
                      const char *, const char **, int, int);
