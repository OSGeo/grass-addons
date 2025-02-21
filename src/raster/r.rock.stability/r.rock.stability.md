## DESCRIPTION

Two important steps can be recognised in the rockfall analysis: the
potential failure detection and the run out simulation. Analyzing the
stability of rock slopes, most important kinematisms are slidings
(planar or wedge) and topplings. r.rock.stability is a module that
allows users to apply geomechanical classifications (SMR and SSPC) for
the preliminary assessment of the susceptibility of rock slopes to
failures induced by these kinematisms.

**SMR approach (default)**:SMR (Slope Mass Rating) is a widely used
geomechanical classification developed by Romana (1995). The final SMR
rating is obtained by means of next expression: SMR=RMRb+(F1\*F2\*F3)+F4
where:

- RMRb is the RMR index resulting from Bieniawski's Rock Mass
    Classification (1989)
- F1 depends on the parallelism between discontinuity and slope dip
    direction
- F2 depends on the discontinuity dip in the case of planar failure
    and the plunge, or of the intersection line in wedge failure. As
    regards toppling failure, this parameter takes the value 1.0
- F3 depends on the relationship between slope and discontinuity dips
    (toppling or planar failure cases) or the immersion line dip (wedge
    failure case)
- F4 is a correction factor that depends on the excavation method
    used:
    <!-- end list -->
    <!-- end list -->
    <!-- end list -->
    <!-- end list -->

r.rock.stability calculate F1, F2 and F3 index by combining DEM (slope
and aspect) and joint dip and dip direction.

F1, F2 and F3 are calculated according two functions of Romana (1995)
and of Tomàs et al. (2007). The functions proposed by Romana are
discrete, instead Tomàs et al. (2007) proposed continuous functions that
reduced subjective interpretations.

**SSPC approach (optional)**: inserting TC value (or a map of TC values)
it's possible to obtain a SSPC map according to Hack's classification
(Hack, 1998). Only a part of the method introduced by Hack is used in
the module: the orientation dependent stability (the stability depend on
relation between slope and discontinuity orientation). According to the
author:

- sliding occurs if: TC \< 0,0113\*AP
- toppling occurs if: TC \< 0,0087\*(-90-AP+dip)

where AP is the apparent dip, TC is the condition factor for a
discontinuity. TC can be calculated by multiplying the large scale
roughness, the small scale roughness, the infill material and the karst
factors observed in the field:

**TC=Rl Rs Im Ka**.

**Rl** (roughness in large scale - area between 0,2x0,2 m2 and 1x1 m2)

- 1,00 Wavy
- 0,95 Slightly wavy
- 0,85 Curved
- 0,80 Slightly curved
- 0,75 Straight

**Rs** (roughness in small scale - area of 0,2x0,2m2):

- 0,95 Rough stepped
- 0,90 Smooth stepped
- 0,85 Polished stepped
- 0,80 Rough undulating
- 0,75 Smooth undulating
- 0,70 Polished undulating
- 0,65 Rough planar
- 0,60 Smooth planar
- 0,55 Polished planar.

**Im** (Infill material)

- Cemented --\> Infill (1,07), No Infill (1,00)
- Non softening and sheared material e.g. free of clay, talc, etc --\>
    Coarse (0,95) Medium (0,90) Fine (0,85)
- Soft sheared material e.g. clay, talc, etc --\> Coarse (0,75) Medium
    (0,65) Fine (0,55)
- Gouge \< irregularities (0,42); Gouge \> irregularities (0,17);
    flowing material (0,05)

**Ka** (karst):

- 1,00 None
- 0.92 Karst

NOTE: high pixel values indicate high susceptibility

**SMR wedge (optional)**: inserting dip and dip direction it's possible
to calculate the SMR index of wedge.

## INPUT

**Digital Elevation Model** = name

**Dip direction** = string

**Dip** = string

**F4** = string

**RMR** = string or map

**TC (optional)** = string or map

**Output prefix** = name

## OUTPUT

**r.rock.stability** generates **3 raster maps of SMR**
(prefix\_toppling; prefix\_planar; prefix\_wedge;) values distribution
according to mechanism: planar sliding, toppling and wedge (if optional
dip and dip direction is inserted).

| SMR classes | SMR values | Suggest supports                                                                                  |
| ----------- | ---------- | ------------------------------------------------------------------------------------------------- |
| Ia          | 91-100     | None                                                                                              |
| Ib          | 81-90      | None, scaling is required                                                                         |
| IIa         | 71-80      | (None, toe ditch or fence), spot bolting                                                          |
| IIb         | 61-70      | (Toe ditch or fence nets), spot or systematic bolting                                             |
| IIIa        | 51-60      | (Toe ditch and/or fence nets), spot or systematic bolting, spot shotcrete                         |
| IIIb        | 41-50      | (Toe ditch and/or fence nets), spot or systematic bolting/anchor, toe wall and/or dental concrete |
| IVa         | 31-40      | Anchor systematic shotcrete, toe wall and/or dental concrete (or re-excavation), drainage         |
| IVb         | 21-30      | Systematic reinforced shotcrete, toe wall and/or concrete, re-excavation, deep drainage           |
| Va          | 11-20      | Gravity or anchored wall, re-excavation                                                           |

## REFERENCES

BIENIAWSKI Z.T. (1989). Engineering Rock Mass Classifications. John
Wiley and Sons: New York.

FILIPELLO A., GIULIANI A., MANDRONE G. (2010) - Rock Slopes Failure
Susceptibility Analysis: From Remote Sensing Measurements to Geographic
Information System Raster Modules. American Journal of Environmental
Sciences 6 (6): 489-494, 2010 ISSN 1553-345X © 2010 Science
Publications.

HACK HRGK (1998) Slope stability probability classification, SSPC, 2nd
edn. ITC, Enschede, The Netherlands, 258 pp, ISBN 90 6164 154 3

ROMANA M. (1995). The geomechanical classification SMR for slope
correction. Proc. Int. Congress on Rock Mechanics 3: 1085-1092.

TOMÀS, R., DELGADO, J.,SERON, J.B. (2007). Modification of slope mass
rating(SMR) by continuous functions. International Journal of Rock
Mechanics and Mining Sciences 44: 1062-1069.

## SEE ALSO

## AUTHORS

Andrea Filipello, University of Turin, Italy

Daniele Strigaro, University of Milan, Italy
