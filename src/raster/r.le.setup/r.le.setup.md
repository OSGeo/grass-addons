## DESCRIPTION

*r.le.setup* program is used to set up the sampling and analysis
framework that will be used by the other *r.le* programs.

## NOTES

*Full instructions can be found in the **r.le manual** (see "REFERENCES"
section below).*

The first menu allows the user to define a rectangular sampling frame,
select how sampling will be done (regions, sampling units, moving
window), setup the limits for groups and classes, and change the color
table. Use the left mouse button to make your choice.

Information about the structure of the landscape is obtained by
overlaying a set of sampling areas on top of a specified part (the
sampling frame of a map layer, and then calculating specific structural
measures for the part of the map layer that corresponds to the area in
each sampling area.

To setup a ***sampling frame*** click on SAMPLING FRAME in the main
menu. The program will ask "Will the sampling frame (total area within
which sampling units are distributed) be the whole map? (y/n) \[y\]"
Just hit a carriage return to accept the default, which is to use the
whole map. You do not need to setup a sampling frame if you want to use
the whole map, as this is the default. To setup a different sampling
frame type "n" in response to this question. Then use the mouse and a
rubber band box to outline a rectangular sampling frame on screen. This
box will be moved to the nearest row and column of the map. You will be
asked last whether you want to "Refresh the screen before choosing more
setup?" If you don't like the sampling frame you just setup, answer yes
to this question, then click on SAMPLING FRAME again to redo this part
of the setup. This sampling frame will be used in all subsequent setup
procedures unless you change it. You can change it at any time by simply
clicking on SAMPLING FRAME again.

A ***sampling area*** may be one of four things. First, it is possible
to treat the entire map layer as the one (and only) sampling area.
Second, if the map layer can be divided into meaningful geographical
regions, then it is possible to treat the regions themselves as sampling
areas. The third option is that the sampling areas may be sampling units
of fixed shape and size (also called scale) that are placed within the
map layer as a whole. The fourth and final option is that the sampling
area may be moved systematically across the map as a moving window.

If regions are to be used as the sampling areas , then the user can use
*r.le.setup* to draw regions or any existing map of regions can simply
be used directly. To draw regions and create a new regions map in
*r.le.setup* select "REGIONS" from the first *r.le.setup* menu, and the
user is asked to do the following:

```text
1.  "ENTER THE NEW REGION MAP NAME:". Only a new raster map name is
acceptable. The user can type LIST to find out the existing raster map
names in this location and mapset.

2. "PLEASE OUTLINE REGION # 1". The user should move the mouse cursor
into the graphic monitor window and use the mouse buttons as instructed:
Left button: where am I.to display the current coordinates of the cursor.
Middle button: Mark start (next) point. to enter a vertex of the region
boundary.
Right button: Finish region-connect to 1st point to close the region
boundary by setting the last vertex to be equal to the first one.

3. A "REGION OPTIONS:" menu is displayed and the user should use the mouse
to select one of
   the options:

"DRAW MORE": repeat the above process and setup another region.
"START OVER": abandon the previous setup and start all over again.
"DONE-SAVE": save the regions outlined so far and exit this procedure.
"QUIT-NO SAVE": quit the procedure without saving the regions.
```

Once the "DONE-SAVE" option is selected, the new raster map of the
sampling regions is generated. It is displayed on the monitor window for
several seconds, the monitor window is refreshed, the main menu is
displayed again, and the program is ready for other setup work. Note
that you cannot draw regions in areas outside the mask, if a mask is
present (see *r.mask* command).

