struct rb {
    int fd;      /* File Descriptor */
    int bw;      /* bandwidth */
    int nsize;   /* bw * 2 + 1 */
    int row;     /* next row to read */
    DCELL **buf; /* for reading raster map */
};

int allocate_bufs(struct rb *rbuf, int ncols, int bw, int fd);
int release_bufs(struct rb *rbuf);
int readrast(struct rb *rbuf, int nrows, int ncols);
