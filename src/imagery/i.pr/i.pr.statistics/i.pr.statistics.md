## DESCRIPTION

Calculate feature statistics. Given an input file of features
(**features**), calculate the Kolgomorov-Smirnov test and t-test for
each class of each feature. If the features contain principal components,
calculate the variance explained by them. If there are multiple principal
component models (for multiple layers), the analysis is performed on
only one layer (**layer**). The **npc** parameter is used to limit
the analysis to the first npc principal components.

## AUTHORS

Stefano Merler, FBK, Trento, Italy
