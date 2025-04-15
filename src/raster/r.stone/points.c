#include <grass/gis.h>

#include "stone.h"
#include "utils.h"

/*
        Variabili globali
*/

static int Bounce(typeParams *rParams, runtimeParams *rtParams,
                  globalParams *gParams, UniSave *uniData, P3d *cp, P3d *v0);
static int Parab(typeParams *rParams, runtimeParams *rtParams,
                 globalParams *gParams, P3d *cp, P3d *v0);
static int Roll(typeParams *rParams, runtimeParams *rtParams,
                globalParams *gParams, UniSave *uniData, P3d *cp, P3d *v0);

void TrackPoints(typeParams *rParams, globalParams *gParams,
                 runtimeParams *rtParams, UniSave *uniData, MathContext *ctx)
{
    int i, fly, type;
    long piv;
    double vs, v0oriz, v0vert, teta, alfa;
    P3d v0, cp, cpp, lb, cp0;
    int count, index, stone_count;
    double slope, max_slope;
    int dir;
    double v_scalar, lbounce_scalar;
    int row, col;

    count = index = 0;

    rtParams->glConter2d = 0L;

    teta = 0.; /* Start direction orizontal */
               /* In future we can get it as a parameter, etc */

    v0oriz = rParams->v0 * cos(teta);
    v0vert = rParams->v0 * sin(teta);

    // print_long_matrix(rtParams->gplStartStop, gParams);

    long rowsCols = gParams->glRowsxCols;
    for (piv = 0; piv < rowsCols; ++piv) {
        G_percent(piv, rowsCols, 2);
        long ss = START_STOP(rtParams, piv);
        if (ss <= 0L)
            continue;

        G_debug(3, "%d) cell: %ld / %ld / %ld - run points: %d / %d", ++index,
                piv, ss, rowsCols, count, rtParams->giCountRuns);

        if (rParams->SwitchVelType == 1) {
            vs = START_VEL(rtParams, piv) * 0.001;

            if (vs <= rParams->min_v)
                continue;

            v0oriz = vs * cos(teta);
            v0vert = vs * sin(teta);
        }

        row = DEC_Y(gParams, piv);
        col = DEC_X(gParams, piv); /* row e col sono usate solo nel logfile
                                                 per indicare la posizione sulla
                                      matrice in righe e colonne */

        cp0.X = POS_X(gParams, piv);
        cp0.Y = POS_Y(gParams, piv);
        cp0.Z = QUOTA(rtParams, piv) * 0.001;

        /*	trova la direzione di massima pendenza fra la cella corrente
                e quelle che la circondano */
        max_slope = -100.;

        dir = 0;

        for (i = 0; i < 8; ++i) {
            if (i % 2)
                slope = (QUOTA(rtParams, piv) -
                         QUOTA(rtParams, piv + rtParams->gsKernel9[i])) *
                        gParams->gdInvCellSq20001;
            else
                slope = (QUOTA(rtParams, piv) -
                         QUOTA(rtParams, piv + rtParams->gsKernel9[i])) *
                        gParams->gdInvCell0001;

            if (slope > max_slope) {
                max_slope = slope;

                dir = i;
            }
        }

        G_debug(4, "Track: dir:%d max_slope:%lf slope:%lf", dir, max_slope,
                slope);

        for (stone_count = 1; stone_count <= START_STOP(rtParams, piv);
             ++stone_count) {
            ++rtParams->glIdMasso;

            ++count;

            G_debug(3, "Start point: %d %d; stone: %d", row, col, stone_count);

            if (NewPlane(rtParams, gParams, &cp0, ctx))
                break;

            lb = cp = cp0; /* Store bounce */

            rtParams->glLastPiv = 0; /* Used in MarkPath */

            rtParams->gpPathCur = rtParams->gpPathRoot; /* Reset track */

            fly = 1; /* We start with a gunshot */

            alfa = GetRandAngle(rParams, rtParams, gParams, uniData, dir);

            v0.X = v0oriz * cos(alfa);
            v0.Y = v0oriz * sin(alfa);
            v0.Z = v0vert;

            rtParams->giUstSlice = 0;

            /* Start! */

            long tmpIndex = -1;
            for (;;) {
                ++tmpIndex;
                if (fly) {
                    type = Parab(rParams, rtParams, gParams, &cp, &v0);

                    switch (type) {
                    case 0: /* Overflow */
                        // if (rParams.EnabledLogFile) fprintf(gFileLog,"Track
                        // overflow\n");
                        G_debug(3, "Track overflow");
                        break;

                    case 1: /* Path needs a new triangle */
                        if (NewPlane(rtParams, gParams, &cp, ctx)) {
                            WritePath(rtParams, rParams, gParams);
                            break;
                        }

                        continue;
                        break;

                    case 2: /* Bounce inside triangle */
                        /*
                                Check if last parab was short: switch to roll
                           mode
                        */
                        lbounce_scalar = P3dDist2(&cp, &lb);

                        G_debug(4, "(P) lbounce_scalar: %f\n", lbounce_scalar);

                        v_scalar = P3dDist2(&v0, rtParams->gP3dZero);

                        G_debug(4, "(P) v_scalar: %f\n", v_scalar);

                        WritePath(rtParams, rParams, gParams);

                        if (lbounce_scalar < rParams->short_bounce2 &&
                            v_scalar < rParams->fly_roll_thresh2) {
                            lbounce_scalar = sqrt(lbounce_scalar);
                            v_scalar = sqrt(v_scalar);

                            // if (rParams->EnabledLogFile)
                            // fprintf(gFileLog,"Track: Short bounce, switch to
                            // roll. bounce_len=%.2lf v=%.2lf\n",
                            // 		lbounce_scalar, v_scalar);
                            G_debug(3,
                                    "Track: Short bounce, switch to roll. "
                                    "bounce_len=%.2lf v=%.2lf",
                                    lbounce_scalar, v_scalar);
                            fly = 0;

                            rtParams->gpPathCur = rtParams->gpPathRoot;
                            continue;
                        }

                        if (!Bounce(rParams, rtParams, gParams, uniData, &cp,
                                    &v0)) /* Stone bounces */
                        {
                            break; /* Stopped (v < min) */
                        }

                        lb = cp; /* Store bounce */

                        rtParams->gpPathCur = rtParams->gpPathRoot;
                        continue;
                        break;

                    case 3: /* Stone reached and end cell */
                        // if (rParams->EnabledLogFile) fprintf(gFileLog,"Stop
                        // cell reached.\n");
                        G_debug(3, "Stop cell reached.");
                        WritePath(rtParams, rParams, gParams);
                        break;

                    case 4: /* Special: We need an initial bounce */
                        if (!Bounce(rParams, rtParams, gParams, uniData, &cp,
                                    &v0)) /* Stone bounces */
                            break;

                        rtParams->gpPathCur = rtParams->gpPathRoot;
                        continue;
                        break;
                    }
                }
                else {
                    type = Roll(rParams, rtParams, gParams, uniData, &cp, &v0);

                    switch (type) {
                    case 0: /* Overflow */
                        G_debug(3, "Track overflow");
                        break;

                    case 1: /* We need a new triangle */
                        if (NewPlane(rtParams, gParams, &cp, ctx)) {
                            WritePath(rtParams, rParams, gParams);
                            break;
                        }

                        MulVectMat(&cp, rtParams->gPlane.toPlane, &cpp);

                        G_debug(4, "Track: DZ:%lf", cpp.Z);

                        /*
                                If point is elevated for new triangle
                                switch to fly
                        */
                        if (cpp.Z > 0.01) {
                            WritePath(rtParams, rParams, gParams);
                            rtParams->gpPathCur = rtParams->gpPathRoot;
                            fly = 1;
                        }
                        continue;
                        break;

                    case 2:
                        // if (rParams->EnabledLogFile) fprintf(gFileLog,"Roll:
                        // Velocity under threshold. Stopped.\n");
                        G_debug(3, "Roll: Velocity under threshold. Stopped.");
                        WritePath(rtParams, rParams, gParams);
                        break;

                    case 3:
                        // if (rParams->EnabledLogFile) fprintf(gFileLog,"Stop
                        // cell reached.\n");
                        G_debug(3, "Stop cell reached.");
                        WritePath(rtParams, rParams, gParams);
                        break;
                    }
                }

                // if (rParams->EnabledLogFile) fprintf(gFileLog,"End of
                // path\n");
                G_debug(3, "End of path");

                break;

            } /* End of infinite loop */

        } /* End of stone_count loop */

    } /* End of piv loop */
}

