#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import joblib
import re

from sklearn.decomposition import (
    PCA, KernelPCA, FastICA, TruncatedSVD, NMF, SparsePCA
)
from sklearn.kernel_approximation import Nystroem


def _parse_band_intervals(band_string, wavelengths):
    """Select subset of bands by intervals or single nm values."""
    if not band_string:
        return np.arange(len(wavelengths))
    selection = np.zeros(len(wavelengths), dtype=bool)
    for part in band_string.split(","):
        part = part.strip()
        if "-" in part:
            start, end = map(float, part.split("-"))
            selection |= (wavelengths >= start) & (wavelengths <= end)
        else:
            val = float(part)
            selection |= np.isclose(wavelengths, val, atol=5)
    return np.where(selection)[0]


def _choose_train_subset(X_valid, memory_limit_gb, cols, min_train=2000):
    """Choose training subset size based on memory budget."""
    bytes_per_row = int(1.5 * cols * 4)
    max_rows = int((memory_limit_gb * (1024 ** 3)) // max(bytes_per_row, 1))
    max_rows = max(min_train, max_rows)
    return min(max_rows, X_valid.shape[0])


def _fit_once_then_transform_in_chunks(X_valid, valid_mask, transformer_fit, transformer_transform, out_dim, chunk_size):
    """Fit transformer once, then transform X_valid in chunks, filling invalid rows with NaN."""
    X_red = np.full((valid_mask.shape[0], out_dim), np.nan, dtype=np.float32)
    idx_valid = np.flatnonzero(valid_mask)

    for start in range(0, X_valid.shape[0], chunk_size):
        end = min(start + chunk_size, X_valid.shape[0])
        X_chunk = X_valid[start:end]
        X_red_chunk = transformer_transform(X_chunk)
        X_red[idx_valid[start:end], :] = X_red_chunk.astype(np.float32)

    return X_red


def _apply_dimensionality_reduction(
    flat_data,
    method=None,
    n_components=0,
    kernel="rbf",
    gamma=0.01,
    degree=3,
    bands=None,
    wavelengths=None,
    export_path=None,
    chunk_size=None,
    memory_limit_gb=8,
    max_iter=200,
    tol=1e-4,
    alpha=0.0,
    l1_ratio=0.0,
    random_state=0,
):
    """
    Apply dimensionality reduction to flattened HSI.

    Supported methods (lowercase internally):
      - pca
      - kpca
      - nystroem
      - fastica
      - truncatedsvd
      - nmf
      - sparsepca
    """
    info = {}
    X = flat_data

    # Band filtering
    if bands and wavelengths is not None:
        idx = _parse_band_intervals(bands, np.array(wavelengths))
        if idx.size == 0:
            raise ValueError("No wavelengths matched given intervals.")
        X = X[:, idx]

    if not method:
        return X.astype(np.float32), info

    # Normalize method name
    method = method.lower()

    # Validate components
    if n_components <= 0 or n_components > X.shape[1]:
        n_components = min(10, X.shape[1])

    # Identify valid spectra
    valid_mask = ~np.isnan(X).any(axis=1)
    if valid_mask.sum() == 0:
        raise ValueError("No valid spectra for dimensionality reduction.")
    X_valid = X[valid_mask]

    # Determine chunk size
    if chunk_size is None:
        bytes_per_val = 4
        total_cols = X_valid.shape[1]
        chunk_size = int((memory_limit_gb * (1024 ** 3)) / (bytes_per_val * total_cols))
        chunk_size = max(5000, min(chunk_size, X_valid.shape[0]))

    # Training subset
    train_rows = _choose_train_subset(X_valid, memory_limit_gb, X_valid.shape[1])
    if train_rows < X_valid.shape[0]:
        rng = np.random.default_rng(random_state if random_state else None)
        sel = rng.choice(X_valid.shape[0], size=train_rows, replace=False)
        X_train = X_valid[sel]
    else:
        X_train = X_valid

    model = None
    feature_map = None
    pca_after = None

    # --- Reduction methods ---
    if method == "pca":
        model = PCA(n_components=n_components, random_state=random_state)
        model.fit(X_train)
        out_dim = model.n_components_
        info["explained_variance_ratio"] = model.explained_variance_ratio_

        def _transform(Z): return model.transform(Z)

    elif method == "kpca":
        model = KernelPCA(
            n_components=n_components,
            kernel=kernel,
            gamma=gamma,
            degree=degree,
            fit_inverse_transform=False,
            eigen_solver="auto",
            remove_zero_eig=True,
            random_state=random_state
        )
        model.fit(X_train)
        out_dim = n_components
        info.update({"kernel": kernel, "gamma": gamma, "degree": degree, "n_components": n_components})

        def _transform(Z): return model.transform(Z)

    elif method == "nystroem":
        feature_map = Nystroem(kernel=kernel, gamma=gamma, degree=degree, n_components=max(n_components, 50), random_state=random_state)
        Z_train = feature_map.fit_transform(X_train)
        pca_after = PCA(n_components=min(n_components, Z_train.shape[1]), random_state=random_state)
        pca_after.fit(Z_train)
        out_dim = pca_after.n_components_
        info.update({
            "kernel": kernel, "gamma": gamma, "degree": degree,
            "n_components": out_dim
        })
        info["explained_variance_ratio"] = pca_after.explained_variance_ratio_

        def _transform(Z):
            Zm = feature_map.transform(Z)
            return pca_after.transform(Zm)

    elif method == "fastica":
        model = FastICA(
            n_components=n_components,
            max_iter=max_iter,
            tol=tol,
            random_state=random_state
        )
        model.fit(X_train)
        out_dim = n_components

        def _transform(Z): return model.transform(Z)

    elif method == "truncatedsvd":
        model = TruncatedSVD(n_components=n_components, random_state=random_state)
        model.fit(X_train)
        out_dim = n_components
        if hasattr(model, "explained_variance_ratio_"):
            info["explained_variance_ratio"] = model.explained_variance_ratio_

        def _transform(Z): return model.transform(Z)

    elif method == "nmf":
        if np.nanmin(X_train) < 0:
            raise ValueError("NMF requires non-negative data. Use clamp-to-zero or rescale before NMF.")
        model = NMF(
            n_components=n_components,
            init="nndsvda",
            max_iter=max_iter,
            tol=tol,
            alpha_W=alpha,
            alpha_H=alpha,
            l1_ratio=l1_ratio,
            random_state=random_state
        )
        model.fit_transform(X_train)
        out_dim = n_components

        def _transform(Z):
            if np.nanmin(Z) < 0:
                raise ValueError("NMF transform requires non-negative data.")
            return model.transform(Z)

    elif method == "sparsepca":
        model = SparsePCA(
            n_components=n_components,
            alpha=alpha if alpha > 0 else 1.0,
            ridge_alpha=0.01,
            max_iter=max_iter,
            tol=tol,
            random_state=random_state,
            n_jobs=None
        )
        model.fit(X_train)
        out_dim = n_components

        def _transform(Z): return model.transform(Z)

    else:
        raise ValueError(f"Unsupported dimensionality reduction method: {method}")

    # Transform valid data in chunks
    X_red = _fit_once_then_transform_in_chunks(
        X_valid, valid_mask, None, _transform, out_dim, chunk_size
    )

    # Export trained models
    if export_path:
        if method == "nystroem":
            joblib.dump((feature_map, pca_after), export_path)
        else:
            joblib.dump(model, export_path)

    return X_red.astype(np.float32), info
