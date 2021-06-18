
/****************************************************************************
 *
 * MODULE:       r.roughset
 * AUTHOR(S):    GRASS module authors ad Rough Set Library (RSL) maintain:
 *			G.Massei (g_massa@libero.it)-A.Boggia (boggia@unipg.it)
 *			Rough Set Library (RSL) ver. 2 original develop:
 *		        M.Gawrys - J.Sienkiewicz
 *
 * PURPOSE:      Geographics rough set analisys and knowledge discovery
 *
 * COPYRIGHT:    (C) A.Boggia - G.Massei (2008)
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 ************************************************************************
** EXTRACT RULE FROM GEOGRAPHICS THEMES (Based on Rough Set Library
**     		written by M.Gawrys J.Sienkiewiczbrary )
**
** The RSL defines three types to be used in applications:
**     setA - set of attributes,
**     setO - set of objects and
**     SYSTEM - information system descriptor.

** The descriptor contains pointers to the information system data matrices:
** - MATRIX A, is the attribute-value table.
** - MATRIX D, is the discernibility matrix
** - MATRIX X, is called a reduced discernibility matrix.

***********************************************************************/

#include "rough.h"
#include "localproto.h"

int rough_analysis(int nrows, int ncols, char *name, int *classify_vect,
                   struct input *attributes, char *file_sample_txt, int strgy,
                   int cls);

void rough_set_library_out(int nrows, int ncols, int nattributes,
                           struct input *attributes, char *file_out_sys);

void output_to_txt(FILE * file_out_txt, value_type * rules, setA P, setA Q,
                   setA core, setA beg, int n, SYSTEM * sys1, int strgy,
                   int r, int *opr, struct input *attributes);

void fPrintSetA(FILE * file, setA set);
void fPrintSetO(FILE * file, setO set);
void fPrintRules(FILE * file, value_type * rules, int N, int *opr, setA P,
                 setA Q, struct input *attributes);

float MeanAttrInRule(value_type * rules, int N, setA P);

int LowRules(value_type ** rules, setA P, setA Q, int mat);
int UppRules(value_type ** rules, setA P, setA Q, int mat);
int NormRules(value_type ** rules, setA P, setA Q, int mat);