The user can also use the GRASS *[wxGUI vector
digitizer](https://grass.osgeo.org/grass-stable/manuals/wxGUI.vdigit.html)*
to digitize circular or polygonal regions and to create a sampling
regions map without using *r.le.setup*. Or, as mentioned above, an
existing raster map can be used as a regions map.

If sampling units are to be used as the sampling areas (Fig. 2), then
choose "SAMPLING UNITS" from the first *r.le.setup* menu. The program
checks the *r.le.para* subdirectory for an existing "units" file from a
previous setup session and allows the user to rename this file (to save
it) before proceeding. The r.le.setup program will otherwise overwrite
the "units" file. Then the following choice is displayed followed by a
series of other choices:

```text
    Which do you want to do?
       (1) Use the keyboard to enter sampling unit parameters
       (2) Draw the sampling units with the mouse
                            Enter 1 or 2:

```

When sampling units are defined using the keyboard, the user inputs the
shape and size (scale) of the sampling units by specifying dimensions in
pixels using the keyboard. When sampling units are drawn with the mouse,
the user clicks the mouse to define the sampling units in the GRASS
monitor window, and then actually places the sampling units for each
scale onto the map. By placing the units with the mouse the user can
directly determine the method of sampling unit distribution as well as
the shape, size, and number of sampling units.

If the choice is made to define sampling units using the keyboard, the
following series of questions must be answered:

```text
    How many different SCALES do you want (1-15)?
```

The user is asked to specify the number of scales that will be used. The
*r.le* programs allow the user to simultaneously sample the same map
with the same measures using sampling areas of different sizes.
Currently there can be between 1 and 15 scales that can be sampled
simultaneously. Substantial output can be produced if many scales are
used.

Sampling units must be placed spatially into the landscape. There are
five options for doing this :

*Random nonoverlapping*  
Sampling units are placed in the landscape by randomly choosing numbers
that specify the location of the upper left corner of each sampling
unit, subject to the constraint that successive sampling units not
overlap other sampling units or the edge of the landscape, and that they
must be entirely within the area defined by the mask (see *r.mask*
command) if one exists.

*Systematic contiguous*  
Sampling units are placed side by side across the rows. The user will be
able to enter a row and column to indicate where the upper left corner
of the systematic contiguous framework should be placed. Rows are
numbered from the top down beginning with row 1 of the sampling frame.
Columns are numbered from left to right, beginning with column 1 of the
sampling frame. A random starting location can be obtained by using a
standard random number table to choose the starting row and column. The
*r.le.setup* program does not avoid placing the set of sampling units
over areas outside the mask. The user will have to make sure that
sampling units do not extend outside the mask by choosing a particular
starting row and column or by drawing a sampling frame before placing
the set of sampling units.

*Systematic noncontiguous*  
The user must specify the starting row and column as in \#2 above and
the amount of spacing (in pixels) between sampling units. Horizontal and
vertical spacing are identical. Sampling units are again placed side by
side (but spaced) across the rows. As in \#2 the program does not avoid
placing sampling units outside the masked area; the user will have to
position the set of units to avoid areas outside the mask.

*Stratified random*  
The strata are rectangular areas within which single sampling units are
randomly located. The user must first specify the starting row and
column as in \#2 above. Then the user must specify the number of strata
in the horizontal and vertical directions. As in \#2 the program does
not avoid placing sampling units outside the masked area; the user will
have to position the set of units to avoid areas outside the mask.

*Centered over sites*  
The user must specify the name of a sitefile containing point locations.
A single sampling unit is placed with its center over each site in the
site file. This is a useful approach for determining the landscape
structure around points, such as around the location of wildlife
observations.

The user is prompted to enter a ratio that defines the shape of the
sampling units. Sampling units may have any rectangular shape, including
square as a special case of rectangular. Rectangular shapes are
specified by entering the ratio of columns/rows (horizontal
dimension/vertical dimension) as a real number. For example, to obtain a
sampling unit 10 columns wide by 4 rows long specify the ratio as 2.5
(10/4).

```text
    Recommended maximum SIZE is m in x cell total area. 

    What size (in cells) for each sampling unit of scale n?
```

The user is then given the recommended maximum possible size for a
sampling unit (in pixels) and asked to input the size of sampling units
at each scale. Sampling units can be of any size, but the maximum size
is the size of the landscape as a whole. All the sampling units, that
make up a single sampling scale, are the same size. After specifying the
size, the program determines the nearest actual number of rows and
columns, and hence size, that is closest to the requested size, given
the shape requested earlier.

```text
    The nearest size is x cells wide X y cells high = xy cells
    Is this size OK?  (y/n)  [y]

    Maximum NUMBER of units in scale n is p?
    What NUMBER of sampling units do you want to try to use?
```

The maximum number of units that can be placed over the map, given the
shape and size of the units, is then given. The user can then choose the
number of sampling units to be used in the map layer. It may not always
be possible to choose the maximum number, depending upon the shape of
the sampling units. In the case of systematic contiguous and
noncontiguous, the program will indicate how many units will fit across
the columns and down the rows. The user can then specify a particular
layout (e.g., 6 units could be placed as 2 rows of 3 per row or as 3
rows of 2 per row).

```text
    Is this set of sampling units OK?  (y/n)  [y]
```

Finally, the set of sampling units is displayed on the screen (e.g.,
Fig. 1) and the user is asked whether it is acceptable. If the answer is
no, then the user is asked if the screen should be refreshed before
redisplaying the menu for "Methods of sampling unit distribution" so
that the user can try the sampling unit setup again.

The choice is made to define sampling units using the mouse, then the
following menu for use with the mouse is displayed:

```text
    Outline the standard sampling unit of scale n.
       Left button: Check unit size
       Middle button:   Move cursor
       Right button:    Lower right corner of unit here
```

The user can then use the mouse and the rubber band box to outline the
standard sampling unit. Once it has been outlined, the number of columns
and rows in the unit, the ratio of width/length and the size of the
unit, in cells, will be displayed. After this first unit is outlined,
then a new menu is displayed:

```text
    Outline more sampling units of scale n?
       Left button: Exit
       Middle button:   Check unit position
       Right button:    Lower right corner of next unit here
```

The user can then place more units identical to the standard unit by
simply clicking the right mouse button where the lower right corner of
the unit should be placed. The rest of the rubber band box can be
ignored while placing additional units. The program is set up so that
units cannot be placed so they overlap one another, so they overlap the
area outside the mask, or so they overlap the edge of the sampling
frame. Warning messages are issued for all three of these errors and a
sampling unit is simply not placed.

Using this procedure a rectangular "window" or single sampling area is
moved systematically across the map to produce a new map (Fig. 2,3).
This sampling procedure can only be used with the measures that produce
a single value or with a single class or group when measures produce
distributions of values (Table 1). The first class or group specified
when defining class or group limits (section 2.3.2.) is used if
distributional measures are chosen with the moving window sampling
method. In this case, the user should manually edit the
*r.le.para/recl\_tb* file so that the desired group is listed as the
first group in this file.

Sampling begins with the upper left corner of the window placed over the
upper left corner of the sampling frame. It is strongly recommended that
the user read the section on the GRASS mask (section 2.2.2) prior to
setting up the moving window, as this mask can be used to speed up the
moving window operation. The value of the chosen measure is calculated
for the window area. This value is assigned to the location on the new
map layer corresponding to the center pixel in the window if the window
has odd (e.g. 3 X 3) dimensions. The value is assigned to the location
on the new map layer corresponding to the first pixel below and to the
right of the center if the window has even dimensions (e.g. 6 X 10). If
this pixel has the value "0," which means "no data" in GRASS, then this
pixel is skipped and a value of "0" is assigned to the corresponding
location in the new map. The window is then moved to the right (across
the row) by one pixel, and the process is repeated. At the end of the
row, the window is moved down one pixel, and then back across the row.
This option produces a new map layer, whose dimensions are smaller by
approximately (m-1)/2 rows and columns, where m is the number of rows or
columns in the window.

If the "MOVE-WINDOW" option in the main menu is selected, first the
program checks for an existing "move\_wind" file, in the r.le.para
subdirectory, containing moving window specifications from a previous
session. The user is given the option to avoid overwriting this file by
entering a new file name for the old "move\_wind" file. Users should be
aware that moving window analyses are very slow, because a large number
of sampling units are, in effect, used. See the appendix on "Time needed
to complete analyses with the r.le programs" for some ideas about how
moving window size and sampling frame area affect the needed time to
complete the analyses.

The *r.le* programs *r.le.dist* and *r.le.patch* allow the attribute
categories in the input map to be reclassed into several attribute
groups, and reports the analysis results by each of these attribute
groups. It is necessary to setup group limits for all measures that say
"by gp" when typing "*r.le.dist help*" or "*r.le.patch help*" at the
GRASS prompt. The same reclassing can be done with the measurement
indices (e.g., size), except that each "cohort" (class) of the reclassed
indices is called an index class instead of a group. It is also
necessary to setup class limits for all measures that say "by class"
when typing "*r.le.dist help*" or "*r.le.patch help*" at the GRASS
prompt.

Group/class limits are setup by choosing "GROUP/CLASS LIMITS" from the
main menu upon starting *r.le.setup*, or you can create the files
manually using a text editor. The program checks for existing
group/class limit files in subdirectory *r.le.para* and allows the user
to rename these files prior to continuing. If the files are not renamed
the program will overwrite them. The files are named recl\_tb (attribute
group limits), size (size class limits), shape\_PA (shape index class
limits for perimeter/area index), shape\_CPA (shape index class limits
for corrected perimeter/area index), shape\_RCC (shape index class
limits for related circumscribing circle index), and from\_to (for the
*r.le.dist* program distance methods m7-m9).

Attribute groups and index classes are defined in a different way. In
the *r.le* programs attribute groups are defined as in the following
example:

```text
    1, 3, 5, 7, 9 thru 21 = 1 (comment)
    31 thru 50 = 2 (comment)
    end
```

In this example, the existing categories 1, 3, 5, 7, {9, 10, ... 20, 21}
are included in the new group 1, while {31, 32, 33, ..., 49, 50} are
included in the new group 2. The characters in bold are the "key words"
that are required in the definition. Each line is called one "reclass
rule".

The GRASS reclass convention is adopted here with a little modification
(see "*r.reclass*" command in the GRASS User's Manual). The difference
is that r.le only allows one rule for each group while the GRASS
*r.reclass* command allows more than one. The definition of "from" and
"to" groups is simply the extension of the GRASS reclass rule. The
advantage of using the GRASS reclass convention is that the user can
generate a permanent reclassed map, using GRASS programs, directly from
the *r.le* setup results.

The *r.le* measurement index classes are defined by the lower limits of
the classes, as in the following example:

```text
    0.0, 10.0, 50.0, 200.0, -999
```

This means:

```text
    if v >= 0.0 and v < 10.0 then  v belongs to index class 1;
    if v >= 10.0 and v < 50.0 then  v belongs to index class 2;
    if v >= 50.0 and v < 200.0 then v belongs to index class 3;
    if v >= 200.0 then v belongs to index class 4;
```

where v is the calculated index value and **-999** marks the end of the
index class definition. The measurement index can be the size index, one
of the three shape indices, or one of the three distance indices. The
program is currently designed to allow no more than 25 attribute groups,
25 size classes, 25 shape index classes, and 25 distance index classes.
As an alternative, the user may want to permanently group certain
attributes prior to entering the *r.le* programs. For example, the user
may want to group attributes 1-10, in a map whose attributes are ages,
into a single attribute representing young patches. The user can do this
using the GRASS *r.reclass* and *r.resample* commands, which will create
a new map layer that can then be analyzed directly (without setting up
group limits) with the *r.le* programs.

## REFERENCES

Baker, W.L. and Y. Cai. 1992. The r.le programs for multiscale analysis
of landscape structure using the GRASS geographical information system.
Landscape Ecology 7(4):291-302.

The [*r.le* manual: Quantitative analysis of landscape
structures](https://grass.osgeo.org/gdp/landscape/r_le_manual5.pdf)
(GRASS 5; 2001)

## SEE ALSO

*[r.le.patch](r.le.patch.md), [r.le.pixel](r.le.pixel.md),
[r.le.trace](r.le.trace.md)*

## AUTHOR

William L. Baker Department of Geography and Recreation University of
Wyoming Laramie, Wyoming 82071 U.S.A.
