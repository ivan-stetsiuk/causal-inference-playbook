"""Data generating processes with known ground truth.

The whole point of this file is step 4 of the chapter template (see
ARCHITECTURE.md §5.1). In real data the counterfactual is never observed, so
there is nothing to check an estimator against. In a simulation it *is*
observed, because we defined both potential outcomes ourselves. If the
estimator returns the effect we planted, the estimator is understood. If it
does not, we have learned exactly what we do not understand.

Every function returns a DataFrame that DOES contain both y0 and y1. Those
columns must never be shown to an estimator — only `t`, `y` and covariates.
The potential-outcome columns exist solely to check the answer.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# --- Column convention -----------------------------------------------------
# y0 : potential outcome without treatment   (unobservable in real data)
# y1 : potential outcome under treatment     (unobservable in real data)
# t  : realized treatment assignment, 0/1
# y  : observed outcome = t*y1 + (1-t)*y0
# x  : covariate / confounder
# ---------------------------------------------------------------------------


def _observed(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse the potential outcomes into the observed one — the fundamental
    problem of causal inference in a single line."""
    df["y"] = np.where(df["t"] == 1, df["y1"], df["y0"])
    return df


def randomized_trial(
    n: int = 2000,
    ate: float = 2.0,
    baseline: float = 10.0,
    noise: float = 1.0,
    p_treat: float = 0.5,
    seed: int = 0,
) -> pd.DataFrame:
    """Randomized experiment: assignment is independent of the outcomes.

    The reference case. A difference in means is unbiased here, and every
    observational design is measured against it.
    """
    rng = np.random.default_rng(seed)
    y0 = baseline + rng.normal(0, noise, n)
    df = pd.DataFrame(
        {
            "y0": y0,
            "y1": y0 + ate,
            # The key line: the coin knows nothing about y0 or y1.
            "t": rng.binomial(1, p_treat, n),
        }
    )
    return _observed(df)


def confounded(
    n: int = 2000,
    ate: float = 2.0,
    confounding: float = 3.0,
    baseline: float = 10.0,
    noise: float = 1.0,
    seed: int = 0,
) -> pd.DataFrame:
    """Observational data with a single observed confounder x.

    x drives both the probability of treatment and the outcome. At
    confounding=0 the design degenerates into a randomized experiment, which
    is what makes it useful behind a slider: the bias grows visibly from zero.
    """
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, n)
    # x pushes assignment...
    p = 1 / (1 + np.exp(-confounding * x))
    t = rng.binomial(1, p)
    # ...and the outcome. That is where the bias in a naive difference is born.
    y0 = baseline + confounding * x + rng.normal(0, noise, n)
    df = pd.DataFrame({"x": x, "y0": y0, "y1": y0 + ate, "t": t})
    return _observed(df)


def heterogeneous(
    n: int = 2000,
    ate: float = 2.0,
    modifier: float = 1.5,
    baseline: float = 10.0,
    noise: float = 1.0,
    seed: int = 0,
) -> pd.DataFrame:
    """Effect varies with x: ATE stays `ate`, but CATE(x) = ate + modifier*x.

    Needed to see the gap between "the average effect" and "the effect for
    this unit", and why an ATE can be useless for decisions.
    """
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, n)
    y0 = baseline + x + rng.normal(0, noise, n)
    df = pd.DataFrame(
        {
            "x": x,
            "y0": y0,
            "y1": y0 + ate + modifier * x,
            "t": rng.binomial(1, 0.5, n),
        }
    )
    return _observed(df)


def selection_bias(
    n: int = 2000,
    ate: float = 2.0,
    selection: float = 2.0,
    baseline: float = 10.0,
    noise: float = 1.0,
    seed: int = 0,
) -> pd.DataFrame:
    """Self-selection: units with a higher y0 are the ones who take treatment.

    Differs from `confounded` in that the driver of selection is NOT observed,
    so controlling for covariates cannot help. This is the counterexample to
    "just add more controls".
    """
    rng = np.random.default_rng(seed)
    u = rng.normal(0, 1, n)  # unobserved propensity
    y0 = baseline + selection * u + rng.normal(0, noise, n)
    p = 1 / (1 + np.exp(-selection * u))
    df = pd.DataFrame({"u": u, "y0": y0, "y1": y0 + ate, "t": rng.binomial(1, p)})
    return _observed(df)


# --- Checking against the truth --------------------------------------------


def true_ate(df: pd.DataFrame) -> float:
    """The real ATE — available only because this is a simulation."""
    return float((df["y1"] - df["y0"]).mean())


def true_att(df: pd.DataFrame) -> float:
    """Effect on the treated. Diverges from the ATE under heterogeneity."""
    treated = df[df["t"] == 1]
    return float((treated["y1"] - treated["y0"]).mean())


def naive_diff(df: pd.DataFrame) -> float:
    """The difference in means an analyst without causal machinery reports."""
    return float(df.loc[df["t"] == 1, "y"].mean() - df.loc[df["t"] == 0, "y"].mean())


def decompose(df: pd.DataFrame) -> dict[str, float]:
    """Split the naive difference into ATT and selection bias.

    Both terms are made of counterfactuals, so this is computable only in a
    simulation — which is exactly why the simulation is worth running.
    """
    treated, control = df[df["t"] == 1], df[df["t"] == 0]
    return {
        "att": float((treated["y1"] - treated["y0"]).mean()),
        "bias": float(treated["y0"].mean() - control["y0"].mean()),
    }


def bias_report(df: pd.DataFrame) -> pd.DataFrame:
    """Compact "truth versus naive estimate" summary to close out step 4."""
    ate, naive = true_ate(df), naive_diff(df)
    return pd.DataFrame(
        {
            "quantity": ["True ATE", "True ATT", "Naive difference", "Bias"],
            "value": [ate, true_att(df), naive, naive - ate],
        }
    )
