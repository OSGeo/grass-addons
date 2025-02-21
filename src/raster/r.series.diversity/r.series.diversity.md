## DESCRIPTION

*r.series.diversity* computes one or more diversity indices based on 2
or more input layers. Each layer should represents a species (or other
categories being used), and its raster values the category count/value.
The name of the output layers will consist of the base name provided by
the user. Currently implemented are the Renyi entropy index and a number
of specialized cases of the Renyi enthropy, viz.the species richness,
the Shannon index, the Shannon based effective number of species (ENS),
the Simpson index (inverse and gini variants), pielou's eveness
(Legendre & Legendre, 1998).

### The Renyi enthropy

This index quantify the diversity, uncertainty, or randomness of a
system. The user can define the order of diversity by setting the order
(**alpha**) value. The order of a diversity indicates its sensitivity to
common and rare species. The diversity of order zero ( **alpha = 0**) is
completely insensitive to species frequencies and is better known as
species richness. Increasing the order diminishes the relative weights
of rare species in the resulting index (Jost 2006, Legendre & Legendre
1998). The name of the output layer is composed of the basename + renyi + alpha.

### Richness

The species richness is simply the count of the number of layers. It is
a special case of the Reny enthropy: `S = exp(R0)`, whereby `S` is the
species richness `R0` the renyi index for `alpha=0`. The name of the
output layer is composed of the basename + richness.

### Shannon index

