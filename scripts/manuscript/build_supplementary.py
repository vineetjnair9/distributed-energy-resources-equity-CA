#!/usr/bin/env python3
"""Build the Supplementary Information document.

Collects everything displaced from the main manuscript by the Nature Sustainability
limits — 16 figures and 18 tables — into a separate file, reusing the original
paragraphs so the embedded images survive, and generating the new tables from the
outputs of ``scripts/nature_revision_analysis.py``.

Run from the repository root, after ``nature_revision_analysis.py``:

    python scripts/manuscript/build_supplementary.py

Writes ``site/supplementary_information.docx``.

Numbering is driven by the main text: every Supplementary item here is cited there, and
``build_manuscript.py`` applies the matching renumbering to its own references. Change
one and you must change the other.
"""
# -*- coding: utf-8 -*-
import copy, os, re, shutil, sys, zipfile
import xml.etree.ElementTree as ET
import pandas as pd

ROOT=os.path.abspath(os.environ.get('REPO_ROOT',os.path.join(os.path.dirname(__file__),'..','..')))
BUILD=os.path.join(ROOT,'build')
NR=os.path.join(ROOT,'outputs','nature_revision')
SOURCE_DOCX=os.path.join(ROOT,'site','index.docx')
DEST_DOCX=os.path.join(ROOT,'site','supplementary_information.docx')
os.makedirs(BUILD,exist_ok=True)
_src=os.path.join(BUILD,'_source')
if not os.path.exists(_src):
    with zipfile.ZipFile(SOURCE_DOCX) as _zf: _zf.extractall(_src)
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
WP='{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'
for p,u in [('w',W),('a',A),('r',R),('wp',WP)]: ET.register_namespace(p,u[1:-1])
SRC=os.path.join(BUILD,'_source')
t=ET.parse(SRC+'/word/document.xml'); body=t.getroot().find(W+'body'); CH=list(body)
NB=[]
def add(x): NB.append(x)

def build_spec_curve_panel():
    """Stack the three per-outcome specification-curve figures into one SI panel."""
    from PIL import Image
    figs = os.path.join(ROOT, 'outputs', 'standardized_figures')
    ims = [Image.open(os.path.join(figs, 'spec_curve_y_%s.png' % n)).convert('RGB')
           for n in ('pv', 'storage', 'chargers')]
    w = max(i.width for i in ims)
    ims = [i.resize((w, int(i.height * w / i.width)), Image.LANCZOS) if i.width != w else i
           for i in ims]
    gap = 40
    out = Image.new('RGB', (w, sum(i.height for i in ims) + gap * (len(ims) - 1)), 'white')
    y = 0
    for i in ims:
        out.paste(i, (0, y))
        y += i.height + gap
    path = os.path.join(BUILD, 'spec_curve_panel.png')
    out.save(path, dpi=(300, 300))
    return path


def declean(el):
    for parent in el.iter():
        for c in list(parent):
            if c.tag in (W+'commentRangeStart',W+'commentRangeEnd'): parent.remove(c)
            elif c.tag==W+'r' and c.find(W+'commentReference') is not None: parent.remove(c)
    return el
def P(style,text):
    p=ET.Element(W+'p')
    if style:
        pr=ET.SubElement(p,W+'pPr'); s=ET.SubElement(pr,W+'pStyle'); s.set(W+'val',style)
    r=ET.SubElement(p,W+'r'); tt=ET.SubElement(r,W+'t')
    tt.set('{http://www.w3.org/XML/1998/namespace}space','preserve'); tt.text=text
    return p
def fig(i,cap):
    add(declean(copy.deepcopy(CH[i]))); add(P('Caption',cap))
TBL_PROTO=CH[30]
def table(rows):
    tbl=ET.Element(W+'tbl'); pr=TBL_PROTO.find(W+'tblPr')
    if pr is not None: tbl.append(copy.deepcopy(pr))
    g=ET.SubElement(tbl,W+'tblGrid')
    for _ in rows[0]: ET.SubElement(g,W+'gridCol')
    for ri,row in enumerate(rows):
        tr=ET.SubElement(tbl,W+'tr')
        for cell in row:
            tc=ET.SubElement(tr,W+'tc'); ET.SubElement(tc,W+'tcPr')
            p=ET.SubElement(tc,W+'p'); r=ET.SubElement(p,W+'r')
            if ri==0:
                rp=ET.SubElement(r,W+'rPr'); ET.SubElement(rp,W+'b')
            tt=ET.SubElement(r,W+'t'); tt.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
            tt.text=str(cell)
    return tbl
