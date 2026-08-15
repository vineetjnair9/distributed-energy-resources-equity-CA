# STALE — not regenerated since the 2026-08-03 audit rerun

The PNGs in this directory (except any listed as regenerated below) date to **March
2026** and were produced from the pre-audit dataset — before the housing-structure
columns were populated, before the duplicate `lat/lon` columns were removed, before
unmatched ZIPs stopped being treated as a `"nan"` county, and before the Tracking the
Sun 2023 date filter. See `AUDIT.md`.

**No current code produces them.** `regression.ipynb` still defines
`make_paper_spatial_figure(...)` and still sets `RUN_MAPS = False`, but nothing reads
that flag and nothing calls that function — the calling code was removed at some point,
so these are unreachable artifacts. Some filenames also refer to model labels the
notebook no longer emits (e.g. `model_4r_interactions_reduced`).

Regenerated on 2026-08-03, from current data, because the site's geography panel
embeds them:

- `y_pv_model_1_baseline_climate_controls_spatial_figure.png`

To regenerate these three again:

```bash
python scripts/regenerate_site_maps.py
```

Everything else here should be treated as historical. Do not cite figures from this
directory without checking the date.
