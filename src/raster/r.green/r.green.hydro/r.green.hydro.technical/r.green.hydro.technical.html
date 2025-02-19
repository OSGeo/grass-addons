<h2>DESCRIPTION</h2>
<em>r.green.hydro.technical</em> calculates the hydropower potential considering technical constrains that include head losses, efficiencies of the turbine, the shaft, the alternator and the transformer.<br><br>
The input is a vector map with the intakes and restitutions of the potential plants as the one computed by r.green.hydro.recommended. The output is a vector map with the structure (derivation channel and penstock) for each potential plant with the value of the corrected power including these technical constrains.

<h2>NOTES</h2>

Firstly, the module computes the <b>structure</b>. As the current potential concerns especially small hydropower (inferior to 20 MW), the structure suggested is the one for small hydropower detailed in the picture below. It is composed of an intake (A) which diverts water from the river. This water is conveyed into a derivation channel (B) with a very low slope and arrives in a forebay tank (C) which regulates the fluctuation of discharge. Finally, the penstock (D) conveys the water with the highest possible head to the turbine-alternator group (E) which produces electricity. The water is then released into the river (restitution F). We use the following vocabulary: the structure of the plant corresponds to the part with the derivation channel, the forebay tank and the penstock, whereas the segment of the plant corresponds to the part of the river (water not diverted) between the intake (A) and the restitution (F).<br><br>

<center>
<img src="r_green_hydro_technical_picstruct.png" alt="structure"><br>
Structure of the plants considered in the module
</center><br><br>

The power is maximized for the highest head in the penstock so the derivation channel is computed along the same quote (the low slope is neglected here) until the point which maximizes the head along the penstock. The structure is computed for both sides of the river in order to determine which one produces the most power.<br><br>

Using the computed structure, the module calculates the <b>head losses</b>:<br><br>
<blockquote>- in the derivation channel <br>
<blockquote>There are regular losses calculated thanks to Manning's formula: <i>
&Delta;h<SUB>deriv</SUB>=L*(Q/(ks*A*Rh<SUP>2/3</SUP>))<SUP>2</SUP></i><br>
<blockquote>where Rh is the hydraulic radius (m),<br>
A the cross sectional area of flow (m<SUP>2</SUP>),<br>
L is the channel length (m),<br>
Q is the discharge (m<SUP>3</SUP>/s),<br>
ks the Strickler coefficient (m<SUP>1/3</SUP>/s), we consider steel as default parameter, with ks=75 m<SUP>1/3</SUP>/s.<br><br></blockquote></blockquote>

- in the forebay tank<br>
<blockquote>There are singular losses caused by the change of section in the forebay tank and the change of direction in the penstock (steep slope).<br>

In any case, singular head losses are expressed like this: <i>&Delta;h<SUB>sing</SUB>=K*V<SUP>2</SUP>/(2g)</i><br>
<blockquote>where V is the velocity (m/s), <br>
g the gravity term (9,81 m/s<sup>2</sup>), <br>
K is a coefficient determined according to the kind of singularity.</blockquote>

In our case, the singular losses are the sum of the ones for these three phenomena:<br>
<blockquote>- enlargement at the entrance of the forebay tank:  K<SUB>1</SUB>=1 and V=1 m/s<br>
- narrowing at the exit of the forebay tank: K<SUB>2</SUB>=0.5 and V=4Q/(&pi;D<SUP>2</SUP>) m/s<br>
- bend at the beginning of the penstock: K<SUB>3</SUB>=(gross head/L)<SUP>2</SUP>+2*sin(ASIN(gross head/L)/2)<SUP>4</SUP> and V=4Q/(&pi;D<SUP>2</SUP>) m/s
<br><br></blockquote></blockquote>

- in the penstock<br>
<blockquote>There are regular losses calculated thanks to this formula: <i>&Delta;h<SUB>pen</SUB>=(f*8*L*Q<SUP>2</SUP>)/(&pi;<SUP>2</SUP>*D<SUP>5</SUP>*g)</i><br>
<blockquote>where L is the penstock length (m), <br>
D is the penstock diameter (m), <br>
Q is the discharge (m<SUP>3</SUP>/s), <br>
f is the Darcy-Weisbach friction coefficient, which can be determined by Colebrooke formula. We consider steel by default with absolute roughness of &epsilon; = 0,015 mm.<br><br></blockquote></blockquote></blockquote>

Then, the module chooses the <b>turbine</b> which is the most accurate for each plant. The data of possible turbines of which you have to enter the path into the turbine_folder=string field, are gathered in the folder turbine. For each turbine there is a text file with the ranges of discharge and head required to use it. There is also the efficiency in function of QW/Q_design. The turbine is designed to work at Q_design and QW corresponds to the real discharge which flows in the turbine. As we don't consider the duration curves but only the mean annual discharge, we assume that QW=Q_design.<br><br>

If you want to create an additional text file for another turbine model, the file has to have this scheme with the correct information at the corresponding lines:<br>
<blockquote><pre>TURBINE 	           ALPHA_C
Name of the turbine	   Value of alpha_c
Q_MIN		           Q_MAX
Value of q_min	           Value of q_max
DH_MIN		           DH_MAX
Value of dh_min	           Value of dh_max
QW/Q_design	           ETA
Coordinates of the curve efficiency=f(QW/Q_design)<br><br></pre></blockquote>