The Shannon (also called the Shannon-Weaver or Shannon-Wiener) index is
defined as `H' = -sum(p_i x log(p_i))`, where `p_i` is the
proportional abundance of species `i`. The function uses the natural
logarithm (one can also use other bases for the log, but that is
currently not implemented, and doesn't make a real difference). Note the
Shannon index is a special case of the Renyi enthropy for `alpha --> 1`.
The name of the output layer is composed of the basename + shannon.

### Effective number of species (ENS)

This option gives the Shannon index, converted to into equivalent or
effective numbers of species (also known as Hill numbers) (Lou Jost,
2006; Chase and Knight, 2013). The Shannon index, and other indice, can
be converted so they represent the number of equally abundant species
necessary to produce the observed value of diversity (an analogue the
concept of effective population size in genetics). An advantage of the
ENS is a more intuitive behavious, e.g., if two communities with equally
abundant but totally distinct species are combined, the ENS of the
combined community is twice that of the original communities. See for an
explanation and examples this [blog
post](http://www.loujost.com/Statistics-and-Physics/Diversity-and-Similarity/EffectiveNumberOfSpecies.htm)
or [this
one](https://jonlefcheck.net/2012/10/23/diversity-as-effective-numbers).
The name of the output layer is composed of the basename + ens.

### Pielou's eveness (equitability) index

Species evenness refers to how close in numbers each species in an
environment are. The evenness of a community can be represented by
Pielou's evenness index, which is defined as `H' / Hmax`. H' is the
Shannon diversity index and Hmax the maximum value of H', equal to
log(species richness). Note that a weakness of this index is its
dependence on species counts, and more specifically that it is a ratio
of a relatively stable index, H', and one that is strongly dependent on
sample size, S. The name of the output layer is composed of the basename + pielou.

### Simpson's index of diversity

The Simpson's index is defined as `D = sum p_i^2`. This is equivalent to
`-1 * 1 / exp(R2)`, with `R2` the renyi index for `alpha=2`. With this
index, 0 represents infinite diversity and 1, no diversity. As this is
counterintuitive behavior for a diversity index, we use `1 - D` (Gini,
1912; Simpson, 1949). This is also called the probability of
interspecific encounter (PIE) or the Gini–Simpson index. The index
represents the probability that two individuals randomly selected from a
sample will belong to different species. The value ranges between 0 and
1, with greater values representing greater sample diversity. The name
of the output layer is composed of the basename + ginisimpson.

### Inverse Simpson index (Simpson's Reciprocal Index)

An alternative way to overcome the problem of the counter-intuitive
nature of Simpson's Index is to use the inverse Simpson index, which is
defined as `ID = 1 / D)`. The lowest value of this index is 1 and
represent a community containing only one species. The higher the value,
the greater the diversity. The maximum value is the number of species in
the sample. The name of the output layer is composed of the basename +
invsimpson.

## NOTES

Note that if you are interested in the landscape diversity, you should
have a look at the [r.diversity](r.diversity.md) addon or the various
related r.li.\* addons (see below). These functions requires one input
layer and compute the diversity using a moving window.

Currently when working with very large raster layers and many input
layers, computations can take a long time. Increasing the number of
threads (parameter **nprocs**) and increasing the memory (parameter
**memory**) can speed up the calculations considerably.

See the blog post [Tree species diversity
distribution](https://ecodiv.earth/post/tree-species-diversity-distribution/)
for a possible application of this addon.

## EXAMPLES

Suppose we have five layers, each representing number of individuals of
a different species. To keep it simple, let's assume individuals of all
five species are homogeneous distributed, with respectively 60, 10, 25,
1 and 4 individuals / raster cell densities.

```sh
r.mapcalc "spec1 = 60"
r.mapcalc "spec2 = 10"
r.mapcalc "spec3 = 25"
r.mapcalc "spec4 = 1"
r.mapcalc "spec5 = 4"
```

Now we can calculate the renyi index for alpha is 0, 1 and 2 (this
should be 1.61, 1.06 and 0.83 respectively)

```sh
r.series.diversity -r in=spec1,spec2,spec3,spec4,spec5 out=renyi alpha=0,1,2

r.info -r map=renyi_Renyi_0_0
min=1.6094379124341
max=1.6094379124341

r.info -r map=renyi_Renyi_1_0
min=1.05813420869358
max=1.05813420869358

r.info -r map=renyi_Renyi_2_0
min=0.834250021537946
max=0.834250021537946
```

You can also compute the species richness, shannon, inverse simpson and
gini-simpson indices

```sh
r.series.diversity -s -h -p -g in=spec1,spec2,spec3,spec4,spec5 out=biodiversity
```

The species richness you get should of course be 5. The shannon index is
the same as the renyi index with `alpha=1 (1.06)`. The inverse simpson
and gini-simpson should be 2.3 and 0.57 respectively. Let's check:

```sh
r.info -r map=biodiversity_richness
min=5
max=5

r.info -r map=biodiversity_shannon
min=1.05813420869358
max=1.05813420869358

r.info -r map=biodiversity_invsimpson
min=2.30308613542147
max=2.30308613542147

r.info -r map=biodiversity_ginisimpson
min=0.5658
max=0.5658
```

## SEE ALSO

*[r.li](https://grass.osgeo.org/grass-stable/manuals/r.li.html),
[r.li.pielou](https://grass.osgeo.org/grass-stable/manuals/r.li.pielou.html),
[r.li.renyi](https://grass.osgeo.org/grass-stable/manuals/r.li.renyi.html),
[r.li.shannon](https://grass.osgeo.org/grass-stable/manuals/r.li.shannon.html),
[r.li.simpson](https://grass.osgeo.org/grass-stable/manuals/r.li.simpson.html)*

## REFERENCES

- Chase and Knight (2013). "Scale-dependent effect sizes of ecological
    drivers on biodiversity: why standardised sampling is not enough".
    Ecology Letters, Volume 16, Issue Supplement s1, pgs 17-26.
- Gini, C. 1912. Variabilità e mutabilità. Reprinted in Memorie di
    metodologica statistica (Ed. Pizetti E, Salvemini, T). Rome:
    Libreria Eredi Virgilio Veschi 1.
- Jost L. 2006. Entropy and diversity. Oikos 113:363-75
- Legendre P, Legendre L. 1998. Numerical Ecology. Second English
    edition. Elsevier, Amsterdam
- Simpson, E. H. 1949. Measurement of Diversity Nature 163

## AUTHOR

Paulo van Breugel, <https://ecodiv.earth>  

HAS green academy University of Applied Sciences  
[Innovative Biomonitoring research
group](https://www.has.nl/en/research/professorships/innovative-bio-monitoring-professorship/)  
[Climate-robust Landscapes research
group](https://www.has.nl/en/research/professorships/climate-robust-landscapes-professorship/)
