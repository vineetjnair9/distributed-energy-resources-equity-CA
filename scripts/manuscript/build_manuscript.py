#!/usr/bin/env python3
"""Build the Nature Sustainability main manuscript from site/index.docx.

Reads the existing manuscript, keeps its figures, tables and styles, and rebuilds the
body against the prose in ``content.py``: a 150-word abstract, an unheaded Introduction
that absorbs the old Background section, a compressed Results with a new subsection on
the nested cumulative ladder, a Discussion that absorbs the old Conclusion, an edited
Methods, and Nature back matter. Everything displaced goes to the Supplementary
Information (see ``build_supplementary.py``).

Run from the repository root:

    python scripts/manuscript/build_manuscript.py

Writes ``site/index_nature_submission.docx`` and prints the compliance checks.

Why the body is rebuilt rather than edited in place: the restructure changes section
order, merges two sections into one, drops roughly half the main text and renumbers
every display item. Reassembling from a paragraph spec, while deep-copying the original
paragraphs for anything that carries an image or a table, is easier to verify than a
long sequence of in-place edits — and it keeps the media parts intact.
"""
# -*- coding: utf-8 -*-
import copy, os, re, shutil, sys, zipfile
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(__file__))
import content as C

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
WP='{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'
for p,u in [('w',W),('a',A),('r',R),('wp',WP)]: ET.register_namespace(p,u[1:-1])

ROOT = os.path.abspath(os.environ.get('REPO_ROOT', os.path.join(os.path.dirname(__file__), '..', '..')))
BUILD = os.path.join(ROOT, 'build')
SOURCE_DOCX = os.path.join(ROOT, 'site', 'index.docx')
DEST_DOCX = os.path.join(ROOT, 'site', 'index_nature_submission.docx')

os.makedirs(BUILD, exist_ok=True)
SRC = os.path.join(BUILD, '_source')
if os.path.exists(SRC):
    shutil.rmtree(SRC)
with zipfile.ZipFile(SOURCE_DOCX) as zf:
    zf.extractall(SRC)
t=ET.parse(SRC+'/word/document.xml'); root=t.getroot(); body=root.find(W+'body')
CH=list(body)

def P(style, text, caption=False):
    p=ET.Element(W+'p')
    if style:
        pPr=ET.SubElement(p,W+'pPr'); ps=ET.SubElement(pPr,W+'pStyle'); ps.set(W+'val',style)
    r=ET.SubElement(p,W+'r'); tt=ET.SubElement(r,W+'t')
    tt.set('{http://www.w3.org/XML/1998/namespace}space','preserve'); tt.text=text
    return p
def CAP(text): return P('Caption',text)
def keep(i): return copy.deepcopy(CH[i])

# ---- strip comment machinery from a cloned element ----
def declean(el):
    for parent in el.iter():
        for child in list(parent):
            tag=child.tag
            if tag in (W+'commentRangeStart',W+'commentRangeEnd'): parent.remove(child)
            elif tag==W+'r' and child.find(W+'commentReference') is not None: parent.remove(child)
    return el

def settext(el, new):
    """Replace all text in a paragraph with `new`, keeping the first run's formatting."""
    ts=list(el.iter(W+'t'))
    if not ts:
        return el
    ts[0].text=new; ts[0].set('{http://www.w3.org/XML/1998/namespace}space','preserve')
    for tt in ts[1:]: tt.text=''
    return el

def edit(i, subs=None, new=None):
    el=declean(keep(i))
    if new is not None: return settext(el,new)
    if subs:
        for tt in el.iter(W+'t'):
            if tt.text:
                s=tt.text
                for a,b in subs: s=s.replace(a,b)
                tt.text=s
    return el

# ------------------------------------------------------------------ tables
TBL_PROTO=CH[30]
def table(rows, header=True):
    tbl=ET.Element(W+'tbl')
    pr=TBL_PROTO.find(W+'tblPr')
    if pr is not None: tbl.append(copy.deepcopy(pr))
    grid=ET.SubElement(tbl,W+'tblGrid')
    for _ in rows[0]: ET.SubElement(grid,W+'gridCol')
    for ri,row in enumerate(rows):
        tr=ET.SubElement(tbl,W+'tr')
        for cell in row:
            tc=ET.SubElement(tr,W+'tc'); ET.SubElement(tc,W+'tcPr')
            p=ET.SubElement(tc,W+'p')
            r=ET.SubElement(p,W+'r')
            if header and ri==0:
                rPr=ET.SubElement(r,W+'rPr'); ET.SubElement(rPr,W+'b')
            tt=ET.SubElement(r,W+'t')
            tt.set('{http://www.w3.org/XML/1998/namespace}space','preserve'); tt.text=str(cell)
    return tbl

T1=[["Predictor","Rooftop PV","Battery storage","EV charging"],
 ["Log median household income","0.439*** (0.084)","0.310*** (0.049)","0.066 (0.039)"],
 ["Black share","−0.218*** (0.047)","−0.106*** (0.021)","−0.000 (0.022)"],
 ["Hispanic share","0.219*** (0.059)","−0.146*** (0.030)","−0.096*** (0.025)"],
 ["Asian share","−0.297*** (0.043)","−0.252*** (0.023)","0.058** (0.021)"],
 ["Poverty rate","−0.043 (0.081)","−0.017 (0.042)","0.149*** (0.037)"],
 ["Resource / climate control","GHI 0.106* (0.044)","CDD 0.033 (0.033); HDD −0.003 (0.035)","CDD −0.120*** (0.022); HDD −0.025 (0.027)"],
 ["N","1,390","1,390","1,390"],
 ["R²","0.074","0.188","0.079"]]

