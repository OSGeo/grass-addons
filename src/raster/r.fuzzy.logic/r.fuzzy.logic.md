## OPTIONS

- **xmap**  
    Name of input x membership operand. This map must be of type FCELL
    with range 0 :1 and may require null values. Otherwise program will
    print error message and stops.
- **ymap**  
    Name of input y membership operand. This map must be of type FCELL
    with range 0 :1 and may require null values. Otherwise program will
    print error message and stops. This map is optional bit is required
    for all operation except NOT
- **operator**  
    A fuzzy set operators are generalization of crisp operators. There
    is more than one possible generalization of every operator. There
    are three operations: fuzzy complements, fuzzy intersections, and
    fuzzy unions. Additional implication operator is also provided.
  - fuzzy intersection (**AND**) use T-norm of given family for
        calculation;
  - fuzzy union (**OR**) use T-conorm of given family for
        calculation;
  - fuzzy complement (**NOT**) fuzzy negation usually 1-x;
  - fuzzy implication (**IMP**) use residuum of given family if
        available;
- **family**  
    T-norms, T-conorms and residuals are a generalization of the
    two-valued logical conjunction, disjunction and implication used by
    boolean logic, for fuzzy logics. Because there is more than one
    possible generalisation of logical operations, *r.fuzzy.logic*
    provides 6 most popular families for fuzzy operations:
  - **Zadeh** with minimum (Godel) t-norm and maximum T-conorm;
  - **product** with product T-norm and probabilistic sum as
        T-conorm;
  - **drastic** with drastic T-norm and drastic T-conorm;
  - **Łukasiewicz** with Łukasiewicz T-norm and bounded sum as a
        T-conorm;
  - **Fodor** with nilpotent minimum as T-norm and nilpotent maximum
        as T-conorm;
  - **Hamacher** (simplified) with Hamacher product as T-norm and
        Einstein sum as T-conorm;
    There is no residuum for drastic and Hamacher families. For more
    details see [Meyer D, Hornik K
    (2009)](http://www.jstatsoft.org/v31/i02);
    [T-norms](https://en.wikipedia.org/wiki/T-norm);

## OUTPUTS

- **output**  
    Map containing result of two-values operations. Map is always of
    type FCELL and contains values from 0 (no membership) to 1 (full
    membership). Values between 0 and 1 indicate partial membership

## SEE ALSO

*[r.fuzzy.set](r.fuzzy.set.md) addon,
[r.fuzzy.system](r.fuzzy.system.md) addon,
[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html)*

## REFERENCES

- Jasiewicz, J. (2011). A new GRASS GIS fuzzy inference system for
    massive data analysis. Computers & Geosciences (37) 1525-1531. DOI
    <https://doi.org/10.1016/j.cageo.2010.09.008>
- Zadeh, L.A. (1965). "Fuzzy sets". Information and Control 8 (3):
    338-353. <https://doi.org/10.1016/S0019-9958(65)90241-X>. ISSN
    0019-9958.
- Novák, Vilém (1989). Fuzzy Sets and Their Applications. Bristol:
    Adam Hilger. ISBN 0-85274-583-4.
- Klir, George J.; Yuan, Bo (1995). Fuzzy sets and fuzzy logic: theory
    and applications. Upper Saddle River, NJ: Prentice Hall PTR. ISBN
    0-13-101171-5.
- Klir, George J.; St Clair, Ute H.; Yuan, Bo (1997). Fuzzy set
    theory: foundations and applications. Englewood Cliffs, NJ: Prentice
    Hall. ISBN 0133410587.
- Meyer D, Hornik K (2009a). Generalized and Customizable Sets in R.
    Journal of Statistical Software, 31(2), 1-27. DOI
    <https://doi.org/10.18637/jss.v031.i02>
- Meyer D, Hornik K (2009b). sets: Sets, Generalized Sets, and
    Customizable Sets. R\~package version\~1.0, URL
    <https://cran.r-project.org/package=sets>.

## AUTHOR

Jarek Jasiewicz
