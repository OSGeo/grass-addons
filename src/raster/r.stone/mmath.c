/*
                Matrix geometry package.

                It (should) allow basic matrix manipulation and operations;
                it is based on 4 X 4 matrices to perform 3D geometric
                operations.
                                                                SEA - Florence,
   September 2000
*/

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include "mmath.h"

/*
        Function declarations
*/
static void push(MathContext *ctx, Mat a);
static Mat pop(MathContext *ctx);

/*
        Function definitions
*/
MathContext *init_mmath_system()
{
    MathContext *ctx = malloc(sizeof(MathContext));
    ctx->pstack = -1;

    push(ctx, ctx->m1);
    push(ctx, ctx->m2);
    push(ctx, ctx->m3);
    push(ctx, ctx->m4);
    push(ctx, ctx->m5);

    ctx->m = pop(ctx);

    mident(ctx->m);

    return ctx;
}

void push(MathContext *ctx, Mat a)
{
    ctx->stack[++(ctx->pstack)] = a;
}

Mat pop(MathContext *ctx)
{
    return ctx->stack[ctx->pstack--];
}

void mzero(Mat a)
{
    int i;

    for (i = 0; i < N; i++)
        *(a + i) = 0.0;
}

void mident(Mat a)
{
    int i;

    mzero(a);

    for (i = 0; i < R; i++)
        M(a, i, i) = 1.0;
}

void minit(MathContext *ctx)
{
    mident(ctx->m);
}

void vinit(MathContext *ctx)
{
    int i;

    for (i = 0; i < R; i++)
        *(ctx->v0 + i) = 0.0;

    ctx->v0[3] = 1.;
}

void mmul(MathContext *ctx, Mat a)
{
    int i, j, k;
    Mat t;

    t = pop(ctx);

    mzero(t);

    for (i = 0; i < R; i++)
        for (j = 0; j < R; j++)
            for (k = 0; k < R; k++)
                M(t, i, j) += M(ctx->m, i, k) * M(a, k, j);

    push(ctx, ctx->m);

    ctx->m = t;
}

void mprint(MathContext *ctx)
{
    int i, j;

    printf("------------------------------------------------\n");

    for (i = 0; i < R; i++) {
        for (j = 0; j < R; j++)
            printf("  %6.2lf", M(ctx->m, i, j));

        printf("\n\n");
    }

    printf("------------------------------------------------\n");
}

void pprint(P3d *p)
{
    printf("X:%11.5lf Y:%11.5lf Z:%11.5lf\n", p->X, p->Y, p->Z);
}

void mget(MathContext *ctx, Mat e)
{
    int i;

    for (i = 0; i < N; i++)
        *(e + i) = *(ctx->m + i);
}

void mput(MathContext *ctx, Mat e)
{
    int i;

    for (i = 0; i < N; i++)
        *(ctx->m + i) = *(e + i);
}

void translate(MathContext *ctx, double x, double y, double z)
{
    Mat t;

    t = pop(ctx);

    mident(t);

    M(t, 3, 0) = x;
    M(t, 3, 1) = y;
    M(t, 3, 2) = z;

    mmul(ctx, t);

    push(ctx, t);
}

void x_rotate(MathContext *ctx, double alfa)
{
    Mat t;
    double sa, ca;

    sa = sin(alfa);
    ca = cos(alfa);

    t = pop(ctx);

    mident(t);

    M(t, 1, 1) = ca;
    M(t, 1, 2) = sa;
    M(t, 2, 1) = -sa;
    M(t, 2, 2) = ca;

    mmul(ctx, t);

    push(ctx, t);
}

void y_rotate(MathContext *ctx, double alfa)
{
    Mat t;
    double sa, ca;

    sa = sin(alfa);
    ca = cos(alfa);

    t = pop(ctx);

    mident(t);

    M(t, 0, 0) = ca;
    M(t, 0, 2) = -sa;
    M(t, 2, 0) = sa;
    M(t, 2, 2) = ca;

    mmul(ctx, t);

    push(ctx, t);
}

void z_rotate(MathContext *ctx, double alfa)
{
    Mat t;
    double sa, ca;

    sa = sin(alfa);
    ca = cos(alfa);

    t = pop(ctx);

    mident(t);

    M(t, 0, 0) = ca;
    M(t, 0, 1) = sa;
    M(t, 1, 0) = -sa;
    M(t, 1, 1) = ca;

    mmul(ctx, t);

    push(ctx, t);
}

void vmmul(MathContext *ctx)
{
    int i, j;

    for (i = 0; i < R; i++) {
        *(ctx->v1 + i) = 0.0;

        for (j = 0; j < R; j++)
            *(ctx->v1 + i) += *(ctx->v0 + j) * M(ctx->m, j, i);
    }
}

void rt(MathContext *ctx, P3d *from, P3d *to)
{
    double m;

    *(ctx->v0 + 0) = from->X;
    *(ctx->v0 + 1) = from->Y;
    *(ctx->v0 + 2) = from->Z;
    *(ctx->v0 + 3) = 1.0;

    vmmul(ctx);

    m = 1 / *(ctx->v1 + 3);

    to->X = *(ctx->v1 + 0) * m;
    to->Y = *(ctx->v1 + 1) * m;
    to->Z = *(ctx->v1 + 2) * m;
}

void MulVectMat(P3d *from, Mat e, P3d *to)
{
    double x, y, z, m;
    double rx, ry, rz, rm;

    x = from->X;
    y = from->Y;
    z = from->Z;
    m = 1;

    rm = x * A(e, 3) + y * A(e, 7) + z * A(e, 11) + m * A(e, 15);

    rm = 1 / rm;

    rx = (x * A(e, 0) + y * A(e, 4) + z * A(e, 8) + m * A(e, 12)) * rm;
    ry = (x * A(e, 1) + y * A(e, 5) + z * A(e, 9) + m * A(e, 13)) * rm;
    rz = (x * A(e, 2) + y * A(e, 6) + z * A(e, 10) + m * A(e, 14)) * rm;

    to->X = rx;
    to->Y = ry;
    to->Z = rz;
}
