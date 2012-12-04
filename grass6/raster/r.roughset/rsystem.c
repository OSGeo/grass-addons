/****************************************************************************
 *
 * MODULE:       r.roughset
 * AUTHOR(S):    GRASS module authors and Rough Set Library (RSL) maintain:
 *					G.Massei (g_massa@libero.it)-A.Boggia (boggia@unipg.it)
 *				 Rough Set Library (RSL) ver. 2 original develop:
 *		         	M.Gawrys - J.Sienkiewicz
 *
 * PURPOSE:      Geographics rough set analisys and knowledge discovery
 *
 * COPYRIGHT:    (C) A.Boggia - G.Massei (2008)
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/
/***                                                                       ***/
/***                SYSTEM HANDLING FUNCTIONS                              ***/
/***                                                                       ***/
/***  part of the RSL system written by M.Gawrys J.Sienkiewicz             ***/
/***                                                                       ***/
/*****************************************************************************/

#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#include "rough.h"

SYSTEM  *_mainsys=NULL;
int      _rerror=0;

SYSTEM  *InitEmptySys(void)
{
    SYSTEM *sys;
    int i;
    cluster_type mask=1;
    if ((sys=(SYSTEM *)malloc(sizeof(SYSTEM)))==NULL)
    {
        _rerror=3;
        return NULL;
    }
    for (i=0; i<_cluster_bits; i++)
    {
        _mask[i]=mask;
        mask <<= 1;
    }
    sys->attributes_num=0;
    sys->objects_num=0;
    sys->description=NULL;
    sys->descr_size=0;
    sys->setAsize=0;
    sys->setOsize=0;
    sys->matA=NULL;
    sys->matD=NULL;
    sys->matX=NULL;
    sys->matXsize=0;
    return sys;
}

void SetParameters(SYSTEM *sys,int obj_num,int attr_num)
{
    sys->attributes_num=attr_num;
    sys->objects_num=obj_num;
    sys->setAsize=1+(attr_num-1)/_cluster_bits;
    sys->setOsize=1+(obj_num-1)/_cluster_bits;
}

void ConnectDescr(SYSTEM *sys,void *descr,int size)
{
    sys->description=descr;
    sys->descr_size=size;
}

void SetName(SYSTEM *sys,char *name)
{
    strncpy(sys->name,name,50);
}

int FileToSys(SYSTEM *sys,char *filename)
{
    FILE *source;
    value_type *buf;
    int descr_size,matAsize;
    long len1,len2;
    char string[50];
    int c,n=0;
    if (sys->matA!=NULL)
    {
        free(sys->matA);
        sys->matA=NULL;
    }
    if (sys->matD!=NULL)
    {
        free(sys->matD);
        sys->matD=NULL;
    }
    if (sys->matX!=NULL)
    {
        free(sys->matX);
        sys->matX=NULL;
    }
    if (sys->description!=NULL)
    {
        free(sys->description);
        sys->description=NULL;
    }
    if ((source=fopen(filename,"r"))==NULL)
        ERROR(1)
        if (!fscanf(source,"NAME%c",string))
            ERROR(2)
            if (string[0]!=':') ERROR(2)
                if (!fgets(sys->name,48,source))
                    ERROR(2)
                    if (sys->name[strlen(sys->name)-1]=='\n')
                        sys->name[strlen(sys->name)-1]='\0';
                    else
                        while (fgetc(source)!='\n' && !feof(source));
    if (!fscanf(source,"ATTRIBUTES:%i\n",&(sys->attributes_num)))
        ERROR(2)
        if (!fscanf(source,"OBJECTS:%i\n",&(sys->objects_num)))
            ERROR(2)
            sys->setAsize=1+(sys->attributes_num-1)/_cluster_bits;
    sys->setOsize=1+(sys->objects_num-1)/_cluster_bits;
    matAsize=(sys->objects_num)*(sys->attributes_num);
    if ((buf=(value_type*)(setA)malloc(sizeof(value_type)*matAsize))==NULL)
        ERROR(3)
        while (!feof(source) && n<matAsize)
            if (fscanf(source,"%s",string)==NULL)
                ERROR(2)
                else if (string[0]=='?' || string[0]=='*')
                    buf[n++]=(value_type)-1;
                else if (sscanf(string,"%d",&c)==NULL)
                    ERROR(2)
                    else buf[n++]=(value_type)c;
    sys->matA=buf;
    while (isspace(fgetc(source)));
    if (!feof(source))
    {
        len1=ftell(source)-1;
        fseek(source,0l,SEEK_END);
        len2=ftell(source);
        fseek(source,len1,SEEK_SET);
        descr_size=(int)(len2-len1);
        buf=(value_type *)(setA)malloc(descr_size);
        fread(buf,sizeof(char),descr_size,source);
        sys->description=buf;
        sys->descr_size=descr_size;
    }
    fclose(source);
    return 1;
}

