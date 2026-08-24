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

## Status

Both scripts reproduce the delivered documents exactly — paragraph for paragraph,
verified against them. The manuscript passes all nine compliance checks on every run,
and its bibliography audits clean: 29 entries, 29 cited, nothing unresolved, nothing
uncited, and every data-source citation resolving to the right entry.

### The bug that was here, so it does not come back

The reference list lives in two places: entries [1]–[24] inside the citation-manager
field, and the typed data-source paragraphs [25]–[36] after it. Removing the duplicated
entry shifts the second group, and the shorter Introduction leaves several entries
uncited, so both groups have to be renumbered together.

For a while the assembly step *also* repaired and renumbered the bibliography, and
`fix_bibliography` then ran over its output. The typed entries got shifted twice, and
the four entries whose titles are retyped lost their numbers to the position-based
renumbering, so they dropped out of the list entirely — 26 references instead of 29,
with every data-source citation silently pointing at its neighbour. Nothing failed
loudly; the document still opened and every internal check still passed.

**Repair, pruning and renumbering happen once, in `fix_bibliography()`, after the body
is assembled.** The assembly step carries the reference paragraphs across untouched. Do
not reintroduce renumbering at assembly time.

Two smaller traps in the same area:

- `find_bibliography_sdt()` exists because the document holds twenty `sdt` elements —
  hyperlink fields wrap themselves in one — so taking the first is wrong. The
  bibliography is the one whose *direct* children are numbered paragraphs.
- `SI_FIG_RENUMBER` is shared by both builders. The main text's references and the SI's
  captions are renumbered independently by the same map; changing it in one place only
  will desynchronise them.

## Spelling

`spelling.py` converts British spellings to American at build time, over assembled
paragraph and table text rather than over `content.py` / `si_content.py`. That is
deliberate: a search-and-replace on the sources misses words split across adjacent
string literals, which is most of them. The bibliography is skipped so reference titles
keep whatever spelling their journals published.

Write the prose in whichever variant is natural; the pass normalizes it. If a new
British form appears, add it to `_ISE` (verbs, base form) or `_LITERAL` in
`spelling.py` — do not patch the built document.

Note that Nature journals set British spelling in their own house style and convert at
proof stage, so this is a drafting preference rather than a submission requirement.

## Structure

- `content.py` — main-text prose: abstract, Introduction, Results, Discussion
- `si_content.py` — Supplementary Information prose, thirteen numbered Notes
- `build_manuscript.py` — assembles the main body, applies text passes, renumbers, verifies
- `build_supplementary.py` — assembles the SI from displaced items plus generated tables

Both deep-copy the original paragraphs for anything carrying an image or a table, so the
media parts survive untouched. Comment parts, relationships and content-type overrides
are stripped: comments survive into the PDF on most submission systems.

## What goes where

The main text carries six display items: the statewide geography panel, the focal
coefficients across the **model series** by technology (the paper's central comparison),
the housing-structure attenuation, the charger-type decomposition, the baseline
coefficient table, and a consolidated robustness table.

Results are ordered by evidential strength rather than by technology convention. Storage
leads because it is the strongest result on every measure — all three race terms
survive the fully stacked specification, 48/48 on the specification curve for Asian
share, Oster δ above one on two terms. Charging sits in the payoff position because it
is the most distinctive. Solar comes between them, and its Black-share coefficient is
reported as the weaker of the two solar race terms rather than alongside Asian share as
though they were equally solid.

The nested cumulative ladder is a short Results subsection and lives in full in
Supplementary Note S2. It corroborates the model series; it is not the headline.

The Supplementary Information is prose, not a caption list — thirteen Notes totalling
about 4,300 words, restoring the original appendix text and the Results material the
main text no longer has room for.

