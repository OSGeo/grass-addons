      SUBROUTINE CDIV(AR,AI,BR,BI,CR,CI)                                EIS0
      DOUBLE PRECISION AR,AI,BR,BI,CR,CI                                EIS0
C                                                                       EIS0
C     COMPLEX DIVISION, (CR,CI) = (AR,AI)/(BR,BI)                       EIS0
C                                                                       EIS0
      DOUBLE PRECISION S,ARS,AIS,BRS,BIS                                EIS0
      S = DABS(BR) + DABS(BI)                                           EIS0
      ARS = AR/S                                                        EIS0
      AIS = AI/S                                                        EIS0
      BRS = BR/S                                                        EIS0
      BIS = BI/S                                                        EIS0
      S = BRS**2 + BIS**2                                               EIS0
      CR = (ARS*BRS + AIS*BIS)/S                                        EIS0
      CI = (AIS*BRS - ARS*BIS)/S                                        EIS0
      RETURN                                                            EIS0
      END                                                               EIS0
