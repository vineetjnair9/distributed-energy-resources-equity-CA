# Manuscript build scripts

Two scripts rebuild the Nature Sustainability submission from `site/index.docx`.

```bash
python scripts/nature_revision_analysis.py        # first: produces outputs/nature_revision/
python scripts/manuscript/build_manuscript.py     # then:  site/index_nature_submission.docx
python scripts/manuscript/build_supplementary.py  #        site/supplementary_information.docx
```

`content.py` holds the new prose — abstract, Introduction, Results including the new
stacked-model subsection, and Discussion. Edit the text there, not in the builders.

The source `site/index.docx` is only ever read.

## Status — read before relying on these

`build_supplementary.py` reproduces the delivered Supplementary Information exactly.

`build_manuscript.py` reproduces the delivered manuscript's structure, prose, figures,
tables and every compliance check — but **its bibliography stage does not reproduce the
delivered reference numbering.** It currently keeps 26 references where the delivered
file has 29, and assigns different numbers to several data-source citations.

**`site/index_nature_submission.docx` as delivered is authoritative for references.** It
was verified entry by entry: every in-text citation resolves to the correct source
(Tracking the Sun → the Tracking the Sun entry, TIGER/Line → the TIGER/Line entry, and
so on), with no unresolved and no uncited entries.

The bug is in `fix_bibliography`. The list lives in two places — entries [1]–[24] inside
the citation-manager field, and the typed data-source paragraphs [25]–[36] after it —
and reconciling the removal of the duplicated entry across both, together with the
uncited-entry pruning, is what is not yet right. Finish that stage before using this
script to regenerate the manuscript, or regenerate everything except the bibliography
and carry the delivered reference list across.

## Structure

- `content.py` — all new prose, as plain Python strings
- `build_manuscript.py` — assembles the body, applies text passes, renumbers, verifies
- `build_supplementary.py` — assembles the SI from displaced items plus generated tables

Both deep-copy the original paragraphs for anything carrying an image or a table, so the
media parts survive untouched. Comment parts, relationships and content-type overrides
are stripped: comments survive into the PDF on most submission systems.
