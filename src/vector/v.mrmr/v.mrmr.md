## DESCRIPTION

***v.mrmr*** is a simple GUI for exporting data to the Minimum
Redundancy Maximum Relevance (mRMR) feature selection command line tool
(Peng et al., 2005). mRMR is designed to select features that have the
maximal statistical "dependency" on the classification variable, while
simultaneously minimizing the redundancy among the selected features.

## NOTES

The command line tool needs to be installed separately in a location
that is recognized by the system or in the PATH. The command line tool
can be installed on windows (binaries available), linux and OS X (needs
compilation). Installation instructions are provided on [Peng's
Website](https://home.penglab.com/proj/mRMR).

The module requires data within a vector attribute table to be arranged
in a specific order. The classification variable (i.e., class labels)
need to be in the first column, except for the cat attribute which is
not exported. The class label also needs to be in numerical form, i.e.,
1, 2, 3.... rather than 'forest' or 'urban'. Also, the attribute table
should not contain any missing values because this causes an erroneous
mRMR result.

The algorithm outputs a tab-separated list of attributes, ranked by the
most important feature first. The *method* parameter allows a choice
between the Maximum Information Difference (MID) and Mutual Information
Quotient (MIQ) feature evaluation criteria, which respectively represent
the relevancy and redundancy of the features. The algorithm also shows
the ranking of the features based on the conventional maximum relevance
method. Additional user options include *nfeatures* which specifies the
number of features that you want to select; *nsamples* limits the
maximum number of samples to base the feature selection, and *maxvar*
limits the maximum number of attributes, both of which can therefore
reduce the computation for very large datasets. *threshold* is the
discretization threshold to apply to the continuous variable data, i.e.,
mean +/- threshold \* standard deviation. *layer* is the attribute layer
to be used in the feature selection process.

## EXAMPLE

```sh
v.mrmr.py vector=vector_layer layer=1 thres=1.0 nfeatures=50 \
      nsamples=10000 maxvar=10000 method=MID
```

## REFERENCES

Peng, H.; Fulmi Long; Ding, C., "Feature selection based on mutual
information criteria of max-dependency, max-relevance, and
min-redundancy," in Pattern Analysis and Machine Intelligence, IEEE
Transactions on , vol.27, no.8, pp.1226-1238, Aug. 2005

## AUTHOR

Steven Pawley
