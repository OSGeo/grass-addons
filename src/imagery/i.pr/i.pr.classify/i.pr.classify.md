## DESCRIPTION

Classifies GRASS raster maps based on a classification model. Given a number
of input GRASS raster maps (**input\_map**), where the order must be
the same as that used for training data extraction (!!!!), and a
classification model (**model**), a GRASS raster map containing
the classification result is produced.

Map values ​​by model type:

- Binary Gaussian Mixture: posterior probability of the most likely class
  multiplied by the class itself {−1, 1}
- Multiclass Gaussian Mixture: most likely class
- Binary Nearest Neighbor: proportion of data in the most likely class
  multiplied by the class itself {−1, 1}
- Multiclass Nearest Neighbor: most likely class
- Binary Classification Trees: proportion of data in the most likely class
  at the terminal node multiplied by the class itself {−1, 1}
- Multiclass Classification Trees: most likely class
- Binary Support Vector Machines: output of the support vector
  machine itself (−∞, ∞)
- Multiclass Bagging Classification Trees: most likely class
- Binary Bagging Classification Trees: weighted sum of models (−1, 1)
- Boosting Classification Trees (binary only): weighted sum of models (−1, 1)
- Bagging Support Vector machines (binary only): weighted sum of
  patterns (−1, 1)
- Boosting support vector machines (binary only): weighted sum of
  patterns (−1, 1)

## AUTHORS

Stefano Merler, FBK, Trento, Italy
