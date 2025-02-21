## DESCRIPTION

*r.green.hydro.financial* computes the economic costs and values of the
plants. It provides an analysis calculating realization costs and
profits for each potential plant in order to know which ones are
feasible.  

## NOTES

The required input maps are the ones with the segments of the potential
plants (vector), the structure of these potential plants (vector), the
electric grid (vector), the landuse (raster) and the slope (raster).  
  
In the section "input column", the column names in the table of the map
with the potential plants have to be reported in order to read correctly
the corresponding values.  
  
Each section of the module calculates a cost. The used formula are valid
for all the currencies but the values have to be adapted. The default
values related to a cost are considered in Euro.  
  
First, we define the **total cost** which is the sum of all the fixed
costs corresponding to the construction and the implementation of the
plant. It includes:

### Compensation cost

This cost represents the value to compensate land owners in case of
plants components implementation according to current Italian
legislation. It is calculated with this formula:  

![image-alt](r_green_hydro_financial_fcompensation.png)

where L<sub>v</sub> is a raster map with the land use value
\[currency/ha\];  
T<sub>r</sub> is a raster map with the tributes \[currency/ha\];  
V<sub>u</sub> is a raster map with the value upper part of the soil
\[currency/ha\];  
r is a scalar with the interest rate (default value: 0.03);  
n is the life of a hydropower plant \[year\] (default value: 30);  
γ is a scalar (default value: 5/4);  
w<sub>e</sub> is a scalar with the average width excavation \[m\]
(default value: 2);  
res is a scalar with the raster resolution  

The V<sub>u</sub> raster map is computed with the formula:  

![image-alt](r_green_hydro_financial_fvu.png)  

where S<sub>v</sub> is a raster map with the stumpage value
\[currency/ha\];  
Rot is a raster map with the value rotation period per land use
type \[year\];  
Y is a raster map with the average year \[year\]

The user can directly add the maps L<sub>v</sub>, T<sub>r</sub>,
S<sub>v</sub>, Rot and Y as inputs. Otherwise, the maps can be
computed using the land use raster map and reclassifying the values
with the module r.reclass. The program creates the reclassified maps
if the user provides the input text files for each category (the
input data is the path of the text file). Here is an example of a
text file to create the landvalue raster map, the costs are in
currency/ha:  

```sh
1 = 0 rocks, macerated, glaciers
2 = 0 urbanized areas, infrastructure
3 = 0 shores
4 = 0 waters
5 = 200 gardens
6 = 4000 mining areas
7 = 2000 agricultural areas
8 = 1500 meadows
9 = 1000 areas with predominantly pastoral value
10 = 3000 forestry land
```

Once the calculation is made, a new column with the compensation cost
is added in the table of the input map with potential plants. A raster
map with the compensation cost can also be computed, as well as a
raster map with the value upper part of the soil (see Optional
section).  

### Excavation cost

This cost concerns the works of digging to implement channels. It is
calculated as followed:  

![image-alt](r_green_hydro_financial_fexcavation.png)  

where S is a raster map with the slope in \[%\];  
Ψ is a raster map with values of minimum excavation costs
\[currency/mc\];  
Φ is a raster map with values of maximum excavation costs
\[currency/mc\];  
w is the width of the excavation \[m\] (default value: 2);  
d is the depth of the excavation \[m\] (default value: 2);  
l is the length of the excavation \[m\] which depends on the
channels lengths  

If the user hasn't got the raster maps Ψ and Φ, the latter can be
computed from the land use raster map if the user provides a text file
with the reclassification values (from land use value to excavation
cost (min or max)). It is the same principle as the one explained
above for landvalue, tributes, stumpage, rotation period per land use
type and average age.  

The user can choose to put a slope limit (S<sub>lim</sub>) \[%\] above
which the cost will be equal to the maximum cost.  

Then, a new column with the excavation cost is added in the table of
the input map with potential plants. A raster map with excavation cost
can also be computed (see Optional section).  

### Electro-mechanical cost

It is the cost of the electro-mechanical equipment which includes the
turbine, the alternator and the regulator. It is a high percentage of
a small hydropower plant budget (around 30% and 40% of the total
sum).  

We use the Aggidis et al. formula which calculates this cost thanks to
the values of power and head:  

CEM = γ \* power<sup>α</sup> \* head<sup>β</sup> + c