int rough_analysis(int nrows, int ncols, char *name, int *classify_vect,
                   struct input *attributes, char *file_sample_txt, int strgy,
                   int cls)
{
    SYSTEM *sys1, *sys2;	/* Information system descriptor structures. */

    /* It contains information about the system parameters (number of objects, number of attributes, system name. */
    value_type value, *buf, *rules;	/* stores a single value of attribute (used for attribute-value table and rule implementation) */
    char c;
    int n, j, i, r, *opr;
    setA beg, P, Q, full, core;	/*set of attributes */
    setO train;			/*set of object */
    FILE *file_out_txt;		/* pointer to text output file */
    int (*genrules) (value_type **, setA, setA, int);

    int nattributes, nobjects = nrows * ncols;	/*objects in information system are all raster cells in working location with a defined resolution */
    int row, col, object, attribute;	/*index and counter */

    sys1 = InitEmptySys();	/* Allocates memory for a system descriptor and returns a pointer. */

    if (file_sample_txt != NULL)  	/*use sample txt file if input in dec_txt->answer isn't NUL */
    {
        name = file_sample_txt;
        G_message("Using %s sys file for rules generation", name);
    }				/* Imports a system from a file of the special format. */


    FileToSys(sys1, name);	/* Imports a system from a file of the special format. */

    if (_rerror > 0)
    {
        G_fatal_error("  Can't open data file \n");
        return (1);
    }

    strcat(name, ".out");

    if (!(file_out_txt = fopen(name, "a")))  	/*output text file */
    {
        G_fatal_error("  Can't open output file \n");
        return (1);
    }

    UseSys(sys1);		/* Activates a system. All routines will work on this indicated system data and parameters. */

    if (_rerror > 0)
    {
        G_fatal_error("Can't open information system <%s>\n", sys1->name);
        return (1);
    }


    full = InitFullSetA();	/*Initialize a full set. Allocates memory for a set and initialize it with all elements of
				   domain based on the active information system */

    InitD(sys1);		/*Generates MATRIX D from MATRIX A.Connected to sys and filled */

    P = InitEmptySetA();	/* Initialize an empty set. Memory size determined by active information system parameters */
    Q = InitEmptySetA();

    nattributes = (AttributesNum(sys1) - 1);

    /* define attribute */
    for (i = 0; i < nattributes; i++)
    {
        AddSetA(P, i);		/* Adds a single element to a set */
    }

    /* define decision */
    AddSetA(Q, (AttributesNum(sys1) - 1));

    InitX(sys1, P, Q, MATD);	/*Generates MATRIX X from another matrix designed for use in core and reducts queries. */
    core = InitEmptySetA();
    Core(core, MATX);		/* Puts a core of the active information system to core. */

    RedOptim(core, MATX);	/* Provides the optimized heuristic search for a single reduct */

    CloseSetA(core);		/* Frees memory allocated for a set */
    n = RedFew(&beg, MATX);	/*Finds all reducts shorter than the first one found. */
    CloseMat(sys1, MATX);	/* Closes a matrix. */

    if (n > 0)
        free(beg);

    switch (strgy)
    {
    case 0:
        genrules = VeryFastRules;
        break;
    case 1:
        genrules = FastRules;
        break;
    case 2:
        genrules = Rules;
        break;
    case 3:
        genrules = BestRules;
        break;
    case 4:
        genrules = AllRules;
        break;
    case 5:
        genrules = LowRules;
        break;
    case 6:
        genrules = UppRules;
        break;
    default:
        genrules = NormRules;
        break;
    }

    r = genrules(&rules, P, Q, MATD);	/* rules generator */

    if (r > 0)
    {
        opr = StrengthOfRules(rules, r);
    }				/* Creates a table of rules strengths */


    /**************************Output text files************************************/

    /***********print output about sys1 in a txt file (file_out_txt)****************/
    output_to_txt(file_out_txt, rules, P, Q, core, beg, n, sys1, strgy, r,
                  opr, attributes);

    /**************************close all********************************************/

    //CloseSys(sys1);   /* close sys1 */

    /*******************************************************************************/

    /**************************Classify*********************************************/

    sys2 = InitEmptySys();
    SetParameters(sys2, nobjects, nattributes);	/* assigning system parameters */
    ConnectA(sys2, malloc(MatMemSize(sys2, MATA)));	/* Connects MATRIX A to a system descriptor. */
    /*MatMemSize: Returns size of memory used by matrix. */
    SetName(sys2, "classys");
    UseSys(sys2);		/* active system sys2 was created in application and has only MATRIX A */

    if (_rerror > 0)
    {
        G_fatal_error("Can't open information system <%s>\n", _mainsys->name);
        return (1);
    }

    G_message("Build information system for classification ");
    for (i = 0; i < nattributes; i++)
    {
        object = 0;		/* set object numbers =0 and increase it until rows*cells for each attribute */
        for (row = 0; row < nrows; row++)
        {
            G_percent(row, nrows, 1);
            /* Reads appropriate information into the buffer buf associated with the requested row */
            G_get_c_raster_row(attributes[i].fd, attributes[i].buf, row);
            for (col = 0; col < ncols; col++)
            {
                value = (attributes[i].buf[col]);	/*make a cast on the DCELL output value */
                PutA(_mainsys, object, i, value);	/* filling MATRIX A */
                object++;
            }
        }
    }

    buf = MatExist(_mainsys, MATA);	/*Returns pointer to specified matrix if exists */

    if (!buf)
    {
        G_fatal_error("Error in the information system <%s>\n",
                      _mainsys->name);
        return (1);
    }


    switch (cls)
    {
    case 0:
    {
        for (j = 0; j < _mainsys->objects_num; j++)  	/*Chooses the best rule to cover sample. Strategy no. 1 */
        {
            classify_vect[j] =
                Classify1(buf + j * _mainsys->attributes_num, rules, r, P,
                          Q);
            G_percent(j, _mainsys->objects_num, 1);
        }
    }
    break;
    case 1:
    {
        for (j = 0; j < _mainsys->objects_num; j++)  	/*Chooses the best rule to cover sample. Strategy no. 2 */
        {
            classify_vect[j] =
                Classify2(buf + j * _mainsys->attributes_num, rules, r, P,
                          Q);
            G_percent(j, _mainsys->objects_num, 1);
        }
    }
    break;
    case 2:
    {
        for (j = 0; j < _mainsys->objects_num; j++)  	/*Chooses the best rule to cover sample. Strategy no. 3 */
        {
            classify_vect[j] =
                Classify3(buf + j * _mainsys->attributes_num, rules, r,
                          opr, P, Q);
            G_percent(j, _mainsys->objects_num, 1);
        }
    }
    break;

    default:
        0;
        break;
    }


    G_message("All cells classified (%d)", j);

    /*****************************************************************************/

    free(rules);
    free(opr);
    CloseSetA(P);
    CloseSetA(Q);
    CloseSetA(full);
    CloseSys(sys2);
    //fclose(file);
    fclose(file_out_txt);
    return (0);
}