T2=[["Outcome","Term","β C1","β C5","Conley HAC","Spec curve (n/48)","Oster δ"],
 ["Rooftop PV","Black share","−0.154***","−0.017","significant, 5%","28","0.32"],
 ["","Hispanic share","−0.058","0.047","not significant","31","—"],
 ["","Asian share","−0.303***","−0.114**","significant, 0.1%, every cutoff","34","1.57"],
 ["","Log income","0.173**","0.188","significant, 5%","46","—"],
 ["Battery storage","Black share","−0.103***","−0.034**","significant, 5%","36","0.71"],
 ["","Hispanic share","−0.196***","−0.113*","significant, 1%","44","1.99"],
 ["","Asian share","−0.248***","−0.116***","significant, 0.1%, every cutoff","48","1.29"],
 ["","Log income","0.220***","0.087","significant, 0.1%","44","0.96"],
 ["EV charging","Black share","−0.006","−0.008","not significant","0","—"],
 ["","Hispanic share","−0.097***","−0.037","significant, 5%","22","1.50"],
 ["","Asian share","0.046*","0.013","significant at 50 and 200 km only","4","0.97"],
 ["","Poverty rate","—","—","significant, 1%","—","—"]]

# ------------------------------------------------------------------ assemble
NB=[]
def add(x): NB.append(x)

add(settext(keep(0), C.TITLE))
add(P(None, C.AUTHORS.replace("\n"," · ")))
add(keep(1))                                  # "Abstract" heading
add(settext(declean(keep(2)), C.ABSTRACT))
for para in C.INTRO: add(P(None, para))

# ---- Results ----
add(keep(25))                                 # "Results" heading
FIGCAP={
 1:"Fig. 1 | Distributed energy deployment across California ZIP Code Tabulation Areas. "
   "Rooftop photovoltaics, battery storage and aggregate EV charging, before any regression "
   "adjustment. Blank areas indicate excluded or missing observations.",
 2:"Fig. 2 | Coefficients across the nested cumulative ladder, C1 to C5. Standardised "
   "predictors; each panel traces one coefficient as confounder blocks accumulate on a frozen "
   "common sample of 1,160 ZCTAs. Filled markers denote p < 0.05.",
 3:"Fig. 3 | Race-coefficient attenuation after adding housing structure and tenure. Hollow "
   "points are the baseline specification; filled points add exhaustive ACS B25024 structure "
   "shares (single-family reference) and B25003 owner occupancy (renter reference).",
 4:"Fig. 4 | Charger-type decomposition. Baseline coefficients for aggregate charging and for "
   "Level 1, Level 2 and DC fast units separately. The positive association with poverty is "
   "carried by Level 2 units; Level 1 is zero in 97.8 per cent of ZCTAs and is shown for "
   "completeness only.",
}
def emit(items):
    for kind,val in items:
        if kind=='H2': add(P('Heading2',val))
        elif kind=='T': add(P(None,val))
        elif kind=='FIG': add(declean(keep(val)))
        elif kind=='CAP': add(CAP(FIGCAP[val]))
        elif kind=='TBLCAP': add(CAP(val))
        elif kind=='TBL': add(val)

r=C.RESULTS
def seg(name):
    out=[];on=False
    for s,txt in r:
        if s=='H2':
            on = (txt==name)
            if on: continue
        if on: out.append(txt)
    return out

emit([('H2','Disparities differ by technology')])
for x in seg('Disparities differ by technology')[:1]: add(P(None,x))
emit([('FIG',132),('CAP',1),
      ('TBLCAP','Table 1 | Baseline associations between neighbourhood composition and distributed energy deployment. Standardised predictors; heteroskedasticity-robust (HC1) standard errors in parentheses. *p < 0.05, **p < 0.01, ***p < 0.001.'),
      ('TBL',table(T1))])
for x in seg('Disparities differ by technology')[1:]: add(P(None,x))
emit([('FIG',32),('CAP',2)])

emit([('H2','Rooftop solar and storage')])
for x in seg('Rooftop solar and storage'): add(P(None,x))
emit([('FIG',236),('CAP',3)])

emit([('H2','Charging measures infrastructure, not access')])
for x in seg('Charging measures infrastructure, not access'): add(P(None,x))
emit([('FIG',62),('CAP',4)])

emit([('H2','Disparities under a fully stacked specification')])
for x in seg('Disparities under a fully stacked specification'): add(P(None,x))
emit([('TBLCAP','Table 2 | Robustness of the focal coefficients. β C1 and β C5 are the bottom and top rungs of the nested cumulative ladder (standardised predictors, frozen sample of 1,160 ZCTAs, 42 county clusters). Conley HAC reports significance under spatially robust standard errors at distance cutoffs from 50 to 200 km. Spec curve counts specifications, out of 48 confounder-block combinations, in which the coefficient is significant and same-signed as the median. Oster δ is reported only where adding controls attenuates the coefficient. *p < 0.05, **p < 0.01, ***p < 0.001.'),
      ('TBL',table(T2))])

emit([('H2','Affordability context')])
for x in seg('Affordability context'): add(P(None,x))

# ---- Discussion ----
add(keep(99))
for s,txt in C.DISCUSSION:
    add(P('Heading2',txt) if s=='H2' else P(None,txt))


