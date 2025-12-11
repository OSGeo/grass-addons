## DESCRIPTION

*i.hyper.preproc* performs preprocessing of hyperspectral data stored as
a 3D raster map (`raster_3d`). It is designed to improve data quality,
suppress noise, and transform the spectral dimension into
representations better suited for scientific analysis and machine
learning workflows.

The module operates directly on hyperspectral cubes imported with
[i.hyper.import](i.hyper.import.html) or other compatible 3D raster
datasets. All transformations are performed along the spectral (*z*)
dimension for each spatial position (*x, y*).

Preprocessing steps can be chained together in a pipeline, specified
with the `steps` option. Each stage is executed sequentially according
to the defined preprocessing pipeline. The module displays the full
pipeline sequence in the console (for example:
`Savitzky–Golay → Baseline correction → Continuum removal → PCA`),
providing a clear overview of the operations applied in order.

*i.hyper.preproc* is part of the **i.hyper** module family and provides
a reproducible, modular framework for spectral preprocessing prior to
feature extraction, classification, or regression. All output maps are
3D rasters (`raster_3d`) compatible with the rest of the *i.hyper*
suite.

## FUNCTIONALITY

The following preprocessing methods are supported:

- **Savitzky--Golay (sav_gol)** -- Polynomial smoothing and derivative
  computation to reduce spectral noise and enhance absorption features.
- **Baseline correction (baseline)** -- Removes global trends or offsets
  in reflectance curves.
- **Continuum removal (cont_rem)** -- Normalizes spectra to their convex
  hull to highlight relative absorption depths.
- **Principal Component Analysis (pca)** -- Linear dimensionality
  reduction using eigen decomposition of covariance.
- **Kernel PCA (kpca)** -- Nonlinear dimensionality reduction using
  kernel functions (RBF, polynomial, sigmoid).
- **Nystroem approximation (nystroem)** -- Scalable approximation of
  Kernel PCA using a low-rank kernel mapping followed by PCA
  compression. Provides nonlinear feature extraction suitable for large
  hyperspectral cubes.
- **Fast Independent Component Analysis (fastica)** -- Separates
  statistically independent spectral sources or mixtures.
- **Truncated Singular Value Decomposition (tsvd)** -- Linear
  dimensionality reduction preserving dominant singular vectors (useful
  for sparse data).
- **Non-negative Matrix Factorization (nmf)** -- Decomposes spectra into
  additive non-negative basis components.
- **Sparse Principal Component Analysis (sparsepca)** -- PCA variant
  enforcing sparsity on component loadings for interpretability.

Multiple steps can be combined in one command by listing them in
`steps=` (comma-separated). For example,
`steps='sav_gol,baseline,cont_rem,kpca'` will execute all four in
sequence. Intermediate rasters are handled internally and automatically
cleaned up.

All dimensionality reduction methods are implemented using the
[scikit-learn](https://scikit-learn.org/stable/api/sklearn.decomposition.html)
library. For detailed algorithmic descriptions and parameter
explanations, refer to the official scikit-learn documentation.

## NOTES

The module is constructed as a preprocessing pipeline engine. Each
transformation acts spectrally while preserving full spatial alignment.
Operations are reported in the console as a sequential pipeline.

When using PCA, KPCA, FastICA, NMF, or SparsePCA, the number of output
components can be controlled using the `dr_components` parameter.

**Chunked dimensionality reduction:**\
Large hyperspectral datasets can be processed in smaller portions using
the `dr_chunk_size` option. This enables dimensionality reduction on
datasets exceeding system memory capacity. When `dr_chunk_size` is used
with kernel-based methods (e.g., **KPCA**), the algorithm operates as an
*approximation* of the full kernel mapping, trading some precision for
scalability.

**Model export and reuse:**\
Trained dimensionality reduction models can be exported using the
`dr_export` option. The exported model (in `.pkl` format) can be reused
to transform other spectra---such as field or laboratory measurements
from a spectroradiometer---into the same reduced feature space. This
allows consistent feature alignment between image-derived data and point
spectra, facilitating integrated machine learning and spectral modeling
workflows.

Results can be directly used by *i.hyper.explore*, *i.hyper.composite*,
or exported with *i.hyper.export* for further analysis.

## EXAMPLES

::: code

    # Example 1: Savitzky–Golay smoothing (basic denoising)

    # Set the region
    g.region raster_3d=prisma

    # Perform Savitzky–Golay smoothin with a window of 7 bands and polynomial order of 3
    i.hyper.preproc input=prisma output=prisma_savgol \
                    window_length=7 polyorder=3

    # Console output:
    Savitzky–Golay
    Loading floating point  data with 4  bytes ...  (1254x1222x234)
:::

::: code

    # Example 2: PCA transformation

    # Set the region
    g.region raster_3d=enmap

    # Performs PCA
    # Interpolaties missing values in valid bands
    i.hyper.preproc input=enmap output=enmap_pca \
                    dr_method=pca dr_components=10 -q

    # Console output:
    PCA
    Interpolating missing values across spectral bands...
    Loading floating point  data with 4  bytes ...  (1263x1127x10)
:::

::: code

    # Example 3.1: Combined preprocessing pipeline

    # Set the region
    g.region raster_3d=tanager

    # Savitzky–Golay derivative + baseline correction + continuum removal + Nystroem
    # Interpolaties missing values in valid bands
    # Processes the hyperspectral 3D map in chunks and exports the fitted Nystroem model
    i.hyper.preproc input=tanager output=tanager_ml \
                    polyorder=3 derivative_order=1 window_length=9 \
                    -b -c -q \
                    dr_method=nystroem dr_components=30 \
                    dr_chunk_size=5000 \
                    dr_export=/models/tanager_nystroem.pkl

    # Console output:
    Savitzky–Golay → Baseline correction → Continuum removal → NYSTROEM
    Interpolating missing values across spectral bands...
    Loading floating point  data with 4  bytes ...  (869x804x426)
:::

::: code

    # Example 3.2: Using the exported Nystroem model in Python
    import joblib, numpy as np

    # Load exported Nystroem model (kernel map + PCA compressor)
    feature_map, pca_after = joblib.load("/models/tanager_nystroem.pkl")

    # Load new field spectra (rows = samples, cols = wavelengths
    # The spectra must use the same wavelength order and scaling as the hyperspectral 3D map)
    spectra = np.loadtxt("/data/field_spectra.txt")

    # Apply the same nonlinear mapping and dimensionality reduction
    Z = feature_map.transform(spectra)
    spectra_reduced = pca_after.transform(Z)
:::

## SEE ALSO

[i.hyper.explore](i.hyper.explore.html),
[i.hyper.composite](i.hyper.composite.html),
[i.hyper.export](i.hyper.export.html),
[i.hyper.import](i.hyper.import.html),
[r3.stats](https://grass.osgeo.org/grass-stable/manuals/r3.stats.html)
[r3.stats](https://grass.osgeo.org/grass-stable/manuals/r3.univar.html)

## DEPENDENCIES

- **NumPy** -- Core numerical operations and array manipulation.
- **SciPy** -- Signal processing.
- **scikit-learn** -- Machine learning algorithms for PCA, KPCA,
  FastICA, NMF, SparsePCA, TruncatedSVD, and Nystroem.

## AUTHORS

Alen Mangafić and Tomaž Žagar, Geodetic Institute of Slovenia
