# Matplotlib & Seaborn Mastery: Seeing Your Data and Your Models

## 1. The Core Concept (What and Why)

*Why is this tool relevant?* Every other guide in this module produces numbers: NumPy arrays (Guide 01), DataFrames (Guide 02), loss values (Guide 05), feature importances (Guide 04), evaluation scores (Guide 25). Numbers in a terminal hide things a picture shows at once: a loss curve that stopped falling at epoch 3, a class the model always confuses with another, a feature with a long tail that wrecks your scaler, a cluster of embeddings sitting far from the rest. Experiment trackers (Guide 23 MLflow, Guide 24 W&B) draw charts for you, but when you need a custom plot for a notebook, a report, a paper or a CI artifact, you draw it yourself, and in Python that almost always means **Matplotlib**, often with **Seaborn** on top.

**What is it?**
- **Matplotlib** is the base plotting library for Python (first released 2003). It draws lines, bars, images and text onto a canvas and saves them to PNG, SVG or PDF, or shows them in a window or notebook. Pandas' `df.plot()`, Seaborn and many ML libraries' "plot" helpers are built on it.
- **Seaborn** is a statistical plotting layer on top of Matplotlib. You hand it a DataFrame plus column names, and it does the grouping, aggregation, confidence intervals, colour mapping and legends for you.

**Why does it exist?**
Matplotlib exists so that any figure can be built exactly the way you want; the cost is that it's verbose. Seaborn exists because 80% of exploratory plots are the same few statistical shapes ("distribution of X split by Y", "mean of Y over X with a confidence band", "correlation matrix"), and writing them in raw Matplotlib is 20 lines each.

The rule of thumb: **Seaborn to explore, Matplotlib to finish.** Seaborn returns ordinary Matplotlib objects, so you can always drop down a level to fix a label, an axis or a layout.

---

## 2. Setup & Installation

```bash
pip install matplotlib seaborn pandas numpy
```

```python
import matplotlib
import seaborn as sns

print(f"Matplotlib version: {matplotlib.__version__}")  # 3.10+ in 2026
print(f"Seaborn version: {sns.__version__}")            # 0.13.x
print(f"Backend: {matplotlib.get_backend()}")
```

*Note on backends:* the **backend** is what actually renders pixels. In Jupyter it's the inline backend; on a desktop it's a GUI toolkit (TkAgg, QtAgg, macosx); on a server, in Docker or in CI there's no display, so you want **`Agg`** (a pure raster renderer that writes files). Set it with the environment variable `MPLBACKEND=Agg` or `matplotlib.use("Agg")` *before* importing `pyplot`.

---

## 3. The "Hello World": The Object-Oriented API

Matplotlib has two APIs. The **pyplot state machine** (`plt.plot(...)`, `plt.title(...)`) acts on an invisible "current figure". It's fine for a one-line notebook plot and confusing for anything with two subplots. The **object-oriented (OO) API** makes you hold the objects explicitly. Use the OO API by default.

```python
import matplotlib
matplotlib.use("Agg")  # headless: write files, no window
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 200)

# 1. One call creates the Figure (the canvas) and a grid of Axes (the plots)
fig, (ax1, ax2) = plt.subplots(
    nrows=1, ncols=2,
    figsize=(10, 4),        # inches (width, height)
    layout="constrained",   # auto-spaces titles/labels so nothing overlaps
)

# 2. Draw on each Axes explicitly
ax1.plot(x, np.sin(x), label="sin(x)")
ax1.plot(x, np.cos(x), label="cos(x)", linestyle="--")
ax1.set(title="Trig functions", xlabel="x", ylabel="value")
ax1.legend()

ax2.hist(np.random.default_rng(0).normal(size=5_000), bins=50)
ax2.set(title="Normal samples", xlabel="value", ylabel="count")

# 3. Save. dpi controls raster resolution; bbox_inches trims whitespace
fig.savefig("hello.png", dpi=150, bbox_inches="tight")
plt.close(fig)  # free the memory (see Pitfall 1)
print("saved hello.png")
```

