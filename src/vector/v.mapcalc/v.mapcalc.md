## DESCRIPTION

*v.mapcalc* performs overlay and buffer functions on vector map layers.
New vector map layers can be created which are expressions of existing
vector map layers, boolean vector operations and buffer functions.

### PROGRAM USE

The module expects its input as expression in the following form:  
  
**result = expression**  
  
This structure is similar to r.mapcalc, see
*[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html)*.
Where **result** is the name of a vector map layer that will contain the
result of the calculation and **expression** is any valid combination of
boolean and buffer operations for existing vector map layers.  
The input is given by using the first module option *expression=* . This
option passes a **quoted** expression on the command line, for
example:  

```sh
v.mapcalc expression="A = B"
```

Where **A** is the new vector map layer that will be equal to the
existing vector map layer **B** in this case.  

```sh
v.mapcalc "A = B"
```

will give the same result.

### OPERATORS AND FUNCTIONS

The module supports the following boolean vector operations:  

| Boolean Name | Operator | Meaning             | Precedence | Correspondent Function  |
|--------------|----------|---------------------|------------|-------------------------|
| AND          | &        | Intersection       | 1          | v.overlay operator=and  |
| OR           | \|       | Union              | 1          | v.overlay operator=or   |
| DISJOINT OR  | +        | Disjoint union     | 1          | v.patch                 |
| XOR          | ^        | Symmetric difference | 1        | v.overlay operator=xor  |
| NOT          | ~        | Complement         | 1          | v.overlay operator=not  |

And vector functions:

```text
 buff_p(A, size)          Buffer the points of vector map layer A with size
 buff_l(A, size)          Buffer the lines of vector map layer A with size
 buff_a(A, size)          Buffer the areas of vector map layer A with size
```

## NOTES

As shown in the operator table above, the boolean vector operators do
not have different precedence. In default setting the expression will be
left associatively evaluated. To define specific precedence use
parentheses around these expressions, for example:  

```sh
 v.mapcalc expression="D = A & B | C"
```

Here the first intermediate result is the intersection of vector map
layers **A & B**. This intermediate vector map layer is taken to create
the union with vector map **C** to get the final result **D**. It
represents the default behaviour of left associativity.

```sh
 v.mapcalc expression="D = A & (B | C)"
```

Here the first intermediate result is taken from the parenthesized union
of vector map layers **B | C**. Afterwards the intersection of the
intermediate vector map layer and **A** will be evaluated to get the
final result vector map layer **D**.  
  
It should be noticed, that the order in which the operations are
performed does matter. Different order of operations can lead to a
different result.

## EXAMPLES

This example needed specific region setting. It should work in UTM and
LL test locations.  
First set the regions extent and create two vector maps with one random
points, respectively:

```sh
g.region s=0 n=30 w=0 e=50 b=0 t=50 res=10 res3=10 -p3

v.random --o -z output=point_1 n=1 seed=1
v.random --o -z output=point_2 n=1 seed=2
v.info point_1
v.info point_2
```

Then the vector algebra is used to create buffers around those points,
cut out a subset and apply different boolean operation on the subsets in
one statement:

```sh
v.mapcalc --o expr="buff_and = (buff_p(point_1, 30.0) ~ buff_p(point_1, 20.0)) & \
                    (buff_p(point_2, 35) ~ buff_p(point_2, 25))"
v.mapcalc --o expr="buff_or  = (buff_p(point_1, 30.0) ~ buff_p(point_1, 20.0)) | \
                    (buff_p(point_2, 35) ~ buff_p(point_2, 25))"
v.mapcalc --o expr="buff_xor = (buff_p(point_1, 30.0) ~ buff_p(point_1, 20.0)) ^ \
                    (buff_p(point_2, 35) ~ buff_p(point_2, 25))"
v.mapcalc --o expr="buff_not = (buff_p(point_1, 30.0) ~ buff_p(point_1, 20.0)) ~ \
                    (buff_p(point_2, 35) ~ buff_p(point_2, 25))"
```

## REFERENCES

The use of this module requires the following software to be installed:
[PLY(Python-Lex-Yacc)](https://www.dabeaz.com/ply/)

```sh
# Ubuntu/Debian
sudo apt-get install python-ply

# Fedora
sudo dnf install python-ply
```

## SEE ALSO

*[v.overlay](https://grass.osgeo.org/grass-stable/manuals/v.overlay.html),
[v.buffer](https://grass.osgeo.org/grass-stable/manuals/v.buffer.html),
[v.patch](https://grass.osgeo.org/grass-stable/manuals/v.patch.html),
[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html)*

## AUTHORS

Thomas Leppelt, Soeren Gebbert, Thuenen Institut, Germany