static int Bounce(typeParams *rParams, runtimeParams *rtParams,
                  globalParams *gParams, UniSave *uniData, P3d *cp, P3d *v0)
{
    P3d v0p;
    double v2;
    long piv;
    double v_el, h_el;

    MulVectMat(v0, rtParams->gPlane.rToPlane, &v0p);

    WriteP3dToLog("Bounce: V0 ", v0);
    WriteP3dToLog("Bounce: V0p ", &v0p);

    piv = Pivot(gParams, cp->X, cp->Y);

    /*
            Special Case: If ELAS is zero stop stone (as it was fallen into
       water)
    */
    if (V_ELAS(rtParams, piv) == 0) {
        // if (rParams.EnabledLogFile) fprintf(gFileLog,"Bounce: Stone was
        // fallen into water. Stopped.\n");
        G_debug(3, "Stone has fallen into water. Stopped.");
        return 0;
    }

    v_el = GetRandVElas(rParams, rtParams, gParams, uniData, piv);
    h_el = GetRandHElas(rParams, rtParams, gParams, uniData, piv);

    v0p.Z *= -v_el;
    v0p.X *= h_el;
    v0p.Y *= h_el;

    MulVectMat(&v0p, rtParams->gPlane.rFromPlane, v0);

    WriteP3dToLog("Bounce: V1 ", v0);
    WriteP3dToLog("Bounce: V1p ", &v0p);

    v2 = v0p.X * v0p.X + v0p.Y * v0p.Y + v0p.Z * v0p.Z;

    if (v2 < rParams->min_v2) {
        // if (runParams->EnabledLogFile) fprintf(gFileLog,"Bounce: Velocity
        // under threshold. Stopped\n");
        G_debug(3, "Bounce: Velocity under threshold. Stopped");
        return 0;
    }

    return 1;
}