def tab(cap,rows): add(P('Caption',cap)); add(table(rows))
def df2rows(df,cols=None,fmt=3):
    df=df[cols] if cols else df
    head=[str(c) for c in df.columns]
    body=[[(f"{v:.{fmt}f}" if isinstance(v,float) else str(v)) for v in r] for r in df.itertuples(index=False)]
    return [head]+body

add(P('Title','Supplementary Information'))
add(P(None,"Supplementary figures and tables for “Inequity in distributed energy adoption is "
 "technology-specific, not uniform”. Every item here is cited at least once in the main text."))

add(P('Heading1','Supplementary Figures'))
fig(44,"Supplementary Fig. S1 | Rooftop PV: coefficients across the model series. Each panel traces one coefficient across the control-block sensitivity specifications, with 95% confidence bands; filled markers denote p < 0.05.")
fig(54,"Supplementary Fig. S2 | Battery storage: coefficients across the model series. Coefficients are larger and more persistent than the corresponding PV estimates.")
fig(60,"Supplementary Fig. S3 | Specification curve for rooftop PV, battery storage and aggregate EV charging. Each panel sorts the focal coefficient across all 48 valid combinations of the six confounder blocks, with the block-membership matrix below.")
fig(95,"Supplementary Fig. S5 | Wind capacity: coefficients across the model series, included as contextual material. Wind capacity is zero in 97.5 per cent of ZCTAs.")
fig(220,"Supplementary Fig. S6 | Battery storage: cross-validated predictive comparison of linear and nonlinear models. Error bars are ±1 s.d. across five cross-validation folds.")
fig(224,"Supplementary Fig. S7 | Aggregate EV charging: cross-validated predictive comparison of linear and nonlinear models.")
fig(228,"Supplementary Fig. S8 | Rooftop PV: observed adoption and baseline standardised residuals by ZCTA.")
fig(232,"Supplementary Fig. S9 | Wind capacity: cross-validated predictive comparison of linear and nonlinear models.")
fig(81,"Supplementary Fig. S10 | Descriptive LOWESS gradients between combined non-white share and the three headline outcomes. Shaded ribbons are 95% bootstrap confidence intervals; these panels do not condition on the full control set.")
fig(83,"Supplementary Fig. S11 | Descriptive LOWESS gradients between bachelor's-degree attainment and the three headline outcomes.")
fig(88,"Supplementary Fig. S12 | California ZCTA clusters from exploratory principal-component and K-means analysis. Cluster identifiers are ordered from lowest to highest mean household income.")
fig(72,"Supplementary Fig. S13 | Descriptive LOWESS gradients between neighbourhood characteristics and the two energy-affordability outcomes.")
fig(74,"Supplementary Fig. S14 | DER predictors in the energy-burden and affordability-gap models. Points are coefficient estimates; horizontal lines are 95% confidence intervals.")
fig(76,"Supplementary Fig. S15 | Coefficient stability for the energy-burden and affordability-gap outcomes across the model series.")
fig(136,"Supplementary Fig. S16 | Descriptive distributions for raw DER deployment rates together with median household income and poverty rate.")
fig(37,"Supplementary Fig. S17 | Cross-outcome dot-whisker comparison of baseline standardised coefficients for rooftop PV, storage and EV charging.")

add(P('Heading1','Supplementary Tables'))
add(P('Caption',"Supplementary Table S1 | Variable definitions for the main outcomes, predictors and controls."))
add(declean(copy.deepcopy(CH[129])))
tab("Supplementary Table S2 | Race-coefficient attenuation after adding housing structure and tenure. Standardised coefficients; baseline versus the specification adding exhaustive ACS B25024 structure shares and B25003 owner occupancy.",
 [["Outcome","Term","Baseline","+ structure & tenure","Attenuation"],
  ["Rooftop PV","Black share","−0.049","−0.023","53%"],
  ["Rooftop PV","Asian share","−0.082","−0.051","38%"],
  ["Battery storage","Black share","−0.106","−0.059","44%"],
  ["Battery storage","Asian share","−0.252","−0.171","32%"],
  ["Aggregate charging","Asian share","0.058","−0.008","not distinguishable from zero"]])
