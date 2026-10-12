# Documentation assets

- `banner.svg` / `.png`: original DealCompass brand graphic; conceptual flow, not a benchmark result.
- `architecture.svg` / `.png`: implemented source → graph → decision → UI flow, with optional Jev and separate persistent state.
- `product-overview.jpg`, `context-graph.jpg`: actual application screenshots captured on 12 October 2026 from a local rules-only build of merged PR #36. No provider request or private upload was used.
- `render_assets.py`: reproducible banner/diagram source. Matplotlib is an optional documentation tool, not an application runtime dependency.

```bash
MPLCONFIGDIR=/tmp/dealcompass-mpl python3 docs/assets/render_assets.py
```

Benchmark exports and their independent render script are in [`evaluation/deal_benchmark/figures`](../../evaluation/deal_benchmark/figures/README.md). SVG files retain editable text; PNG alternatives work in slide software without SVG support.