# ============================== METHODS ==============================
GLOBAL=[("ZIP/ZCTA","ZCTA"),("ZIP/ZCTAs","ZCTAs"),
 ("staged model ladder","model series"),("eight-model ladder","model series"),
 ("model ladder","model series"),("Model ladder","Model series"),
 ("increasingly demanding","progressively richer"),("increasingly rigorous","progressively richer"),
 ("Section 6.6","Methods"),("Section 6.7.2","Methods"),("Section 6.7.5","Methods"),
 ("Section 6.7.9","Methods"),("Section 6.7","Methods"),("Section 6.8","Methods"),
 ("Section 6.9","Methods"),("Section 6.2","Methods"),("Section 6.3","Methods"),
 ("Section 4.1","Results"),("Section 4.2","Results"),("Section 4.3","Results"),
 ("Section 4.4","Results"),("Section 4.5","Results"),("Section 4.7","Results"),
 ("Section 4.8","Supplementary Information"),("Section 4.9","Results"),
 ("Appendix: Additional Robustness Visuals","the Supplementary Information"),
 ("the refreshed aggregate charger baseline","the aggregate charger baseline"),
 ("The regenerated deterministic LOWESS audit","The LOWESS fits"),
 ("source files used in the repo","assembled source files"),
 ("Table 7","Supplementary Table S13"),("Table 8","Supplementary Table S7"),
 ("Table 9","Supplementary Table S8"),("Table 4","Supplementary Table S6"),
 ("Table 5","Supplementary Table S4"),("Table 6","Supplementary Table S14"),
 ("Table 3","Table 1"),("Table 1:","Supplementary Table S1:"),("Table 2:","Supplementary Table S15:"),
 ("Figure 21","Figure 3"),("Figure 16","Supplementary Fig. S5"),
 ("Figure 17","Supplementary Fig. S6"),("Figure 18","Supplementary Fig. S7"),
 ("Figure 19","Supplementary Fig. S8"),("Figure 20","Supplementary Fig. S9"),
 ("Figure 13","Supplementary Fig. S10"),("Figure 14","Supplementary Fig. S11"),
 ("Figure 15","Supplementary Fig. S12"),("Figure 10","Supplementary Fig. S13"),
 ("Figure 11","Supplementary Fig. S14"),("Figure 12","Supplementary Fig. S15"),
 ("Figure 2","Supplementary Fig. S16"),("Figure 3","Figure 2"),
 ("Figure 5","Supplementary Fig. S17"),("Figure 6","Supplementary Fig. S1"),
 ("Figure 7","Supplementary Fig. S2"),("Figure 8","Supplementary Fig. S18"),
 ("Figure 9","Figure 4"),("Figure 4","Figure 2"),
]
def M(i, extra=None, new=None):
    return edit(i, subs=(GLOBAL+(extra or [])), new=new)

add(keep(121))                                     # "Methods" heading
for i in [122,123,124,125,126]: add(M(i))
for i in [127,130,131]: add(M(i))
add(M(134)); add(M(135, extra=[("Figure 1 shows","Supplementary Fig. S16 shows")]))
add(M(140))
add(P(None,
 "Two properties of the source data govern how the outcomes should be read. The EV "
 "charging inventory records public and shared-use stations only: every station row in "
 "the source file carries a public access flag, and the statewide Level 1 total is 256 "
 "ports against 40,078 Level 2 and 13,852 DC fast. Residential charging is therefore "
 "unobserved, and no charging measure in this study speaks to whether a household can "
 "charge where it parks. The storage series is drawn from the California Energy "
 "Commission storage system survey and is overwhelmingly customer-sited: the underlying "
 "records are 4,957 residential, 41 commercial and 2 utility, so the behind-the-meter "
 "reading of the storage results is supported by the source. A sensitivity excluding "
 "non-residential records is reported in Supplementary Table S16."))
for i in [141,142,143,144]: add(M(i))
for i in [145]+list(range(146,154)): add(M(i))
add(P(None,
 "Deployment is zero in a non-trivial share of ZCTAs, and the share differs sharply by "
 "technology: 5.3 per cent for PV, 6.6 for storage, 19.0 for aggregate charging, 22.3 "
 "for Level 2 and 44.2 for DC fast, but 97.8 per cent for Level 1 and 97.5 per cent for "
 "wind capacity (Supplementary Table S17). Level 1 charging and wind are therefore too "
 "sparse to support a coefficient at this geography and are reported descriptively "
 "rather than modelled in the main text."))
for i in [154,155,156,157]: add(M(i))
for i in [158,159,160,161,162]: add(M(i))
add(P(None,
 "The resource control differs by outcome by design rather than by oversight. Each "
 "technology takes the physical suitability measure that governs it: global horizontal "
 "irradiance for photovoltaics, heating and cooling degree days for storage and "
 "charging, and hub-height wind speed for wind. Holding one common resource control "
 "across all three would mis-specify at least two of them. Because the control differs, "
 "cross-technology comparison rests on the standardised scale and on the nested ladder, "
 "in which the control is held fixed within each outcome, rather than on an identical "
 "right-hand side."))
for i in [163,164,165,166,167,168]: add(M(i))

add(P('Heading2','Model series and nested cumulative ladder'))
add(P(None,
 "We estimate two complementary families of specifications. The first is a model series: "
 "each specification varies exactly one control block against a fixed core of income, "
 "race and ethnicity shares, poverty rate and the outcome-specific resource control. The "
 "blocks are education, housing value, housing structure, tenure, alternative climate and "
 "resource measures, centred income-by-race interactions, utility fixed effects, "
 "geographic controls, infrastructure context and an electricity-demand proxy. These are "
 "siblings rather than rungs — some swap a control rather than adding one — so the series "
 "answers which single block moves which coefficient, not whether the blocks jointly "
 "absorb an effect. Full specifications and coefficient tables are in Supplementary "
 "Table S18."))
