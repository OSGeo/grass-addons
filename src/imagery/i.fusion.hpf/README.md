# i.fusion.hpf

`i.fusion.hpf` is a GRASS-GIS module to combine high-resolution
panchromatic data with lower resolution multispectral data, resulting in an
output with both excellent detail and a realistic representation of original
multispectral scene colors.

The process involves a convolution using a High Pass Filter (HPF) on the high
resolution data, then combining this with the lower resolution multispectral
data.

Optionally, a linear histogram matching technique is performed in a way that
matches the resulting Pan-Sharpened imaged to them statistical mean and standard
deviation of the original multi-spectral image.

Source: Gangkofner, 2008

## Algorithm description

1. Computing ratio of low (Multi-Spectral) to high (Panchromatic) resolutions
2. High Pass Filtering the Panchromatic Image
3. Resampling MSX image to the higher resolution
4. Adding weighted High-Pass-Filetred image to the upsampled MSX image
5. Optionally, matching histogram of Pansharpened image to the one of the
   original MSX image

## From the original paper

```text
Step 1: HP Filtering of the High-resolution Image to Extract the Structural
Detail

Step 2: Adding the HP Filtered Image to Each Band of the Multispectral Image
Using a Standard Deviation-based Injection Model

Step 3: Linear Histogram Match to Adapt SD and Mean of the Merged Image Bands
to Those of the Original MS Image Bands

Figure 1:

 ____________________________________________________________________________
+                                                                            +
| Pan Img ->  High Pass Filter  ->  HP Img                                   |
|                                      |                                     |
|                                      v                                     |
| MSx Img ->  Weighting Factors ->  Weighted HP Img                          |
|       |                              |                                     |
|       |                              v                                     |
|       +------------------------>  Addition to MSx Img  =>  Fused MSx Image |
+____________________________________________________________________________+
```

## Installation

### Requirements

See [GRASS Addons SVN repository, README file, Installation - Code Compilation](https://svn.osgeo.org/grass/grass-addons/README)

### Steps

Making the script `i.fusion.hpf` available from within any GRASS-GIS ver. 7.x
session, may be done via the following steps:

1. launch a GRASS-GIS’ ver. 7.x session
2. navigate into the script’s source directory
3. execute `make MODULE_TOPDIR=$GISBASE`

## Usage

After installation, from within a GRASS-GIS session, see help details via
`i.fusion.hpf --help`

### Remarks

* easy to use, i.e.:
  * for one band `i.fusion.hpf pan=Panchromatic msx=${Band}`
  * for multiple bands `i.fusion.hpf pan=Panchromatic msx=Red,Green,Blue,NIR`
* easy to test various parameters that define the High-Pass filter’s
  *kernel size* and *center value*
* should work with **any** kind of imagery (think of bitness)
* the "black border" effect, possibly caused due to a non-perfect match of the
  high vs. the low resolution of the input images, can be trimmed out by using
  the `trim` option --a floating point "trimming factor" with which to multiply
  the pixel size of the low resolution image-- and shrink the extent of the
  output image

## Implementation notes

* First commit on Sat Oct 25 12:26:54 2014 +0300
* Working state reached on Tue Nov 4 09:28:25 2014 +0200

## To Do

* Go through <http://trac.osgeo.org/grass/wiki/Submitting/Python>
* Access input raster by row I/O ?
* Proper command history tracking. Not all "r" modules do it... ?
* Add timestamps (r.timestamp)
* Deduplicate code where applicable
* Make the -v messages shorter, yet more informative (ie report center cell)
* Test. Will it compile in other systems?
* Checking options to integrate in `i.pansharpen`. Think of FFM methods vs.
  Others?
* Who else to thank?  Transfer from archive/
* Improve [Documentation.lyx](https://gitlab.com/NikosAlexandris/i.fusion.hpf/blob/master/lyx/Documentation.lyx)

## Questions

* To Ask!

## References

* Gangkofner, U. G., Pradhan, P. S., and Holcomb, D. W. (2008). Optimizing
  the high-pass filter addition technique for image fusion.
  PHOTOGRAMMETRIC ENGINEERING & REMOTE SENSING, 74(9):1107–1118.
* “ERDAS IMAGINE.” Accessed March 19, 2015. <http://doc.hexagongeospatial.com/ERDAS%20IMAGINE/ERDAS_IMAGINE_Help/#ii_hpfmerge_mergedialog.htm>.

* Aniruddha Ghosh & P.K. Joshi (2013) Assessment of pan-sharpened very
  high-resolution WorldView-2 images, International Journal of Remote Sensing,
  34:23, 8336-8359

## Ευχαριστώ

* Nikos Ves
* Ranjith, <https://class.coursera.org/interactivepython-005/forum/profile?user_id=9361576>
* Anonymous on coursera's discussion forums
* Pietro Zambelli
* StackExchange contributors
  * <http://stackoverflow.com/a/1140966/1172302>
  * <http://stackoverflow.com/a/275025/1172302>
* Yann Chemin
* Aniruddha Ghosh
* Παναγιώτης Μαυρογιώργος (<https://github.com/pmav99>)