sd=pd.read_csv(os.path.join(NR,'sd_conversion.csv'))
tab("Supplementary Table S3 | Predictor means and standard deviations on the analysis sample, for converting standardised coefficients to percentage-point changes.",
 [["Predictor","Mean","Standard deviation","One s.d. in percentage points"]]+
 [[r.predictor,f"{r.mean:.3f}",f"{r.sd:.3f}",("—" if r.predictor.startswith("log") else f"{r.one_sd_in_pp:.1f}")] for r in sd.itertuples()])
add(P('Caption',"Supplementary Table S4 | EV charger subtype comparison in baseline models."))
add(declean(copy.deepcopy(CH[65])))
L=pd.read_csv(os.path.join(NR,'ladder_c1_c5.csv'))
L=L[L.outcome.isin(["y_pv","y_storage","y_chargers"])]
NAME={"y_pv":"Rooftop PV","y_storage":"Battery storage","y_chargers":"EV charging",
 "log_median_household_income":"Log income","pct_black":"Black share","pct_hispanic":"Hispanic share","pct_asian":"Asian share"}
rows=[["Outcome","Term","C1","C2","C3","C4","C5"]]
for o in ["y_pv","y_storage","y_chargers"]:
    for tm in ["log_median_household_income","pct_black","pct_hispanic","pct_asian"]:
        g=L[(L.outcome==o)&(L.term==tm)].set_index("rung")
        cells=[]
        for k in ["C1","C2","C3","C4","C5"]:
            if k in g.index:
                b=g.loc[k,"beta"]; p=g.loc[k,"p"]
                st="***" if p<0.001 else ("**" if p<0.01 else ("*" if p<0.05 else ""))
                cells.append(f"{b:.3f}{st}")
            else: cells.append("—")
        rows.append([NAME[o],NAME[tm]]+cells)
tab("Supplementary Table S5 | Nested cumulative ladder, C1 to C5. Standardised predictors; frozen common sample of 1,160 ZCTAs and 42 county clusters, identical at every rung. C5 uses county-clustered standard errors. *p < 0.05, **p < 0.01, ***p < 0.001.",rows)
add(P('Caption',"Supplementary Table S6 | Battery storage conditional on local PV deployment. This model conditions on a parallel outcome of the same predictors and is not a better-identified estimate of the storage gap."))
add(declean(copy.deepcopy(CH[51])))
add(P('Caption',"Supplementary Table S7 | Moran's I on OLS residuals, eight-nearest-neighbour weights. Every entry is significant at p < 0.001 by permutation test."))
add(declean(copy.deepcopy(CH[248])))
add(P('Caption',"Supplementary Table S8 | Conley spatial HAC standard errors, Bartlett kernel over great-circle distance. Coefficients are identical across columns; only standard errors differ."))
add(declean(copy.deepcopy(CH[252])))
S=pd.read_csv(os.path.join(NR,'spatial_error_model.csv'))
tab("Supplementary Table S9 | Spatial error model, maximum likelihood, eight-nearest-neighbour weights. Standardised predictors; λ is the spatial autoregressive error parameter.",
 [["Outcome","Term","Coefficient","Std. error","p","λ","N"]]+
 [[NAME[r.outcome],NAME[r.term],f"{r.beta_SEM:.3f}",f"{r.se_SEM:.3f}",f"{r.p_SEM:.3f}",f"{r.lambda_:.2f}",str(int(r.N))] for r in S.itertuples()])
Pm=pd.read_csv(os.path.join(NR,'ppml_negbin.csv')); Pm=Pm[Pm.model=="PPML"]
tab("Supplementary Table S10 | Poisson pseudo-maximum-likelihood models on raw counts with a population offset. Fitted directly to counts rather than to a log(1 + rate) transformation, so structural zeros are handled without transformation. HC1 standard errors.",
 [["Outcome","Term","Coefficient","Std. error","p","N"]]+
 [[r.outcome,NAME.get(r.term,r.term),f"{r.coef:.3f}",f"{r.se:.3f}",f"{r.p:.3f}",str(int(r.N))] for r in Pm.itertuples()])