void ConnectA(SYSTEM *sys,value_type *buf)
{
    sys->matA=buf;
}

void PutA(SYSTEM *sys,int obj,int atr,value_type val)
{
    (sys->matA)[obj*(sys->attributes_num)+atr]=val;
}

int FillAfromAscii(SYSTEM *sys,FILE *file)
{
    int k=0,j;
    while (!feof(file)&&(k<Asize(sys)))
    {
        if (fscanf(file,"%d",&j)==NULL) ERROR(2);
        *(sys->matA+k++)=j;
    }
    return 0;
}

int InitD(SYSTEM *sys)
{
    cluster_type *buf;
    int nby=(sys->attributes_num)/_cluster_bits; /* number of full clusters in element of tableD */
    int nbi=sys->attributes_num%_cluster_bits;   /* number of bits in the last cluster */
    int atrnum=sys->attributes_num;  		/* number of attributes */
    int row,column,cluster,bit;
    value_type *A=sys->matA;
    cluster_type val,*ptr;
    if (A==NULL)
        ERROR(5);
    if ((buf=(setA)malloc(MatMemSize(sys,MATD)))==NULL)
        ERROR(3);
    ptr=buf;
    for (row=1;row<sys->objects_num;row++)
        for (column=0;column<row;column++)
        {
            for (cluster=0;cluster<nby;cluster++)
            {
                val=0;
                for (bit=0;bit<_cluster_bits;bit++)
                    if (A[row*atrnum+_cluster_bits*cluster+bit]!=A[column*atrnum+_cluster_bits*cluster+bit] &&
                            A[row*atrnum+_cluster_bits*cluster+bit]!=(value_type)-1  &&
                            A[column*atrnum+_cluster_bits*cluster+bit]!=(value_type)-1  )
                        val=val|_mask[bit];
                *ptr=val;
                ptr++;
            }
            if (nbi)
            {
                val=0;
                for (bit=0;bit<nbi;bit++)
                    if (A[row*atrnum+_cluster_bits*cluster+bit]!=A[column*atrnum+_cluster_bits*cluster+bit] &&
                            A[row*atrnum+_cluster_bits*cluster+bit]!=(value_type)-1  &&
                            A[column*atrnum+_cluster_bits*cluster+bit]!=(value_type)-1  )
                        val=val|_mask[bit];
                *ptr=val;
                ptr++;
            }
        }
    sys->matD=buf;
    return MatMemSize(sys,MATD);
}

int InitX(SYSTEM* sys,setA P,setA Q,int matrix_type)
{
    setA head,tail,el,el1;
    int  memo=1,count=0,no,dif,size,MEMOKWANT=Asize(_mainsys);
    size=_mainsys->setAsize;
    if ((head=(setA)malloc(MEMOKWANT))==NULL) ERROR(3);
    tail=head;
    el=InitEmptySetA();
    for (start_of_tab(matrix_type);end_of_tab();next_of_tab())
    {
        if ( !InterSetA(_table_element,Q) ) continue;
        AndSetA(el,P,_table_element);
        if ( IsEmptySetA(el) ) continue;
        no=0;
        dif=0;
        for (el1=head;el1<tail;el1+=size)
            if (InSetA(el,el1))
            {
                no=1;
                break;
            }
            else
            {
                if (InSetA(el1,el))  dif+=size,count--;
                else if (dif) CopySetA(el1-dif,el1);
            }
        if (!no)
        {
            if ((memo*MEMOKWANT)<((count+1)*size*_cluster_bytes))
                if ((head=(setA)realloc(head,++memo*MEMOKWANT))==NULL)
                {
                    CloseSetA(el);
                    ERROR(3);
                }
            CopySetA(head+count*size,el);
            count++;
            tail=head+count*size;
        }
    }
    CloseSetA(el);
    if ((head=(setA)realloc(head,count*size*_cluster_bytes))==NULL) ERROR(3);
    sys->matX=head;
    sys->matXsize=count*size;
    return(count);
}