void rough_set_library_out(int nrows, int ncols, int nattribute,
                           struct input *attributes, char *file_out_sys)
{
    int row, col, i, j;
    int value, decvalue;
    int nobject;
    char cell_buf[300];
    FILE *fp;			/*file pointer for ASCII output */

    /* open *.sys file for writing or use stdout */
    if (NULL == (fp = fopen(file_out_sys, "w")))
        G_fatal_error("Not able to open file [%s]", file_out_sys);

    fprintf(fp, "NAME: %s\nATTRIBUTES: %d\nOBJECTS: %s\n", file_out_sys,
            nattribute + 1, "            ");

    /************** process the data *************/

    G_message("Build information system for rules extraction in %s",
              file_out_sys);

    nobject = 0;

    for (row = 0; row < nrows; row++)
    {
        for (i = 0; i <= nattribute; i++)
        {
            G_get_c_raster_row(attributes[i].fd, attributes[i].buf, row);	/* Reads appropriate information into the buffer buf associated with the requested row */
        }
        for (col = 0; col < ncols; col++)  	/*make a cast on the DCELL output value */
        {
            decvalue = (int)attributes[nattribute].buf[col];
            if (0 < decvalue)  	/* TODO: correct form will: decval!=null */
            {
                for (j = 0; j < nattribute; j++)  	/*make a cast on the DCELL output value */
                {
                    value = (int)(attributes[j].buf[col]);
                    sprintf(cell_buf, "%d", value);
                    G_trim_decimal(cell_buf);
                    fprintf(fp, "%s ", cell_buf);
                }
                fprintf(fp, "%d\n", decvalue);
                nobject++;
            }
        }
        G_percent(row, nrows, 1);
    }

    /************** write code file*************/

    for (i = 0; i <= nattribute; i++)
    {
        fprintf(fp, "\n%s", attributes[i].name);
    }

    /************** write header file*************/

    rewind(fp);			/*move file pointer to header file */
    /* TODO: make a system to  detect errors like: G_fatal_error("Not able to write file [%s]",file_out_sys); */

    fprintf(fp, "NAME: %s\nATTRIBUTES: %d\nOBJECTS: %d", file_out_sys,
            nattribute + 1, nobject);

    /************** close all and exit ***********/

    fclose(fp);
}