add(P(None,
 "The second is a genuinely nested cumulative ladder in which each rung is a strict "
 "superset of the last: C1 adds nothing to the core; C2 adds educational attainment and "
 "median housing value; C3 adds ACS B25024 housing structure and B25003 tenure; C4 adds "
 "utility fixed effects; and C5 adds county fixed effects with county-clustered standard "
 "errors, dropping the ZCTA-level climate control that county fixed effects very nearly "
 "absorb. County and utility fixed effects are not stacked with climate in one design "
 "matrix. All rungs are fitted on one intersected, listwise-deleted sample — rows "
 "non-missing on every variable used anywhere in the ladder, plus the minimum "
 "cluster-size filter — so N and cluster count are identical at every rung and "
 "coefficient movement reflects controls alone. A separate model adds the "
 "electricity-demand proxy and infrastructure capacity; these sit on the causal path from "
 "income and race to adoption, so conditioning on them estimates a direct rather than a "
 "total effect and it is reported only as a conservative lower bound. Interactions are "
 "kept out of the cumulative ladder."))
add(P(None,
 "Two further robustness families accompany the ladder. A specification curve fits every "
 "subset of the six confounder blocks — 48 of the 64 combinations, excluding those that "
 "stack county and utility fixed effects together — and records, for each focal term, in "
 "how many specifications it is significant and same-signed as the median. Oster δ bounds "
 "compare the core specification with the saturated one, with R²max set to 1.3 times the "
 "saturated R², capped at one; δ is reported only where adding controls attenuates the "
 "coefficient, since the bound is not interpretable otherwise."))
for i in [202,203]: add(M(i))
for i in [204,205,206,207]: add(M(i))
add(P(None,
 "Four additional checks are reported in the Supplementary Information. Poisson "
 "pseudo-maximum-likelihood models fitted to raw counts with a population offset address "
 "the zero-inflation that a log(1 + rate) transformation handles only implicitly. "
 "Population-weighted estimates test whether unweighted ZCTA regressions are driven by "
 "small areas. A spatial error model with eight-nearest-neighbour weights addresses "
 "spatially structured omitted variables, which Conley standard errors correct for in "
 "inference but not in the conditional mean. Finally, because six outcomes are estimated "
 "across a series of specifications, individual p-values close to conventional thresholds "
 "should not be read in isolation; the specification curve and the Oster bounds are "
 "reported precisely so that robustness does not rest on any single test."))
add(P(None,
 "The per-capita energy affordability gap is the California Energy Commission "
 "affordability-gap series divided by ZCTA population, entered as log(1 + gap per "
 "capita). Its distribution is severely skewed — median about $75, maximum above "
 "$236,000, with the top 100 ZCTAs accounting for 92 per cent of the statewide total — "
 "which we attribute to error in the source series. Main-text affordability estimates "
 "exclude the 134 ZCTAs above $1,000 per capita; full-sample estimates are in "
 "Supplementary Table S12. Mean energy burden in the matched sample is about 2.2 per "
 "cent, below commonly cited household energy-burden estimates because the Commission "
 "series covers electricity costs rather than total household energy expenditure, and it "
 "should be read as a relative affordability-stress index rather than a total-burden "
 "measure."))
add(M(208))
for i in [210,211,212,213]: add(M(i))

# ---------------------- back matter ----------------------
add(P('Heading1','Data availability'))
add(P(None,"The harmonised ZCTA analysis dataset is deposited at Zenodo under CC-BY-4.0 "
 "[DOI to be inserted before submission]. All underlying sources are public and are listed "
 "in the Supplementary Information."))
add(P('Heading1','Code availability'))
add(P(None,"Data-construction and analysis code is available at "
 "https://github.com/vineetjnair9/distributed-energy-resources-equity-CA under the MIT License."))
add(P('Heading1','Author contributions'))
add(P(None,"[To be completed.]"))
add(P('Heading1','Competing interests'))
add(P(None,"The authors declare no competing interests."))
add(P('Heading1','Acknowledgements'))
add(P(None,"[To be completed.]"))

# ---------------------- references ----------------------
add(keep(253))
sdt=declean(keep(255))
cont=sdt.find(W+'sdtContent')
FIXES={
 6:"A. Drehobl, L. Ross, R. Ayala, A. Zaman, and J. Amann, “How high are household energy "
   "burdens? An assessment of national and metropolitan energy burden across the United "
   "States,” American Council for an Energy-Efficient Economy, Report U2006, Sep. 2020.",
 13:"R. McAllister, M. Coddington, M. Kolb, S. Murtishaw, L. Schwartz, and S. Sergici, "
    "“Distributed energy resources: technological and policy considerations of hosting "
    "capacity and locational value,” Western Interstate Energy Board, 2016.",
 15:"U.S. Department of Energy, “Distributed energy resource interconnection roadmap,” "
    "i2X initiative, 2023. [Online]. Available: https://www.energy.gov/eere/i2x",
 20:"Solar Energy Industries Association and Vote Solar, “Opening brief before the Public "
    "Utilities Commission of the State of California,” Rulemaking 20-08-020, 2021.",
}
if cont is not None:
    ps=[c for c in list(cont) if c.tag==W+'p']
    for c in list(cont):
        if c.tag==W+'p': cont.remove(c)
    kept=[]
    for j,p in enumerate(ps):
        if j==19: continue                       # duplicate of ref [9]
        if j in FIXES: settext(p, FIXES[j])
        kept.append(p)
    # renumber [n]
    n=0
    for p in kept:
        ts=list(p.iter(W+'t'))
        if ts and ts[0].text and ts[0].text.strip().startswith('['):
            n+=1; ts[0].text=f"[{n}]"
        cont.append(p)
