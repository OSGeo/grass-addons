## DESCRIPTION

*v.percolate* implements continuum percolation analysis. It identifies
clusters of point locations at multiple threshold distances and outputs
various statistics into plain text CSV files. See notes for the
difference between *v.percolate* and *v.cluster*.

For each input point in an input vector map *v.percolate* outputs the
following information at each threshdold distance:

- `Cat`  
    Cat value.
- `<fieldname>`  
    The ID of the point in a chosen field in the input vector map.
- `X`  
    X coordinate (easting).
- `Y`  
    Y coordinate (northing).
- `Membership`  
    Cluster membership (cluster ID).
- `FirstChange`  
    Iteration at which the point first joined a cluster.
- `LastChange`  
    Iteration at which the point most recently joined a new cluster.
- `NChanges`  
    Number of changes of cluster membership.
- `FirstDistance`  
    Distance at which the point first joined a cluster.
- `LastDistance`  
    Distance at which the point most recently joined a new cluster.
- `MaxConCoeff`  
    Maximum connection coefficient obtained.
- `LastGroupConnected`  
    The cluster ID of the most recently connected cluster (the point
    itself may not have changed clusters)
- `LastDistanceConnection`  
    Distance at which the most recently connected cluster joined (the
    point itself may not have changed clusters))

For each cluster formed or already in existence at each threshold
distance *v.percolate* outputs:

- `Cluster`  
    The cluster ID.
- `Birth`  
    Iteration at which the cluster was formed.
- `BirthDist`  
    Distance at which the cluster was formed.
- `Death`  
    Iteration at which the cluster was absorbed into another cluster and
    so ceased to exist as an independent entity.
- `DeathDist`  
    Distance at which the cluster was absorbed into another cluster and
    so ceased to exist as an independent entity.
- `Longevity`  
    Number of iterations during which the cluster existed as an
    independent entity.
- `MaxSize`  
    The number of points in the cluster just before it was absorbed into
    another cluster.
- `Wins`  
    The number of occasions when this cluster continued to exist after
    joining with another cluster because, depending on the rule chosen,
    it was either the larger cluster or the older cluster.

In addition to identifying clusters, *v.percolate* also computes an
*experimental* Connection Coefficient for each point location. This
numerical value is intended to capture a property roughly analogous to
Betweeness Centrality in network analysis. The Connection Coefficient is
smaller if a point location joins 2 small clusters, or 1 large and 1
small cluster, and greater if it joins 2 large clusters.

By default, the series of distance thresholds at which the above
statistics will be reported is determined by setting **min**, **inc**
and **max**. *v.percolate* will never proceed beyond the maximum
distance threshold, but it may cease to provide output before that
distance is reached if the **-e** flag is set to force termination once
all input points are connected in one cluster.

If **interval** is set to a positive non-zero value then *v.percolate*
no longer outputs statistics at fixed distance thresholds. Instead, it
outputs statistics for every *N*th node-pair that is joined in a
cluster, where *N* is the value given as the **interval**. In general
this is less useful than the default behaviour, but it has application
for certain purposes.

The value of **keep** determines what happens when two clusters, each of
2 or more points, are to be joined. The choice is between absorbing the
more recently formed cluster into the older cluster, or absorbing the
smaller cluster into the large cluster. Setting **keep** to 'oldest'
makes it possible to track the gradual growth of one large
super-cluster, but that is not necessarily most appropriate if the
location of the first cluster is of no real significance.

## NOTES

*v.cluster* already provides several methods for partitioning a set of
points into clusters and will be more appropriate for most purposes.

*v.percolate* has a very specific purpose, which is to facilitate
continuum percolation analysis of point locations, as for example
described in Arcaute et al. 2016. The emphasis of this form of analysis
is less on finding optimal partitioning of points into clusters of
certain sizes and more on observing discontinuities in cluster growth
for the purpose of identifying 'natural' sales of interaction. Thus
*v.percolate* automates the reasonably efficient production and
recording of clusters at multiple threshold distances. For example, on a
2018 mid-range laptop computer *v.percolate* requires around 100 seconds
user time to find clusters in 10,513 points (55,256,328 pairwise
relationships) at 128 different distance thresholds. Since the results
will almost certainly be subject to further analysis in other software,
such as [R](https://www.r-project.org/), a range of information (as
described above) is output into plain text CSV files.

Note that *v.percolate* offers only one method of clustering, which is
based purely on threshold distance: if 2 points are closer than the
threshold distance then they are joined in a cluster. This method will
return the same clusters as the
[DBSCAN](https://en.wikipedia.org/wiki/DBSCAN) method if one relaxes the
latter's requirement for clusters to include a minimum number of points.
As a result, clusters created using *v.percolate* can be joined together
by long strings of points, each with only 2 neighbours within the given
threshold difference, a situation which DBSCAN avoids.

## REFERENCES

- Arcaute, E., C. Molinero, E. Hatna, R. Murcio, C. Vargas-Ruiz, P.
    Masucci and M. Batty (2016). 'Regions and Cities in Britain through
    Hierarchical Percolation'. *ArXiv*:1504.08318v2 \[Physics.Soc-Ph\].
    <https://arxiv.org/abs/1504.08318>.
- Arcaute, E., S. Brookes, T. Brown, M. Lake and A. Reynolds (in
    prep). 'Case studies in percolation analysis: the distribution of
    English settlement in the 11th and 19th centuries compared'. For
    submission to *Journal of Archaeological Science*.
- Lake, M, T. Brown and S. Maddison (2018). 'Percolation robustness
    and the deep history of regionality'. Presentation to [Connected
    Past](https://connectedpast.net/other-events/oxford-2018/programme/),
    Oxford.

## SEE ALSO

*[v.cluster](v.cluster.md)*.

## AUTHORS

Theo Brown, UCL Institute of Archaeology / Helyx Secure Information
Systems, UK

Mark Lake, UCL Institute of Archaeology, University College London, UK