---

## 4. Deep Dive: The Anatomy of a Figure

Every Matplotlib figure is a tree of **Artists** (anything that draws itself).

- **`Figure`**: the whole canvas. Owns one or more Axes, plus figure-level titles (`fig.suptitle`) and legends.
- **`Axes`**: one plot area with its own coordinate system. *Not* the same as "axis". This is the object you call `.plot()`, `.scatter()`, `.imshow()` on.
- **`Axis`**: the x or y ruler of an Axes: ticks, tick labels, scale (`linear`, `log`, `symlog`, `logit`).
- **Primitive artists**: `Line2D`, `Rectangle` (a bar), `Text`, `PathCollection` (a scatter). Each call like `ax.plot` returns them, so you can restyle them later.

### Parameter Breakdown: laying out several plots

- `plt.subplots(nrows, ncols, sharex=True, sharey=True)`: a regular grid. `sharex` links zoom and hides duplicate tick labels.
- `plt.subplot_mosaic("AAB;CCB")`: an irregular layout from an ASCII sketch; returns a dict of Axes keyed by letter. Great for dashboards.
- `layout="constrained"`: the modern layout engine; prefer it over the older `fig.tight_layout()`.
- `ax.twinx()`: a second y-axis sharing the same x (for example loss on the left, learning rate on the right). Use sparingly; readers misread twin axes.

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(42)
steps = np.arange(1, 1001)
loss = 2.5 * steps ** -0.3 + rng.normal(0, 0.03, steps.size)
lr = np.minimum(steps / 100, 1.0) * 3e-4 * 0.5 * (1 + np.cos(np.pi * steps / 1000))

fig, axd = plt.subplot_mosaic("LL;HR", figsize=(10, 6), layout="constrained")

axd["L"].plot(steps, loss, color="C0", alpha=0.3, label="raw")
# Exponential moving average: what W&B's "smoothing" slider does
ema = np.empty_like(loss); ema[0] = loss[0]
for i in range(1, loss.size):
    ema[i] = 0.98 * ema[i - 1] + 0.02 * loss[i]
axd["L"].plot(steps, ema, color="C0", label="EMA 0.98")
axd["L"].set(yscale="log", xlabel="step", ylabel="loss (log)", title="Training loss")
axd["L"].legend()

lr_ax = axd["L"].twinx()
lr_ax.plot(steps, lr, color="C1", linewidth=1)
lr_ax.set_ylabel("learning rate", color="C1")

axd["H"].hist(loss[-200:], bins=30, color="C2")
axd["H"].set(title="Loss, last 200 steps", xlabel="loss")

axd["R"].bar(["train", "val", "test"], [0.94, 0.91, 0.90], color=["C0", "C1", "C2"])
axd["R"].bar_label(axd["R"].containers[0], fmt="%.2f")  # numbers on top of bars
axd["R"].set(ylim=(0.8, 1.0), title="Accuracy")  # a zoomed y-axis: say so in the caption!

