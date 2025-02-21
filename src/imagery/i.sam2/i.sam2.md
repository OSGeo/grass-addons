## DESCRIPTION

*i.sam2* allows users to segment orthoimagery based on text prompts
using [SamGeo](https://samgeo.gishub.org/).

## REQUIREMENTS

- [Pillow\>=10.2.0](https://pillow.readthedocs.io/en/stable/)
- [numpy\>=1.26.1](https://numpy.org/)
- [torch\>=2.5.1](https://pytorch.org/)
- [segment-geospatial\>=0.12.3](https://samgeo.gishub.org/)

```sh
        pip install pillow numpy torch segment-geospatial
    
```

## EXAMPLES

Segment orthoimagery using SamGeo2:

```sh
    i.sam2 group=rgb_255 output=tree_mask text_prompt="trees"
    
```

![i.sam2: trees detected in an aerial image with samgeo](i_sam2_trees.jpg)

## NOTES

The first time use will be longer as the model needs to be downloaded.
Subsequent runs will be faster. Additionally, CUDA is required for GPU
acceleration. If you do not have a GPU, you can use the CPU by setting
the environment variable \`CUDA\_VISIBLE\_DEVICES\` to \`-1\`.

## REFERENCES

- Wu, Q., & Osco, L. (2023). samgeo: A Python package for segmenting
    geospatial data with the Segment Anything Model (SAM). Journal of
    Open Source Software, 8(89), 5663.
    <https://doi.org/10.21105/joss.05663>
- Osco, L. P., Wu, Q., de Lemos, E. L., Gonçalves, W. N., Ramos, A. P.
    M., Li, J., & Junior, J. M. (2023). The Segment Anything Model (SAM)
    for remote sensing applications: From zero to one shot.
    International Journal of Applied Earth Observation and
    Geoinformation, 124, 103540.
    <https://doi.org/10.1016/j.jag.2023.103540>

## SEE ALSO

*[i.segment.gsoc](i.segment.gsoc.md) for region growing and merging
segmentation, [i.segment.hierarchical](i.segment.hierarchical) performs
a hierarchical segmentation, [i.superpixels.slic](i.superpixels.slic)
for superpixel segmentation.*

## AUTHOR

Corey T. White (NCSU GeoForAll Lab & OpenPlains Inc.)