static int Parab(typeParams *runParams, runtimeParams *rtParams,
                 globalParams *gParams, P3d *cp, P3d *v0)
{
    P3d v0p, cpp, ga, gp, *pp, *pv, cppt, v0pt;
    double sq, vs, t, t2, t1, st;
    double my;
    int bounce, inside, out_flag, out_count;
    long piv;
    double ca, inv_ca;

    MulVectMat(v0, rtParams->gPlane.rToPlane, &v0p);

    ga.X = 0.;
    ga.Y = 0.;
    ga.Z = -G;

    MulVectMat(&ga, rtParams->gPlane.rToPlane, &gp);

    MulVectMat(cp, rtParams->gPlane.toPlane, &cpp);

    ca = -gp.Z * INV_G;

    if (ca == 0.)
        ca = -1.;

    inv_ca = 1 / ca;

    WriteP3dToLog("Parab: cp", cp);
    WriteP3dToLog("Parab: cpp", &cpp);
    WriteP3dToLog("Parab: V0", v0);
    WriteP3dToLog("Parab: V0P", &v0p);

    inside = 1;

    for (;;) {
        sq = (v0p.Z * v0p.Z - 2 * gp.Z * cpp.Z);

        if (sq < 0.) {
            /*
                    This shouldn't happen. But sometimes switching from
                    triangle to triangle cp may be UNDER the new plane.
            */
            G_debug(4, "parabola: sq < 0");
            cpp.Z = 0;

            sq = (v0p.Z < 0 ? -v0p.Z : v0p.Z);
        }
        else {
            sq = sqrt(sq);
        }

        t2 = (-v0p.Z - sq) / gp.Z;
        t1 = (-v0p.Z + sq) / gp.Z;

        if (t2 <= 0.) {
            G_debug(4, "Parab: t2 < 0: Try a back step.");
            G_debug(4, "Parab: t2:%.6lf t1:%.6lf", t2, t1);

            if (rtParams->gpPathCur - rtParams->gpPathRoot < 2) {
                // if (rParams.EnabledLogFile) fprintf(gFileLog,"Parab: Back
                // step impossible. Bounce forced.\n");
                G_debug(3, "Back step impossible. Bounce forced.");
                return 4;
            }

            --rtParams->gpPathCur;

            *cp = (rtParams->gpPathCur - 1)->pos;

            *v0 = (rtParams->gpPathCur - 1)->v;

            MulVectMat(cp, rtParams->gPlane.toPlane, &cpp);

            MulVectMat(v0, rtParams->gPlane.rToPlane, &v0p);

            WriteP3dToLog("Parab: cp", cp);
            WriteP3dToLog("Parab: cpp", &cpp);
            WriteP3dToLog("Parab: V0", v0);
            WriteP3dToLog("Parab: V0P", &v0p);

            inside = 0;
        }
        else
            break;
    }

    G_debug(4, "parabola: Z0: %8.2lf\n", t2);

    if (t2 > 100.) {
        // if (rParams.EnabledLogFile) fprintf(gFileLog,"Warning time to
        // intercept too long. Set to 100.\n");
        G_debug(3, "Warning time to intercept too long. Set to 100.");
        t2 = 100.;
    }

    vs = sqrt(v0p.X * v0p.X + v0p.Y * v0p.Y + v0p.Z * v0p.Z);

    st = runParams->fly_step / vs;

    G_debug(4, "Parab: step: %6.4lf\n", st);

    bounce = 0;

    out_count = 0;

    t = 0.;

    for (;;) {
        cppt.X = cpp.X + v0p.X * t + gp.X * t * t * 0.5;
        cppt.Y = cpp.Y + v0p.Y * t + gp.Y * t * t * 0.5;
        cppt.Z = cpp.Z + v0p.Z * t + gp.Z * t * t * 0.5;

        v0pt.X = v0p.X + gp.X * t;
        v0pt.Y = v0p.Y + gp.Y * t;
        v0pt.Z = v0p.Z + gp.Z * t;

        if (rtParams->gpPathCur - rtParams->gpPathRoot >= runParams->max_path)
            return 0; /* Track overflow */

        pp = &rtParams->gpPathCur->pos;

        pv = &rtParams->gpPathCur->v;

        MulVectMat(&cppt, rtParams->gPlane.fromPlane, pp);

        RoundP3d(pp);

        MulVectMat(&v0pt, rtParams->gPlane.rFromPlane, pv);

        rtParams->gpPathCur->dz = cppt.Z * inv_ca;

        rtParams->gpPathCur->deleted = 0;

        ++rtParams->gpPathCur;

        /*
                Check current point for end cell
        */
        piv = Pivot(gParams, pp->X, pp->Y);

        if (START_STOP(rtParams, piv) == STOP_CELL) {
            return 3;
        }

        /*
                Check current point against triangle boundaries
        */
        out_flag = 0;

        if (rtParams->gPlane.type == 1) {
            my = rtParams->gPlane.p2.Y - (pp->X - rtParams->gPlane.p0.X);

            if (pp->X < rtParams->gPlane.p0.X ||
                pp->Y < rtParams->gPlane.p0.Y || pp->Y > my)
                out_flag = 1;
        }
        else /* Type 2 */
        {
            my = rtParams->gPlane.p2.Y + (rtParams->gPlane.p0.X - pp->X);

            if (pp->X > rtParams->gPlane.p0.X ||
                pp->Y > rtParams->gPlane.p0.Y || pp->Y < my)
                out_flag = 1;
        }

        /*
                Checks about to finish the loop
        */
        if (inside) /* We are into the current plane */
        {
            if (out_flag) {
                bounce = 0;
                break; /* Transition: inside -> outside */
            }
            else if (bounce) /* Inside; bounced */
                break;
        }
        else /* We did a backstep so far */
        {
            if (!out_flag) {

                WriteP3dToLog("Parab: Inside now.", pp);
                inside = 1; /* Transition: outside -> inside */
            }
            else {
                if (++out_count > 5) {
                    G_debug(4, "Parab: Confused... Aborted.");
                    return 0;
                }
                else {
                    WriteP3dToLog("Parab: Still outside.", pp);
                }
            }
        }

        /*
                Re-evaluate step to avoid to cross triangle boundaries
                with a raw tabulation -- too deep into next triangle.
        */
        vs = sqrt(pv->X * pv->X + pv->Y * pv->Y + pv->Z * pv->Z);

        st = runParams->fly_step / vs;

        /*
                The following few lines to force last iteration
                at the intersection with triangle
        */
        t += st;

        if (t >= t2) {
            t = t2;
            bounce = 1;
        }
    }

    /*
            Return last velocity and position
    */
    G_debug(4, "Parab: 2, saved points=%ld",
            rtParams->gpPathCur - rtParams->gpPathRoot);
    WriteP3dToLog("Parab: pp: ", pp);

    *cp = *pp;
    *v0 = *pv;

    if (bounce)
        return 2;
    else
        return 1;
}