fig.suptitle("Run 42 summary")
fig.savefig("dashboard.png", dpi=120)
plt.close(fig)
print("saved dashboard.png")
```

### Colour: choosing a colormap

A **colormap** maps numbers to colours. Picking the wrong one lies about your data.

| Data type | Use | Examples |
| --- | --- | --- |
| Ordered, one direction (counts, probability) | **Sequential**, perceptually uniform | `viridis` (default), `magma`, `cividis` |
| Signed around a meaningful centre (correlation, residuals) | **Diverging**, centred on 0 | `RdBu_r`, `coolwarm`, `vlag` (seaborn) |
| Unordered categories (class labels) | **Qualitative** | `tab10` (default cycle `C0`..`C9`), `Set2` |

Avoid `jet`/`rainbow`: their brightness isn't monotonic, so they create fake edges and fail for colour-blind readers and greyscale prints. For diverging maps, always pin the centre (`vmin=-1, vmax=1` or `center=0` in Seaborn); otherwise a correlation of 0.1 may render as deep red just because it's the max.

---

## 5. Seaborn: Statistical Plots from a DataFrame

Seaborn expects **tidy ("long") data**: one row per observation, one column per variable. You map columns to visual roles: `x=`, `y=`, `hue=` (colour), `style=`, `size=`, `col=`/`row=` (small multiples).

### Axes-level vs figure-level functions

This is the most important Seaborn concept and a common source of confusion:

| | Axes-level | Figure-level |
| --- | --- | --- |
| Examples | `scatterplot`, `lineplot`, `histplot`, `kdeplot`, `boxplot`, `heatmap` | `relplot`, `displot`, `catplot`, `lmplot`, `pairplot`, `jointplot` |
| Draws into | An Axes you pass with `ax=` | Its own new Figure (via `FacetGrid`) |
| Returns | a Matplotlib `Axes` | a Seaborn `FacetGrid` (use `.figure`, `.axes`, `.set_titles`) |
| Small multiples | No | Yes: `col="model"`, `row="dataset"` |
| Size set by | the parent figure's `figsize` | `height=` and `aspect=` per facet |

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid", context="notebook")  # global look; context="talk"/"paper" rescales fonts

# Tidy data: 3 models x 3 seeds x 20 epochs of validation accuracy
rng = np.random.default_rng(0)
rows = []
for model, ceiling in [("baseline", 0.82), ("+augment", 0.86), ("+augment+wd", 0.88)]:
    for seed in range(3):
        for epoch in range(1, 21):
            acc = ceiling * (1 - np.exp(-epoch / 4)) + rng.normal(0, 0.01)
            rows.append({"model": model, "seed": seed, "epoch": epoch, "val_acc": acc})
df = pd.DataFrame(rows)

# Axes-level: we own the figure, Seaborn aggregates the 3 seeds per epoch
fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
sns.lineplot(data=df, x="epoch", y="val_acc", hue="model",
             errorbar=("ci", 95),   # band = 95% bootstrap CI across seeds. Use "sd" for std-dev
             ax=axes[0])
axes[0].set_title("Validation accuracy (mean, 95% CI over seeds)")

final = df[df.epoch == 20]
sns.boxplot(data=final, x="model", y="val_acc", ax=axes[1])
sns.stripplot(data=final, x="model", y="val_acc", color="black", size=6, ax=axes[1])  # show the raw points
axes[1].set_title("Final-epoch accuracy per seed")
fig.savefig("seaborn_axes_level.png", dpi=120)
plt.close(fig)

# Figure-level: one facet per model, created for us
g = sns.relplot(data=df, x="epoch", y="val_acc", hue="seed", col="model",
                kind="line", height=3, aspect=1.2, palette="tab10")
g.set_titles("{col_name}")
g.figure.savefig("seaborn_figure_level.png", dpi=120)
plt.close(g.figure)
print("saved seaborn plots")
```

*Note:* `errorbar=` replaced the old `ci=` parameter in Seaborn 0.12. Old tutorials using `ci=95` or `ci="sd"` get a deprecation warning.

*Version note:* with Matplotlib 3.11 and Seaborn 0.13.2, `sns.boxplot` emits a `MatplotlibDeprecationWarning` about `vert: bool` from inside Seaborn. It's harmless (the plot is correct) and comes from Seaborn's internals, not your code; it goes away when Seaborn updates its call.

### The Seaborn objects interface

