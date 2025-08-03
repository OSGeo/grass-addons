## DESCRIPTION

Removing unreliable pixels is a fundamental and one of the first steps
in remote sensing. Landsat imagery provides a Quality Assessment (QA)
band which can be used for this purpose.

The *i.landsat.qa* module generates reclassification rule files which
can be used in
[r.reclass](https://grass.osgeo.org/grass-stable/manuals/r.reclass.html)
for filtering the QA band according to pixel quality characteristics the
user defines as unacceptable. It works with both Collection 1 and
Collection 2 data from Landsat 8 OLI/TIRS, 4-7 TM/ETM+. The **dataset**
the QA band belongs to is specified like in
[i.landsat.download](i.landsat.download.md).

Values defined as unacceptable for a given condition will be set to NULL
in the output raster map. All other values will be set to 1.

The Quality Assessment (QA) band from Landsat contains 16bit integer
values that represent "bit-packed combinations of surface, atmosphere,
and sensor conditions that can affect the overall usefulness of a given
pixel".  

The following quality relevant conditions are represented as "single
bits" in the Landsat QA band:

|                                    |            |
| ---------------------------------- | ---------- |
| Condition                          | Collection |
| Designated Fill                    | 1,2        |
| Dilated Cloud                      | 2          |
| Terrain Occlusion / Dropped Pixels | 1          |
| Cloud                              | 1,2        |
| Cirrus                             | 2          |
| Cloud Shadow                       | 2          |
| Snow                               | 2          |
| Clear                              | 2          |
| Water                              | 2          |

Possible choices for the "single bits" are:

|       |                               |                    |
| ----- | ----------------------------- | ------------------ |
| Value | Description                   | Bit representation |
| No    | This condition does not exist | 0                  |
| Yes   | This condition exists         | 1                  |

The following quality relevant conditions are represented as "double
bits" in the Landsat QA band:

|                         |            |
| ----------------------- | ---------- |
| Condition               | Collection |
| Radiometric saturation  | 2          |
| Cloud Confidence        | 1,2        |
| Cloud Shadow Confidence | 1,2        |
| Snow/Ice Confidence     | 1,2        |
| Cirrus Confidence       | 1,2        |

Possible choices for the "double bits" are:

|                |                                                                                         |                    |
| -------------- | --------------------------------------------------------------------------------------- | ------------------ |
| Value          | Description                                                                             | Bit representation |
| Not Determined | Algorithm did not determine the status of this condition                                | 00                 |
| Low            | Algorithm has low to no confidence that this condition exists (0-33 percent confidence) | 01                 |
| Medium         | Algorithm has medium confidence that this condition exists (34-66 percent confidence)   | 10                 |
| High           | Algorithm has high confidence that this condition exists (67-100 percent confidence)    | 11                 |

## NOTES

The Landsat Quality Assessment band is an artificial band which
represents an analysis based on [defined
algorithms](https://landsat.usgs.gov/documents/LDCM_CVT_ADD.pdf). The
USGS provides the users with the following note on how the QA band
should be used:

"Rigorous science applications seeking to optimize the value of pixels
used in a study will find QA bits useful as a first level indicator of
certain conditions. Otherwise, users are advised that this file contains
information that can be easily misinterpreted and it is not recommended
for general use."

## EXAMPLE

```sh
# Create a cloud mask:
i.landsat.qa --overwrite --verbose cloud_confidence="Medium,High" \
    dataset="landsat_ot_c2_l2" \
    output=./Cloud_Mask_rules.txt
r.reclass input=LC81980182015183LGN00_BQA \
    output=LC81980182015183LGN00_Cloud_Mask rules=./Cloud_Mask_rules.txt

# Create a water mask (only available for collection 2):
i.landsat.qa --overwrite --verbose water="Yes" \
    dataset="landsat_ot_c2_l2" \
    output=./Water_Mask_rules.txt
r.reclass input=LC81980182015183LGN00_BQA \
    output=LC81980182015183LGN00_Water_Mask rules=./Water_Mask_rules.txt

```

## SEE ALSO

*[r.reclass](https://grass.osgeo.org/grass-stable/manuals/r.reclass.html),
[i.modis.qc](i.modis.qc.md), [r.bitpattern](r.bitpattern.md),
[i.landsat](i.landsat.md) [i.landsat8.swlst](i.landsat8.swlst.md)*

## REFERENCES

*[Landsat Collection 1 Level 1 Quality Assessment
bands](https://www.usgs.gov/core-science-systems/nli/landsat/landsat-collection-1-level-1-quality-assessment-band)
[Landsat Collection 2 Level 1 Quality Assessment
bands](https://www.usgs.gov/core-science-systems/nli/landsat/landsat-collection-2-quality-assessment-bands)*

## AUTHOR

Stefan Blumentrath, Norwegian Institute for Nature Research, Oslo
(Norway)
