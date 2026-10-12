# Pitch deck benchmark figures

- `benchmark-overview.png`: main slide; 3200 × 1800, 16:9.
- `benchmark-case-matrix.png`: backup slide with every case result; 3200 × 1800, 16:9.
- Matching SVG and PDF files provide vector exports.

These figures read the saved first-run rules and production hybrid API receipts in
`../results/`. They are not new model runs and incur no provider usage. The render
script asserts that plotted counts agree with the saved summary.

Keep the visible qualification: 16 internal synthetic cases, AI-authored expected
checks, independent human review pending. Evidence checks verify reference/path
structure, not semantic correctness of every claim. These are automated screening
results, not overall application accuracy or measured closing uplift.

Use the overview on the main slide and the case matrix for questions about failures.
The original receipts remain unchanged. Figures were visually checked for clipping
and readability after export.

Reproduce from the repository root with Matplotlib installed:

```sh
MPLCONFIGDIR=/tmp/dealcompass-mpl python3 evaluation/deal_benchmark/figures/render.py
```