where power is the power of the plant \[kW\];  
head is the head of the plant \[m\];  
α is a power coefficient (default value: 0.56);  
β is a head coefficient (default value: -0.112);  
γ is a coefficient (default value: 15600);  
c is a constant (default value: 0)  

A new column with the electro-mechanical costs is added in the table
of the input map with potential plants.  

### Supply and installation cost for pipeline and electroline

This is the sum of the supply and installation costs for the
derivation channel, the penstock (both compose the pipeline) and the
electroline which links the transformer near the turbine to the
existing grid. The formula is the following:  

![image-alt](r_green_hydro_financial_flinearcost.png)  

where α is the supply and installation costs \[currency/m\] (default
value for pipeline: 310 Euro/m, and for the electroline 250
Euro/m);  
l is the length of the line \[m\], the pipeline length is found in
the structure map and the electroline length is computed thanks to
the grid vector map  

### Power station cost

It concerns the construction cost of the building composing the power
station. It is considered as a percentage of the electro-mechanical
cost:  

CST = α \* CEM

where α is as default 0.52

### Inlet cost

It concerns the construction cost of the water intake structure. It is
considered as a percentage of the electro-mechanical cost:  

CIN = α \*EM

where α is as default 0.38

All these costs define the **Total cost**:  
  
Total cost = (CCM+CL+CEX+CEM+CST+CIN+CGRD)(1+α+β)

where CCM is the \[currency\];  
CL is the Supply and installation cost for pipeline and electroline
\[currency\];  
CEX is the Excavation cost \[currency\];  
CEM is the Electro-mechanical cost \[currency\];  
CST is the Power station cost \[currency\];  
CIN is the Inlet cost \[currency\];  
CGRD is the Grid connection cost, (default is 50000 Euro), that
includes the easement indemnity;  
α is the factor to consider general expenses (default is 0.15);  
β is the factor to consider hindrances expenses (default is 0.10)  

α and β are factors which offset the underestimation of this total cost.
Indeed, some other costs have to be taken into consideration but it's
hard to make a general assessment because they are specific for each
plant. Moreover, for each plant realization there are unexpected events
(hindrances) which make the implementation more complex and expensive.  
  
Then, the module calculates the **maintenance cost per year**, according
to this formula :  
  
maintenance = α \* power<sup>1+β</sup> + c

where power is the power of the plant \[kW\];  
α is a power coefficient (default value: 3871.2);  
β is a power coefficient (default value: 0.45);  
c is a constant (default value: 0)  

The **yearly revenue** corresponds to the money gained selling all the
electricity the plant produces in a year. It is simply calculated as the
product of the power produced in a year by the price of the electricity
(including some coefficients):  
  
revenue = η \* power \* price \* yh \* α + c

where η is the efficiency of the electro-mechanical components
(default value: 0.81);  
power is the installed power of the plant \[kW\];  
price is the energy price \[currency/kW\] (default value: 0.09
Euro/kW);  
yh is the yearly operation hours of the plant \[hours\] (default
value: 6500);  
α is the coefficient to transform installed power to mean power
(default value: 0.5);  
c is a constant (default value: 0)

Finally, all these values allow to calculate the **Net Present Value
(NPV)**. It is the sum of the present values of incoming and outgoing
cash flows over a period of time. It allows to know if there are profits
so if the plant is feasible. It corresponds to:  
  
![image-alt](r_green_hydro_financial_fnpv.png)  

where revenue is the yearly revenue value \[currency/year\];  
maintenance is the yearly maintenance value \[currency/year\];  
Total cost is the total cost of the plant \[currency\];  
n the number of years of the plant \[year\] (default value: 30);  
γ is a coefficient which assesses the cost of interest and
amortization. It is defined as:  

![image-alt](r_green_hydro_financial_fgamma.png)  

where r is the interest rate (default value: 0.03)  

More concretely, the program computes the following results:  

- the input map with the structure of the plants has an updated table
with the different costs of construction and implementation and their
sum (tot\_cost)  

- the created output map shows the structure of the potential plants
with a re-organized table. The latter doesn't make the difference
between derivation channel and penstock. Each line gives the
intake\_id, plant\_id, side (structures are computed on both sides of
the river), power (kW), gross\_head (m), discharge (m<sup>3</sup>/s),
tot\_cost (total cost for construction and implementation), yearly
maintenance cost, yearly revenue, net present value (NPV) and
max\_NPV. The structure of potential plants is given for each side of
the river, max\_NPV is 'yes' for the side with the highest NPV and
'no' for the other side.  