add(sdt)
for i in range(256,268):
    el=declean(keep(i))
    ts=list(el.iter(W+'t'))
    if ts and ts[0].text and ts[0].text.strip().startswith('['):
        old=int(re.findall(r'\d+',ts[0].text)[0]); ts[0].text=f"[{old-1}]"
    add(el)
add(keep(269))                                   # sectPr

for c in list(body): body.remove(c)
for el in NB: body.append(el)
print("final body children:",len(list(body)))

os.makedirs(BUILD,exist_ok=True)
OUT=os.path.join(BUILD,'main')
if os.path.exists(OUT): shutil.rmtree(OUT)
shutil.copytree(SRC,OUT)
for f in ['comments.xml','commentsExtended.xml','commentsExtensible.xml','commentsIds.xml','people.xml']:
    fp=os.path.join(OUT,'word',f)
    if os.path.exists(fp): os.remove(fp)
# swap Figure 2 image
import subprocess
shutil.copy(os.path.join(ROOT,'outputs/standardized_figures/coefficient_path_c1_c5.png'),
            os.path.join(OUT,'word','media','image2.png'))
t.write(os.path.join(OUT,'word','document.xml'),xml_declaration=True,encoding='UTF-8',default_namespace=None)
print("written")


# =====================================================================
# Post-assembly passes.
#
# These correct things that only become visible once the body exists: sentences whose
# runs were split in the source (so a per-run replacement could not see them), the
# Supplementary figure numbering, and the bibliography. They are separate passes rather
# than part of the assembly because each one needs the finished document to operate on.
# =====================================================================

XS = '{http://www.w3.org/XML/1998/namespace}space'


def para_text(p):
    return ''.join(x.text or '' for x in p.iter(W + 't'))


def set_para_text(p, s):
    """Write `s` into a paragraph, keeping the first run's formatting.

    Word splits a sentence across runs whenever formatting or a spell-check boundary
    changes, so a replacement applied run-by-run silently misses any phrase that spans
    them. Collapsing to the first run is the only reliable way to rewrite a sentence.
    """
    ts = [x for x in p.iter(W + 't')]
    if not ts:
        return
    ts[0].text = s
    ts[0].set(XS, 'preserve')
    for x in ts[1:]:
        x.text = ''


# Sentence-level corrections found during verification. Kept here rather than in
# content.py because several target paragraphs carried over from the original
# manuscript, where the text is not ours to restate.
LATE_EDITS = [
    ("Section 6.6 states the baseline equation, Section 6.7 defines each rung of the ladder",
     "The Methods state the baseline equation and define each rung of the cumulative ladder"),
    ("(Section 6.2)", "(see Dataset construction)"),
    ("Section 6.6", "the Methods"), ("Section 6.7", "the Methods"), ("Section 6.2", "the Methods"),
    # The published standardized_tables standardize predictors only and leave the
    # outcome on its log(1 + rate) scale; the draft described a different convention.
    ("Figure 2 places the three outcomes on a common standardised scale. All coefficients "
     "reported in the main text are standardised, so a coefficient is the change in outcome "
     "standard deviations associated with a one-standard-deviation change in the predictor; "
     "one standard deviation is 6.6 percentage points for Black share, 23.8 for Hispanic "
     "share and 14.1 for Asian share (Supplementary Table S3).",
     "Figure 2 places the three outcomes on a common scale. Coefficients reported in the main "
     "text use standardised predictors, so a coefficient is the change in the log(1 + rate) "
     "outcome associated with a one-standard-deviation change in the predictor; one standard "
     "deviation is 6.6 percentage points for Black share, 23.8 for Hispanic share and 14.1 "
     "for Asian share, and a coefficient near -0.10 corresponds to roughly a 10 per cent "
     "lower deployment rate (Supplementary Table S3)."),
    # The two conventions gave different coefficient pairs for the same quantity. The
    # attenuation percentage is a ratio and is invariant to either, so the percentage
    # carries the claim and the pairs move to the SI.
    ("Adding the exhaustive ACS B25024 structure composition, with single-family units as the "
     "reference, and B25003 owner occupancy, with renters as the reference, moves the "
     "standardised Black-share coefficient for PV from \u22120.049 to \u22120.023 and the "
     "Asian-share coefficient from \u22120.082 to \u22120.051. For storage the corresponding "
     "movements are \u22120.106 to \u22120.059 and \u22120.252 to \u22120.171 (Figure 4). "
     "Area-level housing composition therefore absorbs between 32 and 53 per cent of these "
     "coefficients.",
     "Adding the exhaustive ACS B25024 structure composition, with single-family units as the "
     "reference, and B25003 owner occupancy, with renters as the reference, moves every race "
     "coefficient for PV and storage toward zero without eliminating it (Figure 3). "
     "Area-level housing composition absorbs between 32 and 53 per cent of these coefficients "
     "across the four technology-by-race combinations, most for the PV Black share and least "
     "for the storage Asian share; the coefficient pairs are in Supplementary Table S2."),
    ("In the baseline the standardised coefficient is \u22120.082 for PV and \u22120.252 for "
     "storage, and positive for aggregate charging at 0.058. Once housing structure and tenure "
     "enter, the charging coefficient falls to \u22120.008 and is no longer distinguishable "
     "from zero, while the PV and storage coefficients attenuate but remain negative at "
     "p < 0.001.",
     "In the baseline the coefficient is negative for PV and storage and positive for aggregate "
     "charging. Once housing structure and tenure enter, the charging coefficient falls to "
     "approximately zero and is no longer distinguishable from it, while the PV and storage "
     "coefficients attenuate but remain negative at p < 0.001."),
    # The current standardized_tables give a positive, significant Hispanic-share
    # coefficient for PV; the draft's Table 3 predates a data refresh.
    ("For rooftop PV, ZCTAs with higher median household income show higher adoption intensity, "
     "while those with larger Black and Asian population shares show substantially lower "
     "intensity.",
     "For rooftop PV, ZCTAs with higher median household income show higher adoption intensity, "
     "while those with larger Black and Asian population shares show substantially lower "
     "intensity. Hispanic share runs the other way for PV alone, positive and significant, and "
     "does not follow the Black and Asian pattern in any specification; we therefore treat the "
     "PV racial gradient as a Black- and Asian-share result rather than a general non-white one."),
    ("(Figure 3b, Supplementary Table S4)", "(Figure 4, Supplementary Table S4)"),
    ("ZIP/ZCTA", "ZCTA"),
    ("model ladder", "model series"),
]