Seaborn 0.12 added `seaborn.objects` (imported as `so`), a declarative, grammar-of-graphics API (similar in spirit to R's ggplot2): `so.Plot(df, x=..., y=..., color=...).add(so.Line(), so.Agg())`. It composes better than the classic functions, but as of 0.13 its API is still marked experimental, and most code and interview answers still use the classic functions. Know that it exists; don't build a team standard on it yet.

---

## 6. Pro Level: The ML Plotting Cookbook

These are the plots you're expected to produce (and read) as an ML engineer. The example computes everything with NumPy so it doesn't depend on scikit-learn; in real code `sklearn.metrics` has `ConfusionMatrixDisplay`, `RocCurveDisplay` and `PrecisionRecallDisplay` that draw on an `ax=` you pass in.

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

rng = np.random.default_rng(7)

# ---- Fake binary classifier output (10% positives: an imbalanced problem) ----
n = 5_000
y_true = (rng.random(n) < 0.10).astype(int)
scores = np.clip(rng.normal(0.3 + 0.35 * y_true, 0.18), 0, 1)

def roc_and_pr(y, s):
    order = np.argsort(-s)
    y = y[order]
    tp = np.cumsum(y); fp = np.cumsum(1 - y)
    tpr = tp / y.sum(); fpr = fp / (1 - y).sum()
    precision = tp / (tp + fp)
    return fpr, tpr, precision, tpr  # recall == tpr

fpr, tpr, precision, recall = roc_and_pr(y_true, scores)
auc = np.trapezoid(tpr, fpr)

# ---- Fake 4-class confusion matrix ----
labels = ["cat", "dog", "fox", "wolf"]
cm = np.array([[90, 6, 3, 1], [8, 85, 2, 5], [4, 3, 70, 23], [1, 6, 25, 68]])
cm_norm = cm / cm.sum(axis=1, keepdims=True)  # row-normalise: per-class recall

# ---- 2-D view of embeddings via PCA (SVD) ----
centers = rng.normal(0, 4, (3, 64))
emb = np.vstack([c + rng.normal(0, 1.5, (200, 64)) for c in centers])
emb_labels = np.repeat(["legal", "medical", "sports"], 200)
X = emb - emb.mean(axis=0)
_, S, Vt = np.linalg.svd(X, full_matrices=False)
xy = X @ Vt[:2].T
explained = (S[:2] ** 2).sum() / (S ** 2).sum()

fig, ax = plt.subplots(2, 2, figsize=(11, 9), layout="constrained")

# 1. ROC curve
ax[0, 0].plot(fpr, tpr, label=f"model (AUC={auc:.3f})")
ax[0, 0].plot([0, 1], [0, 1], "k--", label="random")
ax[0, 0].set(xlabel="False positive rate", ylabel="True positive rate", title="ROC", aspect="equal")
ax[0, 0].legend(loc="lower right")

# 2. Precision-recall: the honest view for imbalanced data
ax[0, 1].plot(recall, precision)
ax[0, 1].axhline(y_true.mean(), color="k", linestyle="--", label=f"base rate={y_true.mean():.2f}")
ax[0, 1].set(xlabel="Recall", ylabel="Precision", title="Precision-Recall", ylim=(0, 1.02))
ax[0, 1].legend()

# 3. Confusion matrix as an annotated heatmap
sns.heatmap(cm_norm, annot=cm, fmt="d", cmap="Blues", vmin=0, vmax=1,
            xticklabels=labels, yticklabels=labels, cbar_kws={"label": "row-normalised"},
            ax=ax[1, 0])
ax[1, 0].set(xlabel="Predicted", ylabel="True", title="Confusion matrix (colour = recall)")

# 4. Embedding projection
sns.scatterplot(x=xy[:, 0], y=xy[:, 1], hue=emb_labels, s=12, alpha=0.7,
                linewidth=0, ax=ax[1, 1])
ax[1, 1].set(title=f"Embeddings, PCA 2-D ({explained:.0%} variance)", xlabel="PC1", ylabel="PC2")

fig.savefig("ml_cookbook.png", dpi=120)
plt.close(fig)
print(f"AUC={auc:.3f}, PCA 2-D explains {explained:.0%} of variance")
```

What each plot tells you:
1. **ROC** is insensitive to class balance. With 1% positives, a model can have AUC 0.95 and still be useless at any threshold that matters.
2. **Precision-recall** shows what users feel: "of the things we flagged, how many were real?". Always draw the base-rate line; a PR curve near it means the model has learned nothing.
3. **Confusion matrix**: colour by the *row-normalised* rate but annotate *raw counts*, otherwise big classes dominate the colour scale. Here fox/wolf confusion jumps out: a data or labelling problem, not a model-size problem.
4. **Embedding projection**: PCA is linear and deterministic, good for a sanity check. UMAP/t-SNE (separate libraries) show local clusters better, but distances *between* clusters and cluster sizes in t-SNE are not meaningful; don't draw conclusions from them.

### Correlation heatmap with a diverging map

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

rng = np.random.default_rng(1)
df = pd.DataFrame(rng.normal(size=(500, 6)), columns=list("ABCDEF"))
df["G"] = df["A"] * 0.8 + rng.normal(0, 0.3, 500)   # correlated with A
df["H"] = -df["B"] * 0.6 + rng.normal(0, 0.5, 500)  # anti-correlated with B

corr = df.corr()
mask = np.triu(np.ones_like(corr, dtype=bool))  # hide the redundant upper triangle

fig, ax = plt.subplots(figsize=(6, 5), layout="constrained")
sns.heatmap(corr, mask=mask, cmap="vlag", center=0, vmin=-1, vmax=1,
            annot=True, fmt=".2f", square=True, ax=ax)
ax.set_title("Feature correlation")
fig.savefig("corr.png", dpi=120)
plt.close(fig)
print(corr.loc["G", "A"].round(2), corr.loc["H", "B"].round(2))
```

---

## 7. Production: Plotting in Servers, CI and Big Data

1. **Headless and thread-safe rendering.** `pyplot` keeps global state and isn't thread-safe. In a web server (FastAPI, Flask) or a multi-threaded worker, don't import `pyplot` at all. Build figures directly:
   ```python
   from matplotlib.figure import Figure
   import io

   fig = Figure(figsize=(4, 3))        # not attached to pyplot's global registry
   ax = fig.subplots()
   ax.plot([1, 2, 3], [3, 1, 2])
   buf = io.BytesIO()
   fig.savefig(buf, format="png")      # the Agg canvas is created on demand
   png_bytes = buf.getvalue()          # return this as image/png
   print(len(png_bytes) > 0)
   ```
   Figures made this way are garbage-collected like any object; there's no `plt.close` to forget.
2. **Millions of points.** A scatter of 5M points saved as SVG/PDF writes 5M vector objects (a huge file, and slow to open). Options: `ax.scatter(..., rasterized=True)` keeps axes and text as vectors but turns the dots into an image; `ax.hexbin(x, y, gridsize=100)` or `sns.histplot(x=..., y=...)` (a 2-D histogram) shows density instead of overplotted blobs; or downsample for display.
3. **File formats.** PNG for dashboards and slides (`dpi=150`+); SVG/PDF for papers (vector, scales infinitely); set `fig.savefig(..., metadata=...)` if you need provenance.
4. **Reproducible style.** Put a team `.mplstyle` file in the repo (`plt.style.use("./team.mplstyle")`) or call `sns.set_theme(...)` once at the start, so every chart in a report looks the same.
5. **CI artifacts.** Save evaluation plots as files and upload them from the CI job, or log them to MLflow (`mlflow.log_figure(fig, "roc.png")`, Guide 23) or W&B (`wandb.log({"roc": wandb.Image(fig)})`, Guide 24).

---

## 8. MAANG Interview Scenarios

### Scenario 1: The Misleading Dashboard
*Interviewer:* "A PM shows you a bar chart: new model 0.91 accuracy, old model 0.89, and the new bar is twice as tall. They want to ship. What do you say?"

*Answer:* "Three problems. First, the y-axis must start at zero for bar charts, because bar *length* encodes the value; a truncated axis turns a 2-point difference into a 2x visual difference. If we want to zoom, use a dot plot or say 'axis truncated' explicitly. Second, one number per model hides variance: I'd rerun both with 3-5 seeds and show a box or strip plot, or a mean with a 95% CI, and check whether the intervals overlap. Third, accuracy may be the wrong metric. If the classes are imbalanced I'd look at the precision-recall curve and the per-class confusion matrix; the gain may come entirely from the majority class while the minority class got worse."

### Scenario 2: Memory Grows in a Report Job
*Interviewer:* "A nightly job renders 20,000 per-customer charts with `plt.figure()` / `plt.plot()` / `plt.savefig()`. It gets OOM-killed after a few thousand. Why?"

*Answer:* "`pyplot` keeps a reference to every figure it creates until you close it; `savefig` doesn't release it. After a few thousand figures that's gigabytes (Matplotlib even warns after 20 open figures, `figure.max_open_warning`). Fix: call `plt.close(fig)` after each save, or better, in a batch job use `matplotlib.figure.Figure` directly so figures are ordinary objects and get garbage-collected. I'd also create one figure and reuse it (clear the Axes each iteration, or update line data with `line.set_data`), which is much faster than building 20,000 figures, and parallelise across processes, not threads, since `pyplot` isn't thread-safe."

### Scenario 3: Plotting Embeddings
*Interviewer:* "You projected your document embeddings with t-SNE and two topics look far apart. Can you conclude the model separates them well?"

*Answer:* "Not from t-SNE alone. t-SNE preserves local neighbourhoods but not global distances or cluster sizes, and the picture changes with perplexity and random seed. I'd check it quantitatively instead: nearest-neighbour label purity or a silhouette score in the original embedding space, or retrieval metrics like recall@k. For a visual sanity check I'd also show PCA, which is linear and deterministic, and try several t-SNE perplexities to see if the separation is stable."

---

## 9. Common Pitfalls & Debugging in Production

### ⚠️ Pitfall 1: Too many open figures
`RuntimeWarning: More than 20 figures have been opened` followed by rising memory. Every `plt.figure()`/`plt.subplots()` stays alive until closed.
*Fix:* `plt.close(fig)` after `savefig`, `plt.close("all")` at the end of a notebook cell loop, or use `Figure()` directly in scripts and servers.

### ⚠️ Pitfall 2: `TclError: no display name` / `Could not connect to display`
You're on a headless machine (Docker, CI, SSH) and Matplotlib picked a GUI backend.
*Fix:* `export MPLBACKEND=Agg` or `matplotlib.use("Agg")` before importing `pyplot`. `plt.show()` does nothing under Agg; use `savefig`.

### ⚠️ Pitfall 3: Mixing pyplot and OO calls
After `fig, (ax1, ax2) = plt.subplots(1, 2)`, calling `plt.title("x")` titles only the *last active* Axes (`ax2`), which surprises everyone.
*Fix:* In multi-plot figures, only call methods on the objects: `ax1.set_title(...)`, `fig.suptitle(...)`.

### ⚠️ Pitfall 4: Seaborn figure-level functions ignore `ax=`
`sns.relplot(..., ax=axes[0])` warns and draws a *new* figure, leaving your subplot empty.
*Fix:* Use the axes-level twin (`scatterplot`/`lineplot`) when you want to place the plot yourself, or let the figure-level function own the whole figure and use `col=`/`row=` for the grid.

### ⚠️ Pitfall 5: Wide data given to Seaborn
Passing a DataFrame with columns `acc_run1, acc_run2, acc_run3` and expecting `hue` to split runs doesn't work; Seaborn wants one row per observation.
*Fix:* Reshape first: `df.melt(id_vars="epoch", var_name="run", value_name="acc")`, then `hue="run"`.