- the input map with the segments of the plants has an updated table
with the total cost, yearly maintenance cost, yearly revenue and the
net present value. The parameter "segment\_basename" (in input column)
allows to add a prefix at the column names in order to show the
results for different cases in the same table without overwriting the
columns.  

- in the Optional section, there is the possibility to create three
raster maps showing the compensation, excavation and upper part of the
soil values

## EXAMPLE

This example is based on the case-study of Gesso and Vermenagna valleys
in the Natural Park of the Maritime Alps, Piedmont, Italy.  
  
Here in black you can see the input vector file techplants with the
structure of the potential plants and the technical value of power
(including head losses and efficiencies, computed by
r.green.hydro.technical) computed by r.green.hydro.technical. The vector
map with the segments of the river potentialplants is also visible in
blue in this picture, as well as the vector map with the intakes and
restitutions of the plants (in red).

![image-alt](r_green_hydro_financial_input.png)  
structure of the potential plants

The following command updates the table of structplants and segplants
adding the costs:  
  
Notes:  
The rules files for the reclassification needed for the following
command can be created as shown in the section NOTES above for the
rules\_landvalue.  
To create the other rule files this link might be helpful:
[r.category](https://grass.osgeo.org/grass-stable/manuals/r.category.html)  
The file techplants (input vector map with the structure of the plants)
has to be created for example by r.green.hydro.technical before entering
the following code.

```sh
r.green.hydro.financial
plant=potentialplants
struct=techplants
struct_column_head=net_head
landuse=landuse
rules_landvalue=/pathtothefile/landvalue.rules
rules_tributes=/pathtothefile/tributes.rules
rules_stumpage=/pathtothefile/stumpage.rules
rules_rotation=/pathtothefile/rotation.rules
rules_age=/pathtothefile/age.rules
slope=slope
rules_min_exc=/pathtothefile/excmin.rules
rules_max_exc=/pathtothefile/excmax.rules
electro=grid
output_struct=ecoplants
compensation=comp
excavation=exc
upper=upper
```

It also creates four new raster maps (ecoplants, comp, exc and upper):  

- ecoplants which shows the structure of the potential plants. The
table contains these four columns (total cost, maintenance cost,
revenue and NPV):  

![image-alt](r_green_hydro_financial_tableeco.png)  
table of the output raster map ecoplants

The same columns are added for the input map with the segments
(potentialplants). In the table of the input map with the structure
(techplants), the different costs which compose the total cost are
added in columns (but not the four previous values).  

- comp which shows the compensation values (in currency) for each
land use:  

![image-alt](r_green_hydro_financial_compmap.png)  
output raster map with compensation values

- upper which shows the values of the upper part of the soil (in
currency) for each land use  

- exc which shows the excavation value (in currency) for each land
use  

These two last maps look like comp, but with their corresponding
values.  

## SEE ALSO

*[r.green.hydro.discharge](r.green.hydro.discharge.md)  
[r.green.hydro.delplants](r.green.hydro.delplants.md)  
[r.green.hydro.theoretical](r.green.hydro.theoretical.md)  
[r.green.hydro.optimal](r.green.hydro.optimal.md)  
[r.green.hydro.recommended](r.green.hydro.recommended.md)  
[r.green.hydro.structure](r.green.hydro.structure.md)  
[r.green.hydro.technical](r.green.hydro.technical.md)*

## REFERENCE

*The costs of small-scale hydro power production: Impact on the
development of existing potential*, p.2635, Aggidis et Al, 2010  
  
Text on expropriation for public utility D.P.R. n. 327/2001, updated in
2013  
  
The excavation costs are found in the price list of the Piedmont Region
for public works  
  
The costs of intake and civil works are based on analysis of technical
documents for mini-hydro projects in Italy  
  
The calculation of the yearly maintenance cost is based on the report
AEEG for the Polytechnic University of Milan  
  
## AUTHORS

Pietro Zambelli (Eurac Research, Bolzano, Italy), Sandro Sacchelli
(University of Florence, Italy), manual written by Julie Gros.
