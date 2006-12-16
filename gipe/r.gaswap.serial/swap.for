C     Last change:  PD   24 Nov 1999    1:44 pm
** FILE:
**    SWAMAIN.FOR - main program of SWAP
** FILE IDENTIFICATION:
**    $Id: swamain.for 1.18 1999/02/17 17:35:27 kroes Exp $
** DESCRIPTION:
**    This file contains the program unit SWAP, the main program of SWAP
************************************************************************
      PROGRAM SWAP
C ----------------------------------------------------------------------
C     Date      :22/1/1999
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

      INTEGER   CEXF,BRUNY,BRUND,ERUNY,ERUND,FMAY,NOFRNS,DAYNR
      INTEGER   ICRMOD(0:3,MAYRS),DAYSTA,YEAR,LAYER(MACP)
      INTEGER   BAYRD,BAYRY,RUNNR,THETLO(MAHO),SWSOLU,SWETR,SWNUMS
      INTEGER   SWSCAL,IDEV,YEARP,DAYNRP
      INTEGER   BCRPY(3,MAYRS),BCRPD(3,MAYRS),ECRPY(3,MAYRS)
      INTEGER   ECRPD(3,MAYRS),BSCHY(3,MAYRS),BSCHD(3,MAYRS),CRPNR
      INTEGER   ID,IFINCR,IPORWL,IRMODE,ISEQ,ISTAGE,ISUA,NUMBIT
      INTEGER   NUMLAY,NUMNOD,LOGF,SWHEA,SWSHF,SWDRA,PERIOD,SWRES
      INTEGER   AFO,AUN,ATE,AIR,SWREDU,ISCLAY,SWHYST,SWCF,NOUTDA
      INTEGER   SWVAP,SWDRF,SWSWB,SWAFO,SWAUN,SWATE,SWAIR,SWGC,SWSCRE

      INTEGER   OUTD(366),OUTY(366),SWRAI,SWCFBS
      INTEGER   BOTCOM(MAHO),NSCALE,SWMOBI,SWCRACK,SWDIVD,SWINCO

      REAL      DZ(MACP),LAI,LAT,KDIF,NRAI,NIRD,RAITIM(100),RAIFLX(100)
      REAL      DISNOD(MACP+1),THETOL,ADCRH,ADCRL,ALT,ARFLUX,ATMDEM,CF
      REAL      CIRR,PSAND(MAHO),PSILT(MAHO),PCLAY(MAHO),ORGMAT(MAHO)
      REAL      DPTRA,DRZ,DT,DTM1,DTMAX,DTMIN,DQROT,DTSOLU,DVS,GIRD,GRAI
      REAL      HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,HLIM4,ECMAX,ECSLOP
      REAL      PEVA,PTRA,QTOP,RAD,RD,RDM,RDS,RELTR,RH,KDIR,COFAB
      REAL      T,TCUM,TAV,TAVD,TM1,TMNR,RDCTB(22),WLS,RSRO,POND,PONDMX
      REAL      COFRED,RSIGNI,RSC,GC

      REAL      FSCALE(MAYRS),PF1(MAHO),FM1(MAHO),PF2(MAHO),FM2(MAHO)
      REAL      SHRINA,MOISR1,THETCR(MAHO)
      REAL      MOISRD,ZNCRACK,GEOMF,DIAMPOL,RAPCOEF,DIFDES,COFANI(MAHO)
      REAL      GWLI,CFBS
 
      REAL*8    THETA(MACP),H(MACP),THETM1(MACP),HTABLE(MAHO,99),TAU
      REAL*8    COFGEN(8,MAHO),THETAS(MACP),THETAR(MACP),ALFAMG(MACP)

      REAL*8    THETIM(MAHO),HI(MACP)
 
      CHARACTER METFIL*7,STASTR*7,ENVSTR*50
      CHARACTER*8 CRPFIL(3,MAYRS),CAPFIL(3,MAYRS),BBCFIL(MAYRS)
      CHARACTER*8 DRFIL(MAYRS),IRGFIL(MAYRS),CALFIL(MAYRS)
      CHARACTER*8 OUTFIL(MAYRS),SOLFIL(MAHO)
      CHARACTER*8 PRJNAM
      CHARACTER*72 AFONAM,AUNNAM,ATENAM,AIRNAM

      LOGICAL   FLENDD,FLENDR,FLOUT,FLLAST,FL1ST,FLGENU(MAHO),FLRAI
      LOGICAL   FLIRGE,FLIRGS,FLCROP,FLCAL,FLRAIC,FLRDME
C ----------------------------------------------------------------------
C --- INITIALIZATION

C --- write message running to screen
C --- WRITE (*,'(/,A)') ' Running SWAP ....'

C --- open log file
      CALL Findunit (90,LOGF)
      OPEN (LOGF, FILE = 'SWAP207a.LOG',status='unknown')

        CALL RDKEY (LOGF,PRJNAM,ENVSTR,STASTR,BRUNY,BRUND,ERUNY,
     &  ERUND,ISEQ,FMAY,PERIOD,SWRES,OUTD,OUTY,METFIL,LAT,ALT,SWETR,
     &  SWRAI,IRGFIL,CALFIL,DRFIL,BBCFIL,OUTFIL,NOFRNS,
     &  FLCAL,SWDRA,SWSOLU,SWHEA,SWVAP,SWDRF,SWSWB,SWAFO,AFONAM,
     &  SWAUN,AUNNAM,SWATE,ATENAM,SWAIR,AIRNAM,SWSCRE,NOUTDA)

      CALL RDSWA (PRJNAM,ENVSTR,LOGF,PONDMX,SWREDU,COFRED,RSIGNI,
     &  DTMIN,DTMAX,SWNUMS,THETOL,NUMLAY,NUMNOD,BOTCOM,DZ,SOLFIL,RDS,
     &  SWHYST,TAU,SWSCAL,NSCALE,ISCLAY,FSCALE,SWMOBI,PF1,FM1,PF2,FM2,
     &  THETIM,SWCRACK,SHRINA,MOISR1,MOISRD,ZNCRACK,GEOMF,DIAMPOL,
     &  RAPCOEF,DIFDES,SWDIVD,COFANI,SWINCO,HI,GWLI,THETCR,PSAND,PSILT,
     &  PCLAY,ORGMAT,CFBS,SWCFBS)

C --- do simulation run NOFRNS times
      IF (SWSCAL.EQ.1) NOFRNS = NSCALE
      DO 1000 RUNNR = 1,NOFRNS

C --- do Potential part OR Water Limited part of one run
      DO 1000 IPORWL = 1,2

C ---   Initialize timer
        CALL TIMER (1,IPORWL,RUNNR,ISEQ,FMAY,BRUND,BRUNY,BCRPD,
     &  BCRPY,ECRPD,ECRPY,BSCHD,BSCHY,ERUND,ERUNY,IFINCR,DTMAX,
     &  NUMNOD,H,DTMIN,T,TCUM,TM1,DT,DTM1,ID,DAYNR,DAYSTA,YEAR,FLLAST,
     &  FLENDD,FLENDR,FLOUT,FLCROP,CRPNR,ISTAGE,IRMODE,BAYRD,BAYRY,
     &  RAITIM,RAIFLX,FLRAI,ARFLUX,SWSOLU,DTSOLU,SWNUMS,NUMBIT,
     &  THETOL,QTOP,THETA,THETM1,NOFRNS,SWSCAL,FLCAL,CRPFIL,ICRMOD,
     &  CAPFIL,IRGFIL,CALFIL,BBCFIL,DRFIL,OUTFIL,ENVSTR,
     &  WLS,RSRO,SWDRA,POND,PONDMX,PERIOD,SWRES,FLRAIC,FLRDME,LOGF,
     &  OUTD,OUTY,NOUTDA,YEARP,DAYNRP)

C ---   Initialize soil routine
        IF (IPORWL.EQ.2)
     &  CALL SOIL (1,RUNNR,ISEQ,FLOUT,FL1ST,FLLAST,ENVSTR,
     &  STASTR,OUTFIL(RUNNR),BBCFIL(RUNNR),DRFIL(RUNNR),
     &  BAYRY,BAYRD,DAYNR,ECMAX,ECSLOP,
     &  DAYSTA,YEAR,NUMLAY,NUMNOD,DZ,CIRR,T,TCUM,DT,DRZ,GRAI,GIRD,
     &  PEVA,PTRA,THETA,H,THETM1,TAV,DQROT,DPTRA,ADCRL,ADCRH,ATMDEM,
     &  LAYER,HTABLE,THETLO,DISNOD,NRAI,NIRD,FLGENU,COFGEN,
     &  THETAS,THETAR,ALFAMG,ARFLUX,SWSOLU,DTSOLU,DTMAX,DTMIN,
     &  SWNUMS,NUMBIT,THETOL,QTOP,HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,
     &  HLIM4,RDCTB,RDM,BRUNY,ERUNY,BRUND,ERUND,SWHEA,
     &  WLS,RSRO,SWDRA,POND,PONDMX,FLRAIC,AFO,AUN,ATE,AIR,PERIOD,
     &  SWREDU,COFRED,RSIGNI,SWSCAL,ISCLAY,SWHYST,TAU,
     &  SWVAP,SWDRF,SWSWB,SWAFO,AFONAM,SWAUN,AUNNAM,SWATE,ATENAM,
     &  SWAIR,AIRNAM,LOGF,SWSCRE,SWSHF,
     &  PRJNAM,BOTCOM,SOLFIL,PSAND,PSILT,PCLAY,ORGMAT,
     &  FSCALE,SWMOBI,PF1,FM1,PF2,FM2,THETIM,SWCRACK,SHRINA,
     &  MOISR1,MOISRD,ZNCRACK,GEOMF,DIAMPOL,RAPCOEF,DIFDES,SWDIVD,
     &  COFANI,SWINCO,HI,GWLI,FMAY,THETCR,FLENDD,YEARP,DAYNRP)

C ---   Initialize irrigation routine, part 1
        IF (IPORWL.EQ.2) CALL IRRIG (1,ENVSTR,STASTR,IRGFIL(RUNNR),
     &  OUTFIL(RUNNR),IRMODE,YEAR,DAYNR,RELTR,ID,DVS,FLIRGE,FLIRGS,GIRD,
     &  ISUA,CIRR,NUMNOD,DZ,DRZ,HLIM3L,HLIM3H,HLIM4,LAYER,HTABLE,
     &  THETLO,H,DISNOD,FLGENU,COFGEN,THETAS,THETAR,ALFAMG,
     &  CAPFIL,CRPNR,RUNNR,LOGF,FMAY,BAYRY)

C --- BEGINNING OF A DAY -----------------------------------------------

100     CONTINUE

C ---   Initialize crop routine
        IF (ISTAGE.EQ.2.AND..NOT.FLCROP) THEN
          FLCROP = .TRUE.
          IF (ICRMOD(CRPNR,RUNNR).EQ.1) THEN
            CALL CROPS (1,IPORWL,FLOUT,ID,DAYNR,YEAR,ENVSTR,STASTR,
     &      CRPNR,CRPFIL(CRPNR,RUNNR),OUTFIL(RUNNR),ECRPY(CRPNR,RUNNR),
     &      ECRPD(CRPNR,RUNNR),RDS,TAV,DQROT,PTRA,RELTR,KDIF,KDIR,LAI,
     &      RD,IFINCR,ADCRH,ADCRL,DVS,HLIM1,HLIM2U,HLIM2L,HLIM3H,
     &      HLIM3L,HLIM4,RSC,RDCTB,RDM,ECMAX,ECSLOP,COFAB,LOGF,
     &      SWGC,GC,SWCF,CF,T,IDEV)
          ELSEIF (ICRMOD(CRPNR,RUNNR).EQ.2) THEN
            CALL CROPD (1,IPORWL,FLOUT,ID,DAYNR,YEAR,ENVSTR,STASTR,
     &      CRPNR,CRPFIL(CRPNR,RUNNR),OUTFIL(RUNNR),ECRPY(CRPNR,RUNNR),
     &      ECRPD(CRPNR,RUNNR),RDS,RAD,TAV,TAVD,TMNR,DQROT,PTRA,RELTR,
     &      KDIF,KDIR,LAI,RD,IFINCR,ADCRH,ADCRL,CF,DVS,ECMAX,ECSLOP,
     &      COFAB,LAT,HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,HLIM4,RSC,
     &      RDCTB,RDM,LOGF,T,SWCF)
          ELSEIF (ICRMOD(CRPNR,RUNNR).EQ.3) THEN
            CALL GRASS (1,IPORWL,FLOUT,ID,DAYNR,YEAR,ENVSTR,STASTR,
     &      CRPNR,CRPFIL(CRPNR,RUNNR),OUTFIL(RUNNR),ECRPY(CRPNR,RUNNR),
     &      ECRPD(CRPNR,RUNNR),RDS,RAD,TAV,TAVD,TMNR,DQROT,PTRA,RELTR,
     &      KDIF,KDIR,LAI,RD,IFINCR,ADCRH,ADCRL,ECMAX,ECSLOP,
     &      COFAB,LAT,HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,HLIM4,RSC,
     &      RDCTB,RDM,LOGF,T,SWCF,CF)
          ENDIF
          DRZ = -RD
C ---     Initialize irrigation routine, part 2
          IF (IPORWL.EQ.2) CALL IRRIG (2,ENVSTR,STASTR,IRGFIL(RUNNR),
     &      OUTFIL(RUNNR),IRMODE,YEAR,DAYNR,RELTR,ID,DVS,FLIRGE,FLIRGS,
     &      GIRD,ISUA,CIRR,NUMNOD,DZ,DRZ,HLIM3L,HLIM3H,HLIM4,LAYER,
     &      HTABLE,THETLO,H,DISNOD,FLGENU,COFGEN,THETAS,THETAR,
     &      ALFAMG,CAPFIL,CRPNR,RUNNR,LOGF,FMAY,BAYRY)
        ELSEIF (ISTAGE.EQ.1) THEN
C ---     set 'nocrop conditions'
          CALL NOCROP (DRZ,LAI,CF,FLCROP)
        ENDIF

C ---   Irrigation applied or required ?
        IF ((FLIRGE.OR.FLIRGS).AND.IPORWL.EQ.2) THEN
          CALL IRRIG (3,ENVSTR,STASTR,IRGFIL(RUNNR),OUTFIL(RUNNR),
     &    IRMODE,YEAR,DAYNR,RELTR,ID,DVS,FLIRGE,FLIRGS,GIRD,ISUA,CIRR,
     &    NUMNOD,DZ,DRZ,HLIM3L,HLIM3H,HLIM4,LAYER,
     &    HTABLE,THETLO,H,DISNOD,FLGENU,COFGEN,THETAS,THETAR,
     &    ALFAMG,CAPFIL,CRPNR,RUNNR,LOGF,FMAY,BAYRY)
        ELSE
          GIRD = 0.0
          ISUA = 0
        ENDIF

C ---   Intake of weather data
        CALL METEO (T,DT,IPORWL,YEAR,DAYNR,METFIL,ENVSTR,LAT,
     &  ALT,KDIF,KDIR,LAI,GIRD,ISUA,RAD,TAV,TAVD,TMNR,RH,GRAI,NRAI,
     &  NIRD,ATMDEM,PTRA,PEVA,RAITIM,RAIFLX,FLRAI,ARFLUX,CFBS,RSC,
     &  SWETR,ISTAGE,ICRMOD(CRPNR,RUNNR),LOGF,SWSHF,FLRAIC,COFAB,
     &  FLRDME,SWGC,GC,SWRAI,IDEV,SWCF,CF,SWCFBS)
        FL1ST = .TRUE.

C ---   Soil routine for one timestep
        DO WHILE (.NOT. FLENDD)
          IF (IPORWL.EQ.2) THEN
            CALL SOIL (2,RUNNR,ISEQ,FLOUT,FL1ST,FLLAST,ENVSTR,
     &      STASTR,OUTFIL(RUNNR),BBCFIL(RUNNR),DRFIL(RUNNR),
     &      BAYRY,BAYRD,DAYNR,ECMAX,ECSLOP,
     &      DAYSTA,YEAR,NUMLAY,NUMNOD,DZ,CIRR,T,TCUM,DT,DRZ,GRAI,GIRD,
     &      PEVA,PTRA,THETA,H,THETM1,TAV,DQROT,DPTRA,ADCRL,ADCRH,ATMDEM,
     &      LAYER,HTABLE,THETLO,DISNOD,NRAI,NIRD,FLGENU,COFGEN,
     &      THETAS,THETAR,ALFAMG,ARFLUX,SWSOLU,DTSOLU,DTMAX,DTMIN,
     &      SWNUMS,NUMBIT,THETOL,QTOP,HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,
     &      HLIM4,RDCTB,RDM,BRUNY,ERUNY,BRUND,ERUND,SWHEA,
     &      WLS,RSRO,SWDRA,POND,PONDMX,FLRAIC,AFO,AUN,ATE,AIR,PERIOD,
     &      SWREDU,COFRED,RSIGNI,SWSCAL,ISCLAY,SWHYST,TAU,
     &      SWVAP,SWDRF,SWSWB,SWAFO,AFONAM,SWAUN,AUNNAM,SWATE,ATENAM,
     &      SWAIR,AIRNAM,LOGF,SWSCRE,SWSHF,
     &      PRJNAM,BOTCOM,SOLFIL,PSAND,PSILT,PCLAY,ORGMAT,
     &      FSCALE,SWMOBI,PF1,FM1,PF2,FM2,THETIM,SWCRACK,SHRINA,
     &      MOISR1,MOISRD,ZNCRACK,GEOMF,DIAMPOL,RAPCOEF,DIFDES,SWDIVD,
     &      COFANI,SWINCO,HI,GWLI,FMAY,THETCR,FLENDD,YEARP,DAYNRP)
          ENDIF

C ---     Calculation of next timestep & total time
          CALL TIMER (2,IPORWL,RUNNR,ISEQ,FMAY,BRUND,BRUNY,BCRPD,
     &    BCRPY,ECRPD,ECRPY,BSCHD,BSCHY,ERUND,ERUNY,IFINCR,DTMAX,
     &    NUMNOD,H,DTMIN,T,TCUM,TM1,DT,DTM1,ID,DAYNR,DAYSTA,YEAR,FLLAST,
     &    FLENDD,FLENDR,FLOUT,FLCROP,CRPNR,ISTAGE,IRMODE,BAYRD,BAYRY,
     &    RAITIM,RAIFLX,FLRAI,ARFLUX,SWSOLU,DTSOLU,SWNUMS,NUMBIT,
     &    THETOL,QTOP,THETA,THETM1,NOFRNS,SWSCAL,FLCAL,CRPFIL,ICRMOD,
     &    CAPFIL,IRGFIL,CALFIL,BBCFIL,DRFIL,OUTFIL,ENVSTR,
     &    WLS,RSRO,SWDRA,POND,PONDMX,PERIOD,SWRES,FLRAIC,FLRDME,LOGF,
     &    OUTD,OUTY,NOUTDA,YEARP,DAYNRP)
        END DO

C ---   Rates of crop growth & integrals of crop growth
        IF (ISTAGE.EQ.2) THEN
          IF (IPORWL.EQ.1)  DQROT = PTRA
          IF (ICRMOD(CRPNR,RUNNR).EQ.1) THEN
cpd         DTRA replace by iqrot
            CALL CROPS (2,IPORWL,FLOUT,ID,DAYNR,YEAR,ENVSTR,STASTR,
     &      CRPNR,CRPFIL(CRPNR,RUNNR),OUTFIL(RUNNR),ECRPY(CRPNR,RUNNR),
     &      ECRPD(CRPNR,RUNNR),RDS,TAV,DQROT,PTRA,RELTR,KDIF,KDIR,LAI,
     &      RD,IFINCR,ADCRH,ADCRL,DVS,HLIM1,HLIM2U,HLIM2L,HLIM3H,
     &      HLIM3L,HLIM4,RSC,RDCTB,RDM,ECMAX,ECSLOP,COFAB,LOGF,
     &      SWGC,GC,SWCF,CF,T,IDEV)
         ELSEIF (ICRMOD(CRPNR,RUNNR).EQ.2) THEN
            CALL CROPD (2,IPORWL,FLOUT,ID,DAYNR,YEAR,ENVSTR,STASTR,
     &      CRPNR,CRPFIL(CRPNR,RUNNR),OUTFIL(RUNNR),ECRPY(CRPNR,RUNNR),
     &      ECRPD(CRPNR,RUNNR),RDS,RAD,TAV,TAVD,TMNR,DQROT,PTRA,RELTR,
     &      KDIF,KDIR,LAI,RD,IFINCR,ADCRH,ADCRL,CF,DVS,ECMAX,ECSLOP,
     &      COFAB,LAT,HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,HLIM4,RSC,
     &      RDCTB,RDM,LOGF,T,SWCF)
          ELSEIF (ICRMOD(CRPNR,RUNNR).EQ.3) THEN
            CALL GRASS (2,IPORWL,FLOUT,ID,DAYNR,YEAR,ENVSTR,STASTR,
     &      CRPNR,CRPFIL(CRPNR,RUNNR),OUTFIL(RUNNR),ECRPY(CRPNR,RUNNR),
     &      ECRPD(CRPNR,RUNNR),RDS,RAD,TAV,TAVD,TMNR,DQROT,PTRA,RELTR,
     &      KDIF,KDIR,LAI,RD,IFINCR,ADCRH,ADCRL,ECMAX,ECSLOP,
     &      COFAB,LAT,HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,HLIM4,RSC,
     &      RDCTB,RDM,LOGF,T,SWCF,CF)
          ENDIF
          DRZ = -RD
C ---     terminal activities irrig
          IF (IFINCR.GT.1.AND.IPORWL.EQ.2)
     &      CALL IRRIG (4,ENVSTR,STASTR,IRGFIL(RUNNR),OUTFIL(RUNNR),
     &      IRMODE,YEAR,DAYNR,RELTR,ID,DVS,FLIRGE,FLIRGS,GIRD,ISUA,CIRR,
     &      NUMNOD,DZ,DRZ,HLIM3L,HLIM3H,HLIM4,LAYER,
     &      HTABLE,THETLO,H,DISNOD,FLGENU,COFGEN,THETAS,THETAR,
     &      ALFAMG,CAPFIL,CRPNR,RUNNR,LOGF,FMAY,BAYRY)
        ENDIF

C --- END OF A DAY -----------------------------------------------------

C ---   Update flags, switches and counters
        CALL TIMER (3,IPORWL,RUNNR,ISEQ,FMAY,BRUND,BRUNY,BCRPD,
     &  BCRPY,ECRPD,ECRPY,BSCHD,BSCHY,ERUND,ERUNY,IFINCR,DTMAX,
     &  NUMNOD,H,DTMIN,T,TCUM,TM1,DT,DTM1,ID,DAYNR,DAYSTA,YEAR,FLLAST,
     &  FLENDD,FLENDR,FLOUT,FLCROP,CRPNR,ISTAGE,IRMODE,BAYRD,BAYRY,
     &  RAITIM,RAIFLX,FLRAI,ARFLUX,SWSOLU,DTSOLU,SWNUMS,NUMBIT,
     &  THETOL,QTOP,THETA,THETM1,NOFRNS,SWSCAL,FLCAL,CRPFIL,ICRMOD,
     &  CAPFIL,IRGFIL,CALFIL,BBCFIL,DRFIL,OUTFIL,ENVSTR,
     &  WLS,RSRO,SWDRA,POND,PONDMX,PERIOD,SWRES,FLRAIC,FLRDME,LOGF,
     &  OUTD,OUTY,NOUTDA,YEARP,DAYNRP)

C ---   Write output files
        IF (IPORWL.EQ.2)
     &    CALL SOIL (3,RUNNR,ISEQ,FLOUT,FL1ST,FLLAST,ENVSTR,
     &    STASTR,OUTFIL(RUNNR),BBCFIL(RUNNR),DRFIL(RUNNR),
     &    BAYRY,BAYRD,DAYNR,ECMAX,ECSLOP,
     &    DAYSTA,YEAR,NUMLAY,NUMNOD,DZ,CIRR,T,TCUM,DT,DRZ,GRAI,GIRD,
     &    PEVA,PTRA,THETA,H,THETM1,TAV,DQROT,DPTRA,ADCRL,ADCRH,ATMDEM,
     &    LAYER,HTABLE,THETLO,DISNOD,NRAI,NIRD,FLGENU,COFGEN,
     &    THETAS,THETAR,ALFAMG,ARFLUX,SWSOLU,DTSOLU,DTMAX,DTMIN,
     &    SWNUMS,NUMBIT,THETOL,QTOP,HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,
     &    HLIM4,RDCTB,RDM,BRUNY,ERUNY,BRUND,ERUND,SWHEA,
     &    WLS,RSRO,SWDRA,POND,PONDMX,FLRAIC,AFO,AUN,ATE,AIR,PERIOD,
     &    SWREDU,COFRED,RSIGNI,SWSCAL,ISCLAY,SWHYST,TAU,
     &    SWVAP,SWDRF,SWSWB,SWAFO,AFONAM,SWAUN,AUNNAM,SWATE,ATENAM,
     &    SWAIR,AIRNAM,LOGF,SWSCRE,SWSHF,
     &    PRJNAM,BOTCOM,SOLFIL,PSAND,PSILT,PCLAY,ORGMAT,
     &    FSCALE,SWMOBI,PF1,FM1,PF2,FM2,THETIM,SWCRACK,SHRINA,
     &    MOISR1,MOISRD,ZNCRACK,GEOMF,DIAMPOL,RAPCOEF,DIFDES,SWDIVD,
     &    COFANI,SWINCO,HI,GWLI,FMAY,THETCR,FLENDD,YEARP,DAYNRP)

        IF (.NOT.FLENDR) GOTO 100

C --- END OF A SIMULATION RUN ------------------------------------------

C ---   Terminal activities soil
        IF (IPORWL.EQ.2)
     &  CALL SOIL (4,RUNNR,ISEQ,FLOUT,FL1ST,FLLAST,ENVSTR,
     &  STASTR,OUTFIL(RUNNR),BBCFIL(RUNNR),DRFIL(RUNNR),
     &  BAYRY,BAYRD,DAYNR,ECMAX,ECSLOP,
     &  DAYSTA,YEAR,NUMLAY,NUMNOD,DZ,CIRR,T,TCUM,DT,DRZ,GRAI,GIRD,
     &  PEVA,PTRA,THETA,H,THETM1,TAV,DQROT,DPTRA,ADCRL,ADCRH,ATMDEM,
     &  LAYER,HTABLE,THETLO,DISNOD,NRAI,NIRD,FLGENU,COFGEN,
     &  THETAS,THETAR,ALFAMG,ARFLUX,SWSOLU,DTSOLU,DTMAX,DTMIN,
     &  SWNUMS,NUMBIT,THETOL,QTOP,HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,
     &  HLIM4,RDCTB,RDM,BRUNY,ERUNY,BRUND,ERUND,SWHEA,
     &  WLS,RSRO,SWDRA,POND,PONDMX,FLRAIC,AFO,AUN,ATE,AIR,PERIOD,
     &  SWREDU,COFRED,RSIGNI,SWSCAL,ISCLAY,SWHYST,TAU,
     &  SWVAP,SWDRF,SWSWB,SWAFO,AFONAM,SWAUN,AUNNAM,SWATE,ATENAM,
     &  SWAIR,AIRNAM,LOGF,SWSCRE,SWSHF,
     &  PRJNAM,BOTCOM,SOLFIL,PSAND,PSILT,PCLAY,ORGMAT,
     &  FSCALE,SWMOBI,PF1,FM1,PF2,FM2,THETIM,SWCRACK,SHRINA,
     &  MOISR1,MOISRD,ZNCRACK,GEOMF,DIAMPOL,RAPCOEF,DIFDES,SWDIVD,
     &  COFANI,SWINCO,HI,GWLI,FMAY,THETCR,FLENDD,YEARP,DAYNRP)

1000  CONTINUE

C ---   close log file
        CLOSE (LOGF)

C ---   close ANIMO output files
        CLOSE (AFO)
        CLOSE (AUN)
        CLOSE (ATE)
        CLOSE (AIR)

**C ---   create Suc.CEX file for the GUI
**        Call  FindUnit (90, CEXF)
**        Open  (CEXF, File ='SUC.CEX', status='unknown')
**        Close (CEXF)
        CLOSE (unit=80, status='delete')












        STOP ''
      END

** FILE:
**    SWASUBM.FOR - part of program SWAP
** FILE IDENTIFICATION:
**    $Id: swasubm.for 1.23 1999/02/23 12:14:33 kroes Exp $
** DESCRIPTION:
**    This file contains program units of SWAP. The program units
**    in this file are of the 2nd level and are sorted alphabetically
**    with the first letter of the program unit.
**    The following program units are in this file:
**        CROPD, GRASS, CROPS, IRRIG, METEO, SOIL, TIMER
************************************************************************
C --- SWASUBM.FOR -----------------------------------------------------
C ----------------------------------------------------------------------
      SUBROUTINE CROPD (ITASK,IPORWL,FLOUT,ID,DAYNR,YEAR,ENVSTR,STASTR,
     &  CRPNR,CRPFIL,OUTNAM,ECRPY,ECRPD,RDS,RAD,TAV,TAVD,TMNR,TRA,PTRA,
     &  RELTR,KDIF,KDIR,LAI,RD,IFINCR,ADCRH,ADCRL,CF,DVS,ECMAX,ECSLOP,
     &  COFAB,LAT,HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,HLIM4,RSC,
     &  RDCTAB,RDM,LOGF,T,SWCF)
C ----------------------------------------------------------------------
C     Date               : 21/1/99
C     Purpose            : WOFOST crop growth routine for SWACROP
C     Subroutines called : RDCRP,SHIFTR,SHIFTL,NRTODA,ASTRO,TOTASS
C     Functions called   : AFGEN,LIMIT
C     File usage         : OUTNAM.CR#, file with crop production results
C ----------------------------------------------------------------------
      IMPLICIT NONE
 
      INTEGER   CRP,CRPNR,DAYNR,YEAR,M,D,ECRPY,ECRPD,SWCF
      INTEGER   I1,ID,IDSL,IFINCR,ILVOLD,IPORWL,ITASK,LOGF

      REAL      LAT,KDIF,LAI,LAICR,LAIEM,LAIEXP,LAIMAX,LASUM,MRES,MREST
      REAL      LV(300),LVAGE(300),SLA(300),CPWDM(3,300),PWSO(3,300)
      REAL      DTSMTB(30),SLATB(30),AMAXTB(30),TMPFTB(30),TMNFTB(30)
      REAL      RFSETB(30),FRTB(30),FLTB(30),FSTB(30),FOTB(30)
      REAL      RDRRTB(30),RDRSTB(30),CFTAB(30),RDCTAB(22)
      REAL      ADCRH,ADCRL,ADMI,AFGEN,AMAX,ASRC,LIMIT,T
      REAL      CCHECK,CF,COSLD,CPTR0,CPTR1,CRT0,CRT1,CTR0,CTR1,CVF,CVL
      REAL      CVO,CVR,CVS,CWDM,DALV,DAYL,DAYLP,DELT,DLC,DLO,DMI,DRLV
      REAL      DRRT,DRST,DSLV,DSLV1,DSLV2,DSLVT,DTEFF,DTGA,DTSUM,DVR
      REAL      DVRED,DVS,DVSEND,DWLV,DWRT,DWST,EFF,FCHECK,FL,FO,FR,FS
      REAL      FYSDEL,GASS,GASST,GLA,GLAIEX,GLASOL,GRLV,GRRT,GRST,RDC
      REAL      GWRT,GWSO,GWST,ECMAX,ECSLOP,PERDL,PGASS,PTRA,Q10,RAD,RD
      REAL      RDI,RDM,RDS,RELTR,REST,RGRLAI,RML,RMO,RMR,RMRES,RMS,RR
      REAL      RRI,SINLD,SLAT,SPA,SPAN,SSA,TADW,TAV,TAVD,TBASE,RSC
      REAL      TDWI,TEFF,TMNR,TRA,TSUMAM,TSUMEA,TWLV,TWST,KDIR,COFAB
      REAL      WLV,WRT,WSO,WST,HLIM1,HLIM2L,HLIM2U,HLIM3H,HLIM3L,HLIM4
C     REAL      TAGP,TWRT

      CHARACTER CRPFIL*8,OUTNAM*8,FILNAM*12,ENVSTR*50,STASTR*7
      CHARACTER EXT(3)

      character*80 rmldsp
      
      LOGICAL   ODONE,HDONE,FLOUT
  
      SAVE

      PARAMETER (DELT=1.0)
      DATA EXT/'1','2','3'/
C ----------------------------------------------------------------------
      GOTO (1000,2000) ITASK

1000  CONTINUE

C --- INITIALIZATION ---------------------------------------------------

C --- read crop data
      CALL RDCRPD (CRPFIL,ENVSTR,SWCF,CFTAB,IDSL,DLO,DLC,TSUMEA,
     &  TSUMAM,DTSMTB,DVSEND,TDWI,LAIEM,RGRLAI,SLATB,SPA,
     &  SSA,SPAN,TBASE,KDIF,KDIR,EFF,AMAXTB,TMPFTB,TMNFTB,CVL,CVO,CVR,
     &  CVS,Q10,RML,RMO,RMR,RMS,RFSETB,FRTB,FLTB,FSTB,FOTB,PERDL,RDRRTB,
     &  RDRSTB,HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,HLIM4,RSC,
     &  ADCRH,ADCRL,ECMAX,ECSLOP,COFAB,RDI,RRI,RDC,RDCTAB,LOGF)

C --- maximum rooting depth & actual rooting depth
      RDM = MAX (RDI,MIN(RDS,RDC))
      RD  = RDI

C --- initial values of crop parameters
      DVS      = 0.
      FR       = AFGEN (FRTB,30,DVS)
      FL       = AFGEN (FLTB,30,DVS)
      FS       = AFGEN (FSTB,30,DVS)
      FO       = AFGEN (FOTB,30,DVS)
      SLA(1)   = AFGEN (SLATB,30,DVS)
      LVAGE(1) = 0.
      ILVOLD   = 1

C --- initial state variables of the crop
      WRT    = FR*TDWI
      TADW   = (1.-FR)*TDWI
      WST    = FS*TADW
      WSO    = FO*TADW
      WLV    = FL*TADW
      LAIEM  = WLV*SLA(1)
      LV(1)  = WLV
      LASUM  = LAIEM     
      LAIEXP = LAIEM     
      LAIMAX = LAIEM
      LAI    = LASUM+SSA*WST+SPA*WSO 
      DWRT   = 0.
      DWLV   = 0.
      DWST   = 0.
      CF     = AFGEN (CFTAB,30,DVS)

C --- initial summation variables of the crop
C     TAGP   = WLV+WST+WSO
      GASST  = 0.
      MREST  = 0. 
      CPTR0  = 0.
      CTR0   = 0.
      CPTR1  = 0.
      CTR1   = 0.

C --- misc.
      IFINCR = 0
      IF (IPORWL.EQ.2) HDONE =.FALSE.

      RETURN

2000  CONTINUE

C --- RATES OF CHANGE OF THE CROP VARIABLES ----------------------------

C --- phenological development rate  
      CALL ASTRO (DAYNR,LAT,DAYL,DAYLP,SINLD,COSLD)

C --- increase in temperature sum
      DTSUM = AFGEN (DTSMTB,30,TAV)

      IF (DVS.LT.1.) THEN     
C --- development during vegetative phase
        DVRED = 1.
        IF (IDSL.GE.1) DVRED = LIMIT (0.,1.,(DAYLP-DLC)/(DLO-DLC))
        DVR = DVRED*DTSUM/TSUMEA
      ELSE
C --- development during generative phase
        DVR   = DTSUM/TSUMAM
      ENDIF    

C === DAILY DRY MATTER PRODUCTION 

C --- Gross assimilation

      AMAX  = AFGEN (AMAXTB,30,DVS)
C --- correction for sub-optimum average daytemperature
      AMAX  = AMAX * AFGEN (TMPFTB,30,TAVD)
      CALL TOTASS (DAYNR,DAYL,AMAX,EFF,LAI,KDIF,RAD,SINLD,COSLD,DTGA)
C --- correction for low minimum temperature
      DTGA  = DTGA * AFGEN (TMNFTB,30,TMNR)
C --- potential assimilation in kg CH2O per ha
      PGASS = DTGA * 30./44.

C --- water stress reduction of PGASS to GASS
      RELTR = LIMIT (0.0,1.0,TRA/PTRA)
      GASS  = PGASS * RELTR

C --- respiration and partitioning of carbohydrates between growth and
C --- maintenance respiration
      RMRES = (RMR*WRT+RML*WLV+RMS*WST+RMO*WSO)*AFGEN(RFSETB,30,DVS)
      TEFF  = Q10**((TAV-25.)/10.)
      MRES  = MIN(GASS,RMRES*TEFF)
      ASRC  = GASS-MRES

C --- partitioning factors
      FR = AFGEN(FRTB,30,DVS)
      FL = AFGEN(FLTB,30,DVS)
      FS = AFGEN(FSTB,30,DVS)
      FO = AFGEN(FOTB,30,DVS)
C --- check on partitioning
      FCHECK = FR+(FL+FS+FO)*(1.0-FR) - 1.0
      IF (ABS(FCHECK).GT.0.0001) STOP 'Partitioning error'

C --- dry matter increase
      CVF   = 1./((FL/CVL+FS/CVS+FO/CVO)*(1.-FR)+FR/CVR)
      DMI   = CVF*ASRC
C --- check on carbon balance
      CCHECK = (GASS-MRES-(FR+(FL+FS+FO)*(1.0-FR))*DMI/CVF)
     &         /MAX(0.0001,GASS)      
      IF (ABS(CCHECK).GT.0.0001) STOP 'Carbon balance error'

C === GROWTH RATE BY PLANT ORGAN

C --- root extension
      RR = MIN (RDM-RD,RRI)
      IF (FR.LE.0.OR.PGASS.LT.1.0) RR = 0.0

C --- growth rate roots and aerial parts
      ADMI = (1.-FR)*DMI
      GRRT = FR*DMI
      DRRT = WRT*AFGEN (RDRRTB,30,DVS)
      GWRT = GRRT-DRRT

C --- weight of new leaves
      GRLV = FL*ADMI

C --- death of leaves due to water stress or high LAI
      DSLV1 = WLV*(1.-TRA/PTRA)*PERDL
      LAICR = 3.2/KDIF
      DSLV2 = WLV*LIMIT(0.,0.03,0.03*(LAI-LAICR)/LAICR)
      DSLV  = MAX (DSLV1,DSLV2) 

C --- death of leaves due to exceeding life span:

C --- first: leaf death due to water stress or high LAI is imposed 
C ---        on array until no more leaves have to die or all leaves
C ---        are gone

      REST = DSLV*DELT
      I1   = ILVOLD

100   IF (REST.GT.LV(I1).AND.I1.GE.1) THEN
        REST = REST-LV(I1) 
        I1   = I1-1
        GOTO 100
      ENDIF

C --- then: check if some of the remaining leaves are older than SPAN,
C ---       sum their weights

      DALV = 0.0
      IF (LVAGE(I1).GT.SPAN.AND.REST.GT.0.AND.I1.GE.1) THEN
        DALV = LV(I1)-REST
        REST = 0.0
        I1   = I1-1
      ENDIF

110   IF (I1.GE.1.AND.LVAGE(I1).GT.SPAN) THEN
        DALV = DALV+LV(I1)
        I1   = I1-1
      GOTO 110
      ENDIF

      DALV = DALV/DELT

C --- Finally: calculate total death rate leaves
      DRLV = DSLV+DALV

C --- physiologic ageing of leaves per time step
      FYSDEL = MAX (0.,(TAV-TBASE)/(35.-TBASE))

C --- specific leaf area valid for current timestep
      SLAT   = AFGEN (SLATB,30,DVS)

C --- calculation of specific leaf area in case of exponential growth:
C --- leaf area not to exceed exponential growth curve
      IF (LAIEXP.LT.6.0) THEN
        DTEFF  = MAX (0.,TAV-TBASE)
C ---   increase in leaf area during exponential growth
        GLAIEX = LAIEXP*RGRLAI*DTEFF
C ---   source-limited increase in leaf area
        GLASOL = GRLV*SLAT
C ---   actual increase is determined by lowest value
        GLA    = MIN (GLAIEX,GLASOL)
C ---   SLAT will be modified in case GLA equals GLAIEX
        IF (GRLV.GT.0.0) SLAT = GLA/GRLV
      ENDIF  

C --- growth rate stems
      GRST = FS*ADMI
C --- death rate stems
      DRST = AFGEN (RDRSTB,30,DVS)*WST
C --- net growth rate stems
      GWST = GRST-DRST

C --- growth rate storage organs
      GWSO = FO*ADMI

C ----INTEGRALS OF THE CROP --------------------------------------------

C --- phenological development stage
      DVS    = DVS+DVR*DELT

C --- leaf death (due to water stress or high LAI) is imposed on array 
C --- untill no more leaves have to die or all leaves are gone

      DSLVT = DSLV*DELT
      I1    = ILVOLD
120   IF (DSLVT.GT.0.AND.I1.GE.1) THEN
        IF (DSLVT.GE.LV(I1)) THEN
          DSLVT  = DSLVT-LV(I1)
          LV(I1) = 0.0
          I1     = I1-1
        ELSE
          LV(I1) = LV(I1)-DSLVT
          DSLVT  = 0.0
        ENDIF
      GOTO 120
      ENDIF 

C --- leaves older than SPAN die
130   IF (LVAGE(I1).GE.SPAN.AND.I1.GE.1) THEN
        LV(I1) = 0.0
        I1     = I1-1
      GOTO 130
      ENDIF

C --- oldest class with leaves
      ILVOLD = I1

C --- shifting of contents, updating of physiological age
      DO 140 I1 = ILVOLD,1,-1
        LV(I1+1)    = LV(I1)
        SLA(I1+1)   = SLA(I1)
        LVAGE(I1+1) = LVAGE(I1)+FYSDEL*DELT
140   CONTINUE
      ILVOLD = ILVOLD+1

C --- new leaves in class 1
      LV(1)    = GRLV*DELT
      SLA(1)   = SLAT
      LVAGE(1) = 0. 

C --- calculation of new leaf area and weight
      LASUM = 0.
      WLV   = 0.
      DO 150 I1 = 1,ILVOLD
        LASUM = LASUM+LV(I1)*SLA(I1)
        WLV   = WLV+LV(I1)
150   CONTINUE

C --- leaf area index in case of exponential growth
      LAIEXP = LAIEXP+GLAIEX*DELT

C --- dry weight of living plant organs
      WRT    = WRT+GWRT*DELT
      WST    = WST+GWST*DELT
      WSO    = WSO+GWSO*DELT

C --- total above ground biomass
      TADW   = WLV+WST+WSO

C --- dry weight of dead plant organs (roots,leaves & stems)
      DWRT   = DWRT+DRRT*DELT
      DWLV   = DWLV+DRLV*DELT
      DWST   = DWST+DRST*DELT

C --- dry weight of dead and living plant organs
C     TWRT   = WRT+DWRT
      TWLV   = WLV+DWLV
      TWST   = WST+DWST
      CWDM   = TWLV+TWST+WSO

C --- total gross assimilation and maintenance respiration
      GASST  = GASS + GASST
      MREST  = MRES + MREST

C --- leaf area index
      LAI    = LASUM+SSA*WST+SPA*WSO
C !!! LAIMAX is not used
      LAIMAX = MAX (LAI,LAIMAX)

C --- rooting depth
      RD     = RD+RR

C --- crop factor or crop height
      CF     = AFGEN (CFTAB,30,DVS)

C --- cumulative relative transpiration
      CPTR0 = CPTR0 + PTRA  
      CTR0  = CTR0  + TRA
      CRT0  = LIMIT (0.0,1.0,CTR0/CPTR0)

      IF (DVS.GE.1.00) THEN
        CPTR1 = CPTR1+PTRA
        CTR1  = CTR1 + TRA
        CRT1  = LIMIT (0.0,1.0,CTR1/CPTR1)
      ELSE
        CRT1 = 1.0
      ENDIF

C --- save some results of potential run
      IF (IPORWL.EQ.1) THEN
        CPWDM(CRPNR,ID) = CWDM
        PWSO(CRPNR,ID)  = WSO
      ENDIF

C === CROP FINISH CONDITIONS 

      IF (DVS.GE.DVSEND)                    IFINCR=1
      IF (YEAR.EQ.ECRPY.AND.DAYNR.EQ.ECRPD) IFINCR=2
      IF (LAI.LE.0.002.AND.DVS.GT.0.5)      IFINCR=3

C === OUTPUT SECTION 

      ODONE = .FALSE.
      IF (.NOT.FLOUT.OR.IPORWL.EQ.1) GOTO 2500
      IF (HDONE)      GOTO 2100

C --- compose filename
      CALL SHIFTR (OUTNAM)
      FILNAM = OUTNAM//'.CR'//EXT(CRPNR)
      CALL SHIFTL (FILNAM)
      CALL SHIFTR (ENVSTR)

C --- open output file
      CALL FINDUNIT (10,CRP)
      OPEN (CRP,FILE=rmldsp(ENVSTR//FILNAM), STATUS=STASTR
     & ,ACCESS='SEQUENTIAL')

C --- write header
      WRITE (CRP,2010)
2010  FORMAT (
     &'*DATE       DAY ID DVS  LAI  CF/H  RD  CRT0 CRT1 CPWDM CWDM  CPW'
     &,'SO CWSO *',/,
     &'*dd/mm/yyyy  nr              -/cm  cm            kg/ha kg/ha kg/'
     &,'ha kg/ha*',/,
     &'*<============><==><===><===><====><==><===><===><====><====><=='
     &,'==><====>')
      HDONE=.TRUE.

2100  CONTINUE

C --- Write output

C --- conversion of daynumber to date
      CALL NRTODA (YEAR,DAYNR,M,D)

C --- write output record
      WRITE (CRP,2110) D,M,YEAR,NINT(T),ID,DVS,LAI,CF,
     & NINT(RD),CRT0,CRT1,NINT(CPWDM(CRPNR,ID)),NINT(CWDM),
     & NINT(PWSO(CRPNR,ID)),NINT(WSO)
2110  FORMAT (I3,'/',I2.2,'/',2I4,I4,2F5.2,F6.1,I4,2F5.2,4I6)
      ODONE = .TRUE.

C --- TERMINAL SECTION: write one more record & close output file
2500  IF (IFINCR.GT.0.AND.IPORWL.EQ.2) THEN
        IF (ODONE) THEN
          CLOSE (CRP)
        ELSE
C ---     conversion of daynumber to date
          CALL NRTODA (YEAR,DAYNR,M,D)
          WRITE (CRP,2110) D,M,YEAR,NINT(T),ID,DVS,LAI,CF,
     &    NINT(RD),CRT0,CRT1,NINT(CPWDM(CRPNR,ID)),NINT(CWDM),
     &    NINT(PWSO(CRPNR,ID)),NINT(WSO)
          CLOSE (CRP)
        ENDIF
      ENDIF

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE GRASS (ITASK,IPORWL,FLOUT,ID,DAYNR,YEAR,ENVSTR,STASTR,
     &  CRPNR,CRPFIL,OUTNAM,ECRPY,ECRPD,RDS,RAD,TAV,TAVD,TMNR,TRA,PTRA,
     &  RELTR,KDIF,KDIR,LAI,RD,IFINCR,ADCRH,ADCRL,ECMAX,ECSLOP,
     &  COFAB,LAT,HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,HLIM4,RSC,
     &  RDCTAB,RDM,LOGF,T,SWCF,CF)
C ----------------------------------------------------------------------
C     Date               : 09/10/97
C     Purpose            : grass growth routine for SWAP          
C     Subroutines called : RDCRP,SHIFTR,SHIFTL,NRTODA,ASTRO,TOTASS
C     Functions called   : AFGEN,LIMIT
C     File usage         : OUTNAM.CR#, file with crop production results
C ----------------------------------------------------------------------
      IMPLICIT NONE  

      INTEGER   CRP,CRPNR,DAYNR,YEAR,M,D,ECRPY,ECRPD,LOGF,SWCF
      INTEGER   I1,ID,IDELAY,IDREGR,IFINCR,ILVOLD,IPORWL,ITASK

      REAL      LAT,KDIF,LAI,LAICR,LAIEM,LAIEXP,LAIMAX,LASUM,LIMIT,MRES
      REAL      LV(366),LVAGE(366),SLA(366),CPWDM(366),CPWHM(366)
      REAL      SLATB(30),AMAXTB(30),TMPFTB(30),TMNFTB(30)
      REAL      RFSETB(30),FRTB(30),FLTB(30),FSTB(30),RDRRTB(30)
      REAL      RDRSTB(30),HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L
      REAL      HLIM4,RDCTAB(22),ECMAX,ECSLOP,KDIR,COFAB,T,CF
C     REAL      LAITB(30),TWRT
      REAL      ADCRH,ADCRL,ADMI,AFGEN,AMAX,ASRC
      REAL      CCHECK,COSLD,CPTR0,CRT0,CTR0,CVF,CVL
      REAL      CVR,CVS,DALV,DAYL,DAYLP,DELT,DMI,DRLV
      REAL      DRRT,DRST,DRST1,DRST2,DSLV,DSLV1,DSLV2,DSLVT,DTEFF,DTGA
      REAL      DWLV,DWRT,DWST,FCHECK,FL,FR,FS,EFF
      REAL      FYSDEL,GASS,GLA,GLAIEX,GLASOL,GRLV,GRRT,GRST
      REAL      GWRT,GWST,PERDL,PGASS,PTRA,Q10,RAD,RD,RDC
      REAL      RDI,RDM,RDS,RELTR,REST,RGRLAI,RID,RML,RMR,RMRES,RMS,RR
      REAL      RRI,SINLD,SLAT,SPAN,SSA,TAGP,TAGPS,TAGPT,RSC
      REAL      TAV,TAVD,TBASE,TDWI,TEFF,TMNR,TRA,TWLV,TWST,WLV,WRT,WST

      CHARACTER CRPFIL*8,OUTNAM*8,FILNAM*12,ENVSTR*50,STASTR*7
      CHARACTER EXT(3)

      character*80 rmldsp
      
      LOGICAL   ODONE,HDONE,FLOUT
  
      SAVE

      PARAMETER (DELT=1.0)

c     DATA LAITB/0.0,1.5,1000.0,0.84,2500.0,0.84,4000.0,0.84,
c    &           6000.0,0.6,8000.0,0.3,18*0.0/
C --- LAI of the stubble depends on biomass of preceeding harvest
C --- De Jong and Kabat, Lantinga

      DATA EXT/'1','2','3'/
C ----------------------------------------------------------------------
      GOTO (1000,2000) ITASK

1000  CONTINUE

C --- INITIALIZATION ---------------------------------------------------

C --- read crop data
      CALL RDGRASS (CRPFIL,ENVSTR,TDWI,LAIEM,RGRLAI,SLATB,
     &  SSA,SPAN,TBASE,KDIF,KDIR,EFF,AMAXTB,TMPFTB,TMNFTB,CVL,CVR,CVS,
     &  Q10,RML,RMR,RMS,RFSETB,FRTB,FLTB,FSTB,PERDL,RDRRTB,
     &  RDRSTB,HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,HLIM4,RSC,
     &  ADCRH,ADCRL,ECMAX,ECSLOP,COFAB,RDI,RRI,RDC,RDCTAB,LOGF)

C --- maximum rooting depth & actual rooting depth
      RDM = MAX (RDI,MIN(RDS,RDC))
      RD  = RDI

C --- initial values of crop parameters
      RID      = FLOAT (ID)
      FR       = AFGEN (FRTB,30,RID)
      FL       = AFGEN (FLTB,30,RID)
      FS       = AFGEN (FSTB,30,RID)
      SLA(1)   = AFGEN (SLATB,30,RID)
      LVAGE(1) = 0.
      ILVOLD   = 1
      IDREGR   = 0

C --- initial state variables of the crop

      WRT    = FR*TDWI
      WST    = FS*(1.0-FR)*TDWI 
      WLV    = LAIEM/SLA(1)
      LV(1)  = WLV
      LASUM  = LAIEM     
      LAIEXP = LAIEM     
      LAIMAX = LAIEM
      LAI    = LASUM+SSA*WST 
      DWRT   = 0.
      DWLV   = 0.
      DWST   = 0.
      CF     = 1.0 

C --- initial summation variables of the crop
      TAGP   = WLV+WST
      CPTR0  = 0.0
      CTR0   = 0.0
      TAGPT  = 0.0

C --- misc.
      SWCF   = 1
      IFINCR = 0
      IF (IPORWL.EQ.2) HDONE =.FALSE.

      RETURN

2000  CONTINUE

C --- RATES OF CHANGE OF THE CROP VARIABLES ----------------------------

      RID = FLOAT(ID)

C !!! skip in case of regrowth
      IF (ID.NE.0.AND.ID.LT.IDREGR) GOTO 1330

C === DAILY DRY MATTER PRODUCTION 

C --- Gross assimilation
      AMAX  = AFGEN (AMAXTB,30,RID)
C --- correction for sub-optimum average daytemperature
      AMAX  = AMAX * AFGEN (TMPFTB,30,TAVD)
      CALL ASTRO (DAYNR,LAT,DAYL,DAYLP,SINLD,COSLD)
      CALL TOTASS (DAYNR,DAYL,AMAX,EFF,LAI,KDIF,RAD,SINLD,COSLD,DTGA)
C --- correction for low minimum temperature
      DTGA  = DTGA * AFGEN (TMNFTB,30,TMNR)
C --- potential assimilation in kg CH2O per ha
      PGASS = DTGA * 30./44.

C --- Water stress reduction of PGASS to GASS

      RELTR = LIMIT (0.0,1.0,TRA/PTRA)
      GASS  = PGASS * RELTR

C --- respiration and partitioning of carbohydrates between growth and
C --- maintenance respiration
      RMRES = (RMR*WRT+RML*WLV+RMS*WST)*AFGEN(RFSETB,30,RID)
      TEFF  = Q10**((TAV-25.)/10.)
      MRES  = MIN (GASS,RMRES*TEFF)
      ASRC  = GASS-MRES

C --- partitioning factors
      FR = AFGEN(FRTB,30,RID)
      FL = AFGEN(FLTB,30,RID)
      FS = AFGEN(FSTB,30,RID)
C --- check on partitioning
      FCHECK = FR+(FL+FS)*(1.0-FR) - 1.0
      IF (ABS(FCHECK).GT.0.0001) STOP 'Partitioning error'

C --- dry matter increase
      CVF   = 1./((FL/CVL+FS/CVS)*(1.-FR)+FR/CVR)
      DMI   = CVF*ASRC
C --- check on carbon balance
      CCHECK = (GASS-MRES-(FR+(FL+FS)*(1.0-FR))*DMI/CVF)
     &         /MAX(0.0001,GASS)      
      IF (ABS (CCHECK).GT.0.0001) STOP 'Carbon balance error'

C === GROWTH RATE BY PLANT ORGAN 

C --- root length
      RR = MIN (RDM-RD,RRI)
      IF (FR.LE.0.OR.PGASS.LT.1.0) RR = 0.0

C --- growth rate roots and aerial parts
C --- after reaching a live weight of 2500 kg, the growth
C --- of the roots is balanced by the death of root tissue
      GRRT = FR*DMI
      IF (WRT.GT.2500.0) GRRT = 0.0
      ADMI = (1.-FR)*DMI
      DRRT = 0.0
      GWRT = GRRT-DRRT

C --- Growth rate leaves

C --- weight of new leaves
      GRLV = FL*ADMI

C --- death of leaves due to water stress or high LAI
      DSLV1 = WLV*(1.-TRA/PTRA)*PERDL
      LAICR = 3.2/KDIF
      DSLV2 = WLV*LIMIT(0.,0.03,0.03*(LAI-LAICR)/LAICR)
      DSLV  = MAX (DSLV1,DSLV2) 

C --- death of leaves due to exceeding life span;
C --- leaf death is imposed on array until no more leaves have
C --- to die or all leaves are gone

      REST = DSLV*DELT
      I1   = ILVOLD

100   IF (REST.GT.LV(I1).AND.I1.GE.1) THEN
        REST = REST-LV(I1) 
        I1   = I1-1
        GOTO 100
      ENDIF

C --- check if some of the remaining leaves are older than SPAN,
C --- sum their weights

      DALV = 0.0
      IF (LVAGE(I1).GT.SPAN.AND.REST.GT.0.AND.I1.GE.1) THEN
        DALV = LV(I1)-REST
        REST = 0.0
        I1   = I1-1
      ENDIF

110   IF (I1.GE.1.AND.LVAGE(I1).GT.SPAN) THEN
        DALV = DALV+LV(I1)
        I1   = I1-1
      GOTO 110
      ENDIF

      DALV = DALV/DELT

C --- death rate leaves and growth rate living leaves
      DRLV = DSLV+DALV

C --- physiologic ageing of leaves per time step
      FYSDEL = MAX (0.,(TAV-TBASE)/(35.-TBASE))
      SLAT   = AFGEN (SLATB,30,RID)

C --- leaf area not to exceed exponential growth curve
      IF (LAIEXP.LT.6.0) THEN
        DTEFF  = MAX (0.,TAV-TBASE)
        GLAIEX = LAIEXP*RGRLAI*DTEFF
C --- source-limited increase in leaf area
        GLASOL = GRLV*SLAT
        GLA    = MIN (GLAIEX,GLASOL)
C --- adjustment of specific leaf area of youngest leaf class
        IF (GRLV.GT.0.0) SLAT = GLA/GRLV
      ENDIF  

C --- growth rate stems
      GRST = FS*ADMI
C --- death of stems due to water stress
      DRST1 = WST*(1.0-TRA/PTRA)*PERDL
C --- death of stems due to ageing
      DRST2 = AFGEN (RDRSTB,30,RID)*WST
      DRST = (DRST1+DRST2)/DELT 
      GWST = GRST-DRST

C ----INTEGRALS OF THE CROP --------------------------------------------

************************************************************************
*     After cutting, growth is initialized again. The weight of 
*     the sward is stored.
************************************************************************

C --- Harvest criteria (open to personal choice of user) 
      IF (TAGP.GT.4200.0 .OR. (ID.GT.210 .AND. TAGP.GT.3700.)) THEN

*       when using relation LAITB according to literature:
*       LASUM    = AFGEN (LAITB,30,TAGP)
*       else:  
        LASUM    = LAIEM
        SLA(1)   = AFGEN (SLATB,30,RID)
        WLV      = LASUM/SLA(1)
        FL       = AFGEN (FLTB,30,RID)
        FS       = AFGEN (FSTB,30,RID)
        WST      = FS/FL*WLV
        DWLV     = 0.0
        DWST     = 0.0
        LVAGE(1) = 0.0
        ILVOLD   = 1
        LAIEXP   = LASUM
        LV(1)    = WLV

c       GWLV = 0.0
        GWST = 0.0
        GWRT = 0.0
        DRLV = 0.0
        DRST = 0.0
        DRRT = 0.0

        TAGPS = AMAX1 (0.0,(TAGP-(WLV+DWLV+WST+DWST)))
        TAGPT = TAGPT + TAGPS

C --- regrowth delay after handbook P.R.

        IF (TAGPS.LT.2000.0) IDELAY = 1
        IF (TAGPS.GE.2000.0.AND.TAGPS.LT.2500.0) IDELAY = 2
        IF (TAGPS.GE.2500.0.AND.TAGPS.LT.3000.0) IDELAY = 3
        IF (TAGPS.GE.3000.0.AND.TAGPS.LT.3500.0) IDELAY = 4
        IF (TAGPS.GE.3500.0.AND.TAGPS.LT.4000.0) IDELAY = 5
        IF (TAGPS.GE.4000.0) IDELAY = 6

        IDREGR = ID+IDELAY+1

      ENDIF

      IF (ID.LT.IDREGR) GOTO 1330

C --- leaf death is imposed on array untill no more leaves have to
C --- die or all leaves are gone

      DSLVT = DSLV*DELT
      I1    = ILVOLD
120   IF (DSLVT.GT.0.AND.I1.GE.1) THEN
        IF (DSLVT.GE.LV(I1)) THEN
          DSLVT  = DSLVT-LV(I1)
          LV(I1) = 0.0
          I1     = I1-1
        ELSE
          LV(I1) = LV(I1)-DSLVT
          DSLVT  = 0.0
        ENDIF
      GOTO 120
      ENDIF 

130   IF (LVAGE(I1).GE.SPAN.AND.I1.GE.1) THEN
        LV(I1) = 0.0
        I1     = I1-1
      GOTO 130
      ENDIF

      ILVOLD = I1

C --- shifting of contents, integration of physiological age
      DO 140 I1 = ILVOLD,1,-1
        LV(I1+1)    = LV(I1)
        SLA(I1+1)   = SLA(I1)
        LVAGE(I1+1) = LVAGE(I1)+FYSDEL*DELT
140   CONTINUE
      ILVOLD = ILVOLD+1

C --- new leaves in class 1
      LV(1)    = GRLV*DELT
      SLA(1)   = SLAT
      LVAGE(1) = 0. 

C --- calculation of new leaf area and weight
      LASUM = 0.
      WLV   = 0.
      DO 150 I1 = 1,ILVOLD
        LASUM = LASUM+LV(I1)*SLA(I1)
        WLV   = WLV+LV(I1)
150   CONTINUE

      LAIEXP = LAIEXP+GLAIEX*DELT

1330  CONTINUE

C --- dry weight of living plant organs
      WRT    = WRT+GWRT*DELT
      WST    = WST+GWST*DELT

C --- dry weight of dead plant organs (roots,leaves & stems)
      DWRT   = DWRT+DRRT*DELT
      DWLV   = DWLV+DRLV*DELT
      DWST   = DWST+DRST*DELT

C --- dry weight of dead and living plant organs
c     TWRT   = WRT+DWRT
      TWLV   = WLV+DWLV
      TWST   = WST+DWST
      TAGP   = TWLV+TWST

C --- leaf area index
      LAI    = LASUM+SSA*WST
      LAIMAX = MAX (LAI,LAIMAX)

C --- rooting depth
      RD     = RD+RR

C --- cumulative relative transpiration
      CPTR0 = CPTR0 + PTRA  
      CTR0  = CTR0  + TRA
      CRT0  = LIMIT (0.0,1.0,CTR0/CPTR0)

C --- save some results of potential run
      IF (IPORWL.EQ.1) THEN
        CPWDM(ID) = TAGP
        CPWHM(ID) = TAGPT
      ENDIF

C === CROP FINISH CONDITIONS 

      IF (YEAR.EQ.ECRPY.AND.DAYNR.EQ.ECRPD) IFINCR=2

C === OUTPUT SECTION 

      ODONE = .false.
      IF (.NOT.FLOUT.OR.IPORWL.EQ.1) GOTO 2500
      IF (HDONE)      GOTO 2100

C --- compose filename
      CALL SHIFTR (OUTNAM)
      FILNAM = OUTNAM//'.CR'//EXT(CRPNR)
      CALL SHIFTL (FILNAM)
      CALL SHIFTR (ENVSTR)

C --- open output file
      CALL Findunit (10,CRP)
      OPEN (CRP,FILE=rmldsp(ENVSTR//FILNAM), STATUS=STASTR
     & ,ACCESS='SEQUENTIAL')

C --- write header
      WRITE (CRP,2010)
2010  FORMAT (
     &'*DATE       DAY ID LAI  RD  CRT0 PSTDM STDM  PHADM HADM *',/,
     &'*dd/mm/yyyy  nr         cm       kg/ha kg/ha kg/ha kg/ha*',/,
     &'*<============><==><===><==><===><====><====><====><====>')
      HDONE=.TRUE.

2100  CONTINUE

C --- Write output

C --- conversion of daynumber to date
      CALL NRTODA (YEAR,DAYNR,M,D)

C --- write output record
      WRITE (CRP,2110) D,M,YEAR,NINT(T),ID,LAI,NINT(RD),CRT0,
     &NINT(CPWDM(ID)),NINT(TAGP),NINT(CPWHM(ID)),NINT(TAGPT)
2110  FORMAT (I3,'/',I2.2,'/',2I4,I4,F5.2,I4,F5.2,4I6)
      ODONE = .TRUE.

C --- TERMINAL SECTION: write one more record & close output file
2500  IF (IFINCR.GT.0.AND.IPORWL.EQ.2) THEN
        IF (ODONE) THEN
          CLOSE (CRP)
        ELSE
C ---     conversion of daynumber to date
          CALL NRTODA (YEAR,DAYNR,M,D)
          WRITE (CRP,2110) D,M,YEAR,NINT(T),ID,LAI,NINT(RD),CRT0,
     &    NINT(CPWDM(ID)),NINT(TAGP),NINT(CPWHM(ID)),NINT(TAGPT)
          CLOSE (CRP)
        ENDIF
      ENDIF
 
      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE CROPS (ITASK,IPORWL,FLOUT,ID,DAYNR,YEAR,ENVSTR,STASTR,
     & CRPNR,CRPFIL,OUTNAM,ECRPY,ECRPD,RDS,TAV,TRA,PTRA,RELTR,KDIF,KDIR,
     & LAI,RD,IFINCR,ADCRH,ADCRL,DVS,HLIM1,HLIM2U,HLIM2L,HLIM3H,
     & HLIM3L,HLIM4,RSC,RDCTB,RDM,ECMAX,ECSLOP,COFAB,LOGF,SWGC,GC,
     & SWCF,CF,T,IDEV)
C ----------------------------------------------------------------------
C     Date               : 21/1/99                           
C     Purpose            : simple crop growth routine for SWAP 
C     Subroutines called : RDCRPS,SHIFTR,SHIFTL,NRTODA
C     Functions called   : AFGEN,LIMIT,STEPNR
C     File usage         : OUTNAM.CR#, file with crop growth results
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER   CRP,CRPNR,DAYNR,YEAR,M,D,ECRPY,ECRPD,STEPNR,SWGC
      INTEGER   I,ICGS,ID,IDEV,IFINCR,IPORWL,ITASK,LCC,LOGF,SWCF

      REAL      GCTB(72),CFTB(72),RDTB(72),KYTB(72),LIMIT,LAI,T
      REAL      CPTR(36),CTR(36),CRT(36),RELY(36),HELP(36),RDCTB(22)
      REAL      ADCRH,ADCRL,AFGEN,CPTR0,CRELY,CRT0,CTR0,DTSUM,DVR,DVS
      REAL      ECMAX,ECSLOP,PTRA,RD,RDS,RELTR,TAV,TBASE,TRA,TSUMAM
      REAL      HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,HLIM4,RDM,TSUMEA
      REAL      KDIF,KDIR,COFAB,RSC,GC,CF

      CHARACTER CRPFIL*8,OUTNAM*8,FILNAM*12,ENVSTR*50,STASTR*7
      CHARACTER EXT(3)

      character*80 rmldsp
      
      LOGICAL   ODONE,HDONE,FLOUT

      SAVE

      DATA EXT/'1','2','3'/
C ----------------------------------------------------------------------
      GOTO (1000,2000) ITASK

1000  CONTINUE

C --- INITIALIZATION ---------------------------------------------------

C --- read crop data
      CALL RDCRPS (CRPFIL,ENVSTR,IDEV,LCC,TSUMEA,TSUMAM,TBASE,
     & KDIF,KDIR,GCTB,SWGC,CFTB,SWCF,RDTB,KYTB,HLIM1,HLIM2U,HLIM2L,
     & HLIM3H,HLIM3L,HLIM4,RSC,ADCRH,ADCRL,ECMAX,ECSLOP,RDCTB,
     & COFAB,LOGF)

C --- development stage
      DVS = 0.0

C --- initial LAI or SC
      LAI = AFGEN (GCTB,72,DVS)
      If (SWGC.EQ.2) then
        GC  = LAI
        LAI = LAI*3
      Endif

C --- initial crop factor or crop height
      CF  = AFGEN (CFTB,72,DVS)

C --- maximum rooting depth & actual rooting depth [cm]
      RDM = 0.0
      DO 2 I = 1,36
2     IF (RDM.LT.RDTB(I*2)) RDM = RDTB(I*2)
      RDM = MIN (RDS,RDM)       
      RD  = MIN (RDM,AFGEN (RDTB,72,DVS))

C --- initial summation variables of the crop
      CPTR0 = 0.
      CTR0  = 0.

C --- init arrays with cum. pot. and act. transpiration 
      DO 4 I = 1,36
        CPTR(I) = 0.0
        CTR(I)  = 0.0
4     CONTINUE

C --- misc.
      IFINCR = 0
      IF (IPORWL.EQ.2) HDONE  = .FALSE.

      RETURN          

2000  CONTINUE

C --- RATES OF CHANGE OF THE CROP VARIABLES ----------------------------

C --- increase in temperature sum
      DTSUM = MAX (0.0,TAV-TBASE)

C --- development rate
      IF (IDEV.EQ.1) THEN
        DVR = 2.0/LCC
      ELSEIF (IDEV.EQ.2) THEN
        IF (DVS.LT.1.0) THEN
          DVR = DTSUM/TSUMEA
        ELSE
          DVR = DTSUM/TSUMAM
        ENDIF
      ENDIF

C --- determination of current growing stage
      DO 6 I = 1,36
6     HELP(I) = KYTB(2*I-1)
      ICGS = STEPNR (HELP,36,DVS)

C --- Water stress
      RELTR = LIMIT (0.0,1.0,TRA/PTRA)

C ----INTEGRALS OF THE CROP --------------------------------------------

C --- phenological development stage
      DVS = DVS+DVR

C --- leaf area index or soil cover fraction    
      LAI = AFGEN (GCTB,72,DVS)
      If (SWGC.EQ.2) then
        GC  = LAI
        LAI = LAI*3
      Endif

C --- crop factor or crop height
      CF = AFGEN (CFTB,72,DVS)

C --- rooting depth [cm]
      RD = MIN (RDM,AFGEN (RDTB,72,DVS))

C --- cumulative relative transpiration, total growing season 
      CPTR0 = CPTR0 + PTRA  
      CTR0  = CTR0  + TRA
      CRT0  = LIMIT (0.0,1.0,CTR0/CPTR0)

C --- cumulative relative transpiration, current growing stage
      CPTR(ICGS) = CPTR(ICGS) + PTRA
      CTR(ICGS)  = CTR(ICGS)  + TRA
      CRT(ICGS)  = LIMIT (0.0,1.0,CTR(ICGS)/CPTR(ICGS)) 

C --- relative yield per growing stage and cumulated
      CRELY = 1.0 
      DO 8 I = 1,ICGS
        RELY(I) = 1.0-((1.0-CRT(I))*KYTB(2*I))
        CRELY   = CRELY*RELY(I)
8     CONTINUE

C --- crop finish conditions                       
      IF (DVS.GE.2.0)                       IFINCR = 1 
      IF (YEAR.EQ.ECRPY.AND.DAYNR.EQ.ECRPD) IFINCR = 2 

C --- OUTPUT SECTION 

      ODONE = .FALSE.
      IF (.NOT.FLOUT.OR.IPORWL.EQ.1) GOTO 2500
      IF (HDONE)      GOTO 2100

C --- compose filename
      CALL SHIFTR (OUTNAM)
      FILNAM = OUTNAM//'.CR'//EXT(CRPNR)
      CALL SHIFTL (FILNAM)
      CALL SHIFTR (ENVSTR)

C --- open output file
      CALL FINDUNIT (10,CRP)
      OPEN (CRP,FILE=rmldsp(ENVSTR//FILNAM),STATUS=STASTR
     & ,ACCESS='SEQUENTIAL')

C --- write header
      WRITE (CRP,100)
100   FORMAT (
     $'*DATE       DAY ID DVS  LAI  CF/H  RD  CRT  RELY*',/,
     $'*dd/mm/yyyy  nr              -/cm  cm           *',/,
     $'*<============><==><===><===><====><==><===><===>')
      HDONE = .TRUE.

2100  CONTINUE

C --- Write output

C --- conversion of daynumber to date
      CALL NRTODA (YEAR,DAYNR,M,D)

C --- write output record
      WRITE (CRP,200) D,M,YEAR,NINT(T),ID,DVS,LAI,CF,NINT(RD),
     & CRT0,CRELY
200   FORMAT (I3,'/',I2.2,'/',2I4,I4,2F5.2,F6.1,I4,F5.2,F7.4)
CPD 200   FORMAT (I3,'/',I2.2,'/',2I4,I4,2F5.2,F6.1,I4,2F5.2)
      ODONE = .TRUE.

C --- TERMINAL SECTION: write one more record & close output file
2500  IF (IFINCR.GT.0.AND.IPORWL.EQ.2) THEN
        IF (ODONE) THEN
          CLOSE (CRP)
        ELSE IF (HDONE) THEN
C ---     conversion of daynumber to date
          CALL NRTODA (YEAR,DAYNR,M,D)
          WRITE (CRP,200) D,M,YEAR,NINT(T),ID,DVS,LAI,CF,
     &    NINT(RD),CRT0,CRELY
          CLOSE (CRP)
        ENDIF
      ENDIF

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE IRRIG (TASK,ENVSTR,STASTR,IRGNAM,OUTNAM,IRMODE,YEAR,
     & DAYNR,RELTR,ID,DVS,FLIRGE,FLIRGS,GIRD,ISUA,CIRR,
     & NUMNOD,DZ,DRZ,HLIM3L,HLIM3H,HLIM4,LAYER,HTABLE,THETLO,
     & H,DISNOD,FLGENU,COFGEN,THETAS,THETAR,ALFAMG,
     & CAPFIL,CRPNR,RUNNR,LOGF,FMAY,BAYRY)
C ----------------------------------------------------------------------
C     Date               : 12/01/98        
C     Purpose            : evaluate and schedule irrigations
C     Subroutines called : SHIFTR,SHIFTL,DATONR,NRTODA
C     Functions called   : STEPNR,THENODE
C     File usage         : IRGNAM.IRG, historical irrigations 
C                        : IRGNAM.CAP, timing and depth criteria
C                        : OUTNAM.SCH, scheduled irrigations
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

C --- global
      INTEGER   TASK,YEAR,DAYNR,ID,NUMNOD,LAYER(MACP)
      INTEGER   THETLO(MAHO),ISUA,CRPNR,RUNNR,LOGF,FMAY,BAYRY

      REAL      DZ(MACP),DISNOD(MACP+1),DRZ,RELTR,DVS,GIRD,CIRR
      REAL      HLIM3H,HLIM3L,HLIM4

      REAL*8    H(MACP),COFGEN(8,MAHO),HTABLE(MAHO,99)
      REAL*8    THETAS(MACP),THETAR(MACP),ALFAMG(MACP)

      CHARACTER ENVSTR*50,IRGNAM*8,OUTNAM*8,STASTR*7
      CHARACTER*8 CAPFIL(3,MAYRS)

      LOGICAL   FLIRGE,FLIRGS,FLGENU(MAHO)
C ----------------------------------------------------------------------
C --- local
      INTEGER   NOFPIR,IRG,CAP,SCH,M,D,NR,IIRDAT(3,MAIRG)
      INTEGER   TCS1,TCS2,TCS3,TCS4,TCS5,PHORMC,DCS1,DCS2,STEPNR
      INTEGER   ISUAS,NODE,NODDRZ,NODSEN,IEVENT,IDELTR,I,IRMODE
      INTEGER   IFND,SUA(MAIRG),dd(MAIRG),mm(MAIRG),yy(MAIRG)

      REAL      TPS1X(7),TPS2X(7),TPS3X(7),TPS4X(7),TPS5X(7)
      REAL      TPS1Y(7),TPS2Y(7),TPS3Y(7),TPS4Y(7),TPS5Y(7)
      REAL      DPS1X(7),DPS2X(7),DPS1Y(7),DPS2Y(7),RIRDAT(2,MAIRG)
      REAL      CIRRS,DEP,FRLOW,PHLO,PHHI,PHME,AWLH,AWMH,AWAH,CDEF
      REAL      WCLO,WCME,WCHI,WCAC,TPS1,TPS2,TPS3,TPS4,TPS5,DEPL,PHCRIT
      REAL      DCRIT,DPS1,DPS2
      REAL      depth(MAIRG),Conc(MAIRG)

      REAL*8    THENODE,PRHNODE

      CHARACTER FILNAM*12,LINE*80
      CHARACTER EXT(3)

      character*80 rmldsp

      LOGICAL   EXISTS,HDONE,BLANK,COMMENT

      SAVE

      DATA EXT/'1','2','3'/
C ----------------------------------------------------------------------
      GOTO (1000,2000,3000,4000) TASK

1000  CONTINUE

C --- INITIALIZATION part one ------------------------------------------

C --- Read file with irrigation gifts

C --- compose filename
      CALL SHIFTR (IRGNAM)
      FILNAM = IRGNAM//'.IRG'
      CALL SHIFTL (FILNAM)
      CALL SHIFTR (ENVSTR)

C --- check if a file with fixed irrigation data has been specified
      IF (FILNAM(1:4) .EQ. '.IRG' .OR. FILNAM .EQ. '        .IRG') THEN
        FLIRGE = .FALSE.
      ELSE
        FLIRGE = .TRUE.
      ENDIF

      IF (FLIRGE) THEN
C ---   check if a file with fixed irrigation gifts does exist
        INQUIRE (FILE=rmldsp(ENVSTR//FILNAM),EXIST=EXISTS)

        IF (.NOT.EXISTS) THEN
C ---     write error to log file
          WRITE (LOGF,122) ENVSTR//FILNAM
 122      FORMAT ('SWAP can not find the input file',/,A)
          STOP 'The .IRG file was not found: SWAP stopped !'
        ENDIF

C ---   read irrigation gifts and store in IRGDAT
        NOFPIR = 0
        Call FINDUNIT (38,IRG)
        OPEN (IRG,FILE=rmldsp(ENVSTR//FILNAM),status='old'
     & ,access='sequential')

C --- position file pointer
        IFND = 0
5       READ (IRG,'(A)') LINE
        CALL ANALIN (LINE,BLANK,COMMENT)
        IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 5
        IF (COMMENT) GOTO 15
          IFND = IFND+1
          BACKSPACE (IRG)
          READ (IRG,*) DD(IFND),MM(IFND),depth(IFND),conc(IFND),
     &    sua(IFND) 
        GOTO 5
C ---   ready...
15      CONTINUE

C ---   year is calculated
        DO 22 I = 1,IFND
          IF (mm(I).GE.FMAY) yy(I) = BAYRY
          IF (mm(I).LT.FMAY) yy(I) = BAYRY+1
22       CONTINUE

        Do 44 I= 1,IFND
          CALL DATONR (YY(I),MM(I),DD(I),NR)
          IIRDAT(1,I) = YY(I)
          IIRDAT(2,I) = NR
          RIRDAT(1,I) = depth(I)
          RIRDAT(2,I) = conc(I)
          IIRDAT(3,I) = sua(I)
44       CONTINUE
        CLOSE (IRG)
        NOFPIR = IFND

      ENDIF

      RETURN

C --- READ IRRIGATION CRITERIA (TIMING & DEPTH) - scheduling phase

2000  CONTINUE

C --- compose filename
      CALL SHIFTR (CAPFIL(CRPNR,RUNNR))
      FILNAM = CAPFIL(CRPNR,RUNNR)//'.CAP'
      CALL SHIFTL (FILNAM)
   
C --- check if a file with irrigation scheduling criteria has been specified
      IF (FILNAM(1:4) .EQ. '.CAP' .OR. FILNAM .EQ. '        .CAP') THEN
        FLIRGS = .FALSE.
      ELSE
        FLIRGS = .TRUE.
      ENDIF
     
      IF (FLIRGS) THEN
C ---   check if a file with irrigation scheduling criteria does exist
        INQUIRE (FILE=rmldsp(ENVSTR//FILNAM),EXIST=EXISTS)

        IF (.NOT.EXISTS) THEN
C ---     write error to log file
          WRITE (LOGF,126) ENVSTR//FILNAM
 126      FORMAT ('SWAP can not find the input file',/,A)
          STOP 'The .CAP file was not found: SWAP stopped !'
        ENDIF

C ---   read application method & timing and depth criteria
        Call FINDUNIT (38,CAP)  
        OPEN (CAP,FILE=rmldsp(ENVSTR//FILNAM),status='old'
     & ,access='sequential')

C ---   application method
        Call RSINTR (CAP,FILNAM,LOGF,'ISUAS',0,1,ISUAS)

C ---   solute concentration irrigation water
        CALL RSREAR (CAP,FILNAM,LOGF,'CIRRS',0.0,100.0,CIRRS)
        
C ===   TIMING criteria

C -1-   Timing - allowable daily stress
        Call RSINTR (CAP,FILNAM,LOGF,'TCS1',0,1,TCS1)
        IF (TCS1.EQ.1) THEN
          IFND = 0 
 55       READ (CAP,'(A)') LINE           
          CALL ANALIN (LINE,BLANK,COMMENT)
	  IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 55
          IF (COMMENT) GOTO 56
          IFND = IFND+1
          BACKSPACE (CAP)
          READ (CAP,*) TPS1X(IFND),TPS1Y(IFND)
          GOTO 55
        ENDIF
C ---   ready...
56      CONTINUE
        CALL JMPLBL (CAP,FILNAM,LOGF,'TCS2')

C -2-   Timing - depletion of readily available water
        CALL RSINTR (CAP,FILNAM,LOGF,'TCS2',0,1,TCS2)
        IF (TCS2.EQ.1) THEN
          IFND = 0 
 57       READ (CAP,'(A)') LINE           
          CALL ANALIN (LINE,BLANK,COMMENT)
          IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 57
          IF (COMMENT) GOTO 58
          IFND = IFND+1
          BACKSPACE (CAP)
          READ (CAP,*) TPS2X(IFND),TPS2Y(IFND)
          GOTO 57
        ENDIF
C ---   ready...
58      CONTINUE
        CALL JMPLBL (CAP,FILNAM,LOGF,'TCS3')

C -3-   Timing - depletion of totally available water
        CALL RSINTR (CAP,FILNAM,LOGF,'TCS3',0,1,TCS3)
        IF (TCS3.EQ.1) THEN
          IFND = 0 
 59       READ (CAP,'(A)') LINE           
          CALL ANALIN (LINE,BLANK,COMMENT)
          IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 59
          IF (COMMENT) GOTO 60
          IFND = IFND+1
          BACKSPACE (CAP)
          READ (CAP,*) TPS3X(IFND),TPS3Y(IFND)
          GOTO 59
        ENDIF
C ---   ready...
60      CONTINUE
        CALL JMPLBL (CAP,FILNAM,LOGF,'TCS4')

C -4-   Timing - allowable depletion amount            
        CALL RSINTR (CAP,FILNAM,LOGF,'TCS4',0,1,TCS4)
        IF (TCS4.EQ.1) THEN
          IFND = 0 
 61       READ (CAP,'(A)') LINE           
          CALL ANALIN (LINE,BLANK,COMMENT)
          IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 61
          IF (COMMENT) GOTO 62
          IFND = IFND+1
          BACKSPACE (CAP)
          READ (CAP,*) TPS4X(IFND),TPS4Y(IFND)
          GOTO 61
        ENDIF
C ---   ready...
62      CONTINUE
        CALL JMPLBL (CAP,FILNAM,LOGF,'TCS5')

C -5-   Timing - critical press. head or moist. content at sensor depth
        CALL RSINTR (CAP,FILNAM,LOGF,'TCS5',0,1,TCS5)
        IF (TCS5.EQ.1) THEN
          CALL RSINTR (CAP,FILNAM,LOGF,'PHORMC',0,1,PHORMC)
          CALL RSREAR (CAP,FILNAM,LOGF,'DCRIT',-100.0,0.0,DCRIT)
          IFND = 0 
 63       READ (CAP,'(A)') LINE           
          CALL ANALIN (LINE,BLANK,COMMENT)
          IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 63
          IF (COMMENT) GOTO 64
          IFND = IFND+1
          BACKSPACE (CAP)
          READ (CAP,*) TPS5X(IFND),TPS5Y(IFND)
          GOTO 63
        ENDIF
C ---   ready...
64      CONTINUE
        CALL JMPLBL (CAP,FILNAM,LOGF,'DCS1')

C ===   DEPTH criteria

C -1-   Depth - back to field capacity
        CALL RSINTR (CAP,FILNAM,LOGF,'DCS1',0,1,DCS1)
        IF (DCS1.EQ.1) THEN
          IFND = 0 
 65       READ (CAP,'(A)') LINE           
          CALL ANALIN (LINE,BLANK,COMMENT)
          IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 65
          IF (COMMENT) GOTO 66
          IFND = IFND+1
          BACKSPACE (CAP)
          READ (CAP,*) DPS1X(IFND),DPS1Y(IFND)
          GOTO 65
        ENDIF
C ---   ready...
66      CONTINUE
        CALL JMPLBL (CAP,FILNAM,LOGF,'DCS2')

C -2-   Depth - fixed depth
        CALL RSINTR (CAP,FILNAM,LOGF,'DCS2',0,1,DCS2)
        IF (DCS2.EQ.1) THEN
          IFND = 0 
 67       READ (CAP,'(A)') LINE           
          CALL ANALIN (LINE,BLANK,COMMENT)
          IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 67
          IF (COMMENT) GOTO 68
          IFND = IFND+1
          BACKSPACE (CAP)
          READ (CAP,*) DPS2X(IFND),DPS2Y(IFND)
          GOTO 67
        ENDIF
C ---   ready...
68      CONTINUE

        CLOSE (CAP)
      ENDIF

C --- miscellaneous
      HDONE = .FALSE.
      IDELTR = 1

      RETURN

3000  CONTINUE

C --- DRIVING VARIABLES ------------------------------------------------

C --- EVALUATION MODE - search for irrigation gift [cm]  

      IF (IRMODE.EQ.1.OR.IRMODE.EQ.2) THEN
        IEVENT = 0
        GIRD   = 0.0
        CIRR   = 0.0
        ISUA   = 0
        DO 84 I = 1,NOFPIR
          IF (YEAR.EQ.IIRDAT(1,I).AND.DAYNR.EQ.IIRDAT(2,I)) THEN
            GIRD = RIRDAT(1,I)/10.0
            CIRR = RIRDAT(2,I)
            ISUA = IIRDAT(3,I) 
            GOTO 88
          ENDIF
84      CONTINUE
88      CONTINUE
        IF (GIRD.GT.0.0) RETURN
      ENDIF

C --- SCHEDULING MODE - current timing and depth criterion

      IF (IRMODE.EQ.2) THEN
        IEVENT = 0
        GIRD   = 0.0
        CIRR   = CIRRS
        ISUA   = ISUAS

C ---   determine lowest compartment containing roots
        DEP = 0.0 
        DO 92 NODE = 1,NUMNOD
          NODDRZ = NODE
          DEP    = DEP - DZ(NODE)
          IF (DRZ.GE.DEP-1.0E-6) GOTO 96
92      CONTINUE
96      FRLOW = (DZ(NODDRZ)-(DRZ-DEP))/DZ(NODDRZ)

C ---   determine water holding capacity, readily available water, 
C ---   actual available water and water deficit
        PHLO = -100.0
        PHME = (HLIM3L+HLIM3H)/2
        PHHI = HLIM4
        AWLH = 0.0
        AWMH = 0.0
        AWAH = 0.0
        CDEF = 0.0
        DO 100 NODE = 1,NODDRZ
          WCLO = REAL(THENODE(NODE,DBLE(PHLO),LAYER,FLGENU,
     &           COFGEN,HTABLE,THETLO,ALFAMG,THETAR,THETAS))*DZ(NODE)
                 IF (NODE.EQ.NODDRZ) WCLO = WCLO*FRLOW
          WCME = REAL(THENODE(NODE,DBLE(PHME),LAYER,FLGENU,
     &           COFGEN,HTABLE,THETLO,ALFAMG,THETAR,THETAS))*DZ(NODE)
                 IF (NODE.EQ.NODDRZ) WCME = WCME*FRLOW
          WCHI = REAL(THENODE(NODE,DBLE(PHHI),LAYER,FLGENU,
     &           COFGEN,HTABLE,THETLO,ALFAMG,THETAR,THETAS))*DZ(NODE)
                 IF (NODE.EQ.NODDRZ) WCHI = WCHI*FRLOW
          WCAC = REAL(THENODE(NODE,H(NODE),LAYER,FLGENU,
     &           COFGEN,HTABLE,THETLO,ALFAMG,THETAR,THETAS))*DZ(NODE)
                 IF (NODE.EQ.NODDRZ) WCAC = WCAC*FRLOW
            
          AWLH = AWLH+(WCLO-WCHI)
          AWMH = AWMH+(WCME-WCHI)
          AWAH = AWAH+(WCAC-WCHI)
          CDEF = CDEF+(WCLO-WCAC) 
100     CONTINUE

C -1-   Timing - allowable daily stress
        IF (TCS1.EQ.1) THEN
          TPS1 = TPS1Y (STEPNR(TPS1X,7,DVS))
          IF ((RELTR.LT.TPS1).AND.(ID.GT.1).AND.(CDEF.GT.0)) IEVENT = 1
        ENDIF

C -2-   Timing - depletion of Readily Available Water (fraction)
        IF (TCS2.EQ.1) THEN
C ---     compare readily available water and actual available water
          TPS2 = TPS2Y (STEPNR(TPS2X,7,DVS))
          DEPL = TPS2*(AWLH-AWMH)
          IF (DEPL.GT.AWLH) DEPL=AWLH 
          IF (AWAH.LT.(AWLH-DEPL)) IEVENT=1
        ENDIF

C -3-   Timing - depletion of Totally Available Water (fraction)
        IF (TCS3.EQ.1) THEN
C ---     compare totally available water and actual available water
          TPS3 = TPS3Y (STEPNR(TPS3X,7,DVS))
          DEPL = TPS3*AWLH
          IF (AWAH.LT.(AWLH-DEPL)) IEVENT=1
        ENDIF

C -4-   Timing - allowable amount of depletion
        IF (TCS4.EQ.1) THEN
C ---     check if depletion amount has been exceeded                
          TPS4 = TPS4Y (STEPNR(TPS4X,7,DVS))/10.0
          IF ((AWLH-AWAH).GT.TPS4) IEVENT=1
        ENDIF

C -5-   Timing - critical pressure head or moisture content exceeded
        IF (TCS5.EQ.1) THEN
C ---     determine compartment number of sensor depth
          DEP = 0.0
          DO 110 NODE = 1,NUMNOD
            NODSEN = NODE
            DEP    = DEP - DZ(NODE)
            IF (-ABS(DCRIT).GE.DEP-1.0E-6) GOTO 114
110       CONTINUE

114       TPS5 = TPS5Y (STEPNR(TPS5X,7,DVS))
C ---     calculation of critical pressure head
          IF (PHORMC.EQ.0) THEN
            PHCRIT = -ABS(TPS5)
          ELSEIF (PHORMC.EQ.1) THEN
            PHCRIT = REAL(PRHNODE(NODSEN,DBLE(TPS5),LAYER,DISNOD,
     &               H,FLGENU,THETAR,THETAS,COFGEN,ALFAMG,HTABLE))
          ENDIF

C ---     compare critical pressure head and actual pressure head
          IF (REAL(H(NODSEN)).LE.PHCRIT) IEVENT = 1
        ENDIF

C ---   Depth - back to field capacity [cm]
        IF ((IEVENT.EQ.1).AND.(DCS1.EQ.1)) THEN
C ---     correct for over- or under irrigation
          DPS1 = DPS1Y (STEPNR(DPS1X,7,DVS))
          GIRD = MAX (0.0,CDEF+DPS1/10.0) 
        ENDIF

C ---   Depth - fixed depth [cm]
        IF ((IEVENT.EQ.1).AND.(DCS2.EQ.1)) THEN
          DPS2 = DPS2Y (STEPNR(DPS2X,7,DVS))
          GIRD = DPS2/10.0
        ENDIF

      ENDIF

C --- OUTPUT SECTION ---------------------------------------------------

C --- triggering on two consecutive days is prohibited
      IDELTR = IDELTR+1
      IF (IEVENT.EQ.0) GOTO 2500
      IF (IDELTR.EQ.1) THEN
        GIRD = 0.0
        GOTO 2500
      ELSE
        IDELTR = 0
      ENDIF

      GOTO (2500,2300) IRMODE 

C --- Write scheduled irrigations

2300  IF (HDONE) GOTO 2350

C --- compose filename
      CALL SHIFTR (OUTNAM)
      FILNAM = OUTNAM//'.SC'//EXT(CRPNR)
      CALL SHIFTL(FILNAM)

C --- open output file
      CALL FINDUNIT (38,SCH)
      OPEN (SCH,FILE=rmldsp(ENVSTR//FILNAM),STATUS=STASTR
     & ,ACCESS='SEQUENTIAL')

C --- write header
      WRITE (SCH,2310)
2310  FORMAT (
     &'*OUTNAM   DATE       ID DEPTH*',/,
     &'*         dd/mm/yyyy    mm   *',/,
     &'*<======><=============><====>')
      HDONE = .TRUE.

2350  CONTINUE

C --- Write output

C --- conversion of daynumber to date
      CALL NRTODA (YEAR,DAYNR,M,D)

C --- write output record
      WRITE (SCH,'(A8,I3,''/'',I2.2,''/'',2I4,I6)') OUTNAM,D,M,YEAR,ID,
     &INT(GIRD*10) 

2500  RETURN

4000  CONTINUE
 
C --- TERMINAL SECTION -------------------------------------------------

C --- close output file scheduling phase
      CLOSE (SCH)

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE METEO (T,DT,IPORWL,
     &  YEAR,DAYNR,WTHFIL,ENVSTR,LAT,ALT,KDIF,KDIR,LAI,GIRD,
     &  ISUA,RAD,TAV,TAVD,TMNR,RH,GRAI,NRAI,NIRD,ATMDEM,PTRA,PEVA,
     &  RAITIM,RAIFLX,FLRAI,ARFLUX,CFBS,RSC,SWETR,
     &  ISTAGE,ICRMOD,LOGF,SWSHF,FLRAIC,COFAB,FLRDME,SWGC,GC,SWRAI,
     &  IDEV,SWCF,CF,SWCFBS)
C ----------------------------------------------------------------------
C     Last modified      : 29/1/99              
C     Purpose            : returns daily values for the variables:
C                          solar radiation         := J/m2,
C                          average temperature     := C,
C                          average day temperature := C,
C                          7 day running av. min t := C,
C                          vapour pressure deficit := mbar
C                          relative humidity       := fraction,
C                          gross rainfall          := cm,
C                          net rainfall            := cm,
C                          net irr. depth          := cm,
C                          atmospheric demand      := cm,
C                          potential evaporation   := cm;
C                          potential transpiration := cm,
C     Subroutines called : SHIFTR,SHIFTL
C     Functions called   : LIMIT
C     File usage         : file with meteo data               
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER   YEAR,DAYNR,DAYNRF,DAYNRL,WTH,RAI,Y,M,D,SWSHF,SWGC,SWCF
      INTEGER   I,J,ICOUNT,SWETR,IPORWL,ISUA,NOFD,NR,ISTAGE,ICRMOD,LOGF
      INTEGER   SWRAI,IOST,IFND,IDEV,SWCFBS

      REAL      LIMIT,LAT,KDIF,LAI,NRAI,NIRD,RAITIM(100),RAIFLX(100)
      REAL      CRAI,CROLD,T,DT
      REAL      A,AINTC,ALT,ARFLUX,ATMDEM,B,CF,COFAB,COFBB
      REAL      ES0,ET0,ETR,EW0,GIRD,GRAI,HUM,PEVA,PTRA
      REAL      RAD,RCC,RCS,RFLUX,RH,RPD,SVP,TAV,TAVD,TIM,TIMOLD,TMN
      REAL      TMNR,TMX,WFRAC,WIN,KDIR,CFBS,RSC,GC

      CHARACTER WTHFIL*7,TEMP*4,CYEAR*4,ENVSTR*50,FILNAM*12 
      CHARACTER RAIFIL*8,LINE*80

      CHARACTER*8 ACHDUM(366),ACHDUMR(366),CHDUM

      character*80 rmldsp
      
      INTEGER   AD(366),AM(366),AY(366),ADR(366),AMR(366),AYR(366)
      INTEGER   DAYNUMBER,H,MN
      REAL      ARAD(366),ATMN(366),ATMX(366),ARADR(366),ATMNR(366),
     &          ATMXR(366),AHUM(366),AWIN(366),ARAI(366),AHUMR(366),
     &          AWINR(366),ARAIR(366),AETR(366),AETRR(366)

      LOGICAL   FLRAI,EXISTS,FLRAIC,FLRDME,BLANK,COMMENT

      SAVE

      DATA      RCS/0.15/,RCC/0.23/
C ----------------------------------------------------------------------

C *** Read meteo data file if flag FLRDME has been set *****************
C *** FLRDME is set in TIMER & reset here, after reading the meteo file 

      IF (FLRDME) THEN

C ---   Compose filename
        CALL SHIFTR (WTHFIL)
        WRITE (TEMP,'(I4)') YEAR
        READ  (TEMP,'(A4)') CYEAR

C ---   remove possible blanks
        DO 2  I = 1,4
 2      IF (CYEAR(I:I).EQ.' ') CYEAR(I:I) = '0'
 
        FILNAM = WTHFIL//'.'//CYEAR(2:4)
        CALL SHIFTL (FILNAM)
        CALL SHIFTR (ENVSTR)
    
C --- check if a file with daily meteorological data does exist
      INQUIRE (FILE=rmldsp(ENVSTR//FILNAM),EXIST=EXISTS)

      IF (.NOT.EXISTS) THEN
C ---   write error to log file
        WRITE (LOGF,92) ENVSTR//FILNAM
 92     FORMAT ('SWAP can not find the input file',/,A)
        STOP 'Meteorological data file was not found: SWAP stopped!'
      ENDIF

c ---   open meteo-file
        Call FINDUNIT (50,WTH)  
        OPEN (WTH,FILE=rmldsp(ENVSTR//FILNAM),status='old',
     &  access='sequential')

        IFND = 0
102     READ (WTH,'(A)',IOSTAT = IOST) LINE
        IF (IOST.LT. 0) GOTO 200
        CALL ANALIN (LINE,BLANK,COMMENT)
        IF (BLANK.OR.COMMENT) GOTO 102

        IFND = IFND+1
        BACKSPACE (WTH)
        READ (WTH,*) ACHDUMR(IFND),ADR(IFND),AMR(IFND),AYR(IFND),
     &  ARADR(IFND),ATMNR(IFND),ATMXR(IFND),AHUMR(IFND),AWINR(IFND),
     &  ARAIR(IFND),AETRR(IFND)

C ---   next record...
        GOTO 102

C ---   Close meteo file
200     Close (WTH)

        CALL DATONR (YEAR,AMR(1),ADR(1),DAYNRF) 
        CALL DATONR (YEAR,AMR(IFND),ADR(IFND),DAYNRL) 

C ---   position data in arrays
        J = DAYNRF
        DO 4 I = 1,IFND
          ACHDUM(J) = ACHDUMR(I)
          AD(J)     = ADR(I)
          AM(J)     = AMR(I)
          AY(J)     = YEAR
C ---     check date 
          CALL DATONR (AY(J),AM(J),AD(J),DAYNUMBER)
          IF (DAYNUMBER.NE.J) THEN 
		  WRITE (*,202) FILNAM,AD(J),AM(J)
		  WRITE (LogF,202) FILNAM,AD(J),AM(J)
 202        FORMAT('In meteo file ',A,'the date of ',i2,'/',i2,1x,
     &             'is not correct!')
            STOP   'First adapt meteo file'
          ENDIF

          ARAD(J)   = ARADR(I)
          ATMN(J)   = ATMNR(I)
          ATMX(J)   = ATMXR(I)
          AHUM(J)   = AHUMR(I)
          AWIN(J)   = AWINR(I)
          ARAI(J)   = ARAIR(I)
          AETR(J)   = AETRR(I)
          J = J+1
4       Continue

        FLRDME = .FALSE.
      ENDIF

C *** End of reading meteo data file *************************************************

c --- the weather for today     

      CALL NRTODA (YEAR,DAYNR,M,D)
      Y = YEAR

      IF (DAYNR.LT.DAYNRF.OR.DAYNR.GT.DAYNRL)
     &  STOP 'METEO - no meteo data for today available'

      RAD  = ARAD(DAYNR)
      TMN  = ATMN(DAYNR)
      TMX  = ATMX(DAYNR)
      HUM  = AHUM(DAYNR)
      WIN  = AWIN(DAYNR)
      GRAI = ARAI(DAYNR)
      ETR  = AETR(DAYNR)
 
C --- Calculate running average of minimum temperature ----------------- 
      NOFD = MIN(DAYNR-DAYNRF+1,7)
      TMNR = 0.0
      DO 10 I = DAYNR-NOFD+1,DAYNR
        TMNR = TMNR + ATMN(I)/NOFD
 10   CONTINUE

C --- Detection & handling of missing values ---------------------------

C -1- missing value for rainfall is never allowed
      IF (GRAI.LT.-98.0) THEN
C ---   write error to log file
        WRITE (LOGF,'(I2,''/'',I2.2,''/'',I4,'' - RAI missing'')')
     &  D,M,Y
        STOP 'METEO input error - RAI missing'
      ENDIF

C -2- no missing values allowed if PENMON must be executed
      IF (SWETR.EQ.0.OR.(SWETR.EQ.1.AND.ETR.LT.-98.0)) THEN
        IF (RAD.LT.-98.0.OR.TMN.LT.-98.0.OR.TMX.LT.-98.0.OR.
     &  HUM.LT.-98.0.OR.WIN.LT.-98.0) THEN
C ---     write error to log file
          WRITE (LOGF,'(I2,''/'',I2.2,''/'',I4,'' - RAD,TMN,TMX,HUM '',
     &    '' or WIN missing'')') D,M,Y
          STOP 'METEO input error - RAD,TMN,TMX,HUM or WIN missing'
        ENDIF
      ENDIF

C -3- no missing values for TMN and TMX allowed if cropD is present or
C --- numerical soil temperatures or cropS development must be simulated
      IF ((ISTAGE.EQ.2.AND..NOT.(ICRMOD.EQ.1.AND.IDEV.EQ.1))
     &.OR.(ISTAGE.EQ.1.AND.(SWSHF.EQ.2.AND.IPORWL.EQ.2))) THEN
        IF (TMN.LT.-98.0.OR.TMX.LT.-98.0) THEN
C ---     write error to log file
          WRITE (LOGF,'(I2,''/'',I2.2,''/'',I4,''- TMN or TMX missing'')
     &     ') D,M,Y
          STOP 'METEO input error - TMN or TMX missing'
        ENDIF
      ENDIF

C -4- no missing value for RAD allowed in case the detailed crop model
C --- or the grass routine is active 
      IF (ISTAGE.EQ.2.AND.(ICRMOD.EQ.2.OR.ICRMOD.EQ.3)) THEN
        IF (RAD.LT.-98.0) THEN
C ---     write error to log file
          WRITE (LOGF,'(I2,''/'',I2.2,''/'',I4,'' - RAD missing'')')
     &    D,M,Y
          STOP 'METEO input error - RAD missing'
        ENDIF
      ENDIF

C -5- if HUM is missing or TAV cannot be calculated: set RH at -99.0
      RH = 1.0
      IF (HUM.LT.-98.0.OR.TMN.LT.-98.0.OR.TMX.LT.-98.0) RH = -99.0

C -6- error in case ETRef missing
      IF (SWETR.EQ.1.AND. ETR.LT.-0.00001) THEN
C ---   write error to log file
        WRITE(LOGF,'(I2,''/'',I2.2,''/'',I4,''- ETRef missing'')') 
     &  D,M,Y
        STOP 'METEO input error - ETRef missing'
      ENDIF  

C --- End of handling missing values -----------------------------------

C --- convert radiation from kJ/m2 to J/m2
      RAD = RAD*1000

C --- calculate 24h average temperature
      TAV  = (TMX+TMN)/2
C --- calculate average day temperature
      TAVD = (TMX+TAV)/2

      IF (RH.GE.-98.0) THEN
C ---   calculate saturated vapour pressure [kPa]
        SVP = 0.611*EXP(17.4*TAV/(TAV+239.))
C ---   calculate relative humidity [fraction]
        RH  = MIN(HUM/SVP,1.0)
C ---   calculate vapour pressure deficit [mbar]
c       VPD = (SVP-HUM)*10
      ENDIF
 
C --- gross rainfall in cm
      GRAI = GRAI/10.0

C --- Calculation of Net RAIn & Net IRrigation Depth [cm] --------------

      IF (LAI.LT.0.001) THEN
C --- no vegetation
        NRAI = GRAI
        NIRD = GIRD
      ELSE

C --- Calculate interception, method H.Braden

        RPD = GRAI*10.0
        IF (ISUA.EQ.0) RPD = (GRAI+GIRD)*10.0

        COFBB = MIN (LAI/3.0,1.0)
        AINTC = (COFAB*LAI*(1.0-(1/(1.0+RPD*COFBB/(COFAB*LAI)))))/10.0

C --- divide interception into rain part and irrigation part

        IF (AINTC.LT.0.001) THEN
          NRAI = GRAI          
          NIRD = GIRD
        ELSE
           IF (ISUA.EQ.0) THEN
             NRAI = GRAI-AINTC*(GRAI/(GRAI+GIRD)) 
             NIRD = GIRD-AINTC*(GIRD/(GRAI+GIRD)) 
           ELSE 
             NRAI = GRAI-AINTC
             NIRD = GIRD
           ENDIF
        ENDIF
  
      ENDIF

C ----------------------------------------------------------------------
C --- calculation of Angstrom coefficients A and B
      A = 0.4885-0.0052*LAT
      B = 0.1563+0.0074*LAT

C --- Calculate evapotranspiration: ET0, EW0, ES0

C --- reference evapotranspiration has been specified 
      IF (SWETR.EQ.1) THEN
        If (Istage.EQ.1) then
C ---   no crop 
          ET0 = 0.0
          EW0 = 0.0
          ES0 = ETR
          if (SWCFBS.EQ.1) ES0 = CFBS*ETR
        elseif (Istage.EQ.2) then
C ---   yes crop
          if (SWCF.EQ.1) then 
            ET0 = CF*ETR
            EW0 = CF*ETR
          else
            ET0 = ETR
            EW0 = ETR
          endif 
          ES0 = ETR
          if (SWCFBS.EQ.1) ES0 = CFBS*ETR
        endif   
C --- reference evapotranspiration must be calculated
      ELSE
        IF (RAD.GT.9.9999E7) THEN
C ---     write error to log file
          WRITE(LOGF,'(I2,''/'',I2.2,''/'',I4,''- RAD missing'')') 
     &    D,M,Y
          STOP 'METEO input error - RAD missing'
        ENDIF  
        CALL PENMON (DAYNR,LAT,ALT,A,B,RCS,RCC,RAD,TAV,HUM,
     &  WIN,RSC,ES0,ET0,EW0,SWCF,CF,IStage)
        If (Istage.EQ.1) then
C ---     no crop 
          ET0 = 0.0
          EW0 = 0.0
          if (SWCFBS.EQ.1) ES0 = CFBS*ES0
        elseif (Istage.EQ.2) then
C ---     yes crop
          if (SWCF.EQ.1) then 
            ET0 = CF*ET0
            EW0 = CF*EW0
          endif 
          if (SWCFBS.EQ.1) ES0 = CFBS*ET0
        ENDIF
      ENDIF

C --- ET0, EW0 and ES0 are always defined !

C --- Calculate atmospheric demand [cm]
      ATMDEM = ET0/10

C --- Calculate fraction of the day the crop is wet
      IF (EW0.LT.0.0001) THEN 
        WFRAC = 0.0 
      ELSE
        WFRAC = LIMIT (0.0,1.0,AINTC*10.0/EW0)
      ENDIF

C --- Potential soil evap. (PEVA) & transpiration (PTRA) [cm]
      PEVA = MAX (0.0,ES0*EXP(-1.*KDIR*KDIF*LAI))/10.
      PTRA = MAX (1.0E-9,(1.0-WFRAC)*ET0-PEVA*10)/10. 
C --- alternative (simple model, soil cover fraction specified)
        IF (ISTAGE.EQ.2.AND.ICRMOD.EQ.1.AND.SWGC.EQ.2) THEN
          PEVA = (1.0-GC)*(1.0-WFRAC)*ES0/10.0
          PTRA = MAX(1.0E-9,GC*(1.0-WFRAC)*ET0)/10.0
        ENDIF

C ----------------------------------------------------------------------
C --- Detailed rainfall      
   
      FLRAI = .FALSE.
      IF (SWRAI.EQ.1) THEN
        IF (IPORWL.EQ.2) THEN

          DO 16 I = 1,100
            RAITIM(I) = 2.0       
            RAIFLX(I) = 0.0
16        CONTINUE
          TIMOLD = 0.0
          CROLD  = 0.0
          ICOUNT = 1

          CALL SHIFTR(WTHFIL)
          RAIFIL = WTHFIL//'R'
          FILNAM = RAIFIL//'.'//CYEAR(2:4)
          CALL SHIFTL(FILNAM)

C ---     check if a file with detailed rainfall data does exist
          INQUIRE (FILE=rmldsp(ENVSTR//FILNAM),EXIST=EXISTS)

          IF (.NOT.EXISTS) THEN
C ---       write error to log file
            WRITE (LOGF,93) ENVSTR//FILNAM
 93         FORMAT ('SWAP can not find the input file',/,A)
            STOP 'Detailed rainfall file was not found: SWAP stopped'

          ELSE
            Call FINDUNIT (50,RAI)  
            OPEN (RAI,FILE=rmldsp(ENVSTR//FILNAM),STATUS='OLD',
     &      ACCESS='SEQUENTIAL') 

20          READ (RAI,'(A)',IOSTAT=IOST) LINE
            IF (IOST.LT. 0) GOTO 100
            CALL ANALIN (LINE,BLANK,COMMENT)
            IF (BLANK.OR.COMMENT) GOTO 20

            BACKSPACE (RAI)
            READ (RAI,*) CHDUM,D,M,Y,H,MN,CRAI
            CALL DATONR (Y,M,D,NR)

            IF (NR.NE.DAYNR.AND.FLRAI) GOTO 100
            IF (NR.NE.DAYNR) GOTO 20

            FLRAI = .TRUE.

            TIM   = H/24.0 + MN/1440.0

C ---       skip record if time does not proceed (TIM-TIMOLD ~ 0)
            IF (TIM-TIMOLD.LT.1.0E-6) GOTO 20

            IF (GRAI.LT.0.000001) THEN
              RFLUX = 0.0
            ELSE
              RFLUX = (((CRAI-CROLD)/(TIM-TIMOLD)) * (NRAI/GRAI))/10.0 
            ENDIF
            RAITIM (ICOUNT) = TIMOLD
            RAIFLX (ICOUNT) = RFLUX

            TIMOLD = TIM
            CROLD  = CRAI
            ICOUNT = ICOUNT+1
            GOTO 20     

C ---       end of file reached
100         CLOSE (RAI)

C ---       period from last recording till end of the day
            IF (FLRAI) THEN
              IF (ABS(TIM-1.0).GT.1/1440.0) THEN
                RAITIM (ICOUNT) = TIM
                RAIFLX (ICOUNT) = 0.0
              ENDIF
            ENDIF 

          ENDIF
        ENDIF
      ENDIF

C --- actual rain flux
      IF (FLRAI) THEN
        ARFLUX = RAIFLX(1)
      ELSE
        ARFLUX = NRAI
      ENDIF

C --- check time step for next rain record 
      IF (T+DT .GT. (INT(T)+RAITIM(2))-1.0E-4 .AND. 
     &    RAIFLX(1) .GT. 1.E-6) THEN
        DT     = (INT(T)+RAITIM(2))-T
        FLRAIC = .TRUE.
      ENDIF

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE SOIL(ITASK,RUNNR,ISEQ,FLOUT,FL1ST,FLLAST,ENVSTR,
     &  STASTR,OUTFIL,BBCFIL,DRFIL,BAYRY,BAYRD,DAYNR,ECMAX,
     &  ECSLOP,DAYSTA,YEAR,NUMLAY,NUMNOD,DZ,CIRR,T,TCUM,DT,DRZ,GRAI,
     &  GIRD,PEVA,PTRA,THETA,H,THETM1,TAV,DQROT,DPTRA,ADCRL,ADCRH,
     &  ATMDEM,LAYER,HTABLE,THETLO,DISNOD,NRAI,NIRD,FLGENU,COFGEN,
     &  THETAS,THETAR,ALFAMG,ARFLUX,SWSOLU,DTSOLU,DTMAX,DTMIN,
     &  SWNUMS,NUMBIT,THETOL,QTOP,
     &  HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,HLIM4,RDCTB,RDM,
     &  BRUNY,ERUNY,BRUND,ERUND,SWHEA,WLS,RSRO,SWDRA,POND,PONDMX,
     &  FLRAIC,AFO,AUN,ATE,AIR,PERIOD,
     &  SWREDU,COFRED,RSIGNI,SWSCAL,ISCLAY,SWHYST,TAU,
     &  SWVAP,SWDRF,SWSWB,SWAFO,AFONAM,SWAUN,AUNNAM,SWATE,ATENAM,
     &  SWAIR,AIRNAM,LOGF,SWSCRE,SWSHF,
     &  PRJNAM,BOTCOM,SOLFIL,PSAND,PSILT,PCLAY,ORGMAT,
     &  FSCALE,SWMOBI,PF1,FM1,PF2,FM2,THETIM,SWCRACK,SHRINA,
     &  MOISR1,MOISRD,ZNCRACK,GEOMF,DIAMPOL,RAPCOEF,DIFDES,SWDIVD,
     &  COFANI,SWINCO,HI,GWLI,FMAY,THETCR,FLENDD,YEARP,DAYNRP)

C ----------------------------------------------------------------------
C     Date      : 18/08/98
C     Purpose   : SWAP soil submodel
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

      INTEGER   ITASK,RUNNR,ISEQ,SWNUMS,SWHEA,SWDRF,SWSWB,LOGF,FMAY
      INTEGER   SWREDU,NUMLAY,NUMNOD,BOTCOM(MAHO),SWSCAL,SWMOBI
      INTEGER   SWSHF,SWSRF,SWB,DRF,SWBR,SWSCRE

      INTEGER   ISCLAY,SWHYST,SWDRA,SWSOLU,SWINCO,SWVAP,SWCRACK
      INTEGER   BAYRD,BAYRY,SWBOTB,THETLO(MAHO),THETHI(MAHO),LAYER(MACP)
      INTEGER   INDEKS(MACP),SWALLO(5),SWDTYP(5),NPEGWL,YEARP,DAYNRP
      INTEGER   NRPRI,NRSEC,NRSRF,SWQHR,NQH(10),SWSEC,NODHD(10)
      INTEGER   NRLEVS,DAYNR,YEAR,OUTPER,LEVEL,N,IMPER,YEAR1,DAYNR1
      INTEGER   DAYSTA,WBA,VAP,SBA,TEP,NUMBIT,DRAMET,DAT,INC
      INTEGER   NMPER,IMPEND(10),SWMAN(10),NPHASE(10),INTWL(10),NODGWL
      INTEGER   NNCRACK,DNOCON,I,BRUNY,ERUNY,BRUND,ERUND,IPOS,NUMADJ
      INTEGER   SWAFO,SWAUN,SWATE,SWAIR,AFO,AUN,ATE,AIR,PERIOD,SWDIVD

      REAL      PONDMX,HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,FSCALE(MAYRS)
      REAL      HLIM4,CPRE,CMLI(MACP),DDIF,LDIS,TSCF,KF,CREF
      REAL      FREXP,KMOBIL,DECPOT,GAMPAR,RTHETA,BEXP,TAMPLI
      REAL      TMEAN,DDAMP,TIMREF,FDEPTH(MAHO),FMOBIL(MACP),PF1(MAHO)
      REAL      FM1(MAHO),HDRAIN,GWLINP
      REAL      PF2(MAHO),FM2(MAHO),SLOPFM(MAHO),QIMMOB(MACP),GWLI
      REAL      GWLTAB(732),SHAPE,RIMLAY,AQAVE,AQAMP,AQTAMX,AQOMEG
      REAL      QBOTAB(732),COFQHA,COFQHB,HGITAB(50)
      REAL      DZ(MACP),Z(MACP),DISNOD(MACP+1),INPOLA(MACP)
      REAL      INPOLB(MACP),T,TCUM,QCOMP,QDARCY,CQDARCY
      REAL      GWL,GWLBAK(4),RSRO,ORGMAT(MAHO)
      REAL      CML(MACP),CIL(MACP),CL(MACP),CMSY(MACP),CISY(MACP)
      REAL      INQROT(MACP),INQ(MACP+1),INQDRA(5,MACP),IQROT,IQDRA
      REAL      IINTC,AFGEN,PSAND(MAHO),PSILT(MAHO),PCLAY(MAHO)
      REAL      IPTRA,IPEVA,IEVAP,IRUNO,IPREC,IQBOT,IGRAI,IGIRD
      REAL      QBOT,DT,QROT(MACP),QDRA(5,MACP),TEMPI(MACP)
      REAL      POND,L(5),ZBOTDR(5),OWLTAB(5,2*MAOWL)
      REAL      BASEGW(2),WETPER(5),DRARES(5),QDRTAB(50)
      REAL      CQROT,CQDRA,CQBOT,CQTOP,CPTRA,CPEVA,CEVAP,CRUNO
      REAL      CGRAI,CNRAI,CGIRD,CNIRD,CUMTOP,CUMBOT
      REAL      REVA,PEVA,GRAI,NRAI,GIRD,NIRD,TAV,DTSOLU
      REAL      ECMAX,ECSLOP,ADCRH,ADCRL,ATMDEM,THETOL,DTMAX,DTMIN
      REAL      WIDTHR(5),TALUDR(5),RDRAIN(5),RINFI(5),RENTRY(5)
      REAL      REXIT(5),GWLINF(5),WLPTAB(2*MAWLP),WLS,WLSTAR,WLP
      REAL      WLDIP(10)
      REAL      HQHTAB(10,10),QQHTAB(10,10),WLSMAN(10,10),HDEPTH(10)
      REAL      HBWEIR(10),ALPHAW(10),BETAW(10),DROPR(10),GWLCRIT(10,10)
      REAL      WSCAP(10),WLSTAB(2*MAWLS),STTAB(22,2),WSTINI,WST,QDRTOT      
      REAL      DRAINL(5),QDRAIN(5),CQDRAIN(5),RDCTB(22),RDM,VTAIR
      REAL      HCRIT(10,10),VCRIT(10,10),cqdrd,cwsupp,cwout,HWLMAN
      REAL      SHRINA,MOISR1,MOISRD,ZNCRACK,GEOMF,DIAMPOL,RAPCOEF
      REAL      SHRINB,SHRINC,THETCR(MAHO),ACRACK,QCRACK,RAPDRA,WTOPLAT
      REAL      ADSFLU(MACP),IQDRAR,IQCRACK,CQDRAR,CQCRACK,CRACKW
      REAL      SQPREC,SQIRRIG,PONDM1,CPOND,CRACKC,CKWM1,SOLBAL
      REAL      ARFLUX,CIRR,DPTRA,DQROT,DRZ,DTRA,PTRA,QTOP
      REAL      RUNOTS,WLSBAK(4),OSSWLM,HSURF,CRALEV,DIFDES
      REAL      HAQUIF,POROS,KFSAT,DECSAT,CDRAIN,SAMINI,DECTOT,ROTTOT
      REAL      SAMPRO,SAMCRA,SQBOT,SQDRA,SQSUR,SQRAP,SAMAQ
      REAL      KHTOP,KHBOT,KVTOP,KVBOT,ENTRES,ZINTF,GEOFAC,INFRES(5)
      REAL      QDRD,QROSUM,COFRED,RSIGNI,COFANI(MAHO),SDRAIN
      REAL      BDENS(MAHO),FQUARTZ(MACP),FCLAY(MACP),FORG(MACP),WLSOLD

      REAL*8    TAU,THETIM(MAHO),THETAI(MACP),HI(MACP),HTABLE(MAHO,99)
      REAL*8    KTABLE(MAHO,99),TEMP(MACP) 
      REAL*8    THETSL(MAHO),KSAT(MAHO),DMCH(MAHO,99),DMCC(MAHO,99)
      REAL*8    COFGEN(8,MAHO)
      REAL*8    KSE99(MAHO),THETAS(MACP),THETAR(MACP),ALFAMG(MACP)
      REAL*8    THETA(MACP),H(MACP),VOLM1,VOLACT,VOLINI,VOLSAT
      REAL*8    THETM1(MACP)
      REAL*8    HM1(MACP),DIMOCA(MACP),K(MACP+1),KMEAN(MACP+1),Q(MACP+1)

      CHARACTER ENVSTR*50,OUTFIL*8,BBCFIL*8,DRFIL*8,STASTR*7
      CHARACTER*8 SOLFIL(MAHO)
      CHARACTER*8 AFONAM,AUNNAM,ATENAM,AIRNAM,PRJNAM

      character*80 rmldsp
      
      LOGICAL   FLGENU(MAHO),HWBAD,HVAPD,HSBAD,HAFOD,HAUND,HTEPD,FLTSAT
      LOGICAL   FL1ST,FLLAST,FLOUT,FTOPH,HSWBD,HDRFD,FLRAIC,HLEVD
      LOGICAL   FLREVA,OVERFL,HATED,HAIRD,FLENDD,HINCD,FPEGWL

      SAVE

C ----------------------------------------------------------------------
      GOTO (1000,2000,3000,4000) ITASK

1000  CONTINUE

C --- INITIALIZATION ---------------------------------------------------

      QTOP = 0.0

      IF (RUNNR.EQ.1.OR.ISEQ.EQ.0) then 
        IF (SWSOLU.EQ.1) THEN
          CALL RDSLT (PRJNAM,ENVSTR,LOGF,CPRE,CMLI,DDIF,LDIS,TSCF,KF,
     &    FREXP,CREF,DECPOT,GAMPAR,RTHETA,BEXP,FDEPTH,KMOBIL,
     &    HAQUIF,POROS,KFSAT,DECSAT,CDRAIN,NUMNOD,NUMLAY,SWBR)
        ENDIF
        IF (SWHEA.EQ.1) THEN
          CALL RDHEA (PRJNAM,ENVSTR,LOGF,SWSHF,TAMPLI,TMEAN,DDAMP,
     &    TIMREF,TEMPI,NUMNOD)
        ENDIF
      ENDIF

C --- read input file containing bottom boundary conditions
      CALL RDBBC (BBCFIL,ENVSTR,BAYRD,BAYRY,GWLTAB,SHAPE,RIMLAY,AQAVE,
     & AQAMP,AQTAMX,AQOMEG,QBOTAB,COFQHA,COFQHB,HGITAB,SWBOTB,LOGF,YEAR,
     & FMAY,HDRAIN)

C --- First year only
      IF (RUNNR.EQ.1.OR.ISEQ.EQ.0) THEN
        CALL INITSOL (NUMLAY,SOLFIL,ENVSTR,FLGENU,THETHI,THETLO,
     & HTABLE,KTABLE,THETSL,KSAT,DMCH,DMCC,COFGEN,SWSCAL,ISCLAY,RUNNR,
     & KSE99,NUMNOD,DZ,Z,DISNOD,INPOLB,INPOLA,BOTCOM,
     & LAYER,THETAS,THETAR,SWHYST,INDEKS,ALFAMG,SWINCO,THETA,
     & THETAI,H,SWBOTB,HGITAB,T,HI,GWLTAB,GWLI,GWL,GWLBAK,
     & SWSOLU,CMLI,CML,CIL,SAMINI,PSAND,PSILT,PCLAY,ORGMAT,
     & CL,CMSY,KF,FREXP,CISY,VOLM1,VOLACT,VOLINI,VOLSAT,CREF,
     & THETM1,HM1,DIMOCA,K,KMEAN,THETIM,SWMOBI,FMOBIL,KMOBIL,PF1,FM1,
     & PF2,FM2,SLOPFM,QIMMOB,SWCRACK,SHRINA,MOISR1,MOISRD,ZNCRACK,
     & SHRINB,SHRINC,NNCRACK,ACRACK,QCRACK,RAPDRA,WTOPLAT,ADSFLU,
     & CKWM1,LOGF,FSCALE,DT,POND,BDENS,FQUARTZ,FCLAY,FORG)

        DO 8 I = 1,NUMLAY
          IF (.NOT.FLGENU(I).AND.SWHYST.NE.0)
     &    STOP 'Hysteresis option not allowed'
8       CONTINUE

        CALL ZEROINTR (NUMNOD,INQROT,INQ,INQDRA,IQROT,IQDRA,IINTC,
     &  IPTRA,IPEVA,IEVAP,IRUNO,IPREC,IQBOT,OUTPER,IQDRAR,IQCRACK,
     &  IGRAI,IGIRD)

        IF (SWHEA.EQ.1) THEN
	    IF (SWSHF.EQ.1) THEN 
C ---       Analytical solution soil temperatures
	      CALL SOILTMP (NUMNOD,THETA,THETM1,THETAS,TAV,
     &      SWSHF,TEMP,DZ,DISNOD,DT,TAMPLI,TMEAN,
     &      DDAMP,TIMREF,DAYNR,Z,FQUARTZ,FCLAY,FORG)
          ELSE
C ---       Numerical solution soil temperatures
            DO 10 I = 1,NUMNOD
 10         TEMP(I) = TEMPI(I)
          ENDIF
        ENDIF

        HAFOD = .FALSE.
        HAUND = .FALSE.
        HATED = .FALSE.
        HAIRD = .FALSE.
      ENDIF

C --- misc.
      HTEPD = .FALSE.
      HWBAD = .FALSE.
	HINCD = .FALSE.
      HVAPD = .FALSE.
      HSBAD = .FALSE.
      HDRFD = .FALSE.
      HSWBD = .FALSE.
      HLEVD = .FALSE.

C --- read input file(s) containing drainage & surface water system par.
      IF (SWDRA.EQ.1) THEN
        CALL RDDRB (DRFIL,ENVSTR,BAYRD,BAYRY,DRAMET,
     &  IPOS,BASEGW,KHTOP,KHBOT,KVTOP,KVBOT,ZINTF,L,WETPER,ZBOTDR,
     &  ENTRES,GEOFAC,NRLEVS,DRARES,INFRES,SWALLO,SWDTYP,OWLTAB,QDRTAB,
     &  LOGF,FMAY,SWDIVD)
      ELSEIF (SWDRA.EQ.2) THEN
        CALL RDDRE (DRFIL,ENVSTR,RSRO,NRSRF,NRPRI,NRSEC,L,
     &  ZBOTDR,WIDTHR,TALUDR,RDRAIN,RINFI,RENTRY,REXIT,GWLINF,SWDTYP,
     &  WLPTAB,BAYRD,BAYRY,SWSEC,WLS,OSSWLM,NMPER,
     &  WLSTAR,IMPEND,SWMAN,WSCAP,SWQHR,HBWEIR,ALPHAW,BETAW,NQH,HQHTAB,
     &  QQHTAB,DROPR,WLSMAN,GWLCRIT,WLSTAB,STTAB,WSTINI,WST,T,WLSBAK,
     &  SWSRF,NPHASE,HCRIT,HDEPTH,VCRIT,WLP,NODHD,NUMNOD,DZ,WLDIP,
     &  NUMADJ,LOGF,FMAY,INTWL)
        NRLEVS = NRSRF
        IF (SWSWB.EQ.1) THEN
          CALL OUTSWB (OUTFIL,SWB,HSWBD,ENVSTR,STASTR,DAYNR,YEAR,
     &    GWL,POND,WLSTAR,WLS,WSTINI,WST,CQDRD,CRUNO,CQDRAR,CWSUPP,
     &    CWOUT,NUMADJ,HWLMAN,VTAIR,OVERFL,SWSEC,SWMAN,NMPER,IMPEND,
     &    IMPER,HBWEIR,T)
        ENDIF
      ENDIF

C --- set intermediate totals to zero
      CALL ZEROINTR (NUMNOD,INQROT,INQ,INQDRA,IQROT,IQDRA,IINTC,
     & IPTRA,IPEVA,IEVAP,IRUNO,IPREC,IQBOT,OUTPER,IQDRAR,IQCRACK,
     & IGRAI,IGIRD)

C --- set initial values
      CALL ZEROCUMU (CQROT,CQDRA,CQBOT,CQTOP,CPTRA,CPEVA,CEVAP,CRUNO,
     &CGRAI,CNRAI,CGIRD,CNIRD,CUMBOT,CUMTOP,CQDRAR,CQCRACK,
     &CQDRAIN,CQDRD,CWSUPP,CWOUT,SQBOT,SQDRA,SQSUR,SQRAP,DECTOT,
     &ROTTOT,SQPREC,SQIRRIG,CQDARCY)

C --- ANIMO output, initial situation, first year only
      IF (RUNNR.EQ.1.OR.ISEQ.EQ.0) THEN
        IF (SWAFO.EQ.1) THEN
          CALL OUTAFO (AFO,AFONAM,HAFOD,STASTR,ENVSTR,
     &    NUMNOD,OUTPER,PERIOD,TCUM,POND,GWL,THETA,H,INQ,
     &    INQROT,NRLEVS,INQDRA,IPREC,IINTC,IEVAP,IPEVA,IPTRA,IRUNO,
     &    NUMLAY,BOTCOM,DZ,THETAS,BRUNY,ERUNY,BRUND,ERUND,
     &    LAYER,FLGENU,ALFAMG,THETAR,COFGEN,HTABLE,THETLO)
      ENDIF
        IF (SWAUN.EQ.1) THEN
          CALL OUTAUN (AUN,AUNNAM,HAUND,STASTR,ENVSTR,
     &    NUMNOD,OUTPER,PERIOD,TCUM,POND,GWL,THETA,H,INQ,
     &    INQROT,NRLEVS,INQDRA,IPREC,IINTC,IEVAP,IPEVA,IPTRA,IRUNO,
     &    NUMLAY,BOTCOM,DZ,THETAS,BRUNY,ERUNY,BRUND,ERUND,
     &    LAYER,FLGENU,ALFAMG,THETAR,COFGEN,HTABLE,THETLO)
        ENDIF
      ENDIF

C --- profile output, initial situation, first year only
      IF ((RUNNR.EQ.1 .OR. ISEQ.EQ.0) .AND. (SWVAP.EQ.1))
     &   CALL OUTVAP (SWSOLU,OUTFIL,VAP,HVAPD,ENVSTR,STASTR,DAYNR,
     &               YEAR,NUMNOD,Z,THETA,H,CML,SWHEA,TEMP,T,Q)

      RETURN

2000  CONTINUE

C --- TIMESTEP LOOP ----------------------------------------------------

C --- only first timestep of the day
      IF (FL1ST) THEN
        CALL REDUCEVA (SWREDU,REVA,PEVA,DAYNR,DAYSTA,NRAI,
     &  NIRD,RUNNR,ISEQ,COFRED,RSIGNI)
	  QCOMP = 0.0
        FL1ST = .FALSE.
      ENDIF

C --- find phreatic or perched groundwater level 
      CALL CALCGWL(GWL,GWLBAK,NUMNOD,H,Z,DZ,SWBOTB,POND,NODGWL,
     &             FPEGWL,NPEGWL)

C --- calculate lateral drainage
      IF (GWL.GT.998.0) THEN
        Do 2001 level = 1,nrlevs
2001    QDRAIN(level) = 0.0
      ELSEIF (SWDRA.EQ.1) THEN
        CALL BOCODRB (DRAMET,GWL,ZBOTDR,POND,BASEGW,L,QDRAIN,IPOS,
     &  KHTOP,KHBOT,KVTOP,KVBOT,ENTRES,WETPER,ZINTF,GEOFAC,SWDTYP,
     &  OWLTAB,T,SWALLO,DRARES,INFRES,QDRTAB,NRLEVS)
      ELSEIF (SWDRA.EQ.2) THEN
        CALL BOCODRE (SWSEC,SWSRF,NRSRF,NRPRI,GWL,ZBOTDR,TALUDR,
     &  WIDTHR,POND,PONDMX,SWDTYP,DT,WLS,WLP,DRAINL,L,RDRAIN,RINFI,
     &  RENTRY,REXIT,GWLINF,WETPER,QDRAIN,QDRD,T,IMPEND,NMPER,WSCAP,WST)
      ENDIF

      IF (SWDRA.GE.1) THEN
        IF (SWDIVD.EQ.1) THEN
C ---   partition drainage flux over compartments
          CALL DIVDRA (NUMNOD,NRLEVS,DZ,KSAT,LAYER,COFANI,GWL,L,
     &    QDRAIN,QDRA)
        ELSE
C ---   drainage flux through lowest compartment 
          do 102 level=1,nrlevs
            do 104 n=1,numnod-1
              qdra(level,n) =0.0
 104        CONTINUE
            qdra(level,numnod) =qdrain(level)
102       CONTINUE
        ENDIF
      ENDIF

C --- calculate bottom boundary conditions and restrict saturated flux
      CALL BOCOBOT (SWBOTB,GWL,GWLTAB,T,H,Z,LAYER,FLGENU,COFGEN,
     & HTABLE,THETLO,ALFAMG,THETAR,THETAS,THETHI,DMCH,DMCC,KTABLE,KSE99,
     & KSAT,FMOBIL,THETA,DIMOCA,K,KMEAN,QBOT,QBOTAB,AQAVE,
     & AQAMP,AQOMEG,AQTAMX,RIMLAY,COFQHA,COFQHB,HGITAB,NUMNOD,
     & SWMOBI,FM1,PF1,SLOPFM,NODGWL,SWDRA,QDRTOT,QDRA,NRLEVS,
     & QDRAIN,HDRAIN,SHAPE,GWLINP)

C --- determine flow crack
      IF (SWCRACK.EQ.1) CALL CRACK (LAYER,NNCRACK,THETSL,THETA,SHRINA,
     & SHRINB,
     & SHRINC,ACRACK,WTOPLAT,GEOMF,POND,NUMNOD,ADSFLU,THETCR,Z,DZ,
     & QCRACK,MOISR1,MOISRD,CRACKW,FLGENU,COFGEN,THETAR,THETAS,THETLO,
     & THETHI,KTABLE,KSE99,KSAT,SWMOBI,FMOBIL,H,DIAMPOL,DISNOD,RAPDRA,
     & RAPCOEF,CRALEV)

C --- calculate top boundary conditions
      CALL BOCOTOP (POND,REVA,NIRD,DT,QTOP,QBOT,QDRTOT,
     & KMEAN,K,H,DISNOD,LAYER,FLGENU,COFGEN,THETA,THETIM,DZ,
     & HTABLE,THETLO,THETHI,KTABLE,ALFAMG,FTOPH,ARFLUX,THETAR,
     & THETAS,KSE99,KSAT,SWMOBI,FMOBIL,VOLSAT,VOLACT,ACRACK,QCRACK,
     & FLTSAT,HSURF,FLLAST,FLRAIC,DTMIN,WTOPLAT,FLREVA,NUMNOD,QROSUM,
     & QCOMP,FPEGWL,NPEGWL,Q,SWBOTB,GWLINP)

C --- calculate root extraction rates
      CALL ROOTEX (NUMNOD,QROT,DRZ,DZ,PTRA,Z,HLIM3H,HLIM3L,HLIM4,HLIM2U,
     & H,CML,BOTCOM,HLIM2L,HLIM1,ADCRL,ADCRH,ATMDEM,RDCTB,
     & RDM,SWSOLU,ECMAX,ECSLOP,LAYER,THETSL,THETA,QROSUM)

C --- calculate pressure heads and water contents
      CALL HEADCALC(NUMNOD,HM1,H,THETM1,THETA,NUMBIT,FTOPH,DT,T,KMEAN,
     & DZ,DISNOD,DIMOCA,QROT,QDRA,POND,QTOP,LAYER,FLGENU,COFGEN,
     & HTABLE,THETLO,THETHI,ALFAMG,THETAR,THETAS,DMCH,DMCC,SWBOTB,
     & SWNUMS,THETOL,REVA,NIRD,QBOT,QDRTOT,K,KTABLE,Q,ARFLUX,
     & KSE99,KSAT,SWMOBI,FMOBIL,VOLSAT,VOLACT,DTMIN,DNOCON,QIMMOB,FM1,
     & PF1,SLOPFM,THETIM,FLLAST,ADSFLU,ACRACK,QCRACK,FLTSAT,HSURF,
     & FLRAIC,WTOPLAT,FLREVA,QROSUM,QCOMP,QDARCY,FPEGWL,NPEGWL,GWLINP)

C --- update soil temperature profile
      IF (SWHEA.eq.1) CALL SOILTMP (NUMNOD,THETA,THETM1,THETAS,TAV,
     & SWSHF,TEMP,DZ,DISNOD,DT,TAMPLI,TMEAN,DDAMP,TIMREF,DAYNR,Z,
     & FQUARTZ,FCLAY,FORG)

C --- calculate actual water content of profile
      CALL WATCON (VOLM1,VOLACT,NUMNOD,THETA,DZ,FMOBIL,LAYER,
     & THETIM,SWCRACK,CKWM1,CRACKW,WTOPLAT,QCRACK,ARFLUX,NIRD,ACRACK,
     & RAPDRA,DT) 

C --- update parameters for hysterese
      IF (SWHYST.NE.0) CALL UPDATE (NUMNOD,LAYER,H,HM1,INDEKS,TAU,
     &FLGENU,COFGEN,THETAR,THETAS,ALFAMG,THETLO,THETHI,DMCH,DMCC,DIMOCA,
     &SWMOBI,FM1,PF1,SLOPFM,HTABLE,THETA)

C --- integrate daily totals of fluxes
      CALL FLUXES (Q,QBOT,DT,INQ,NUMNOD,THETM1,THETA,DZ,QROT,
     &  QDRA,QIMMOB,ADSFLU,QTOP,QROSUM,QDRTOT,VOLACT,VOLM1,
     &  SWBOTB,QCRACK,FLREVA,POND,WTOPLAT,ARFLUX,NIRD,ACRACK,REVA,QCOMP)

      CALL INTEGRAL (PTRA,DT,PEVA,REVA,QBOT,POND,QTOP,NRAI,NIRD,
     & PONDMX,NUMNOD,QROT,QDRTOT,QDRAIN,DQROT,DPTRA,IQROT,INQROT,IQDRA,
     & NRLEVS,INQDRA,QDRA,GRAI,GIRD,IINTC,IPTRA,IPEVA,IEVAP,IRUNO,
     & IPREC,IQBOT,CQROT,CQDRA,CQDRAIN,CPTRA,CPEVA,CEVAP,CRUNO,
     & CGRAI,CNRAI,CGIRD,CNIRD,CQBOT,CQTOP,PONDM1,WTOPLAT,RAPDRA,
     & IQDRAR,IQCRACK,QCRACK,CQDRAR,CQCRACK,ACRACK,ARFLUX,T,
     & WLS,RSRO,RUNOTS,QROSUM,SWCRACK,SWDRA,IGRAI,IGIRD,QCOMP,
     & QDARCY,CQDARCY)

C --- surface water system (extended drainage option only)
      IF (SWDRA.EQ.2) THEN
        IF (SWSRF .EQ. 3) THEN 
          wlp = AFGEN (WLPTAB,2*MAWLP,T+DT+1.0)
        ENDIF
        IF (SWSEC.EQ.2) THEN
C ---     water level of secondary system is simulated
          CALL WLEVBAL (HLEVD,NRPRI,impend,nmper,swman,imper,
     &     wlstar,wls,hbweir,gwl,wlsman,gwlcrit,nphase,dropr,sttab,
     &     wscap,dt,runots,rapdra,wst,zbotdr,alphaw,betaw,qdrd,cqdrd,
     &     cwsupp,cwout,wlsbak,osswlm,T,NUMNOD,THETAS,THETA,DZ,VCRIT,
     &     NODHD,HCRIT,H,SWQHR,QQHTAB,HQHTAB,wldip,hwlman,vtair,overfl,
     &     numadj,intwl)
        ELSEIF (SWSEC.EQ.1) THEN
C ---     water level of secondary system is input
          CALL WBALLEV (wls,t,wlstab,wst,
     &     sttab,dt,runots,rapdra,qdrd,cqdrd,cwsupp,cwout,WLSOLD)
        ENDIF
      ENDIF

C --- calculate solute concentrations
      IF (SWSOLU.EQ.1)
     &  CALL SOLUTE (CPRE,NIRD,CIRR,DT,NUMNOD,LAYER,INPOLA,
     &  INPOLB,CML,THETA,DDIF,LDIS,Q,DISNOD,THETSL,
     &  Z,GAMPAR,RTHETA,BEXP,DECPOT,FDEPTH,KF,FREXP,FMOBIL,
     &  TSCF,QROT,DZ,KMOBIL,CIL,QDRA,CMSY,THETIM,CISY,CL,DTSOLU,
     &  DTMAX,TEMP,CPOND,PONDM1,QTOP,WTOPLAT,ACRACK,ADSFLU,CRACKC, 
     &  ARFLUX,SWCRACK,CRACKW,CKWM1,RAPDRA,QCRACK,POND,CREF,
     &  QDRTOT,POROS,KFSAT,DECSAT,CDRAIN,HAQUIF,DECTOT,SAMPRO,SAMCRA,
     &  SAMAQ,CRALEV,DIFDES,ROTTOT,SQDRA,SWBR,SDRAIN,BDENS)

C --- calculate mass balance of solute transport
      IF (SWSOLU.EQ.1)
     &  CALL SLTBAL (DT,NIRD,CIRR,ARFLUX,CPRE,QBOT,CDRAIN,CML,NUMNOD,
     &  QDRTOT,RAPDRA,CRACKC,SQBOT,SQSUR,SQRAP,SQPREC,SQIRRIG)

      RETURN

3000  CONTINUE

C --- END OF THE DAY ---------------------------------------------------

C --- just for debug purposes
      if (daynr. eq. 22) then
	  i = i+1
	endif

C --- set daily totals to zero
      DTRA  = DQROT
      DQROT = 0.0
      DPTRA = 0.0

C --- length of output period
      OUTPER = OUTPER+1

C --- OUTPUT SECTION

C --- AIR file, irrigations for ANIMO
      IF (GIRD.Gt.0.0.AND.SWAIR.EQ.1) CALL OUTAIR (AIR,AIRNAM,HAIRD,
     &  STASTR,ENVSTR,YEAR,(DAYNR-1),TCUM,GIRD,CIRR)

C --- skip if not flout 
      IF (.NOT.FLOUT) GOTO 3900

C --- temporary adjust year and daynr for output files
      YEAR1 = YEAR
      YEAR = YEARP
	DAYNR1 = DAYNR
      DAYNR = DAYNRP

C --- calculation of groundwater level
      CALL CALCGWL(GWL,GWLBAK,NUMNOD,H,Z,DZ,SWBOTB,POND,NODGWL,
     &             FPEGWL,NPEGWL)
C --- wba file 
      CALL OUTWBA (OUTFIL,WBA,HWBAD,ENVSTR,STASTR,DAYNR,YEAR,CGRAI,
     &  CNRAI,CGIRD,CNIRD,CRUNO,CQROT,CEVAP,CQBOT,CQDRA,CPTRA,
     &  CPEVA,GWL,T,CQDRAR,VOLACT,VOLINI,POND,RUNNR,SWSCRE,
     &  CQDARCY,CQTOP)

C --- inc file
      CALL OUTINC (OUTFIL,INC,HINCD,ENVSTR,STASTR,DAYNR,YEAR,
     &  IGRAI,IGIRD,IINTC,IRUNO,IPTRA,IQROT,IPEVA,IEVAP,IQDRA,
     &  IQDRAR,IQBOT,T)

C --- tmp file
      IF (SWHEA.eq.1) CALL OUTTEP (OUTFIL,TEP,HTEPD,ENVSTR,STASTR,
     & DAYNR,YEAR,NUMNOD,TEMP,T)

C --- ATE file, soil temperatures
      IF (SWATE.EQ.1) CALL OUTATE (ATE,ATENAM,HATED,STASTR,ENVSTR,
     &  NUMNOD,YEAR,DAYNR,TCUM,TEMPI,TEMP,TAV)

C --- vap file
      IF (SWVAP.EQ.1) CALL OUTVAP (SWSOLU,OUTFIL,VAP,HVAPD,ENVSTR,
     &  STASTR,DAYNR,YEAR,NUMNOD,Z,THETA,H,CML,SWHEA,TEMP,T,Q)

C --- slt file
      IF (SWSOLU.EQ.1) THEN 
        SOLBAL = SAMPRO + SAMCRA - SQPREC - SQIRRIG - SQBOT + SQDRA 
     &         + SQRAP + DECTOT + ROTTOT - SAMINI
        CALL OUTSBA (OUTFIL,SBA,HSBAD,ENVSTR,STASTR,DAYNR,YEAR,
     &       DECTOT,ROTTOT,SAMPRO,SAMCRA,SQBOT,SQSUR,SQRAP,SAMAQ,
     &       SQDRA,T,SOLBAL,SQPREC,SQIRRIG)
      ENDIF

C --- drainage fluxes
      IF (SWDRA.EQ.2 .AND. SWDRF.EQ.1) THEN
        CALL OUTDRF (OUTFIL,DRF,HDRFD,ENVSTR,STASTR,DAYNR,YEAR,
     &  NRPRI,NRSRF,CQDRAIN,CQDRD,CRUNO,CQDRAR,T)
      ENDIF 

C --- surface water system
      IF (SWDRA.EQ.2 .AND. SWSWB.EQ.1) THEN
        CALL OUTSWB (OUTFIL,SWB,HSWBD,ENVSTR,STASTR,DAYNR,YEAR,
     &  GWL,POND,WLSTAR,WLS,WSTINI,WST,CQDRD,CRUNO,CQDRAR,CWSUPP,
     &  CWOUT,NUMADJ,HWLMAN,VTAIR,OVERFL,SWSEC,SWMAN,NMPER,IMPEND,
     &  IMPER,HBWEIR,T)
      ENDIF

C --- ANIMO output files
      IF (SWAFO.EQ.1) THEN
        CALL OUTAFO (AFO,AFONAM,HAFOD,STASTR,ENVSTR,
     &  NUMNOD,OUTPER,PERIOD,TCUM,POND,GWL,THETA,H,INQ,
     &  INQROT,NRLEVS,INQDRA,IPREC,IINTC,IEVAP,IPEVA,IPTRA,IRUNO,
     &  NUMLAY,BOTCOM,DZ,THETAS,BRUNY,ERUNY,BRUND,ERUND,
     &  LAYER,FLGENU,ALFAMG,THETAR,COFGEN,HTABLE,THETLO)
      ENDIF

      IF (SWAUN.EQ.1) THEN
        CALL OUTAUN (AUN,AUNNAM,HAUND,STASTR,ENVSTR,
     &  NUMNOD,OUTPER,PERIOD,TCUM,POND,GWL,THETA,H,INQ,
     &  INQROT,NRLEVS,INQDRA,IPREC,IINTC,IEVAP,IPEVA,IPTRA,IRUNO,
     &  NUMLAY,BOTCOM,DZ,THETAS,BRUNY,ERUNY,BRUND,ERUND,
     &  LAYER,FLGENU,ALFAMG,THETAR,COFGEN,HTABLE,THETLO)
      ENDIF

C --- reset year and daynr to original value
      YEAR = YEAR1
      DAYNR = DAYNR1

C --- set intermediate totals to zero
      CALL ZEROINTR (NUMNOD,INQROT,INQ,INQDRA,IQROT,IQDRA,IINTC,
     & IPTRA,IPEVA,IEVAP,IRUNO,IPREC,IQBOT,OUTPER,IQDRAR,IQCRACK,
     & IGRAI,IGIRD)

3900  RETURN

4000  CONTINUE

C --- TERMINAL SECTION -------------------------------------------------

C --- bal file
      CALL OUTBAL (OUTFIL,ENVSTR,DAYNR,YEAR,BRUND,BRUNY,BAYRD,
     &     BAYRY,CGRAI,CNRAI,CGIRD,CNIRD,CRUNO,CQROT,CEVAP,CQBOT,
     &     CQDRAIN,CQDRA,CQDRAR,VOLACT,VOLINI,Z,DZ,SWDRA,NUMNOD,
     &     NRLEVS,SAMINI,SAMPRO,SAMCRA,SQPREC,SQIRRIG,SQBOT,DECTOT,
     &     ROTTOT,SQRAP,SQDRA,SWSOLU,POND)

C --- write final soil water pressure heads
      CALL FINDUNIT (80,DAT)
      OPEN (DAT,FILE=rmldsp(ENVSTR)//'HFINAL.DAT',STATUS='UNKNOWN')
      WRITE (DAT,'(10F11.3)') (H(I), I=1,NUMNOD)
      CLOSE (DAT)

C --- initial water content next simulation period
      VOLINI = VOLACT+POND
      CLOSE (WBA)
      CLOSE (INC)

C ---   initial solute amount next simulation period

      IF (SWSOLU.EQ.1) THEN
        SAMINI = SAMPRO + SAMCRA
        CLOSE (SBA)
      ENDIF

      IF (SWHEA.EQ.1)  CLOSE (TEP)
      IF (SWVAP.EQ.1)  CLOSE (VAP)
	IF (SWDRA.EQ.2.AND.SWSWB.EQ.1) CLOSE (SWB)
	IF (SWDRA.EQ.2.AND.SWDRF.EQ.1) CLOSE (DRF)

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE TIMER (TASK,IPORWL,RUNNR,ISEQ,FMAY,BRUND,BRUNY,BCRPD,
     & BCRPY,ECRPD,ECRPY,BSCHD,BSCHY,ERUND,ERUNY,IFINCR,DTMAX,
     & NUMNOD,H,DTMIN,T,TCUM,TM1,DT,DTM1,ID,DAYNR,DAYSTA,YEAR,FLLAST,
     & FLENDD,FLENDR,FLOUT,FLCROP,CRPNR,ISTAGE,IRMODE,BAYRD,BAYRY,
     & RAITIM,RAIFLX,FLRAI,ARFLUX,SWSOLU,DTSOLU,SWNUMS,NUMBIT,THETOL,
     & QTOP,THETA,THETM1,NOFRNS,SWSCAL,FLCAL,CRPFIL,ICRMOD,CAPFIL,
     & IRGFIL,CALFIL,BBCFIL,DRFIL,OUTFIL,ENVSTR,WLS,RSRO,SWDRA,POND,
     & PONDMX,PERIOD,SWRES,FLRAIC,FLCOPY,LOGF,OUTD,OUTY,NOUTDA,YEARP,
     & DAYNRP)
C ----------------------------------------------------------------------
C     Date               : 16/04/98              
C     Purpose            : SWAP time keeper              
C     Subroutines called : SHIFTR, DATONR, NRTODA                   
C     Functions called   : FROMTO        
C     File usage         :                                 
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

      INTEGER   BRUND,BRUNY,ERUND,ERUNY,FMAY,FDAY,LDJY
      INTEGER   BCRPD(3,MAYRS),BCRPY(3,MAYRS),BSCHD(3,MAYRS)
      INTEGER   BSCHY(3,MAYRS)
      INTEGER   NOFCRP(MAYRS),ICRMOD(0:3,MAYRS),ECRPD(3,MAYRS)
      INTEGER   ECRPY(3,MAYRS),NOUTDA,YEARP,DAYNRP
      INTEGER   OUTD(366),OUTY(366),DAYNR,DAYSTA,YEAR,D,M
      INTEGER   BAYRD,BAYRY,RUNNR,FROMTO,SWSOLU,SWNUMS,SWDRA
      INTEGER   TASK,IPORWL,ISEQ,NRM1,IRSTEP,ISTAGE,IRMODE,ID
      INTEGER   CRPNR,NUMNOD,DAYNRO,YEARO,NUMBIT,I,J,IFINCR
      INTEGER   NOFRNS,SWSCAL,CAL,PERIOD,CNTPER,SWRES,LOGF

      INTEGER D1(3),M1(3),Y1(3),D2(3),M2(3),Y2(3),D3(3),M3(3),Y3(3)
      INTEGER IType(3),ITIMES,IFND

      REAL      RAITIM(100),RAIFLX(100),THETOL,QTOP,ARFLUX,POND
      REAL      T,TCUM,TM1,DT,DTM1,DTMIN,DTMAX,DTSOLU,WLS,RSRO,PONDMX
      REAL*8    H(MACP),THETA(MACP),THETM1(MACP),DTHETA

      CHARACTER   FILNAM*12,ENVSTR*50,LINE*80
      CHARACTER*8 CRPFIL(3,MAYRS),CAPFIL(3,MAYRS)
      CHARACTER*8 IRGFIL(MAYRS),CALFIL(MAYRS),DRFIL(MAYRS)
      CHARACTER*8 BBCFIL(MAYRS),OUTFIL(MAYRS)
      CHARACTER*2 EXT(MAYRS)
      CHARACTER*6 TMPNAM
      CHARACTER*8 CRPFLB(3),CAPFLB(3)

      character*80 rmldsp

      LOGICAL   FLENDD,FLENDR,FLOUT,FLLAST,FLRAI,FLCROP,FLRAIC
      LOGICAL   FLCAL,EXISTS,FLCOPY,BLANK,COMMENT

      SAVE

      DATA EXT/'1 ','2 ','3 ','4 ','5 ','6 ','7 ','8 ','9 ','10',
     &         '11','12','13','14','15','16','17','18','19','20',
     &         '21','22','23','24','25','26','27','28','29','30',
     &         '31','32','33','34','35','36','37','38','39','40',
     &         '41','42','43','44','45','46','47','48','49','50',
     &         '51','52','53','54','55','26','57','58','59','60',
     &         '61','62','63','64','65','66','67','68','69','70'/
C ----------------------------------------------------------------------
*     T      := time since start of agricultural year
*     TCUM   := time since start of simulation
*     DAYNR  := daynumber from start of calendar year
*     ID     := daynumber from emergence of the crop
*     ISTAGE := no crop (1) or yes crop (2)
*     IRMODE := no scheduling (1) or yes scheduling (2)
C ----------------------------------------------------------------------
C --- tijdelijk
      LOGF = LOGF

      GOTO (1000,2000,3000) TASK

1000  CONTINUE

C === INITIALIZATION ===================================================

C --- Read crop calendars once, expand number of runs in case of scaling
      IF (FLCAL) THEN

C ---   in case of no scaling read NOFRNS crop calendars
C ---   in case of scaling read 1 crop calendar 
        ITIMES = NOFRNS
        IF (SWSCAL.EQ.1) ITIMES = 1

        DO 2 I = 1,ITIMES
C ---     read crop calendar from CALFIL
          CALL SHIFTR (CALFIL(I))
          FILNAM = CALFIL(I)//'.CAL'
          CALL SHIFTL (FILNAM)
          CALL SHIFTR (ENVSTR)

C ---     check if a crop calendar file has been specified
          IF (FILNAM(1:4).EQ.'.CAL' .OR. FILNAM.EQ.'        .CAL') THEN
            NOFCRP(I) = 0            
          ELSE

C ---       check if a crop calendar file does exist
            INQUIRE (FILE=rmldsp(ENVSTR//FILNAM),EXIST=EXISTS)
            IF (.NOT.EXISTS) THEN
C ---         write error to log file
              WRITE (LOGF,122) ENVSTR//FILNAM
 122          FORMAT ('SWAP can not find the input file',/,A)
              STOP 'The .CAL file was not found: SWAP stopped !'
            ENDIF

C ---       open calendar file
            CALL FINDUNIT (10,CAL)
            OPEN (CAL,FILE=rmldsp(ENVSTR//FILNAM),status='old',
     &      access='sequential')

C ---       position file pointer
            IFND = 0
34          READ (CAL,'(A)') LINE
            CALL ANALIN (LINE,BLANK,COMMENT)
            IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 34
            IF (COMMENT) GOTO 35
            IFND = IFND+1
            BACKSPACE (CAL)
            READ (CAL,*) CRPFLB(IFND),ITYPE(IFND),CAPFLB(IFND),
     &      D1(IFND),M1(IFND),D2(IFND),M2(IFND),D3(IFND),M3(IFND)
            GOTO 34
C ---       ready...
35          CONTINUE

C --- year is calculated, BRUNY moet eigenlijk BAYRY zijn
            DO 22 J = 1,IFND 
              if (m1(J).GE.FMAY) y1(J) = BRUNY
              if (m1(J).LT.FMAY) y1(J) = BRUNY+1
cpd
cpd           error for parallel sub-runs
cpd              y1(J) = y1(J)+I-1
              if (BRUNY.eq.ERUNY) then
                y1(J) = y1(J)
              else
                y1(J) = y1(J)+I-1
              end if
cpd

22          CONTINUE
C --- year is calculated
            DO 32 J = 1,IFND 
              if (m2(J).GE.FMAY) y2(J) = BRUNY
              if (m2(J).LT.FMAY) y2(J) = BRUNY+1
cpd
cpd           error for parallel sub-runs
cpd              y2(J) = y2(J)+I-1
              if (BRUNY.eq.ERUNY) then
                y2(J) = y2(J)
              else
                y2(J) = y2(J)+I-1
              end if
cpd
32          CONTINUE
C --- year is calculated
            DO 42 J = 1,IFND 
              if (m3(J).GE.FMAY) y3(J) = BRUNY
              if (m3(J).LT.FMAY) y3(J) = BRUNY+1
cpd
cpd           error for parallel sub-runs
cpd              y3(J) = y3(J)+I-1
              if (BRUNY.eq.ERUNY) then
                y3(J) = y3(J)
              else
                y3(J) = y3(J)+I-1
              end if
cpd
42          CONTINUE

            DO 4 J = 1,IFND
              CRPFIL(J,I) = CRPFLB(J)
              ICRMOD(J,I) = ITYPE(J)
              CAPFIL(J,I) = CAPFLB(J)
              BCRPY(J,I) = Y1(J)
              CALL DATONR (Y1(J),M1(J),D1(J),BCRPD(J,I))
              ECRPY(J,I) = Y2(J)
              CALL DATONR (Y2(J),M2(J),D2(J),ECRPD(J,I))
              BSCHY(J,I) = Y3(J)
              CALL DATONR (Y3(J),M3(J),D3(J),BSCHD(J,I))
4           CONTINUE

            NOFCRP(I) = IFND    
            CLOSE (CAL)
          ENDIF

2       CONTINUE

C ---   expand in case of scaling
        IF (SWSCAL.EQ.1) THEN
          CALL SHIFTL(OUTFIL(1))
          TMPNAM = OUTFIL(1)(1:6)
          Call SHIFTR(TMPNAM)
          DO 154 I = 1,NOFRNS
            IRGFIL(I) = IRGFIL(1)
            NOFCRP(I) = NOFCRP(1)
            DO 156 J = 1,NOFCRP(1)
              CRPFIL(J,I) = CRPFIL(J,1)
              ICRMOD(J,I) = ICRMOD(J,1)
              CAPFIL(J,I) = CAPFIL(J,1)
              BCRPY(J,I)  = BCRPY(J,1)
              BCRPD(J,I)  = BCRPD(J,1)
              ECRPY(J,I)  = ECRPY(J,1)
              ECRPD(J,I)  = ECRPD(J,1)
              BSCHY(J,I)  = BSCHY(J,1)
              BSCHD(J,I)  = BSCHD(J,1)
156         CONTINUE
            BBCFIL(I) = BBCFIL(1)
            DRFIL(I) = DRFIL(1)
C ---       Modify OUTFIL
            OUTFIL(I) = TMPNAM//EXT(I)          
154       CONTINUE
        ENDIF

      FLCAL = .FALSE.
      ENDIF

C --- Initialize flags, switches & counters ----------------------------

      FLOUT  = .FALSE.
      FLLAST = .FALSE.
      FLENDD = .FALSE.
      FLENDR = .FALSE.
      FLCROP = .FALSE.
      FLRAIC = .FALSE.
      FLCOPY = .TRUE.

      IRSTEP = 1
      ISTAGE = 1
      IRMODE = 1
      ID     = 0
      CRPNR  = 0

C --- fill ICRMOD(0,??) with 0 (nu kan METEO worden aangeroepen met
C --- CRPNR = 0
      DO 17, I = 1,MAYRS
17    ICRMOD(0,I) = 0

      IFINCR = 0

C --- first year only
      IF (RUNNR.EQ.1.OR.ISEQ.EQ.0) THEN

C ---   initial value counter output interval
        CNTPER = 1

        TCUM = BRUND-1
        DAYNR  = BRUND 
        DAYSTA = BRUND
        YEAR   = BRUNY

        IF (DAYNR.EQ.BCRPD(1,RUNNR).AND.YEAR.EQ.BCRPY(1,RUNNR)) THEN
          ISTAGE = 2
          ID     = ID+1
          IF (DAYNR.EQ.BSCHD(1,RUNNR).AND.YEAR.EQ.BSCHY(1,RUNNR))
     &    IRMODE = 2
        ENDIF

C ---   calculate T, BAYRD,BAYRY
        IF (FMAY.EQ.1) THEN
          T     = DAYNR -1
          BAYRD = 1
          BAYRY = YEAR
        ELSE
          CALL NRTODA (YEAR,DAYNR,M,D)
          CALL DATONR (YEAR,FMAY,1 ,FDAY)
          CALL DATONR (YEAR-1,FMAY,1,NRM1)
          IF (FMAY.LE.M) THEN
            T     = FROMTO (FDAY,YEAR,DAYNR,YEAR)  
            BAYRD = FDAY
            BAYRY = YEAR
          ELSE  
            T     = FROMTO (NRM1,YEAR-1,DAYNR,YEAR) 
            BAYRD = NRM1
            BAYRY = YEAR-1
          ENDIF  
        ENDIF

        TM1  = T
        IF (IPORWL.EQ.1) THEN
          DT = 1.0
        ELSE
          DT   = SQRT (DTMIN*DTMAX)
        ENDIF
        DTM1 = DT

C --- following years
      ELSE

C ---   reset counter output interval
        IF (SWRES.EQ.1) CNTPER = 1

        DAYNR  = DAYNRO
        YEAR   = YEARO

        T      = 0
        BAYRD  = DAYNR
        BAYRY  = YEAR
        TM1    = T
        IF (IPORWL.EQ.1) THEN
          DT = 1.0
        ELSE
          DT     = SQRT (DTMIN*DTMAX)
        ENDIF
        DTM1   = DT
        IF (DAYNR.EQ.BCRPD(1,RUNNR).AND.YEAR.EQ.BCRPY(1,RUNNR)) THEN
          CRPNR  = CRPNR+1
          ISTAGE = 2
          ID     = ID+1
          IF (DAYNR.EQ.BSCHD(1,RUNNR).AND.YEAR.EQ.BSCHY(1,RUNNR))
     &    IRMODE = 2 
        ENDIF

      ENDIF
C ----------------------------------------------------------------------

      RETURN

2000  CONTINUE

C === NEXT TIME STEP ===================================================

C --- Update time T and cumulated time (ANIMO)
      T    = T + DT
      IF (IPORWL.EQ.2) TCUM = TCUM + DT

      IF (IPORWL.EQ.1) THEN
        DT     = 1.0
        FLENDD = .TRUE.
        GOTO 2900
      ENDIF

C --- store old value
      tm1  = t
      dtm1 = dt

C --- indicate t is at end of day
      if (FLLAST) then
         FLLAST = .FALSE.
         FLENDD = .TRUE.
      endif

C --- dt as determined by water transport for SWNUMS = 1
      if (SWNUMS.eq.1) then
        dt = dtmax
        do 100 i = 1,numnod
          if (h(i).gt.0.0) then
            dt = min(dt,dtmax)
          else
            dtheta = abs(thetm1(i)-theta(i))
            if (dtheta.lt.1.0d-6) then
              dt = min(dt,dtmax)
            else
              dt = min(dt, 10.0*thetol*dtm1/real(dtheta))
            endif
          endif
100     continue
      else
C --- dt as determined by water transport for SWNUMS = 2
        if (numbit.lt.2) then
          if (qtop.gt.0.0) then
            dt = dt*1.25
          else
            dt = dt*1.10
          endif
        else
          if (numbit.gt.4) dt = dt/1.25
        endif
      endif 

C --- dtmax as determined by solute transport
      if (swsolu.eq.1) dt = min (dt,dtsolu)

      IF (FLRAI.AND..NOT.FLENDD) THEN
        IF (FLRAIC) THEN
          ARFLUX = RAIFLX(IRSTEP+1)
          IRSTEP = IRSTEP+1
          FLRAIC = .FALSE.
        ENDIF 
        IF (T+DT.GT.(INT(T)+RAITIM(IRSTEP+1))-1.0E-4) THEN
          DT     = (INT(T)+RAITIM(IRSTEP+1))-T
          FLRAIC = .TRUE.
        ENDIF
      ENDIF

C --- limit dt at lower and upper boundary
      dt = max(dt,dtmin)
      dt = min(dt,dtmax)

      IF (SWDRA.EQ.2) THEN
        IF (WLS.GT.PONDMX .OR. POND.GT.PONDMX) 
     &  dt = min(dt,(0.02*rsro))
      ENDIF

C --- if step is last timestep of the day : synchronise step
      if (t+1.2*dt.gt.aint(t+1.0)) then
        dt     = aint(t+1.0)-t
        FLLAST = .TRUE.
      endif

2900  CONTINUE

      RETURN

3000  CONTINUE

C === NEXT DAY =========================================================

C --- is it an output day ?
      IF (IPORWL.EQ.2) THEN
        FLOUT = .FALSE.
        IF (CNTPER .EQ. PERIOD) THEN
          CNTPER = 0
          FLOUT = .TRUE.
	    DAYNRP = DAYNR
	    YEARP = YEAR
        ELSE  
          DO 20 I = 1,NOUTDA
            IF (DAYNR.EQ.OUTD(I).AND.YEAR.EQ.OUTY(I)) THEN
              FLOUT = .TRUE.
	        DAYNRP = DAYNR
	        YEARP = YEAR
              GOTO 30
            ENDIF
 20       CONTINUE
        ENDIF
      ENDIF

C --- end of run ?
 30   IF (DAYNR.EQ.ERUND.AND.YEAR.EQ.ERUNY) THEN
        FLENDR = .TRUE.
        DAYNR  = DAYNR+1
        GOTO 24
      ENDIF

C --- update daynumber
      DAYNR  = DAYNR+1
      FLENDD = .FALSE.
      IF (IPORWL.EQ.2) CNTPER = CNTPER + 1

C --- new calendar year ?
      CALL DATONR (YEAR,12,31,LDJY)
      IF (DAYNR.GT.LDJY) THEN
        DAYNR = 1
        YEAR  = YEAR+1
C ---   enable copying of meteofile to temporary file
        FLCOPY = .TRUE.
      ENDIF

C --- new agricultural year ?
      CALL DATONR (YEAR,FMAY,1,FDAY)
      IF (DAYNR.EQ.FDAY) THEN
        FLENDR = .TRUE.
        IF (IPORWL.EQ.2) THEN
          DAYNRO = DAYNR
          YEARO  = YEAR
        ENDIF
        GOTO 24
      ENDIF

C --- Determine current cropping stage & irrigation mode

      IF (IFINCR.GT.0) THEN
        IFINCR = 0
        ISTAGE = 1
        IRMODE = 1
        ID     = 0
        FLCROP = .FALSE.
      ENDIF

      IF (CRPNR.LT.NOFCRP(RUNNR)) THEN
        IF (DAYNR.EQ.BCRPD(CRPNR+1,RUNNR).AND.YEAR.EQ.
     &    BCRPY(CRPNR+1,RUNNR)) THEN
          CRPNR  = CRPNR+1
          ISTAGE = 2
        ENDIF
      ENDIF
      IF (CRPNR.GT.0) THEN
        IF (DAYNR.EQ.BSCHD(CRPNR,RUNNR).AND.YEAR.EQ.
     &  BSCHY(CRPNR,RUNNR)) IRMODE = 2
      ENDIF
      IF (ISTAGE.EQ.2) ID = ID+1

C --- reset counter for small rainfall timesteps 
24    IRSTEP = 1

c --- reset timestep for next day
      dt = max(dt, sqrt(dtmin*dtmax))

      RETURN
      END 


** FILE:
**    SWALIBAO.FOR - part of program SWAP
** FILE IDENTIFICATION:
**    $Id: swalibao.for 1.10.2.10 1999/02/23 14:34:52 kroes Exp $
** DESCRIPTION:
**    This file contains program units of SWAP. The program units 
**    in this file are of the 3rd level and are sorted alphabetically
**    with the first letter of the program unit ranging from A - O.
**    The following program units are in this file:
**        ASSIM, ASTRO, BOCOBOT, BOCODRB, BOCODRE, BOCOTOP
**        CALCGWL, CRACK, DEVRIES, DIVDRA, DMCNODE, FLUXES
**        HCONODE, HEADCALC, INITSOL, INTEGRAL, NOCROP, OUTAFO
**        OUTAIR, OUTATE, OUTAUN, OUTBAL, OUTDRF, OUTSBA, OUTSWB, 
**        OUTTEP, OUTVAP, OUTWBA
************************************************************************
C ----------------------------------------------------------------------
      SUBROUTINE ASSIM (AMAX,EFF,LAI,KDIF,SINB,PARDIR,PARDIF,FGROS)
C ----------------------------------------------------------------------
C     Author: Daniel van Kraalingen, 1986
C     Calculates the gross CO2 assimilation rate of the whole crop, 
C     FGROS, by performing a Gaussian integration over depth in the 
C     crop canopy. At three different depths in the canopy, i.e. for
C     different values of LAI, the assimilation rate is computed for
C     given fluxes of photosynthetically active radiation, whereafter
C     integration over depth takes place. For more information: see 
C     Spitters et al. (1988). The input variables SINB, PARDIR and 
C     PARDIF are calculated in RADIAT.
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER I

      REAL    LAI,LAIC,KDIF,KDIRBL,KDIRT
      REAL    AMAX,EFF,FGL,FGROS,FGRSH,FGRSUN,FSLLA,GAUSR,PARDIF,PARDIR
      REAL    REFH,REFS,SCV,SINB,VISD,VISDF,VISPP,VISSHD,VIST

      DATA    GAUSR /0.3872983/
C ----------------------------------------------------------------------
C --- extinction coefficients KDIF,KDIRBL,KDIRT
      SCV    = 0.2
      REFH   = (1.-SQRT(1.-SCV))/(1.+SQRT(1.-SCV))
      REFS   = REFH*2./(1.+1.6*SINB)
      KDIRBL = (0.5/SINB)*KDIF/(0.8*SQRT(1.-SCV))
      KDIRT  = KDIRBL*SQRT(1.-SCV)

C --- three point gaussian integration over LAI
      FGROS  = 0.
      DO 10 I = 1,3
        LAIC   = 0.5*LAI+GAUSR*(I-2)*LAI
C --- absorbed diffuse radiation (VIDF),light from direct
C --- origine (VIST) and direct light(VISD)
        VISDF  = (1.-REFS)*PARDIF*KDIF  *EXP(-KDIF  *LAIC)
        VIST   = (1.-REFS)*PARDIR*KDIRT *EXP(-KDIRT *LAIC)
        VISD   = (1.-SCV) *PARDIR*KDIRBL*EXP(-KDIRBL*LAIC)
C --- absorbed flux in W/m2 for shaded leaves and assimilation
        VISSHD = VISDF+VIST-VISD
        FGRSH  = AMAX*(1.-EXP(-VISSHD*EFF/AMAX))
C --- direct light absorbed by leaves perpendicular on direct
C --- beam and assimilation of sunlit leaf area
        VISPP  = (1.-SCV)*PARDIR/SINB
        IF (VISPP.LE.0.) FGRSUN = FGRSH
        IF (VISPP.GT.0.) FGRSUN = AMAX*(1.-
     $    (AMAX-FGRSH)*(1.-EXP(-VISPP*EFF/AMAX))/ (EFF*VISPP))
C --- fraction of sunlit leaf area (FSLLA) and local
C --- assimilation rate (FGL)
        FSLLA  = EXP(-KDIRBL*LAIC)
        FGL    = FSLLA*FGRSUN+(1.-FSLLA)*FGRSH
C --- integration
        IF (I.EQ.2) FGL = FGL*1.6
        FGROS  = FGROS+FGL
10    CONTINUE
      FGROS  = FGROS*LAI/3.6

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE ASTRO (IDAY,LAT,DAYL,DAYLP,SINLD,COSLD)
C ----------------------------------------------------------------------
C     Author: Daniel van Kraalingen, 1986
C     Computation of astronomical daylength (DAYL), photoperiodic
C     daylength (DAYLP) and two intermediate variables, SINLD and COSLD, 
C     from day number and geographic latitude. Photoperiodic daylength
C     for the effects on development rate is defined as the period that
C     the angle of the sun above the horizon exceeds -4 degrees.
C ----------------------------------------------------------------------
      IMPLICIT NONE
 
      INTEGER IDAY

      REAL    LAT
      REAL    ANGLE,AOB,COSLD,DAYL,DAYLP,DEC,PI,RAD,SINLD

      DATA    PI /3.1415926/,ANGLE /-4./
C ----------------------------------------------------------------------
C --- declination of the sun as a function of IDAY
      RAD   = PI/180.
      DEC   = -ASIN(SIN(23.45*RAD)*COS(2.*PI*(IDAY+10.)/365.))
C --- some intermediate variables
      SINLD = SIN(RAD*LAT)*SIN(DEC)
      COSLD = COS(RAD*LAT)*COS(DEC)
      AOB   = SINLD/COSLD      
C --- calculation of daylenght and photoperiodic daylength
      DAYL  = 12.0*(1.+2.*ASIN(AOB)/PI)
      DAYLP = 12.0*(1.+2.*ASIN((-SIN(ANGLE*RAD)+SINLD)/COSLD)/PI)

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE BOCOBOT (SWBOTB,GWL,GWLTAB,T,H,Z,LAYER,
     & FLGENU,COFGEN,HTABLE,THETLO,ALFAMG,THETAR,THETAS,THETHI,
     & DMCH,DMCC,KTABLE,KSE99,KSAT,FMOBIL,THETA,DIMOCA,K,KMEAN,
     & QBOT,QBOTAB,AQAVE,AQAMP,AQOMEG,AQTAMX,RIMLAY,COFQHA,COFQHB,
     & HGITAB,NUMNOD,SWMOBI,FM1,PF1,SLOPFM,NODGWL,SWDRA,QDRTOT,
     & QDRA,NRLEVS,QDRAIN,HDRAIN,SHAPE,GWLINP)
C ----------------------------------------------------------------------
C     Date               : 21/01/98                              
C     Purpose            : determines boundary conditions at the bottom
C                          of the soil profile at time T
C     Subroutines called : -
C     Functions called   : AFGEN,THENODE,DMCNODE,HCONODE                   
C     File usage         : -         
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

C ---  global
       INTEGER SWBOTB,LAYER(MACP),THETLO(MAHO),THETHI(MAHO),NUMNOD
       INTEGER SWMOBI,NODGWL,SWDRA,NRLEVS

       REAL    GWL,GWLTAB(732),T,Z(MACP),QBOT,QBOTAB(732),HGITAB(50)
       REAL    FMOBIL(MACP),FM1(MAHO),PF1(MAHO),SLOPFM(MAHO),QDRTOT
       REAL    AFGEN,AQAMP,AQAVE,AQOMEG,AQTAMX,COFQHA,COFQHB,RIMLAY
       REAL    QDRA(5,MACP),QDRAIN(5),HDRAIN,SHAPE,GWLINP

       REAL*8  H(MACP),KMEAN(MACP+1),THENODE,DMCNODE,HCONODE
       REAL*8  COFGEN(8,MAHO),HTABLE(MAHO,99),KTABLE(MAHO,99)
       REAL*8  ALFAMG(MACP),THETAR(MACP),THETAS(MACP),DMCC(MAHO,99)
       REAL*8  DMCH(MAHO,99)
       REAL*8  KSE99(MAHO),KSAT(MAHO),THETA(MACP),DIMOCA(MACP),K(MACP+1)

       LOGICAL FLGENU(MAHO)
C ----------------------------------------------------------------------
C --- local
      INTEGER  node,i,lay,level

      REAL     deepgw,qdrnode(macp),fluxtotal,ratio,gwlmean,hresis,hmax
C ----------------------------------------------------------------------

C --- interpolation between daily values of given groundwaterlevel
      if (swbotb.eq.1) then
        if (gwl.lt.998.0) then
C ---     calculate soil profile resistance 
	    hresis = gwl - real(h(numnod)) - real (z(numnod))
          lay            = layer(numnod)
          hmax   = 0.5*(-z(numnod))
	    hresis = min(hresis,hmax)
	    hresis = max(hresis,-hmax)
	  else
	    hresis = 0.0
	  endif
        gwlinp    = AFGEN (GWLTAB,732,T)
        h(numnod) = gwlinp - z(numnod) - hresis

C ---   adapt theta, water capacity and conductivity to new h(numnod)
        lay            = layer(numnod)
        i              = numnod
        if (SWMOBI.EQ.1) then
          if (h(i).gt.-1.0d0) then
            fmobil(i) = fm1(lay)+(0.0-pf1(lay))*slopfm(lay)
          else
            fmobil(i) = fm1(lay)+(log10(abs(real(h(i))))-pf1(lay))*
     &                  slopfm(lay)
          endif
          fmobil(i) = min (1.0,fmobil(i))
          fmobil(i) = max (0.3,fmobil(i))
          thetar(i) = cofgen(1,lay)*fmobil(i)
          thetas(i) = cofgen(2,lay)*fmobil(i)
        endif
        theta(numnod)  = thenode (numnod,h(numnod),LAYER,FLGENU,
     &                   COFGEN,HTABLE,THETLO,ALFAMG,THETAR,THETAS)
        dimoca(numnod) = dmcnode (numnod,h(numnod),LAYER,FLGENU,COFGEN,
     &                   THETLO,THETHI,DMCH,DMCC,THETAS,THETAR,
     &                   ALFAMG,SWMOBI,FM1,PF1,SLOPFM,HTABLE,THETA)
        k(numnod)      = hconode (numnod,theta(numnod),LAYER,FLGENU,
     &                   COFGEN,THETAR,THETAS,THETLO,THETHI,KTABLE,
     &                   KSE99,KSAT,SWMOBI,FMOBIL)
        kmean(numnod)  = 0.5*(k(numnod)+k(numnod-1))
      endif

C --- interpolation between daily values of given flux
      if (swbotb.eq.2) qbot = AFGEN (QBOTAB,732,T)

C --- seepage or infiltration from/to deep groundwater
      if (swbotb.eq.3) then
        gwlmean = hdrain + shape*(gwl - hdrain)
        deepgw = aqave + aqamp*cos(aqomeg*(t - aqtamx))
        qbot   = (deepgw - gwlmean)/rimlay
      endif

C --- flux calculated as function of h
      if (swbotb.eq.4) qbot = cofqha*exp(cofqhb*abs(gwl))

C --- interpolation between daily values of given pressurehead
      if (swbotb.eq.5) THEN
        h(numnod)      = AFGEN (HGITAB,50,T)
        lay            = layer(numnod)
        i              = numnod
        if (SWMOBI.EQ.1) then
          if (h(i).gt.-1.0d0) then
            fmobil(i) = fm1(lay)+(0.0-pf1(lay))*slopfm(lay)
          else
            fmobil(i) = fm1(lay)+(log10(abs(real(h(i))))-pf1(lay))*
     &                  slopfm(lay)
          endif
          fmobil(i) = min (1.0,fmobil(i))
          fmobil(i) = max (0.3,fmobil(i))
          thetar(i) = cofgen(1,lay)*fmobil(i)
          thetas(i) = cofgen(2,lay)*fmobil(i)
        endif
        theta(numnod)  = thenode (numnod,h(numnod),LAYER,FLGENU,
     &                   COFGEN,HTABLE,THETLO,ALFAMG,THETAR,THETAS)
        dimoca(numnod) = dmcnode (numnod,h(numnod),LAYER,FLGENU,COFGEN,
     &                   THETLO,THETHI,DMCH,DMCC,THETAS,THETAR,
     &                   ALFAMG,SWMOBI,FM1,PF1,SLOPFM,HTABLE,THETA)
        k(numnod)      = hconode (numnod,theta(numnod),LAYER,FLGENU,
     &                   COFGEN,THETAR,THETAS,THETLO,THETHI,KTABLE,
     &                   KSE99,KSAT,SWMOBI,FMOBIL)
        kmean(numnod)  = 0.5*(k(numnod)+k(numnod-1))
      endif

C --- zero flux at the bottom
      if (swbotb.eq.6) qbot = 0.0

C --- free drainage
      if (swbotb.eq.7) qbot = -1.0 * real(kmean(numnod+1))

C --- lysimeter with free drainage
      if (swbotb.eq.8) qbot = 0.0

C --- restrict bottom and drainage flux if necessary
      if (gwl.lt.998.0 .and. nodgwl.lt.numnod .and. swbotb.le.6) then

        if (swdra.ge.1) then
C ---   calculate total drainage flux of each node

          do 230 node = 1,numnod
            qdrnode(node) = 0.0
 230      continue
          qdrtot = 0.0

          do 250 node = nodgwl,numnod
            do 270 level = 1,nrlevs
              qdrnode(node) = qdrnode(node) + qdra(level,node)
 270        continue
            qdrtot = qdrtot + qdrnode(node)
 250      continue
        endif
        fluxtotal = qbot - qdrtot

C ---   search for less conductive layers and restrict fluxes if necessary
        do 300 node = nodgwl,numnod
          lay = layer(node)
          if (fluxtotal .lt. -ksat(lay)) then
            ratio = real(-ksat(lay)/fluxtotal*0.8)
            fluxtotal = 0.0
            do 320 i = node,numnod
              do 340 level=1,nrlevs
                qdra(level,i) = ratio * qdra(level,i)
 340          continue
              qdrnode(i) = ratio * qdrnode(i)
              fluxtotal = fluxtotal - qdrnode(i)
 320        continue
            qbot = ratio * qbot
            fluxtotal = fluxtotal + qbot + qdrnode(node)
          else
            fluxtotal = fluxtotal + qdrnode(node)
          endif
 300    continue
      endif      

C --- in case of drainage always calculate total drainage flux

      if (swdra.ge.1) then

        do 350 level = 1,nrlevs
          qdrain(level) = 0.0
 350    continue
        qdrtot = 0.0

        do 360 level = 1,nrlevs
          do 370 node = 1,numnod
             qdrain(level) = qdrain(level) + qdra(level,node)
 370      continue
          qdrtot = qdrtot + qdrain(level)
 360    continue
      endif

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE BOCODRB (DRAMET,GWL,ZBOTDR,POND,BASEGW,L,QDRAIN,IPOS,
     &  KHTOP,KHBOT,KVTOP,KVBOT,ENTRES,WETPER,ZINTF,GEOFAC,SWDTYP,
     &  OWLTAB,T,SWALLO,DRARES,INFRES,QDRTAB,NRLEVS)
C ----------------------------------------------------------------------
C     Date               : 12/03/98                         
C     Purpose            : determines the values of the boundary       
C                          conditions at the lateral side of the soil  
C                          profile : basic drainage routine                    
C     Subroutines called : -                                           
C     Functions called   : AFGEN                                     
C     File usage         : -                                           
C ----------------------------------------------------------------------  
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

C --- global
      INTEGER DRAMET,IPOS,SWDTYP(5),SWALLO(5),NRLEVS

      REAL    GWL,ZBOTDR(5),POND,BASEGW(2),L(5),QDRAIN(5),KHTOP,KHBOT
      REAL    KVTOP,KVBOT,ENTRES,WETPER(5),ZINTF,GEOFAC,T
      REAL    DRARES(5),INFRES(5),QDRTAB(50),AFGEN,OWLTAB(5,2*MAOWL)
C ----------------------------------------------------------------------
C --- local
      INTEGER i,lev

      REAL    dh,zimp,dbot,pi,totres,x,fx,eqd,rver,rhor,rrad
      REAL    TEMPTAB(2*MAOWL)

      LOGICAL FLDRY

      PARAMETER (pi=3.14159)

C ----------------------------------------------------------------------
C --- drainage flux calculated according to Hooghoudt or Ernst

      if (dramet.eq.2) then

        dh    = gwl-zbotdr(1)
        if (abs(gwl).lt.1.0e-7) dh = dh + pond
C ---   contributing layer below drains limited to 1/4 L
        zimp  = max (basegw(1),zbotdr(1)-0.25*L(1))
        dbot  = (zbotdr(1)-ZIMP)  

        if (dbot.lt.0.0) STOP 'Error - Bocodrb: DBOT negative'

C ---   no infiltration allowed
        if (dh.lt.1.0E-10) then
          qdrain(1) = 0.0
          return
        endif

C ---   case 1: homogeneous, on top of impervious layer

        if (ipos.eq.1) then

C ---     calculation of drainage resistance and drainage flux

          totres    = l(1)*l(1)/(4*khtop*abs(dh)) + entres
          qdrain(1) = dh/totres 

C ---   case 2,3: in homogeneous profile or at interface of 2 layers

        elseif (ipos.eq.2.or.ipos.eq.3) then

C ---     calculation of equivalent depth
          x = 2*pi*dbot/l(1)
          if (x.gt.0.5) then
            fx = 0.0
            do 10 i = 1,5,2
10          fx = fx + (4*exp(-2*i*x))/(i*(1.0-exp(-2*i*x)))
            eqd = pi*l(1)/8 / (log(l(1)/wetper(1))+fx)
          else
            if (x.lt.1.0E-6) then
              eqd = dbot
            else
              fx  = pi**2/(4*x) + log(x/(2*pi))
              eqd = pi*l(1)/8 / (log(l(1)/wetper(1))+fx)
            endif
          endif 
          if (eqd.gt.dbot) eqd = dbot

C ---     calculation of drainage resistance & drainage flux

          if (ipos.eq.2) then
            totres = l(1)*l(1)/(8*khtop*eqd+4*khtop*abs(dh)) + entres 
          elseif (ipos.EQ.3) then
            totres = l(1)*l(1)/(8*khbot*eqd+4*khtop*abs(dh)) + entres
          endif
          qdrain(1) = dh/totres 

C ---   case 4: drain in bottom layer
        elseif (ipos.eq.4) then
          if (zbotdr(1).gt.zintf) STOP 'Error - check ZINTF and ZBOTDR' 
          rver      = max (gwl-zintf,0.0) / kvtop +
     &                (min (zintf,gwl) -zbotdr(1))/kvbot
          rhor      = l(1)*l(1)/(8*khbot*dbot) 
          rrad      = l(1)/(pi*sqrt(khbot*kvbot)) * log(dbot/wetper(1))
          totres    = rver+rhor+rrad+entres
          qdrain(1) = dh/totres 

C ---   case 5 : drain in top layer
        elseif (ipos.eq.5) then
          if (zbotdr(1).lt.zintf) STOP 'Error - check ZINTF and ZBOTDR'
          rver      = (gwl-zbotdr(1))/kvtop
          rhor      = l(1)*l(1) / (8*khtop*(zbotdr(1)-zintf) +
     &                             8*khbot*(zintf-zimp))
          rrad      = l(1)/(pi*sqrt(khtop*kvtop))*log((geofac*
     &                (zbotdr(1)-zintf))/wetper(1))
          totres    = rver+rhor+rrad+entres
          qdrain(1) = dh/totres
 
        ENDIF

C --- drainage flux calc. using given drainage/infiltration resistance
      elseif (dramet.EQ.3) then

        DO 1000 LEV = 1,NRLEVS

          FLDRY = .FALSE.
          if (swdtyp(lev).EQ.1) then
            dh = gwl-zbotdr(lev)
          elseif (swdtyp(lev).eq.2) then
C ---       first copy to 1-dimensional table TEMPTAB
            DO 12 I = 1,2*MAOWL 
12          TEMPTAB(I) = OWLTAB(LEV,I)
            if (afgen (TEMPTAB,2*MAOWL,t+1.0)-zbotdr(lev).lt.1.0e-3) 
     &      FLDRY = .TRUE.  
            dh = gwl- afgen (TEMPTAB,2*MAOWL,t+1.0)
            if (FLDRY) dh = gwl-zbotdr(lev)
          endif
          if (abs(gwl).lt.1.0e-7) dh = dh + pond

          if (dh.ge.0.0) then
C ---       drainage
            qdrain(lev) = dh/drares(lev)
            if (swallo(lev).eq.2) qdrain(lev) = 0.0
          else
C ---       infiltration
            qdrain(lev) = dh/infres(lev)
            if (swallo(lev).eq.3.or.FLDRY) qdrain(lev) = 0.0
          endif

1000    CONTINUE

C --- drainage flux from table with gwlevel - flux data pairs
      elseif (dramet.eq.1) THEN
        qdrain(1) = afgen (qdrtab,50,abs(gwl))
      endif

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE BOCODRE (SWSEC,SWSRF,NRSRF,NRPRI,GWL,ZBOTDR,TALUDR,
     & WIDTHR,POND,PONDMX,SWDTYP,DT,WLS,WLP,DRAINL,L,RDRAIN,RINFI,
     & RENTRY,REXIT,GWLINF,WETPER,QDRAIN,QDRD,T,IMPEND,NMPER,WSCAP,WST)
C ----------------------------------------------------------------------
C     Date               : 05/06/98                        
C     Purpose            :        

C --- Calculate drainage/infiltration fluxes for all levels: qdrain(level).
C --- Summate fluxes to secondary system: qdrd
C --- Given present storage (wst), qdrd and wscap(imper), check if the
C --- system falls dry. If so reduce drainage fluxes proportionally in 
C --- such a way that total drainage flux equals available amount 
C --- (= wst + wscap).

C     Subroutines called : -                                           
C     Functions called   : -                                     
C     File usage         : -                                           
C ----------------------------------------------------------------------  
      IMPLICIT NONE

C --- global
      INTEGER SWSEC,SWSRF,NRSRF,NRPRI,SWDTYP(5),IMPEND(10),NMPER

      REAL    GWL,ZBOTDR(5),TALUDR(5),WIDTHR(5),POND,PONDMX,WLS,WLP
      REAL    DRAINL(5),L(5),WETPER(5),RINFI(5),REXIT(5),GWLINF(5),DT,T
      REAL    RDRAIN(5),RENTRY(5),QDRAIN(5),QDRD,WST
      REAL    WSCAP(10)

C ----------------------------------------------------------------------
C --- local
      INTEGER level,imper

      REAL    dh,qdrdm,qdratio,swdepth,swexbrd,dvmax,wstmax,wl,rd,re

C ----------------------------------------------------------------------
C --- summate fluxes for use by swballev and swlevbal
      qdrd = 0.0
      do 500 level = 1,nrsrf

C ---   surface water level
        if (swsrf.ge.2) then
          if (level.gt.nrpri) then
            wl = wls
          else
            wl = wlp
          endif
        endif

C ---   drainage fluxes are set to zero if both groundwater level and surface 
C ---   water level are above ponding sill (so the nonzero drainage flux is only 
C ---   computed if either the gwl or the wl is below pondmx)
        if (wl .lt. pondmx .or. gwl .lt. pondmx) then

C ---   channel is active medium if either groundwater or surface water
C ---   level is above channel bottom
          if (gwl.gt.(zbotdr(level)+0.001) .or. 
     &          wl.gt.(zbotdr(level)+0.001)) then

            if (wl .le. (zbotdr(level)+0.001).or.swsrf.eq.1) then

C ---       only groundw. level above channel bottom; bottom is dr. base
              drainl(level) = zbotdr(level)

C ---       wetted perimeter only computed for open channels
C ---       (for drains it is input) 
              if (swdtyp(level) .eq. 0) then
                wetper(level) = widthr(level)
              endif
            else
C ---       surface water level above channel bottom
              drainl(level) = wl
              if (swdtyp(level) .eq. 0) then
                swdepth = wl-zbotdr(level)
                swexbrd = (wl-zbotdr(level))/taludr(level)
                wetper(level) = widthr(level) +
     &            2*sqrt(swdepth**2 + swexbrd**2) 
              endif
            endif

C ---     drainage flux (cm/d)
            dh = gwl - drainl(level)
            if (gwl.gt.-0.1) dh = dh+pond
            if (dh.lt.0.0 .and.gwl.lt.gwlinf(level)) then
              dh = gwlinf(level)-drainl(level)
            endif

            if (dh.gt.0.0) then
              rd = rdrain(level)
              re = rentry(level)
            else
              rd = rinfi(level)
              re = rexit(level)
            endif 
            if (swdtyp(level).eq.0) then
              qdrain(level) = dh / ((rd + re*l(level)/wetper(level)))
            else
              qdrain(level) = dh/rd
            endif 
          else
            if (swdtyp(level) .eq. 0) then
              wetper(level) = 0.0
            endif
            dh = 0.0
            qdrain(level) = 0.0
          endif
c
	  else
	    qdrain(level) = 0.0
        endif
c
        if (swsrf.ge.2.and.level.gt.nrpri) then

C ---     qdrd is total flux to or from secondary system
          qdrd = qdrd + qdrain(level)
        endif
500   continue

C ----------------------------------------------------------------------
C --- check for system falling dry (only for swsec = 2):
      if (swsec .eq. 1) return

      if (swsrf.eq.1) then
        do 10 level = 1,nrsrf
          if (qdrain(level).lt.0.0) then
            qdrain(level) = 0.0
          endif
10      continue
      elseif (swsrf.ge.2) then

C ---   determine which management period the model is in:
        imper   = 0
 800    imper   = imper + 1
        if (imper .gt. nmper) stop 'BOCODRE: err. sw-management periods'
        if (int(T+1.0) .gt. impend(imper)) goto 800

C ---   determine whether the system will become empty
        dvmax  = (qdrd + wscap(imper)) * dt
        wstmax = wst + dvmax

        if (wstmax .lt. 0.0) then
C ---     storage decreases to below zero, then the surface water system 
C ---     falls dry; make the total infiltration exactly equal to the
C ---     available amount:
          qdrdm = - (wst + wscap(imper)*dt) / dt
          qdratio = qdrdm / qdrd
          if (qdratio .gt. 1.0 .or. qdratio .lt. 0.0) then
            PRINT *, qdratio,qdrdm,wst,wscap(imper),dt
            stop 'BOCODRE: error algorithm swbal'
          endif

          do 820 level=1+NRPRI,nrsrf
            qdrain(level) = qdrain(level)*qdratio
820       continue
          qdrd = qdrdm
        endif
      endif

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE BOCOTOP (POND,REVA,NIRD,DT,QTOP,QBOT,QDRTOT,
     & KMEAN,K,H,DISNOD,LAYER,FLGENU,COFGEN,THETA,THETIM,DZ,
     & HTABLE,THETLO,THETHI,KTABLE,ALFAMG,FTOPH,ARFLUX,THETAR,
     & THETAS,KSE99,KSAT,SWMOBI,FMOBIL,VOLSAT,VOLACT,ACRACK,QCRACK,
     & FLTSAT,HSURF,FLLAST,FLRAIC,DTMIN,WTOPLAT,FLREVA,NUMNOD,QROSUM,
     & QCOMP,FPEGWL,NPEGWL,Q,SWBOTB,GWLINP)
C ----------------------------------------------------------------------
C     Date               : 02/07/1998                                     
C     Purpose            : determines the values of the boundary       
C                          conditions at the top of the profile        
C     Formal parameters  :                                             
C     Subroutines called : -                                           
C     Functions called   : hconode,thenode                                 
C     File usage         : -                                           
C --------------------------------------------------------------------  
      IMPLICIT NONE
      INCLUDE 'PARAM.FI' 

C --- global
      INTEGER LAYER(MACP),THETLO(MAHO),THETHI(MAHO),SWMOBI,NUMNOD,NODE
	INTEGER NPEGWL,SWBOTB

      REAL    POND,REVA,NIRD,DT,QTOP,QBOT,QDRTOT,DISNOD(MACP+1),WTOPLAT
      REAL    FMOBIL(MACP),ARFLUX,ACRACK,QCRACK,HSURF,QTOP1,DTMIN,QROSUM
      REAL    QCOMP,DZ(MACP),GWLINP
      REAL*8  KSURF,HCONODE,KMEAN(MACP+1),K(MACP+1),H(MACP)
      REAL*8  COFGEN(8,MAHO),THETA(MACP),THETIM(MAHO)
      REAL*8  HTABLE(MAHO,99),KTABLE(MAHO,99),ALFAMG(MACP)
      REAL*8  THETAR(MACP),THETAS(MACP),THENODE,KSE99(MAHO),KSAT(MAHO)
      REAL*8  VOLACT,VOLSAT,Q(MACP+1)

      LOGICAL FLGENU(MAHO),FTOPH,FLTSAT,FLLAST,FLRAIC,FLREVA,FPEGWL
C ----------------------------------------------------------------------
C --- local
      INTEGER i,lay
      REAL    inflow,qmax,qsurf,hatm,vair,Emax,Imax

C ----------------------------------------------------------------------
C --- pressure head of the atmosphere
      hatm  = -2.75E+05
C --- hydraulic conductivity corresponding with this pressure head
      ksurf = hconode (1,THENODE(1,DBLE(HATM),LAYER,FLGENU,
     &        COFGEN,HTABLE,THETLO,ALFAMG,THETAR,THETAS),LAYER,
     &        FLGENU,COFGEN,THETAR,THETAS,THETLO,THETHI,KTABLE,
     &        KSE99,KSAT,SWMOBI,FMOBIL)

C --- determine potential flux at the top of the profile
      flreva = .false.
C --- save qtop from previous timestep
      qtop1 = qtop
      if (pond.gt.1.0e-6) then
        qtop = reva - (pond - wtoplat)/dt
     &       - (ARFLUX+NIRD)*(1.0-acrack) + qcomp
      else
        qtop = reva - (ARFLUX+NIRD)*(1.0-acrack) + qcomp
      end if  

c --- decrease time step at transition evaporation --> large infiltration
      if (qtop1 .gt. 0.001 .and. qtop .lt. -1.0 .and. pond.lt.1.0e-7
     &  .and. dt .gt. (dtmin+1.e-9)) then
        dt = dtmin
C ---   qtop opnieuw berekenen
        qtop = reva-(pond-wtoplat)/dt-(ARFLUX+NIRD)*(1.0-acrack)+qcomp
        if (fllast) fllast = .false.
        if (flraic) flraic = .false.
      endif        

C --- maximum evaporation rate according to Darcy
      kmean(1) = 0.5*(ksurf+k(1))
      Emax = real(kmean(1) * (h(1)-hatm) / disnod(1) - kmean(1))

C --- maximum infiltration rate according to Darcy
      kmean(1) = 0.5*(ksat(1)+k(1))
      Imax = real(kmean(1) * (pond-h(1)) / disnod(1) + kmean(1))
	Imax = max(ksat(1),Imax)

C --- potential flux at soil surface
      qsurf = min(qtop,Emax)
      qsurf = max(qsurf,-Imax)

C --- determine inflow
      if (fpegwl) then
C ---   perched groundwater level exists
        inflow = (- qsurf + q(npegwl+1)) * dt
	else
C ---   just phreatic groundwater level
        inflow = (qbot - qsurf - qrosum - qdrtot + qcrack) * dt
      endif

C --- set flux boundary condition
      ftoph = .false.

c --- determine whether soil profile is saturated
      fltsat = .true.
      do 100 node = 1,numnod
        if (h(node) .lt. 0.0) fltsat = .false.
 100  continue      

      if (fltsat) then
c ---   soil profile was saturated
        if (inflow .gt. -1.0e-6) then
C ---     profile remains saturated, head boundary condition
          ftoph    = .true.
          hsurf    = inflow
          kmean(1) = ksat(1)
        else
C ---     profile becomes unsaturated
          if (dt .gt. (dtmin+0.001)) then
C ---     decrease time step for numerical stability
            dt = 0.001
C ---       qtop opnieuw berekenen
            qtop = reva - (pond - wtoplat)/dt 
     &           - (ARFLUX+NIRD)*(1.0-acrack) + qcomp
            if (fllast) fllast = .false.
            if (flraic) flraic = .false.
          endif

          if (qtop .ge. 0.0) then
c ---       maximum evaporation flux soil
            if (qtop.gt.Emax) then
              ftoph  = .true.
              flreva = .true.
              hsurf  = hatm
            endif             
          else
c ---       maximum infiltration flux soil
            if ((qtop .lt. -ksat(1)) .and. (qtop .lt. (-Imax))) then 
              ftoph = .true.
              hsurf = pond
            endif
          endif
        endif
      else   

c ---   soil profile was unsaturated 

c ---   air volume in case of perched groundwater level
        if (fpegwl) then
          vair = 0.0
          do 120 i = 1,npegwl
            lay    = layer(i)
            vair = vair + real(thetas(i) - theta(i) - 
     &                         (1.0-fmobil(i))*thetim(lay))*dz(i)
 120      continue
c ---   air volume in case of phreatic groundwater level
	  else
          vair = volsat-volact
	  endif

        if (inflow .ge. vair) then
C ---     profile becomes saturated
          ftoph    = .true.
          if (swbotb .eq. 1) then
            hsurf = gwlinp
	    else
            hsurf = real(inflow - vair)
	    endif
          kmean(1) = ksat(1)
        else
C ---     profile remains unsaturated
          if (qtop .ge. 0.0) then
C ---       maximum evaporation flux soil
            if (qtop .gt. Emax) then
              ftoph = .true.
              flreva = .true.
              hsurf = hatm
            endif             
          else
C ---       maximum infiltration flux soil
            if ((qtop .lt. -ksat(1)) .and. (qtop .lt. (-Imax))) then 
              ftoph = .true.
              hsurf = pond 
            endif
          endif
        endif

      endif               

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE CALCGWL(GWL,GWLBAK,NUMNOD,H,Z,DZ,SWBOTB,POND,NODGWL,
     &                   FPEGWL,NPEGWL)
C ----------------------------------------------------------------------
C     Date               : 22/07/96                                    
C     Purpose            : search for the watertable and perched       
C                          watertable(s) (if existing).        
C     Formal parameters  :                                             
C     Subroutines called : -                                           
C     Functions called   : -                                     
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

C --- global
      INTEGER  NUMNOD,SWBOTB,NODGWL,NPEGWL
     
      REAL     GWL,GWLBAK(4),Z(MACP),DZ(MACP),POND
      REAL*8   H(MACP)

	LOGICAL  FPEGWL

C ----------------------------------------------------------------------
      INTEGER  node,i
      REAL     gwprod1,gwprod2
c --- REAL oscil

      LOGICAL  flsat
C ----------------------------------------------------------------------
C --- set initial values
      if (swbotb.ne.1) then
        gwl       = 999.
      end if
      flsat     = .false.
      nodgwl    = numnod + 1
      fpegwl    = .false.

C --- search for ground watertable
      if (h(numnod).ge.0.0d0) then
        flsat  = .true.
      endif

      do 200 node = numnod-1,1,-1
          if (flsat.and.h(node).lt.0.0d0) then
              gwl = real(z(node+1) + h(node+1) / (h(node+1)-h(node))
     $                 * 0.5 * (dz(node) + dz(node+1))) 
             flsat   =.false.
             nodgwl  = node
          end if
 200  continue

C --- groundwater level near soil surface
      if (flsat) then
        if (pond .lt. 1.e-8) then
          gwl = real(z(1) + h(1))
        else
          gwl = pond
        endif
        nodgwl = 1
      endif 
 
c --- search for perched groundwater table
      do 300 node = numnod,2,-1
c ---   first search for transition to saturated part 
        if ((.not.fpegwl) .and. (h(node).lt.0.0d0)
     &	                .and. (h(node-1).gt.0.0d0)) then            
          do 400 i = node-1,2,-1
c ---       next search for transition to unsaturated part 
            if ((.not.fpegwl) .and. (h(i).gt.0.0d0)
     &	                    .and. (h(i-1).lt.0.0d0)) then            
              fpegwl  =.true.
              npegwl  = i - 1
            end if
 400      continue
        endif
 300  continue

C --- warning gwl below profile
      if ((swbotb.eq.3.or.swbotb.eq.4).and.gwl.gt.998.) then
        stop 'Groundwater table below lower boundary'
      endif

C --- updating registration of last four groundwater levels, for noting 
C     oscillation
        gwlbak(1) = gwlbak(2)
        gwlbak(2) = gwlbak(3)
        gwlbak(3) = gwlbak(4)
        gwlbak(4) = gwl

        gwprod1 = (gwlbak(2)-gwlbak(1))*(gwlbak(3)-gwlbak(2))
        gwprod2 = (gwlbak(3)-gwlbak(2))*(gwlbak(4)-gwlbak(3))

        if (gwprod1.lt.0.0 .and. gwprod2.lt.0.0) then
C       tijdelijk !! 
c          oscil = abs(gwlbak(3)-gwlbak(2)) 
c          if (oscil.gt.osgwlm.and.(gwl.lt.-10.0.or.gwl.gt.5.0))
c     &  then
c           write(6,9997) i,oscil
c 9997      format(/' >>gw-level(',i1,') oscillation of ',f4.1,' cm;',
c     &        'advise reduction of dtmax') 
c          endif
        endif

      return
      end

C ----------------------------------------------------------------------
      subroutine crack (layer,nncrack,thetsl,theta,shrina,shrinb,shrinc,
     & acrack,wtoplat,geomf,pond,numnod,adsflu,thetcr,z,dz,qcrack,
     & moisr1,moisrd,crackw,flgenu,cofgen,thetar,thetas,thetlo,thethi,
     & ktable,kse99,ksat,swmobi,fmobil,h,diampol,disnod,rapdra,rapcoef,
     & cralev)
C ----------------------------------------------------------------------
C      Date               : 3/3/98                                    
C      Purpose            : infiltration into cracks, absorption to     
C                           soil matrix, rapid drainage                 
C      Subroutines called :
C      Functions called   :
C      File usage         :
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

C --- global
      INTEGER swmobi,nncrack,layer(MACP),numnod,thetlo(MAHO)
      INTEGER thethi(MAHO)

      REAL    shrina,shrinb,shrinc,acrack,wtoplat,geomf,pond,cralev
      REAL    adsflu(MACP),thetcr(MAHO),z(MACP),dz(MACP),qcrack,moisr1
      REAL    moisrd
      REAL    crackw,fmobil(MACP),diampol,disnod(MACP+1),rapdra,rapcoef

      REAL*8  thetsl(MAHO),theta(MACP),hconode,cofgen(8,MAHO)
      REAL*8  ktable(MAHO,99)
      REAL*8  ksat(MAHO),kse99(MAHO),thetar(MACP),thetas(MACP),h(MACP)

      LOGICAL flgenu(MAHO)
C ----------------------------------------------------------------------
C --- local
      INTEGER lay,node

      REAL    vsolid,moisr,voidr,vapore,vshrink,subsid,vcrack
      REAL    totalv,conduc,ratio
C ----------------------------------------------------------------------

C --- shrinkage volume and area crack at soil surface
      lay = layer(nncrack)
      if (theta(nncrack) .gt. (thetsl(lay)-0.01D0)) then
        acrack = 0.0
        wtoplat = 0.0
      else
        vsolid = real(1.0d0 - thetsl(lay))
        moisr = real(theta(nncrack) / vsolid)
        if (moisr .lt. moisr1) then
          voidr = shrina / exp(shrinb*moisr) + shrinc * moisr
        else
          voidr = moisr1 + moisrd
        endif
        vapore = voidr * vsolid
        vshrink = real(thetsl(lay) - vapore)
        subsid = 1.0 - (1.0 - vshrink) ** (1.0 / geomf)
        vcrack = vshrink - subsid
        acrack = vcrack / (1.0 - subsid)
C ---   lateral flow due to ponding at the soil surface 
        wtoplat = pond
      endif

C --- initialize values
      do 50 node = 1,numnod
        adsflu(node) = 0.0
 50   continue
      totalv = 0.0
      qcrack = 0.0
      cralev = 0.0

C --- determine depth of crack
      node = numnod
      lay  = layer(node)
 60   if (theta(node).gt.(thetcr(lay) - 1.0e-4) .and. node.gt.1) then
        node = node - 1
        lay  = layer(node)
        goto 60
      endif

C --- skip calculation when cracks are closed until soil surface
      if (node.eq.1 .and. theta(1).gt.(thetsl(1)-0.01D0)) goto 70

C --- crack volume for each node 
 65   if (theta(node) .gt. (thetsl(lay)-0.01D0)) then
        if (node .gt. 1) then
          node = node -1
          lay = layer(node)
          goto 65
        endif
      else
        vsolid = real(1.0d0 - thetsl(lay))
        moisr = real(theta(node) / vsolid)
        if (moisr .lt. moisr1) then
          voidr = shrina / exp(shrinb*moisr) + shrinc * moisr
        else
          voidr = moisr1 + moisrd
        endif
        vapore = voidr * vsolid
        vshrink = real(thetsl(lay) - vapore)
        subsid = 1.0 - (1.0 - vshrink) ** (1.0 / geomf)
        vcrack = (vshrink - subsid)*dz(node)
        totalv = totalv + vcrack

c ---   determine lateral infiltration flux from crack 
        if (totalv .lt. crackw) then

c ---   compartment participates with full height 
          conduc = real(hconode (node,theta(node),LAYER,FLGENU,COFGEN,
     &           THETAR,THETAS,THETLO,THETHI,KTABLE,KSE99,KSAT,SWMOBI,
     &           FMOBIL))
          adsflu(node) = real(- conduc*24*dz(node)*h(node)/(diampol*
     &                 diampol))
          qcrack = qcrack + adsflu(node)
          if (node .gt. 1) then
            node = node -1
            lay = layer(node)
            goto 65
          endif
        else
c ---   compartment participates with part of total height 
          ratio  = (crackw - (totalv - vcrack)) / vcrack
          cralev = z(node) - 0.5 * disnod(node+1) + ratio * dz(node)
          conduc = real(hconode (node,theta(node),LAYER,FLGENU,COFGEN,
     &           THETAR,THETAS,THETLO,THETHI,KTABLE,KSE99,KSAT,SWMOBI,
     &           FMOBIL))
                 
          adsflu(node) = real(- conduc*24*dz(node)*h(node)/(diampol*
     &                   diampol)* ratio)
          qcrack = qcrack + adsflu(node)
        endif

      endif

C --- rapid drainage
 70   rapdra = rapcoef * crackw

      return
      end

************************************************************************
      Subroutine Devries (NumNod,theta,THETAS,HeaCap,HeaCon,FQUARTZ,
     &           FCLAY,FORG)
************************************************************************
** Purpose:    Calculate soil heat capacity and conductivity for each  *
**             compartment by full de Vries model                      *     
** References:                                                         *
** Description:                                                        *
** de Vries model for soil heat capcity and thermal conductivity.      * 
** Heat capacity is calculated as average of heat capacities for each  *
** soil component. Thermal conductivity is calculated as weighted      *
** average of conductivities for each component. If theta > 0.05 liquid*
** water is assumed to be the main transport medium in calculating the *
** weights. If theta < 0.02 air is assumed to be the main transport    *
** medium (there is also an empirical adjustment to the conductivity). *
** For 0.02 < theta < 0.05 conductivity is interpolated.               *
** See: Heat and water transfer at the bare soil surface, H.F.M Ten    *
** Berge (pp 48-54 and Appendix 2)                                     *
************************************************************************
** Input:                                                              *
** NumNod - number of compartments (-)                                 *
** theta/THETAS - volumetric soil moisture/ saturated vol. s. moist (-)*
** Fquartz, Fclay and Forg - volume fractions of sand, clay and org.ma.*
** Output:                                                             *
** HeaCap - heat capacity (J/m3/K)                                     *
** HeaCon - thermal conductivity (W/m/K)                               *
************************************************************************
      Implicit None
      INCLUDE 'PARAM.FI'
 
*     (i) Global declarations                                          *
*     (i.i) Input                                                      *
      Integer NumNod
      Real*8 theta(1:MACP),THETAS(1:MACP)
*     (i.ii)
      Real*8 HeaCap(MACP), HeaCon(MACP)
*     (ii) Local declarations                                          *
      Integer Node
      Real kqa,kca,kwa,koa,kaa,kqw,kcw,kww,kow,kaw
      Parameter (kaa = 1.0, kww = 1.0)
      Real fAir(MACP),fClay(MACP),fQuartz(MACP),fOrg(MACP)
      Real*8 HeaConDry,HeaConWet
*     (iii) Parameter declarations                                     *
*     (iii.i) Physical constants                                       *
*     Specific heats (J/kg/K)                                          *
      Real    cQuartz,cClay,cWat,cAir,cOrg
      Parameter (cQuartz = 800.0, cClay = 900.0, cWat = 4180.0,
     &           cAir = 1010.0, cOrg = 1920.0)
*     Density (kg/m)
      Real dQuartz, dClay, dWat, dAir, dOrg
      Parameter (dQuartz = 2660.0, dClay = 2650.0, dWat = 1000.0,
     &           dAir = 1.2, dOrg = 1300.0)
*     Thermal conductivities (W/m/K)                                   *
      Real    kQuartz,kClay,kWat,kAir,kOrg
      Parameter (kQuartz = 8.8, kClay = 2.92, kWat = 0.57,
     &           kAir = 0.025, kOrg = 0.25)
*     
      Real    GQuartz,GClay,GWat,GAir,GOrg
      Parameter (GQuartz = 0.14, GClay = 0.0 , GWat = 0.14, 
     &           GAir = 0.2, GOrg = 0.5)
*     (iii.ii) theta 0.02, 0.05 and 1.00                               *
      Real  thetaDry,thetaWet
      Parameter (thetaDry = 0.02, thetaWet = 0.05)    
C ----------------------------------------------------------------------
*     (0) Weights for each component in conductivity calculations      *
*     (Calculate these but define as parameters in later version)      *
      kaw = 0.66 / (1.0 + ((kAir/kWat) - 1.0) * GAir) + 0.33 /
     &      (1.0 + ((kAir/kWat) - 1.0) * (1.0 - 2.0 * GAir)) 
      kqw = 0.66 / (1.0 + ((kQuartz/kWat) - 1.0) * GQuartz) + 0.33 /
     &      (1.0 + ((kQuartz/kWat) - 1.0) * (1.0 - 2.0 * GQuartz)) 
      kcw = 0.66 / (1.0 + ((kClay/kWat) - 1.0) * GClay) + 0.33 /
     &      (1.0 + ((kClay/kWat) - 1.0) * (1.0 - 2.0 * GClay)) 
      kow = 0.66 / (1.0 + ((kOrg/kWat) - 1.0) * GOrg) + 0.33 /
     &      (1.0 + ((kOrg/kWat) - 1.0) * (1.0 - 2.0 * GOrg)) 
      kwa = 0.66 / (1.0 + ((kWat/kAir) - 1.0) * GWat) + 0.33 /
     &      (1.0 + ((kWat/kAir) - 1.0) * (1.0 - 2.0 * GWat)) 
      kqa = 0.66 / (1.0 + ((kQuartz/kAir) - 1.0) * GQuartz) + 0.33 /
     &      (1.0 + ((kQuartz/kAir) - 1.0) * (1.0 - 2.0 * GQuartz)) 
      kca = 0.66 / (1.0 + ((kClay/kAir) - 1.0) * GClay) + 0.33 /
     &      (1.0 + ((kClay/kAir) - 1.0) * (1.0 - 2.0 * GClay)) 
      koa = 0.66 / (1.0 + ((kOrg/kAir) - 1.0) * GOrg) + 0.33 /
     &      (1.0 + ((kOrg/kAir) - 1.0) * (1.0 - 2.0 * GOrg)) 

      Do Node = 1,NumNod

*        (1) Air fraction
         fAir(Node) = Sngl (THETAS(Node) - theta(Node))

*        (2) Heat capacity (W/m3/K) is average of heat capacities for  *
*        all components (multiplied by density for correct units)      *
         HeaCap(Node) = fQuartz(Node)*dQuartz*cQuartz + fClay(Node)*
     &                  dClay*cClay + theta(Node)*dWat*cWat + 
     &                  fAir(Node)*dAir*cAir +
     &                  fOrg(Node)*dOrg*cOrg

*        (3) Thermal conductivity (W/m/K) is weighted average of       *
*        conductivities of all components                              *
*        (3.1) Dry conditions (include empirical correction) (eq. 3.44)*
         If (theta(Node).LE.Dble(thetaDry)) Then
            HeaCon(Node) = 1.25 * (kqa*fQuartz(Node)*kQuartz + 
     &                      kca*fClay(Node)*kClay +
     &                      kaa*fAir(Node)*kAir +
     &                      koa*fOrg(Node)*kOrg +
     &                      kwa*theta(Node)*kWat) /
     &   (kqa * fQuartz(Node) + kca * fClay(Node) + kaa * fAir(Node) +
     &    koa * fOrg(Node) + kwa * theta(Node))

*        (3.2) Wet conditions  (eq. 3.43)                              *
         Else If (theta(Node).GE.Dble(thetaWet)) Then
            HeaCon(Node) = (kqw*fQuartz(Node)*kQuartz + 
     &                      kcw*fClay(Node)*kClay +
     &                      kaw*fAir(Node)*kAir +
     &                      kow*fOrg(Node)*kOrg +
     &                      kww*theta(Node)*kWat) /
     &   (kqw * fQuartz(Node) + kcw * fClay(Node) + kaw * fAir(Node) +
     &    kow * fOrg(Node) + kww * theta(Node))

*        (3.3) dry < theta < wet (interpolate)
         Else
*           (3.3.1) Conductivity for theta = 0.02                      *
            HeaConDry = 1.25 * (kqa*fQuartz(Node)*kQuartz + 
     &                      kca*fClay(Node)*kClay +
     &                      kaa*fAir(Node)*kAir +
     &                      koa*fOrg(Node)*kOrg +
     &                      kwa*thetaDry*kWat) /
     &   (kqa * fQuartz(Node) + kca * fClay(Node) + kaa * fAir(Node) +
     &    koa * fOrg(Node) + kwa * thetaDry)
*           (3.3.1) Conductivity for theta = 0.05                      *
            HeaConWet = (kqw*fQuartz(Node)*kQuartz + 
     &                      kcw*fClay(Node)*kClay +
     &                      kaw*fAir(Node)*kAir +
     &                      kow*fOrg(Node)*kOrg +
     &                      kww*thetaWet*kWat) /
     &   (kqw * fQuartz(Node) + kcw * fClay(Node) + kaw * fAir(Node) +
     &    kow * fOrg(Node) + kww * thetaWet)
*         (3.3.3) Interpolate                                          *
          HeaCon(Node) = HeaConDry + (theta(Node)-Dble(thetaDry)) * 
     &                   (HeaConWet - HeaConDry) 
     &                 / Dble(thetaWet - thetaDry)      
         End If

C ---    conversion of capacity from J/m3/K to J/cm3/K
         HEACAP(NODE) = HEACAP(NODE)*1.0E-6

C ---    conversion of conductivity from W/m/K to J/cm/K/d
         HEACON(NODE) = HEACON(NODE)*864.0

      End Do

      Return
      End 

C ----------------------------------------------------------------------
      SUBROUTINE DIVDRA( NumComp, NumDrain,ThickComp,KSAT,LAYER,COFANI,
     &                   GWLEV, DistDrain, FluxDr,FluxDrComp )  
C ----------------------------------------------------------------------
C     Date               : 01/04/98                                          
C     Purpose            : Simulation of lateral waterfluxes in the
C                          saturated zone. In two steps:
C                          1. Calculate bottom-boundaries of
C                             model_discharge_layers;
C                          2. Distribute drainage fluxes over each
C                             model_discharge_layer.
C                          
C     Subroutines called : -                                           
C     Functions called   : -                                     
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

      INTEGER DrainSequence(5),Icomp,idr,iidr,I
      INTEGER idum,jdr,NumComWatLev,NumComBotDislay(5),NumActDrain
      INTEGER NumDrain,NumComp,LAYER(MACP),ActLevel(5)

      REAL    FacAniso,CondSatHorAv,CondSatVerAV,BotDisLay(5),ThickCum
      REAL    CumThickCondHor,CumThickCondVer,DistDrain(5),Dum
      REAL    FluxDr(5),FluxDrComp(5,MACP),FlowDrDisch(5),HelpFl(5)
      REAL    HelpTh,HelpTr,MaxDepthDislay(5),CondSatHor(MACP)
      REAL    CondSatVer(MACP),Small,ThickComp(MACP),ThickCompSatWatLev
      REAL    ThickCompBotDislay(5),Transmissivity(5),WatLevAv,GWLEV
      REAL    COFANI(MAHO)
      REAL*8  KSAT(MAHO)

      LOGICAL NonExistFluxDr

      data    Small /1.0e-10/
C ----------------------------------------------------------------------
C --- groundwater level converted to cm below surface level 
      WatLevAv = -1*MIN(GWLEV,0.0)

C --- calculation of CondSatHor and CondSatVer
      DO 10 icomp = 1,NumComp
        CondSatHor(icomp) = real(KSAT(LAYER(icomp)))
        CondSatVer(icomp) = real(KSAT(LAYER(icomp))*
     &                      COFANI(LAYER(icomp)))
10    CONTINUE

C --- Initialisation and test whether any drainflux exists

      NonExistFluxDr = .true.
      do idr=1,NumDrain
         if( abs( FluxDr(idr) ) .gt. Small ) NonExistFluxDr = .false.
         do icomp = 1, NumComp
            FluxDrComp(idr,icomp) = 0.0
         end do
      end do
      
      if( NonExistFluxDr ) return

C --- paragraph 2 
C --- Search for compartment with groundwaterlevel (NumComWatLev)

      NumComWatLev = 1
      ThickCum     = ThickComp(1)
      do while (WatLevAv.gt.ThickCum)
         NumComWatLev = NumComWatLev + 1
         ThickCum     = ThickCum + ThickComp(NumComWatLev)
      end do

C --- saturated part (ThickComp_unsat) of compartment with waterlevel
      ThickCompSatWatLev = ThickCum - WatLevAv

C --- paragraph 3
C --- Calculate overall anisotropic factor model profile and 
C --- cumulative transmissivity as a function of depth

      CumThickCondHor = ThickCompSatWatLev * CondSatHor(NumComWatLev)
      CumThickCondVer = ThickCompSatWatLev / CondSatVer(NumComWatLev)
      ThickCum        = ThickCompSatWatLev

      do icomp=NumComWatLev+1,NumComp
         CumThickCondHor = CumThickCondHor + ThickComp(icomp) * 
     &                       CondSatHor(icomp)
         CumThickCondVer = CumThickCondVer + ThickComp(icomp) /
     &                       CondSatVer(icomp)
         ThickCum        = ThickCum + ThickComp(icomp)
      end do
      
      CondSatHorAv      = CumThickCondHor / ThickCum
      CondSatVerAv      = ThickCum / CumThickCondVer
      FacAniso          = sqrt( CondSatVerAv / CondSatHorAv )

C --- paragraph 4      
C --- Calculate maximum depth per drainage system and discharge 
C --- flow rate per drainage system 

      do idr=1,NumDrain
         MaxDepthDislay(idr) = 0.25*DistDrain(idr)*FacAniso+WatLevAv
C ---    beperken tot SWAP profiel dikte
         MaxDepthDislay(idr) = MIN (MaxDepthDislay(idr),
     &                              Thickcum+WatLevAv)
CCC         FlowDrDisch(idr)    = abs(FluxDr(idr)) 
      end do

C --- paragraph 5      
C --- determine sequence of order of drainage systems 

      NumActDrain = 0
      do idr=1,NumDrain
          DrainSequence(idr) = idr
          HelpFl(idr)        = DistDrain(idr)
          if ( abs(FluxDr(idr)) .gt. small ) then
            NumActDrain = NumActDrain+1
            ActLevel(NumActDrain) = idr 
          endif 
      end do
      
      do idr=1,NumDrain-1
         do iidr = idr+1,NumDrain
            if ( HelpFl(idr) .lt. HelpFl(iidr) )then
             dum                 = HelpFl(iidr)
             HelpFl(iidr)        = HelpFl(idr)
             HelpFl(idr)         = dum
             idum                = DrainSequence(iidr)
             DrainSequence(iidr) = DrainSequence(idr)
             DrainSequence(idr)  = idum
C ---        also modify ActLevel( )     
             do I = 1,NumactDrain
               if (idum.eq.ActLevel(I)) ActLevel(I) = idr
             Enddo
            end if
         end do
      end do 
      
      idr = DrainSequence(ActLevel(NumActDrain))
      FlowDrDisch(idr) = abs(FluxDr(idr))
      do iidr=NumActDrain-1,1,-1 
         idr = DrainSequence(ActLevel(iidr))
         jdr = DrainSequence(ActLevel(iidr+1))
         FlowDrDisch(idr) = FlowDrDisch(jdr) + abs(FluxDr(idr))
      end do

C --- paragraph 6
C --- Bottom of 1st order model_discharge_layer
      
      idr = DrainSequence(ActLevel(1))
      Transmissivity(idr)     = CumThickCondHor
      BotDisLay(idr)          = ThickCum + WatLevAv
      NumComBotDislay(idr)    = NumComp
      ThickCompBotDislay(idr) = ThickComp(NumComp)           
      
C --- correction of BotDisLay(1) if D1 < 0.25 L \/(kv/kh) 

      if (abs(FluxDr(idr)).gt.Small) then
         if (BotDisLay(idr) .gt. MaxDepthDislay(idr) )then
            BotDisLay(idr) = MaxDepthDislay(idr)

C ---       determine adjusted transmissivity and compartment 
C ---       number which contains bottom of discharge layer

            NumComBotDislay(idr) = NumComWatLev
            HelpTh               = ThickCompSatWatLev
            Transmissivity(idr)  = ThickCompSatWatLev * 
     &                             CondSatHor(NumComWatLev)
            do while ( BotDisLay(idr)-WatlevAv .gt. HelpTh )      
               NumComBotDislay(idr) = NumComBotDislay(idr) + 1       
               HelpTh               = HelpTh + 
     &                                ThickComp(NumComBotDislay(idr))
               Transmissivity(idr)  = Transmissivity(idr) + 
     &                                ThickComp(NumComBotDislay(idr)) * 
     &                                CondSatHor(NumComBotDislay(idr))              
            end do
            Transmissivity(idr) = Transmissivity(idr) - 
     &                          (HelpTh - BotDisLay(idr)) * 
     &                          CondSatHor(NumComBotDislay(idr))              

C ---       thickness of part of bottom compartment

            ThickCompBotDislay(idr) = ThickComp(NumComBotDislay(idr)) - 
     &                              (HelpTh - BotDisLay(idr)) 
         end if      
      else 
         BotDisLay(idr) = WatLevAv
      end if

C --- paragraph 7
C --- Bottom of 2nd and higher order model_discharge_layers 

C --- for drainage system of orders 2 to NumDrain (number of drains)         

      do iidr=2,NumActDrain

         idr = DrainSequence(ActLevel(iidr)) 
         jdr = DrainSequence(ActLevel(iidr-1))
       
         Transmissivity(idr) = Transmissivity(jdr) * 
     &                         FlowDrDisch(idr) / FlowDrDisch(jdr) 

C                   bottom of discharge layer of order i
C                   and thickness of bottom compartment, and
C                   number of bottom compartment
         
         icomp  = NumComWatLev
         HelpTr = ThickCompSatWatLev * CondSatHor(icomp)
         HelpTh = ThickCompSatWatLev
         do while ( HelpTr .lt. transmissivity(idr) )      
            icomp  = icomp + 1       
            HelpTr = HelpTr + ThickComp(icomp)*CondSatHor(icomp)      
            HelpTh = HelpTh + ThickComp(icomp)       
         end do
         NumComBotDislay(idr)    = icomp
         ThickCompBotDislay(idr) = ThickComp(icomp) - 
     &             ( HelpTr - Transmissivity(idr)) / CondSatHor(icomp)
            BotDisLay(idr)      = WatLevAv + HelpTh +
     &             ( Transmissivity(idr) - HelpTr) / CondSatHor(icomp)

C --- paragraph 8
C --- correction of BotDisLay(idr) if D(idr) < 0.25 L(idr) \/(kv/kh) 

         if (BotDisLay(idr).gt. MaxDepthDislay(idr)) then
            BotDisLay(idr) = MaxDepthDislay(idr)

C ---       transmissivity of order i, thickness 
C ---       of bottom compartment, and number 
C ---       of bottom compartment

            NumComBotDislay(idr) = NumComWatLev
            HelpTh               = ThickCompSatWatLev
            Transmissivity(idr)  = ThickCompSatWatLev * 
     &                             CondSatHor(NumComWatLev)
            do while ( BotDisLay(idr)-WatLevAv .gt. HelpTh )      
               NumComBotDislay(idr) = NumComBotDislay(idr) + 1       
               HelpTh = HelpTh + ThickComp(NumComBotDislay(idr))       
               Transmissivity(idr)  = Transmissivity(idr) + 
     &                               ThickComp(NumComBotDislay(idr)) * 
     &                               CondSatHor(NumComBotDislay(idr))              
            end do
            Transmissivity(idr) = Transmissivity(idr) - 
     &                            (HelpTh - BotDisLay(idr))*
     &                            CondSatHor(NumComBotDislay(idr))              
            ThickCompBotDislay(idr) = ThickComp(NumComBotDislay(idr)) - 
     &                            (HelpTh - BotDisLay(idr)) 
         end if
         
      end do

C --- paragraph 9
C --- Distribute drainage fluxes as lateral fluxes over 
C --- ith order model discharge layers

      do iidr=1,NumActDrain
         idr = DrainSequence(ActLevel(iidr)) 
         FluxDrComp(idr,NumComWatLev) = FluxDr(idr)*ThickCompSatWatLev*
     &                              CondSatHor(NumComWatLev) / 
     &                              Transmissivity(idr)
         do icomp=NumComWatLev+1,NumComBotDislay(idr)-1
            FluxDrComp(idr,icomp) = FluxDr(idr)*ThickComp(icomp)*
     &                              CondSatHor(icomp) / 
     &                              Transmissivity(idr)
         end do
         FluxDrComp(idr,NumComBotDislay(idr)) = FluxDr(idr)*
     &                              ThickCompBotDislay(idr)*
     &                              CondSatHor(NumComBotDislay(idr)) / 
     &                              Transmissivity(idr)
      end do

      return
      end

C ----------------------------------------------------------------------
      REAL*8 FUNCTION DMCNODE (NODE,HEAD,LAYER,FLGENU,COFGEN,THETLO,
     & THETHI,DMCH,DMCC,THETAS,THETAR,ALFAMG,SWMOBI,FM1,PF1,SLOPFM,
     & HTABLE,THETA)
C ----------------------------------------------------------------------
C     Date               : 29/08/95                                          
C     Purpose            : calculate the differential moisture         
C                          capacity (as a function of pressure head)
C     Subroutines called : -                                           
C     Functions called   : thenode                                     
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

C --- global
      INTEGER LAYER(MACP),NODE,THETLO(MAHO),THETHI(MAHO),SWMOBI

      REAL    FM1(MAHO),PF1(MAHO),SLOPFM(MAHO) 

      REAL*8  HEAD,COFGEN(8,MAHO),DMCC(MAHO,99),DMCH(MAHO,99)
      REAL*8  THETAS(MACP)
      REAL*8  THETAR(MACP),ALFAMG(MACP),HTABLE(MAHO,99),THETA(MACP)

      LOGICAL FLGENU(MAHO)
C ----------------------------------------------------------------------
C --- local 

      INTEGER lay,posit

      REAL    fmobile

      REAL*8  deltah,head2,theta2,tresid,tsatu,thenode,alphah
      REAL*8  term1,term2
C ----------------------------------------------------------------------
C --- soil layer of node
      lay = layer(node)

      if (flgenu(lay)) then
C ---   according to van Genuchten
        if (head.gt. -1.0d-8) then
          dmcnode = 1.0d-7
        else
          if (SWMOBI.EQ.1) then
C ---       use numerical evaluation of capacity
            deltah = 0.001 * (1.0e-3 * abs(head)+1.0d0)
            head2 = head + deltah
            if (head2.gt.0.0) then
              deltah = - deltah
              head2 = head + deltah
            endif
            if (head2.gt.-1.0d0) then
              fmobile = fm1(lay)+(0.0-pf1(lay))*slopfm(lay)
            else
              fmobile = fm1(lay)+(log10(abs(real(head2)))-pf1(lay))*
     &        slopfm(lay)
            endif
            fmobile = min (1.0,fmobile)
            fmobile = max (0.3,fmobile)
            tresid  = thetar(node)
            tsatu   = thetas(node)
            thetar(node) = cofgen(1,lay)*fmobile
            thetas(node) = cofgen(2,lay)*fmobile
            theta2 = thenode (node,head2,layer,flgenu,cofgen,
     &               htable,thetlo,alfamg,thetar,thetas)
            thetar(node) = tresid
            thetas(node) = tsatu           
            dmcnode = (theta2 - theta(node))/deltah
          else
C ---       use analytical evaluation of capacity
            alphah = abs (alfamg(node)*head)
C ---       compute |alpha * h| to the power n-1
            term1 = alphah ** (cofgen(6,lay) -1.0d0)
C ---       compute |alpha*h| to the power n
            term2 = term1 * alphah
C ---       add one and raise to the power m+1
            term2 = (1.0d0 + term2) ** (cofgen(7,lay) + 1.0d0)
C ---       divide theta-s minus theta-r by term2
            term2 = (thetas(node)-thetar(node)) / term2
C ---       calculate the differential moisture capacity
            dmcnode = abs(-1.0d0 * cofgen(6,lay) * cofgen(7,lay) * 
     $                alfamg(node) * term2 * term1)
          endif
          if (head.gt.-1.0d0.and.dmcnode.lt.1.0d-7) dmcnode = 1.0d-7
        endif
      else
C ---   according to the tables
        if (head.ge.0.0d0) then
          dmcnode = 1.0d-7
        else
          do 100 posit = thetlo(lay)+1,thethi(lay)
            if (head.le.dmch(lay,posit)) go to 120
 100      continue
 120      dmcnode = dmcc(lay,posit-1)+(head-dmch(lay,posit-1))*
     $              (dmcc(lay,posit)-dmcc(lay,posit-1))/
     $              (dmch(lay,posit)-dmch(lay,posit-1))
        endif
      endif

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE FLUXES (Q,QBOT,DT,INQ,NUMNOD,THETM1,THETA,DZ,QROT,
     & QDRA,QIMMOB,ADSFLU,QTOP,QROSUM,QDRTOT,VOLACT,VOLM1,
     & SWBOTB,QCRACK,FLREVA,POND,WTOPLAT,ARFLUX,NIRD,ACRACK,REVA,QCOMP)
C ----------------------------------------------------------------------
C     Date               : 09/10/98
C     Purpose            : calculates the fluxes between compartments
C     Subroutines called : -                                           
C     Functions called   : -                                     
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

C --- global
      INTEGER NUMNOD,SWBOTB

      REAL    QBOT,DT,INQ(MACP+1),DZ(MACP),QROT(MACP),QDRA(5,MACP)
      REAL    QIMMOB(MACP),POND,WTOPLAT,ARFLUX,NIRD,ACRACK
      REAL    ADSFLU(MACP),QTOP,QROSUM,QDRTOT,QCRACK,REVA,QCOMP
      REAL*8  Q(MACP+1),THETM1(MACP),THETA(MACP),VOLACT,VOLM1

      LOGICAL FLREVA

C --- local
      INTEGER i
C ----------------------------------------------------------------------
c --- determine qbot if not specified 

      if (swbotb .eq. 1 .or. swbotb .eq. 5 .or. swbotb .eq. 8) 
     &  qbot = real(qtop + qrosum + qdrtot - qcrack+(volact-volm1)/dt)

C --- calculate fluxes (cm/d) from changes in volume per compartment

      i      = numnod+1
      q(i)   = qbot
      inq(i) = real(inq(i) + q(i) * dt)

      do 100 i = numnod,1,-1
        q(i)   = - real(theta(i)-thetm1(i)+qimmob(i))*dz(i)/dt + q(i+1)-
     &           qrot(i)-qdra(1,i)-qdra(2,i)-qdra(3,i)-qdra(4,i)-
     &           qdra(5,i)+adsflu(i)
        inq(i) = real(inq(i) + q(i)*dt)
100   continue

c --- set final value qtop
      qtop = real(q(1))

c --- determine reduced evaporation rate in case of FLREVA
      if (flreva) reva = max(0.0,qtop + (pond - wtoplat)/dt - qcomp
     &                 + (arflux+nird)*(1.0 - acrack))

      return
      end

C ----------------------------------------------------------------------
      REAL*8 FUNCTION HCONODE (NODE,WCON,LAYER,FLGENU,COFGEN,THETAR,
     & THETAS,THETLO,THETHI,KTABLE,KSE99,KSAT,SWMOBI,FMOBIL)
C ----------------------------------------------------------------------
C     Date               : 29/08/1995                                    
C     Purpose            : calculate hydraulic conductivity (as a     
C                          function of pressure head)
C     Subroutines called : -                                           
C     Functions called   : -                     
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

C --- global
      INTEGER NODE,LAYER(MACP),THETLO(MAHO),THETHI(MAHO),SWMOBI

      REAL    FMOBIL(MACP)
      REAL*8  WCON,COFGEN(8,MAHO),KTABLE(MAHO,99),KSAT(MAHO),KSE99(MAHO)
      REAL*8  THETAR(MACP),THETAS(MACP) 

      LOGICAL FLGENU(MAHO)
C ----------------------------------------------------------------------
C --- local
      INTEGER lay,posit 

      REAL*8  term1,exponl,relsat
C ----------------------------------------------------------------------
C --- soil layer of node
      lay = layer(node)

      if (flgenu(lay)) then

C ---   calculation according to van Genuchten
        relsat = (wcon-thetar(node))/(thetas(node)-thetar(node))
        if (relsat.gt.0.99d0) then
C ---     linear interpolation of k
          hconode = kse99(lay) + (relsat-0.99d0)/0.01
     &              *(ksat(lay)-kse99(lay))
        else
          if (relsat.lt.0.001d0) then
            hconode = 1.0d-10
          else
            exponl  = cofgen(5,lay)/cofgen(7,lay)-2.0d0
            term1   = (1.0d0-relsat**(1.0d0/cofgen(7,lay)))
     &                **cofgen(7,lay)
            hconode = cofgen(3,lay)*(relsat**exponl)*(1.0d0-term1)
     &               *(1.0d0-term1)
            if (SWMOBI.EQ.1) hconode = hconode*fmobil(node)
          endif
        endif

      else
C ---   calculation according to the tables   
        if (wcon.lt.0.01*thetlo(lay)) then
          stop 'HCONODE - calculated water content outside range'
        else
          if (wcon.ge.(thetas(node)-0.001d0)) then
            hconode = ktable(lay,thethi(lay))
          else
            posit   = int(100.0*wcon)
            hconode = ktable(lay,posit)+(ktable(lay,posit+1)-
     &                ktable(lay,posit))*(100.0*wcon-real(posit))
          endif
        endif
          
      endif

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE HEADCALC (NUMNOD,HM1,H,THETM1,THETA,NUMBIT,FTOPH,DT,T,
     & KMEAN,DZ,DISNOD,DIMOCA,QROT,QDRA,POND,QTOP,LAYER,FLGENU,
     & COFGEN,HTABLE,THETLO,THETHI,ALFAMG,THETAR,THETAS,DMCH,DMCC,
     & SWBOTB,SWNUMS,THETOL,REVA,NIRD,QBOT,QDRTOT,K,KTABLE,Q,
     & ARFLUX,KSE99,KSAT,SWMOBI,FMOBIL,VOLSAT,VOLACT,DTMIN,DNOCON,
     & QIMMOB,FM1,PF1,SLOPFM,THETIM,FLLAST,ADSFLU,ACRACK,QCRACK,FLTSAT,
     & HSURF,FLRAIC,WTOPLAT,FLREVA,QROSUM,QCOMP,QDARCY,FPEGWL,NPEGWL,
     & GWLINP)
C ----------------------------------------------------------------------
C     Date               : 23/09/97  
C     Purpose            : calculate pressure heads, water contents,
C                          and conductivities for next time step
C     Subroutines called : bocotop,TriDag                                     
C     Functions called   : hconode,dmcnode,thenode                 
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

C --- global
      INTEGER NUMNOD,NUMBIT,LAYER(MACP),THETLO(MAHO),THETHI(MAHO)
      INTEGER SWBOTB,SWNUMS,DNOCON,SWMOBI,NPEGWL

      REAL    DTMIN,DT,T,DZ(MACP),DISNOD(MACP+1),QROT(MACP)
      REAL    QDRA(5,MACP),POND,QTOP,QROSUM,GWLINP
      REAL    THETOL,REVA,NIRD,QBOT,QDRTOT,ARFLUX,FMOBIL(MACP)
      REAL    QIMMOB(MACP),FM1(MAHO),PF1(MAHO),SLOPFM(MAHO),ADSFLU(MACP)
      REAL    ACRACK,QCRACK,HSURF,WTOPLAT,QCOMP,QDARCY

      REAL*8  HM1(MACP),H(MACP),THETM1(MACP),THETA(MACP),KMEAN(MACP+1)
      REAL*8  DIMOCA(MACP),Q(MACP+1)
      REAL*8  COFGEN(8,MAHO),HTABLE(MAHO,99),ALFAMG(MACP),THETAR(MACP)
      REAL*8  THETAS(MACP),DMCH(MAHO,99),DMCC(MAHO,99),K(MACP+1)
      REAL*8  KTABLE(MAHO,99)  
      REAL*8  KSE99(MAHO),KSAT(MAHO),VOLSAT,VOLACT,THETIM(MAHO)

      LOGICAL FTOPH,FLGENU(MAHO),FLLAST,FLRAIC,FLTSAT,FLREVA,FPEGWL
C ----------------------------------------------------------------------
C --- local
      INTEGER i,j,lay 

      REAL    qimold(MACP),fmobm1(MACP),deno
      REAL*8  thenode,hconode,thoma(MACP),thomb(MACP),thomc(MACP)
      REAL*8  thomf(MACP)
      REAL*8  capold(MACP),dmcnode,hold(MACP),theold(MACP)

C ----------------------------------------------------------------------
C --- store values of h, theta and fmobil
      do 400 i = 1,numnod
       hm1(i)    = h(i)
        thetm1(i) = theta(i)
        fmobm1(i) = fmobil(i)
400   continue

410   numbit = 1

C --- first step :
C --- ============
C --- calculation of coefficients for node = 1
      i = 1
      if (ftoph) then
C ---   h at soil surface prescribed
        thomc(i) = - dt*kmean(i+1)/dz(i)/disnod(i+1)
        thomb(i) = - thomc(i)+dimoca(i)+dt*kmean(1)/disnod(i)/dz(i)
        thomf(i) = dimoca(i)*h(i)-qimmob(i) +
     &             dt/dz(i)*(+kmean(i)-kmean(i+1)-qrot(i)+adsflu(i)
     &             -qdra(1,i)-qdra(2,i)-qdra(3,i)-qdra(4,i)-qdra(5,i))
     &             + dt*kmean(i)*hsurf/disnod(i)/dz(i)
      else
C ---   q at soil surface prescribed
        thomc(i) = - dt*kmean(i+1)/dz(i)/disnod(i+1)
        thomb(i) = - thomc(i) + dimoca(i)
        thomf(i) = dimoca(i)*h(i) -qimmob(i)+
     &             dt/dz(i)*(-qtop-kmean(i+1)-qrot(i)+adsflu(i)
     &             -qdra(1,i)-qdra(2,i)-qdra(3,i)-qdra(4,i)-qdra(5,i))
      endif

C --- calculation of coefficients for 2 < node < numnod
      do 500 i = 2, numnod-1
        thoma(i) = - dt*kmean(i)/dz(i)/disnod(i)
        thomc(i) = - dt*kmean(i+1)/dz(i)/disnod(i+1)
        thomb(i) = - thoma(i) - thomc(i) + dimoca(i)
        thomf(i) = dimoca(i)*h(i) -qimmob(i)+
     &             dt/dz(i)*(kmean(i)-kmean(i+1)-qrot(i)+adsflu(i)
     &             -qdra(1,i)-qdra(2,i)-qdra(3,i)-qdra(4,i)-qdra(5,i))
500   continue

C --- calculation of coefficients for node = numnod
      i = numnod
      if (swbotb .eq. 1 .or. swbotb .eq. 5) then
        thoma(i) = 0.0
        thomb(i) = 1.0d0
        thomf(i) = h(i)
      else
        thoma(i) = - dt*kmean(i)/dz(i)/disnod(i)
        thomb(i) = - thoma(i) + dimoca(i)
        thomf(i) = dimoca(i)*h(i) -qimmob(i)+
     &             dt/dz(i)*(kmean(i)+qbot-qrot(i)+adsflu(i)
     &             -qdra(1,i)-qdra(2,i)-qdra(3,i)-qdra(4,i)-qdra(5,i))
      endif

C --- save old values of h, theta and dimoca
      Do i = 1, numnod
        Hold(i)   = h(i)
        TheOld(i) = theta(i)
        CapOld(i) = DiMoCa(i)
      End Do

C --- Solve the tridiagonal matrix
      Call TriDag(NumNod, thoma, thomb, thomc, thomf, h)

C --- first solution 
      do 530 i = 1,numnod
        lay     = layer(i)
        if (SWMOBI.EQ.1) then
          if (h(i).gt.-1.0d0) then
            fmobil(i) = fm1(lay)+(0.0-pf1(lay))*slopfm(lay)
          else
            fmobil(i) = fm1(lay)+(log10(abs(real(h(i))))-pf1(lay))*
     &                  slopfm(lay)
          endif
          fmobil(i) = min (1.0,fmobil(i))
          fmobil(i) = max (0.3,fmobil(i))
          thetar(i) = cofgen(1,lay)*fmobil(i)
          thetas(i) = cofgen(2,lay)*fmobil(i)
          qimold(i) = qimmob(i)
          qimmob(i) = real((fmobm1(i)-fmobil(i))*thetim(lay))
        endif
        theta(i)  = thenode(i,h(i),LAYER,FLGENU,COFGEN,HTABLE,
     &              THETLO,ALFAMG,THETAR,THETAS)
        dimoca(i) = dmcnode(i,h(i),LAYER,FLGENU,COFGEN,THETLO,THETHI,
     &              DMCH,DMCC,THETAS,THETAR,ALFAMG,SWMOBI,FM1,PF1,
     &              SLOPFM,HTABLE,THETA)
530   continue

C --- iteration step : 
C --- ================

C --- updating coefficients tridiagonal Thomas matrix 

700   i = 1
      if (ftoph) then
C ---   head controlled boundary 
        thomb(i) = - thomc(i)+dimoca(i)+dt*kmean(1)/disnod(i)/dz(i)
        thomf(i) = -theta(i)+thetm1(i)-qimmob(i)+qimold(i)+
     &             dimoca(i) * h(i) +
     &             dt/dz(i)*(+kmean(i)-kmean(i+1)-qrot(i)+adsflu(i)
     &             -qdra(1,i)-qdra(2,i)-qdra(3,i)-qdra(4,i)-qdra(5,i))
     &             + dt*kmean(i)*hsurf/disnod(i)/dz(i)
      else
C ---   flux controlled boundary
        thomb(i) = - thomc(i) + dimoca(i)
        thomf(i) = -theta(i) + thetm1(i)-qimmob(i)+qimold(i)+
     &             dimoca(i) * h(i) +
     &             dt/dz(i)*(-qtop-kmean(i+1)-qrot(i)+adsflu(i)
     &             -qdra(1,i)-qdra(2,i)-qdra(3,i)-qdra(4,i)-qdra(5,i))
      endif
          
      do 550 i = 2,numnod
        thomb(i) = thomb(i) - capold(i) + dimoca(i)
        thomf(i) = thomf(i) - capold(i) * hold(i) + dimoca(i) * h(i)
     &             - theta(i) + theold(i)-qimmob(i)+qimold(i)
550   continue

      i = numnod
      if (swbotb .eq. 1 .or. swbotb .eq. 5) then
        thomb(i) = 1.0d0
        thomf(i) = h(i)       
      endif

      if (swbotb .eq. 8 .and. h(i) .gt. (-disnod(i+1)+0.001)) then
        thoma(i) = 0.0d0
        thomb(i) = 1.0d0
        thomf(i) = - disnod(i+1)
      endif

C --- save old values of h, theta and dimoca
      Do i = 1, numnod
        Hold(i)   = h(i)
        TheOld(i) = theta(i)
        CapOld(i) = DiMoCa(i)
      End Do

C --- Solve the tridiagonal matrix
      Call TriDag(NumNod, thoma, thomb, thomc, thomf, h)

      do 590 i = 1,numnod
        lay     = layer(i)
        if (SWMOBI.EQ.1) then
          if (h(i).gt.-1.0d0) then
            fmobil(i) = fm1(lay)+(0.0-pf1(lay))*slopfm(lay)
          else
            fmobil(i) = fm1(lay)+(log10(abs(real(h(i))))-pf1(lay))*
     &                  slopfm(lay)
          endif
          fmobil(i) = min (1.0,fmobil(i))
          fmobil(i) = max (0.3,fmobil(i))
          thetar(i) = cofgen(1,lay)*fmobil(i)
          thetas(i) = cofgen(2,lay)*fmobil(i)
          qimold(i) = qimmob(i)
          qimmob(i) = real((fmobm1(i)-fmobil(i))*thetim(lay))
        endif
        theta(i) = thenode(i,h(i),LAYER,FLGENU,COFGEN,HTABLE,
     &             THETLO,ALFAMG,THETAR,THETAS)
        dimoca(i) = dmcnode(i,h(i),LAYER,FLGENU,COFGEN,THETLO,THETHI,
     &              DMCH,DMCC,THETAS,THETAR,ALFAMG,SWMOBI,FM1,PF1,
     &              SLOPFM,HTABLE,THETA)
590   continue

C --- only one iteration if SWNUMS = 1
      if (swnums .eq. 1) goto 640

C --- check on convergence of solution
      do 600 i = 1,numnod
        if (abs(h(i)) .lt. 1.0d0) then
          deno = 1.0
        else
          deno = real(h(i))
        endif
        if (abs(theold(i)-theta(i)) .gt. thetol
     &  .or. abs( (h(i)-hold(i)) / deno ) .gt. 0.001d0
     &  .or. h(1) .gt. 50.0d0 ) then
          if (numbit .lt. 6) then
C ---       perform another iteration
            numbit = numbit + 1
            CALL BOCOTOP (POND,REVA,NIRD,DT,QTOP,QBOT,QDRTOT,
     &        KMEAN,K,H,DISNOD,LAYER,FLGENU,COFGEN,THETA,THETIM,DZ,
     &        HTABLE,THETLO,THETHI,KTABLE,ALFAMG,FTOPH,ARFLUX,THETAR,
     &        THETAS,KSE99,KSAT,SWMOBI,FMOBIL,VOLSAT,VOLACT,ACRACK,
     &        QCRACK,FLTSAT,HSURF,FLLAST,FLRAIC,DTMIN,WTOPLAT,FLREVA,
     &        NUMNOD,QROSUM,QCOMP,FPEGWL,NPEGWL,Q,SWBOTB,GWLINP)
            goto 700
          else
            if (dt .gt. 3.0*dtmin) then
C ---         start headcalc again with smaller timestep
              dt = dt / 3.0
              if (FLLAST) FLLAST=.FALSE.
              if (FLRAIC) FLRAIC=.FALSE.
              if (SWMOBI.EQ.1) then
                qimmob(1) = 0.0
                fmobil(1) = fmobm1(1)
                thetar(1) = cofgen(1,1)*fmobil(1)
                thetas(1) = cofgen(2,1)*fmobil(1)
              endif
              h(1)      = hm1(1)
              theta(1)  = thetm1(1)
              k(1)      = hconode(1,theta(1),LAYER,FLGENU,COFGEN,
     &                    THETAR,THETAS,THETLO,THETHI,KTABLE,
     &                    KSE99,KSAT,SWMOBI,FMOBIL)
              dimoca(1) = dmcnode(1,hm1(1),LAYER,FLGENU,COFGEN,THETLO,
     &                    THETHI,DMCH,DMCC,THETAS,THETAR,ALFAMG,
     &                    SWMOBI,FM1,PF1,SLOPFM,HTABLE,THETA) 
              do 620 j = 2,numnod
                lay = layer(j)
                if (SWMOBI.EQ.1) then
                  qimmob(j) = 0.0
                  fmobil(j) = fmobm1(j)
                  thetar(j) = cofgen(1,lay)*fmobil(j)
                  thetas(j) = cofgen(2,lay)*fmobil(j)
                endif
                h(j)      = hm1(j)
                theta(j)  = thetm1(j)
                k(j)      = hconode(j,theta(j),LAYER,FLGENU,COFGEN,
     &                      THETAR,THETAS,THETLO,THETHI,KTABLE,
     &                      KSE99,KSAT,SWMOBI,FMOBIL)
                dimoca(j) = dmcnode(j,h(j),LAYER,FLGENU,COFGEN,THETLO,
     &                      THETHI,DMCH,DMCC,THETAS,THETAR,
     &                      ALFAMG,SWMOBI,FM1,PF1,SLOPFM,HTABLE,THETA)
                kmean(j)  = 0.5*(k(j) + k(j-1))
620           continue
              kmean(numnod+1) =k (numnod)
              CALL BOCOTOP (POND,REVA,NIRD,DT,QTOP,QBOT,QDRTOT,
     &          KMEAN,K,H,DISNOD,LAYER,FLGENU,COFGEN,THETA,THETIM,DZ,
     &          HTABLE,THETLO,THETHI,KTABLE,ALFAMG,FTOPH,ARFLUX,THETAR,
     &          THETAS,KSE99,KSAT,SWMOBI,FMOBIL,VOLSAT,VOLACT,ACRACK,
     &          QCRACK,FLTSAT,HSURF,FLLAST,FLRAIC,DTMIN,WTOPLAT,FLREVA,
     &          NUMNOD,QROSUM,QCOMP,FPEGWL,NPEGWL,Q,SWBOTB,GWLINP)
              goto 410
            else
C ---         no convergence !! continue, but store daynumber
              if (dnocon .eq. 0) dnocon = INT(T)
            endif
          endif
        endif
600   continue 


640   CONTINUE  

C --- flux at soil surface according to Darcy
      if (ftoph) then
        qdarcy = real(- kmean(1) * ((hsurf - h(1)) / disnod(1) + 1.0d0))
      else
        qdarcy = qtop
      endif

C --- determine top boundary flux in case of ponding or limited evaporation
      if (ftoph) qtop = qdarcy 

C --- adjust conductivities
      k(1) = hconode(1,theta(1),LAYER,FLGENU,COFGEN,THETAR,THETAS,
     &       THETLO,THETHI,KTABLE,KSE99,KSAT,SWMOBI,FMOBIL)
      do 650 i = 2,numnod
        k(i)     = hconode(i,theta(i),LAYER,FLGENU,COFGEN,THETAR,
     &             THETAS,THETLO,THETHI,KTABLE,KSE99,KSAT,SWMOBI,FMOBIL)
        kmean(i) = 0.5*(k(i)+k(i-1))
650   continue
      kmean(numnod+1) = k(numnod)

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE INITSOL (NUMLAY,SOLFIL,ENVSTR,FLGENU,THETHI,THETLO,
     & HTABLE,KTABLE,THETSL,KSAT,DMCH,DMCC,COFGEN,SWSCAL,ISCLAY,RUNNR,
     & KSE99,NUMNOD,DZ,Z,DISNOD,INPOLB,INPOLA,BOTCOM,
     & LAYER,THETAS,THETAR,SWHYST,INDEKS,ALFAMG,SWINCO,THETA,
     & THETAI,H,SWBOTB,HGITAB,T,HI,GWLTAB,GWLI,GWL,GWLBAK,
     & SWSOLU,CMLI,CML,CIL,SAMINI,PSAND,PSILT,PCLAY,ORGMAT,
     & CL,CMSY,KF,FREXP,CISY,VOLM1,VOLACT,VOLINI,VOLSAT,CREF,
     & THETM1,HM1,DIMOCA,K,KMEAN,THETIM,SWMOBI,FMOBIL,KMOBIL,PF1,FM1,
     & PF2,FM2,SLOPFM,QIMMOB,SWCRACK,SHRINA,MOISR1,MOISRD,ZNCRACK,
     & SHRINB,SHRINC,NNCRACK,ACRACK,QCRACK,RAPDRA,WTOPLAT,ADSFLU,
     & CKWM1,LOGF,FSCALE,DT,POND,BDENS,FQUARTZ,FCLAY,FORG)

C ----------------------------------------------------------------------
C     Date               : 15/09/97                                         
C     Purpose            : initialize soil profile data               
C     Subroutines called : RDSOL,WATCON                                
C     Functions called   : PRHNODE,THENODE,DMCNODE,HCONODE,AFGEN
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

C --- global
      INTEGER NUMLAY,THETHI(MAHO),THETLO(MAHO),SWSCAL,ISCLAY,RUNNR
      INTEGER NUMNOD,BOTCOM(MAHO),LAYER(MACP),SWHYST,INDEKS(MACP),SWINCO
      INTEGER SWBOTB,SWSOLU,NNCRACK,SWMOBI,LOGF,SWCRACK

      REAL FMOBIL(MACP),DZ(MACP),Z(MACP),DISNOD(MACP+1),INPOLA(MACP)
      REAL INPOLB(MACP),HGITAB(50),T,GWLTAB(732),GWL,CMLI(MACP)
      REAL CML(MACP),CIL(MACP),CL(MACP),CMSY(MACP),KF,CISY(MACP)
      REAL FM1(MAHO),SLOPFM(MAHO),PF1(MAHO)
      REAL SHRINA,MOISR1,MOISRD,ZNCRACK,SHRINB,SAMINI
      REAL SHRINC,ACRACK,QCRACK,RAPDRA,WTOPLAT,ADSFLU(MACP)
      REAL PF2(MAHO),FM2(MAHO),QIMMOB(MACP),KMOBIL,AFGEN,FREXP
      REAL GWLI,CREF,GWLBAK(4),CKWM1,CRACKW,DT,POND
      REAL PCLAY(MAHO),PSAND(MAHO),PSILT(MAHO),BDENS(MAHO),FQUARTZ(MACP)
      REAL FCLAY(MACP),FORG(MACP),FSCALE(MAYRS),ORGMAT(MAHO)

      REAL*8 PRHNODE,THENODE,DMCNODE,HCONODE
      REAL*8 HTABLE(MAHO,99),KTABLE(MAHO,99),THETSL(MAHO),KSAT(MAHO)
      REAL*8 DMCC(MAHO,99)
      REAL*8 DMCH(MAHO,99),COFGEN(8,MAHO),KSE99(MAHO),THETAS(MACP)
      REAL*8 THETAR(MACP),ALFAMG(MACP),THETA(MACP),THETAI(MACP),H(MACP)
      REAL*8 HI(MACP)
      REAL*8 VOLM1,VOLACT,VOLINI,VOLSAT,THETM1(MACP),HM1(MACP)
      REAL*8 DIMOCA(MACP),K(MACP+1),KMEAN(MACP+1),THETIM(MAHO)

      CHARACTER   ENVSTR*50
      CHARACTER*8 SOLFIL(MAHO)

      LOGICAL FLGENU(MAHO)
C ----------------------------------------------------------------------
C --- local
      INTEGER LAY,NODE,I,I2
 
      REAL    beta1,beta2,func,deri,ARFLUX,NIRD,DUMMY,GMINERAL
C ----------------------------------------------------------------------
C --- read input file(s) containing soil physical data
      DO 30 LAY = 1,NUMLAY
        CALL RDSOL (SOLFIL(LAY),ENVSTR,LAY,FLGENU,THETHI,THETLO,HTABLE,
     &  KTABLE,THETSL,KSAT,DMCH,DMCC,COFGEN,SWSCAL,ISCLAY,FSCALE,RUNNR,
     &  KSE99,LOGF,SWHYST)
30    CONTINUE

C --- position of nodal points and distances between them
      Z(1)      = - 0.5*DZ(1)
      DISNOD(1) = - Z(1)
      DO 20 NODE=2,NUMNOD
        Z(NODE)      = Z(NODE-1) - 0.5*(DZ(NODE-1)+DZ(NODE))
        DISNOD(NODE) = Z(NODE-1)-Z(NODE)
20    CONTINUE
      DISNOD(NUMNOD+1) = 0.5*DZ(NUMNOD)

C --- interpolation values for calculation solute transport
      INPOLB(1) = 0.5*DZ(1)/DISNOD(2)
      DO 22 NODE = 2,NUMNOD-1
        INPOLA(NODE) = 0.5*DZ(NODE)/DISNOD(NODE)
        INPOLB(NODE) = 0.5*DZ(NODE)/DISNOD(NODE+1)
22    CONTINUE
      INPOLA(NUMNOD) = 0.5*DZ(NUMNOD)/DISNOD(NUMNOD)

c --- immobile soil fractions
      IF (SWMOBI.EQ.1) THEN
        DO 24 I = 1,NUMLAY
24      SLOPFM(I) = (FM2(I)-FM1(I))/(PF2(I)-PF1(I))
      ELSE
        DO 26 I = 1,NUMNOD
26      FMOBIL(I) = 1.0
        KMOBIL    = 0.0
      ENDIF
      DO 28 I = 1,NUMNOD
28    QIMMOB(I) = 0.0

C --- per node: layer, saturated watercontent, dry bulk density
C --- volume fractions sand, clay and organic matter, hysteresis data
      LAY = 1
      DO 40 NODE = 1,NUMNOD
        IF (NODE.GT.BOTCOM(LAY)) LAY = LAY+1
        LAYER(NODE) = LAY
        IF (FLGENU(LAY)) THEN
          THETAS(NODE) = COFGEN(2,LAY)
          THETAR(NODE) = COFGEN(1,LAY)
          IF (SWHYST.EQ.1) THEN
C ---       wetting curve  
            INDEKS(NODE)   = 1
            ALFAMG(NODE)  = COFGEN(8,LAY)
          ELSEIF (SWHYST.EQ.0.OR.SWHYST.EQ.2) THEN
C ---       drying branch or simulation without hysteresis
            INDEKS(NODE)   = -1
            ALFAMG(NODE)  = COFGEN(4,LAY)
          ENDIF
        ELSE
          THETAS(NODE) = THETSL(LAY)
        ENDIF
          DUMMY = ORGMAT(LAY)/(1.0 - ORGMAT(LAY))
          GMINERAL = (1.0 - real(THETAS(NODE))) / (0.370 + 0.714*DUMMY)
          BDENS(LAY) = (1.0 + DUMMY) * GMINERAL
          FQUARTZ(NODE) = (PSAND(LAY) + PSILT(LAY))*GMINERAL/2.7
          FCLAY(NODE) = PCLAY(LAY)*GMINERAL/2.7
          FORG(NODE) = DUMMY*GMINERAL/1.4
40    CONTINUE

C --- Initial conditions
      POND = 0.0 
      IF (SWINCO.EQ.0) THEN
C ---   compute initial pressure heads from moisture content
        DO 60 NODE = 1,NUMNOD
          THETA(NODE)  = THETAI(NODE)
          H(NODE) = PRHNODE (NODE,THETA(NODE),LAYER,DISNOD,H,
     &    FLGENU,THETAR,THETAS,COFGEN,ALFAMG,HTABLE)
60      CONTINUE
C ---   change h for last node
        IF (SWBOTB.EQ.5) THEN
          H(NUMNOD)     = AFGEN (HGITAB,50,T+1.0) 
          THETA(NUMNOD) = THENODE (NUMNOD,H(NUMNOD),LAYER,
     &    FLGENU,COFGEN,HTABLE,THETLO,ALFAMG,THETAR,THETAS)
        ENDIF
      ELSEIF (SWINCO.EQ.1) THEN
C ---   pressure head profile is given 
        DO 70 NODE = 1,NUMNOD
70      H(NODE) = HI(NODE)
C ---   in case of preferential flow, adjust MVG parameters
        if (SWMOBI.EQ.1) then
          do 170 i = 1,numnod
            lay = layer(i)
            if (h(i).gt.-1.0d0) then
              fmobil(i) = fm1(lay)+(0.0-pf1(lay))*slopfm(lay)
            else
              fmobil(i) = fm1(lay)+(log10(abs(real(h(i))))-pf1(lay))*
     &                    slopfm(lay)
            endif
            fmobil(i) = min (1.0,fmobil(i))
            fmobil(i) = max (0.3,fmobil(i))
            thetar(i) = cofgen(1,lay)*fmobil(i)
            thetas(i) = cofgen(2,lay)*fmobil(i)
170       continue
        endif
        do 180 node = 1,numnod
          THETA(NODE) = THENODE (NODE,H(NODE),LAYER,FLGENU,
     &                  COFGEN,HTABLE,THETLO,ALFAMG,THETAR,THETAS)
180     continue
      ELSEIF (SWINCO.EQ.2) THEN
C ---   pressure head profile is calculated 
        IF (SWBOTB.EQ.1) THEN  
          GWL = AFGEN (GWLTAB,732,T+1.0)
        ELSE
          GWL = GWLI
        ENDIF
        IF (GWL.GT.0.0) POND = GWL
        DO 80 I = 1,NUMNOD
          H(I) = GWL - Z(I)

C ---     in case of preferential flow, adjust MVG parameters
          if (SWMOBI.EQ.1) then
            lay = layer(i)
            if (h(i).gt.-1.0d0) then
              fmobil(i) = fm1(lay)+(0.0-pf1(lay))*slopfm(lay)
            else
              fmobil(i) = fm1(lay)+(log10(abs(real(h(i))))-pf1(lay))*
     &                    slopfm(lay)
            endif
            fmobil(i) = min (1.0,fmobil(i))
            fmobil(i) = max (0.3,fmobil(i))
            thetar(i) = cofgen(1,lay)*fmobil(i)
            thetas(i) = cofgen(2,lay)*fmobil(i)
          endif
          THETA(I) = THENODE (I,H(I),LAYER,FLGENU,
     &               COFGEN,HTABLE,THETLO,ALFAMG,THETAR,THETAS)
80      CONTINUE 
      ENDIF

C --- water volume in totally saturated profile
      VOLSAT = 0.0
      DO 82 NODE = 1,NUMNOD
82    VOLSAT = VOLSAT + DZ(NODE)*THETSL(LAYER(NODE))

C --- save initial moisture contents and pressure heads
      DO 90 NODE = 1,NUMNOD
        THETM1(NODE) = THETA(NODE)
        HM1(NODE)    = H(NODE)
90    CONTINUE

C --- hydr. conductivities, differential moisture capacities
C --- and geometrical mean hydr. conductivities for each node
      DIMOCA(1) = DMCNODE(1,H(1),LAYER,FLGENU,COFGEN,THETLO,THETHI,
     &            DMCH,DMCC,THETAS,THETAR,ALFAMG,SWMOBI,FM1,
     &            PF1,SLOPFM,HTABLE,THETA)
      K(1) = HCONODE (1,THETA(1),LAYER,FLGENU,COFGEN,THETAR,THETAS,
     &       THETLO,THETHI,KTABLE,KSE99,KSAT,SWMOBI,FMOBIL)
      DO 50 NODE = 2,NUMNOD
        DIMOCA(NODE) = DMCNODE (NODE,H(NODE),LAYER,FLGENU,COFGEN,
     &                 THETLO,THETHI,DMCH,DMCC,THETAS,THETAR,
     &                 ALFAMG,SWMOBI,FM1,PF1,SLOPFM,HTABLE,THETA)
        K(NODE) = HCONODE (NODE,THETA(NODE),LAYER,FLGENU,COFGEN,
     &            THETAR,THETAS,THETLO,THETHI,KTABLE,KSE99,KSAT,
     &            SWMOBI,FMOBIL)
        KMEAN(NODE) = 0.5*(K(NODE)+K(NODE-1))
50    CONTINUE
      KMEAN(NUMNOD+1) = K(NUMNOD)

C --- initial solute profiles
      IF (SWSOLU.EQ.1) THEN
        SAMINI = 0.0
        DO 4 I = 1,NUMNOD
          LAY = LAYER(I)
          IF (FMOBIL(I).GT.0.995) THEN
            CML(I) = CMLI(I)
            CIL(I) = 0.0   
            CL(I)  = CML(I)
            CMSY(I) = real(THETA(I)*CML(I)+BDENS(LAY)*KF*CREF*(CML(I)
     &                /CREF)**FREXP)
            CISY(I) = 0.0
          ELSE
            CML(I) = CMLI(I)
            CIL(I) = CML(I)
            CL(I)  = CML(I)
            CMSY(I) = real(THETA(I)*CML(I)+BDENS(LAY)*KF*CREF*((CML(I)
     &                /CREF)**FREXP) * FMOBIL(I))
            CISY(I) = real((THETIM(LAY)*CIL(I)+BDENS(LAY)*KF*CREF
     &                *(CIL(I)/CREF)**FREXP)* (1.0-FMOBIL(I)))
          ENDIF
          SAMINI = SAMINI + (CMSY(I)+CISY(I)) * DZ(I)
4       CONTINUE
      ENDIF

C --- flow through soil cracks
      IF (SWCRACK.EQ.1) THEN
        shrinc = 0.7
        beta2  = -1.0/moisr1*log((moisrd+moisr1-shrinc*moisr1)/shrina)      
        beta1  = beta2+1.0

445     if (abs(beta2-beta1).gt.0.001) then
          beta1 = beta2
          func  = (shrina+shrina*moisr1*beta1)*exp(-beta1*moisr1)-moisrd
          deri  = (2.0*shrina*moisr1-shrina*moisr1*moisr1*beta1)*
     &            exp(-beta1*moisr1)
          beta2 = beta1-func/deri
          goto 445
        endif
        shrinb = beta2

        shrinc = 1.0+shrina*shrinb*exp(-shrinb*moisr1) 

C ---   number node for evaluating shrinkage characteristic
        i = 1
460     if (z(i).gt.zncrack) then
          i = i+1
          goto 460
        endif
        nncrack = i

      ELSE
C ---   set variables to zero
        acrack  = 0.0
        qcrack  = 0.0
        rapdra  = 0.0
        wtoplat = 0.0
        do 443 i = 1,numnod
443     adsflu(i) = 0.0
      ENDIF         

C --- initial total volume
      ARFLUX = 0.0
      NIRD   = 0.0
      CRACKW = 0.0
      CALL WATCON (VOLM1,VOLACT,NUMNOD,THETA,DZ,FMOBIL,LAYER,
     & THETIM,SWCRACK,CKWM1,CRACKW,WTOPLAT,QCRACK,ARFLUX,NIRD,ACRACK,
     & RAPDRA,DT) 
      VOLINI = VOLACT+POND

C --- initialize registration of last four groundwaterlevels, for noting
C --- oscillation
       do 454 i2=1,4
         gwlbak(i2)= 0.0
 454   continue

      RETURN
      END 


C ----------------------------------------------------------------------
      SUBROUTINE INTEGRAL (PTRA,DT,PEVA,REVA,QBOT,POND,QTOP,NRAI,NIRD,
     & PONDMX,NUMNOD,QROT,QDRTOT,QDRAIN,DQROT,DPTRA,IQROT,INQROT,IQDRA,
     & NRLEVS,INQDRA,QDRA,GRAI,GIRD,IINTC,IPTRA,IPEVA,IEVAP,IRUNO,
     & IPREC,IQBOT,CQROT,CQDRA,CQDRAIN,CPTRA,CPEVA,CEVAP,CRUNO,
     & CGRAI,CNRAI,CGIRD,CNIRD,CQBOT,CQTOP,PONDM1,WTOPLAT,RAPDRA,
     & IQDRAR,IQCRACK,QCRACK,CQDRAR,CQCRACK,ACRACK,ARFLUX,T,
     & WLS,RSRO,RUNOTS,QROSUM,SWCRACK,SWDRA,IGRAI,IGIRD,QCOMP,
     & QDARCY,CQDARCY)
C ----------------------------------------------------------------------
C     Date               : 29/08/96                                           
C     Purpose            : calculation of intermediate values and     
C                          cumulative values          
C     Subroutines called : -                                           
C     Functions called   : -                     
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

C --- global
      INTEGER NUMNOD,NRLEVS,SWCRACK,SWDRA

      REAL    PTRA,DT,PEVA,REVA,POND,QTOP,NRAI,NIRD,PONDMX,QROT(MACP)
      REAL    QDRTOT,QDRAIN(5),DQROT,DPTRA,IQROT,INQROT(MACP),IQDRA
      REAL    INQDRA(5,MACP),IGRAI,IGIRD
      REAL    QDRA(5,MACP),IINTC,IPTRA,IPEVA,IEVAP,IRUNO,IPREC
      REAL    IQBOT,GRAI,GIRD,CQROT,CQDRA,CQDRAIN(5),CPTRA,CPEVA,CEVAP
      REAL    CRUNO,QROSUM,QCOMP,T,QDARCY,CQDARCY
      REAL    CGRAI,CNRAI,CGIRD,CNIRD,CQBOT,CQTOP,QBOT,ACRACK
      REAL    PONDM1,WTOPLAT,RAPDRA,IQDRAR,IQCRACK,QCRACK,CQDRAR,CQCRACK
      REAL    WLS,RSRO,RUNOTS,ARFLUX         
      
C ----------------------------------------------------------------------
C --- local
      INTEGER node,level

      REAL    qrotts,qdrats,ptrats,pevats,revats,masdif
      REAL    qbotts,difpond
C ----------------------------------------------------------------------
              
C --- potential transpiration of this timestep
      ptrats = ptra * dt

C --- potential soil evaporation of this timestep
      pevats = peva * dt

C --- reduced soil evaporation of this timestep
      revats = reva * dt

C --- flux lower boundary of this timestep
      qbotts = qbot*dt

C --- runoff of this timestep, take physical limits into account
      pondm1 = pond
      difpond = (qtop + (ARFLUX + NIRD) * (1.0 - acrack)) * dt 
     &        - revats - wtoplat
      difpond = min(difpond, 100.0*dt)
      pond = pond + difpond
      if (pond.lt.1.0e-6) pond=0.0

C --- height ponding layer determines amount runoff or runon
      runots = 0.0
      if (SWDRA.LT.2) then
        if (pond.gt.pondmx .and. .not. (SWCRACK.EQ.1)) then
            runots = pond - pondmx
        endif
      else
         if (pond.gt.pondmx .or. wls.gt.pondmx) then
           if (pond.gt.pondmx) then
             if (wls.gt.pondmx) then
                runots = pond - wls
             else
                runots = pond - pondmx
             endif
           else
             runots = pondmx - wls
           endif
C ---      reduce runots so that the rate corresponds to a drainage flux
C ---      with drainage resistance of RSRO
           runots = runots*dt/rsro
         endif
      endif
      pond = pond - runots


C --- total root extraction of this timestep
      qrotts = QROSUM * dt

C --- total drainage flux of this timestep
      qdrats = qdrtot * dt

C --- add time step fluxes to daily totals
      dqrot = dqrot + qrotts
      dptra = dptra + ptrats

C --- add time step fluxes to intermediate totals
      iqrot  = iqrot + qrotts
      do 300 node = 1,numnod
300   inqrot(node) = inqrot(node) + qrot(node) * dt
      iqdra = iqdra + qdrats + rapdra*dt
      do 410 node = 1,numnod
        do 400 level = 1,nrlevs
          inqdra(level,node) = inqdra(level,node)+qdra(level,node)*dt
400     continue
410   continue

      iintc   = iintc + ((GRAI-NRAI)+(GIRD-NIRD))*dt
      iptra   = iptra + ptrats
      ipeva   = ipeva + pevats
      ievap   = ievap + revats
      iruno   = iruno + runots
      iprec   = iprec + (GRAI+GIRD)*dt
      igrai   = igrai + grai*dt
      igird   = igird + gird*dt
      iqbot   = iqbot + qbotts
      iqdrar  = iqdrar + rapdra*dt 
      iqcrack = iqcrack +qcrack*dt

C --- add time step fluxes to total cumulative values
      cqrot   = cqrot + qrotts
      cqdra   = cqdra + qdrats
      cptra   = cptra + ptrats
      cpeva   = cpeva + pevats
      cevap   = cevap + revats
      cruno   = cruno + runots
      CGRAI   = CGRAI + GRAI*DT
      CNRAI   = CNRAI + NRAI*DT
      CGIRD   = CGIRD + GIRD*DT
      CNIRD   = CNIRD + NIRD*DT
      cqbot   = cqbot + qbotts
      cqdrar  = cqdrar + rapdra*dt
      cqcrack = cqcrack + qcrack*dt 
      cqtop   = cqtop + qtop*dt
      cqdarcy = cqdarcy + qdarcy*dt
      do 150 level = 1,5
        cqdrain(level) = cqdrain(level) + qdrain(level)*dt
150   continue

c --- compensate water balance error of this time step during remaining day part
      MASDIF = (QTOP - QCOMP + (ARFLUX + NIRD)*(1.0 - ACRACK))*DT
     &       - WTOPLAT - REVATS - RUNOTS - POND + PONDM1
      QCOMP = QCOMP - MASDIF / (AINT(T+1.0) - T)

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE NOCROP (DRZ,LAI,CF,FLCROP)
C ----------------------------------------------------------------------
      REAL    DRZ,LAI,CF
      LOGICAL FLCROP
C ----------------------------------------------------------------------
      DRZ    = 0.0
      LAI    = 0.0
      CF     = 0.0
      FLCROP = .FALSE.

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE OUTAFO (AFO,AFONAM,HAFOD,STASTR,ENVSTR,
     &  NUMNOD,OUTPER,PERIOD,TCUM,POND,GWL,THETA,H,INQ,
     &  INQROT,NRLEVS,INQDRA,IPREC,IINTC,IEVAP,IPEVA,IPTRA,IRUNO,
     &  NUMLAY,BOTCOM,DZ,THETAS,BRUNY,ERUNY,BRUND,ERUND,
     &  LAYER,FLGENU,ALFAMG,THETAR,COFGEN,HTABLE,THETLO)
C ----------------------------------------------------------------------
C     Date               : 15/10/1997           
C     Purpose            : ANIMO output: formatted hydrological data
C     Subroutines called : -              
C     Functions called   : THENODE 
C     File usage         : AFONAM
C ---------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

      INTEGER AFO,OUTPER,PERIOD,LAY,LEVEL,NODE
      INTEGER NUMLAY,NUMNOD,NRLEVS,BOTCOM(MAHO),LAYER(MACP)
      INTEGER BRUNY,ERUNY,BRUND,ERUND,THETLO(MAHO)

      REAL    GWL,INQDRA(5,MACP),IPREC,IINTC,IEVAP,POND,TCUM
      REAL    IPEVA,IPTRA,IRUNO,INQ(MACP+1),INQROT(MACP),DZ(MACP)
      REAL*8  THETA(MACP),H(MACP),THETAS(MACP),THENODE
      REAL*8  ALFAMG(MACP),THETAR(MACP),COFGEN(8,MAHO),HTABLE(MAHO,99)
      REAL*8  DVAL(MAHO)

      CHARACTER AFONAM*8,STASTR*7,ENVSTR*50,FILNAM*12

      character*80 rmldsp
      
      LOGICAL HAFOD,FLGENU(MAHO)
C ----------------------------------------------------------------------
      IF (.NOT.HAFOD) THEN
C ---   open output file
        CALL SHIFTR (AFONAM)
        FILNAM = AFONAM//'.AFO'
        CALL SHIFTL (FILNAM)
        CALL SHIFTR (ENVSTR)
        CALL FINDUNIT (72,AFO)
        OPEN (AFO,FILE=rmldsp(ENVSTR//FILNAM),STATUS=STASTR,
     &  FORM ='FORMATTED',ACCESS='SEQUENTIAL')

        write (AFO,4000) BRUNY,ERUNY, 
     &  float(BRUND-1),float(ERUND),float(PERIOD)
        write (AFO,4010) numnod,numlay,nrlevs
        write (AFO,4010) (botcom(lay),lay=1,numlay)
        write (AFO,4020) (real(thetaS(botcom(lay))), lay=1,numlay)

        DO 4 lay = 1,numlay
          DVAL(lay) = thenode(botcom(lay),-100.d0,LAYER,
     &                FLGENU,COFGEN,HTABLE,THETLO,ALFAMG,THETAR,THETAS)
4       CONTINUE
        write (AFO,4020) (REAL(DVAL(lay)),lay=1,numlay) 

        DO 6 lay = 1,numlay
          DVAL(lay) = thenode(botcom(lay),-15849.0d0,LAYER,
     &                FLGENU,COFGEN,HTABLE,THETLO,ALFAMG,THETAR,THETAS)
6       CONTINUE
        write (AFO,4020) (REAL(DVAL(lay)),lay=1,numlay) 

        write (AFO,4020) (0.01*dz(node),node=1,numnod)
        write (AFO,4020) (real(theta(node)),node=1,numnod)
        write (AFO,4020) -0.01*gwl,0.01*pond
4000    format (2(1X,I8),3(1X,F8.0),1X,i8) 
4010    format (5(1X,i8))
4020    format (8(1X,F8.4))

        HAFOD = .TRUE.
        RETURN
      ENDIF

C --- formatted output of data - dynamic part
      if (HAFOD) then
        write (AFO,30) TCUM,
     &  0.01*iprec/OUTPER,
     $  0.01*iintc/OUTPER,
     $  0.01*ievap/OUTPER,
     &  0.0,
     $  0.01*ipeva/OUTPER,
     $  0.01*iptra/OUTPER,
     &  0.01*iruno/OUTPER,
     $  -0.01*gwl,0.01*pond
        write (AFO,40) (h(node)                 ,node=1,numnod)
        write (AFO,50) (theta(node)             ,node=1,numnod)
        write (AFO,50) (0.01*inqrot(node)/OUTPER,node=1,numnod)
        write (AFO,50) (-0.01*inq(node)/OUTPER  ,node=1,numnod+1)
        if (nrlevs.gt.0) then
          do 300 level=1,nrlevs
            write (AFO,50) (0.01*inqdra(level,node)/OUTPER,
     $        node=1,numnod)
 300      continue
        end if
      end if

30    format (1x,f6.0,7(1x,f7.6),2(1x,f7.4))
40    format (8(1x,e8.3e1))
50    format (10(1x,f7.5))

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE OUTAIR (AIR,AIRNAM,HAIRD,STASTR,ENVSTR,
     &  YEAR,DAYNR,TCUM,GIRD,CIRR)
C ----------------------------------------------------------------------
C     Date               : 24/10/1997           
C     Purpose            : ANIMO/Pestla output: irrigations           
C     Subroutines called : -              
C     Functions called   : -       
C     File usage         : AIRNAM
C ---------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER AIR,YEAR,DAYNR
c     INTEGER(2) iday,imon,iyr

      REAL    TCUM,GIRD,CIRR

      CHARACTER AIRNAM*8,STASTR*7,IRSTRING*12,ENVSTR*50,FILNAM*12

      character*80 rmldsp
      
      LOGICAL HAIRD
C ----------------------------------------------------------------------
      IF (.NOT.HAIRD) THEN
C ---   open output file
        CALL SHIFTR (AIRNAM)
        FILNAM = AIRNAM//'.AIR'
        CALL SHIFTL (FILNAM)
        CALL SHIFTR (ENVSTR)
        CALL Findunit (74,AIR)
        OPEN (AIR,FILE=rmldsp(ENVSTR//FILNAM),STATUS=STASTR,
     &  FORM ='FORMATTED',ACCESS='SEQUENTIAL')
C ---   write header
        WRITE (AIR,'(2A)')'* Filename     : ',ENVSTR//FILNAM  
        WRITE (AIR,'(A)') '* FileContent  : irrigations'
        WRITE (AIR,'(A)') '* ProducerId   :     '
c       CALL GETDAT (iyr,imon,iday)
c       WRITE (AIR,'(A,2I3,I5)') '* ProducerDate :',iday,imon,iyr
        WRITE (AIR,'(A)') '* ProducerDate :'
        HAIRD = .TRUE.
      ENDIF

      IRSTRING = '''IRRIGATION'''
      WRITE (AIR,'(A,I5,1X,I3,1X,I5,2F10.3)') IRSTRING,YEAR,
     & DAYNR,INT(TCUM),GIRD/100,CIRR

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE OUTATE (ATE,ATENAM,HATED,STASTR,ENVSTR,NUMNOD,
     &  YEAR,DAYNR,TCUM,TEMPI,TEMP,TAV)
C ----------------------------------------------------------------------
C     Date               : 09/01/1997           
C     Purpose            : ANIMO output: soil temperatures           
C     Subroutines called : -              
C     Functions called   : -       
C     File usage         : ATENAM
C ---------------------------------------------------------------------
      IMPLICIT NONE 
      INCLUDE 'PARAM.FI' 

      INTEGER NUMNOD,YEAR,DAYNR,ATE,I

      REAL    TCUM,TAV,TEMPI(MACP)
      REAL*8  TEMP(MACP)

      CHARACTER ATENAM*8,STASTR*7,FILNAM*12
      CHARACTER ENVSTR*50

      character*80 rmldsp

      LOGICAL HATED

      SAVE

C ----------------------------------------------------------------------
      IF (.NOT.HATED) THEN
C ---   open output file
        CALL SHIFTR (ATENAM)
        FILNAM = ATENAM//'.ATE'
        CALL SHIFTL (FILNAM)
        CALL SHIFTR (ENVSTR)
        CALL Findunit (76,ATE)
        OPEN (ATE,FILE=rmldsp(ENVSTR//FILNAM),STATUS=STASTR,
     &  FORM ='FORMATTED',ACCESS='SEQUENTIAL',RECL=22+numnod*6)
C ---   write header
        WRITE (ATE,'(2A)')'* Filename     : ',ENVSTR//FILNAM  
        WRITE (ATE,'(A)') '* FileContent  : soil temperature profiles'
        WRITE (ATE,'(A)') '* ProducerId   :     '
        WRITE (ATE,'(A)') '* ProducerDate :'
C ---   write initial temperature profile
        WRITE (ATE,'(I4,1X,I3,1X,I5,100F6.1)') YEAR,DAYNR,INT(TCUM),
     &         TEMPI(1),(TEMPI(I),I=1,NUMNOD)

        HATED = .TRUE.
      ENDIF

      WRITE (ATE,'(I4,1X,I3,1X,I5,100F6.1)') YEAR,DAYNR,INT(TCUM),TAV,
     &      (TEMP(I),I=1,NUMNOD)

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE OUTAUN (AUN,AUNNAM,HAUND,STASTR,ENVSTR,
     &  NUMNOD,OUTPER,PERIOD,TCUM,POND,GWL,THETA,H,INQ,
     &  INQROT,NRLEVS,INQDRA,IPREC,IINTC,IEVAP,IPEVA,IPTRA,IRUNO,
     &  NUMLAY,BOTCOM,DZ,THETAS,BRUNY,ERUNY,BRUND,ERUND,
     &  LAYER,FLGENU,ALFAMG,THETAR,COFGEN,HTABLE,THETLO)
C ----------------------------------------------------------------------
C     Date               : 15/10/1997           
C     Purpose            : ANIMO output: unformatted hydrological data
C     Subroutines called : SHIFTR,SHIFTL
C     Functions called   : THENODE 
C     File usage         : AUNNAM
C ---------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

      INTEGER AUN,OUTPER,PERIOD,LAY,LEVEL,NODE
      INTEGER NUMLAY,NUMNOD,NRLEVS,BOTCOM(MAHO),LAYER(MACP)
      INTEGER BRUNY,ERUNY,BRUND,ERUND,THETLO(MAHO)

      REAL    GWL,INQDRA(5,MACP),IPREC,IINTC,IEVAP,POND,TCUM
      REAL    IPEVA,IPTRA,IRUNO,INQ(MACP+1),INQROT(MACP),DZ(MACP)
      REAL*8  THETA(MACP),H(MACP),THETAS(MACP),THENODE
      REAL*8  ALFAMG(MACP),THETAR(MACP),COFGEN(8,MAHO),HTABLE(MAHO,99)
      REAL*8  DVAL(MAHO) 

      CHARACTER AUNNAM*8,STASTR*7,ENVSTR*50,FILNAM*12

      character*80 rmldsp
      
      LOGICAL HAUND,FLGENU(MAHO)
C ----------------------------------------------------------------------
      IF (.NOT.HAUND) THEN 
C --- open output file
        CALL SHIFTR (AUNNAM)
        FILNAM = AUNNAM//'.AUN'
        CALL SHIFTL (FILNAM)
        CALL SHIFTR (ENVSTR)
        CALL FINDUNIT (72,AUN)
        OPEN (AUN,FILE=rmldsp(ENVSTR//FILNAM),STATUS=STASTR,
     &  FORM ='UNFORMATTED',ACCESS='SEQUENTIAL')

        write (AUN) BRUNY,ERUNY, 
     &  float(BRUND-1),float(ERUND),float(PERIOD)
        write (AUN) numnod,numlay,nrlevs
        write (AUN) (botcom(lay),lay=1,numlay)
        write (AUN) (real(thetaS(botcom(lay))), lay=1,numlay)

        DO 4 lay = 1,numlay
          DVAL(lay) = thenode(botcom(lay),-100.d0,LAYER,
     &                FLGENU,COFGEN,HTABLE,THETLO,ALFAMG,THETAR,THETAS)
4       CONTINUE
        write (AUN) (REAL(DVAL(lay)),lay=1,numlay) 

        DO 6 lay = 1,numlay
          DVAL(lay) = thenode(botcom(lay),-15849.0d0,LAYER,
     &                FLGENU,COFGEN,HTABLE,THETLO,ALFAMG,THETAR,THETAS)
6       CONTINUE

        write (AUN) (REAL(DVAL(lay)),lay=1,numlay) 

        write (AUN) (0.01*dz(node),node=1,numnod)
        write (AUN) (real(theta(node)),node=1,numnod)
        write (AUN) -0.01*gwl,0.01*pond

        HAUND = .TRUE.
        RETURN
      ENDIF

C --- unformatted output of data - dynamic part
      if (HAUND) then
        write (AUN) TCUM,
     &  0.01*iprec/OUTPER,
     $  0.01*iintc/OUTPER,
     &  0.01*ievap/OUTPER,
     &  0.0,    
     $  0.01*ipeva/OUTPER,
     &  0.01*iptra/OUTPER,
     &  0.01*iruno/OUTPER,
     $  -0.01*gwl,0.01*pond
        write (AUN) (real(h(node))           ,node=1,numnod)
        write (AUN) (real(theta(node))       ,node=1,numnod)
        write (AUN) (0.01*inqrot(node)/OUTPER,node=1,numnod)
        write (AUN) (-0.01*inq(node)/OUTPER  ,node=1,numnod+1)
        if (nrlevs.gt.0) then
          do 310 level=1,nrlevs
            write (AUN) (0.01*inqdra(level,node)/OUTPER,
     $        node=1,numnod)
 310      continue
        end if
      end if

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE OUTBAL (OUTNAM,ENVSTR,DAYNR,YEAR,BRUND,BRUNY,BAYRD,
     &  BAYRY,CGRAI,CNRAI,CGIRD,CNIRD,CRUNO,CQROT,CEVAP,CQBOT,
     &  CQDRAIN,CQDRA,CQDRAR,VOLACT,VOLINI,Z,DZ,SWDRA,NUMNOD,
     &  NRLEVS,SAMINI,SAMPRO,SAMCRA,SQPREC,SQIRRIG,SQBOT,DECTOT,ROTTOT,
     &  SQRAP,SQDRA,SWSOLU,POND)
C ----------------------------------------------------------------------
C     Date               : 22/12/1998
C     Purpose            : write overview balances to OUTNAM.BAL file
C     Subroutines called : SHIFTR,SHIFTL,NRTODA
C     Functions called   : -
C     File usage         : OUTNAM.BAL
C ---------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE  'PARAM.FI'

      INTEGER   DAYNR,YEAR,BRUND,BRUNY,BAYRD,BAYRY,BAL,SWDRA
      INTEGER   DSTART,MSTART,YSTART,DEND,MEND,YEND,NUMNOD,NRLEVS,I
      INTEGER   SWSOLU

      REAL      CEVAP,CGIRD,CGRAI,CNIRD,CNRAI,CQBOT,INTERC
      REAL      CQROT,CRUNO,CQDRAR,CQDRA,CQDRAIN(5),DZ(MACP),Z(MACP)
      REAL      SAMINI,SAMPRO,SAMCRA,SQPREC,SQIRRIG,SQBOT,DECTOT,ROTTOT
      REAL      SQRAP,SQDRA,POND
      REAL*8    VOLACT,VOLINI

      CHARACTER OUTNAM*8,FILNAM*12,ENVSTR*50

      character*80 rmldsp

C --- compose filename
        CALL SHIFTR (OUTNAM)
        FILNAM = OUTNAM//'.BAL'
        CALL SHIFTL (FILNAM)
        CALL SHIFTR (ENVSTR)

C --- open output file
        CALL FINDUNIT (10,BAL)
        OPEN (BAL,FILE = rmldsp(ENVSTR//FILNAM), STATUS = 'UNKNOWN')

C --- start date of sub-run
      IF (BAYRY.GT.BRUNY.OR.
     &  ((BAYRY.EQ.BRUNY).AND.(BAYRD.GT.BRUND))) THEN
        CALL NRTODA (BAYRY,BAYRD,MSTART,DSTART)
        YSTART = BAYRY
      ELSE
        CALL NRTODA (BRUNY,BRUND,MSTART,DSTART)
        YSTART = BRUNY
      ENDIF

C --- end date of sub-run
      IF (DAYNR.GT.1) THEN
        CALL NRTODA (YEAR,(DAYNR-1),MEND,DEND)
          YEND = YEAR
      ELSE
          MEND = 12
          DEND = 31
          YEND = YEAR - 1
      ENDIF

C --- write output record

      WRITE (BAL,20) DSTART,MSTART,YSTART,DEND,MEND,YEND
      WRITE (BAL,22) (-Z(NUMNOD) + 0.5*DZ(NUMNOD))

      IF (SWSOLU .EQ. 1) THEN
          WRITE (BAL,24) (VOLACT+POND),(SAMPRO+SAMCRA),VOLINI,SAMINI,
     &    (VOLACT+POND-VOLINI),(SAMPRO+SAMCRA-SAMINI)
      ELSE
          WRITE (BAL,25) (VOLACT+POND),VOLINI,(VOLACT+POND-VOLINI)
      ENDIF

      INTERC = CGRAI+CGIRD-CNRAI-CNIRD
      WRITE (BAL,26) CGRAI,INTERC,CGIRD,CRUNO,CQBOT,CQROT,CEVAP,CQDRAR

      IF (SWDRA .NE. 0) THEN
        DO 100 I = 1,NRLEVS
          WRITE (BAL,28) I,CQDRAIN(I)
 100    CONTINUE
      ENDIF
      WRITE (BAL,30) (CGRAI+CGIRD+CQBOT),(INTERC+CRUNO+CQROT+CEVAP+
     &   CQDRAR+CQDRA)

      IF (SWSOLU .EQ. 1) THEN
        WRITE (BAL,34) SQPREC,DECTOT,SQIRRIG,ROTTOT,SQBOT,SQRAP,SQDRA
        WRITE (BAL,36) (SQPREC+SQIRRIG+SQBOT),
     &    (DECTOT+ROTTOT+SQRAP+SQDRA)
      ENDIF

      CLOSE (BAL)

 20   FORMAT('Period',t20,':',t22,i2,'/',i2.2,'/',i4,
     &   ' until  ',i2,'/',i2.2,'/',i4)
 22   FORMAT('Depth soil profile',t20,':',f8.2,' cm')
 24   FORMAT(/,T13,'Water storage',t36,'Solute storage',/,
     &   'Final',t9,':',t15,f8.2,' cm',t31,e12.4,' mg/cm2',/,
     &   'Initial',t9,':',t15,f8.2,' cm',t31,e12.4,' mg/cm2',/,
     &    t13,13('='),t33,17('='),/,
     &   'Change',t15,f8.2,' cm',t31,e12.4,' mg/cm2')
 25   FORMAT(/,T13,'Water storage',/,'Final',t9,':',t15,f8.2,' cm',/,
     &   'Initial',t9,':',t15,f8.2,' cm',/,
     &    t13,13('='),/,'Change',t15,f8.2,' cm')
 26   FORMAT(//,'Water balance components (cm)',//,
     &   'In',t30,'Out',/,25('='),t30,28('='),/,
     &   'Rain',t16,':',f9.2,t30,'Interception',t48,':',f9.2,/,
     &   'Irrigation',t16,':',f9.2,t30,'Runoff',t48,':',f9.2,/,
     &   'Bottom flux',t16,':',f9.2,t30,'Transpiration',t48,':',f9.2,
     &   /,t30,'Soil evaporation',t48,':',f9.2,/,
     &   t30,'Crack flux',t48,':',f9.2)
 28   FORMAT(t30,'Drainage level',i2,t48,':',f9.2)
 30   FORMAT(25('='),t30,28('='),/,
     &   'Sum',t16,':',f9.2,t30,'Sum',t48,':',f9.2)
 34   FORMAT(//,'Solute balance components (mg/cm2)',//,
     &   'In',t30,'Out',/,25('='),t30,28('='),/,
     &   'Rain',t13,':',e12.4,t30,'Decomposition',t45,':',e12.4,/,
     &   'Irrigation',t13,':',e12.4,t30,'Root uptake',t45,':',e12.4,/,
     &   'Bottom flux',t13,':',e12.4,t30,'Cracks',t45,':',e12.4,/,
     &   t30,'Drainage',t45,':',e12.4)
 36   FORMAT(25('='),t30,28('='),/,
     &   'Sum',t13,':',e12.4,t30,'Sum',t45,':',e12.4)

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE OUTINC (OUTNAM,INC,HINCD,ENVSTR,STASTR,DAYNR,YEAR,
     &  IGRAI,IGIRD,IINTC,IRUNO,IPTRA,IQROT,IPEVA,IEVAP,IQDRA,
     &  IQDRAR,IQBOT,T)
C ----------------------------------------------------------------------
C     Date               : 18/08/98
C     Purpose            : write water balance increments to OUTNAM.WBA file
C     Subroutines called : SHIFTR,SHIFTL,NRTODA
C     Functions called   : -
C     File usage         : OUTNAM.INC
C ---------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER   INC,DAYNR,YEAR,D,M

      REAL      IGRAI,IGIRD,IINTC,IRUNO,IPTRA,IQROT,IPEVA,IEVAP,IQDRA
      REAL      IQDRAR,IQBOT,T

      CHARACTER OUTNAM*8,FILNAM*12,ENVSTR*50,STASTR*7

      character*80 rmldsp
      
      LOGICAL   HINCD
C ----------------------------------------------------------------------
      IF (.NOT.HINCD) THEN

C --- compose filename
        CALL SHIFTR (OUTNAM)
        FILNAM = OUTNAM//'.INC'
        CALL SHIFTL (FILNAM)
        CALL SHIFTR (ENVSTR)

C --- open output file
        CALL FINDUNIT (10,INC)
        OPEN (INC,FILE =rmldsp(ENVSTR//FILNAM), STATUS = STASTR, 
     &  ACCESS = 'SEQUENTIAL')

C --- write header
        WRITE (INC,10)
 10     FORMAT (t18,'Water balance increments (cm/period)',//,
     &'*      Date Day    Rain   Irrig  Interc  Runoff   Transpiration',
     &'     Evaporation Drainage QBottom',/,
     &'*dd/mm/yyyy  nr   gross   gross                     pot     act',
     &'     pot     act      net     net',/,
     &'<=========><==><======><======><======><======><======><======>',
     &'<======><======><=======><======>')

        HINCD = .TRUE.
      ENDIF

C --- Write output .INC file

C --- conversion of daynumber to date
      CALL NRTODA (YEAR,DAYNR,M,D)

C --- write output record
      WRITE (INC,20) D,M,YEAR,NINT(T),IGRAI,IGIRD,IINTC,IRUNO,
     &  IPTRA,IQROT,IPEVA,IEVAP,(IQDRAR+IQDRA),IQBOT
20    FORMAT (I3,'/',I2.2,'/',2I4,8F8.3,F9.3,F8.3)

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE OUTDRF (OUTNAM,DRF,HDRFD,ENVSTR,STASTR,DAYNR,YEAR,
     &  NRPRI,NRSRF,CQDRAIN,CQDRD,CRUNO,CQDRAR,T)
C ----------------------------------------------------------------------
C     Date               : 13/11/97
C     Purpose            : write drainage fluxes, surface runoff, rapid
C                          drainage to  OUTNAM.DRF file
C     Subroutines called : 
C     Functions called   : -
C     File usage         : OUTNAM.DRF
C ---------------------------------------------------------------------
C --- Global
      INTEGER   DRF,DAYNR,YEAR,D,M,NRPRI,NRSRF
      REAL      CQDRAIN(5),CQDRD,CRUNO,CQDRAR,T
      CHARACTER OUTNAM*8,FILNAM*12,ENVSTR*50,STASTR*7

      character*80 rmldsp

C --- Local
      INTEGER   LEVEL
      REAL      C1QDRAIN(5),C1QDRD,C1RUNO,C1QDRAR
      LOGICAL   HDRFD

      SAVE
C ----------------------------------------------------------------------
      IF (.NOT.HDRFD) THEN

C --- compose filename
        CALL SHIFTR (OUTNAM)
        FILNAM = OUTNAM//'.DRF'
        CALL SHIFTL (FILNAM)
        CALL SHIFTR (ENVSTR)

C --- open output file
        CALL FINDUNIT (10,DRF)
        OPEN (DRF,FILE =rmldsp(ENVSTR//FILNAM), STATUS = STASTR, 
     &  ACCESS = 'SEQUENTIAL')

C --- write header
        if (nrpri .eq. 1) then
          WRITE (DRF,100) NRSRF
        else
          WRITE (DRF,101) NRSRF
        endif
100     FORMAT (
C
     &'* CUMULATIVE DRAINAGE FLUXES, SURFACE RUNOFF AND RAPID',
     &' DRAINAGE:',/,'*',/,
     &'* Total number of levels for drainage fluxes :',I3,/,'*',/
     &'* First level (primary system) NOT included in sw-reservoir',/,
     &'*',/)
101     FORMAT (
     &'* CUMULATIVE DRAINAGE FLUXES, SURFACE RUNOFF AND RAPID',
     &' DRAINAGE:',/,'*',/,
     &'* Total number of levels for drainage fluxes :',I3,/,'*',/
     &'* First level (primary system) IS included in sw-reservoir',/,
     &'*')
C
        WRITE (DRF,11)
11      FORMAT (
     &'* Meaning of symbols:',/,
     &'* - CQD(*)  : Drainage fluxes all levels',/,
     &'* - CQDRD   : Total of drainage fluxes into surface',
     &            ' water reservoir (SWSRF>=1)',/,
     &'* - CRUNO   : Surface runoff (increment can be <0.0)',/,
     &'* - CQDRAR  : Rapid drainage (increment always >= 0.0)',/,
     &'* - cum     : cumulative value',/,
     &'* - inc     : incremental value',/,'*',/, 
     &'* DATE            CQD(1)  CQD(2)  CQD(3)  CQD(4)  CQD(5)',
     &'   CQDRD   CRUNO  CQDRAR',/,
     &'* dd/mm/yyyy  nr    inc/    inc/    inc/    inc/    inc/',
     &'    inc/    inc/    inc/',/,
     &'*                    cum     cum     cum     cum     cum',
     &'     cum     cum     cum',/,
     &'*                   [cm]    [cm]    [cm]    [cm]    [cm]',
     &'    [cm]    [cm]    [cm]',/,
     &'* <============><======><======><======><======><======>',
     &'<======><======><======>')

        do 30 level=1,5
          c1qdrain(level)=0.0
 30     continue
        c1qdrd   = 0.0
        c1runo   = 0.0
        c1qdrar  = 0.0
        hdrfd    = .true.
      endif

C --- conversion of daynumber to date
      CALL NRTODA (YEAR,DAYNR,M,D)

C --- write output record
      WRITE (DRF,20) D,M,YEAR,NINT(T),((cqdrain(level)-c1qdrain(level)),
     &  level=1,5),(cqdrd-c1qdrd),(cruno-c1runo),(cqdrar-c1qdrar),
     &  D,M,YEAR,NINT(T),(cqdrain(level),level=1,5),cqdrd,cruno,cqdrar

 20   FORMAT ('1',1X,I2,'/',I2.2,'/',2I4,8f8.2,/,
     &        '2',1X,I2,'/',I2.2,'/',2I4,8f8.1)

C --- store cumulative values
      do 50 level=1,5
          c1qdrain(level)=cqdrain(level)
 50   continue
      c1qdrd   = cqdrd
      c1runo   = cruno
      c1qdrar  = cqdrar

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE OUTSBA (OUTNAM,SBA,HSBAD,ENVSTR,STASTR,DAYNR,YEAR,
     &   DECTOT,ROTTOT,SAMPRO,SAMCRA,SQBOT,SQSUR,SQRAP,SAMAQ,
     &   SQDRA,T,SOLBAL,SQPREC,SQIRRIG)
C ----------------------------------------------------------------------
C     Date               : 18/08/98                            
C     Purpose            : output of salt balance
C     Subroutines called : SHIFTR,SHIFTL,NRTODA
C     Functions called   : -
C     File usage         : OUTNAM.SBA
C ---------------------------------------------------------------------
      IMPLICIT NONE

C --- global
      INTEGER   SBA,DAYNR,YEAR
      REAL      SAMPRO,SAMCRA,SQBOT,SQSUR,SQRAP,SAMAQ,SQDRA,T
      REAL      SOLBAL,DECTOT,ROTTOT,SQPREC,SQIRRIG

      CHARACTER OUTNAM*8,ENVSTR*50,STASTR*7

      character*80 rmldsp

      LOGICAL   HSBAD
C ----------------------------------------------------------------------
C --- local
      INTEGER   D,M
      CHARACTER filnam*12
C ----------------------------------------------------------------------
      IF (.NOT.HSBAD) THEN 

C --- open output file
        CALL SHIFTR (OUTNAM)
        FILNAM = OUTNAM//'.SBA'
        CALL SHIFTL (FILNAM)
        CALL SHIFTR (ENVSTR)
        CALL FINDUNIT (10,SBA)

        OPEN (SBA,FILE=rmldsp(ENVSTR//FILNAM),STATUS=STASTR,
     &  ACCESS='SEQUENTIAL')

C --- write headers
        WRITE (SBA,10)
10    FORMAT (
     &'*DATE       DAY      SQTOP      DECTOT      ROTTOT       SAMPRO',
     &'      SAMCRA       SQBOT       SQDRA       SQRAP       SAMAQ',
     &'       SQSUR     SOLBAL      DATE*',/,
     &'*dd/mm/yyyy  nr      mg/cm2      mg/cm2      mg/cm2      mg/cm2',
     &'      mg/cm2      mg/cm2      mg/cm2      mg/cm2      mg/cm2',
     &'      mg/cm2     mg/cm2 dd/mm/yyyy',/,
     &'*<========><==><==========><==========><==========><==========>',
     &'<==========><==========><==========><==========><==========>',
     &'<==========><=========><=========>')

        HSBAD = .TRUE.
      ENDIF

C --- conversion of daynumber to date
      CALL NRTODA (YEAR,DAYNR,M,D)

C --- Write output record .SBA file

      WRITE(SBA,15) D,M,YEAR,NINT(T),(SQPREC+SQIRRIG),DECTOT,ROTTOT,
     &  SAMPRO,SAMCRA,SQBOT,SQDRA,SQRAP,SAMAQ,SQSUR,SOLBAL,D,M,YEAR
 15   FORMAT(I3,'/',I2.2,'/',2I4,10E12.4,1E11.2,I3,'/',I2.2,'/',I4)

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE OUTSWB (OUTNAM,SWB,HSWBD,ENVSTR,STASTR,DAYNR,YEAR,
     & GWL,POND,wlstar,wls,WSTINI,wst,CQDRD,CRUNO,CQDRAR,CWSUPP,CWOUT,
     & NUMADJ,HWLMAN,VTAIR,OVERFL,SWSEC,SWMAN,NMPER,IMPEND,IMPER,
     & HBWEIR,T)
C ----------------------------------------------------------------------
C     Date               : 11/11/97
C     Purpose            : write surface water balance data to 
C                          OUTNAM.SWB file surface water management
C                          data to OUTNAM.MAN. The files overlap
C     Subroutines called : 
C     Functions called   : -
C     File usage         : OUTNAM.SWB, OUTNAM.MAN
C ---------------------------------------------------------------------
      IMPLICIT NONE

C --- Global
      INTEGER   SWB,MAN,DAYNR,YEAR,D,M,swsec,swman(10),nmper,impend(10)
      INTEGER   imper, numadj

      REAL      GWL,POND,WLSTAR,WSTINI,WLS,WST,CQDRD,CRUNO
      REAL      CQDRAR,CWSUPP,CWOUT,hwlman,vtair,t,hbweir(nmper)

      CHARACTER OUTNAM*8,FILNAM*12,ENVSTR*50,STASTR*7

      character*80 rmldsp
      
      LOGICAL   OVERFL

C --- Local
      REAL      GWLEV,CQDRF1,C1WSUPP,C1WOUT,DELBAL

      CHARACTER SPC*1

      LOGICAL   HSWBD

      SAVE
c
C ----------------------------------------------------------------------
C ---   determine which management period the model is in:
      IF (SWSEC .EQ. 2) THEN
        imper   = 0
   5    imper   = imper + 1
        if (imper .gt. nmper) stop 'OUTSWB: err. sw-management periods'
        if (int(T) .gt. impend(imper)) goto 5
      ENDIF

C --- add ponding to groundwater level, if gwl at soil surface:
      if (abs(gwl) .lt. 1.0e-7) then
          gwlev = pond
      else
          gwlev = gwl
      endif

      IF (.NOT.HSWBD) THEN

C --- compose filename
        CALL SHIFTR (OUTNAM)
        FILNAM = OUTNAM//'.SWB'
        CALL SHIFTL (FILNAM)
        CALL SHIFTR (ENVSTR)

C --- open output file
        CALL FINDUNIT (10,SWB)
        OPEN (SWB,FILE =rmldsp(ENVSTR//FILNAM),STATUS =STASTR,
     &  ACCESS = 'SEQUENTIAL')

C --- write header
        WRITE (SWB,10)
        WRITE (SWB,11)
10      FORMAT (
     &'* Surface water system:',/,'*',/,
     &'* - GWL           : groundwater level + ponding (<0. = below ',
     &'s.s)',/,
     &'* - WLST          : target level,  aut. weir (<0. = b.s.s.) ',/,
     &'* - WLST          : weir crest,   fixed weir (<0. = b.s.s.) ',/,
     &'* - WLS           : surface water level (<0. = b.s.s.) ',/,
     &'* - WST           : storage in sw-reservoir, per unit area of',
     &'* subcatchment',/,
     &'* - D+RO+R        : drainage fluxes (>0. = into sw) + runoff +',
     &'* rapid drainage')
c
11      FORMAT (
     &'* - QSUPP         : external supply to sw-reservoir',/, 
     &'* - QOUT          : outflow from sw-reservoir',/,'*',/,
     &'*DATE              GWL   WLST    WLS   WST D+RO+R  QSUPP',
     &'   QOUT D+RO+R  QSUPP   QOUT',/,
     &'*dd/mm/yyyy  nr                               inc    inc',
     &'    inc    cum    cum    cum',/,
     &'*                 [cm]   [cm]   [cm]  [cm]   [cm]   [cm]',
     &'   [cm]   [cm]   [cm]   [cm]',/,
     &'*<============><=====><=====><=====><====><=====><=====>',
     &'<=====><=====><=====><=====>')

C --- write record for initial state
        WRITE (SWB,19) gwlev,wlstar,wls,wst,(0.),(0.),(0.),(0.),
     &   (0.),(0.)
 19     FORMAT ('*>> initial    ',3f7.1,f6.1,6f7.1)

C --- compose filename for management data
        IF (SWSEC .EQ. 2) THEN
          CALL SHIFTR (OUTNAM)
          FILNAM = OUTNAM//'.MAN'
          CALL SHIFTL (FILNAM)
          CALL SHIFTR (ENVSTR)

C --- open output file for management
          CALL Findunit (10,MAN)
          OPEN (MAN,FILE =rmldsp(ENVSTR//FILNAM),STATUS =STASTR,
     &    ACCESS = 'SEQUENTIAL')

          WRITE (MAN,20)
          WRITE (MAN,21)
20        FORMAT (
     &'* Surface water management:',/,'*',/,
     &'* - SWMAN         : type of weir (f = fixed; a = automatic)',/
     &'* - GWL           : groundwater level + ponding (<0. = below ',
     &'s.s)',/,
     &'* - HWLMAN        : pressure head used for target level (cm)',/,
     &'* - VTAIR         : total air volume in soil profile (cm)',/
     &'* - WLST          : target level of autom. weir (<0. = b.s.s.) '
     & ,/,
     &'*              or : crest  level of fixed  weir (<0. = b.s.s.) '
     & ,/,
     &'* - WLS           : surface water level (<0. = b.s.s.) ',/,
     &'* - QOUT          : surface water outflow (<0. = supply)',/,
     &'* - NUMADJ        : number of adjustments of target level',/,
     &'* - OVERFL        : flag for overflow of aut. weir (o)',/,
     &'* - CREST         : Crest level (<0. = b.s.s.)',/,'*')
21        FORMAT (
     &'*DATE           SWMAN     GWL HWLMAN  VTAIR   WLST    WLS   QOUT'
     &,' NUMADJ OVERFL  CREST',/,
     &'*dd/mm/yyyy  nr          [cm]   [cm]   [cm]   [cm]   [cm]   [cm]'
     &'   [cm]',/,
     &'*<============><=====><=====><=====><=====><=====><=====><=====>'
     &,'<=====><=====><=====>')
C
        ENDIF
C
        cqdrf1 = 0
        c1wsupp = 0
        c1wout = 0

        HSWBD    = .true.

        return
      endif

C --- water balance error (water creation)
      delbal = (wst + cwout) - (wstini + cqdrd+cruno+cqdrar + cwsupp)
      if (delbal .gt. 0.05) then
         write(6,1001) delbal
1001     format(/' >>Error in cumulative water balance of sw:',
     &     f5.2)
      endif

C --- write output record OUTNAM.SWB

C --- conversion of daynumber to date
      CALL NRTODA (YEAR,DAYNR,M,D)

      WRITE (SWB,30) D,M,YEAR,NINT(T),gwlev,wlstar,wls,wst,
     &  (cqdrd+cruno+cqdrar-cqdrf1),(cwsupp-c1wsupp),(cwout-c1wout),
     &  (cqdrd+cruno+cqdrar),cwsupp,cwout

 30   FORMAT (1x,I2,'/',I2.2,'/',2I4,3f7.1,f6.1,6f7.1)

C --- write output record OUTNAM.MAN
      if (swsec .eq. 2) then
        if (overfl) then
          spc = 'o'
        else
          spc = '-'
        endif
        IF (SWMAN(imper) .EQ. 1) THEN
          WRITE (MAN,31) D,M,YEAR,NINT(T),gwlev,wlstar,wls,
     &  ((cwout-c1wout)-(cwsupp-c1wsupp)),numadj,spc,hbweir(imper)
        ELSE
          WRITE (MAN,32) D,M,YEAR,NINT(T),gwlev,hwlman,vtair,wlstar,wls,
     &  ((cwout-c1wout)-(cwsupp-c1wsupp)),numadj,spc,hbweir(imper)
        ENDIF

 31     FORMAT (1x,I2,'/',I2.2,'/',2i4,4x,'f',2x,f7.1,2('     - '),
     &  3f7.1,i7,6x,a1,f7.1)
 32     FORMAT (1x,I2,'/',I2.2,'/',2i4,4x,'a',2x,6f7.1,i7,6x,a1,f7.1)
      endif

C --- store cumulative values
      cqdrf1  = (cqdrd+cruno+cqdrar)
      c1wsupp = cwsupp
      c1wout  = cwout

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE OUTTEP (OUTNAM,TEP,HTEPD,ENVSTR,STASTR,DAYNR,YEAR,
     &  NUMNOD,TEMP,T)
C ----------------------------------------------------------------------
C     Date               : 16/01/97
C     Purpose            : write soil temperatures to output file
C     Subroutines called : SHIFTR,SHIFTL,NRTODA
C     Functions called   : -
C     File usage         : OUTNAM.TEP
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

      INTEGER   TEP,DAYNR,YEAR,NODE,NUMNOD,D,M
      REAL      T
      REAL*8    TEMP(MACP)

      CHARACTER OUTNAM*8,FILNAM*12,ENVSTR*50,STASTR*7

      character*80 rmldsp
      
      LOGICAL   HTEPD
C ----------------------------------------------------------------------
      IF (.NOT.HTEPD) THEN

C --- compose filename
        CALL SHIFTR (OUTNAM)
        FILNAM = OUTNAM//'.TEP'
        CALL SHIFTL (FILNAM)
        CALL SHIFTR (ENVSTR)

C --- open output file
        CALL FINDUNIT (10,TEP)
        OPEN (TEP,FILE =rmldsp(ENVSTR//FILNAM),STATUS = STASTR,
     &  ACCESS = 'SEQUENTIAL')

C --- write header
        WRITE (TEP,10)
10      FORMAT (
     &'*DATE      DAY Compartment number------------------------------'
     & ,/,
     &'*dd/mm/yyyy nr      1     6    11    16    21    26    31    36'
     & ,/,
     &'*<========><==><====><====><====><====><====><====><====><====>')
        HTEPD = .TRUE.
      ENDIF
 
C --- conversion of daynumber to date
      CALL NRTODA (YEAR,DAYNR,M,D)

      write (TEP,1010) D,M,YEAR,NINT(T),(temp(node),node=1,numnod,5)
1010  format(I3,'/',I2.2,'/',2I4,8F6.1)

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE OUTVAP (SWSOLU,OUTNAM,VAP,HVAPD,ENVSTR,STASTR,DAYNR,
     &  YEAR,NUMNOD,Z,THETA,H,CML,SWTEMP,TEMP,T,Q)
C ----------------------------------------------------------------------
C     Date               : 22/12/98
C     Purpose            : write to additional short output file
C     Subroutines called : SHIFTR,SHIFTL,NRTODA
C     Functions called   : -
C     File usage         : OUTNAM.VAP
C ---------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'
C --- global
      INTEGER   SWSOLU,VAP,DAYNR,YEAR,NUMNOD,SWTEMP

      REAL      Z(MACP),CML(MACP),T
      REAL*8    THETA(MACP),H(MACP),TEMP(MACP),Q(MACP+1)

      CHARACTER OUTNAM*8,ENVSTR*50,STASTR*7

      character*80 rmldsp

      LOGICAL   HVAPD
C ----------------------------------------------------------------------
C --- local
      INTEGER   d,m,node

      CHARACTER filnam*12
      REAL*8 WFLUX,SFLUX
C ----------------------------------------------------------------------
      IF (.NOT.HVAPD) THEN 

C --- compose filename
        CALL SHIFTR (OUTNAM)
        FILNAM = OUTNAM//'.VAP'
        CALL SHIFTL (FILNAM)
        CALL SHIFTR (ENVSTR)
      
C --- open output file
        CALL FINDUNIT (10,VAP)
        OPEN (VAP,FILE=rmldsp(ENVSTR//FILNAM), STATUS = STASTR,
     &  ACCESS='SEQUENTIAL')

C --- write header
        WRITE (VAP,50) 

 50   FORMAT ('*      date       depth  water       head     solute  ',
     &        'temp       Wflux       Sflux',/,
     &        '*                    cm    (-)         cm     mg/cm3  ',
     &        '   C        cm/d    mg/cm2/d')


c        HVAPD = .TRUE.

      ENDIF

C --- Write output .VAP file

C --- conversion of daynumber to date
      CALL NRTODA (YEAR,DAYNR,M,D)

C --- write output record

      DO 20 NODE = 1,NUMNOD
        if (SWTEMP.EQ.0) TEMP(NODE) = -99.9d0
        if (SWSOLU.EQ.0) CML(NODE)  = 0.0
        WFLUX = (Q(NODE)+Q(Node+1))/2
        SFLUX = WFLUX*CML(NODE)

        IF  (.not. HVAPD) then
          WRITE (VAP,79) D,M,YEAR,NINT(T),Z(NODE),THETA(NODE),
     &                   H(NODE),CML(NODE), TEMP(NODE),WFLUX,SFLUX
        ELSE
          WRITE (VAP,80) D,M,YEAR,NINT(T),Z(NODE),THETA(NODE),
     &                   H(NODE),CML(NODE), TEMP(NODE),WFLUX,SFLUX
        ENDIF

20    CONTINUE
      HVAPD = .true.

      WRITE (VAP,'(2X)')

 79   FORMAT('*',I2,'/',I2.2,'/',2I4,1X,F7.1,F7.3,E11.3,E11.3,F6.1,
     & 2E12.3)
 80   FORMAT(    I3,'/',I2.2,'/',2I4,1X,F7.1,F7.3,E11.3,E11.3,F6.1,
     & 2E12.3)

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE OUTWBA (OUTNAM,WBA,HWBAD,ENVSTR,STASTR,DAYNR,YEAR,
     &  CGRAI,CNRAI,CGIRD,CNIRD,CRUNO,CQROT,CEVAP,CQBOT,CQDRA,
     &  CPTRA,CPEVA,GWL,T,CQDRAR,VOLACT,VOLINI,POND,RUNNR,
     &  SWSCRE,CQDARCY,CQTOP)
C ----------------------------------------------------------------------
C     Date               : 18/08/98
C     Purpose            : write water balance data to OUTNAM.WBA file
C     Subroutines called : SHIFTR,SHIFTL,NRTODA
C     Functions called   : -
C     File usage         : OUTNAM.WBA
C ---------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER   WBA,DAYNR,YEAR,D,M,RUNNR,SWSCRE

      REAL      CEVAP,CGIRD,CGRAI,CNIRD,CNRAI,CPEVA,CPTRA,CQBOT,DSTOR
      REAL      CQDRA,CQROT,CRUNO,GWL,T,CQDRAR,POND,CQDARCY,CQTOP
      REAL*8    VOLACT,VOLINI

      CHARACTER OUTNAM*8,FILNAM*12,ENVSTR*50,STASTR*7

      character*80 rmldsp

      LOGICAL   HWBAD
C ----------------------------------------------------------------------
      IF (.NOT.HWBAD) THEN

C --- compose filename
        CALL SHIFTR (OUTNAM)
        FILNAM = OUTNAM//'.WBA'
        CALL SHIFTL (FILNAM)
        CALL SHIFTR (ENVSTR)

C --- open WBA output file
        CALL FINDUNIT (10,WBA)
        OPEN (WBA,FILE =rmldsp(ENVSTR//FILNAM), STATUS = STASTR, 
     &  ACCESS = 'SEQUENTIAL')

C --- write header WBA file
        WRITE (WBA,10)
10      FORMAT (
     &'*      DATE DAY   RAIN [cm]     IRR [cm]      RUO    TRA [cm]  ',
     &'    EVS [cm]      FLUX [cm]      DSTOR     GWL  QDIF      Date*',
     & /, 
     &'*dd/mm/yyyy  nr    gro....net   gro...net      cm    pot....act',
     &'    pot....act     lat.....bot      cm      cm    cm dd/mm/yyyy',
     & /,
     &'*<========><==><=====><=====><====><====><======><=====><=====>',
     &'<=====><=====><======><======><======><======><====><=========>')

C --- write header screen output
        IF (SWSCRE.EQ.1) THEN
          WRITE (*,20) RUNNR
 20       FORMAT(/,' RUN ',I2,T20,
     &           'Cumulative water balance components (cm)',/)
          WRITE (*,22)
 22       FORMAT ('       Date   Rain  Irrig Runoff Transp Evapor',
     &            '  Drain   Qbot    Gwl   Qdif'/,
     &            '             gross  gross        actual actual',
     &            '    net    net           cum')
        ENDIF

        HWBAD = .TRUE.
      ENDIF
C --- write output water balance components

C --- conversion of daynumber to date
      CALL NRTODA (YEAR,DAYNR,M,D)

C --- write output record WBA file
      DSTOR = REAL(VOLACT) + POND - REAL(VOLINI)
      WRITE (WBA,30) D,M,YEAR,NINT(T),CGRAI,CNRAI,CGIRD,CNIRD,CRUNO,
     &  CPTRA,CQROT,CPEVA,CEVAP,(CQDRA+CQDRAR),CQBOT,DSTOR,GWL,
     &  (CQDARCY-CQTOP),D,M,YEAR
 30   FORMAT (I3,'/',I2.2,'/',2I4,2(1x,F6.2),2(1x,F5.1),1x,F7.2,
     &        4(1x,F6.2),3(1x,F7.2),1x,F7.1,1x,F5.2,I3,'/',I2.2,'/',I4)

C --- write output record screen
      IF (SWSCRE.EQ.1) THEN
        WRITE (*,40) D,M,YEAR,CGRAI,CGIRD,CRUNO,CQROT,CEVAP,
     &               (CQDRA+CQDRAR),CQBOT,GWL,(CQDARCY-CQTOP)
 40     FORMAT(I3,'/',I2.2,'/',I4,7F7.2,F7.1,F7.2)
      ENDIF

      RETURN
      END

** FILE:
**    SWALIBPZ.FOR - part of program SWAP
** FILE IDENTIFICATION:
**    $Id: swalibpz.for 1.8.1.10 1999/02/17 17:35:13 kroes Exp $
** DESCRIPTION:
**    This file contains program units of SWAP. The program units 
**    in this file are of the 3rd level and are sorted alphabetically
**    with the first letter of the program unit ranging from P - Z.
**    The following program units are in this file:
**        PENMON, PRHNODE, RADIAT, RDBBC, RDCRPD, RDCRPS, RDDRB, RDDRE,
**        RDGRASS, RDHEA, RDKEY, RDSLT, RDSOL, RDSWA, EDUCEVA,
**        ROOTEX, SLTBAL, SOILTMP, SOLUTE, THENODE, TOTASS,
**        TRIDAG, UPDATE, WATCON, WBALLEV, WLEVBAL, WLEVST, WSTLEV,
**        QHTAB, ZEROCUMU, ZEROINTR
************************************************************************
C ----------------------------------------------------------------------
      SUBROUTINE PENMON (DAYNR,LAT,ALT,A,B,RCS,RCC,RAD,TAV,HUM,
     & WIN,RSC,ES0,ET0,EW0,SWCF,CF,ISTAGE)
C ----------------------------------------------------------------------
C     Date               : 14/01/99
C     Purpose            : Calculation of potential evaporation & 
C                          transpiration rates from a bare soil surface,
C                          a dry and a wet crop canopy;           
C                          based on the Penman - Monteith approach.
C
C     Formal parameters  : (I = input, O = output)
C     DAYNR  daynumber (January 1st = 1) [-]...........................I
C     LAT    latitude [degr.,dec.degr., N=+,S=-].......................I
C     ALT    altitude above mean sea level [m].........................I
C     A      first  Angstrom coefficient [-]...........................I
C     B      second Angstrom coefficient [-]...........................I
C     RCS    reflection coefficient soil [-]...........................I
C     RCC    reflection coefficient crop [-]...........................I
C     RAD    incoming short wave radiation [J/m2/d]....................I
C     TAV    average day temperature [C]...............................I
C     HUM    vapour pressure [kPa].....................................I
C     WIN    windspeed at 2 m height [m/s].............................I
C     RCS    minimum canopy resistance [s/m]...........................I
C     ES0    potential evaporation rate from a  bare soil [mm/d].......O
C     ET0    potential transpiration rate from a dry crop [mm/d].......O
C     EW0    potential transpiration rate from a wet crop [mm/d].......O
C     SWCF   CF contains crop factor (=1) or crop height (=2)
C     CF     crop factor [-] or crop height [cm]
C     IStage no crop [=1] or yes crop [=2]
C
C     Subroutines called : ASTRO
C
C     Functions called   : LIMIT
C
C     File usage         : -
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER DAYNR,SWCF,IStage

      REAL    LIMIT,LAMBDA,LAT,CHRef,CF
      REAL    A,ALT,ATMTR,B,COSLD,CP,DAYL,DAYLP,DELTA,DSINB,DSO,EA
      REAL    ED,ES0,ET0,ETAERC,ETAERS,ETAERW,ETRADC,ETRADS,ETRADW,EW0
      REAL    G,GAMMA,GAMMOC,GAMMOS,GAMMOW,HUM,PALT,PI,RAC,RAD,RAS,RAW
      REAL    RCC,RCS,RELSSD,RHO,RNC,RNL,RNS,RNW,RSC,RSS,RSW,SC,SINLD
      REAL    TAV,TAVK,TKV,UD,VPD,WIN,CH

      PARAMETER (CHRef = 12.0, PI = 3.1415962)
C ----------------------------------------------------------------------
C --- avoid zero crop height and crop height > 3.0 m
      If (Istage.EQ.1) then
        CH = CHref
      else 
        If (SWCF.EQ.1) Then
          CH = CHRef
        Else
          CH = MAX (CF,0.1)
          CH = Min (CF,295.0)
        Endif
      Endif
     
C --- conversion of average temperature from [C] to [K]
      TAVK = TAV+273.0

C --- atmospheric pressure at elevation ALT [kPa]
      PALT = 101.3*((TAVK-0.0065*ALT)/TAVK)**5.26

C --- latent heat of vaporization [MJ/kg]
      LAMBDA = 2.501-0.002361*TAV

C --- saturation vapour pressure at TAV [kPa]
      EA  = 0.611*EXP(17.27*TAV/(TAV+237.3))
C --- measured vapour pressure not to exceed saturated vapour pressure
      ED  = MIN(HUM,EA)
C --- vapour pressure deficit [kPa]
      VPD = EA-ED

C --- slope vapour pressure curve [kPa/C]
      DELTA = 4098*EA/(TAV+237.3)**2

C --- psychrometric constant [kPa/C]
      GAMMA = 0.00163*PALT/LAMBDA

C --- atmospheric density [kg/m3]
      TKV = TAVK/(1.0-0.378*ED/PALT)
      RHO = 3.486*PALT/TKV

C --- specific heat moist air [kJ/kg/C]
      CP = 622*GAMMA*LAMBDA/PALT

C --- day wind [m/s], avoid zero windspeed
      UD = MAX (WIN*1.33,0.0001)

C --- surface resistance [s/m] - Soil & Wet crop
      RSS = 0
      RSW = 0

C --- aerodynamic resistance [s/m] - Soil, Crop & Wet crop
      RAS = LOG((200.-0.67*0.1)/0.123/0.1)*LOG((200.-0.67*0.1)
     &      /0.0123/0.1)/(0.1681*UD)
      RAC = LOG((200.-0.67*CH)/0.123/CH)*LOG((200.-0.67*CH)/
     &      0.0123/CH)/(0.1681*UD)
      RAW = LOG((200.-0.67*CH)/0.123/CH)*LOG((200.-0.67*CH)/
     &      0.0123/CH)/(0.1681*UD)

C --- modified psychrometric constant [kPa/C] - Soil, Crop & Wet crop 
      GAMMOS = GAMMA*(1.0+RSS/RAS)
      GAMMOC = GAMMA*(1.0+RSC/RAC)
      GAMMOW = GAMMA*(1.0+RSW/RAW)

C --- net short wave radiation [MJ/m**2/d] - Soil, Crop & Wet crop
      RNS = (1.0-RCS)*RAD/1000000
      RNC = (1.0-RCC)*RAD/1000000
      RNW = (1.0-RCC)*RAD/1000000

C --- net long wave radiation [MJ/m**2/d]
      CALL ASTRO (DAYNR,LAT,DAYL,DAYLP,SINLD,COSLD)
      DSINB  = 3600.*(DAYL*SINLD+24.*COSLD*SQRT(1.-(SINLD/COSLD)**2)/PI)
      SC     = 1370.*(1.+0.033*COS(2.*PI*DAYNR/365.))
      DSO    = SC*DSINB
      ATMTR  = RAD/DSO
      RELSSD = LIMIT(0.0,1.0,(ATMTR-A)/B)
      RNL    = 4.9E-9*TAVK**4*(0.34-0.14*SQRT(ED))*(0.1+0.9*RELSSD)

C --- soil heat flux [MJ/m2/d]
      G = 0.0

C --- aerodynamic term of the PM equation [mm/d] - Soil, Crop & Wet crop
      ETAERS = (86.4/LAMBDA)*(1/(DELTA+GAMMOS))*(RHO*CP*VPD/RAS)
      ETAERC = (86.4/LAMBDA)*(1/(DELTA+GAMMOC))*(RHO*CP*VPD/RAC)
      ETAERW = (86.4/LAMBDA)*(1/(DELTA+GAMMOW))*(RHO*CP*VPD/RAW)

C --- radiation term of the PM equation [mm/d] - Soil, Crop & Wet crop
      ETRADS = DELTA/(DELTA+GAMMOS)*(RNS-RNL-G)*1/LAMBDA      
      ETRADC = DELTA/(DELTA+GAMMOC)*(RNC-RNL-G)*1/LAMBDA      
      ETRADW = DELTA/(DELTA+GAMMOW)*(RNW-RNL-G)*1/LAMBDA      

C --- sum of both terms [mm/d] - Soil, Crop and Wet crop      
      ES0 = MAX (0.0,ETAERS+ETRADS)
      ET0 = MAX (0.0,ETAERC+ETRADC)
      EW0 = MAX (0.0,ETAERW+ETRADW)

      RETURN
      END

C ----------------------------------------------------------------------
      REAL*8 FUNCTION PRHNODE (NODE,WCON,LAYER,DISNOD,H,FLGENU,
     & THETAR,THETAS,COFGEN,ALFAMG,HTABLE)
C ----------------------------------------------------------------------
C     Date               : 29/08/95                                       
C     Purpose            : calculate pressure head at nodal      
C                          point node from water content wcon
C     Subroutines called : -                                           
C     Functions called   : -                     
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

C --- global
      INTEGER NODE,LAYER(MACP)

      REAL    DISNOD(MACP+1)
      REAL*8  WCON,H(MACP),COFGEN(8,MAHO),HTABLE(MAHO,99),ALFAMG(MACP)
      REAL*8  THETAR(MACP),THETAS(MACP) 

      LOGICAL FLGENU(MAHO)
C ----------------------------------------------------------------------
C --- local
      INTEGER posit,lay

      REAL*8  help
C ----------------------------------------------------------------------
C --- soil layer of node 
      lay = layer(node)

      if (thetas(node)-wcon.lt.1.0d-6) then
C ---   saturated pressure head
        if (node.eq.1) then
          prhnode = disnod(node)
        else
          prhnode = h(node-1) + disnod(node)
        endif
      else
        if (flgenu(lay)) then
C ---     pressure head according to van Genuchten
          if (wcon-thetar(node).lt.1.0d-6) then
            prhnode = -1.0d12
          else
C ---       first calculate the inverse of the sorptivity
            help = (thetas(node) - thetar(node)) / 
     $             (wcon - thetar(node))
C ---       raise to the power 1/m
            help = help ** (1.0d0 / cofgen(7,lay))
C ---       subtract one and raise to the power 1/n 
            help = (help - 1.0d0) ** (1.0d0 / cofgen(6,lay))
C ---       divide by alpha.
            prhnode = -1.0d0 * abs(help/alfamg(node))
          endif
        else
C ---     interpolated pressure head from the table
          posit   = int(max (1.0,real(wcon*100.0)))
          prhnode = htable(lay,posit) + (htable(lay,posit+1)-
     $              htable(lay,posit))*(wcon-posit*0.01d0) / 0.01d0
        endif
      endif

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE RADIAT (IDAY,HOUR,DAYL,SINLD,COSLD,AVRAD,SINB,
     $                   PARDIR,PARDIF)
C ----------------------------------------------------------------------
C --- Author: Daniel van Kraalingen, 1986
C --- Calculates the fluxes of diffuse and direct photosynthetically
C --- active radiation from the total daily shortwave radiation actually
C --- received (AVRAD) for a given day of the year and hour of the day.
C --- The input variables DAYL, SINLD and COSLD are calculated in ASTRO.
C --- For more information: see Spitters et al. (1988).
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER IDAY

      REAL    AOB,ATMTR,AVRAD,COSLD,DAYL,DSINB,DSINBE,DSO,FRDIF,HOUR
      REAL    PAR,PARDIF,PARDIR,PI,SC,SINB,SINLD

      DATA    PI /3.1415926/
C ----------------------------------------------------------------------
C --- calculations on solar elevation
C --- sine of solar elevation SINB
      AOB    = SINLD/COSLD
      SINB   = AMAX1 (0.,SINLD+COSLD*COS(2.*PI*(HOUR+12.)/24.))
C --- integral of SINB
      DSINB  = 3600.*(DAYL*SINLD+24.*COSLD*SQRT(1.-AOB*AOB)/PI)
C --- integral of SINB, corrected for lower atmospheric transmission
C --- at low solar elevations
      DSINBE = 3600.*(DAYL*(SINLD+0.4*(SINLD*SINLD+COSLD*COSLD*0.5))+
     $         12.0*COSLD*(2.0+3.0*0.4*SINLD)*SQRT(1.-AOB*AOB)/PI)

C --- solar constant and daily extraterrestrial radiation
      SC     = 1370.*(1.+0.033*COS(2.*PI*IDAY/365.))
      DSO    = SC*DSINB

C --- diffuse light fraction from atmospheric transmission
      ATMTR  = AVRAD/DSO
      IF (ATMTR.GT.0.75) FRDIF = 0.23
      IF (ATMTR.LE.0.75.AND.ATMTR.GT.0.35) FRDIF = 1.33-1.46*ATMTR
      IF (ATMTR.LE.0.35.AND.ATMTR.GT.0.07) 
     $ FRDIF = 1.-2.3*(ATMTR-0.07)**2
      IF (ATMTR.LE.0.07) FRDIF = 1.

C --- photosynthetic active radiation, diffuse and direct
      PAR    = 0.5*AVRAD*SINB*(1.+0.4*SINB)/DSINBE
      PARDIF = AMIN1 (PAR,SINB*FRDIF*ATMTR*0.5*SC)
      PARDIR = PAR-PARDIF

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RDBBC (BBCFIL,ENVSTR,BAYRD,BAYRY,GWLTAB,SHAPE,RIMLAY,
     & AQAVE,AQAMP,AQTAMX,AQOMEG,QBOTAB,COFQHA,COFQHB,HGITAB,SWBOTB,
     & LOGF,YEAR,FMAY,HDRAIN)
C ----------------------------------------------------------------------
C     Date               : 17/4/98                                
C     Purpose            : reading b.c.'s at bottom of soil profile,   
C                          for the entire calculation period.          
C     Subroutines called : DATONR,SHIFTL,SHIFTR            
C     Functions called   : FROMTO                                      
C     File usage         : .BBC, file containing bottom boundary data  
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER   BBC,FROMTO,BAYRD,BAYRY,SWBOTB,NR,LOGF,YEAR,FMAY

      REAL      GWLTAB(732),QBOTAB(732),HGITAB(50)
      REAL      SHAPE,RIMLAY,AQAVE,AQAMP,AQTAMX,AQOMEG,HDRAIN
      REAL      AQPER,COFQHA,COFQHB,PI

      CHARACTER BBCFIL*8,ENVSTR*50,FILNAM*12

      PARAMETER (PI=3.14159)
C ----------------------------------------------------------------------
C --- local
      INTEGER SWOPT,SWC2,dd(366),mm(366),yy(366),I,IFND

      REAL    value(366),C2AVE,C2AMP,C2MAX

      CHARACTER LINE*80

      character*80 rmldsp
      
      LOGICAL BLANK,COMMENT,EXISTS
C ----------------------------------------------------------------------

C --- compose filename
      CALL SHIFTR (BBCFIL)
      FILNAM = BBCFIL//'.BBC'
      CALL SHIFTL (FILNAM)
      CALL SHIFTR (ENVSTR)

C --- check if a file with bottom boundary conditions does exist
      INQUIRE (FILE=rmldsp(ENVSTR//FILNAM),EXIST=EXISTS)

      IF (.NOT.EXISTS) THEN
C ---   write error to log file
        WRITE (LOGF,98) ENVSTR//FILNAM
 98     FORMAT ('SWAP can not find the input file',/,A)
        STOP 'The .BBC file was not found: SWAP stopped !'
      ENDIF

C --- open file with bottom boundary data
      CALL FINDUNIT (14,BBC)
      OPEN (BBC,FILE=rmldsp(ENVSTR//FILNAM),status='old'
     & ,access='sequential')

C --- given groundwaterlevel
      CALL RSINTR (BBC,FILNAM,LOGF,'SWOPT1',0,1,SWOPT)
      IF (SWOPT.EQ.1) THEN

C ---   position file pointer
        IFND = 0
14      READ (BBC,'(A)') LINE
        CALL ANALIN (LINE,BLANK,COMMENT)
        IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 14
        IF (COMMENT) GOTO 15
        IFND = IFND+1
        BACKSPACE (BBC)
        READ (BBC,*) DD(IFND),MM(IFND),value(IFND)
        GOTO 14
C ---   ready...
15      CONTINUE
C ---   year is calculated
        DO 16 I = 1,IFND 
          if (mm(I).GE.FMAY) yy(I) = BAYRY
          if (mm(I).LT.FMAY) yy(I) = BAYRY+1
16      CONTINUE
        DO 17, I=1,IFND
          CALL DATONR (yy(I),mm(I),dd(I),nr)
          GWLTAB(I*2)   = value(I) 
          GWLTAB(I*2-1) = FROMTO (BAYRD,BAYRY,NR,YY(I))+1
17      CONTINUE
        SWBOTB = 1
        GOTO 1000
      ENDIF 
      CALL JMPLBL (BBC,FILNAM,LOGF,'SWOPT2')

C --- regional bottom flux is given                             
      CALL RSINTR (BBC,FILNAM,LOGF,'SWOPT2',0,1,SWOPT)
      IF (SWOPT.EQ.1) THEN
        CALL RSINTR (BBC,FILNAM,LOGF,'SWC2',1,2,SWC2)
        IF (SWC2 .EQ. 1) THEN
          CALL RSREAR (BBC,FILNAM,LOGF,'C2AVE',-10.0,10.0,C2AVE)
          CALL RSREAR (BBC,FILNAM,LOGF,'C2AMP',-10.0,10.0,C2AMP)
          CALL RSREAR (BBC,FILNAM,LOGF,'C2MAX',1.0,366.0,C2MAX)
          C2MAX = FROMTO (BAYRD,BAYRY,INT(C2MAX),YEAR)+1
C ---     fill table with sine function
          DO 19 I = 1,366
            QBOTAB(I*2)   = C2AVE+C2AMP*cos(0.0172*(I-C2MAX)) 
            QBOTAB(I*2-1) = I
 19       CONTINUE 
          SWBOTB = 2
          GOTO 1000
        ELSE
C ---     read table, position pointer
          Call JMPLBL (BBC,FILNAM,LOGF,'C2MAX')
          Read (BBC,'(A)') LINE
          IFND = 0
24        READ (BBC,'(A)') LINE
          CALL ANALIN (LINE,BLANK,COMMENT)
          IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 24
          IF (COMMENT) GOTO 25
          IFND = IFND+1
          BACKSPACE (BBC)
          READ (BBC,*) DD(IFND),MM(IFND),value(IFND)
          GOTO 24
C ---     ready...
25        CONTINUE
C ---     year is calculated
          DO 26 I = 1,IFND 
            if (mm(I).GE.FMAY) yy(I) = BAYRY
            if (mm(I).LT.FMAY) yy(I) = BAYRY+1
26        CONTINUE
          DO 27, I=1,IFND
            CALL DATONR (yy(I),mm(I),dd(I),nr)
            QBOTAB(I*2)   = value(I) 
            QBOTAB(I*2-1) = FROMTO (BAYRD,BAYRY,NR,YY(I))+1
27        CONTINUE
          SWBOTB = 2
          GOTO 1000
        ENDIF
      ENDIF 
      CALL JMPLBL (BBC,FILNAM,LOGF,'SWOPT3')

C --- calculated flux through the bottom of the profile
      CALL RSINTR (BBC,FILNAM,LOGF,'SWOPT3',0,1,SWOPT)
      IF (SWOPT.EQ.1) THEN
        CALL RSREAR (BBC,FILNAM,LOGF,'SHAPE',0.0,1.0,SHAPE)
        CALL RSREAR (BBC,FILNAM,LOGF,'HDRAIN',-1.0E4,0.0,HDRAIN)
        CALL RSREAR (BBC,FILNAM,LOGF,'RIMLAY',0.0,1.0E5,RIMLAY)
        CALL RSREAR (BBC,FILNAM,LOGF,'AQAVE',-1000.0,1000.0,AQAVE)
        CALL RSREAR (BBC,FILNAM,LOGF,'AQAMP',0.0,1000.0, AQAMP)
        CALL RSINTR (BBC,FILNAM,LOGF,'AQTAMX',1,366,NR)
        AQTAMX = FROMTO (BAYRD,BAYRY,NR,YEAR)+1
        CALL RSREAR (BBC,FILNAM,LOGF,'AQPER',0.0,366.0,AQPER)
        AQOMEG = PI*2./365.
        IF (AQAMP.GT.0.1) THEN
          AQOMEG = PI*2./AQPER
        ENDIF
        SWBOTB = 3
        GOTO 1000
      ENDIF
      CALL JMPLBL (BBC,FILNAM,LOGF,'SWOPT4')

C --- flux-groundwater level relationship 
      CALL RSINTR (BBC,FILNAM,LOGF,'SWOPT4',0,1,SWOPT)
      IF (SWOPT.EQ.1) THEN
        CALL RSREAR (BBC,FILNAM,LOGF,'COFQHA',-100.0,100.0,COFQHA)
        CALL RSREAR (BBC,FILNAM,LOGF,'COFQHB',-1.0,1.0,COFQHB)
        SWBOTB = 4
        GOTO 1000
      ENDIF
      CALL JMPLBL (BBC,FILNAM,LOGF,'SWOPT5')

C --- pressure head of lowest compartment is given 
      CALL RSINTR (BBC,FILNAM,LOGF,'SWOPT5',0,1,SWOPT)
      IF (SWOPT.EQ.1) THEN

C ---   position file pointer
        IFND = 0
34      READ (BBC,'(A)') LINE
        CALL ANALIN (LINE,BLANK,COMMENT)
        IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 34
        IF (COMMENT) GOTO 35
        IFND = IFND+1
        BACKSPACE (BBC)
        READ (BBC,*) DD(IFND),MM(IFND),value(IFND)
        GOTO 34
C ---   ready...
35      CONTINUE
C ---   year is calculated
        DO 36 I = 1,IFND 
          if (mm(I).GE.FMAY) yy(I) = BAYRY
          if (mm(I).LT.FMAY) yy(I) = BAYRY+1
36      CONTINUE
        DO 37, I=1,IFND
          CALL DATONR (yy(I),mm(I),dd(I),nr)
          HGITAB(I*2)   = value(I) 
          HGITAB(I*2-1) = FROMTO (BAYRD,BAYRY,NR,YY(I))+1
37      CONTINUE
        SWBOTB = 5
        GOTO 1000
      ENDIF 
      CALL JMPLBL (BBC,FILNAM,LOGF,'SWOPT6')

C --- zero flux
      CALL RSINTR (BBC,FILNAM,LOGF,'SWOPT6',0,1,SWOPT)
      IF (SWOPT.EQ.1) THEN
        SWBOTB = 6
        GOTO 1000
      ENDIF
      CALL JMPLBL (BBC,FILNAM,LOGF,'SWOPT7')

C --- free drainage 
      CALL RSINTR (BBC,FILNAM,LOGF,'SWOPT7',0,1,SWOPT)
      IF (SWOPT.EQ.1) THEN
        SWBOTB = 7
        GOTO 1000
      ENDIF
      CALL JMPLBL (BBC,FILNAM,LOGF,'SWOPT8')

C --- lysimeter with free outflow 
      CALL RSINTR (BBC,FILNAM,LOGF,'SWOPT8',0,1,SWOPT)
      IF (SWOPT.EQ.1) THEN
        SWBOTB = 8
        GOTO 1000
      ENDIF

1000  CLOSE (BBC)
      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RDCRPD (CRPFIL,ENVSTR,SWCF,CFTB,IDSL,DLO,DLC,TSUMEA,
     &  TSUMAM,DTSMTB,DVSEND,TDWI,LAIEM,RGRLAI,SLATB,SPA,
     &  SSA,SPAN,TBASE,KDIF,KDIR,EFF,AMAXTB,TMPFTB,TMNFTB,CVL,CVO,CVR,
     &  CVS,Q10,RML,RMO,RMR,RMS,RFSETB,FRTB,FLTB,FSTB,FOTB,PERDL,RDRRTB,
     &  RDRSTB,HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,HLIM4,RSC,ADCRH,
     &  ADCRL,ECMAX,ECSLOP,COFAB,RDI,RRI,RDC,RDCTB,LOGF)
C ----------------------------------------------------------------------
C     Date               : 14/1/99    
C     Purpose            : get crop parameters from cropfile
C     Subroutines called : SHIFTR, SHIFTL
C     Functions called   : -
C     File usage         : CRPFIL, file containing crop parameters
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER CRP,I,IDSL,LOGF,IFND,SWCF
 
      REAL CFTB(30),DTSMTB(30),SLATB(30),AMAXTB(30),TMPFTB(30)
      REAL TMNFTB(30),RFSETB(30),FRTB(30),FLTB(30),FSTB(30),FOTB(30)
      REAL ECMAX,ECSLOP,RDRRTB(30),RDRSTB(30),KDIF,KDIR,COFAB,LAIEM
      REAL ADCRH,ADCRL,CVL,CVO,CVR,CVS,DLC,DLO,DVSEND,EFF
      REAL PERDL,Q10,RDC,RDI,RGRLAI,RML,RMO,RMR,RMS,RRI,SPA,SPAN
      REAL SSA,TBASE,TDWI,TSUMAM,TSUMEA,RDCTB(22)
      REAL HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,HLIM4,RSC
      REAL X,SUM,RFAC,VALUE,AFGEN

      CHARACTER CRPFIL*8,ENVSTR*50,FILNAM*12

      character*80 rmldsp
      
      LOGICAL   EXISTS
C ----------------------------------------------------------------------
C --- compose filename 
      CALL SHIFTR (CRPFIL)
      FILNAM = CRPFIL//'.CRP'
      CALL SHIFTL (FILNAM)
      CALL SHIFTR (ENVSTR)
     
C --- check if a file with detailed crop data does exist
      INQUIRE (FILE=rmldsp(ENVSTR//FILNAM),EXIST=EXISTS)
     
      IF (.NOT.EXISTS) THEN
C ---   write error to log file
        WRITE (LOGF,92) ENVSTR//FILNAM
 92     FORMAT ('SWAP can not find the input file',/,A)
       STOP 'The .CRP file was not found: SWAP stopped !'
      ENDIF

     
C --- open file with crop data
      Call FINDUNIT (10,CRP) 
      OPEN (CRP,FILE=rmldsp(ENVSTR//FILNAM),STATUS='OLD',
     & access='sequential')

C --- Crop factor or crop height
      CALL RSINTR (CRP,FILNAM,LOGF,'SWCF',1,2,SWCF)
      IF (SWCF.EQ.1) then
        CALL RAREAR (CRP,FILNAM,LOGF,'CFTB',0.0,2.01,CFTB,30,IFND)
      ELSEIF (SWCF.EQ.2) then
        CALL RAREAR (CRP,FILNAM,LOGF,'CFTB',0.0,1000.0,CFTB,30,IFND)
      ENDIF

C --- phenology
      CALL RSINTR (CRP,FILNAM,LOGF,'IDSL',0,2,IDSL)
      IF (IDSL.EQ.1.OR.IDSL.EQ.2) then
        CALL RSREAR (CRP,FILNAM,LOGF,'DLO',0.0,24.0,DLO)
        CALL RSREAR (CRP,FILNAM,LOGF,'DLC',0.0,24.0,DLC)
      ENDIF
      CALL JMPLBL (CRP,FILNAM,LOGF,'TSUMEA')
      IF (IDSL.EQ.0.OR.IDSL.EQ.2) then
        CALL RSREAR (CRP,FILNAM,LOGF,'TSUMEA',0.0,10000.0,TSUMEA)
        CALL RSREAR (CRP,FILNAM,LOGF,'TSUMAM',0.0,10000.0,TSUMAM)
      ENDIF
      CALL JMPLBL (CRP,FILNAM,LOGF,'DTSMTB')
      CALL RAREAR (CRP,FILNAM,LOGF,'DTSMTB',0.0,100.0,DTSMTB,30,IFND) 
      CALL RSREAR (CRP,FILNAM,LOGF,'DVSEND',0.0,3.0,DVSEND)

C --- initial
      CALL RSREAR (CRP,FILNAM,LOGF,'TDWI',0.0,10000.0,TDWI)
      CALL RSREAR (CRP,FILNAM,LOGF,'LAIEM',0.0,10.0,LAIEM)
      CALL RSREAR (CRP,FILNAM,LOGF,'RGRLAI',0.0,1.0,RGRLAI)

C --- green area
      CALL RAREAR (CRP,FILNAM,LOGF,'SLATB',0.0,2.0,SLATB,30,IFND)
      CALL RSREAR (CRP,FILNAM,LOGF,'SPA',0.0,1.0,SPA)
      CALL RSREAR (CRP,FILNAM,LOGF,'SSA',0.0,1.0,SSA)
      CALL RSREAR (CRP,FILNAM,LOGF,'SPAN',0.0,366.0,SPAN)
      CALL RSREAR (CRP,FILNAM,LOGF,'TBASE',-10.0,30.0,TBASE)

C --- assimilation
      CALL RSREAR (CRP,FILNAM,LOGF,'KDIF',0.0,2.0,KDIF)
      CALL RSREAR (CRP,FILNAM,LOGF,'KDIR',0.0,2.0,KDIR)
      CALL RSREAR (CRP,FILNAM,LOGF,'EFF',0.0,10.0,EFF)
      CALL RAREAR (CRP,FILNAM,LOGF,'AMAXTB',0.0,100.0,AMAXTB,30,IFND)
      CALL RAREAR (CRP,FILNAM,LOGF,'TMPFTB',-10.0,50.0,TMPFTB,30,IFND)
      CALL RAREAR (CRP,FILNAM,LOGF,'TMNFTB',-10.0,50.0,TMNFTB,30,IFND)

C --- conversion of assimilates into biomass
      CALL RSREAR (CRP,FILNAM,LOGF,'CVL',0.0,1.0,CVL)
      CALL RSREAR (CRP,FILNAM,LOGF,'CVO',0.0,1.0,CVO)
      CALL RSREAR (CRP,FILNAM,LOGF,'CVR',0.0,1.0,CVR)
      CALL RSREAR (CRP,FILNAM,LOGF,'CVS',0.0,1.0,CVS)

C --- maintenance respiration
      CALL RSREAR (CRP,FILNAM,LOGF,'Q10',0.0,5.0,Q10)
      CALL RSREAR (CRP,FILNAM,LOGF,'RML',0.0,1.0,RML)
      CALL RSREAR (CRP,FILNAM,LOGF,'RMO',0.0,1.0,RMO)
      CALL RSREAR (CRP,FILNAM,LOGF,'RMR',0.0,1.0,RMR)
      CALL RSREAR (CRP,FILNAM,LOGF,'RMS',0.0,1.0,RMS)
      CALL RAREAR (CRP,FILNAM,LOGF,'RFSETB',0.0,3.0,RFSETB,30,IFND)

C --- partitioning
      CALL RAREAR (CRP,FILNAM,LOGF,'FRTB',0.0,3.0,FRTB,30,IFND)
      CALL RAREAR (CRP,FILNAM,LOGF,'FLTB',0.0,3.0,FLTB,30,IFND)
      CALL RAREAR (CRP,FILNAM,LOGF,'FSTB',0.0,3.0,FSTB,30,IFND)
      CALL RAREAR (CRP,FILNAM,LOGF,'FOTB',0.0,3.0,FOTB,30,IFND)

C --- death rates
      CALL RSREAR (CRP,FILNAM,LOGF,'PERDL',0.0,3.0,PERDL)
      CALL RAREAR (CRP,FILNAM,LOGF,'RDRRTB',0.0,3.0,RDRRTB,30,IFND)
      CALL RAREAR (CRP,FILNAM,LOGF,'RDRSTB',0.0,3.0,RDRSTB,30,IFND)

C --- water use
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM1' ,-100.0,100.0,HLIM1)
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM2U',-1000.0,100.0,HLIM2U)
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM2L',-1000.0,100.0,HLIM2L)
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM3H',-10000.0,100.0,HLIM3H)
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM3L',-10000.0,100.0,HLIM3L)
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM4' ,-16000.0,100.0,HLIM4)
      CALL RSREAR (CRP,FILNAM,LOGF,'RSC',0.0,1000.0,RSC)
      CALL RSREAR (CRP,FILNAM,LOGF,'ADCRH',0.0,5.0,ADCRH)
      CALL RSREAR (CRP,FILNAM,LOGF,'ADCRL',0.0,5.0,ADCRL)
      CALL RSREAR (CRP,FILNAM,LOGF,'ECMAX',0.0,20.0,ECMAX)
      CALL RSREAR (CRP,FILNAM,LOGF,'ECSLOP',0.0,40.0,ECSLOP)
      CALL RSREAR (CRP,FILNAM,LOGF,'COFAB',0.0,1.0,COFAB)

C --- rooting
      CALL RAREAR (CRP,FILNAM,LOGF,'RDCTB',0.0,100.0,RDCTB,22,IFND)
      CALL RSREAR (CRP,FILNAM,LOGF,'RDI',0.0,1000.0,RDI)
      CALL RSREAR (CRP,FILNAM,LOGF,'RRI',0.0,100.0,RRI)
      CALL RSREAR (CRP,FILNAM,LOGF,'RDC',0.0,1000.0,RDC)

C --- normalize RDCTB
      SUM = 0.0
      DO 96 X = 0.05,1.0,0.1
        VALUE = AFGEN (RDCTB,22,X)
        SUM = SUM+0.1*VALUE
96    CONTINUE

      RFAC = 1/SUM
      DO 98 I = 1,IFND/2
98    RDCTB(I*2) = RDCTB(I*2)*RFAC

      CLOSE (CRP)

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RDCRPS (CRPFIL,ENVSTR,IDEV,LCC,TSUMEA,TSUMAM,TBASE,
     & KDIF,KDIR,GCTB,SWGC,CFTB,SWCF,RDTB,KYTB,HLIM1,HLIM2U,HLIM2L,
     & HLIM3H,HLIM3L,HLIM4,RSC,ADCRH,ADCRL,ECMAX,ECSLOP,RDCTB,
     & COFAB,LOGF)
C ----------------------------------------------------------------------
C     Date               : 21/1/99             
C     Purpose            : get crop parameters from cropfile
C     Subroutines called : SHIFTR, SHIFTL
C     Functions called   : AFGEN
C     File usage         : CRPFIL, file containing crop parameters
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER   CRP,IDEV,I,LCC,SWGC,SWCF,LOGF,IFND

      REAL      GCTB(72),CFTB(72),RDTB(72),KYTB(72),RDCTB(22)
      REAL      ADCRH,ADCRL,ECMAX,ECSLOP,TBASE,TSUMAM,TSUMEA
      REAL      HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,HLIM4,RSC
      REAL      X,SUM,VALUE,RFAC,AFGEN,KDIF,KDIR,COFAB

      CHARACTER CRPFIL*8,FILNAM*12,ENVSTR*50

      character*80 rmldsp

      LOGICAL   EXISTS
C ----------------------------------------------------------------------
C --- compose filename
      CALL SHIFTR (CRPFIL)
      FILNAM = CRPFIL//'.CRP'
      CALL SHIFTL (FILNAM)
      CALL SHIFTR (ENVSTR)

C --- check if a file with simple crop data does exist
      INQUIRE (FILE=rmldsp(ENVSTR//FILNAM),EXIST=EXISTS)

      IF (.NOT.EXISTS) THEN
C ---   write error to log file
        WRITE (LOGF,92) ENVSTR//FILNAM
 92     FORMAT ('SWAP can not find the input file',/,A)
        STOP 'The .CRP file was not found: SWAP stopped !'
      ENDIF

C --- open file with crop data
      CALL FINDUNIT (10,CRP)
      OPEN (CRP,FILE=rmldsp(ENVSTR//FILNAM),STATUS='OLD',
     & access='sequential')

C --- phenology
      CALL RSINTR (CRP,FILNAM,LOGF,'IDEV',1,2,IDEV)
      IF (IDEV.EQ.1) then
        CALL RSINTR (CRP,FILNAM,LOGF,'LCC',1,366,LCC)
        CALL JMPLBL (CRP,FILNAM,LOGF,'KDIF')
      ELSEIF (IDEV.EQ.2) then
        CALL JMPLBL (CRP,FILNAM,LOGF,'TSUMEA')
        CALL RSREAR (CRP,FILNAM,LOGF,'TSUMEA',0.0,10000.0,TSUMEA)
        CALL RSREAR (CRP,FILNAM,LOGF,'TSUMAM',0.0,10000.0,TSUMAM)
        CALL RSREAR (CRP,FILNAM,LOGF,'TBASE',-10.0, 20.0,TBASE)
      ENDIF

C --- assimilation                        
      CALL RSREAR (CRP,FILNAM,LOGF,'KDIF',0.0,2.0,KDIF)
      CALL RSREAR (CRP,FILNAM,LOGF,'KDIR',0.0,2.0,KDIR) 
     
C --- LAI or soil cover fraction 
      CALL RSINTR (CRP,FILNAM,LOGF,'SWGC',1,2,SWGC)
      IF (SWGC.EQ.1) then
        CALL RAREAR (CRP,FILNAM,LOGF,'GCTB',0.0,12.0,GCTB,72,IFND)
      ELSEIF (SWGC.EQ.2) then
        CALL RAREAR (CRP,FILNAM,LOGF,'GCTB',0.0,2.0,GCTB,72,IFND)
      ENDIF

C --- Crop factor or crop height
      CALL RSINTR (CRP,FILNAM,LOGF,'SWCF',1,2,SWCF)
      IF (SWCF.EQ.1) then
        CALL RAREAR (CRP,FILNAM,LOGF,'CFTB',0.0,2.01,CFTB,72,IFND)
      ELSEIF (SWCF.EQ.2) then
        CALL RAREAR (CRP,FILNAM,LOGF,'CFTB',0.0,1000.0,CFTB,72,IFND)
      ENDIF

C --- rooting depth
      CALL RAREAR (CRP,FILNAM,LOGF,'RDTB',0.0,1000.0,RDTB,72,IFND)

C --- yield response
      CALL RAREAR (CRP,FILNAM,LOGF,'KYTB',0.0,5.0,KYTB,72,IFND)

C --- water use
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM1' ,-100.0,100.0,HLIM1)
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM2U',-1000.0,100.0,HLIM2U)
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM2L',-1000.0,100.0,HLIM2L)
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM3H',-10000.0,100.0,HLIM3H)
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM3L',-10000.0,100.0,HLIM3L)
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM4' ,-16000.0,100.0,HLIM4)
      CALL RSREAR (CRP,FILNAM,LOGF,'RSC',0.0,1000.0,RSC)
      CALL RSREAR (CRP,FILNAM,LOGF,'ADCRH',0.0,5.0,ADCRH)
      CALL RSREAR (CRP,FILNAM,LOGF,'ADCRL',0.0,5.0,ADCRL)
      CALL RSREAR (CRP,FILNAM,LOGF,'ECMAX',0.0,20.0,ECMAX)
      CALL RSREAR (CRP,FILNAM,LOGF,'ECSLOP',0.0,40.0,ECSLOP)
      CALL RSREAR (CRP,FILNAM,LOGF,'COFAB',0.0,1.0,COFAB)

C --- read table with root distribution coefficients
      CALL RAREAR (CRP,FILNAM,LOGF,'RDCTB',0.0,100.0,RDCTB,22,IFND)

C --- normalize RDCTB
      SUM = 0.0
      DO 96 X = 0.05,1.0,0.1
        VALUE = AFGEN (RDCTB,22,X)
        SUM = SUM+0.1*VALUE
96    CONTINUE

      RFAC = 1/SUM
      DO 98 I = 1,IFND/2
98    RDCTB(I*2) = RDCTB(I*2)*RFAC

C --- close file with crop data
      CLOSE (CRP)

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RDDRB (DRBFIL,ENVSTR,BAYRD,BAYRY,DRAMET,
     &IPOS,BASEGW,KHTOP,KHBOT,KVTOP,KVBOT,ZINTF,L,WETPER,ZBOTDR,ENTRES,
     &GEOFAC,NRLEVS,DRARES,INFRES,SWALLO,SWDTYP,OWLTAB,QDRTAB,LOGF,FMAY,
     &SWDIVD)
C ----------------------------------------------------------------------
C     Date               : 17/4/98                        
C     Purpose            : reading drainage parameters    
C                          for one agricultural year;  
C     Subroutines called : DATONR,SHIFTL,SHIFTR  
C     Functions called   : FROMTO                                      
C     File usage         : DRBFIL, file containing drainage data
C ----------------------------------------------------------------------
      IMPLICIT NONE
	INCLUDE 'PARAM.FI' 

      INTEGER   SWALLO(5),SWDTYP(5),FROMTO,BAYRD,BAYRY,FMAY
      INTEGER   DRAMET,DRB,NR,IPOS,NRLEVS,LOGF,SWDIVD

      REAL      L(5),ZBOTDR(5),OWLTAB(5,2*MAOWL),DRARES(5),INFRES(5)
      REAL      QDRTAB(50)
      REAL      BASEGW(2),WETPER(5),KHTOP,KHBOT,KVTOP,KVBOT
      REAL      ZINTF,ENTRES,GEOFAC

      CHARACTER DRBFIL*8,ENVSTR*50,FILNAM*12
C ----------------------------------------------------------------------
C --- local
      INTEGER  dd(MAOWL),mm(MAOWL),yy(MAOWL),IFND,I

      REAL     level(MAOWL),q(25),gwl(25)

      CHARACTER LINE*80

      character*80 rmldsp
      
      LOGICAL COMMENT,BLANK,EXISTS
C ----------------------------------------------------------------------
C --- compose filename
      CALL SHIFTR (DRBFIL)
      FILNAM = DRBFIL//'.DRB'
      CALL SHIFTL (FILNAM)
      CALL SHIFTR (ENVSTR)

C --- check if a file with basic drainage data does exist
      INQUIRE (FILE=rmldsp(ENVSTR//FILNAM),EXIST=EXISTS)

      IF (.NOT.EXISTS) THEN
C ---   write error to log file
        WRITE (LOGF,92) ENVSTR//FILNAM
 92     FORMAT ('SWAP can not find the input file',/,A)
        STOP 'The .DRB file was not found: SWAP stopped !'
      ENDIF

C --- open file with drainage data
      CALL FINDUNIT (12,DRB)
      OPEN (DRB,FILE=rmldsp(ENVSTR//FILNAM),status='old'
     & ,access='sequential')

C --- method to establish drainage/infiltration fluxes
      CALL RSINTR (DRB,FILNAM,LOGF,'DRAMET',1,3,DRAMET) 
      IF (dramet.ne.3) NRLEVS = 1

      IF (DRAMET.EQ.1) THEN
	  
	  CALL JMPLBL (DRB,FILNAM,LOGF,'LM1')
        CALL RSREAR (DRB,FILNAM,LOGF,'LM1',1.0,1000.,L(1))
        L(1) = 100.0*L(1)
        IFND = 0
4       READ (DRB,'(A)') LINE
        CALL ANALIN (LINE,BLANK,COMMENT)
        IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 4
        IF (COMMENT) GOTO 5
        IFND = IFND+1
        BACKSPACE (DRB)
        READ (DRB,*) gwl(IFND),q(IFND)
        GOTO 4
C ---   ready...
5       CONTINUE

        DO 7 I = 1,50
7       QDRTAB(I) = 0.0
        DO 9 I = 1,IFND
          QDRTAB(I*2-1) = ABS(gwl(I))
          QDRTAB(I*2)   = q(I)
9       CONTINUE

        CLOSE (DRB) 
        RETURN

      ELSEIF (DRAMET.EQ.2) THEN
   
        CALL JMPLBL (DRB,FILNAM,LOGF,'IPOS')

C ---   read profile characteristics
        CALL RSINTR (DRB,FILNAM,LOGF,'IPOS',1,5,IPOS)
        CALL RSREAR (DRB,FILNAM,LOGF,'BASEGW',-1.E4,0.0,BASEGW(1))
        CALL RSREAR (DRB,FILNAM,LOGF,'KHTOP',0.0,1000.0,KHTOP)

        IF (IPOS.GE.3) THEN
          CALL RSREAR (DRB,FILNAM,LOGF,'KHBOT',0.0,1000.0,KHBOT)
        ELSE
          CALL JMPLBL (DRB,FILNAM,LOGF,'KVTOP')
        ENDIF
        IF (IPOS.GE.4) THEN
          CALL RSREAR (DRB,FILNAM,LOGF,'KVTOP',0.0,1000.0,KVTOP)
          CALL RSREAR (DRB,FILNAM,LOGF,'KVBOT',0.0,1000.0,KVBOT)  
        ELSE
          CALL JMPLBL (DRB,FILNAM,LOGF,'GEOFAC')
        ENDIF
        IF (IPOS.EQ.5) THEN
          CALL RSREAR (DRB,FILNAM,LOGF,'GEOFAC',0.0,100.0,GEOFAC)
        ELSE
          CALL JMPLBL (DRB,FILNAM,LOGF,'ZINTF')
        ENDIF
        IF (IPOS.GE.3) THEN
          CALL RSREAR (DRB,FILNAM,LOGF,'ZINTF',-1.E4,0.0,ZINTF)
        ELSE
          CALL JMPLBL (DRB,FILNAM,LOGF,'LM2')
        ENDIF

C ---   read drain characteristics
        CALL RSREAR (DRB,FILNAM,LOGF,'LM2',1.0,1000.,L(1))
        L(1) = 100.0*L(1)
        CALL RSREAR (DRB,FILNAM,LOGF,'WETPER',0.0,1000.0,WETPER(1))
        CALL RSREAR (DRB,FILNAM,LOGF,'ZBOTDR',-1000.0,0.0,ZBOTDR(1))
        CALL RSREAR (DRB,FILNAM,LOGF,'ENTRES',0.0,1000.0,ENTRES)

        CLOSE (DRB)
        RETURN

      ELSEIF (DRAMET.EQ.3) THEN
   
        CALL JMPLBL (DRB,FILNAM,LOGF,'NRLEVS')
        CALL RSINTR (DRB,FILNAM,LOGF,'NRLEVS',1,5,NRLEVS)

        IF (NRLEVS.GE.1) THEN
          CALL JMPLBL (DRB,FILNAM,LOGF,'DRARES1')
          CALL RSREAR (DRB,FILNAM,LOGF,'DRARES1',10.0,1.0E5,DRARES(1))
          CALL RSREAR (DRB,FILNAM,LOGF,'INFRES1',0.0,1.0E5,INFRES(1))
          CALL RSINTR (DRB,FILNAM,LOGF,'SWALLO1',1,3,SWALLO(1))
          IF (SWDIVD .EQ. 1) CALL RSREAR (DRB,FILNAM,LOGF,'L1',1.0,
     &    1000.,L(1))
          L(1) = 100.0*L(1)
          CALL JMPLBL (DRB,FILNAM,LOGF,'ZBOTDR1')           
          CALL RSREAR (DRB,FILNAM,LOGF,'ZBOTDR1',-1000.0,0.0,ZBOTDR(1))
          CALL RSINTR (DRB,FILNAM,LOGF,'SWDTYP1',1,2,SWDTYP(1))
          IF (SWDTYP(1).EQ.2) then
C ---       position file pointer
            READ (DRB,'(2X)')
            IFND = 0
14          READ (DRB,'(A)') LINE
            CALL ANALIN (LINE,BLANK,COMMENT)
            IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 14
            IF (COMMENT) GOTO 15
            IFND = IFND+1
            BACKSPACE (DRB)
            READ (DRB,*) dd(IFND),mm(IFND),level(IFND)
            GOTO 14
C ---       ready...
15          CONTINUE
C ---       year is calculated
            DO 16 I = 1,IFND 
              if (mm(I).GE.FMAY) yy(I) = BAYRY
              if (mm(I).LT.FMAY) yy(I) = BAYRY+1
              CALL DATONR (yy(I),mm(I),dd(I),nr)
              OWLTAB(1,I*2)   = -ABS(LEVEL(I))
              OWLTAB(1,I*2-1) = FROMTO (BAYRD,BAYRY,NR,YY(I))+1
16          CONTINUE
          ENDIF
        ENDIF 

        IF (NRLEVS.GE.2) THEN
          CALL JMPLBL (DRB,FILNAM,LOGF,'DRARES2')
          CALL RSREAR (DRB,FILNAM,LOGF,'DRARES2',10.0,1.0E5,DRARES(2))
          CALL RSREAR (DRB,FILNAM,LOGF,'INFRES2',0.0,1.0E5,INFRES(2))
          CALL RSINTR (DRB,FILNAM,LOGF,'SWALLO2',1,3,SWALLO(2))
          IF (SWDIVD .EQ. 1) CALL RSREAR (DRB,FILNAM,LOGF,'L2',1.0,
     &    1000.,L(2))
          L(2) = 100.0*L(2)
          CALL JMPLBL (DRB,FILNAM,LOGF,'ZBOTDR2')           
          CALL RSREAR (DRB,FILNAM,LOGF,'ZBOTDR2',-1000.0,0.0,ZBOTDR(2))
          CALL RSINTR (DRB,FILNAM,LOGF,'SWDTYP2',1,2,SWDTYP(2))
          IF (SWDTYP(2).EQ.2) THEN
            READ (DRB,'(2X)')	      
            IFND = 0
24          READ (DRB,'(A)') LINE
            CALL ANALIN (LINE,BLANK,COMMENT)
            IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 24
            IF (COMMENT) GOTO 25
            IFND = IFND+1
            BACKSPACE (DRB)
            READ (DRB,*) dd(IFND),mm(IFND),level(IFND)
            GOTO 24
C ---       ready...
25          CONTINUE
C ---       year is calculated
            DO 26 I = 1,IFND 
              if (mm(I).GE.FMAY) yy(I) = BAYRY
              if (mm(I).LT.FMAY) yy(I) = BAYRY+1
              CALL DATONR (yy(I),mm(I),dd(I),nr)
              OWLTAB(2,I*2)   = -ABS(LEVEL(I))
              OWLTAB(2,I*2-1) = FROMTO (BAYRD,BAYRY,NR,YY(I))+1
26          CONTINUE
          ENDIF
        ENDIF 

        IF (NRLEVS.GE.3) THEN
          CALL JMPLBL (DRB,FILNAM,LOGF,'DRARES3')
          CALL RSREAR (DRB,FILNAM,LOGF,'DRARES3',10.0,1.0E5,DRARES(3))
          CALL RSREAR (DRB,FILNAM,LOGF,'INFRES3',0.0,1.0E5,INFRES(3))
          CALL RSINTR (DRB,FILNAM,LOGF,'SWALLO3',1,3,SWALLO(3))
          IF (SWDIVD .EQ. 1) CALL RSREAR (DRB,FILNAM,LOGF,'L3',1.0,
     &    1000.,L(3))
          L(3) = 100.0*L(3)
          CALL JMPLBL (DRB,FILNAM,LOGF,'ZBOTDR3')           
          CALL RSREAR (DRB,FILNAM,LOGF,'ZBOTDR3',-1000.0,0.0,ZBOTDR(3))
          CALL RSINTR (DRB,FILNAM,LOGF,'SWDTYP3',1,2,SWDTYP(3))
          IF (SWDTYP(3).EQ.2) then
            READ (DRB,'(2X)')
            IFND = 0
34          READ (DRB,'(A)') LINE
            CALL ANALIN (LINE,BLANK,COMMENT)
            IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 34
            IF (COMMENT) GOTO 35
            IFND = IFND+1
            BACKSPACE (DRB)
            READ (DRB,*) dd(IFND),mm(IFND),level(IFND)
            GOTO 34
C ---       ready...
35          CONTINUE
C ---       year is calculated
            DO 36 I = 1,IFND 
              if (mm(I).GE.FMAY) yy(I) = BAYRY
              if (mm(I).LT.FMAY) yy(I) = BAYRY+1
              CALL DATONR (yy(I),mm(I),dd(I),nr)
              OWLTAB(3,I*2)   = -ABS(LEVEL(I))
              OWLTAB(3,I*2-1) = FROMTO (BAYRD,BAYRY,NR,YY(I))+1
36          CONTINUE
          ENDIF
        ENDIF 

        IF (NRLEVS.GE.4) THEN
          CALL JMPLBL (DRB,FILNAM,LOGF,'DRARES4')
          CALL RSREAR (DRB,FILNAM,LOGF,'DRARES4',10.0,1.0E5,DRARES(4))
          CALL RSREAR (DRB,FILNAM,LOGF,'INFRES4',0.0,1.0E5,INFRES(4))
          CALL RSINTR (DRB,FILNAM,LOGF,'SWALLO4',1,3,SWALLO(4))
          IF (SWDIVD .EQ. 1) CALL RSREAR (DRB,FILNAM,LOGF,'L4',1.0,
     &    1000.,L(4))
          L(4) = 100.0*L(4)
          CALL JMPLBL (DRB,FILNAM,LOGF,'ZBOTDR4')           
          CALL RSREAR (DRB,FILNAM,LOGF,'ZBOTDR4',-1000.0,0.0,ZBOTDR(4))
          CALL RSINTR (DRB,FILNAM,LOGF,'SWDTYP4',1,2,SWDTYP(4))
          IF (SWDTYP(4).EQ.2) then
            READ (DRB,'(2X)')
            IFND = 0
44          READ (DRB,'(A)') LINE
            CALL ANALIN (LINE,BLANK,COMMENT)
            IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 44
            IF (COMMENT) GOTO 45
            IFND = IFND+1
            BACKSPACE (DRB)
            READ (DRB,*) dd(IFND),mm(IFND),level(IFND)
            GOTO 44
C ---       ready...
45          CONTINUE
C ---       year is calculated
            DO 46 I = 1,IFND 
              if (mm(I).GE.FMAY) yy(I) = BAYRY
              if (mm(I).LT.FMAY) yy(I) = BAYRY+1
              CALL DATONR (yy(I),mm(I),dd(I),nr)
              OWLTAB(4,I*2)   = -ABS(LEVEL(I))
              OWLTAB(4,I*2-1) = FROMTO (BAYRD,BAYRY,NR,YY(I))+1
46          CONTINUE
          ENDIF
        ENDIF 

        IF (NRLEVS.GE.5) THEN
          CALL JMPLBL (DRB,FILNAM,LOGF,'DRARES5')
          CALL RSREAR (DRB,FILNAM,LOGF,'DRARES5',10.0,1.0E5,DRARES(5))
          CALL RSREAR (DRB,FILNAM,LOGF,'INFRES5',0.0,1.0E5,INFRES(5))
          CALL RSINTR (DRB,FILNAM,LOGF,'SWALLO5',1,3,SWALLO(5))
          IF (SWDIVD .EQ. 1) CALL RSREAR (DRB,FILNAM,LOGF,'L5',1.0,
     &    1000.,L(5))
          L(5) = 100.0*L(5)
          CALL JMPLBL (DRB,FILNAM,LOGF,'ZBOTDR5')           
          CALL RSREAR (DRB,FILNAM,LOGF,'ZBOTDR5',-1000.0,0.0,ZBOTDR(5))
          CALL RSINTR (DRB,FILNAM,LOGF,'SWDTYP5',1,2,SWDTYP(5))
          IF (SWDTYP(5).EQ.2) then
            READ (DRB,'(2X)')
            IFND = 0
54          READ (DRB,'(A)') LINE
            CALL ANALIN (LINE,BLANK,COMMENT)
            IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 54
            IF (COMMENT) GOTO 55
            IFND = IFND+1
            BACKSPACE (DRB)
            READ (DRB,*) dd(IFND),mm(IFND),level(IFND)
            GOTO 54
C ---       ready...
55          CONTINUE
C ---       year is calculated
            DO 56 I = 1,IFND 
              if (mm(I).GE.FMAY) yy(I) = BAYRY
              if (mm(I).LT.FMAY) yy(I) = BAYRY+1
              CALL DATONR (yy(I),mm(I),dd(I),nr)
              OWLTAB(5,I*2)   = -ABS(LEVEL(I))
              OWLTAB(5,I*2-1) = FROMTO (BAYRD,BAYRY,NR,YY(I))+1
56          CONTINUE
          ENDIF
        ENDIF 
      ENDIF 

C --- close file with drainage data
      CLOSE (DRB)         

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RDDRE (SRFFIL,ENVSTR,RSRO,NRSRF,NRPRI,NRSEC,L,
     & ZBOTDR,WIDTHR,TALUDR,RDRAIN,RINFI,RENTRY,REXIT,GWLINF,SWDTYP,
     & WLPTAB,BAYRD,BAYRY,SWSEC,WLS,OSSWLM,NMPER,WLSTAR,IMPEND,SWMAN,
     & WSCAP,SWQHR,HBWEIR,ALPHAW,BETAW,NQH,HQHTAB,QQHTAB,DROPR,WLSMAN,
     & GWLCRIT,WLSTAB,STTAB,WSTINI,WST,T,WLSBAK,SWSRF,NPHASE,HCRIT,
     & HDEPTH,VCRIT,WLP,NODHD,NUMNOD,DZ,WLDIP,NUMADJ,LOGF,FMAY,INTWL)
C ----------------------------------------------------------------------
C     Date               : 02/06/98                       
C     Purpose            : reading multilevel drainage characteristics 
C                          and specification of the surface water system
C                          for a period up to one year;  

C --- 1 Reading .DRE input file
C --- 2 Initializations

C --- Initializations:
C -1- wlp: water level in primary system   (SWSRF = 3)
C -2- wls: water level in secondary system (SWSRF = 2 or 3, SWSEC = 1 or 2) 
C -3- HBWEIR(IMPER) in case of table discharge relation (SWQHR = 2)
C -4- NUMADJ: number of target level adjustments
C -5- sttab(22,2) table with storage as a function of water level
C ---    sttab(i,1) contains levels:
C ---    i=1: +100 cm; i=2: 0 cm; i=22: bottom of deepest dr. medium
C ---    sttab(i,2) contains storage expressed as surface layer 

C     Subroutines called :  
C     Functions called   :                               
C     File usage         : DREFIL, file containing drainage data
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'
C --- global
      INTEGER   NRPRI,NRSEC,NRSRF,SWDTYP(5),NMPER,SWMAN(10),IMPEND(10)
      INTEGER   SWQHR,NQH(10),BAYRD,BAYRY,SWSEC,SWSRF,NPHASE(10)
      INTEGER   NODHD(10),NUMNOD,NUMADJ,LOGF,FMAY,INTWL(10)

      REAL      L(5),ZBOTDR(5),WIDTHR(5),TALUDR(5),RDRAIN(5)
      REAL      RINFI(5),RENTRY(5),REXIT(5),GWLINF(5),WLPTAB(2*MAWLP)
      REAL      RSRO
      REAL      WLS,OSSWLM,WLSTAR,WSCAP(10),HBWEIR(10),ALPHAW(10)
      REAL      BETAW(10),HQHTAB(10,10),QQHTAB(10,10),DROPR(10)
      REAL      WLSMAN(10,10),WLSTAB(2*MAWLS),STTAB(22,2),T,HDEPTH(10)
      REAL      WSTINI,WST,WLSBAK(4),HCRIT(10,10),VCRIT(10,10)
      REAL      AFGEN,WLP,DZ(MACP),GWLCRIT(10,10),WLDIP(10)

      CHARACTER SRFFIL*8,ENVSTR*50

C ----------------------------------------------------------------------
C --- local
      INTEGER   DRE,level,D,M,Y,NR,FROMTO,ITAB,I
      INTEGER   iph,NRMAN1,NRMAN2,NODE,IMPER,IMPERB,IMPERI,IFND
   
      REAL      VALUE,wdepth,wbreadth,wvolum,DEP,WSTLEV,SOFCU,ALTCU

      LOGICAL   FLWEIR(10),EXISTS(10),FLZERO(10),BLANK,COMMENT

      CHARACTER FILNAM*12,LINE*80

      character*80 rmldsp

C ----------------------------------------------------------------------
C --- compose filename
      CALL SHIFTR (SRFFIL)
      FILNAM = SRFFIL//'.DRE'
      CALL SHIFTL (FILNAM)
      CALL SHIFTR (ENVSTR)

C --- open file with drainage data
      CALL Findunit (10,DRE)
      OPEN (DRE,FILE =rmldsp(ENVSTR//FILNAM),STATUS='OLD',
     & ACCESS = 'SEQUENTIAL')

C --- altitude of control unit (relative to reference level)
      CALL RSREAR (DRE,FILNAM,LOGF,'ALTCU',-300000.0,300000.0,ALTCU)

C --- section 1

C --- drainage resistance of surface runoff
      CALL RSREAR (DRE,FILNAM,LOGF,'RSRO',0.001,1.0,RSRO)

C --- number of drainage levels
      CALL RSINTR (DRE,FILNAM,LOGF,'NRSRF',1,5,NRSRF)

C --- characteristics of each drainage level 
      IFND = 0
4     READ (DRE,'(A)') LINE
      CALL ANALIN (LINE,BLANK,COMMENT)
      IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 4
      IF (COMMENT) GOTO 6 
        IFND = IFND+1
        BACKSPACE (DRE)
        READ (DRE,*) level, swdtyp(level)
        BackSpace (DRE)
        If (swdtyp(level) .EQ.0 ) then
C ---     open      
          READ (DRE,*) level,swdtyp(level),l(level),zbotdr(level),
     &      gwlinf(level),rdrain(level),rinfi(level),rentry(level),
     &      rexit(level),widthr(level),taludr(level)
        else
C ---     closed 
          READ (DRE,*) level,swdtyp(level),l(level),zbotdr(level),
     &      gwlinf(level),rdrain(level),rinfi(level)

        endif
        if (level.ne.IFND) stop 'RDDRE: dr. level index not consistent' 
C ---   necessairy conversions
        l(level)      = l(level)*100.0
        ZBOTDR(level) = ZBOTDR(level) -ALTCU
C ---   some security checks....
C ---   1 - levels must be ordered, starting with the deepest
C ---   2 - zbotdr always below surface level
C ---   3 - gwlinf must be below bottom of deepest drainage medium
        if (level .gt. 1) then
          if (zbotdr(level) .lt. zbotdr(level-1))
     &    stop 'RDDRE: levels must be ordered, starting with deepest'
        endif
        if (zbotdr(level).gt.0.0)
     &    stop 'RDDRE: zbotdr must be negative'
        if (gwlinf(level).gt.zbotdr(level))
     &    stop 'RDDRE: gwlinf higher than zbotdr'

C ---   next record...
        GOTO 4
6     CONTINUE
      IF (IFND.NE. NRSRF)
     &  stop 'RDDRE: incorrect number of drainage levels described'

C --- section 2a

      CALL RSINTR (DRE,FILNAM,LOGF,'SWSRF',1,3,SWSRF)
      IF (SWSRF.EQ.3) THEN
        NRPRI = 1
        NRSEC = NRSRF-NRPRI
      ELSEIF (SWSRF.EQ.2) THEN
        NRPRI = 0
        NRSEC = NRSRF-NRPRI
      ELSEIF (SWSRF.EQ.1) THEN
C ---   no surface water system...ready
        Close (DRE)
        Return
      ENDIF
C --- is dit wel goed ?
      IF (NRSEC.LT.1) STOP 'RDDRE - secondary system not specified'

      If (SWDTYP(1+NRPRI).NE.0)
     &  STOP 'RDDRE - Deepest sec. level must be open'

C --- section 2b

C --- read table with water levels in the primary system (SWSRF=3)
      IF (SWSRF.EQ.3) THEN
C ---   init table
        DO 8 I = 1,2*MAWLP
8       WLPTAB(I) = 0.0
C ---   position file pointer
        IFND = 0
12      READ (DRE,'(A)') LINE
        CALL ANALIN (LINE,BLANK,COMMENT)
        IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 12
        IF (COMMENT) GOTO 14 
          IFND = IFND+1
          BACKSPACE (DRE)
          READ (DRE,*) D,M,VALUE
C ---     calculate year 
          IF (M.GE.FMAY) Y = BAYRY
          IF (M.LT.FMAY) Y = BAYRY+1
          CALL DATONR (Y,M,D,NR)
          IF (IFND.GT.MAWLP) STOP 'RDDRE - WLPTAB too large'
          WLPTAB(IFND*2) = VALUE -ALTCU
          if (VALUE.gt.0.0) 
     &      STOP 'RDDRE: water level in primary system must be negative'
          WLPTAB(IFND*2-1) = FROMTO (BAYRD,BAYRY,NR,Y)+1
C ---     next record...
          GOTO 12
14      CONTINUE
C ---   set initial value
        wlp = AFGEN (WLPTAB,2*MAWLP,T+1.0)

C ---   Ready in case of only a primary system
C       if (NRSEC.LT.1) then
C          CLOSE(DRE)
C          Return
C       endif 

      ELSE
        CALL JMPLBL (DRE,FILNAM,LOGF,'SWSEC')
      ENDIF

C --- Section 2c

      CALL RSINTR (DRE,FILNAM,LOGF,'SWSEC',1,2,SWSEC)

C --- Section 3

      IF (SWSEC.EQ.1) THEN
C ---   surface water level of secondary system is input
C ---   position file pointer
510     READ (DRE,'(A)') LINE
        CALL ANALIN (LINE,BLANK,COMMENT)
        IF (BLANK.OR.COMMENT) GOTO 510  
        BACKSPACE (DRE)

C ---   init table
        DO 60 I = 1,2*MAWLS
60      WLSTAB(I) = 0.0

        IFND = 0
512     READ (DRE,'(A)') LINE
        CALL ANALIN (LINE,BLANK,COMMENT)
        IF (BLANK) GOTO 512
        IF (COMMENT) GOTO 514 

          IFND = IFND+1
          BACKSPACE (DRE)
          READ (DRE,*) D,M,VALUE
C ---     calculate year 
          IF (M.GE.FMAY) Y = BAYRY
          IF (M.LT.FMAY) Y = BAYRY+1
          CALL DATONR (Y,M,D,NR)
          IF (IFND.GT.MAWLS) STOP 'RDDRE - WLSTAB too large'
          WLSTAB(IFND*2)   = VALUE - ALTCU
          WLSTAB(IFND*2-1) = FROMTO (BAYRD,BAYRY,NR,Y)+1
          GOTO 512
514     CONTINUE
C ---   set initial value
        wls = AFGEN (WLSTAB,2*MAWLS,T+1.0)

C ---   Section 4a

C --- surface water level of secondary system is simulated
      ELSEIF (SWSEC.EQ.2) THEN
        CALL JMPLBL (DRE,FILNAM,LOGF,'WLACT')
        CALL RSREAR (DRE,FILNAM,LOGF,'WLACT',zbotdr(1+NRPRI)+ALTCU,
     &       ALTCU,wls)
        WLS = WLS - ALTCU
        CALL RSREAR (DRE,FILNAM,LOGF,'OSSWLM',0.0,10.0,osswlm)

C ---   Section 4b

        CALL RSINTR (DRE,FILNAM,LOGF,'NMPER',1,10,nmper)
        wlstar = wls
        NRMAN1 = 0
        NRMAN2 = 0

C ---   position file pointer
16      READ (DRE,'(A)') LINE
        CALL ANALIN (LINE,BLANK,COMMENT)
        IF (BLANK.OR.COMMENT) GOTO 16 
        BACKSPACE (DRE)

18      READ (DRE,'(A)') LINE
        CALL ANALIN (LINE,BLANK,COMMENT)
        IF (BLANK) GOTO 18
        IF (COMMENT) GOTO 20 

          BACKSPACE (DRE)
          READ (DRE,*) imper,D,M,swman(imper),wscap(imper),wldip(imper),
     &       intwl(imper)
          if (swman(imper).eq.2 .and. intwl(imper).lt.1) then
            STOP 'RDDRE: INTWL (management interval) must be >= 1 day'
          endif
          wldip(imper) = abs(wldip(imper))

C ---     for each type of management: count number of periods 
          if (swman(imper).eq.1) then 
            NRMAN1 = NRMAN1+1
          elseif (swman(imper).eq.2) then
            NRMAN2 = NRMAN2+1
          else
            STOP 'RDDRE: SWMAN out of range'
          endif

C ---     calculate year 
          IF (M.GE.FMAY) Y = BAYRY
          IF (M.LT.FMAY) Y = BAYRY+1
          CALL DATONR (Y,M,D,NR)
          impend(imper) = FROMTO (BAYRD,BAYRY,NR,Y)+1

C ---   next record...
        GOTO 18
20      IF ((NRMAN1+NRMAN2).NE.NMPER)
     &  STOP 'RDDRE: NRMAN1+NRMAN2 does not match NMPER'

C ---   type of discharge relationship
        CALL RSINTR (DRE,FILNAM,LOGF,'SWQHR',1,2,SWQHR)

        IF (SWQHR.EQ.1) THEN

C ---     Section 4c

          CALL RSREAR (DRE,FILNAM,LOGF,'SOFCU',0.1 ,100000.0,SOFCU)

C ---     position file pointer
22        READ (DRE,'(A)') LINE
          CALL ANALIN (LINE,BLANK,COMMENT)
          IF (BLANK.OR.COMMENT) GOTO 22 
          BACKSPACE (DRE)

          IMPERB = 0
          IMPERI = 0

24        READ (DRE,'(A)') LINE
          CALL ANALIN (LINE,BLANK,COMMENT)
          IF (BLANK) GOTO 24
          IF (COMMENT) GOTO 26 

            BACKSPACE (DRE)
            READ (DRE,*) imper,hbweir(imper),alphaw(imper),betaw(imper)
            hbweir(imper)= hbweir(imper)-ALTCU
C ---       correction for units
            alphaw(imper) = alphaw(imper)*(8.64*100**(1.0-betaw(imper))
     &                      /SOFCU)     
            if (hbweir(imper).lt.zbotdr(1+NRPRI)) then
              write(6,*) 'RDDRE - weir crest level below bottom of'
              write(6,*) 'deepest channel of secondary system'
              stop
            endif
c --- check for target level above channel bottom when supply is 
c --- attempted (system may never become dry in this case)
            if (swman(imper).eq.1 .and. wscap(imper).gt.1.e-7 .and.
     &         (hbweir(imper)-wldip(imper)).lt.
     &         (zbotdr(1+NRPRI)+1.e-4)) then
              STOP 'RDDRE: HBWEIR/WLDIP supply not possible =< zbotdr !'
            endif

            IF (imper.ne.imperb) then
              imperb = imper
              imperi = imperi + 1
            ELSE
              STOP 'RDDRE: 4c IMPER not unique'
            ENDIF
C ---     next record
          GOTO 24

C ---     check number of records.. 
26        IF (IMPERI.NE.NMPER)
     &    STOP 'INISRF: section 4c - not enough records'

        ELSEIF (SWQHR.EQ.2) THEN

C ---     Section 4d

          CALL JMPLBL (DRE,FILNAM,LOGF,'LABEL4d')
          CALL RSINTR (DRE,FILNAM,LOGF,'LABEL4d',0,10,I)

C ---     position file pointer
28        READ (DRE,'(A)') LINE
          CALL ANALIN (LINE,BLANK,COMMENT)
          IF (BLANK.OR.COMMENT) GOTO 28 
          BACKSPACE (DRE)

          IMPERB = 0
          IMPERI = 0

30        READ (DRE,'(A)') LINE
          CALL ANALIN (LINE,BLANK,COMMENT)
          IF (BLANK) GOTO 30
          IF (COMMENT) GOTO 32 

            DO 34 IMPER = 1,10
              NQH (IMPER)    = 0
              FLWEIR (IMPER) = .FALSE.
              EXISTS (IMPER) = .FALSE.
              FLZERO (IMPER) = .FALSE.
34          CONTINUE

            BACKSPACE (DRE)
            READ (DRE,*) IMPER,ITAB,HQHTAB(IMPER,ITAB),
     &        QQHTAB(IMPER,ITAB)
            NQH(IMPER) = NQH(IMPER)+1
            EXISTS(IMPER) = .TRUE.
            IF (QQHTAB(IMPER,ITAB).LT.0.000001) FLZERO(IMPER)=.TRUE.
            if (hqhtab(imper,itab).lt.zbotdr(1+NRPRI)) then
              write(6,*) 'RDDRE - level in q-h table below bottom of '
              write(6,*) 'deepest channel of secondary system'
              stop
            endif
            IF (imper.ne.imperb) then
              imperb = imper
              imperi = imperi + 1
            ENDIF

C ---       establish HBWEIR (at level where QTAB = 0) 
            if (QQHTAB(IMPER,ITAB).LT.0.0001.AND..NOT.FLWEIR(IMPER)) 
     &      THEN
              HBWEIR(IMPER) = HQHTAB(IMPER,ITAB)
              FLWEIR(IMPER) = .TRUE.
            ENDIF 

C ---       consistency checks
            if (NQH(IMPER).NE.ITAB)
     &        STOP 'RDDRE: QH-table / IMPER - ITAB mismatch'
            if (ITAB.EQ.1) THEN
            if (ABS(HQHTAB(IMPER,ITAB)-100.0).GT.0.00001)
     &        STOP 'RDDRE: first value in HTAB should be 100.0'
            endif
            if (ITAB.GT.1) THEN
              if ((HQHTAB(IMPER,ITAB).GE.HQHTAB(IMPER,ITAB-1)).OR.
     &           (QQHTAB(IMPER,ITAB).GT.QQHTAB(IMPER,ITAB-1)))
     &          STOP 'RDDRE: QH-table - no descending values'
            endif

C ---       next record
            GOTO 30

C ---     check number of periods.. 
32        IF (IMPERI.NE.NMPER)
     &    STOP 'RDDRE: section 4d - number of periods incorrect'

C ---     check that QQHTAB goes down to zero
          DO 36 imper = 1,10
            IF (EXISTS(IMPER).AND..NOT.FLZERO(IMPER))
     &      STOP 'RDDRE: QQHTAB not going down to zero'
36         CONTINUE

        ENDIF

C ---   position filepointer at 4e
        CALL JMPLBL (DRE,FILNAM,LOGF,'LABEL4e')
        CALL RSINTR (DRE,FILNAM,LOGF,'LABEL4e',0,10,I)

        IF (NRMAN2.GT.0) THEN

38        READ (DRE,'(A)') LINE
          CALL ANALIN (LINE,BLANK,COMMENT)
          IF (BLANK.OR.COMMENT) GOTO 38 
          BACKSPACE (DRE)

          IMPERB = 0
          IMPERI = 0

C ---     read table with drop rates 
40        READ (DRE,'(A)') LINE
          CALL ANALIN (LINE,BLANK,COMMENT)
          IF (BLANK) GOTO 40
          IF (COMMENT) GOTO 42 

            BACKSPACE (DRE)
            READ (DRE,*) imper,dropr(imper),hdepth(imper)
            hdepth(imper) = -abs(hdepth(imper))
C ---       determine compartment number related to hdepth
            DEP = 0.0
            DO 44 NODE = 1,NUMNOD
              NODHD(imper) = NODE
              DEP = DEP-DZ(NODE)
              IF (hdepth(imper).ge.DEP-1.0E-6) GOTO 46
44          CONTINUE
46          CONTINUE

            IF (SWMAN(imper) .NE. 2)
     &        STOP 'RDDRE: #4e swman - imper mismatch'
            IF (imper.ne.imperb) then
              imperb = imper
              imperi = imperi + 1
            ELSE
              STOP 'RDDRE: two drop rates same period'
            ENDIF
C ---     next record
          GOTO 40
42        IF (IMPERI .NE. NRMAN2)
     &    STOP 'RDDRE: #4e number of periods for drop rate incorrect'
 
48        READ (DRE,'(A)') LINE
          CALL ANALIN (LINE,BLANK,COMMENT)
          IF (BLANK.OR.COMMENT) GOTO 48 
          BACKSPACE (DRE)

          IMPERB = 0
          IMPERI = 0

          DO 54 IMPER = 1,10
54        NPHASE(IMPER) = 0

          IFND = 0
50        READ (DRE,'(A)') LINE
          CALL ANALIN (LINE,BLANK,COMMENT)
          IF (BLANK) GOTO 50
          IF (COMMENT) GOTO 52 

            BACKSPACE (DRE)
            READ (DRE,*) imper,iph,wlsman(imper,iph),
     &      gwlcrit(imper,iph),HCRIT(imper,iph),VCRIT(imper,iph)
            NPHASE(IMPER) = NPHASE(IMPER) + 1
            wlsman(imper,iph) = wlsman(imper,iph)-ALTCU
            if (wlsman(imper,iph).lt.zbotdr(1+NRPRI)) then
              write(6,*) 'RDDRE - level of automatic weir below bottom'
              write(6,*) 'of deepest channel of secondary system'
              stop
            endif
            IF (SWMAN(imper) .NE. 2)
     &      STOP 'RDDRE: #4e swman - imper mismatch'
            IF (imper.ne.imperb) then
              imperb = imper
              imperi = imperi + 1
            ENDIF

C ---     next record...
          GOTO 50
52        IF (IMPERI .NE. NRMAN2)
     &    STOP 'RDDRE: #4e number of periods incorrect'

C ---     consistency checks WLSMAN, GWLCRIT, HCRIT and VCRIT
          DO 446 imper = 1,nmper
            IF (SWMAN(imper).EQ.2) THEN
              if (abs(gwlcrit(imper,1)) .gt. 0.01) 
     &          STOP 'RDDRE: #4e - GWLCRIT(1) must be 0.'
              if (abs(vcrit(imper,1)) .gt. 0.01) 
     &          STOP 'RDDRE: #4e - VCRIT(1) must be 0.'
              if (abs(hcrit(imper,1)) .gt. 0.01) 
     &          STOP 'RDDRE: #4e - HCRIT(1) must be 0.'

              if (swman(imper).eq.2 .and. 
     &          hbweir(imper).gt. (wlsman(imper,1)-0.99999)) then
               STOP 'RDDRE: #4e - HBWEIR within 1 cm of wlsman(1)' 
              endif

              DO 448 iph = 2,nphase(imper)
                if (wlsman(imper,iph).LT.wlsman(imper,iph-1))
     &          STOP 'RDDRE: #4e - WLSMAN inconsistent'
                if (GWLCRIT(imper,iph).GT.GWLCRIT(imper,iph-1))
     &          STOP 'RDDRE: #4e - GWLCRIT inconsistent'
                if (HCRIT(imper,iph).GT.HCRIT(imper,iph-1))
     &          STOP 'RDDRE: #4e - HCRIT inconsistent'
                if (VCRIT(imper,iph).LT.VCRIT(imper,iph-1))
     &          STOP 'RDDRE: #4e - VCRIT inconsistent'
448           CONTINUE
            ENDIF 
446       CONTINUE
        ENDIF
      ENDIF
C ----------------------------------------------------------------------
C --- initialize counter for number of target level adjustments
      numadj = 0

C --- sttab(i,1) contains depths

C --- sw-levels, to be used in piece-wise linear functions (first level)
C --- is 100 cm above soil surface to allow for situations with ponding)
      sttab(1,1) = 100.0
      sttab(2,1) =   0.0
      do 100 i = 3,22
C ---   layer between surface level and deepest
C ---   drain/channel bottom is divided into 20 compartments
        sttab(i,1) = zbotdr(1+nrpri)*(i-2)/20.0
100   continue

C --- sttab(i,2) contains storage expressed in cm

C --- calculation of surface water storage (in cm, i.e. volume
C --- per unit area), as a function of sw-level, only for open channels:
      do 104 i = 1,22
        sttab(i,2) = 0.0
        do 108 level = 1+nrpri,nrsrf
          if (swdtyp(level).eq.0.and.sttab(i,1).gt.zbotdr(level)) then
C ---       for levels above soil surface the volume-increment is
C ---       computed for a rectangle, and not a trapezium
            if (sttab(i,1) .le. 0.0) then
              wdepth   = sttab(i,1)-zbotdr(level)
              wvolum   = wdepth*(widthr(level)+wdepth/taludr(level))
            else
              wdepth   = -zbotdr(level)
              wvolum   = wdepth*(widthr(level)+wdepth/taludr(level))
              wbreadth = widthr(level) + 2*wdepth/taludr(level)
              wdepth   = sttab(i,1)
              wvolum   = wvolum + wbreadth*wdepth
            endif
            sttab(i,2) = sttab(i,2)+wvolum/l(level)
          endif
108     continue
104   continue

C --- initial storage wstini
      wstini = wstlev (wls,sttab)
      wst = wstini
C --- initialize memorization of wls for most recent 4 timesteps 
      do 200 i=1,4
        wlsbak(i) = 0.0
 200  continue

C --- close input file with lateral boundary conditions
      CLOSE (DRE)         

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RDGRASS (CRPFIL,ENVSTR,TDWI,LAIEM,RGRLAI,SLATB,
     &  SSA,SPAN,TBASE,KDIF,KDIR,EFF,AMAXTB,TMPFTB,TMNFTB,CVL,CVR,CVS,
     &  Q10,RML,RMR,RMS,RFSETB,FRTB,FLTB,FSTB,PERDL,RDRRTB,
     &  RDRSTB,HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,HLIM4,RSC,ADCRH,
     &  ADCRL,ECMAX,ECSLOP,COFAB,RDI,RRI,RDC,RDCTB,LOGF)
C ----------------------------------------------------------------------
C     Date               : 14/1/99   
C     Purpose            : get crop parameters for grass     
C     Subroutines called : SHIFTR, SHIFTL
C     Functions called   : AFGEN
C     File usage         : CRPFIL, file containing crop parameters
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER CRP,I,LOGF,IFND
 
      REAL SLATB(30),AMAXTB(30),TMPFTB(30)
      REAL TMNFTB(30),RFSETB(30),FRTB(30),FLTB(30),FSTB(30),RDRRTB(30)
      REAL RDRSTB(30),KDIF,KDIR,LAIEM,ECMAX,ECSLOP,COFAB,RSC
      REAL HLIM1,HLIM2U,HLIM2L,HLIM3H,HLIM3L,HLIM4,RDCTB(22)
      REAL X,SUM,RFAC,VALUE,ADCRH,ADCRL,AFGEN,CVL,CVR,CVS,EFF,RMR
      REAL PERDL,Q10,RDC,RDI,RGRLAI,RML,RMS,RRI,SPAN,SSA,TBASE,TDWI

      CHARACTER CRPFIL*8,ENVSTR*50,FILNAM*12

      character*80 rmldsp
      
      LOGICAL   EXISTS

C ----------------------------------------------------------------------
C --- compose filename 
      CALL SHIFTR (CRPFIL)
      FILNAM = CRPFIL//'.CRP'
      CALL SHIFTL (FILNAM)
      CALL SHIFTR (ENVSTR)

C --- check if a file with detailed grass data does exist
      INQUIRE (FILE=rmldsp(ENVSTR//FILNAM),EXIST=EXISTS)

      IF (.NOT.EXISTS) THEN
C ---   write error to log file
        WRITE (LOGF,92) ENVSTR//FILNAM
 92     FORMAT ('SWAP can not find the input file',/,A)
        STOP 'The .CRP file was not found: SWAP stopped !'
      ENDIF

C --- open file with crop data
      Call FINDUNIT (10,CRP) 
      OPEN (CRP,FILE=rmldsp(ENVSTR//FILNAM),STATUS='OLD',
     & access='sequential')

C --- initial
      CALL RSREAR (CRP,FILNAM,LOGF,'TDWI',0.0,10000.0,TDWI)
      CALL RSREAR (CRP,FILNAM,LOGF,'LAIEM',0.0,10.0,LAIEM)
      CALL RSREAR (CRP,FILNAM,LOGF,'RGRLAI',0.0,1.0,RGRLAI)

C --- green area
      CALL RAREAR (CRP,FILNAM,LOGF,'SLATB',0.0,366.0,SLATB,30,IFND)
      CALL RSREAR (CRP,FILNAM,LOGF,'SSA',0.0,1.0,SSA)
      CALL RSREAR (CRP,FILNAM,LOGF,'SPAN',0.0,366.0,SPAN)
      CALL RSREAR (CRP,FILNAM,LOGF,'TBASE',-10.0,30.0,TBASE)

C --- assimilation
      CALL RSREAR (CRP,FILNAM,LOGF,'KDIF',0.0,2.0,KDIF)
      CALL RSREAR (CRP,FILNAM,LOGF,'KDIR',0.0,2.0,KDIR)
      CALL RSREAR (CRP,FILNAM,LOGF,'EFF',0.0,10.0,EFF)
      CALL RAREAR (CRP,FILNAM,LOGF,'AMAXTB',0.0,366.0,AMAXTB,30,IFND)
      CALL RAREAR (CRP,FILNAM,LOGF,'TMPFTB',-10.0,50.0,TMPFTB,30,IFND)
      CALL RAREAR (CRP,FILNAM,LOGF,'TMNFTB',-10.0,50.0,TMNFTB,30,IFND)

C --- conversion of assimilates into biomass
      CALL RSREAR (CRP,FILNAM,LOGF,'CVL',0.0,1.0,CVL)
      CALL RSREAR (CRP,FILNAM,LOGF,'CVR',0.0,1.0,CVR)
      CALL RSREAR (CRP,FILNAM,LOGF,'CVS',0.0,1.0,CVS)

C --- maintenance respiration
      CALL RSREAR (CRP,FILNAM,LOGF,'Q10',0.0,5.0,Q10)
      CALL RSREAR (CRP,FILNAM,LOGF,'RML',0.0,1.0,RML)
      CALL RSREAR (CRP,FILNAM,LOGF,'RMR',0.0,1.0,RMR)
      CALL RSREAR (CRP,FILNAM,LOGF,'RMS',0.0,1.0,RMS)
      CALL RAREAR (CRP,FILNAM,LOGF,'RFSETB',0.0,366.0,RFSETB,30,IFND)

C --- partitioning
      CALL RAREAR (CRP,FILNAM,LOGF,'FRTB',0.0,366.0,FRTB,30,IFND)
      CALL RAREAR (CRP,FILNAM,LOGF,'FLTB',0.0,366.0,FLTB,30,IFND)
      CALL RAREAR (CRP,FILNAM,LOGF,'FSTB',0.0,366.0,FSTB,30,IFND)

C --- death rates
      CALL RSREAR (CRP,FILNAM,LOGF,'PERDL',0.0,3.0,PERDL)
      CALL RAREAR (CRP,FILNAM,LOGF,'RDRRTB',0.0,366.0,RDRRTB,30,IFND)
      CALL RAREAR (CRP,FILNAM,LOGF,'RDRSTB',0.0,366.0,RDRSTB,30,IFND)

C --- water use
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM1' ,-100.0,100.0,HLIM1)
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM2U',-1000.0,100.0,HLIM2U)
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM2L',-1000.0,100.0,HLIM2L)
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM3H',-10000.0,100.0,HLIM3H)
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM3L',-10000.0,100.0,HLIM3L)
      CALL RSREAR (CRP,FILNAM,LOGF,'HLIM4' ,-16000.0,100.0,HLIM4)
      CALL RSREAR (CRP,FILNAM,LOGF,'RSC',0.0,1000.0,RSC)
      CALL RSREAR (CRP,FILNAM,LOGF,'ADCRH',0.0,5.0,ADCRH)
      CALL RSREAR (CRP,FILNAM,LOGF,'ADCRL',0.0,5.0,ADCRL)
      CALL RSREAR (CRP,FILNAM,LOGF,'ECMAX',0.0,20.0,ECMAX)
      CALL RSREAR (CRP,FILNAM,LOGF,'ECSLOP',0.0,40.0,ECSLOP)
      CALL RSREAR (CRP,FILNAM,LOGF,'COFAB',0.0,1.0,COFAB)

C --- rooting
      CALL RAREAR (CRP,FILNAM,LOGF,'RDCTB',0.0,100.0,RDCTB,22,IFND)
      CALL RSREAR (CRP,FILNAM,LOGF,'RDI',0.0,1000.0,RDI)
      CALL RSREAR (CRP,FILNAM,LOGF,'RRI',0.0,100.0,RRI)
      CALL RSREAR (CRP,FILNAM,LOGF,'RDC',0.0,1000.0,RDC)

C --- normalize RDCTB
      SUM = 0.0
      DO 96 X = 0.05,1.0,0.1
        VALUE = AFGEN (RDCTB,22,X)
        SUM = SUM+0.1*VALUE
96    CONTINUE

      RFAC = 1/SUM
      DO 98 I = 1,IFND/2
98    RDCTB(I*2) = RDCTB(I*2)*RFAC

      CLOSE (CRP)

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RDHEA (PRJNAM,ENVSTR,LOGF,SWSHF,TAMPLI,TMEAN,DDAMP,
     &  TIMREF,TEMPI,NUMNOD)
C ----------------------------------------------------------------------
C     Date               : 12/11/1997                                      
C     Purpose            : read soil heat transport input data     
C                          
C     Subroutines called : SHIFTL,SHIFTR,FINDUNIT,TTUTIL                                          
C     Functions called   : -                     
C     File usage         : PARAM.FI                                           
C ----------------------------------------------------------------------
C---- Declarations
      IMPLICIT NONE

      INCLUDE 'PARAM.FI'

      INTEGER LOGF,SWSHF,NUMNOD

      REAL TAMPLI,TMEAN,DDAMP,TIMREF,TEMPI(MACP)

      CHARACTER PRJNAM*8,ENVSTR*50 ,FILNAM*12

      character*80 rmldsp
C-----------------------------------------------------------------------
C --- local
      INTEGER HEA,CP

      REAL    TEMP(MACP)

      LOGICAL EXISTS
C ----------------------------------------------------------------------
C --- compose filename
      CALL SHIFTR (PRJNAM)
      FILNAM = PRJNAM//'.HEA'
      CALL SHIFTL (FILNAM)
      CALL SHIFTR (ENVSTR)

C --- check if a file with heat flow data does exist
      INQUIRE (FILE=rmldsp(ENVSTR//FILNAM),EXIST=EXISTS)

      IF (.NOT.EXISTS) THEN
C ---   write error to log file
        WRITE (LOGF,92) ENVSTR//FILNAM
 92     FORMAT ('SWAP can not find the input file',/,A)
        STOP 'The .HEA file was not found: SWAP stopped !'
      ENDIF

C --- open file with soil heat flow parameters
      CALL FINDUNIT(20,HEA)
      OPEN (HEA,FILE=rmldsp(ENVSTR//FILNAM),STATUS='OLD',
     &  ACCESS='SEQUENTIAL')

C --- method 
      CALL RSINTR (HEA,FILNAM,LOGF,'SWSHF',1,2,SWSHF)

      IF (SWSHF.EQ.1) THEN
        CALL RSREAR (HEA,FILNAM,LOGF,'TAMPLI',0.0,50.0,TAMPLI)
        CALL RSREAR (HEA,FILNAM,LOGF,'TMEAN',5.0,30.0,TMEAN)
        CALL RSREAR (HEA,FILNAM,LOGF,'DDAMP',0.0,500.0,DDAMP)
        CALL RSREAR (HEA,FILNAM,LOGF,'TIMREF',0.0,366.0,TIMREF)
	  close(hea)
	  RETURN
      ELSEIF (SWSHF.EQ.2) THEN
        CALL JMPLBL (HEA,FILNAM,LOGF,'TEMPI')
        CALL RFREAR (HEA,FILNAM,LOGF,'TEMPI',-10.0,40.0,TEMP,MACP,
     &  NUMNOD)
        DO 30  CP = 1,NUMNOD
   30   TEMPI(CP) = TEMP(CP)
      ENDIF

      CLOSE(HEA)

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RDKEY (LOGF,PRJNAM,ENVSTR,STASTR,BRUNY,BRUND,ERUNY,
     &  ERUND,ISEQ,FMAY,PERIOD,SWRES,OUTD,OUTY,METFIL,LAT,ALT,SWETR,
     &  SWRAI,IRGFIL,CALFIL,DRFIL,BBCFIL,OUTFIL,NOFRNS,
     &  FLCAL,SWDRA,SWSOLU,SWHEA,SWVAP,SWDRF,SWSWB,SWAFO,AFONAM,
     &  SWAUN,AUNNAM,SWATE,ATENAM,SWAIR,AIRNAM,SWSCRE,NOUTDA)
C ----------------------------------------------------------------------
C     Date               : 17/4/98       
C     Purpose            : read general input data SWAP
C     Subroutines called : SHIFTR,DATONR 
C     Functions called   : FROMTO
C     File usage         : SWAP.KEY, file with general input data
C ---------------------------------------------------------------------
      IMPLICIT NONE 
      INCLUDE 'PARAM.FI'

      INTEGER LOGF,BRUND,BRUNY,ERUND,ERUNY,ISEQ,FMAY,PERIOD,SWRES
      INTEGER OUTD(366),OUTY(366),SWETR,SWRAI,NOFRNS,SWDRA,SWSOLU
      INTEGER SWHEA,SWVAP,SWDRF,SWSWB,SWAFO,SWAUN,SWATE,SWAIR,SWSCRE
	INTEGER NOUTDA

      REAL    LAT,ALT
      
      CHARACTER   PRJNAM*8,ENVSTR*50,STASTR*7,METFIL*7
      CHARACTER*8 IRGFIL(MAYRS),CALFIL(MAYRS),DRFIL(MAYRS)
      CHARACTER*8 BBCFIL(MAYRS),OUTFIL(MAYRS)
      CHARACTER*8 AFONAM,AUNNAM,ATENAM,AIRNAM

      LOGICAL FLCAL,EXISTS

C ----------------------------------------------------------------------
C --- local
      INTEGER DD(366),MM(366),D1,M1,Y1,IFND,SSRUN(3),ESRUN(3),KEY
      INTEGER FROMTO,I,NR,SWODAT,FDAY

      CHARACTER LINE*80 ,FILNAM*12

      LOGICAL  BLANK,COMMENT
C ----------------------------------------------------------------------

C --- check if file SWAP.KEY does exist
      INQUIRE (FILE='SWAP.KEY',EXIST=EXISTS)
      IF (.NOT.EXISTS) THEN
C ---   write error to log file
        WRITE (LOGF,92) 'SWAP.KEY'
 92     FORMAT ('SWAP can not find the input file ',A)
        STOP 'The SWAP.KEY file was not found: SWAP stopped !'
      ENDIF
      EXISTS=.TRUE.
C --- open key file
      CALL FINDUNIT (10,KEY)
      FILNAM = 'SWAP.KEY'
      OPEN (KEY,FILE=FILNAM,STATUS='OLD',ACCESS='SEQUENTIAL')

C --- environment
      CALL RSCHAR (KEY,FILNAM,LOGF,'PROJECT',PRJNAM)
      CALL RSCHAR (KEY,FILNAM,LOGF,'PATH',ENVSTR)
      CALL RSINTR (KEY,FILNAM,LOGF,'CTYPE',1,2,I)
      IF (I.EQ.1) STASTR = 'UNKNOWN'
      IF (I.EQ.2) STASTR = 'NEW    '
      CALL RSINTR (KEY,FILNAM,LOGF,'SWSCRE',0,1,SWSCRE) 

C --- time variables
      CALL RFINTR (KEY,FILNAM,LOGF,'SSRUN',1,3000,SSRUN,3,3)
      D1 = SSRUN(1)
      M1 = SSRUN(2)
      Y1 = SSRUN(3)
      BRUNY = Y1
      CALL DATONR (Y1,M1,D1,BRUND)
      CALL RFINTR (KEY,FILNAM,LOGF,'ESRUN',0,3000,ESRUN,3,3)
      D1 = ESRUN(1)
      M1 = ESRUN(2)
      Y1 = ESRUN(3)
      ERUNY = Y1
      CALL DATONR (Y1,M1,D1,ERUND)
      CALL RSINTR (KEY,FILNAM,LOGF,'FMAY',1,12,FMAY)
      CALL RSINTR (KEY,FILNAM,LOGF,'PERIOD',0,366,PERIOD)
      CALL RSINTR (KEY,FILNAM,LOGF,'SWRES',0,1,SWRES)

      CALL DATONR (BRUNY,FMAY,1,FDAY) 
      ISEQ  = 0
      IF (FROMTO(FDAY,BRUNY,ERUND,ERUNY).GT.366) ISEQ=1

C --- read additional output dates
      Do 4 I = 1,366
        OUTD(I) = 0
        OUTY(I) = 0
4     Continue

      CALL RSINTR (KEY,FILNAM,LOGF,'SWODAT',0,1,SWODAT)
      IF (SWODAT.EQ.0) THEN
        CALL JMPLBL (KEY,FILNAM,LOGF,'METFIL')
      ELSE
C ---   position file pointer
        IFND = 0
5       READ (KEY,'(A)') LINE
        CALL ANALIN (LINE,BLANK,COMMENT)
        IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 5
        IF (COMMENT) GOTO 15
          IFND = IFND+1
          BACKSPACE (KEY)
          READ (KEY,*) DD(IFND),MM(IFND),OUTY(IFND) 
          CALL DATONR(OUTY(IFND),MM(IFND),DD(IFND),NR)
          OUTD(IFND) = NR
          GOTO 5
C ---   ready...
15      CONTINUE
        NOUTDA = IFND
        IF (PERIOD.EQ.0 .AND. IFND.EQ.0) Then
         PRINT *,'No output dates specified'
         STOP
        ENDIF
      ENDIF

C --- meteo
      CALL RSCHAR (KEY,FILNAM,LOGF,'METFIL',METFIL)
      CALL RSREAR (KEY,FILNAM,LOGF,'LAT',-60.0,60.0,LAT)
      CALL RSREAR (KEY,FILNAM,LOGF,'ALT',-400.0,3000.0,ALT)
      CALL RSINTR (KEY,FILNAM,LOGF,'SWETR',0,1,SWETR)
      CALL RSINTR (KEY,FILNAM,LOGF,'SWRAI',0,1,SWRAI) 

C --- rerun list
      IFND = 0
6     READ (KEY,'(A)') LINE
      CALL ANALIN (LINE,BLANK,COMMENT)
      IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 6
      IF (COMMENT) GOTO 16
        IFND = IFND+1
        IF (IFND.GT.MAYRS) STOP 'KEY - rerun list too long'
        BACKSPACE (KEY)
        READ (KEY,*) IRGFIL(IFND),CALFIL(IFND),DRFIL(IFND),
     &                BBCFIL(IFND),OUTFIL(IFND) 
        GOTO 6
C --- ready...
16    CONTINUE
      NOFRNS = IFND
      FLCAL  = .TRUE.

C --- drainage
      CALL RSINTR (KEY,FILNAM,LOGF,'SWDRA',0,2,SWDRA)

C --- solute
      CALL RSINTR (KEY,FILNAM,LOGF,'SWSOLU',0,1,SWSOLU)

C --- heat
      CALL RSINTR (KEY,FILNAM,LOGF,'SWHEA',0,1,SWHEA)

C --- summary
      CALL RSINTR (KEY,FILNAM,LOGF,'SWVAP',0,1,SWVAP)

C --- drainage fluxes, surface reservoir 
      IF (SWDRA.EQ.2) THEN
        CALL RSINTR (KEY,FILNAM,LOGF,'SWDRF',0,1,SWDRF)
        CALL RSINTR (KEY,FILNAM,LOGF,'SWSWB',0,1,SWSWB)
      ELSE
        CALL JMPLBL (KEY,FILNAM,LOGF,'SWAFO')
      ENDIF
 
C --- output for water quality models
      CALL RSINTR (KEY,FILNAM,LOGF,'SWAFO',0,1,SWAFO)
      IF (SWAFO.EQ.1) THEN
        CALL RSCHAR (KEY,FILNAM,LOGF,'AFONAM',AFONAM)
      ELSE
        CALL JMPLBL (KEY,FILNAM,LOGF,'SWAUN')
      ENDIF

      CALL RSINTR (KEY,FILNAM,LOGF,'SWAUN',0,1,SWAUN)
      IF (SWAUN.EQ.1) THEN
        CALL RSCHAR (KEY,FILNAM,LOGF,'AUNNAM',AUNNAM)
      ELSE
        CALL JMPLBL (KEY,FILNAM,LOGF,'SWATE')
      ENDIF

      CALL RSINTR (KEY,FILNAM,LOGF,'SWATE',0,1,SWATE)
      IF (SWATE.EQ.1) THEN
        CALL RSCHAR (KEY,FILNAM,LOGF,'ATENAM',ATENAM)
      ELSE
        CALL JMPLBL (KEY,FILNAM,LOGF,'SWAIR')
      ENDIF
      
      CALL RSINTR (KEY,FILNAM,LOGF,'SWAIR',0,1,SWAIR)
      IF (SWAIR.EQ.1) CALL RSCHAR (KEY,FILNAM,LOGF,'AIRNAM',AIRNAM)

      CLOSE (KEY)

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RDSLT (PRJNAM,ENVSTR,LOGF,CPRE,CMLI,DDIF,LDIS,TSCF,KF,
     &  FREXP,CREF,DECPOT,GAMPAR,RTHETA,BEXP,FDEPTH,KMOBIL,
     &  HAQUIF,POROS,KFSAT,DECSAT,CDRAIN,NUMNOD,NUMLAY,SWBR)
C ----------------------------------------------------------------------
C     Date               : 17/4/98                                     
C     Purpose            : read soil water and profile characteristics     
C                          
C     Subroutines called : -                                           
C     Functions called   : -                     
C     File usage         : -                                           
C ----------------------------------------------------------------------
C---- Declarations
      IMPLICIT NONE

      INCLUDE 'PARAM.FI'

      INTEGER NUMNOD,NUMLAY,LOGF,SWBR

      REAL  CPRE,CMLI(MACP),DDIF,LDIS,TSCF,KF,FREXP,CREF 
      REAL  DECPOT,GAMPAR,RTHETA,BEXP,FDEPTH(MAHO),KMOBIL,HAQUIF,POROS
      REAL  KFSAT,DECSAT,CDRAIN

      CHARACTER PRJNAM*8,ENVSTR*50,FILNAM*12

      character*80 rmldsp
C ----------------------------------------------------------------------
C --- local
      INTEGER SLT,LAY,SWSP,SWDC,SWPREF

      LOGICAL EXISTS
C ----------------------------------------------------------------------
C --- compose filename
      CALL SHIFTR (PRJNAM)
      FILNAM = PRJNAM//'.SLT'
      CALL SHIFTL (FILNAM)
      CALL SHIFTR (ENVSTR)

C --- check if a file with solute transport data does exist
      INQUIRE (FILE=rmldsp(ENVSTR//FILNAM),EXIST=EXISTS)

      IF (.NOT.EXISTS) THEN
C ---   write error to log file
        WRITE (LOGF,92) ENVSTR//FILNAM
 92     FORMAT ('SWAP can not find the input file',/,A)
        STOP 'The .SLT file was not found: SWAP stopped !'
      ENDIF

C --- open file with solute parameters
      CALL FINDUNIT(30,SLT)
      OPEN (SLT,FILE=rmldsp(ENVSTR//FILNAM),STATUS='OLD',
     &  ACCESS='SEQUENTIAL')

      CALL RSREAR (SLT,FILNAM,LOGF,'CPRE',0.0,100.0,CPRE)
      CALL RFREAR (SLT,FILNAM,LOGF,'CMLI',0.0,1000.0,CMLI,MACP,NUMNOD)
	CALL JMPLBL (SLT,FILNAM,LOGF,'DDIF')
      CALL RSREAR (SLT,FILNAM,LOGF,'DDIF',0.0,10.0,DDIF)
      CALL RSREAR (SLT,FILNAM,LOGF,'LDIS',0.0,100.0,LDIS)
      CALL RSREAR (SLT,FILNAM,LOGF,'TSCF',0.0,10.0,TSCF)

C --- sorption
      CALL RSINTR (SLT,FILNAM,LOGF,'SWSP',0,1,SWSP)
      IF (SWSP .EQ. 1) THEN
        CALL RSREAR (SLT,FILNAM,LOGF,'KF',0.0,100.0,KF)
        CALL RSREAR (SLT,FILNAM,LOGF,'FREXP',0.0,10.0,FREXP)
        CALL RSREAR (SLT,FILNAM,LOGF,'CREF',0.0,1000.0,CREF)
      ELSE IF (SWSP.EQ.0) THEN
        FREXP = 1.0
        CREF  = 1.0
        KF    = 0.0
        CALL JMPLBL (SLT,FILNAM,LOGF,'SWDC')
      ENDIF

C --- decomposition
      CALL RSINTR (SLT,FILNAM,LOGF,'SWDC',0,1,SWDC)
      IF (SWDC .EQ. 1) THEN
        CALL RSREAR (SLT,FILNAM,LOGF,'DECPOT',0.0,10.0,DECPOT)
        CALL RSREAR (SLT,FILNAM,LOGF,'GAMPAR',0.0,0.5,GAMPAR)
        CALL RSREAR (SLT,FILNAM,LOGF,'RTHETA',0.0,0.4,RTHETA)
        CALL RSREAR (SLT,FILNAM,LOGF,'BEXP',0.0,2.0,BEXP)
        CALL RFREAR (SLT,FILNAM,LOGF,'FDEPTH',0.0,1.0,FDEPTH,MAHO,
     &  NUMLAY)
      ELSE IF (SWDC .EQ. 0) THEN
        DECPOT = 0.0
        GAMPAR = 0.0
        RTHETA = 0.5
        BEXP   = 0.0
        DO 181 LAY = 1,MAHO
181     FDEPTH(LAY) = 0.0
        CALL JMPLBL (SLT,FILNAM,LOGF,'SWPREF')
      ENDIF

C --- preferential flow 
      CALL RSINTR (SLT,FILNAM,LOGF,'SWPREF',0,1,SWPREF)
      IF (SWPREF .EQ. 1) THEN
        CALL RSREAR (SLT,FILNAM,LOGF,'KMOBIL',0.0,100.0,KMOBIL)
      ELSEIF (SWPREF .EQ. 0) THEN
        KMOBIL = 0.0
        CALL JMPLBL (SLT,FILNAM,LOGF,'SWBR')
      ENDIF

C --- breakthrough
      CALL RSINTR (SLT,FILNAM,LOGF,'SWBR',0,1,SWBR)
      IF (SWBR .EQ. 0) THEN
        CALL RSREAR (SLT,FILNAM,LOGF,'CDRAIN',0.0,100.0,CDRAIN)
        HAQUIF = 100.0
        POROS  = 1.0
        KFSAT  = 0.0
        DECSAT = 0.0
      ELSEIF (SWBR .EQ. 1) THEN
        CALL JMPLBL (SLT,FILNAM,LOGF,'HAQUIF')
        CALL RSREAR (SLT,FILNAM,LOGF,'HAQUIF',0.0,10000.0,HAQUIF)
        CALL RSREAR (SLT,FILNAM,LOGF,'POROS',0.0,0.6,POROS)
        CALL RSREAR (SLT,FILNAM,LOGF,'KFSAT',0.0,100.0,KFSAT)
        CALL RSREAR (SLT,FILNAM,LOGF,'DECSAT',0.0,10.0,DECSAT)
        CALL RSREAR (SLT,FILNAM,LOGF,'CDRAINI',0.0,100.0,CDRAIN)
      ENDIF

      CLOSE(SLT)

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RDSOL (SOLFIL,ENVSTR,LAY,FLGENU,THETHI,THETLO,HTABLE,
     & KTABLE,THETSL,KSAT,DMCH,DMCC,COFGEN,SWSCAL,ISCLAY,FSCALE,IRUNNR,
     & KSE99,LOGF,SWHYST)
C ----------------------------------------------------------------------
C     Date               : 17/4/98
C     Purpose            : reading the soil physical data              
C     Subroutines called : SHIFTL,SHIFTR           
C     File usage         : SOLFIL, file containing soil characteristics        
C ----------------------------------------------------------------------
C --- global
      IMPLICIT NONE
 
      INCLUDE 'PARAM.FI'

      INTEGER   LAY,SWSCAL,ISCLAY,THETLO(MAHO),THETHI(MAHO),IRUNNR,LOGF
      INTEGER   SWHYST

      REAL      fscale(MAYRS)

      REAL*8    HTABLE(MAHO,99),COFGEN(8,MAHO),KTABLE(MAHO,99)
      REAL*8    DMCC(MAHO,99),DMCH(MAHO,99),THETSL(MAHO),KSAT(MAHO)
      REAL*8    KSE99(MAHO)

      CHARACTER SOLFIL*8,ENVSTR*50

      LOGICAL   FLGENU(MAHO)
C ----------------------------------------------------------------------
C --- local
      INTEGER   sol,swphys,i,j,ifnd

      REAL      relsat
      REAL*8    exponl,term1,THETB(99),HBUF(99),KBUF(99)

      CHARACTER filnam*12,LINE*80

      character*80 rmldsp
      
      LOGICAL BLANK,COMMENT,EXISTS
C ----------------------------------------------------------------------
C --- compose filename
      CALL SHIFTR (SOLFIL)
      FILNAM = SOLFIL//'.SOL'
      CALL SHIFTL (FILNAM)
      CALL SHIFTR (ENVSTR)

C --- check if a file with soil hydraulic data does exist
      INQUIRE (FILE=rmldsp(ENVSTR//FILNAM),EXIST=EXISTS)

      IF (.NOT.EXISTS) THEN
C ---   write error to log file
        WRITE (LOGF,92) ENVSTR//FILNAM
 92     FORMAT ('SWAP can not find the input file: ',A)
        STOP 'The .SOL file was not found: SWAP stopped !'
      ENDIF

C --- open file with soil parameters
      CALL FINDUNIT (16,SOL)
      OPEN (SOL,FILE=rmldsp(ENVSTR//FILNAM),STATUS='OLD',
     & ACCESS='SEQUENTIAL')

C --- method to describe soil physical parameters
      CALL RSINTR (SOL,FILNAM,LOGF,'SWPHYS',0,1,SWPHYS)
      IF (SWPHYS.EQ.0) THEN
	  IF (SWHYST.GT.0) THEN
          WRITE(LOGF,2) FILNAM
	    WRITE(*,2) FILNAM
 2        FORMAT(' Error in file:',A,': In order to calculate ',
     &     'hysteresis, the soil hydraulic functions',/,
     &     ' should be described by the Mualem-Van Genuchten model;',/,
     &     ' please adapt the *.SOL file')
          STOP 'Check log file'
	  ENDIF
        FLGENU(LAY) = .FALSE.
      ELSE
        FLGENU(LAY) = .TRUE.
      ENDIF

C --- soil physical data presented as a table
      IF (.NOT.FLGENU(LAY)) THEN
C ---   read table
        IFND = 0
4       READ (SOL,'(A)') LINE
        CALL ANALIN (LINE,BLANK,COMMENT)
        IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 4
        IF (COMMENT) GOTO 8
          IFND = IFND+1
          IF (IFND.GT.99) STOP 'RDSOL - table too long'
          BACKSPACE (SOL)
          READ (SOL,*) THETB(IFND),HBUF(IFND),KBUF(IFND)
          GOTO 4
8       CONTINUE

        THETLO(LAY) = INT(100.0D0 *THETB(1)+0.5D0)
        THETHI(LAY) = INT(100.0D0 * THETB(IFND) + 0.5D0)

C ---   saturated water content and hydraulic conductivity
        THETSL(LAY) = THETB(IFND)
        KSAT(LAY)   = KBUF(IFND)

C ---   fill HTABLE and KTABLE
        J = 1
        DO 14 I = THETLO(LAY),THETHI(LAY)
          HTABLE(LAY,I) = HBUF(J)
          KTABLE(LAY,I) = KBUF(J)
          J = J+1
14      CONTINUE

C ---   check pressure head range
        IF (HTABLE(LAY,THETLO(LAY)) .GT. -0.99D6) THEN
          WRITE(LOGF,16) FILNAM
          WRITE(*,16) FILNAM
 16       FORMAT(' Fatal error in file: ',A,
     &           ': the lowest pressure head in',/, 
     &           ' the table of the soil hydraulic functions should be',
     &           ' smaller than or equal to -1.0e6')
          STOP 'Check log file'
        ENDIF

        IF (HTABLE(LAY,THETHI(LAY)) .LT. -1.0D-6) THEN
          WRITE(LOGF,18) FILNAM
          WRITE(*,18) FILNAM
 18       FORMAT(' Fatal error in file: ',A,
     &           ': the highest pressure head in',/,
     &           ' the table of the soil hydraulic functions should be',
     &           ' equal to zero')
          STOP 'Check log file'
        ENDIF

C ---   prepare dmc-table
        DO 20 I = THETLO(LAY),THETHI(LAY)-1
          DMCH(LAY,I) = 0.5D0*(HTABLE(LAY,I)+HTABLE(LAY,I+1))
          DMCC(LAY,I) = 0.01D0/(HTABLE(LAY,I+1)-HTABLE(LAY,I))
20      CONTINUE
        DMCH(LAY,THETHI(LAY)) = 0.0D0
        DMCC(LAY,THETHI(LAY)) = DMCC(LAY,THETHI(LAY)-1)

        HTABLE(LAY,THETHI(LAY)+1) = -1.0D0*HTABLE(LAY,THETHI(LAY)-1)
        HTABLE(LAY,THETHI(LAY)+2) = -1.0D0*HTABLE(LAY,THETHI(LAY)-2) 
        KTABLE(LAY,THETHI(LAY)+1) = KTABLE(LAY,THETHI(LAY))
        KTABLE(LAY,THETHI(LAY)+2) = KTABLE(LAY,THETHI(LAY))
      ENDIF

C --- soil physical data according to Van Genuchten
      IF (FLGENU(LAY)) THEN
C ---   first position file pointer
        CALL JMPLBL(SOL,FILNAM,LOGF,'COFGEN1')

        CALL RSDOUR (SOL,FILNAM,LOGF,'COFGEN1',0.0D0,0.4D0,COFGEN(1,
     &               LAY))
        CALL RSDOUR (SOL,FILNAM,LOGF,'COFGEN2',COFGEN(1,LAY),0.95D0,
     &               COFGEN(2,LAY))
        CALL RSDOUR (SOL,FILNAM,LOGF,'COFGEN3',1.0D-2,1.0D4,COFGEN(3,
     &  LAY))
        CALL RSDOUR (SOL,FILNAM,LOGF,'COFGEN4',0.1D-4,1.0D0,COFGEN(4,
     &  LAY))
        CALL RSDOUR (SOL,FILNAM,LOGF,'COFGEN5',-25.0D0,25.0D0,COFGEN(5,
     &  LAY))
        CALL RSDOUR (SOL,FILNAM,LOGF,'COFGEN6',1.0D0,5.0D0,COFGEN(6,
     &  LAY))
        IF (SWHYST .NE. 0) THEN
          CALL RSDOUR (SOL,FILNAM,LOGF,'COFGEN8',COFGEN(4,LAY),1.0D0, 
     &    COFGEN(8,LAY))
	  ENDIF

        COFGEN(7,LAY) = 1.0d0 - (1.0d0/cofgen(6,lay))
        COFGEN(5,LAY) = COFGEN(7,LAY) * (COFGEN(5,LAY)+2.0D0)

C --- modify some parameters according to scaling factors
        IF (SWSCAL.EQ.1.AND.ISCLAY.EQ.LAY) THEN
          COFGEN(3,LAY) = COFGEN(3,LAY)*FSCALE(IRUNNR)**2
          COFGEN(4,LAY) = COFGEN(4,LAY)*FSCALE(IRUNNR)
        ENDIF

C --- saturated water content and conductivity for each layer
        thetsl(lay) = cofgen(2,lay)
        ksat(lay)   = cofgen(3,lay)
        relsat      = 0.99
        exponl      = cofgen(5,lay)/cofgen(7,lay)-2.0d0
        term1       = (1.0d0-relsat**(1.0/cofgen(7,lay)))**cofgen(7,lay)
        kse99(lay)  = cofgen(3,lay)*(relsat**exponl)*(1.0d0-term1)*
     &                (1.0d0-term1)
      ENDIF

      CLOSE (SOL)
      RETURN
      END


c------------------------------------------------------------
      character*80 function rmldsp( str )
c       Remove leading spaces and return character*80
c       if the length of str is more than 80, it will be cut
c       to 80.
c------------------------------------------------------------

      character*(*) str
      character*80 buf

      buf=str
      do i=1,len(str)
        if( str(i:i) .ne. ' ' ) then
                k=1
                buf=str(i:)
                goto 100
         endif
      end do
  100 continue
      rmldsp=buf

      end




C ----------------------------------------------------------------------
      SUBROUTINE RDSWA(PRJNAM,ENVSTR,LOGF,PONDMX,SWREDU,COFRED,RSIGNI,
     &  DTMIN,DTMAX,SWNUMS,THETOL,NUMLAY,NUMNOD,BOTCOM,DZ,SOLFIL,RDS,
     &  SWHYST,TAU,SWSCAL,NSCALE,ISCLAY,FSCALE,SWMOBI,PF1,FM1,PF2,FM2,
     &  THETIM,SWCRACK,SHRINA,MOISR1,MOISRD,ZNCRACK,GEOMF,DIAMPOL,
     &  RAPCOEF,DIFDES,SWDIVD,COFANI,SWINCO,HI,GWLI,THETCR,PSAND,PSILT,
     &  PCLAY,ORGMAT,CFBS,SWCFBS)
C ----------------------------------------------------------------------
C     Date               : 14/1/99
C     Purpose            : read soil water and profile characteristics
C
C     Subroutines called : -
C     Functions called   : -
C     File usage         : -
C ----------------------------------------------------------------------
C---- Declarations
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

      INTEGER LOGF,SWREDU,SWNUMS,NUMLAY,NUMNOD,BOTCOM(MAHO),SWHYST
      INTEGER SWSCAL,NSCALE,ISCLAY,SWMOBI,SWCRACK,SWDIVD,SWINCO,SWCFBS

      REAL  PONDMX,COFRED,RSIGNI,DTMIN,DTMAX,THETOL,DZ(MACP),RDS
      REAL  FSCALE(MAYRS),PF1(MAHO),FM1(MAHO),PF2(MAHO),FM2(MAHO),SHRINA
      REAL  MOISR1,MOISRD,ZNCRACK,GEOMF,DIAMPOL,RAPCOEF,DIFDES
      REAL  COFANI(MAHO),GWLI,THETCR(MAHO),PSAND(MAHO),PSILT(MAHO)
      REAL  PCLAY(MAHO),ORGMAT(MAHO),CFBS

      REAL*8 TAU,THETIM(MAHO),HI(MACP)

      CHARACTER   PRJNAM*8,ENVSTR*50
      CHARACTER*8 SOLFIL(MAHO)

C ----------------------------------------------------------------------
C --- local variables
      INTEGER SWA,IFND,LAY

      CHARACTER   FILNAM*12,LINE*80

      character*80 rmldsp
      
      LOGICAL BLANK,COMMENT,EXISTS
C ----------------------------------------------------------------------
C --- compose filename
      CALL SHIFTR (PRJNAM)
      FILNAM = PRJNAM//'.SWA'
      CALL SHIFTL (FILNAM)
      CALL SHIFTR (ENVSTR)

C --- check if a file with soil water data does exist
      INQUIRE (FILE=rmldsp(ENVSTR//FILNAM),EXIST=EXISTS)
      IF (.NOT.EXISTS) THEN
C ---   write error to log file
        WRITE (LOGF,98) ENVSTR//FILNAM
 98     FORMAT ('SWAP can not find the input file',/,A)
        STOP 'The .SWA file was not found: SWAP stopped !'
      ENDIF

C --- open file with soil parameters
      CALL FINDUNIT(22,SWA)
      OPEN (SWA,FILE=rmldsp(ENVSTR//FILNAM),STATUS='OLD',
     & ACCESS='SEQUENTIAL')

C --- ponding
      CALL RSREAR (SWA,FILNAM,LOGF,'PONDMX',0.0,1000.0,PONDMX)

C --- soil evaporation
      CALL RSINTR (SWA,FILNAM,LOGF,'SWCFBS',0,1,SWCFBS)
      IF (SWCFBS.EQ.1) THEN
        CALL RSREAR (SWA,FILNAM,LOGF,'CFBS',0.5,1.5,CFBS)
      ELSE
        CALL JMPLBL(SWA,FILNAM,LOGF,'SWREDU')
      ENDIF
      CALL RSINTR (SWA,FILNAM,LOGF,'SWREDU',0,2,SWREDU)
      IF (SWREDU .GT.0) THEN
        CALL RSREAR (SWA,FILNAM,LOGF,'COFRED',0.0,1.0,COFRED)
        CALL RSREAR (SWA,FILNAM,LOGF,'RSIGNI',0.0,1.0,RSIGNI)  
      ELSE
        CALL JMPLBL (SWA,FILNAM,LOGF,'DTMIN')
      ENDIF
 
C --- parameters numerical scheme
      CALL RSREAR (SWA,FILNAM,LOGF,'DTMIN',1.0E-8,0.1,DTMIN)
      CALL RSREAR (SWA,FILNAM,LOGF,'DTMAX',0.01,0.5,DTMAX)
      CALL RSINTR (SWA,FILNAM,LOGF,'SWNUMS',1,2,SWNUMS)
      CALL RSREAR (SWA,FILNAM,LOGF,'THETOL',1.E-5,0.01,THETOL)

C --- geometry of the soil profile
      CALL RSINTR (SWA,FILNAM,LOGF,'NUMLAY',1,MAHO,NUMLAY)
      CALL RSINTR (SWA,FILNAM,LOGF,'NUMNOD',1,MACP,NUMNOD)
      CALL RFINTR (SWA,FILNAM,LOGF,'BOTCOM',1,NUMNOD,BOTCOM,MAHO,NUMLAY)
C --- thickness of compartments
      CALL RFREAR (SWA,FILNAM,LOGF,'DZ',1.0E-6,500.0,DZ,MACP,NUMNOD)

C --- files with soil hydraulic functions
      CALL RFCHAR (SWA,FILNAM,LOGF,'SOLFIL',SOLFIL,MAHO,NUMLAY)

C --- soil texture and organic matter per soil layer
      IFND = 0
 36   READ (SWA,'(A)') LINE
      CALL ANALIN (LINE,BLANK,COMMENT)
      IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 36
      IF (COMMENT) GOTO 38
        IFND = IFND+1
        IF (IFND.GT.MAHO) STOP 'SWA - swmobi_table too long'
        BACKSPACE (SWA)
        READ (SWA,*) PSAND(IFND),PSILT(IFND),PCLAY(IFND),ORGMAT(IFND)
        GOTO 36
 38   CONTINUE

C --- rooting depth limitation
      CALL RSREAR (SWA,FILNAM,LOGF,'RDS',1.0,1000.0,RDS)

C --- hysteresis
      CALL RSINTR (SWA,FILNAM,LOGF,'SWHYST',0,2,SWHYST)
      IF (SWHYST.GT.0) THEN
        CALL RSDOUR (SWA,FILNAM,LOGF,'TAU',0.0D0,1.0D0,TAU)
      ELSE
        CALL JMPLBL(SWA,FILNAM,LOGF,'SWSCAL')
      ENDIF

C --- scaling
      CALL RSINTR (SWA,FILNAM,LOGF,'SWSCAL',0,1,SWSCAL)
      IF (SWSCAL.EQ.1) then
	  IF (SWHYST.GT.0) THEN
          WRITE(LOGF,40) FILNAM
	    WRITE(*,40) FILNAM
 40       FORMAT(' Hysteresis in combination with scaling is not',
     &           ' allowed; adapt: ',A)
          STOP 'Check log file'
	  ENDIF
        CALL RSINTR (SWA,FILNAM,LOGF,'NSCALE',1,MAYRS,NSCALE)
        CALL RSINTR (SWA,FILNAM,LOGF,'ISCLAY',1,MAHO,ISCLAY)
        CALL RAREAR (SWA,FILNAM,LOGF,'FSCALE',0.0,100.0,FSCALE,MAYRS,
     &  IFND)
      ELSE
        CALL JMPLBL(SWA,FILNAM,LOGF,'SWMOBI')
      ENDIF

C --- preferential flow due to immobile water
      CALL RSINTR (SWA,FILNAM,LOGF,'SWMOBI',0,1,SWMOBI)
      IF (SWMOBI.EQ.1) THEN
	  IF (SWHYST.GT.0) THEN
          WRITE(LOGF,42) FILNAM
	    WRITE(*,42) FILNAM 
 42       FORMAT(' Hysteresis in combination with preferential',
     &           ' flow is not allowed; adapt: ',A)
          STOP 'Check log file'
	  ENDIF
	  IF (SWSCAL.EQ.1) THEN
          WRITE(LOGF,44) FILNAM
	    WRITE(*,44) FILNAM
 44       FORMAT(' Scaling in combination with preferential',
     &           ' flow is not allowed; adapt: ',A)
          STOP 'Check log file'
	  ENDIF
C ---   read table
        IFND = 0
4       READ (SWA,'(A)') LINE
        CALL ANALIN (LINE,BLANK,COMMENT)
        IF (BLANK .OR. (COMMENT .AND. IFND .EQ. 0)) GOTO 4
        IF (COMMENT) GOTO 8
          IFND = IFND+1
          IF (IFND.GT.MAHO) STOP 'SWA - swmobi_table too long'
          BACKSPACE (SWA)
          READ (SWA,*) PF1(IFND),FM1(IFND),PF2(IFND),FM2(IFND),
     &                  THETIM(IFND)

          GOTO 4
8       CONTINUE

      ELSE IF (SWMOBI.EQ.0) THEN
        DO 20  LAY = 1, MAHO
          PF1(LAY) = 0.0
          FM1(LAY) = 0.0
          PF2(LAY) = 0.0
          FM2(LAY) = 0.0
          THETIM(LAY) = 0.0
   20   CONTINUE
        CALL JMPLBL(SWA,FILNAM,LOGF,'SWCRACK')
      ENDIF

C --- flow through soil cracks
      CALL RSINTR (SWA,FILNAM,LOGF,'SWCRACK',0,1,SWCRACK)
      IF (SWCRACK.EQ.1) THEN
        CALL RSREAR (SWA,FILNAM,LOGF,'SHRINA',0.0,2.0,SHRINA)
        CALL RSREAR (SWA,FILNAM,LOGF,'MOISR1',0.0,5.0,MOISR1)
        CALL RSREAR (SWA,FILNAM,LOGF,'MOISRD',0.0,1.0,MOISRD)
        CALL RSREAR (SWA,FILNAM,LOGF,'ZNCRACK',-100.0,0.0,ZNCRACK)
        CALL RSREAR (SWA,FILNAM,LOGF,'GEOMF',0.0,100.0,GEOMF)
        CALL RSREAR (SWA,FILNAM,LOGF,'DIAMPOL',0.0,100.0,DIAMPOL)
        CALL RSREAR (SWA,FILNAM,LOGF,'RAPCOEF',0.0,10000.0,RAPCOEF)
        CALL RSREAR (SWA,FILNAM,LOGF,'DIFDES',0.0,10000.0,DIFDES)
        CALL RFREAR (SWA,FILNAM,LOGF,'THETCR',0.0,1.0,THETCR,MAHO,
     &  NUMLAY)
      ELSEIF (SWCRACK.eq.0) THEN
        SHRINA = 0.0
        MOISR1 = 0.0
        MOISRD = 0.0
        ZNCRACK = 0.0
        GEOMF = 0.0
        DIAMPOL = 0.0
        RAPCOEF = 0.0
        DIFDES = 0.0
        CALL JMPLBL(SWA,FILNAM,LOGF,'SWDIVD')
      END IF

C --- fate of discharge water in a regional system
      CALL RSINTR (SWA,FILNAM,LOGF,'SWDIVD',0,1,SWDIVD)
      IF (SWDIVD.EQ.1) THEN
        CALL RFREAR (SWA,FILNAM,LOGF,'COFANI',0.0,1000.0,COFANI,MAHO,
     &  NUMLAY)
      ELSE
        CALL JMPLBL(SWA,FILNAM,LOGF,'SWINCO')
      ENDIF

C --- initial water conditions
      CALL RSINTR (SWA,FILNAM,LOGF,'SWINCO',1,2,SWINCO)
      IF (SWINCO.EQ.1) THEN
        CALL RFDOUR (SWA,FILNAM,LOGF,'HI',-1.0D10,1.0D4,HI,MACP,NUMNOD)
      ELSEIF (SWINCO.EQ.2) THEN
        CALL JMPLBL(SWA,FILNAM,LOGF,'GWLI')
        CALL RSREAR (SWA,FILNAM,LOGF,'GWLI',-5000.0,100.0,GWLI)
      ENDIF

      CLOSE (SWA)

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE REDUCEVA (SWREDU,REVA,PEVA,DAYNR,DAYSTA,NRAI,
     &                     NIRD,RUNNR,ISEQ,COFRED,RSIGNI)
C ----------------------------------------------------------------------
C     Date               : 18/08/98                                         
C     Purpose            : calculates reduction of soil evaporation
C     Subroutines called : -                                           
C     Functions called   : -                                     
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE

C --- global
      INTEGER SWREDU,DAYNR,DAYSTA,RUNNR,ISEQ

      REAL    REVA,PEVA,NRAI,NIRD,COFRED, RSIGNI
C ----------------------------------------------------------------------
C --- local
      REAL    ldwet,spev,saev,saevm1

      SAVE
C ----------------------------------------------------------------------
      if (swredu.eq.0) then
C ---   no reduction ---
        reva = peva
      elseif (swredu.eq.1) then
C ---   reduction with Black model ---
        if (daynr.eq.daysta .and. (runnr.eq.1.or.iseq.eq.0)
     &      .or. (nrai+nird) .gt. RSIGNI) ldwet = 0.0
        ldwet = ldwet + 1.0
        reva  = COFRED * (sqrt(ldwet)-sqrt(ldwet-1.0))
        reva  = min(reva,peva)
      elseif (swredu.eq.2) then
C ---   reduction with Boesten and Stroosnijder model ---
        if (daynr.eq.daysta .and. (runnr.eq.1.or.iseq.eq.0)
     &      .or. (nrai+nird) .gt. RSIGNI) then
          spev = 0.0
          saev = 0.0
        endif
        if ((nrai+nird) .lt. peva) then
          spev = spev + (peva - (nrai+nird))
          saevm1 = saev
          if (spev .lt. COFRED**2) then
            saev = spev
          else
            saev = COFRED * sqrt(spev)
          endif
          reva = nrai + nird + saev - saevm1
        else
          reva = peva
          saev = max (0.0,saev - (nrai+nird-peva))
          if (saev .lt. (COFRED**2)) then
            spev = saev
          else
            spev = (saev/COFRED)**2
          endif
        endif
      endif

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE ROOTEX (NUMNOD,QROT,DRZ,DZ,PTRA,Z,HLIM3H,HLIM3L,HLIM4,
     & HLIM2U,H,CML,BOTCOM,HLIM2L,HLIM1,ADCRL,ADCRH,ATMDEM,
     & RDCTAB,RDM,SWSOLU,ECMAX,ECSLOP,LAYER,THETSL,THETA,QROSUM)
C ----------------------------------------------------------------------
C     Date               : 06/11/95                                          
C     Purpose            : calculates the root extraction rates (as a
C                          function of press. head) for each nodal point
C     Subroutines called : -                                           
C     Functions called   : AFGEN                                       
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'
C --- global
      INTEGER NUMNOD,BOTCOM(MAHO),SWSOLU,LAYER(MACP)

      REAL    QROT(MACP),DRZ,DZ(MACP),PTRA,Z(MACP),CML(MACP),RDCTAB(22)
      REAL    HLIM3H,HLIM3L,HLIM4,HLIM2U,HLIM2L,ECMAX,ECSLOP,RDM
      REAL    ADCRH,ADCRL,ATMDEM,HLIM1,HLIM2,HLIM3,AFGEN,QROSUM

      REAL*8  H(MACP),THETA(MACP),THETSL(MAHO)
C ----------------------------------------------------------------------
C --- local
      INTEGER node,noddrz,lay

      REAL    depth,SMEAN,top,bot,mid,lam,lam1,lam2,lam3,alpsol,alpwat
      REAL    ECsat
C ----------------------------------------------------------------------
C --- clean rtex-array
      do 10 node = 1,numnod
        qrot(node) = 0.0
10    continue
      QROSUM = 0.0

C --- skip routine if there are no roots
      if (drz.gt.-1.e-3) goto 500

C --- determine lowest compartment containing roots
      depth = 0.0
      do 20 node = 1,numnod
        noddrz = node
        depth  = depth - dz(node)
        if (drz.ge.depth-1.0e-6) goto 30
20    continue

30    SMEAN = ptra/abs(drz)

C --- calculate root extraction of the compartments
      do 100 node = 1,noddrz
        top = abs(z(node) + 0.5*dz(node))
        mid = abs(z(node))
        bot = abs(z(node) - 0.5*dz(node))
        if (z(node)- 0.5*dz(node).lt.drz) bot = abs(drz)
        if (abs(drz).lt.rdm .and. noddrz .lt. 8) then
          qrot(node) = SMEAN*(bot-top) 
        else
          lam1 = AFGEN (RDCTAB,22,top/abs(drz))
          lam2 = AFGEN (RDCTAB,22,mid/abs(drz))
          lam3 = AFGEN (RDCTAB,22,bot/abs(drz))
          lam  = (lam1+lam2+lam3)/3
          qrot(node) = SMEAN*(bot-top)*lam
        endif 
100   continue

C --- calculating critical point hlim3 according to Feddes
      hlim3=hlim3h
      if (ATMDEM.ge.ADCRL) then
        if (ATMDEM.le.ADCRH) hlim3=hlim3h+((ADCRH-ATMDEM)/(ADCRH-ADCRL))
     &  *(hlim3l-hlim3h)
      else
        hlim3 = hlim3l
      endif

C --- calculation of transpiration reduction
      hlim2 = hlim2u
      do 200 node = 1,noddrz
        alpwat = 1.0
        alpsol = 1.0

C ---   reduction due to water stress
        if (node.gt.botcom(1)) hlim2=hlim2l
C ---   waterstress/ wet circumstances
        if (h(node).le.hlim1.and.h(node).gt.hlim2) 
     &    alpwat = real((hlim1-h(node))/(hlim1-hlim2))
C ---   waterstress/ dry circumstances
        if (h(node).le.hlim3.and.h(node).ge.hlim4) 
     &    alpwat = real((hlim4-h(node))/(hlim4-hlim3))
C ---   no transpiration 
        if (h(node).gt.hlim1.or.h(node).lt.hlim4)
     &    alpwat = 0.0

C ---   reduction due to salt stress
        if (SWSOLU.EQ.1) then
          lay = layer(node)
CPD       conversion factor from mg/cm3 to EC
CPD       1 dS/m = 640 * mg/l
CPD       1 dS/m = 0.64 * mg/cm3
CPD       1 mg/cm3 = 1/0.64 = 1.56 dS/m
CPD       SWAP uses 1.492
          ECsat = real(1.492*cml(node)*theta(node)/thetsl(lay))
          if (ECsat .lt. ECmax) then
            alpsol = 1.0
          else
            alpsol = (100. - (ECsat - ECmax)*ECSLOP) / 100.
            alpsol = max(0.0,alpsol)
          endif
        endif

        qrot(node) = qrot(node)*alpwat*alpsol
        QROSUM = qrot(node) + QROSUM
200   continue

500   return
      end

C ----------------------------------------------------------------------
      SUBROUTINE SLTBAL (DT,NIRD,CIRR,ARFLUX,CPRE,QBOT,CDRAIN,CML,
     &     NUMNOD,QDRTOT,RAPDRA,CRACKC,SQBOT,SQSUR,SQRAP,SQPREC,SQIRRIG)
C ----------------------------------------------------------------------
C     Date               : 18/08/97                   
C     Purpose            : calculation of solute balance           
C     Subroutines called : -                                           
C     Functions called   : -                                           
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'
  
C --- global
      INTEGER NUMNOD

      REAL    DT,NIRD,CIRR,ARFLUX,CPRE,QBOT,CDRAIN,CML(MACP),QDRTOT
      REAL    RAPDRA,CRACKC,SQBOT,SQSUR,SQRAP,SQPREC,SQIRRIG

C ----------------------------------------------------------------------
C --- add time step fluxes to total cumulative values

      sqprec = sqprec + arflux*cpre*dt
      sqirrig = sqirrig + nird*cirr*dt

      if (qbot .gt. 0.0) then
        sqbot = sqbot + qbot*cdrain*dt
      else 
        sqbot = sqbot + qbot*cml(numnod)*dt
      endif

      sqrap = sqrap + rapdra*crackc*dt
      sqsur = sqsur + qdrtot*cdrain*dt

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE SOILTMP (NUMNOD,THETA,THETM1,THETAS,TAV,SWSHF,
     & TEMP,DZ,DISNOD,DT,TAMPLI,TMEAN,DDAMP,TIMREF,DAYNR,Z,
     & FQUARTZ,FCLAY,FORG)
C ----------------------------------------------------------------------
C     Date               : 15/10//97
C     Purpose            : calc. soil temperature profile          
C     Subroutines called : -        
C     Functions called   : -
C     File usage         : -
C ----------------------------------------------------------------------
      IMPLICIT NONE 
      INCLUDE 'PARAM.FI'

      INTEGER I,NODE,NUMNOD,DAYNR,SWSHF

      REAL   DISNOD(MACP+1),DT,DZ(MACP),TAV,TAMPLI,TMEAN,DDAMP,TIMREF
      REAL   Z(MACP),FCLAY(MACP),FQUARTZ(MACP),FORG(MACP)

      REAL*8 THETA(MACP),THETM1(MACP),HEACAP(MACP),THETAS(MACP)
      REAL*8 HEACND(MACP),HEACON(MACP),TEMP(MACP),TMPOLD(MACP)
      REAL*8 QHBOT,THEAVE(MACP)
      REAL*8 thoma(MACP),thomb(MACP),thomc(MACP),thomf(MACP)

C ----------------------------------------------------------------------
 
C --- save old temperature profile
      do 10 node = 1,numnod
10    TMPOLD(node) = temp(node)

      if (SWSHF .eq. 2) then

C --- compute heat conductivity and capacity ---------------------------

        do 110 node = 1,numnod
110     THEAVE(node) = 0.5 * (theta(node) + thetm1(node))

C --- calculate nodal heat capacity and thermal conductivity 
        CALL DEVRIES(NUMNOD,THEAVE,THETAS,HEACAP,HEACND,FQUARTZ,
     &        FCLAY,FORG)
        HEACON(1) = HEACND(1)
        do 130 node = 2,numnod
130     HEACON(node) = 0.5 * (HEACND(node) + HEACND(node-1))

C --- Calculate new temperature profile --------------------------------

C ---   no heat flow through bottom of profile assumed
        qhbot = 0.0

C ---   calculation of coefficients for node = 1
        I = 1
C ---   temperature fixed at soil surface
        THOMA(I) = - DT * HEACON(I) / (DZ(I) * DISNOD(I))
        THOMC(I) = - DT * HEACON(I+1) / (DZ(I) * DISNOD(I+1))
        THOMB(I) = HEACAP(I) - THOMA(I) - THOMC(I)
        THOMF(I) = HEACAP(I) * TMPOLD(I) - THOMA(I) * TAV

C ---   calculation of coefficients for 2 < node < numnod
	  DO 500 I = 2,NUMNOD-1 
          THOMA(I) = - DT * HEACON(I) / (DZ(I) * DISNOD(I))
          THOMC(I) = - DT * HEACON(I+1) / (DZ(I) * DISNOD(I+1))
          THOMB(I) = HEACAP(I) - THOMA(I) - THOMC(I)
          THOMF(I) = HEACAP(I) * TMPOLD(I)
500     CONTINUE

C ---   calculation of coefficients for node = numnod
        I = NUMNOD
        THOMA(I) = - DT * HEACON(I) / (DZ(I) * DISNOD(I))
        THOMB(I) = HEACAP(I) - THOMA(I)
        THOMF(I) = HEACAP(I) * TMPOLD(I) - (QHBOT * DT)/DZ(I)

C ---   solve for vector temp a tridiagonal linear set
        Call TriDag (Numnod, thoma, thomb, thomc, thomf, Temp)

      else

c ---   analytical solution temperature profile ---
        do 540 i = 1,numnod
          temp(i) = tmean + tampli*(sin(0.0172*(daynr-timref+91.) +
     &              z(i)/ddamp)) / exp(-z(i)/ddamp)
 540    continue

      endif
      
      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE SOLUTE (CPRE,NIRD,CIRR,DT,NUMNOD,LAYER,INPOLA,
     & INPOLB,CML,THETA,DDIF,LDIS,Q,DISNOD,THETSL,
     & Z,GAMPAR,RTHETA,BEXP,DECPOT,FDEPTH,KF,FREXP,FMOBIL,
     & TSCF,QROT,DZ,KMOBIL,CIL,QDRA,CMSY,THETIM,CISY,CL,DTSOLU,
     & DTMAX,TEMP,CPOND,PONDM1,QTOP,WTOPLAT,ACRACK,ADSFLU,CRACKC,
     & ARFLUX,SWCRACK,CRACKW,CKWM1,RAPDRA,QCRACK,POND,CREF,
     & QDRTOT,POROS,KFSAT,DECSAT,CDRAIN,HAQUIF,DECTOT,SAMPRO,SAMCRA,
     & SAMAQ,CRALEV,DIFDES,ROTTOT,SQDRA,SWBR,SDRAIN,BDENS)
C ----------------------------------------------------------------------
C     Date               : 18/08/98             
C     Purpose            : calculation of solute concentrations           
C     Subroutines called : -                                           
C     Functions called   : -                                           
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

C --- global
      INTEGER NUMNOD,LAYER(MACP),SWCRACK,SWBR

      REAL    CPRE,NIRD,CIRR,DT,INPOLA(MACP),INPOLB(MACP),CML(MACP)
      REAL    DDIF,LDIS,DISNOD(MACP+1),Z(MACP)
      REAL    GAMPAR,RTHETA,BEXP,DECPOT,FDEPTH(MAHO),KF,FREXP
      REAL    FMOBIL(MACP),TSCF,QROT(MACP),DZ(MACP),KMOBIL,CIL(MACP)
      REAL    QDRA(5,MACP),ARFLUX,BDENS(MAHO)
      REAL    CMSY(MACP),CISY(MACP),CL(MACP),DTSOLU,DTMAX,CREF
      REAL    CPOND,PONDM1,QTOP,WTOPLAT,ACRACK,ADSFLU(MACP),CRACKC
      REAL    CRACKW,CKWM1,RAPDRA,QCRACK,POND,QDRTOT,POROS,KFSAT
      REAL    DECSAT,CDRAIN,HAQUIF,DECTOT,CRALEV,DIFDES,ROTTOT
      REAL    SAMAQ,SAMCRA,SAMPRO,SQDRA,SDRAIN

      REAL*8  THETA(MACP),Q(MACP+1),THETIM(MAHO),TEMP(MACP)
      REAL*8  THETSL(MAHO)

      LOGICAL differ
C ----------------------------------------------------------------------
C --- local
      INTEGER level,lay,i 

      REAL    cmlav,thetav,ftemp,ftheta,decact,cfluxt,cfluxb
      REAL    cdrtot,ctrans,cdiff,crot,dispr,diffus,old,dummy,rer
      REAL    in,vpore,desflu(MACP+1),deswat,desconc,destot,isqdra
      REAL    samount
C ----------------------------------------------------------------------
      parameter (rer = 0.001)
      save      destot

      isqdra  = 0.0
      samount = 0.0
 
C --- flux at surface      
      if (qtop.lt.-1.e-6) then
        cpond = ((NIRD*cirr + ARFLUX*cpre)*dt +pondm1*cpond)/
     &          (pond-qtop*dt+wtoplat)
        cfluxt = qtop*(1.0-acrack)*cpond*dt
      else
        cpond = 0.0
        cfluxt = 0.0
      endif

C --- solute balance in cracks
      if (SWCRACK.EQ.1) then
        in = wtoplat*cpond + ARFLUX*acrack*cpre*dt + destot
        if (crackw.gt.1.0e-5) then
          crackc = (crackc*ckwm1 + in)/(crackw+(rapdra+qcrack)*dt)
        else
          crackc = 0.0
        endif
      endif

C --- Flux and concentration of water flowing through clay cracks
      if (SWCRACK.EQ.1) then
        destot = 0.0
        deswat = wtoplat + arflux*acrack*dt
        if (deswat .gt. 1.e-7) then
          desconc = (wtoplat*cpond + arflux*acrack*cpre*dt) / deswat
        else
          desconc = 0.0
        endif
      endif

C --- Start loop of calculations per compartment

      do  500 i = 1,numnod
        lay = layer(i)

C --- Mobile phase -----------------------------------------------------

C ---   mass exchanged between compartments 
          if (i .lt. numnod) then
            cmlav  = inpola(i+1) * cml(i) + inpolb(i) * cml(i+1)
            thetav = real(inpola(i+1)*theta(i)+inpolb(i)* theta(i+1))
            vpore  = real(abs(q(i+1))/thetav)
            diffus = real(ddif*(thetav**2.33)/(thetsl(lay)*thetsl(lay)))
            dispr  = diffus + ldis * vpore + 0.5 * dt * vpore * vpore
            cfluxb = (real(q(i+1)*cmlav +thetav * dispr 
     &               * (cml(i+1)-cml(i)) / disnod(i+1)))*dt
        else
          if (q(i+1).gt.0.0) then
            cfluxb = real(q(i+1)*cdrain*dt)
          else
            cfluxb = real(q(i+1)*cml(i)*dt)
          endif
        endif

C ---   transformation of the substance
        ftemp  = real(exp(gampar*(temp(i)-20.0d0)))
        ftheta = min(1.0,(real(theta(i))/rtheta)**bexp)
        decact = decpot*ftemp*ftheta*fdepth(lay)
        ctrans = real(decact*theta(i)*cml(i) + decact*bdens(lay)
     &           *fmobil(i)*kf*cref*((cml(i)/cref)**frexp))
        dectot = dectot + ctrans*dt*dz(i)
        
C ---   plant uptake and diffusion between mobile and immobile region
        crot = tscf*qrot(i)*cml(i)/dz(i)
        rottot = rottot + tscf*qrot(i)*cml(i)*dt
        if (fmobil(i).lt.0.99) then
          cdiff = kmobil*(cml(i)-cil(i))
        else
          cdiff = 0.0
        endif

C ---   lateral drainage
        cdrtot = 0.0
        do 100 level = 1,5
	    if (qdra(level,i) .gt. 0.0) then
          cdrtot = cdrtot + qdra(level,i)*cml(i)/dz(i)
	    else
          cdrtot = cdrtot + qdra(level,i)*cdrain/dz(i)
	    endif
100     continue
C ---   cumulative amount of solutes to lateral drainage
        isqdra  = isqdra + cdrtot*dz(i)
        sqdra   = sqdra + cdrtot*dz(i)*dt 
        samount = samount + cdrtot*dz(i)

C ---   desorption flux of water flowing through cracks
        if ((SWCRACK.EQ.1) .and. z(i) .gt. cralev) then
          desflu(i) = deswat * (cml(i) - desconc) * difdes * dz(i)
          destot = destot + desflu(i)
        else
          desflu(i) = 0.0
        endif

C ---   conservation equation for the substance
        cmsy(i) = cmsy(i)+(cfluxb-cfluxt-desflu(i))/dz(i)+
     &            (-ctrans-crot-cdrtot-cdiff)*dt +
     &            adsflu(i) * crackc * dt / dz(i)

C ---   iteration procedure for calculation of cml
        differ = .true.
        if (cmsy(i).lt.1.e-6) then
          cmsy(i) = 0.0
          cml(i)  = 0.0
        else
          if (abs(frexp-1.0).lt.0.001) then
            cml(i) = real(cmsy(i)/(theta(i)+bdens(lay)*kf*fmobil(i)))
          else 
            if (cml(i).lt.1.e-6) cml(i) = 1.e-6
200         if (differ) then
              old    = cml(i)
              dummy  = bdens(lay)*kf*(cml(i)/cref)**(frexp-1.0)
              cml(i) = real(cmsy(i)/(theta(i)+dummy*fmobil(i)))
              if (abs(cml(i)-old).lt.rer*cml(i)) differ = .false.
              goto 200
            endif
          endif
        endif

C --- Immobile phase ---------------------------------------------------

        if (fmobil(i).lt.0.99) then

C ---     transformation of the substance
          ctrans = real(decact*(1.0-fmobil(i))*(thetim(lay)*cil(i)+
     &             bdens(lay)*kf*cref*(cil(i)/cref)**frexp))
          dectot = dectot + ctrans*dt*dz(i)

C ---     conservation equation for the substance
          cisy(i) = cisy(i)+(-ctrans+cdiff)*dt

C ---     iteration procedure for calculation of cil
          differ = .true.
          if (cisy(i).lt.1.e-6) then
            cisy(i) = 0.0
            cil(i)  = 0.0
          else
            if (abs(frexp-1.0).lt.0.001) then
              cil(i) = real(cisy(i) / (thetim(lay) + bdens(lay)*kf) /
     &                 (1.0-fmobil(i)))
            else
              if (cil(i).lt.1.e-6) cil(i) = 1.e-6
300           if (differ) then
                old    = cil(i)
                dummy  = bdens(lay)*kf*(cil(i)/cref)**(frexp-1.0)
                cil(i) = real(cisy(i)/(thetim(lay)+dummy)/(1.0-
     &                   fmobil(i)))
                if (abs(cil(i)-old).lt.rer*cil(i)) differ = .false.
                goto 300
              endif
            endif
          endif
        endif

C ---   mean solute concentration in liquid
        cl(i)  = real((theta(i)*cml(i)+thetim(lay)*(1.0-fmobil(i))
     &           *cil(i))/(theta(i)+thetim(lay)*(1.0-fmobil(i))))
        cfluxt = cfluxb

C --- next compartment...
  500 continue

C --- solute balance in aquifer for breakthrough curve
      if (swbr .eq. 1) then
        if (qdrtot .gt. 0.0) then
          cdrain = cdrain + dt/(poros + bdens(layer(numnod))*kfsat) * 
     &           ( (isqdra - qdrtot*cdrain)/haquif -
     &           decsat*cdrain*(poros + bdens(layer(numnod))*kfsat) )
	  else
          cdrain = cdrain + dt/(poros + bdens(layer(numnod))*kfsat) * 
     &           ( isqdra/haquif -
     &           decsat*cdrain*(poros + bdens(layer(numnod))*kfsat) )
	  endif
	endif

C --- concentration of drainage water if DIVDRA = 1
      if (qdrtot.gt.1.e-6) then
        sdrain = samount/qdrtot
      else
        sdrain = 0.0
      endif

C --- total solute amounts for balance
      sampro = 0.0
      do 520 i = 1,numnod
        sampro = sampro + (cmsy(i) + cisy(i)) * dz(i)
 520  continue
      samcra = crackw*crackc
      samaq = cdrain*poros*haquif

C --- determine maximum timestep
      dtsolu = dtmax
      do 550 i = 1,numnod
        diffus = real(ddif * (thetav**2.33) / (thetsl(lay)*thetsl(lay)))
        dispr  = real(diffus+ldis*abs(q(i))/theta(i))
        if (dispr.lt.1.0e-8) dispr = 1.0e-8
        dummy  = real(dz(i)*dz(i)*theta(i)/2.0/dispr)
        dtsolu = min(dtsolu,dummy)
550   continue

      dtsolu = max(0.001, dtsolu)
      
      return
      end

C-----------------------------------------------------------------------
      REAL*8 FUNCTION THENODE (NODE,HEAD,LAYER,FLGENU,COFGEN,
     & HTABLE,THETLO,ALFAMG,THETAR,THETAS)
C ----------------------------------------------------------------------
C     Date               : 29/08/95                                           
C     Purpose            : calc. water content at nodal point NODE from
C                          pressure head HEAD
C     Subroutines called : -                                          
C     Functions called   : -                                           
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

C --- global 
      INTEGER NODE,LAYER(MACP),THETLO(MAHO)

      REAL*8  HEAD,COFGEN(8,MAHO),HTABLE(MAHO,99)
      REAL*8  ALFAMG(MACP),THETAR(MACP),THETAS(MACP)

      LOGICAL FLGENU(MAHO)

C ----------------------------------------------------------------------
C --- local

      INTEGER lay,posit

      REAL*8  help
C ----------------------------------------------------------------------

C --- soil layer of the node
      lay = layer(node)

      if (head.ge.-1.0d-2) then
C ---   saturated moisture content
        thenode = thetas(node)
      else
        if (flgenu(lay)) then
C ---     soil physical data presented according to Van Genuchten
C ---     first compute |alpha * h| ** n
          help = (abs(alfamg(node)*head))**cofgen(6,lay)
C ---     add 1 and raise to the power m
          help = (1.0d0 + help) ** cofgen(7,lay)
C ---     now compute theta
          thenode = thetar(node)+(thetas(node)-thetar(node))/help    
        else
C ---     soil physical data presented in a table
          if (head.le.htable(lay,thetlo(lay))) then
C ---       h is below lowest value of table
            thenode = (0.01d0 * thetlo(lay))
          else
            posit   = thetlo(lay)
100         posit   = posit+1
            if (head.gt.htable(lay,posit)) goto 100
C ---       linear interpolation between water contents
            thenode = 0.01d0*((posit-1)+(head-htable(lay,posit-1))/
     $                (htable(lay,posit)-htable(lay,posit-1)))
          endif
        end if
      end if

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE TOTASS (IDAY,DAYL,AMAX,EFF,LAI,KDIF,AVRAD,
     $SINLD,COSLD,DTGA)
C ----------------------------------------------------------------------
C --- Author: Daniel van Kraalingen, 1986
C --- Calculates daily total gross assimilation (DTGA) by performing
C --- a Gaussian integration over time. At three different times of 
C --- the day, irradiance is computed and used to calculate the instan- 
C --- taneous canopy assimilation, whereafter integration takes place.
C --- more information on this routine is given by Spitters et al./1988
C --- Subroutines and functions called: ASSIM, RADIAT
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER I,IDAY

      REAL    LAI,KDIF
      REAL    AMAX,AVRAD,COSLD,DAYL,DTGA,EFF,FGROS,GAUSR,HOUR,PARDIF
      REAL    PARDIR,SINB,SINLD

      DATA    GAUSR /0.3872983/
C ----------------------------------------------------------------------
C --- three point gaussian integration over day
      DTGA  = 0.
      IF (AMAX.LT.1.0E-10) GOTO 20
      DO 10 I=1,3
        HOUR = 12.0+DAYL*0.5*(0.5+(I-2)*GAUSR)
C --- at a specified hour, diffuse and direct irradiance is computed
        CALL RADIAT (IDAY,HOUR,DAYL,SINLD,COSLD,AVRAD,SINB,PARDIR,
     $              PARDIF)
C --- irradiance and crop properties determine assimilation
        CALL ASSIM (AMAX,EFF,LAI,KDIF,SINB,PARDIR,PARDIF,FGROS)
        IF(I.EQ.2) FGROS=FGROS*1.6
        DTGA = DTGA+FGROS
10    CONTINUE
      DTGA  =DTGA*DAYL/3.6

20    RETURN
      END


************************************************************************
** Subroutine: Tridag                                           *
** Purpose:    Solves for a vector U a tridiagonal linear set.             *
** References:                                                         *
** Press, W.H., B.P. Flannery, S.A. Teukolsky & W.T. Vetterling, 1989. *
** Numerical Recipes in FORTRAN. Cambridge University Press, New York. *
** pp 40-41                                                           *
************************************************************************
** Input:       N -      Number of equations                            *
**            A, B, C - Coefficients of the matrix                       *
**            R -      known vector                               *
** Output:      U -      solved vector                               *
************************************************************************
** Called by: HeadCalc and Scheme2                                     *
************************************************************************
** Version: 1.0                                                        *
** Date:    14-Oct-1994                                               *
** Author:  E.Moors                                                    *
************************************************************************

      Subroutine Tridag (N, A, B, C, R, U)

***** Variable declaration *********************************************

      IMPLICIT NONE 

*     (i) Global declarations                                          *
*     (i.i) Input                                                      *
      Integer      N
      Real*8      A(N), B(N), C(N), R(N)
*     (i.ii) Output                                                    *
      Real*8    U(N)
*     (ii) Parameters                                                  *
      Integer      NMax
      Real      Zero
      Parameter (NMax = 100, Zero = 0.3e-37)
*     (iii) Local declarations                                         *
      Integer   I
      Real*8      Gamma(NMax), Beta, Small
***** End of variable declaration **************************************

      Small = Dble(Zero)

*     (1) If B(1)=0 then rewrite the equations as a set of order N-1
*     to eliminate U(2)
      If (Abs(B(1)).LT.Small) Then
       Write(*,*) ' Coefficient B(1) = 0.'
       Pause
      End If

*     (2) Decomposition and forward substitution
      Beta = B(1)
      U(1) = R(1) / Beta
      Do I = 2, N
        Gamma(I) = C(I-1) / Beta
        Beta = B(I) - A(I)*Gamma(I)
*     (2.1) If Beta=0 then go to another algorithm including
*     elimination with pivoting
        If (Abs(Beta).LT.Small) Then
          Write(*,*) ' Algoritm fails!'
          Pause
        End If
        U(I) = (R(I) - A(I)*U(I-1)) / Beta
      End Do

*     (3) Back substitution
      Do I = N-1, 1, -1
       U(I) = U(I) - Gamma(I+1)*U(I+1)
      End Do

      Return
      End

C ----------------------------------------------------------------------
      SUBROUTINE UPDATE (NUMNOD,LAYER,H,HM1,INDEKS,TAU,FLGENU,COFGEN,
     & THETAR,THETAS,ALFAMG,THETLO,THETHI,DMCH,DMCC,DIMOCA,
     & SWMOBI,FM1,PF1,SLOPFM,HTABLE,THETA)
C ----------------------------------------------------------------------
C     Date               : 19/07/96    
C     Purpose            : to check for hysteretic reversal and update      
C                          model parameters            
C     Subroutines called : -                                           
C     Functions called   : DMCNODE               
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'
C --- global
      INTEGER  NUMNOD,LAYER(MACP),INDEKS(MACP),THETLO(MAHO),THETHI(MAHO)
      INTEGER  SWMOBI       
      REAL     FM1(MAHO),PF1(MAHO),SLOPFM(MAHO)

      REAL*8  H(MACP),HM1(MACP),TAU,THETAR(MACP),THETAS(MACP)
      REAL*8  THETA(MACP)  
      REAL*8  COFGEN(8,MAHO),ALFAMG(MACP),WCN
      REAL*8  DMCC(MAHO,99),DMCH(MAHO,99),DIMOCA(MACP),HTABLE(MAHO,99)

      LOGICAL FLGENU(MAHO)
C ----------------------------------------------------------------------
C --- local
      INTEGER node,lay,indtem(MACP)

      REAL*8  dmcnode,delp,sew,sed
C ----------------------------------------------------------------------

C --- check for reversal
      do 50 node = 1,numnod
        delp = hm1(node)-h(node)
        if (delp/float(indeks(node)).gt.tau.and.
     &     h(node).lt.-10.0d0 .and. h(node).gt.-1.0d3) then
          indtem(node) = -indeks(node)
        else
          indtem(node) = indeks(node)
        endif
50    continue

      do 60 node = 2,numnod-2
        if (indtem(node).ne.indtem(node-1).and.
     &      indtem(node).ne.indtem(node+1).and.
     &      indtem(node).ne.indtem(node+2)) indtem(node)=-indtem(node)
60    continue

C --- change parameters scanning curves
      do 100 node = 1,numnod
        if (indtem(node).eq.indeks(node)) goto 100
        lay = layer(node)

C ---   wcn is water content at reversal point
        sew = (1.0d0+(cofgen(8,lay)*(-h(node)))**cofgen(6,lay))
     &        **(-cofgen(7,lay)) 
        sed = (1.0d0+(cofgen(4,lay)*(-h(node)))**cofgen(6,lay))
     &        **(-cofgen(7,lay))

        if (indeks(node).eq.1) then
          wcn = thetar(node)+(thetas(node)-thetar(node))*sew
        else
          wcn = thetar(node)+(thetas(node)-thetar(node))*sed
        endif 

C ---   change index
        indeks(node) = -1*indeks(node)

C ---   update alfa, thetar and thetas
        if (indeks(node).eq.1) then
C ---     wetting branch
          alfamg(node) = cofgen(8,lay)
          thetas(node) = cofgen(2,lay)
          if (sew.lt.0.995d0) then
            thetar(node) = (wcn-cofgen(2,lay)*sew)/(1.0d0-sew)
          endif
        else
C ---     drying branch
          alfamg(node) = cofgen(4,lay)
          thetar(node) = cofgen(1,lay)
          thetas(node) = cofgen(1,lay)+(wcn-cofgen(1,lay))/sed
        endif

C ---   update capacity 
        dimoca(node) = dmcnode(node,h(node),LAYER,FLGENU,COFGEN,THETLO,
     &                 THETHI,DMCH,DMCC,THETAS,THETAR,ALFAMG,
     &                 SWMOBI,FM1,PF1,SLOPFM,HTABLE,THETA)

100   continue

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE WATCON (VOLM1,VOLACT,NUMNOD,THETA,DZ,FMOBIL,LAYER,
     & THETIM,SWCRACK,CKWM1,CRACKW,WTOPLAT,QCRACK,ARFLUX,NIRD,ACRACK,
     & RAPDRA,DT) 
C ----------------------------------------------------------------------
C     Date               : 15/09/97                                            
C     Purpose            : calc. water storage in the soil profile        
C     Subroutines called : -                                           
C     Functions called   : -                                           
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

C --- global
      INTEGER NUMNOD,LAYER(MACP),SWCRACK

      REAL    DZ(MACP),FMOBIL(MACP),CKWM1,CRACKW,WTOPLAT,QCRACK,ARFLUX
      REAL    ACRACK,RAPDRA,DT,NIRD
      REAL*8  THETA(MACP),VOLM1,VOLACT,THETIM(MAHO)
C ----------------------------------------------------------------------
C --- local
      INTEGER i,lay
C ----------------------------------------------------------------------

c ---  change of water storage in cracks
       if (SWCRACK.EQ.1) then
         ckwm1 = crackw
         crackw = crackw + wtoplat + 
     &            ((arflux+nird)*acrack - qcrack - rapdra) * dt
         crackw = max (0.0, crackw)
       endif

c --- update soil profile water storage
      volm1  = volact
      volact = 0.0
      do 10 i = 1,numnod
        lay    = layer(i)
        volact = volact+real(theta(i)+(1.0-fmobil(i))*thetim(lay))*dz(i)
10    continue

      return
      end

C ----------------------------------------------------------------------
      subroutine wballev (wls,t,wlstab,wst,
     & sttab,dt,runots,rapdra,qdrd,cqdrd,cwsupp,cwout,WLSOLD)
C ----------------------------------------------------------------------
C     Date               : 05/06/98                         
C     Purpose            : close surface water balance using 
C                          given (input) surface water levels   

C --- Compare storage at T + drainage fluxes with storage at T+DT
C --- The difference will be either discharge or supply
C --- Update totals (of discharge, supply and qdrd)

C     Subroutines called :                          
C     Functions called   : wstlev                          
C     File usage         :        
C ----------------------------------------------------------------------
      IMPLICIT NONE
	
      INCLUDE 'PARAM.FI' 

C --- global
      REAL    wls,t,wlstab(2*MAWLS)
      REAL    wst,sttab(22,2),dt,runots,rapdra,qdrd,cqdrd,cwsupp
      REAL    cwout,AFGEN

C --- local
      REAL    wlsold,wstold,wstrest,wdis,wsupp,wstlev

C ----------------------------------------------------------------------
C --- wlsold gets w-level of previous time step
       wlsold = wls

C --- fetch new level from input series
       wls = AFGEN (WLSTAB,2*MAWLS,T+DT+1.0)

C --- determine surface water storage for level(t-dt) and level(t)
      wstold = wstlev(wlsold,sttab) 
      wst    = wstlev(wls,sttab)

C --- determine from the surface water storages and the qdrain whether
C --- supply has taken place during period (t)-(t+dt) or water has 
C --- been discharged
      wstrest = wstold + (qdrd + rapdra)*dt + runots - wst

C --- if supply was needed, set discharge to zero
      if (wstrest.le.0.0) then
        wdis  = 0.0
        wsupp = -wstrest/dt

C --- if discharge has taken place, set supply to zero
      else
        wdis  = wstrest/dt
        wsupp = 0.0
      endif

C --- cumulation of water balance terms
      cqdrd  = cqdrd  + qdrd*dt
      cwsupp = cwsupp + wsupp*dt
      cwout  = cwout  + wdis*dt

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE WLEVBAL (HLEVD,NRPRI,impend,nmper,swman,imper,
     & wlstar,wls,hbweir,gwl,wlsman,gwlcrit,nphase,dropr,sttab,wscap,
     & dt,runots,rapdra,wst,zbotdr,alphaw,betaw,qdrd,cqdrd,cwsupp,
     & cwout,wlsbak,osswlm, T,NUMNOD,THETAS,THETA,DZ,VCRIT,NODHD,HCRIT,
     & H,SWQHR,QQHTAB,HQHTAB,wldip,hwlman,vtair,overfl,numadj,intwl)
C ----------------------------------------------------------------------
C     Date               : 05/06/98                         
C     Purpose            : calculate surf. water level from water balance


C --- Set target level wlstar:
C --- SWMAN = 1: HBWEIR
C --- SWMAN = 2: from table (4e #2) and within adjustment period and 
C --- taking into account the maximum drop rate. 
C --- Calculate level for maximum supply wlstara (= wlstar-wldip)

C --- Calculate storage at wlstar and at wlstara
C ---   If wlstara is above deepest bottom level then water supply 
C ---   capacity is set to maximum value otherwise both wsttara and
C ---   wsmax are set to zero

C --- Calculate max. new storage: old + incoming/outgoing fluxes
C --- 1 System falls dry: set supply to maximum,
C       set wls at bottom of deepest channel
C --- 2 System will not become full: set supply to maximum
C       calculate new level from storage
C --- 3 System becomes full under maximum supply conditions,
C ---   Determine how, first without supply
C --- 3a wlstara cannot be reached: calculate required supply,
C ---    to reach wlstara and set wls to wlstara
C --- 3b system can be filled above wlstara, however no discharge:
C ---    wls is calculated from storage and is somewhere between
C ---    wlstar and wlstara, no supply, no discharge
C --- 3c wlstar can be reached :wsupp = 0;
C ---    Now check whether there are automatic weirs for keeping the 
C ---    level at target value or that the discharge relationship
C ---    determines new level:
C --- 3c1 SWMAN=2: calculate discharge
C ---     check whether there is enough discharge capacity:
C ---     in case SWQHR = 1: calculate discap
C ---     in case SWQHR = 2: find discap from table
C ---     if sufficient capacity wls = wlstar otherwise set overflow
C --- 3c2 SWMAN=1 or overflow
C ---     Calculate highest possible discharge, if still unsufficient 
C ---     to handle present drain fluxes: stop - system overflow
C ---     otherwise start iteration procedure to determine new level,
C ---     storage and discharge:
C ***********************************************
C --- Iteration Procedure:
C --- Establish lower and upper bounds: hbweir(imper) and +100cm
C --- Calculate storage and discharge for point halfway: wsti, wdisi
C --- Calculate new storage: if higher than wsti then adjust lower
C --- bound to point halfway otherwise adapt upper bound to point halfway
C --- Continue until upper and lower bounds converge (< 0.001 cm)   
C --- Ready: update wls, wst and wdis
C ***********************************************

C     Subroutines called :                          
C     Functions called   : wstlev                          
C     File usage         :        
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'

C --- global
      INTEGER impend(10),nmper,swman(10),nphase(10),NUMNOD
      INTEGER NODHD(10),SWQHR,NRPRI,NUMADJ,intwl(10)

      REAL    wlstar,hbweir(10),gwl,wlsman(10,10)
      REAL    dropr(10),sttab(22,2),wscap(10),dt,runots,rapdra
      REAL    wls,wst,osswlm,gwlcrit(10,10)
      REAL    zbotdr(5),alphaw(10),betaw(10),qdrd,cqdrd,cwsupp
      REAL    cwout,wlsbak(4),T,DZ(MACP),VCRIT(10,10),HCRIT(10,10)
      REAL    QQHTAB(10,10),HQHTAB(10,10),WLDIP(10),HWLMAN
      REAL    VTAIR
      REAL*8  THETAS(MACP),THETA(MACP),H(MACP)

      LOGICAL hlevd, overfl
     
C --- local
      INTEGER imper,iphase,NODE,iday

      REAL    wlstx,wsttar,dvmax,wstmax,wsupp,wdis,wlstarb
      REAL    wover,discap,wlsl,wlsu,wlsi,wsti,wdisi,wstn
      REAL    wprod1,wprod2,oscil,wlevst,wstlev,wlstara
      REAL    wsttara,qhtab,rday,wsmax

C --- retain values of local variables
      SAVE

c ---------------------------------------------------------------------
C --- resetting of flag for overflowing of automatic weir
      overfl = .false.

C --- memorizing previous target level
      wlstarb = wlstar

C ----------------------------------------------------------------------
C --- determine which management period the model is in:
      imper   = 0
 100  imper   = imper + 1
      if (imper .gt. nmper) stop 'WLEVBAL: error sw-management periods'
      if (INT(T+1.0) .gt. impend(imper)) goto 100

C --- determine the target sw-level:
      if (swman(imper) .eq. 1) then
C ---   in the case of a fixed weir the 'target level' is set to the 
C ---   weir crest, for later use in calculations to determine whether 
c ---   there is any outflow at all (see below):
        wlstar = hbweir(imper)
      else
C ---   for automatic weir, determine the target level of the surface 
C ---   water, dependent on groundwater level:

c ---   only adjust it if new subperiod, with length intwl(imper) has 
c       started  (or if it is is the first call)
        rday = (T+1.0)/intwl(imper)
        iday = int(rday)
        if (abs(rday - 1.0*iday).lt.0.00001 .or. .not.hlevd) then
        
          iphase = nphase(imper)
200       if (gwl.gt.gwlcrit(imper,iphase).and.iphase.gt.1) then
            iphase = iphase-1
            goto 200
          endif

C ---   compare total air volume with VCRIT, adapt iphase
          VTAIR = 0.0
          DO 210 NODE = 1,NUMNOD
210       VTAIR = VTAIR + real((THETAS(NODE)-THETA(NODE))*abs(DZ(NODE)))
214       IF (VTAIR.LT.VCRIT(imper,iphase).AND.IPHASE.GT.1) THEN
            iphase = iphase - 1
            GOTO 214
          ENDIF

C ---   compare H(nodhd(imper)) with HCRIT, adapt iphase 
218       HWLMAN = real(H(NODHD(imper)))
          IF (HWLMAN.GT.HCRIT(imper,iphase).AND.IPHASE.GT.1) THEN
            iphase = iphase - 1
            GOTO 218
          ENDIF

          wlstx = wlsman(imper,iphase)
        else

c ---   use old level
          wlstx = wlstarb
        endif

C ---   if the level must drop, then do not let it drop at more than 
C ---   the specified rate:
        if (wlstx .lt. wlstar .and. dropr(imper) .gt. 0.001) then
          wlstar = wlstar - dropr(imper)*dt
          if (wlstar .lt. wlstx) wlstar = wlstx
        else
          wlstar = wlstx
        endif
      endif

C --- counter of adjustments
      if (abs(wlstar-wlstarb) .gt. 0.00001) then
         numadj = numadj + 1
      endif

C --- storage for the 'target level'
      wsttar = wstlev(wlstar,sttab)

C --- level and storage for "max. level for supply"
      wlstara = wlstar - wldip(imper)
      if (wlstara .gt. (zbotdr(1+NRPRI)+1.e-4)) then
         wsttara = wstlev(wlstara,sttab)
         wsmax   = wscap(imper)
      else
         wsttara = 0.0
         wsmax   = 0.0
      endif

C --- determine whether the system will become full (target level or
C --- level of weir crest):
      dvmax   = (qdrd + rapdra + wsmax) * dt + runots
      wstmax  = wst + dvmax

      if (wstmax .lt. 1.0e-7) then
C ---   storage decreases to zero, then the surface water system 
C ---   falls dry; set surface water supply to maximum: 
        if (wstmax .lt. -0.1) then
           stop 'WLEVBAL: error algorithm for sw falling dry'
        endif
        wsupp  = wsmax
        wdis   = 0.0
        wst    = 0.0
        wls    = zbotdr(NRPRI+1)
      elseif (wstmax .ge. 0.0 .and. wstmax .lt. wsttara) then
C ---   system will not become full - set supply to max. capacity
        wsupp  = wsmax
        wdis   = 0.0
        wst    = wstmax
C
C ---   calculate new level from storage
        wls = wlevst(wst,sttab)
      else
C ---   determine how system will become full: with or without needing
C ---   surface water supply; try first without any supply:
        dvmax  = (qdrd + rapdra) * dt + runots
        wstmax = wst + dvmax
        if (wstmax .le. wsttara) then
C ---     apparently supply is needed for reaching target level, system 
C ---     is made full up to level wlstara, because supply is controllable:
          wsupp  = (wsttara - wst - (qdrd+rapdra)*dt-runots)/dt
          wdis   = 0.0
          wst    = wsttara
          wls    = wlstara
        elseif (wstmax .le. wsttar) then
C ---     apparently drainage is more than sufficient for filling system
C ---     to a level above the target level FOR SUPPLY, but not enough
C ---     for generating discharge; so calculate level from storage:
          wsupp = 0.0
          wdis  = 0.0
          wst   = wstmax
          wls   = wlevst(wst,sttab)
        else
C ---     drainage water is more than sufficient for reaching target
C ---     level;  now see whether there are automatic weirs for keeping
C ---     the level at target value, or that the discharge relationship
C ---     determines new level:
          wsupp = 0.
          if (swman(imper) .eq. 2) then
C ---       the outflow equals the drainage flux, plus the storage
C ---       excess (or deficit !) in the target situation compared to
C ---       the actual situation: 
            wdis = (wst-wsttar + (qdrd+rapdra)*dt + runots )/dt

C ---       now check whether the weir has enough discharge capacity 
C ---       at this water level
            IF (SWQHR.EQ.1) THEN
              wover = wls - hbweir(imper)
              discap = alphaw(imper) * (wover**betaw(imper))
            ELSEIF (SWQHR.EQ.2) THEN
C ---         interpolate QH table
              discap = qhtab(wlstar,imper,hqhtab,qqhtab)
            ENDIF
            if (discap .gt. wdis) then
              wls    = wlstar
              wst    = wsttar
              overfl = .false.
            else
              overfl = .true.
            endif
          endif

          if (swman(imper) .eq. 1 .or. overfl) then
C ---       determine level from q-h relationship, and also account
C ---       for change in storage (see below)
C ---       check first that the system does not overflow 
            IF (SWQHR.EQ.1) THEN
              wover = sttab(1,1) - hbweir(imper)
              discap = alphaw(imper) * (wover**betaw(imper))
            ELSEIF (SWQHR.EQ.2) THEN
              discap = QQHTAB(imper,1)
            ENDIF
            if (discap .lt. (qdrd+rapdra+runots/dt)) then
              write(6,*) qdrd,rapdra,runots,dt
              stop 'LEVBAL: surface water system has overflowed !'
            endif

C ---       iteration procedure for determining new level, storage, 
C ---       and discharge
            wlsl = hbweir(imper)
            wlsu = sttab(1,1)

C ---       find storage and discharge for intermediate point
  700       wlsi   = (wlsl + wlsu) * 0.5
            wsti  = wstlev(wlsi,sttab)

            IF (SWQHR.EQ.1) THEN
              wdisi = alphaw(imper)*(wlsi-hbweir(imper))**betaw(imper)
            ELSE
              wdisi = qhtab(wlsi,imper,hqhtab,qqhtab)
            ENDIF
            wstn  = wst + (qdrd + rapdra - wdisi)*dt + runots

            if (wstn .lt. wsti) then
              wlsu = wlsi 
            else
              wlsl = wlsi
            endif
            if ((wlsu - wlsl) .gt. 0.001) then
C ---         continue iteration procedure:
              goto 700
            else
C ---         updating of sw-parameters:
              wls  = wlsi
              wst  = wstn
              wdis = wdisi
            endif
          endif
        endif
      endif

C --- cumulative terms:
      cqdrd  = cqdrd  + qdrd*dt
      cwsupp = cwsupp + wsupp*dt
      cwout  = cwout  + wdis*dt

C --- updating registration of last four levels, for noting oscillation
      wlsbak(1) = wlsbak(2)
      wlsbak(2) = wlsbak(3)
      wlsbak(3) = wlsbak(4)
      wlsbak(4) = wls

      wprod1 = (wlsbak(2)-wlsbak(1))*(wlsbak(3)-wlsbak(2))
      wprod2 = (wlsbak(3)-wlsbak(2))*(wlsbak(4)-wlsbak(3))

      if (wprod1.lt.0.0 .and. wprod2.lt.0.0) then
        oscil = abs(wlsbak(3)-wlsbak(2)) 
        if (oscil .gt. osswlm) then
           write(6,9997) oscil
 9997      format(/' >>sw-level oscillation of ',f4.1,' cm; advise ',
     &       'reduction of dtmax') 
        endif
      endif

c ---------------------------------------------------------------------
c --- register that first call for target level has been
      if (.not.hlevd) then
        hlevd = .true.
      end if

      return
      end

C ----------------------------------------------------------------------
      real function wlevst (wstor,sttab)
C ----------------------------------------------------------------------
C     Date               : 28/08/96                          
C     Purpose            : calculate surface water level from    
C                          surface water storage                    
C     Subroutines called : -                                
C     Functions called   : -                                
C     File usage         : -                                
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER i

      REAL    wstor, sttab(22,2),dwst
C ----------------------------------------------------------------------
      if (wstor .lt. sttab(22,2)) then
         STOP 'WLEVST : surface water storage below bottom of table'
      endif
      if (wstor .gt. sttab(1,2)) then
         STOP 'WLEVST : surface water storage above top of table'
      endif
C
      i = 0
100   i = i+1
      if (.not.(wstor.ge.sttab(i+1,2).and.
     &          wstor.le.sttab(i,2))) goto 100
      dwst   = (wstor - sttab(i+1,2)) / (sttab(i,2) - sttab(i+1,2))
      wlevst = sttab(i+1,1) + dwst * (sttab(i,1) - sttab(i+1,1))

      return
      end

C ----------------------------------------------------------------------
      real function wstlev (wlev,sttab)
C-----------------------------------------------------------------------
C     Date               : 28/08/96                          
C     Purpose            : calculate surface water storage from  
C                          surface water level                    
C     Subroutines called : -                                
C     Functions called   : -                                
C     File usage         : -                                
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER i

      REAL    wlev, sttab(22,2),dwl
C ----------------------------------------------------------------------
      if (wlev .lt. sttab(22,1)) then
         STOP 'WSTLEV : surface water level below bottom of table'
      endif
      if (wlev .gt. sttab(1,1)) then
         STOP 'WSTLEV : surface water level above top of table'
      endif
C
      i = 0
100   i = i+1
      if (.not.(wlev.ge.sttab(i+1,1).and.wlev.le.sttab(i,1))) goto 100
      dwl    = (wlev - sttab(i+1,1)) / (sttab(i,1) - sttab(i+1,1))
      wstlev = sttab(i+1,2) + dwl * (sttab(i,2) - sttab(i+1,2))

      return
      end

C ----------------------------------------------------------------------
      real function qhtab (wlev,imper,hqhtab,qqhtab)
C-----------------------------------------------------------------------
C     Date               : 01/11/96                    
C     Purpose            : calculate surface water discharge from  
C                          surface water level, using table              
C     Subroutines called : -                                
C     Functions called   : -                                
C     File usage         : -                                
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER imper,itab

      REAL    wlev, hqhtab(10,10),qqhtab(10,10),dwl
C ----------------------------------------------------------------------

      ITAB = 2
  100 IF (wlev.lt.HQHTAB(IMPER,ITAB)) THEN 
        ITAB = ITAB+1
        GOTO 100
      ENDIF
      dwl  = (wlev-HQHTAB(IMPER,ITAB))/
     &    (HQHTAB(IMPER,ITAB-1)-HQHTAB(IMPER,ITAB))
      qhtab = QQHTAB(IMPER,ITAB) + dwl *
     &    (QQHTAB(IMPER,ITAB-1)-QQHTAB(IMPER,ITAB))  

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE ZEROCUMU (CQROT,CQDRA,CQBOT,CQTOP,CPTRA,CPEVA,CEVAP,
     & CRUNO,CGRAI,CNRAI,CGIRD,CNIRD,CUMBOT,CUMTOP,CQDRAR,CQCRACK,
     & CQDRAIN,CQDRD,CSWSUPP,CSWOUT,SQBOT,SQDRA,SQSUR,SQRAP,
     & DECTOT,ROTTOT,SQPREC,SQIRRIG,CQDARCY)
C ----------------------------------------------------------------------
C     Date               : 19/07/96                                      
C     Purpose            : set cumulative totals to 0                
C     Subroutines called : -                                           
C     Functions called   : -                                           
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE

C --- global
      REAL    CQROT,CQDRA,CQBOT,CQTOP,CPTRA,CPEVA,CEVAP,CRUNO
      REAL    CGRAI,CNRAI,CGIRD,CNIRD,CUMBOT,CUMTOP,CQDARCY
      REAL    CQDRAIN(5),CQDRD,cswsupp,cswout,CQDRAR,CQCRACK 
      REAL    SQBOT,SQDRA,SQSUR,SQRAP,DECTOT,ROTTOT,SQPREC,SQIRRIG

C --- local
      INTEGER i
C ----------------------------------------------------------------------
C --- setting cumulative fluxes to zero
      cqrot   = 0.0
      cqdra   = 0.0
      cqbot   = 0.0
      cqtop   = 0.0
      cqdarcy = 0.0
      cptra   = 0.0
      cpeva   = 0.0
      cevap   = 0.0
      cruno   = 0.0
      CGRAI   = 0.0
      CNRAI   = 0.0
      CGIRD   = 0.0
      CNIRD   = 0.0
      cumbot  = 0.0
      cumtop  = 0.0
      cqdrar  = 0.0
      cqcrack = 0.0

      DO 15 i = 1,5
15    cqdrain(i) = 0.0

C --- solute fluxes
      SQPREC  = 0.0
      SQIRRIG = 0.0
      SQBOT  = 0.0
      SQDRA  = 0.0
      SQSUR  = 0.0
      SQRAP  = 0.0
      DECTOT = 0.0
      ROTTOT = 0.0

C --- surface water system
      cqdrd    = 0.0
      cswsupp  = 0.0
      cswout   = 0.0

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE ZEROINTR (NUMNOD,INQROT,INQ,INQDRA,IQROT,IQDRA,IINTC,
     & IPTRA,IPEVA,IEVAP,IRUNO,IPREC,IQBOT,OUTPER,IQDRAR,IQCRACK,IGRAI,
     & IGIRD)
C ----------------------------------------------------------------------
C     Date               : 19/07/96                                       
C     Purpose            : set intermediate totals to 0                
C     Subroutines called : -                                           
C     Functions called   : -                                           
C     File usage         : -                                           
C ----------------------------------------------------------------------
      IMPLICIT NONE
      INCLUDE 'PARAM.FI'
 
C --- global
      INTEGER NUMNOD,OUTPER

      REAL    INQROT(MACP),INQ(MACP+1),INQDRA(5,MACP),IINTC,IPTRA,IPEVA
      REAL    IEVAP,IGRAI,IGIRD
      REAL    IRUNO,IPREC,IQROT,IQDRA,IQBOT,iqdrar,iqcrack
C ----------------------------------------------------------------------
C --- local
      INTEGER node,level
C ----------------------------------------------------------------------

C --- setting intermediate fluxes to zero
      DO 10 NODE = 1,NUMNOD
        INQROT(NODE) = 0.0
        INQ(NODE)    = 0.0
        DO 20 LEVEL = 1,5
          INQDRA(LEVEL,NODE) = 0.0
20      CONTINUE
10    CONTINUE
      INQ(NUMNOD+1) = 0.0
      IQROT   = 0.0
      IQDRA   = 0.0
      IINTC   = 0.0
      IPTRA   = 0.0
      IPEVA   = 0.0
      IEVAP   = 0.0
      IRUNO   = 0.0
      IPREC   = 0.0
      IGRAI   = 0.0
      IGIRD   = 0.0
      IQBOT   = 0.0
      OUTPER  = 0
      iqdrar  = 0.0
      iqcrack = 0.0

      RETURN
      END


** FILE:
**    SWAUTIL.FOR - part of program SWAP
** FILE IDENTIFICATION:
**    $Id: swautil.for 1.12 1999/02/17 17:35:59 kroes Exp $
** DESCRIPTION:
**    This file contains program units of SWAP. The program units 
**    in this file utilities and are sorted alphabetically
**    with the first letter of the program unit ranging from A - O.
**    The following program units are in this file:
**        AFGEN, ANALIN, DATONR, ERRHANDL, FINDUNIT, FROMTO, JMPLBL,
**        LIMIT, NRTODA, RADATA, RACHAR, RADOUR, RAINTR, RAREAR,
**        RFCHAR, RFDOUR, RFINTR, RFREAR, RSCHAR, RSDATA, RSDOUR,
**        RSINTR, RSREAR, SHIFTL, SHIFTR, SKPLBL, STEPNR
************************************************************************
C ----------------------------------------------------------------------
      REAL FUNCTION AFGEN(TABLE,ILTAB,X)
C ----------------------------------------------------------------------
C     Source             : Kees Rappoldt, 1/86
C     Purpose            : Linear interpolation in table TABLE with
C                          length ILTAB for a given value of the
C                          independent variable X.
C     Subroutines called : -
C     Functions called   : -
C     File usage         : -
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER I,ILTAB
      REAL    TABLE(ILTAB),SLOPE,X
C ----------------------------------------------------------------------
      IF (TABLE(1).GE.X)  GOTO 40
      DO 10 I = 3,ILTAB-1,2
        IF (TABLE(I).GE.X) GOTO 30
        IF (TABLE(I).LT.TABLE(I-2)) GOTO 20
 10   CONTINUE
C --- table fully filled, argument larger then last X in table
      AFGEN = TABLE(ILTAB)
      RETURN
C --- table partly filled, argument larger then last X in table
 20   AFGEN = TABLE(I-1)
      RETURN
C --- argument between first and last X in table, interpolation
 30   SLOPE = (TABLE(I+1)-TABLE(I-1))/(TABLE(I)-TABLE(I-2))
      AFGEN = TABLE(I-1) + (X-TABLE(I-2))*SLOPE
      RETURN
C --- argument less or equal to first X in table
 40   AFGEN = TABLE(2)
      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE ANALIN (LINE,BLANK,COMMENT)
C ----------------------------------------------------------------------
C     Date               : 27/10/1997
C     Purpose            : check if LINE is blank or COMMENT line
C                          COMMENT lines start with '*' or '!'
C     Subroutines called :
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      CHARACTER LINE*80
      LOGICAL BLANK,COMMENT
C ----------------------------------------------------------------------
C --- local
      INTEGER I
C ----------------------------------------------------------------------
      BLANK = .TRUE.                     
      I = 1
  30  IF (LINE(I:I) .NE. ' ') THEN
        BLANK = .FALSE.
      ELSE IF (I .LT. 80) THEN
        I = I+1
        GOTO 30
      ENDIF

      COMMENT = .FALSE.
      I = 1
40    IF (LINE(I:I).NE.' ') THEN
        IF (LINE(I:I).EQ.'*'.OR.LINE(I:I).EQ.'!') COMMENT = .TRUE.
      ELSEIF (I.LT.80) THEN
        I = I+1
        GOTO 40
      ENDIF

      RETURN 
      END

C ----------------------------------------------------------------------
      SUBROUTINE DATONR (YEAR,MONTH,DAY,DAYNR)
C ----------------------------------------------------------------------
C     Date               : 11/91
C     Purpose            : Conversion of date (YEAR,MONTH,DAY) to    
C                          daynumber (DAYNR)
C     Subroutines called : -
C     Functions called   : -
C     File usage         : -
C ----------------------------------------------------------------------
      IMPLICIT NONE 
      
      INTEGER ILEAP,YEAR,MONTH,DAY,DAYNR
      INTEGER FDM365(12),FDM366(12)

      DATA FDM365/1,32,60,91,121,152,182,213,244,274,305,335/
      DATA FDM366/1,32,61,92,122,153,183,214,245,275,306,336/
C ----------------------------------------------------------------------

C --- is YEAR a leap-year?
      ILEAP=0
      IF (((MOD(YEAR,4).EQ.0).AND.(MOD(YEAR,100).NE.0)).OR.
     $     (MOD(YEAR,400).EQ.0)) ILEAP=1   

C --- calculate daynumber
      IF (ILEAP.EQ.0) THEN
        DAYNR=FDM365(MONTH)+DAY-1
      ELSEIF (ILEAP.EQ.1) THEN
        DAYNR=FDM366(MONTH)+DAY-1
      ENDIF

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE ERRHANDL(UOER,SWER,KIER,MONA,NAER,PANA1,PAVA1,PADN1,
     &                    PANA2,PAVA2,PADN2,PANA3,PAVA3,PADN3)
************************************************************************
** SUBPROGRAM:
**    subroutine errhandl - handling of errors
** SYNOPSIS:
**    SUBROUTINE ERRHANDL
**    IN
**       integer      
**          UOER = unit number of output file with error messages (-)
**          SWER = switch for error output; 1=complete,2=partial (-)
**          KIER = kind of error (-)
**          MONA = module name that produced error (-)
**          NUPA = number of parameters as real type (-)
**       real
**          PAVA(3) = 3 parameter values of real type (-)
**       character    
**          NAER = name of error message (error description) (-)
**          PADN1,PADN2,PADN3 = the dimensions(units) of parameters 1,2,3 (-)
**          PANA1,PANA2,PANA3 = the names of parameters 1,2,3 of real type (-)
**    OUT: 
**       integer
**          UOER = unit number for file with error messages (-)
**       file usage:  UOER
**    USE OF SUBPROGRAMS:   -
**    USE OF COMMON BLOCKS: -
** DESCRIPTION:
**    This subroutine deals with all error handling. A file is opened
**    and 3 types of messages are written to this file: 
**    1. warning: these messages are informational only
**    2. recoverable error: these messages are informational only
**    3. fatal error: these messages indicate a severe problem, one that
**                    prevents a continuation of the simulation. This 
**                    message always results in interrupting simulation.
** HISTORY:
**    May 1995       J.G. Kroes
**                   creation
************************************************************************
C---- Declarations
      IMPLICIT NONE
C --- formal arguments
      INTEGER  KIER, SWER, UOER
      CHARACTER*(*) MONA, NAER, PADN1, PADN2, PADN3, PANA1, PANA2, PANA3
      REAL     PAVA1,PAVA2,PAVA3
C --- local variables
      CHARACTER*18 HV(3)
      INTEGER  I
C --- retain values of local variables
      SAVE
C --- local data
      DATA   (HV(I),I=1,3)    /'Warning           ',
     &    'Recoverable error ','Fatal error       '/
C ----------------------------------------------------------------------      
      IF (SWER.EQ.2 .AND. KIER.NE.3)  THEN
C--       Suppress warning and recoverable errors
        CONTINUE 

      ELSE
C--       Write Warning, Recoverable Error or Fatal error
        WRITE(UOER,11)  HV(KIER), MONA, NAER

        IF (PANA1.NE.' ') THEN
          IF (ABS(PAVA1).LT. 1.0 .OR. ABS(PAVA1).GT.100000.0) THEN
            WRITE(UOER,22)  PANA1, PAVA1, PADN1
          ELSE
            WRITE(UOER,33)  PANA1, PAVA1, PADN1
          END IF
        END IF
        IF (PANA2.NE.' ') THEN
          IF (ABS(PAVA2).LT. 1.0 .OR. ABS(PAVA2).GT.100000.0) THEN
            WRITE(UOER,22)  PANA2, PAVA2, PADN2
          ELSE
            WRITE(UOER,33)  PANA2, PAVA2, PADN2
          END IF
        END IF
        IF (PANA3.NE.' ') THEN
          IF (ABS(PAVA3).LT. 1.0 .OR. ABS(PAVA3).GT.100000.0) THEN
            WRITE(UOER,22)  PANA3, PAVA3, PADN3
          ELSE
            WRITE(UOER,33)  PANA3, PAVA3, PADN3
          END IF
        END IF
      END IF

   
C--     Fatal error
      IF (KIER.EQ.3) THEN
        WRITE(UOER,55)
        WRITE(*,11)  HV(3), MONA, NAER
        WRITE(*,44)
        WRITE(*,55)
        STOP
      END IF


      RETURN

   11 FORMAT(1X,A19,'   Produced by module  ',A,/,6X,A)
   22 FORMAT(6X,A,' = ',E10.3,5X,A)
   33 FORMAT(6X,A,' = ',F12.3,5X,A)
   44 FORMAT(6X,'verify output file MESSAGE.OUT')
   55 FORMAT(6X,'*** SIMULATION INTERRUPTED ***')
      END

C ----------------------------------------------------------------------
      SUBROUTINE FINDUNIT(UI,UO)
C ----------------------------------------------------------------------
C     Date               : 22/10/97
C     Purpose            : finds first free even unit number
C     Subroutines called : -
C     Functions called   : -
C     File usage         : -
C ----------------------------------------------------------------------
C---- Declarations
      IMPLICIT NONE
      INTEGER  UI,UO
C ----------------------------------------------------------------------                                                 
C --- local
      LOGICAL  INUSE
C ----------------------------------------------------------------------      
C---- Initialise
      UO = UI
      IF (MOD(UO,2).EQ.1) UO = UO +1
      INQUIRE (UNIT = UO, OPENED = INUSE)

C---- Search for available unit number
      IF (INUSE) THEN
        DO 10 WHILE (INUSE) 
          INQUIRE (UNIT = UO, OPENED = INUSE)
          UO = UO + 2
   10   CONTINUE
        UO = UO - 2
      END IF
   
      RETURN
      END

C ----------------------------------------------------------------------
      INTEGER FUNCTION FROMTO (DAY1,YEAR1,DAY2,YEAR2)
C ----------------------------------------------------------------------
C     Date               : 2/92
C     Purpose            : Calculates number of days between DAY1, YEAR1
C                          and DAY2, YEAR2
C     Subroutines called : DATONR
C     Functions called   : -
C     File usage         : -
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER I,J,DAY1,YEAR1,DAY2,YEAR2,DAYS
C ----------------------------------------------------------------------
      IF (YEAR1.EQ.YEAR2) THEN
        FROMTO = DAY2 - DAY1
      ELSEIF (YEAR2.GT.YEAR1) THEN 
        DAYS=0
        DO 10 I = YEAR1,YEAR2-1
          CALL DATONR (I,12,31,J)
          DAYS = DAYS + J
10      CONTINUE
        FROMTO = DAYS+DAY2-DAY1
      ENDIF

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE JMPLBL (INF,FNAME,LOGF,NAME)  
C ----------------------------------------------------------------------
C     Date               : 17/04/98
C     Purpose            : jump to label NAME
C     Subroutines called :
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER   INF,LOGF
      CHARACTER *(*) NAME
      CHARACTER*12 FNAME
C ----------------------------------------------------------------------
C --- local
      INTEGER NLB,J,K,NL,NN,IOST

      CHARACTER LINE*80

      LOGICAL BLANK,COMMENT
C ----------------------------------------------------------------------
C --- tijdelijk
      LOGF = LOGF

C --- always start from BOF
      REWIND (INF)

10    READ (INF,'(A)',IOSTAT=IOST) LINE
      IF (IOST.LT.0) then
C ---   EOF reached, label not found
        WRITE (*,12) NAME,FNAME
        WRITE (LogF,12) NAME,FNAME
12      FORMAT ('Label: ',A,' not found in file: ',A)
        STOP
      ENDIF 
      CALL ANALIN (LINE,BLANK,COMMENT)
      IF (BLANK.OR.COMMENT) GOTO 10

C --- count number ofleading blanks
      NLB = 1
  35  IF (LINE(NLB:NLB) .EQ. ' ') THEN
        NLB = NLB+1
        GOTO 35
      ENDIF

      J = 1
      DO 40 K = NLB,NLB+LEN(NAME)-1

C --- verify case insensitive label  
        NL = ICHAR(LINE(K:K))
        IF (NL.GT.90) NL = NL-32
        NN = ICHAR(NAME(J:J))
        IF (NN.GT.90) NN = NN-32
        IF (NL.NE.NN) THEN
C ---   no match, next line
          GOTO 10
        ENDIF
	  J = J+1 
40    CONTINUE

C --- found
      BACKSPACE (INF)

      RETURN
      END

C ----------------------------------------------------------------------
      REAL FUNCTION LIMIT(P1,P2,X)
C ----------------------------------------------------------------------
C --- Limits X to values within the range between lower limit P1 and
C --- upper limit P2
C ----------------------------------------------------------------------
      IMPLICIT NONE

      REAL P1,P2,X
C ----------------------------------------------------------------------
      LIMIT=X
      IF (X.GT.P2) LIMIT=P2
      IF (X.LT.P1) LIMIT=P1
      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE NRTODA (YEAR,DAYNR,MONTH,DAY)
C ----------------------------------------------------------------------
C     Date               : 11/91
C     Purpose            : Conversion of daynumber (YEAR,DAYNR) to    
C                          date (MONTH,DAY)
C     Subroutines called : -
C     Functions called   : -
C     File usage         : -
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER ILEAP,YEAR,MONTH,DAY,DAYNR
      INTEGER FDM365(12),FDM366(12)

      DATA FDM365/1,32,60,91,121,152,182,213,244,274,305,335/
      DATA FDM366/1,32,61,92,122,153,183,214,245,275,306,336/
C ----------------------------------------------------------------------

C --- is YEAR a leap-year?
      ILEAP=0
      IF (((MOD(YEAR,4).EQ.0).AND.(MOD(YEAR,100).NE.0)).OR.
     &     (MOD(YEAR,400).EQ.0)) ILEAP=1   

C --- calculate month, day
      IF (ILEAP.EQ.0) THEN
        MONTH=12
10      IF (DAYNR.LT.FDM365(MONTH)) THEN
          MONTH=MONTH-1
          GOTO 10
        ENDIF
        DAY=DAYNR-FDM365(MONTH)+1
      ELSEIF (ILEAP.EQ.1) THEN
        MONTH=12
20      IF (DAYNR.LT.FDM366(MONTH)) THEN
          MONTH=MONTH-1
          GOTO 20
        ENDIF
        DAY=DAYNR-FDM366(MONTH)+1
      ENDIF

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RADATA (DTYPE,INF,FNAME,LOGF,NAME,IVALUE,RVALUE,DVALUE,
     &  CVALUE,LENGTH,CITEMS,IVALS,ERROR)
C ----------------------------------------------------------------------
C     Date               : 06/02/1998
C     Purpose            :    
C     Subroutines called :
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER        DTYPE,INF,LOGF,LENGTH,IVALUE(LENGTH)
      REAL           RVALUE(LENGTH)
      REAL*8         DVALUE(LENGTH)
      CHARACTER *(*) CVALUE(LENGTH)
      CHARACTER *(*) NAME,FNAME

C ----------------------------------------------------------------------
C --- local
      INTEGER IP,I,J,BLN,ELN,ITEMS,CITEMS,IVALS,TMP

      CHARACTER LINE*120,BUFLIN*120

      LOGICAL   BLANK,COMMENT,BLMIN1,ERROR
C ----------------------------------------------------------------------
      ERROR = .false. 

      CALL FINDUNIT (80,TMP)
      OPEN (TMP,FILE='SWAP.TMP',STATUS='UNKNOWN')
      REWIND (TMP)

C --- read line from input file
10    READ (INF,'(A)') LINE
      CALL ANALIN (LINE, BLANK,COMMENT) 
      IF (BLANK.OR.COMMENT) GOTO 10

      CALL SKPLBL (LOGF,FNAME,LINE,NAME,IP) 

      CITEMS = 0

C --- analyze line
1000  I = IP+1

      BLN = I
      ELN = 120
      DO 12 J = I,120
        IF (LINE(J:J).EQ.'!') THEN
          ELN = J-1
          GOTO 13
        ENDIF
12    CONTINUE
13    CONTINUE

C --- area between BLN and ELN may contain data
      ITEMS = 0
      BLMIN1 = .TRUE.

      IF (DTYPE.LE.3) THEN
        DO 14 J = BLN,ELN
          IF (LINE(J:J).NE.' ') THEN
            IF (BLMIN1) THEN
              BLMIN1 = .FALSE.
              ITEMS  = ITEMS+1
            ENDIF
          ELSE
            BLMIN1 = .TRUE.
          ENDIF
14      CONTINUE
      ELSE
        DO 15 J = BLN,ELN
          IF (LINE(J:J).EQ.'''') THEN
            IF (BLMIN1) then
              BLMIN1 = .FALSE.
              ITEMS  = ITEMS+1
            ELSE
              BLMIN1 = .TRUE.
            ENDIF
          ENDIF
15      CONTINUE
      ENDIF           

C --- extract data
      IF (ITEMS.GT.0) THEN
        BUFLIN = ' '
        BUFLIN(BLN:ELN) = LINE(BLN:ELN)
        WRITE (TMP,'(A)') BUFLIN
        BACKSPACE (TMP)
        IF (DTYPE.EQ.1) THEN
          READ (TMP,*) (IVALUE(J), J = CITEMS+1,CITEMS+ITEMS)
        ELSEIF (DTYPE.EQ.2) THEN
          READ (TMP,*) (RVALUE(J), J = CITEMS+1,CITEMS+ITEMS)
        ELSEIF (DTYPE.EQ.3) THEN
          READ (TMP,*) (DVALUE(J), J = CITEMS+1,CITEMS+ITEMS)
        ELSEIF (DTYPE.EQ.4) THEN
          READ (TMP,*) (CVALUE(J), J = CITEMS+1,CITEMS+ITEMS)
        ENDIF
C ---   update total number of items
        CITEMS = CITEMS+ITEMS
        IF (CITEMS.EQ.LENGTH.OR.CITEMS.GE.IVALS) GOTO 30
      ENDIF

C --- next line...
20    READ (INF,'(A)') LINE
      CALL ANALIN (LINE,BLANK,COMMENT)
      IF (BLANK) GOTO 20
      IF (.NOT.COMMENT) THEN
       IP = 0
       GOTO 1000
      ENDIF

      IF (CITEMS.EQ.0) ERROR = .TRUE.

30    CLOSE (TMP,status='delete')

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RACHAR (INF,FNAME,LOGF,NAME,VALUE,LENGTH,CITEMS)
C ----------------------------------------------------------------------
C     Date               : 3/2/99
C     Purpose            : Reads an array of CHARACTER values from a 
C                          data file and carries out a range check on
C                          the returned values. The number of values on
C                          file is returned as CITEMS.
C     Subroutines called :
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER        INF,LOGF,LENGTH,CITEMS
      CHARACTER *(*) FNAME,NAME,VALUE(LENGTH)

C ----------------------------------------------------------------------
C --- local
      INTEGER DTYPE,IVALUE(1)
      REAL    RVALUE(1)
      REAL*8  DVALUE(1)
      LOGICAL ERROR
C ----------------------------------------------------------------------
      DTYPE = 4
      CALL RADATA (DTYPE,INF,FNAME,LOGF,NAME,IVALUE,RVALUE,DVALUE,VALUE,
     &  LENGTH,CITEMS,10000,ERROR)
      IF (ERROR) THEN
        WRITE (*,5) FNAME,NAME
        WRITE (LOGF,5) FNAME,NAME
        STOP 'Reading error - RADATA' 
5       Format (' Fatal error in file: ',A,' ,no items found for: ',A)
      ENDIF
      RETURN
      END


C ----------------------------------------------------------------------
      SUBROUTINE RADOUR (INF,FNAME,LOGF,NAME,LOW,HIGH,VALUE,LENGTH,
     & CITEMS)
C ----------------------------------------------------------------------
C     Date               : 3/2/99
C     Purpose            : Reads an array of DOUBLE PRECISION values 
C                          from a data file and carries out a range 
C                          check on the returned values. The number of 
C                          values on file is returned as CITEMS.
C     Subroutines called : RADATA
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER        INF,LOGF,LENGTH,CITEMS
      REAL*8         VALUE(LENGTH),LOW,HIGH
      CHARACTER *(*) NAME
      CHARACTER*12 FNAME
C ----------------------------------------------------------------------
C --- local
      INTEGER DTYPE,IVALUE(1),I
      REAL    RVALUE(1)
      CHARACTER CVALUE(1)
      LOGICAL ERROR
C ----------------------------------------------------------------------
      DTYPE = 3
      CALL RADATA (DTYPE,INF,FNAME,LOGF,NAME,IVALUE,RVALUE,VALUE,CVALUE,
     &  LENGTH,CITEMS,10000,ERROR)
      IF (ERROR) THEN
        WRITE (*,5) FNAME,NAME
        WRITE (LOGF,5) FNAME,NAME
        STOP 'Reading error - RADATA' 
5       Format (' Fatal error in file: ',A,' ,no items found for: ',A)
      ENDIF

C --- range checking
      DO 100 I = 1,CITEMS
        IF (VALUE(I) .LT. LOW) THEN
          WRITE(LOGF,60) FNAME,NAME,VALUE(I),LOW
          WRITE(*,60) FNAME,NAME,VALUE(I),LOW
 60       FORMAT(' Fatal error in file: ',A,' ,the variable ',A,
     &           ' =',d10.4,' while lower limit =',d10.4)
          STOP 'Check log file'
        ELSE IF (VALUE(I) .GT. HIGH) THEN
          WRITE(LOGF,70) FNAME,NAME,VALUE(I),HIGH
          WRITE(*,70) FNAME,NAME,VALUE(I),HIGH
 70       FORMAT(' Fatal error in file: ',A,' ,the variable ',A,
     &           ' =',d10.4,' while upper limit =',d10.4)
          STOP 'Check log file'
        ENDIF
 100  CONTINUE

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RAINTR (INF,FNAME,LOGF,NAME,LOW,HIGH,VALUE,LENGTH,
     & CITEMS)
C ----------------------------------------------------------------------
C     Date               : 3/2/99
C     Purpose            : Reads an array of INTEGER values from a data
C                          file and carries out a range check on the 
C                          returned values. The number of values on file
C                          is returned as CITEMS.
C     Subroutines called : RADATA
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER        INF,LOGF,LENGTH,VALUE(LENGTH),CITEMS,LOW,HIGH 
      CHARACTER *(*) NAME
      CHARACTER*12   FNAME
C ----------------------------------------------------------------------
C --- local
      INTEGER DTYPE,I
      REAL    RVALUE(1)
      REAL*8  DVALUE(1)
c     CHARACTER *(*) CVALUE(LENGTH)
      CHARACTER CVALUE(1)
      LOGICAL ERROR
C ----------------------------------------------------------------------
      DTYPE = 1
      CALL RADATA (DTYPE,INF,FNAME,LOGF,NAME,VALUE,RVALUE,DVALUE,CVALUE,
     &  LENGTH,CITEMS,10000,ERROR)
      IF (ERROR) THEN
        WRITE (*,5) FNAME,NAME
        WRITE (LOGF,5) FNAME,NAME
        STOP 'Reading error - RADATA' 
5       Format (' Fatal error in file: ',A,' ,no items found for: ',A)
      ENDIF

C --- range checking
      DO 100 I = 1,CITEMS
        IF (VALUE(I) .LT. LOW) THEN
          WRITE(LOGF,60) FNAME,NAME,VALUE(I),LOW
          WRITE(*,60) FNAME,NAME,VALUE(I),LOW
 60       FORMAT(' Fatal error in file: ',A,' ,the variable ',A,
     &           ' =',I10,' while lower limit =',I10)
          STOP 'Check log file'
        ELSE IF (VALUE(I) .GT. HIGH) THEN
          WRITE(LOGF,70) FNAME,NAME,VALUE(I),LOW
          WRITE(*,70) FNAME,NAME,VALUE(I),LOW
 70       FORMAT(' Fatal error in file: ',A,' ,the variable ',A,
     &           ' =',I10,' while upper limit =',I10)
          STOP 'Check log file'
        ENDIF
100   CONTINUE

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RAREAR (INF,FNAME,LOGF,NAME,LOW,HIGH,VALUE,LENGTH,
     &  CITEMS)
C ----------------------------------------------------------------------
C     Date               : 3/2/99
C     Purpose            : Reads an array of REAL values from a data
C                          file and carries out a range check on the 
C                          returned values. The number of values on file
C                          is returned as CITEMS.
C     Subroutines called : RADATA
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER        INF,LOGF,LENGTH,CITEMS
      REAL           VALUE(LENGTH),LOW,HIGH
      CHARACTER *(*) NAME
      CHARACTER*12   FNAME
C ----------------------------------------------------------------------
C --- local
      INTEGER DTYPE,IVALUE(1),I
      REAL*8  DVALUE(1)
c     CHARACTER *(*) CVALUE(LENGTH)
      CHARACTER CVALUE(1)
      LOGICAL ERROR
C ----------------------------------------------------------------------
      DTYPE = 2
      CALL RADATA (DTYPE,INF,FNAME,LOGF,NAME,IVALUE,VALUE,DVALUE,CVALUE,
     &  LENGTH,CITEMS,10000,ERROR)
      IF (ERROR) THEN
        WRITE (*,5) FNAME,NAME
        WRITE (LOGF,5) FNAME,NAME
        STOP 'Reading error - RADATA' 
5       Format (' Fatal error in file: ',A,' ,no items found for: ',A)
      ENDIF

C --- range checking
      DO 100 I = 1,CITEMS 
        IF (VALUE(I) .LT. LOW) THEN
          WRITE(LOGF,60) FNAME,NAME,VALUE(I),LOW
          WRITE(*,60) FNAME,NAME,VALUE(I),LOW
 60       FORMAT(' Fatal error in file: ',A,', the variable ',A,
     &           ' =',e10.4,' while lower limit =',e10.4)
          STOP 'Check log file'
        ELSE IF (VALUE(I) .GT. HIGH) THEN
          WRITE(LOGF,70) FNAME,NAME,VALUE(I),HIGH
          WRITE(*,70) FNAME,NAME,VALUE(I),HIGH
 70       FORMAT(' Fatal error in file: ',A,', the variable ',A,
     &           ' =',e10.4,' while upper limit =',e10.4)
          STOP 'Check log file'
        ENDIF
 100  CONTINUE

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RFCHAR (INF,FNAME,LOGF,NAME,VALUE,LENGTH,IVALS)
C ----------------------------------------------------------------------
C     Date               : 3/2/1999
C     Purpose            : Reads a fixed number of elements into a
C                          CHARACTER array
C     Subroutines called :
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER        INF,LOGF,LENGTH,IVALS
      CHARACTER *(*) FNAME,NAME,VALUE(LENGTH)

C ----------------------------------------------------------------------
C --- local
      INTEGER DTYPE,IVALUE(1),CITEMS
      REAL    RVALUE(1)
      REAL*8  DVALUE(1)
      LOGICAL ERROR
C ----------------------------------------------------------------------
      DTYPE = 4
      CALL RADATA (DTYPE,INF,FNAME,LOGF,NAME,IVALUE,RVALUE,DVALUE,VALUE,
     &  LENGTH,CITEMS,IVALS,ERROR)   
      IF (ERROR) THEN
        WRITE (*,5) FNAME,NAME
        WRITE (LOGF,5) FNAME,NAME
        STOP 'Reading error - RADATA' 
5       Format (' Fatal error in file: ',A,' ,no items found for: ',A)
      ENDIF

      IF (CITEMS.LT.IVALS) THEN
        WRITE(LOGF,10) NAME
        WRITE(*,10) NAME
 10     FORMAT (' Not enough elements found in array: ',A)
        STOP 'Check log file'
      ENDIF

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RFDOUR (INF,FNAME,LOGF,NAME,LOW,HIGH,VALUE,LENGTH,
     &  IVALS)
C ----------------------------------------------------------------------
C     Date               : 3/2/99
C     Purpose            : Reads a fixed number of elements into a
C                          DOUBLE PRECISION array and carries out a 
C                          range check on the returned values
C     Subroutines called : RADATA
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER        INF,LOGF,LENGTH,IVALS
      REAL*8         VALUE(LENGTH),LOW,HIGH
      CHARACTER *(*) NAME
      CHARACTER*12   FNAME
C ----------------------------------------------------------------------
C --- local
      INTEGER DTYPE,IVALUE(1),I,CITEMS
      REAL    RVALUE(1)
      CHARACTER CVALUE(1)
      LOGICAL ERROR
C ----------------------------------------------------------------------
      DTYPE = 3
      CALL RADATA (DTYPE,INF,FNAME,LOGF,NAME,IVALUE,RVALUE,VALUE,CVALUE,
     &  LENGTH,CITEMS,IVALS,ERROR)   
      IF (ERROR) THEN
        WRITE (*,5) FNAME,NAME
        WRITE (LOGF,5) FNAME,NAME
        STOP 'Reading error - RADATA' 
5       Format (' Fatal error in file: ',A,' ,no items found for: ',A)
      ENDIF

      IF (CITEMS.LT.IVALS) THEN
        WRITE(LOGF,10) NAME
        WRITE(*,10) NAME
 10     FORMAT (' Not enough elements found in array: ',A)
        STOP 'Check log file'
      ENDIF

C --- range checking
      DO 100 I = 1,CITEMS
        IF (VALUE(I) .LT. LOW) THEN
          WRITE(LOGF,60) FNAME,NAME,VALUE(I),LOW
          WRITE(*,60) FNAME,NAME,VALUE(I),LOW
 60       FORMAT(' Fatal error in file: ',A,' ,the variable ',A,' ='
     &           ,d10.4,' while lower limit =',d10.4)
          STOP 'Check log file'
        ELSE IF (VALUE(I) .GT. HIGH) THEN
          WRITE(LOGF,70) NAME,VALUE(I),HIGH
          WRITE(*,70) NAME,VALUE(I),HIGH
 70       FORMAT(' Fatal error in file: ',A,' ,the variable ',A,' ='
     &           ,d10.4,' while upper limit =',d10.4)
          STOP 'Check log file'
        ENDIF
 100  CONTINUE

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RFINTR (INF,FNAME,LOGF,NAME,LOW,HIGH,VALUE,LENGTH,
     &  IVALS)
C ----------------------------------------------------------------------
C     Date               : 3/2/99
C     Purpose            : Reads a fixed number of elements into an
C                          INTEGER array and carries out a range check
C                          on the returned values
C     Subroutines called : RADATA
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER        INF,LOGF,LENGTH,VALUE(LENGTH),IVALS,LOW,HIGH 
      CHARACTER *(*) NAME
      CHARACTER*12   FNAME
C ----------------------------------------------------------------------
C --- local
      INTEGER DTYPE,I,CITEMS
      REAL    RVALUE(1)
      REAL*8  DVALUE(1)
c     CHARACTER *(*) CVALUE(LENGTH)
      CHARACTER CVALUE(1)
      LOGICAL ERROR
C ----------------------------------------------------------------------
      DTYPE = 1
      CALL RADATA (DTYPE,INF,FNAME,LOGF,NAME,VALUE,RVALUE,DVALUE,CVALUE,
     &  LENGTH,CITEMS,IVALS,ERROR)   
      IF (ERROR) THEN
        WRITE (*,5) FNAME,NAME
        WRITE (LOGF,5) FNAME,NAME
        STOP 'Reading error - RADATA' 
5       Format (' Fatal error in file: ',A,' ,no items found for: ',A)
      ENDIF

      IF (CITEMS.LT.IVALS) THEN
        WRITE(LOGF,10) NAME
        WRITE(*,10) NAME
 10     FORMAT (' Not enough elements found in array: ',A)
        STOP 'Check log file'
      ENDIF

C --- range checking
      DO 100 I = 1,CITEMS
        IF (VALUE(I) .LT. LOW) THEN
          WRITE(LOGF,60) FNAME,NAME,VALUE(I),LOW
          WRITE(*,60) FNAME,NAME,VALUE(I),LOW
 60       FORMAT(' Fatal error in file: ',A,' , the variable ',A,' ='
     &           ,I10,' while lower limit =',I10)
          STOP 'Check log file'
        ELSE IF (VALUE(I) .GT. HIGH) THEN
          WRITE(LOGF,70) FNAME,NAME,VALUE(I),LOW
          WRITE(*,70) FNAME,NAME,VALUE(I),LOW
 70       FORMAT(' Fatal error in file: ',A,' ,the variable ',A,' ='
     &           ,I10,' while upper limit =',I10)
          STOP 'Check log file'
        ENDIF
100   CONTINUE

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RFREAR (INF,FNAME,LOGF,NAME,LOW,HIGH,VALUE,LENGTH,
     &  IVALS)
C ----------------------------------------------------------------------
C     Date               : 3/2/99
C     Purpose            : Reads a fixed number of elements into a
C                          REAL array and carries out a range check
C                          on the returned values
C     Subroutines called : RADATA
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER        INF,LOGF,LENGTH,IVALS
      REAL           VALUE(LENGTH),LOW,HIGH
      CHARACTER *(*) NAME
      CHARACTER*12   FNAME
C ----------------------------------------------------------------------
C --- local
      INTEGER DTYPE,IVALUE(1),I,CITEMS

      REAL*8  DVALUE(1)
c     CHARACTER *(*) CVALUE(LENGTH)
      CHARACTER CVALUE(1)
      LOGICAL ERROR
C ----------------------------------------------------------------------
      DTYPE = 2
      CALL RADATA (DTYPE,INF,FNAME,LOGF,NAME,IVALUE,VALUE,DVALUE,CVALUE,
     &  LENGTH,CITEMS,IVALS,ERROR)   
      IF (ERROR) THEN
        WRITE (*,5) FNAME,NAME
        WRITE (LOGF,5) FNAME,NAME
        STOP 'Reading error - RADATA' 
5       Format (' Fatal error in file: ',A,' ,no items found for: ',A)
      ENDIF

      IF (CITEMS.LT.IVALS) THEN
        WRITE(LOGF,10) NAME
        WRITE(*,10) NAME
 10     FORMAT (' Not enough elements found in array: ',A)
        STOP 'Check log file'
      ENDIF

C --- range checking
      DO 100 I = 1,CITEMS 
        IF (VALUE(I) .LT. LOW) THEN
          WRITE(LOGF,60) FNAME,NAME,VALUE(I),LOW
          WRITE(*,60)FNAME,NAME,VALUE(I),LOW
 60       FORMAT(' Fatal error in file: ',A,' ,the variable ',A,' ='
     &           ,e10.4,' while lower limit =',e10.4)
          STOP 'Check log file'
        ELSE IF (VALUE(I) .GT. HIGH) THEN
          WRITE(LOGF,70) FNAME,NAME,VALUE(I),HIGH
          WRITE(*,70) FNAME,NAME,VALUE(I),HIGH
 70       FORMAT(' Fatal error in file: ',A,' ,the variable ',A,' ='
     &           ,e10.4,' while upper limit =',e10.4)
          STOP 'Check log file'
        ENDIF
 100  CONTINUE

      RETURN
      END

C ----------------------------------------------------------------------
       SUBROUTINE RSCHAR (INF,FNAME,LOGF,XNAME,VALUE)
C ----------------------------------------------------------------------
C     Date               : 3/2/1999
C     Purpose            : reads a single CHARACTER value from a data
C                          file    
C     Subroutines called :
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER INF,LOGF

      CHARACTER *(*) FNAME,XNAME,VALUE
C ----------------------------------------------------------------------
C --- local
      INTEGER   DTYPE,IVALUE
      REAL      RVALUE
      REAL*8    DVALUE
      LOGICAL   ERROR 
C ----------------------------------------------------------------------
      DTYPE = 4
      CALL RSDATA (INF,FNAME,LOGF,XNAME,IVALUE,RVALUE,DVALUE,VALUE,
     &  DTYPE,ERROR)
      IF (ERROR) THEN
        WRITE (*,5) FNAME,XNAME
        WRITE (LOGF,5) FNAME,XNAME
        STOP 'Reading error - RSDATA' 
5       Format (' Fatal error in file: ',A,' ,no items found for: ',A)
      ENDIF

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RSDATA(INF,FNAME,LOGF,NAME,IVALUE,RVALUE,DVALUE,
     & CVALUE,DTYPE,ERROR)
C ----------------------------------------------------------------------
C     Date               : 3/2/99
C     Purpose            :    
C     Subroutines called :
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER    DTYPE,INF,LOGF,IVALUE
      REAL       RVALUE
      REAL*8     DVALUE

      CHARACTER *(*) FNAME,NAME,CVALUE 
      LOGICAL    ERROR
C ----------------------------------------------------------------------
C --- local
      INTEGER    I,BLN,ELN,IP,TMP
      CHARACTER  LINE*80,BUFLIN*80
      LOGICAL    BLANK,COMMENT
C ----------------------------------------------------------------------
      CALL FINDUNIT (80,TMP)
      OPEN (TMP,FILE='SWAP.TMP',STATUS='UNKNOWN')
      REWIND (TMP)

C      CALL JMPLBL (INF,'SHIT',LOGF,NAME)

C --- read line from input file
  25  READ(INF,'(A)') LINE
      CALL ANALIN (LINE,BLANK,COMMENT) 

C --- if comment line or blank line read next line 
      IF (BLANK.OR.COMMENT) GOTO 25

      CALL SKPLBL (LOGF,FNAME,LINE,NAME,IP)  

C --- find start of value: BLN
      I = IP+1
 50   IF (LINE(I:I) .EQ. ' ') THEN
        I = I+1
        IF (I.EQ.81) THEN
          ERROR = .TRUE.
          CLOSE (TMP,status='delete')
          RETURN
        ENDIF
        GOTO 50
      ELSE IF (LINE(I:I).EQ.'!') THEN
        ERROR = .TRUE.
        CLOSE (TMP,status='delete')
        RETURN
      ENDIF

      BLN = I

C --- find end of value: ELN
      I = I+1
 
      IF (DTYPE.LE.3) then
 55     IF (LINE(I:I) .NE. ' ' .AND. LINE(I:I) .NE. '!') THEN
          I = I+1
          GOTO 55
        ENDIF
      ELSE
56      IF (LINE(I:I).NE.'''') THEN
          I = I+1
          GOTO 56      
        ENDIF     
      ENDIF
            
      ELN = I-1
      IF (DTYPE.EQ.4) ELN = ELN+1

C --- extract data 
      BUFLIN = ' '
      BUFLIN(BLN:ELN) = LINE(BLN:ELN)
      WRITE (TMP,'(A)') BUFLIN
      BACKSPACE (TMP)

      IF (DTYPE .EQ. 1) READ (TMP,*) IVALUE
      IF (DTYPE .EQ. 2) READ (TMP,*) RVALUE
      IF (DTYPE .EQ. 3) READ (TMP,*) DVALUE
      IF (DTYPE .EQ. 4) READ (TMP,*) CVALUE

      CLOSE (TMP,status='delete')
      ERROR = .FALSE.
      RETURN
      END 

C ----------------------------------------------------------------------
      SUBROUTINE RSDOUR(INF,FNAME,LOGF,NAME,LOW,HIGH,VALUE)
C ----------------------------------------------------------------------
C     Date               : 3/2/99
C     Purpose            : reads a single DOUBLE PRECISION value from a 
C                          data file and carries our a range check on 
C                          the returned value
C     Subroutines called : RSDATA
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER   INF,LOGF

      REAL*8    VALUE,LOW,HIGH
      CHARACTER *(*) NAME     
      CHARACTER*12   FNAME
C ----------------------------------------------------------------------
C --- local
      INTEGER   DTYPE,IVALUE
      REAL      RVALUE
      CHARACTER CVALUE*80
      LOGICAL   ERROR
C ----------------------------------------------------------------------
      DTYPE = 3
      CALL RSDATA (INF,FNAME,LOGF,NAME,IVALUE,RVALUE,VALUE,CVALUE,
     &  DTYPE,ERROR)
      IF (ERROR) THEN
        WRITE (*,5) FNAME,NAME
        WRITE (LOGF,5) FNAME,NAME
        STOP 'Reading error - RSDATA' 
5       Format (' Fatal error in file: ',A,' ,no items found for: ',A)
      ENDIF

      IF (VALUE .LT. LOW) THEN
        WRITE(LOGF,60) FNAME,NAME,VALUE,LOW
        WRITE(*,60) FNAME,NAME,VALUE,LOW
 60     FORMAT(' Fatal error in file: ',A,', the variable ',A,' ='
     &         ,D10.4,' while lower limit =',D10.4)
        STOP 'Check log file' 
      ELSE IF (VALUE .GT. HIGH) THEN
        WRITE(LOGF,70) FNAME,NAME,VALUE,HIGH
        WRITE(*,70) FNAME,NAME,VALUE,HIGH
 70     FORMAT(' Fatal error in file: ',A,', the variable ',A,' ='
     &         ,D10.4,' while upper limit =',D10.4)
        STOP 'Check log file'
      ENDIF

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RSINTR(INF,FNAME,LOGF,NAME,LOW,HIGH,VALUE)
C ----------------------------------------------------------------------
C     Date               : 3/2/99
C     Purpose            : reads a single INTEGER value from a data file
C                          and carries out a range check on the returned
C                          value
C     Subroutines called : RSDATA
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER   INF,LOGF,VALUE,LOW,HIGH
      CHARACTER *(*) NAME     
      CHARACTER*12   FNAME
C ----------------------------------------------------------------------
C --- local
      INTEGER   DTYPE
      REAL      RVALUE
      REAL*8    DVALUE

      CHARACTER CVALUE*80
      LOGICAL   ERROR
C ----------------------------------------------------------------------
      DTYPE = 1
      CALL RSDATA (INF,FNAME,LOGF,NAME,VALUE,RVALUE,DVALUE,CVALUE,
     &  DTYPE,ERROR)
      IF (ERROR) THEN
        WRITE (*,5) FNAME,NAME
        WRITE (LOGF,5) FNAME,NAME
        STOP 'Reading error - RSDATA' 
5       Format (' Fatal error in file: ',A,' ,no items found for: ',A)
      ENDIF

      IF (VALUE .LT. LOW) THEN
        WRITE(LOGF,60) FNAME,NAME,VALUE,LOW
        WRITE(*,60) FNAME,NAME,VALUE,LOW
 60     FORMAT(' Fatal error in file: ',A,', the variable ',A,' =',I10,
     &         ' while lower limit =',I10)
        STOP 'Check log file'
      ELSE IF (VALUE .GT. HIGH) THEN
        WRITE(LOGF,70) FNAME,NAME,VALUE,HIGH
        WRITE(*,70) FNAME,NAME,VALUE,HIGH
 70     FORMAT(' Fatal error in file: ',A,', the variable ',A,' =',I10,
     &         ' while upper limit =',I10)
        STOP 'Check log file'
      ENDIF

      RETURN
      END

C ----------------------------------------------------------------------
      SUBROUTINE RSREAR(INF,FNAME,LOGF,NAME,LOW,HIGH,VALUE)
C ----------------------------------------------------------------------
C     Date               : 3/2/99
C     Purpose            : reads a single INTEGER value from a data file
C                          and carries our a range check on the returned
C                          value
C     Subroutines called : RSDATA
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER INF,LOGF

      REAL      VALUE,LOW,HIGH
      CHARACTER *(*) NAME     
      CHARACTER*80 CVALUE
      CHARACTER*12 FNAME
C ----------------------------------------------------------------------
C --- local
      INTEGER   DTYPE,IVALUE
      REAL*8    DVALUE
      LOGICAL   ERROR
C ----------------------------------------------------------------------
      DTYPE = 2
      CALL RSDATA (INF,FNAME,LOGF,NAME,IVALUE,VALUE,DVALUE,CVALUE,
     &  DTYPE,ERROR)
      IF (ERROR) THEN
        WRITE (*,5) FNAME,NAME
        WRITE (LOGF,5) FNAME,NAME
        STOP 'Reading error - RSDATA' 
5       Format (' Fatal error in file: ',A,' ,no items found for: ',A)
      ENDIF

      IF (VALUE .LT. LOW) THEN
        WRITE(LOGF,60) FNAME,NAME,VALUE,LOW
        WRITE(*,60) FNAME,NAME,VALUE,LOW
 60     FORMAT(' Fatal error in file: ',A,', the variable ',A,' ='
     &         ,e10.4,' while lower limit =',e10.4)
        STOP 'Check log file'
      ELSE IF (VALUE .GT. HIGH) THEN
        WRITE(LOGF,70) FNAME,NAME,VALUE,HIGH
        WRITE(*,70) FNAME,NAME,VALUE,HIGH
 70     FORMAT(' Fatal error in file: ',A,', the variable ',A,' ='
     &         ,e10.4,' while upper limit =',e10.4)
        STOP 'Check log file'
      ENDIF

      RETURN
      END

C-----------------------------------------------------------------------
      SUBROUTINE SHIFTL(STRING)
C-----------------------------------------------------------------------
C     Date               : 26/10/95
C     Purpose            : Shift STRING to the left as far as possible
C     Subroutines called : -
C     Functions called   : -
C     File usage         : -
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER   I,LS,empty

      CHARACTER *(*) STRING
C-----------------------------------------------------------------------
      ls  = len (string)

      empty = 0
      i     = 1
30    if (string(i:i).eq.' ') then
        empty = empty+1
        i     = i+1
        if (i.le.ls) goto 30
      endif

      if (empty.gt.0) then
        do 40 i = 1,ls-empty
          string(i:i) = string(i+empty:i+empty)
40      continue
        do 50 i = ls-empty+1,ls
          string(i:i) = ' '
50      continue
      endif

      return
      end 

C-----------------------------------------------------------------------
      SUBROUTINE SHIFTR(STRING)
C-----------------------------------------------------------------------
C     Date               : 26/10/95 
C     Purpose            : Shift STRING to the right as far as possible
C     Subroutines called : -
C     Functions called   : -
C     File usage         : -
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER   i,ls,empty

      CHARACTER *(*) STRING
C-----------------------------------------------------------------------
      LS  = LEN (STRING)

      empty = 0
      i     = ls
30    if (string(i:i).eq.' ') then
        empty = empty+1
        i     = i-1
        if (i.ge.1) goto 30
      endif

      if (empty.gt.0) then
        do 40 i = ls,empty+1,-1
          string(i:i) = string(i-empty:i-empty)
40      continue
        do 50 i = 1,empty
          string(i:i) = ' '
50      continue
      endif

      return
      end

C ----------------------------------------------------------------------
      SUBROUTINE SKPLBL (LOGF,FNAME,LINE,NAME,POSIT)  
C ----------------------------------------------------------------------
C     Date               : 27/10/1997
C     Purpose            : verify label and return position of '='
C     Subroutines called :
C     Functions called   :
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER   LOGF,POSIT,NL,NN
      CHARACTER LINE*80 
      CHARACTER *(*) FNAME,NAME
C ----------------------------------------------------------------------
C --- local
      INTEGER NLB,J,K
C ----------------------------------------------------------------------
C --- count Number of Leading Blanks
      NLB = 1
2     IF (LINE(NLB:NLB).EQ.' ') THEN
        NLB = NLB+1
	  GOTO 2
	ENDIF   	 

      J = 1
      DO 10 K = NLB,NLB+LEN(NAME)-1

C ---   verify case insensitive label  
        NL = ICHAR(LINE(K:K))
        IF (NL.GT.90) NL = NL-32
        NN = ICHAR(NAME(J:J))
        IF (NN.GT.90) NN = NN-32
        IF (NL.NE.NN) THEN
          WRITE (*,5) FNAME,NAME
          WRITE (LOGF,5) FNAME,NAME
          STOP 'Reading error - SKPLBL' 
5         Format(' Fatal error in file: ',A,
     &           ' cannot read parameter: ',A)
        ENDIF 
        J = J+1
10    CONTINUE

      K = NLB+LEN(NAME)-1
20    K = K+1
      IF (K.GT.80) THEN
          WRITE (*,5) FNAME,NAME
          WRITE (LOGF,5) FNAME,NAME
          STOP 'Reading error - SKPLBL' 
      ENDIF
      IF (LINE(K:K).NE.'=') GOTO 20

      POSIT = K
                             
      RETURN
      END

C ----------------------------------------------------------------------
      INTEGER FUNCTION STEPNR(ARRAY,LENGTH,X)
C ----------------------------------------------------------------------
C --- Find stepnumber 
C ----------------------------------------------------------------------
      IMPLICIT NONE

      INTEGER I,LENGTH
      REAL    X,ARRAY(LENGTH)
C ----------------------------------------------------------------------
      IF (ARRAY(1).GE.X) GOTO 30

      DO 10 I = 2,LENGTH
        IF (ARRAY(I).GT.X)          GOTO 20 
        IF (ARRAY(I).LT.ARRAY(I-1)) GOTO 20
10    CONTINUE  
C --- array fully filled, argument larger than last X in array
      STEPNR = LENGTH
      RETURN
C --- array partly filled, argument larger than last X in array or
C --- argument between first and last X in table
20    STEPNR = I-1
      RETURN
C --- argument less or equal to first X in array
30    STEPNR = 1
      RETURN
      END


