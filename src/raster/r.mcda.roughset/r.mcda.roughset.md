## DESCRIPTION

*r.mcda.roughset* is the python implementation of the dominance rough
set approach (Domlem algorithm) in GRASS GIS environment. It requires
the following input:  
1\. the geographical criteria constituting the information system for
the rough set analysis; they have to describe environmental, economic or
social issues(**criteria**=*name\[,name,...\]*);  
2\. the preference (**preferences**=*character*)for each criteria used
in analysis (gain or cost with comma separator)  
3\. the theme in which areas with the issues to be studied are
classified (with crescent preference values) (**decision**=*string*).

An information system is generated and Domlem algorithm is applied for
extraction a minimal set of rules.

The algorithm builds two text files (**outputTxt**=*name*): the first
with isf extension for more deep analysis with non geographic software
like 4emka and JAMM ; the second file with rls extension hold all the
set of rules generate. An output map (**outputMap**=*string*)is
generated for region classification with the rules finded and the
criteria stored in GRASS geodb.

## NOTES

The module can work very slowly with high number of criteria and sample.
For bug please contact Gianluca Massei (g\_mass@libero.it)

## REFERENCE

1. Greco S., Matarazzo B., Slowinski R.: *Rough sets theory for
    multicriteria decision analysis*. European Journal of Operational
    Research, 129, 1 (2001) 1-47.

2. Greco S., Matarazzo B., Slowinski R.: *Multicriteria classification
    by dominance-based rough set approach*. In: W.Kloesgen and J.Zytkow
    (eds.), Handbook of Data Mining and Knowledge Discovery, Oxford
    University Press, New York, 2002.

3. Greco S., Matarazzo B., Slowinski, R., Stefanowski, J.: *An
    Algorithm for Induction of Decision Rules Consistent with the
    Dominance Principle*. In W. Ziarko, Y. Yao (eds.): Rough Sets and
    Current Trends in Computing. Lecture Notes in Artificial
    Intelligence 2005 (2001) 304 - 313. Springer-Verlag

4. Greco, S., B. Matarazzo, R. Slowinski and J. Stefanowski: *Variable
    consistency model of dominance-based rough set approach.* In
    W.Ziarko, Y.Yao (eds.): Rough Sets and Current Trends in Computing.
    Lecture Notes in Artificial Intelligence 2005 (2001) 170 - 181.
    Springer-Verlag

5. <https://en.wikipedia.org/wiki/Dominance-based_rough_set_approach> -
    “Dominance-based rough set approach”

6. <https://fcds.cs.put.poznan.pl/IDSS/software/software_and_projects.htm>
    - Software from Laboratory of intelligent decision support system in
    Poznań University of Technology

## SEE ALSO

*r.mcda.fuzzy, r.mcda.electre, r.mcda.regime, r.to.drsa, r.in.drsa*

## AUTHORS

Antonio Boggia - Gianluca Massei  
Department of Economics and Appraisal - University of Perugia - Italy
