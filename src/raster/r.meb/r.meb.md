## DESCRIPTION

The Multivariate Environmental Bias (MEB) takes the medium conditions in
an reference area *N* and computes how much conditions in a subset of
*N* (*S*) deviate from these medium conditions (van Breugel et al.
2015). This can for example be used to see how well conditions in the
protected areas of a country represent conditions in the whole country.

The measure is based on the Multivariate Environmental Similarity
(*MES*) surface, which was proposed by Elith et al (2010). The MESS
measures the similarity in a set of variables between any given location
in an area and the locations in a reference area.

The first step to compute the MES for a location *P* is to calculate how
similar conditions in *P* are compared to the conditions in the
reference area *N*, based on variable *V<sub>i</sub>*. The similarity is
expressed as the deviation from *V<sub>i</sub>* in *P* from the median
of *V<sub>i</sub>* in *N*. This is done for all variables of interest
(V<sub>1</sub>, V<sub>2</sub>, ...V<sub>j</sub>).

In the original equation proposed by Elith et al (2010) the final *MES*
in location *P* is computed as the minimum of the similarity values
(*IES<sub>minimum</sub>*) of the individual variables (*V<sub>j</sub>*)
in *P*. However, to compute the *MEB* using the mean or median may be a
better choice as they take into account the similarity along all
environmnetal axes and not only the one that deviates most. The user
therefore has the option to use the mean (*IES<sub>mean</sub>*) or
median (*IES<sub>median</sub>*) of the *IES* instead (there is still the
option to use the minimum as well).

The *MEB* is computed as the absolute difference of the median of the
*MES* in the whole target area (MES<sub>N</sub>) and the median of the
*MES* in the subset (*MES<sub>S</sub>*), divided by the median absolute
deviation
(*[MAD](https://en.wikipedia.org/wiki/Median_absolute_deviation)*) of
the *MES* in *N*. It is also possible to compute the bias based on the
individual variables (IEB) in which case the *IES* instead of the *MES*
is used.

![image-alt](r_meb_concept.png)

The addon creates a MES layer and a table (saved to csv file) with the
median value of each variable in the region and in the reference area,
the median absolute deviation (mad) and the environmental bias (eb).
Optionally, this can be computed for the individual variables as well.
The user has the option to have the addon compute the *MEB* based on the
*MES* computed using the minimum, average and/or median of the IES
layers (see above)

## NOTE

Input variables are expected to be or to represent continuous variables.

## Example

In the example below the *MEB* is computed for a map 'forestmap' which
gives the distribution of forest (1) and other land cover types (0). As
environmental variables, the bio1, bio3 and bio9 are used.

```sh
r.meb -m -n -o env=bio_1,bio_3,bio_9 ref=forestmap
output=Test file=Test
Median Test_MES_mean (all region) = 47.338
Median Test_MES_mean (ref. area) = 69.798
MAD Test_MES_mean (all region) = 14.594
EB = 1.539

Median Test_MES_median (all region) = 45.712
Median Test_MES_median (ref. area) = 69.897
MAD Test_MES_median (all region) = 18.786
EB = 1.287

Median Test_MES_minimum (all region) = 20.364
Median Test_MES_minimum (ref. area) = 55.807
MAD Test_MES_minimum (all region) = 15.096
EB = 2.348

The results are written to Test.csv
```

## CITATION

van Breugel P, Kindt R, Lillesø J-PB, van Breugel M (2015) Environmental
Gap Analysis to Prioritize Conservation Efforts in Eastern Africa. PLoS
ONE 10(4): e0121444. doi: 10.1371/journal.pone.0121444

## REFERENCES

- Elith, J, Kearney, M, and Phillips, S. 2010. The art of modelling
    range-shifting species. Methods in Ecology and Evolution 1:330-342.
- van Breugel P, Kindt R, Lillesø J-PB, van Breugel M. 2015.
    Environmental Gap Analysis to Prioritize Conservation Efforts in
    Eastern Africa. PLoS ONE 10(4): e0121444. doi:
    10.1371/journal.pone.0121444.

## SEE ALSO

*[r.mess](r.mess.md)*

## AUTHOR

Paulo van Breugel, paulo at ecodiv.earth