Wt=pd.read_csv(os.path.join(NR,'population_weighted.csv'))
tab("Supplementary Table S11 | Population-weighted versus unweighted baseline estimates. Standardised predictors; weights are ZCTA total population.",
 [["Outcome","Term","Unweighted","p","Population-weighted","p","N"]]+
 [[NAME[r.outcome],NAME[r.term],f"{r.beta_unweighted:.3f}",f"{r.p_unw:.3f}",f"{r.beta_weighted:.3f}",f"{r.p_w:.3f}",str(int(r.N))] for r in Wt.itertuples()])
Af=pd.read_csv(os.path.join(NR,'affordability_outliers.csv'))
tab("Supplementary Table S12 | Energy-affordability models with and without the 134 ZCTAs whose per-capita affordability gap exceeds $1,000. Standardised predictors.",
 [["Outcome","Sample","Term","Coefficient","p","N","R²"]]+
 [[r.outcome,r.sample,NAME.get(r.term,r.term),f"{r.beta:.3f}",f"{r.p:.3f}",str(int(r.N)),f"{r.R2:.3f}"] for r in Af.itertuples()])
add(P('Caption',"Supplementary Table S13 | Variance inflation factors across four rooftop PV specifications. Values above about 10 indicate a coefficient is not separately identified."))
add(declean(copy.deepcopy(CH[244])))
add(P('Caption',"Supplementary Table S14 | Cluster-profile means from the principal-component and K-means assignment."))
add(declean(copy.deepcopy(CH[91])))
add(P('Caption',"Supplementary Table S15 | Summary statistics for the main outcomes and key predictors."))
add(declean(copy.deepcopy(CH[139])))
tab("Supplementary Table S16 | Storage sensitivity by customer sector. The California Energy Commission storage records are 193,070 residential, 3,211 commercial and 291 utility. Standardised predictors; models re-fitted on capacity aggregated from all sectors and from residential records only.",
 [["Term","All sectors","p","Residential only","p"],
  ["Log income","0.523","<0.001","0.421","<0.001"],
  ["Black share","−0.116","0.002","−0.107","<0.001"],
  ["Hispanic share","−0.024","0.646","−0.247","<0.001"],
  ["Asian share","−0.303","<0.001","−0.302","<0.001"],
  ["Poverty rate","0.130","0.162","−0.022","0.467"],
  ["N","1,390","","1,390",""],
  ["R²","0.087","","0.414",""]])
Z=pd.read_csv(os.path.join(NR,'zero_shares.csv'))
tab("Supplementary Table S17 | Share of ZCTAs reporting zero deployment, by outcome. Level 1 charging and wind capacity are too sparse to support a coefficient at this geography.",
 [["Outcome","Source variable","N","% zero","Median","Maximum"]]+
 [[NAME.get(r.outcome,r.outcome),r.raw_var,str(int(r.N)),f"{r.pct_zero:.1f}",f"{r.median:.2f}",f"{r.max:.1f}"] for r in Z.itertuples()])
tab("Supplementary Table S18 | Specifications in the model series. Each varies one control block against the fixed core of income, race and ethnicity shares, poverty rate and the outcome-specific resource control.",
 [["Label","Deviation from the core"],
  ["M1","Core specification"],
  ["M2 / M2C / M2D","Adds educational attainment, or housing value, or exhaustive housing structure, or structure and tenure"],
  ["M3A / M3B / M3C","Resource control swapped: degree days, mean temperature, or global horizontal irradiance"],
  ["M4 / M4R","Adds centred income-by-race interactions; M4R drops the poverty control"],
  ["M5 / M5C","Adds utility fixed effects; M5C re-estimates the core with county-clustered standard errors"],
  ["M6A / M6B","Replaces the resource control with latitude and longitude, or with county fixed effects"],
  ["M7 / M7pc","Adds installed infrastructure capacity, in levels or per capita"],
  ["M8","Adds the logged electricity-demand proxy"],
  ["M9","Storage only: adds local PV deployment"]])
add(copy.deepcopy(CH[269]))