int InitXforObject(SYSTEM* sys,int obj,setA P,setA Q,int matrix_type)
{
    setA head,tail,el,el1;
    int  memo=1,count=0,no,dif,MEMOKWANT=Asize(_mainsys);
    int size=_mainsys->setAsize;
    int obj2;
    if ((head=(setA)malloc(MEMOKWANT))==NULL)
        ERROR(3);
    tail=head;
    el=InitEmptySetA();
    for (obj2=0; obj2<_mainsys->objects_num; obj2++)
    {
        if ( obj==obj2 ) continue;
        if ( matrix_type==MATA ) GetDfromA( el, obj, obj2 );
        else
        {
            _table_element=GetD( obj, obj2 );
            CopySetA( el, _table_element );
        }
        if ( !InterSetA(el,Q) ) continue;
        AndSetA(el,P,el);
        if ( IsEmptySetA(el) ) continue;
        no=0;
        dif=0;
        for (el1=head;el1<tail;el1+=size)
            if (InSetA(el,el1))
            {
                no=1;
                break;
            }
            else
            {
                if (InSetA(el1,el))  dif+=size,count--;
                else if (dif) CopySetA(el1-dif,el1);
            }
        if (!no)
        {
            if ((memo*MEMOKWANT)<((count+1)*size*_cluster_bytes))
                if ((head=(setA)realloc(head,++memo*MEMOKWANT))==NULL)
                {
                    CloseSetA(el);
                    ERROR(3);
                }
            CopySetA(head+count*size,el);
            count++;
            tail=head+count*size;
        }
    }
    CloseSetA(el);
    if ((head=(setA)realloc(head,count*size*_cluster_bytes))==NULL)
        if (count>0) ERROR(3);
    sys->matX=head;
    sys->matXsize=count*size;
    return(count);
}

int InitXforObjects(SYSTEM* sys,setO objects,setA P,setA Q,int matrix_type)
{
    setA head,tail,el,el1;
    int  memo=1,count=0,no,dif,size,MEMOKWANT=Asize(_mainsys);
    size=_mainsys->setAsize;
    if ((head=(setA)malloc(MEMOKWANT))==NULL) ERROR(3);
    tail=head;
    el=InitEmptySetA();
    for (start_of_tab(matrix_type);end_of_tab();next_of_tab())
    {
        if ( !ContSetO(objects,_table_row) &&
                !ContSetO(objects,_table_column) ) continue;
        if ( !InterSetA(_table_element,Q) ) continue;
        AndSetA(el,P,_table_element);
        if ( IsEmptySetA(el) ) continue;
        no=0;
        dif=0;
        for (el1=head;el1<tail;el1+=size)
            if (InSetA(el,el1))
            {
                no=1;
                break;
            }
            else
            {
                if (InSetA(el1,el))  dif+=size,count--;
                else if (dif) CopySetA(el1-dif,el1);
            }
        if (!no)
        {
            if ((memo*MEMOKWANT)<((count+1)*size*_cluster_bytes))
                if ((head=(setA)realloc(head,++memo*MEMOKWANT))==NULL)
                {
                    CloseSetA(el);
                    ERROR(3);
                }
            CopySetA(head+count*size,el);
            count++;
            tail=head+count*size;
        }
    }
    CloseSetA(el);
    if ((head=(setA)realloc(head,count*size*_cluster_bytes))==NULL) ERROR(3);
    sys->matX=head;
    sys->matXsize=count*size;
    return(count);
}

int InitXforObjectFromClass(SYSTEM* sys,int obj,setA P,setO aclass,int matrix_type)
{
    setA head,tail,el,el1;
    int  memo=1,count=0,no,dif,MEMOKWANT=Asize(_mainsys);
    int size=_mainsys->setAsize;
    int obj2;
    if ((head=(setA)malloc(MEMOKWANT))==NULL) ERROR(3);
    tail=head;
    el=InitEmptySetA();
    for (obj2=0; obj2<_mainsys->objects_num; obj2++)
    {
        if ( ContSetO( aclass, obj2 ) ) continue;
        if ( matrix_type==MATA ) GetDfromA( el, obj, obj2 );
        else
        {
            _table_element=GetD( obj, obj2 );
            CopySetA( el, _table_element );
        }
        AndSetA(el,P,el);
        if ( IsEmptySetA(el) ) continue;
        no=0;
        dif=0;
        for (el1=head;el1<tail;el1+=size)
            if (InSetA(el,el1))
            {
                no=1;
                break;
            }
            else
            {
                if (InSetA(el1,el))  dif+=size,count--;
                else if (dif) CopySetA(el1-dif,el1);
            }
        if (!no)
        {
            if ((memo*MEMOKWANT)<((count+1)*size*_cluster_bytes))
                if ((head=(setA)realloc(head,++memo*MEMOKWANT))==NULL)
                {
                    CloseSetA(el);
                    ERROR(3);
                }
            CopySetA(head+count*size,el);
            count++;
            tail=head+count*size;
        }
    }
    CloseSetA(el);
    if ((head=(setA)realloc(head,count*size*_cluster_bytes))==NULL) ERROR(3);
    sys->matX=head;
    sys->matXsize=count*size;
    return(count);
}



