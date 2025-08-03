#ifndef mmath_h_200504101312
#define mmath_h_200504101312

typedef double *Mat;

typedef struct {
    double X, Y, Z;
} P3d;

#define R     4  /* dimensione vettori e righe/colonne matrici */
#define N     16 /* numero di celle matrici 4x4 */
#define SSIZE 10 /* dimensioni stack puntatori a matrici */

#define M(m, i, j)                            \
    *(m + i * R + j) /* cattura cella matrice \
                                tramite riga e colonna*/
#define A(m, i) (*(m + i))

typedef struct {
    double m1[N];
    double m2[N];
    double m3[N];
    double m4[N];
    double m5[N];
    double v0[R];
    double v1[R];
    Mat m;
    Mat stack[SSIZE];
    int pstack;
} MathContext;

MathContext *init_mmath_system();
void mzero(Mat a);
void mident(Mat a);
void minit(MathContext *ctx);
void vinit(MathContext *ctx);
void mmul(MathContext *ctx, Mat a);
void mget(MathContext *ctx, Mat e);
void mput(MathContext *ctx, Mat e);
void mprint(MathContext *ctx);
void pprint(P3d *p);
void translate(MathContext *ctx, double x, double y, double z);
void x_rotate(MathContext *ctx, double alfa);
void y_rotate(MathContext *ctx, double alfa);
void z_rotate(MathContext *ctx, double alfa);
void vmmul(MathContext *ctx);
void rt(MathContext *ctx, P3d *from, P3d *to);

void MulVectMat(P3d *from, Mat e, P3d *to);

#endif /* mmath_h_200504101312 */