void output_to_txt(FILE * file_out_txt, value_type * rules, setA P, setA Q,
                   setA core, setA beg, int n, SYSTEM * sys1, int strgy,
                   int r, int *opr, struct input *attributes)
{
    int i;

    fprintf(file_out_txt, "Condition attributes are\n");
    fPrintSetA(file_out_txt, P);
    fprintf(file_out_txt, "\nDecision attributes are\n");
    fPrintSetA(file_out_txt, Q);
    fprintf(file_out_txt, "\nDependCoef = %f\n", DependCoef(P, Q, MATD));	/* Returns degree of dependency Q from P in the active information system. */
    fprintf(file_out_txt, "CORE = ");
    fPrintSetA(file_out_txt, core);
    fprintf(file_out_txt, "\nRedOptim = ");
    fPrintSetA(file_out_txt, core);
    fprintf(file_out_txt, "\nFew reducts ( %i ):\n", n);

    for (i = 0; i < n; i++)
    {
        fPrintSetA(file_out_txt, beg + i * sys1->setAsize);
        fprintf(file_out_txt, "\n");
    }

    fprintf(file_out_txt, "%d strategy of generating rules\n", strgy);

    if (r > 0)
    {
        fprintf(file_out_txt, "Rules ( %i )\n", r);
        fPrintRules(file_out_txt, rules, r, opr, P, Q, attributes);	/*print to file generated rules */
        fprintf(file_out_txt, "Mean number of attributes in rule = %.1f\n",
                MeanAttrInRule(rules, r, P));
    }
}




void fPrintSetA(FILE * f, setA set)
{
    int attr;

    fprintf(f, "{");
    for (attr = 0; attr < _mainsys->attributes_num; attr++)
        if (ContSetA(set, attr))
        {
            fprintf(f, " %d", attr);
            attr++;
            break;
        }
    for (; attr < _mainsys->attributes_num; attr++)
        if (ContSetA(set, attr))
            fprintf(f, ",%d", attr);
    fprintf(f, " }");
}

void fPrintSetO(FILE * f, setO set)
{
    int obj;

    fprintf(f, "{");
    for (obj = 0; obj < _mainsys->objects_num; obj++)
        if (ContSetO(set, obj))
        {
            fprintf(f, " %d", obj);
            obj++;
            break;
        }
    for (; obj < _mainsys->objects_num; obj++)
        if (ContSetO(set, obj))
            fprintf(f, ",%d", obj);
    fprintf(f, " }");
}

void fPrintRules(FILE * file, value_type * rules,
                 int N, int *opr, setA P, setA Q, struct input *attributes)
{
    int n, j;

    for (n = 0; n < N; n++)
    {
        for (j = 0; j < _mainsys->attributes_num; j++)
            if (ContSetA(P, j))
                if (rules[n * _mainsys->attributes_num + j] != MINUS)
                    fprintf(file, "%s=%d  ", attributes[j].name,
                            rules[n * _mainsys->attributes_num + j]);
        fprintf(file, " => ");
        for (j = 0; j < _mainsys->attributes_num; j++)
            if (ContSetA(Q, j))
                if ((rules + n * _mainsys->attributes_num)[j] != MINUS)
                    fprintf(file, "%s=%d  ", attributes[j].name,
                            (rules + n * _mainsys->attributes_num)[j]);
        fprintf(file, " ( %i objects )\n", opr[n]);
    }
    return;
}



float MeanAttrInRule(value_type * rules, int N, setA P)
{
    int counter = 0;
    int i, j;
    int size = _mainsys->attributes_num;

    for (i = 0; i < N; i++)
        for (j = 0; j < size; j++)
            if (ContSetA(P, j))
                if ((rules + i * size)[j] != MINUS)
                    counter++;
    return (float)counter / N;
}

int LowRules(value_type ** rules, setA P, setA Q, int mat)
{
    return ApprRules(rules, P, Q, LOWER, mat);
}

int UppRules(value_type ** rules, setA P, setA Q, int mat)
{
    return ApprRules(rules, P, Q, UPPER, mat);
}

int NormRules(value_type ** rules, setA P, setA Q, int mat)
{
    return ApprRules(rules, P, Q, NORMAL, mat);
}


/* dom 07 dic 2008 07:04:58 CET */