void UseSys(SYSTEM *sys)
{
    _mainsys=sys;
}

int SysToFile(SYSTEM *sys,char *filename)
{
    FILE *output;
    int attr,obj;
    if ((output=fopen(filename,"wb"))==NULL)
        ERROR(1)
        if (!fprintf(output,"NAME: %s\n",sys->name))
            ERROR(4)
            if (!fprintf(output,"ATTRIBUTES: %i\n",sys->attributes_num))
                ERROR(4);
    if (!fprintf(output,"OBJECTS: %i\n\n",sys->objects_num))
        ERROR(4);
    for (obj=0;obj<sys->objects_num;obj++)
    {
        for (attr=0;attr<sys->attributes_num;attr++)
            if (sys->matA[obj*sys->attributes_num+attr]==(value_type)-1 )
            {
                if (!fprintf(output,"%c ",'?'))
                    ERROR(4)
                }
            else if (!fprintf(output,"%i ",sys->matA[obj*sys->attributes_num+attr]))
                ERROR(4)
                fprintf(output,"\n");
    }
    if (sys->descr_size!=0)
    {
        fprintf(output,"\n");
        fwrite(sys->description,sizeof(char),sys->descr_size,output);
    }
    fclose(output);
    return 1;
}

void CloseSys(SYSTEM *sys)
{
    if (sys->matA) free(sys->matA);
    if (sys->matD) free(sys->matD);
    if (sys->matX) free(sys->matX);
    if (sys->description) free(sys->description);
    free(sys);
}

void CloseMat(SYSTEM *sys, int matrix_type)
{
    switch (matrix_type)
    {
    case (MATA): if (sys->matA) free(sys->matA);
        sys->matA=NULL;
        return;
    case (MATD): if (sys->matD) free(sys->matD);
        sys->matD=NULL;
        return;
    case (MATX): if (sys->matX) free(sys->matX);
        sys->matX=NULL;
        return;
    default:
        _rerror=8;
    }
}

void DisconMat(SYSTEM *sys, int matrix_type)
{
    switch (matrix_type)
    {
    case (MATA): sys->matA=NULL;
        return;
    case (MATD): sys->matD=NULL;
        return;
    case (MATX): sys->matX=NULL;
        return;
    default:
        _rerror=8;
    }
}

unsigned int Asize(SYSTEM *sys)
{
    return  (unsigned int)(sys->attributes_num)
            *(unsigned int)(sys->objects_num);
}

unsigned int Dsize(SYSTEM *sys)
{
    return  (unsigned int)(sys->objects_num-1)
            *(unsigned int)(sys->objects_num)/2
            *(unsigned int)(sys->setAsize);
}

unsigned int Xsize(SYSTEM *sys)
{
    return sys->matXsize;
}

unsigned int MatMemSize(SYSTEM *sys,int matrix_type)
{
    switch (matrix_type)
    {
    case (MATA): return Asize(sys)*sizeof(value_type);
    case (MATD): return Dsize(sys)*sizeof(cluster_type);
    case (MATX): return Xsize(sys)*sizeof(cluster_type);
    }
    ERROR(8)
}

void *MatExist(SYSTEM *sys,int matrix_type)
{
    switch (matrix_type)
    {
    case (MATA): return (void *)sys->matA;
    case (MATD): return (void *)sys->matD;
    case (MATX): return (void *)sys->matX;
    }
    _rerror=8;
    return NULL;
}

int ObjectsNum(SYSTEM *sys)
{
    return sys->objects_num ;
}

int AttributesNum(SYSTEM *sys)
{
    return sys->attributes_num;
}

void *Description(SYSTEM *sys)
{
    return sys->description;
}

char *SysName(SYSTEM *sys)
{
    return sys->name;
}