static int Roll(typeParams *rParams, runtimeParams *rtParams,
                globalParams *gParams, UniSave *uniData, P3d *cp, P3d *v0)
{
    P3d v0p, cpp, ga, gp, *pp, *pv;
    double st, vs, t;
    double my;
    long piv, lpiv;
    double fc, f = 0, alfa, beta, dx, dy;

    MulVectMat(v0, rtParams->gPlane.rToPlane, &v0p);

    WriteP3dToLog("Roll: cp ", cp);
    WriteP3dToLog("Roll: V0 ", v0);
    WriteP3dToLog("Roll: V0P ", &v0p);

    v0p.Z = 0.;

    ga.X = 0.;
    ga.Y = 0.;
    ga.Z = -G;

    MulVectMat(&ga, rtParams->gPlane.rToPlane, &gp);

    MulVectMat(cp, rtParams->gPlane.toPlane, &cpp);

    vs = sqrt(v0p.X * v0p.X + v0p.Y * v0p.Y);

    st = rParams->roll_step / vs;

    G_debug(4, "Roll: step: %6.4lf", st);

    /*mput(gPlane.fromPlane);*/

    cpp.Z = 0.;

    lpiv = 0;

    t = 0.;

    pp = &rtParams->gpPathCur->pos;

    *pp = *cp;

    for (;;) {
        piv = Pivot(gParams, pp->X, pp->Y);
        if (piv != lpiv) /* Take last friction if piv is not changed */
        {
            fc = GetRandFrict(rParams, rtParams, gParams, uniData, piv);

            beta = atan(fc);

            f = sin(beta) * G;

            G_debug(4, "Roll: f: %6.4lf", f);
            lpiv = piv;
        }

        /*
                Evaluate dx and dy: these are directions of friction along axes
        */
        if (v0p.X != 0.) {
            alfa = atan(v0p.Y / v0p.X);

            if (alfa < 0.)
                alfa *= -1.;

            dx = cos(alfa);

            if (v0p.X < 0.)
                dx *= -1.;

            dy = sin(alfa);

            if (v0p.Y < 0.)
                dy *= -1.;
        }
        else {
            dx = 0.;

            if (v0p.Y > 0.)
                dy = 1.;
            else
                dy = -1.;
        }

        /*
                Avoid friction to act as a spring; Evaluate time step
                to intercept velocity = 0
        */
        vs = sqrt(v0p.X * v0p.X + v0p.Y * v0p.Y);

        if (vs < f * t) {
            t = vs / f;

            // if (runParams.EnabledLogFile) fprintf(gFileLog, "Roll: Stop
            // between two steps. t=%lf\n", t);
            G_debug(3, "Roll: Stop between two steps. t=%lf", t);
        }
        /*
                New point and velocity
        */
        cpp.X = cpp.X + v0p.X * t + (gp.X - dx * f) * t * t * 0.5;
        cpp.Y = cpp.Y + v0p.Y * t + (gp.Y - dy * f) * t * t * 0.5;

        v0p.X += (gp.X - dx * f) * t;
        v0p.Y += (gp.Y - dy * f) * t;

        if (rtParams->gpPathCur - rtParams->gpPathRoot >= rParams->max_path)
            return 0; /* Track overflow */

        pp = &rtParams->gpPathCur->pos;
        pv = &rtParams->gpPathCur->v;

        MulVectMat(&cpp, rtParams->gPlane.fromPlane, pp);

        RoundP3d(pp);

        MulVectMat(&v0p, rtParams->gPlane.rFromPlane, pv);

        rtParams->gpPathCur->dz = cpp.Z;

        rtParams->gpPathCur->deleted = 0;

        ++rtParams->gpPathCur;

        /*
                Re-evaluate step from last velocity
        */
        vs = sqrt(v0p.X * v0p.X + v0p.Y * v0p.Y);

        st = rParams->roll_step / vs;

        t = st;

        /*
                Check if velocity is under threshold
        */
        if (vs < rParams->min_v) {
            return 2;
        }

        /*
                Check current point for end cell
        */
        if (START_STOP(rtParams, piv) == STOP_CELL) {
            G_debug(4, "Roll: 0, saved points=%ld\n",
                    rtParams->gpPathCur - rtParams->gpPathRoot);
            return 3;
        }

        /*
                Check current point against triangle boundaries
        */
        if (rtParams->gPlane.type == 1) {
            my = rtParams->gPlane.p2.Y - (pp->X - rtParams->gPlane.p0.X);

            if (pp->X < rtParams->gPlane.p0.X ||
                pp->Y < rtParams->gPlane.p0.Y) {
                break;
            }
            if (pp->Y > my) {
                break;
            }
        }
        else /* Type 2 */
        {
            my = rtParams->gPlane.p2.Y + (rtParams->gPlane.p0.X - pp->X);

            if (pp->X > rtParams->gPlane.p0.X ||
                pp->Y > rtParams->gPlane.p0.Y) {
                break;
            }
            if (pp->Y < my) {
                break;
            }
        }
    }

    /*
            Return last velocity
    */
    MulVectMat(&v0p, rtParams->gPlane.rFromPlane, v0);

    G_debug(4, "Roll: 2, saved points=%ld",
            rtParams->gpPathCur - rtParams->gpPathRoot);

    *cp = *pp;

    return 1;
}