In the turbine folder there is already the text file called list with a large choice of turbines available. You have to enter the path of the list file into the turbine_list=string field of the GUI. But the user can also create his own text file that has to have the same structure with a list of the names of the turbines he has selected and wants to be considered. <br><br>

To choose the turbine, the module first selects the turbines with ranges of discharge and head containing the values of the corresponding potential plant. Among these turbines, it chooses the one which has the best efficiency for QW=Q_design.<br><br>

Thus the efficiency of the turbine is found. The global efficiency also includes the <b>efficiencies</b> of the shaft, the alternator and the transformer which can be chosen or they are respectively equal to 1, 0.96 and 0.99 by default.<br><br>

Finally, the corrected value of power which can be exploited is calculated.<br>
It corresponds to <i>P=&eta;*&rho;*g*Q*&Delta;h<SUB>net</SUB></i><br>
<blockquote>where &eta; is the global efficiency of the plant (turbine, shaft, alternator and transformer),<br>
&rho; the density of water (1000 kg/m<sup>3</sup>), <br>
g the gravity term (9,81 m/s<sup>2</sup>), <br>
Q the discharge (m<SUP>3</SUP>/s),<br>
&Delta;h<SUB>net</SUB> the net head, that means the gross head minus head losses<br><br></blockquote>

The output map of the module is the one with the structure for each plant, including in the <b>table</b> the data of:<br>
<blockquote>- discharge (m<sup>3</sup>/s)<br>
- gross head (m)<br>
- kind of the channel: derivation (conduct) or penstock<br>
- side of the river (option0 or option1)<br>
- diameter of the channel (m)<br>
- losses in the channel (m)<br><br>

Moreover, only in the penstock's line of the structure, there are:<br>
- singular losses (m) in the forebay tank between the derivation channel and the penstock<br>
- the total losses (m) for each structure, which are the sum of the regular losses in the derivation channel and in the penstock and the singular losses in the forebay tank<br>
- net head (m), which is the gross head minus the total losses<br>
- hydraulic power (hyd_power, in kW) which is the power considering the gross head and a global efficiency equal to 1. It corresponds to the theoretical power (the maximum)<br>
- efficiency of the selected turbine (e_turbine)<br>
- kind of the selected turbine (turbine)<br>
- power (kW) which can be exploited considering the technical constrains<br>
- global efficiency (power/hyd_power)<br>
- max_power: yes or no, yes for the side (option1 or option0) which produces the most power</blockquote>


<h2>EXAMPLE</h2>
This example is based on the case-study of Gesso and Vermenagna valleys in the Natural Park of the Maritime Alps, Piedmont, Italy.<br><br>

Here is the input vector map potentialplants with the intakes and restitutions (in red) computed by r.green.hydro.recommended. The vector map with the segments of river is also visible in blue in this picture. These potential plants have a maximum length of 800 m and a distance of 800 m between them.

<center>
<img src="r_green_hydro_technical_input.png" alt="input"><br>
Potential intakes and restitutions
</center><br><br>

The following command that you can either put in the command console or the GUI of r.green.hydro.technical computes the structure of the potential plants for each side of the river and includes the corrected power on the output map table:<br>
<div class="code"><pre>r.green.hydro.technical plant=potentialplants elevation=elevation output_struct=techplants output_plant=segmentplants
turbine_folder=/pathtothefileoftheturbine_folder  turbine_list=/pathtothefileoftheturbine_list</pre></div><br>
The result is shown in the following vector map called techplants. The table of this map is completed as explained in the end of the NOTES part.<br><br>

<center>
<img src="r_green_hydro_technical_output.png" alt="output"><br>
Structure of the potential plants in black (techplants map)
</center><br><br>


<h2>SEE ALSO</h2>
<em>
<a href="r.green.hydro.discharge.html">r.green.hydro.discharge</a><br>
<a href="r.green.hydro.delplants.html">r.green.hydro.delplants</a><br>
<a href="r.green.hydro.theoretical.html">r.green.hydro.theoretical</a><br>
<a href="r.green.hydro.recommended.html">r.green.hydro.recommended</a><br>
<a href="r.green.hydro.structure.html">r.green.hydro.structure</a><br>
<a href="r.green.hydro.optimal.html">r.green.hydro.optimal</a><br>
<a href="r.green.hydro.financial.html">r.green.hydro.financial</a><br>
</em>

<h2>REFERENCE</h2>
Picture of the plant structure taken from Micro-hydropower Systems - A Buyer's Guide, Natural Resources Canada, 2004<br>
Sources for the theory : Courses of French engineering schools ENSE3 Grenoble-INP (Hydraulique des ecoulements en charge) and ENGEES Strasbourg (Hydraulique a surface libre)

<h2>AUTHORS</h2>

Giulia Garegnani (Eurac Research, Bolzano, Italy), Julie Gros (Eurac Research, Bolzano, Italy),
manual written by Julie Gros.