for c in list(body): body.remove(c)
for el in NB: body.append(el)
print("SI body children:",len(list(body)))
OUT=os.path.join(BUILD,'si')
if os.path.exists(OUT): shutil.rmtree(OUT)
shutil.copytree(SRC,OUT)
for f in ['comments.xml','commentsExtended.xml','commentsExtensible.xml','commentsIds.xml','people.xml']:
    fp=os.path.join(OUT,'word',f)
    if os.path.exists(fp): os.remove(fp)
shutil.copy(build_spec_curve_panel(),os.path.join(OUT,'word','media','image6.png'))
t.write(os.path.join(OUT,'word','document.xml'),xml_declaration=True,encoding='UTF-8')
# fix extent of swapped image + strip comment rels
from PIL import Image
im=Image.open(os.path.join(OUT,'word','media','image6.png')); iw,ih=im.size
t2=ET.parse(os.path.join(OUT,'word','document.xml')); rt=t2.getroot()
for dr in rt.iter(W+'drawing'):
    b=dr.find('.//'+A+'blip')
    if b is not None and b.get(R+'embed')=='rId15':
        cx=5943600; cy=int(cx*ih/iw)
        e=dr.find('.//'+WP+'extent')
        if e is not None: e.set('cx',str(cx)); e.set('cy',str(cy))
        for ex in dr.iter(A+'ext'): ex.set('cx',str(cx)); ex.set('cy',str(cy))
t2.write(os.path.join(OUT,'word','document.xml'),xml_declaration=True,encoding='UTF-8')
rp=os.path.join(OUT,'word','_rels','document.xml.rels'); s=open(rp,encoding='utf8').read()
s=re.sub(r'<Relationship[^>]*Target="comments[^"]*"[^>]*/>','',s); s=re.sub(r'<Relationship[^>]*Target="people\.xml"[^>]*/>','',s)
open(rp,'w',encoding='utf8').write(s)
cp=os.path.join(OUT,'[Content_Types].xml'); s=open(cp,encoding='utf8').read()
for part in ['comments','commentsExtended','commentsExtensible','commentsIds','people']:
    s=re.sub(r'<Override[^>]*PartName="/word/%s\.xml"[^>]*/>'%part,'',s)
open(cp,'w',encoding='utf8').write(s)


# Close the gap the SI figure series picks up once displaced figures are assigned, so
# the numbers run consecutively and match the main text.
dest = DEST_DOCX

SI_FIG_RENUMBER = {1:1,2:2,3:3,4:4,6:5,7:6,8:7,9:8,10:9,11:10,12:11,13:12,14:13,15:14,16:15,17:16}
_t2 = ET.parse(os.path.join(OUT,'word','document.xml'))
_body = _t2.getroot().find(W+'body')
for _p in _body.iter(W+'p'):
    if _p.find('.//'+W+'drawing') is not None: continue
    _ts=[x for x in _p.iter(W+'t')]; _s=''.join(x.text or '' for x in _ts)
    if not _s: continue
    _s2 = _s.replace('Supplementary Fig. S5 |','Supplementary Fig. S4 |')
    _s2 = re.sub(r'Supplementary Fig\. S(\d+)',
                 lambda m: 'Supplementary Fig. S%d'%SI_FIG_RENUMBER.get(int(m.group(1)),int(m.group(1))), _s2)
    if _s2!=_s:
        _ts[0].text=_s2; _ts[0].set('{http://www.w3.org/XML/1998/namespace}space','preserve')
        for _x in _ts[1:]: _x.text=''
_t2.write(os.path.join(OUT,'word','document.xml'),xml_declaration=True,encoding='UTF-8')

os.path.exists(dest) and os.remove(dest)
zf=zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED)
zf.write(os.path.join(OUT,'[Content_Types].xml'),'[Content_Types].xml')
for _r,_d,_fs in os.walk(OUT):
    for _f in _fs:
        _fu=os.path.join(_r,_f); _rel=os.path.relpath(_fu,OUT)
        if _rel!='[Content_Types].xml': zf.write(_fu,_rel)
zf.close()
import docx
_doc=docx.Document(dest); _txt='\n'.join(p.text for p in _doc.paragraphs)
print('wrote %s (%.1f MB)'%(dest,os.path.getsize(dest)/1e6))
print('  %d figures, %d tables'%(len(re.findall(r'Fig\. S\d+ \|',_txt)), len(_doc.tables)))