# The Supplementary figure series ends up with a gap once the displaced figures are
# assigned; close it so the SI numbers run consecutively.
SI_FIG_RENUMBER = {1: 1, 2: 2, 3: 3, 4: 4, 6: 5, 7: 6, 8: 7, 9: 8, 10: 9,
                   11: 10, 12: 11, 13: 12, 14: 13, 15: 14, 16: 15, 17: 16}

# Descriptive SI items that the compressed main text no longer mentions individually.
# Nature requires every Supplementary item to be cited, so they are collected here.
SUPPLEMENTARY_POINTER = (
    "Descriptive material supporting the analysis sample is reported in the Supplementary "
    "Information: variable definitions (Supplementary Table S1), summary statistics "
    "(Supplementary Table S15), the distribution of raw deployment rates (Supplementary "
    "Fig. S15), non-parametric gradients against non-white share and educational attainment "
    "(Supplementary Figs. S9 and S10), the two affordability outcomes and their model "
    "coefficients (Supplementary Figs. S12, S13 and S14), the exploratory principal-component "
    "and K-means neighbourhood typology (Supplementary Fig. S11 and Supplementary Table S14), "
    "spatial residual maps (Supplementary Fig. S7) and the baseline cross-outcome comparison "
    "(Supplementary Fig. S16)."
)


def find_bibliography_sdt(body):
    """Return the structured-document tag holding the reference list.

    The document contains several sdt elements — hyperlink fields wrap themselves in one
    — so taking the first is wrong. The bibliography is the one whose content is a run
    of paragraphs each opening with a bracketed number.
    """
    best = None
    for sdt in body.iter(W + 'sdt'):
        cont = sdt.find(W + 'sdtContent')
        if cont is None:
            continue
        numbered = [p for p in cont.findall(W + 'p')
                    if re.match(r'^\[\d+\]', para_text(p).strip())]
        if len(numbered) >= 5 and (best is None or len(numbered) > best[1]):
            best = (sdt, len(numbered))
    if best is None:
        raise RuntimeError('bibliography sdt not found')
    return best[0]


def apply_text_passes(body):
    """LATE_EDITS, Supplementary figure renumbering, and the pointer paragraph."""
    sdt = find_bibliography_sdt(body)
    in_bib = {id(x) for x in sdt.iter(W + 'p')}
    n = 0
    for p in body.iter(W + 'p'):
        if id(p) in in_bib or p.find('.//' + W + 'drawing') is not None:
            continue
        s = para_text(p)
        if not s:
            continue
        original = s
        for a, b in LATE_EDITS:
            s = s.replace(a, b)
        s = re.sub(r'Supplementary Fig\. S(\d+)',
                   lambda m: 'Supplementary Fig. S%d' % SI_FIG_RENUMBER.get(int(m.group(1)), int(m.group(1))),
                   s)
        if s != original:
            set_para_text(p, s)
            n += 1

    # Insert the pointer just before the back matter.
    children = list(body)
    sect = children[-1]
    body.remove(sect)
    idx = len(list(body))
    for i, el in enumerate(list(body)):
        if el.tag == W + 'p' and para_text(el) == 'Data availability':
            idx = i
            break
    pointer = ET.Element(W + 'p')
    r = ET.SubElement(pointer, W + 'r')
    tt = ET.SubElement(r, W + 't')
    tt.set(XS, 'preserve')
    tt.text = SUPPLEMENTARY_POINTER
    body.insert(idx, pointer)
    body.append(sect)
    return n


def fix_bibliography(body):
    """Repair, prune and renumber the bibliography, and remap every in-text citation.

    Three things are wrong in the source: one entry is duplicated (Light, McIntosh &
    Stephenson at [9] and again at [20]); four titles carry reference-manager debris —
    cover text, an acknowledgements header, a filing header, and one entry with no
    author or year; and the compressed Introduction leaves several entries uncited.

    The list lives in two places. Entries [1]-[24] sit inside the citation-manager
    field; the data sources [25]-[36] are ordinary typed paragraphs after it. Both are
    renumbered here, in the same order they appear in the document.

    NOTE: this edits the citation-manager field in place. Refreshing the bibliography in
    Mendeley will restore the duplicate and the four garbled titles.
    """
    sdt = find_bibliography_sdt(body)
    cont = sdt.find(W + 'sdtContent')
    in_bib = {id(x) for x in cont.iter(W + 'p')}

    # Keyed by the number each entry prints. Retyped from the source documents; the
    # exporter will not clean these.
    fixes = {
        7: 'A. Drehobl, L. Ross, R. Ayala, A. Zaman, and J. Amann, \u201cHow high are household '
           'energy burdens? An assessment of national and metropolitan energy burden across the '
           'United States,\u201d American Council for an Energy-Efficient Economy, Report U2006, '
           'Sep. 2020.',
        14: 'R. McAllister, M. Coddington, M. Kolb, S. Murtishaw, L. Schwartz, and S. Sergici, '
            '\u201cDistributed energy resources: technological and policy considerations of '
            'hosting capacity and locational value,\u201d Western Interstate Energy Board, 2016.',
        16: 'U.S. Department of Energy, \u201cDistributed energy resource interconnection '
            'roadmap,\u201d i2X initiative, 2023. [Online]. Available: '
            'https://www.energy.gov/eere/i2x',
        21: 'Solar Energy Industries Association and Vote Solar, \u201cOpening brief before the '
            'Public Utilities Commission of the State of California,\u201d Rulemaking 20-08-020, '
            '2021.',
    }
    DUPLICATE = 20
    DUPLICATE_OF = 9
    CONLEY = 25

    # --- stage 1: repair the field entries, drop the duplicate, renumber them 1..n ---
    field_entries = []
    for p in cont.findall(W + 'p'):
        m = re.match(r'^\[(\d+)\]', para_text(p).strip())
        if not m:
            continue
        n = int(m.group(1))
        if n == DUPLICATE:
            cont.remove(p)
            continue
        if n in fixes:
            set_para_text(p, '[%d]%s' % (n, fixes[n]))
        field_entries.append(p)
    for i, p in enumerate(field_entries, start=1):
        set_para_text(p, '[%d]%s' % (i, re.sub(r'^\[\d+\]\s*', '', para_text(p).strip())))

    # --- stage 2: the typed data-source entries shift down by the removed duplicate ---
    typed = []
    for p in body.iter(W + 'p'):
        if id(p) in in_bib:
            continue
        s = para_text(p).strip()
        if re.match(r'^\[\d+\]', s) and ('[Online]' in s or 'doi:' in s):
            typed.append(p)
    for p in typed:
        n = int(re.match(r'^\[(\d+)\]', para_text(p).strip()).group(1))
        set_para_text(p, re.sub(r'^\[\d+\]', '[%d]' % (n - 1), para_text(p).strip()))

    # --- stage 3: in-text citations follow the same shift ---
    def shift(old):
        old = int(old)
        if old <= DUPLICATE - 1:
            return old
        if old == DUPLICATE:
            return DUPLICATE_OF
        return old - 1

    bib_ids = in_bib | {id(p) for p in typed}
    for p in body.iter(W + 'p'):
        if id(p) in bib_ids:
            continue
        s = para_text(p)
        if re.search(r'\[\d+\]', s):
            set_para_text(p, re.sub(r'\[(\d+)\]', lambda m: '[%d]' % shift(m.group(1)), s))

    # --- stage 4: cite Conley where the HAC estimator is described ---
    for p in body.iter(W + 'p'):
        if id(p) in bib_ids:
            continue
        s = para_text(p)
        if 'Conley heteroskedasticity- and autocorrelation-consistent' in s and \
                '[%d]' % shift(CONLEY) not in s:
            set_para_text(p, s.replace(
                'Conley heteroskedasticity- and autocorrelation-consistent (HAC) standard errors',
                'Conley heteroskedasticity- and autocorrelation-consistent (HAC) standard errors '
                '[%d]' % shift(CONLEY)))
            break

    # --- stage 5: drop entries the compressed text no longer cites, renumber once more ---
    refs = []
    for p in body.iter(W + 'p'):
        if id(p) not in bib_ids:
            continue
        m = re.match(r'^\[(\d+)\]', para_text(p).strip())
        if m:
            refs.append((int(m.group(1)), p))
    cited = set()
    for p in body.iter(W + 'p'):
        if id(p) in bib_ids:
            continue
        cited |= {int(x) for x in re.findall(r'\[(\d+)\]', para_text(p))}

    keep = [(n, p) for n, p in refs if n in cited]
    dropped = sorted(n for n, _ in refs if n not in cited)
    mapping = {n: i + 1 for i, (n, _) in enumerate(keep)}
    drop_ids = {id(p) for n, p in refs if n not in cited}
    for parent in list(body.iter()):
        for c in list(parent):
            if id(c) in drop_ids:
                parent.remove(c)
    for old, p in keep:
        set_para_text(p, '[%d]%s' % (mapping[old],
                                     re.sub(r'^\[\d+\]\s*', '', para_text(p).strip())))
    for p in body.iter(W + 'p'):
        if id(p) in bib_ids:
            continue
        s = para_text(p)
        if re.search(r'\[\d+\]', s):
            set_para_text(p, re.sub(r'\[(\d+)\]',
                                    lambda m: '[%d]' % mapping.get(int(m.group(1)), int(m.group(1))), s))
    return len(keep), dropped


def repackage(unpacked, dest):
    if os.path.exists(dest):
        os.remove(dest)
    zf = zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED)
    zf.write(os.path.join(unpacked, '[Content_Types].xml'), '[Content_Types].xml')
    for r, _, files in os.walk(unpacked):
        for f in files:
            full = os.path.join(r, f)
            rel = os.path.relpath(full, unpacked)
            if rel != '[Content_Types].xml':
                zf.write(full, rel)
    zf.close()
    return dest


def strip_comment_parts(unpacked):
    """Remove comment parts, relationships and content-type overrides.

    Comments survive into the PDF on most submission systems, so they are removed
    rather than left resolved.
    """
    for f in ('comments.xml', 'commentsExtended.xml', 'commentsExtensible.xml',
              'commentsIds.xml', 'people.xml'):
        fp = os.path.join(unpacked, 'word', f)
        if os.path.exists(fp):
            os.remove(fp)
    rp = os.path.join(unpacked, 'word', '_rels', 'document.xml.rels')
    s = open(rp, encoding='utf8').read()
    s = re.sub(r'<Relationship[^>]*Target="comments[^"]*"[^>]*/>', '', s)
    s = re.sub(r'<Relationship[^>]*Target="people\.xml"[^>]*/>', '', s)
    open(rp, 'w', encoding='utf8').write(s)
    cp = os.path.join(unpacked, '[Content_Types].xml')
    s = open(cp, encoding='utf8').read()
    for part in ('comments', 'commentsExtended', 'commentsExtensible', 'commentsIds', 'people'):
        s = re.sub(r'<Override[^>]*PartName="/word/%s\.xml"[^>]*/>' % part, '', s)
    open(cp, 'w', encoding='utf8').write(s)


def fix_image_extent(unpacked, rel_id, image_name, width_emu=6400800):
    """Reset a drawing's extent after swapping in an image with a different aspect ratio."""
    from PIL import Image
    iw, ih = Image.open(os.path.join(unpacked, 'word', 'media', image_name)).size
    f = os.path.join(unpacked, 'word', 'document.xml')
    tree = ET.parse(f)
    cy = int(width_emu * ih / iw)
    for dr in tree.getroot().iter(W + 'drawing'):
        blip = dr.find('.//' + A + 'blip')
        if blip is None or blip.get(R + 'embed') != rel_id:
            continue
        ext = dr.find('.//' + WP + 'extent')
        if ext is not None:
            ext.set('cx', str(width_emu))
            ext.set('cy', str(cy))
        for e in dr.iter(A + 'ext'):
            e.set('cx', str(width_emu))
            e.set('cy', str(cy))
    tree.write(f, xml_declaration=True, encoding='UTF-8')


# =====================================================================
if __name__ != '__main__':
    raise SystemExit('build_manuscript.py is a script, not a module')

print('assembled body: %d elements' % len(list(body)))
edits = apply_text_passes(body)
print('sentence-level corrections applied: %d paragraphs' % edits)
n_refs, dropped = fix_bibliography(body)
print('references: %d kept, dropped as uncited: %s' % (n_refs, dropped or 'none'))
t.write(os.path.join(OUT, 'word', 'document.xml'), xml_declaration=True, encoding='UTF-8')

# Figure 2 becomes the nested-ladder panel, which has a different aspect ratio than the
# figure whose drawing it reuses.
fix_image_extent(OUT, 'rId11', 'image2.png')
strip_comment_parts(OUT)
repackage(OUT, DEST_DOCX)
print('wrote %s (%.1f MB)' % (DEST_DOCX, os.path.getsize(DEST_DOCX) / 1e6))

# ---------------------------------------------------------------- verification
import docx  # noqa: E402

d = docx.Document(DEST_DOCX)
paras = [(p.style.name, p.text) for p in d.paragraphs]
full = '\n'.join(t for _, t in paras)
intro = body_words = state = 0
for style, text in paras:
    if style == 'Heading 1':
        state = 1 if text == 'Abstract' else (2 if text in ('Results', 'Discussion') else 0)
        continue
    if style == 'Caption':
        continue
    if state == 1:
        intro += len(text.split())
    elif state == 2:
        body_words += len(text.split())
title, abstract = paras[0][1], paras[3][1]
abs_words = len(abstract.split())
main_words = intro - abs_words + body_words
items = len(re.findall(r'Fig\. \d+ \|', full)) + len(re.findall(r'Table \d+ \|', full))
banned = [b for b in ('ZIP/ZCTA', 'model ladder', 'household outlets', 'parsing fault',
                      'in the repo', 'asset folder') if b in full]
h1 = [t for s, t in paras if s == 'Heading 1']

checks = [
    (len(title.split()) <= 10 and len(title) <= 90,
     'title %d words / %d chars (limit 10 / 90)' % (len(title.split()), len(title))),
    (abs_words <= 150 and not re.search(r'\[\d+\]', abstract),
     'abstract %d words, unreferenced (limit 150)' % abs_words),
    (main_words <= 3500, 'main text %d words (limit 3500)' % main_words),
    (items == 6, 'display items %d (limit 6)' % items),
    (not re.findall(r'Section \d+', full), 'no numbered section cross-references'),
    (not banned, 'banned phrases: %s' % (banned or 'none')),
    ('word/comments.xml' not in zipfile.ZipFile(DEST_DOCX).namelist(), 'comments removed'),
    (h1[:4] == ['Abstract', 'Results', 'Discussion', 'Methods'],
     'structure %s' % ' / '.join(h1[:4])),
    (all(k in full for k in ('Data availability', 'Code availability',
                             'Competing interests', 'Author contributions')),
     'back matter present'),
]
print('\n== compliance ==')
for ok, label in checks:
    print('%s %s' % ('PASS' if ok else 'FAIL', label))
if not all(ok for ok, _ in checks):
    raise SystemExit('compliance checks failed')
