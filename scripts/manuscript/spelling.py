# -*- coding: utf-8 -*-
"""British to American spelling conversion for both documents.

Applied at build time to assembled paragraph and table text rather than to the source
prose, so it also catches words split across adjacent string literals in ``content.py``
and ``si_content.py`` — a plain search-and-replace on the sources misses those and
leaves a British spelling in the output.

Pairs are given in base form. Verbs ending in -ise are matched on their stem so every
inflection is covered, including the ones that drop the final e (``harmonising``,
``standardising``). Words identical in both variants — analysis, characteristics,
hypothesis, stepwise, listwise — are deliberately absent and are left alone by the
word-boundary match.
"""
import re

# -ise verbs and their derived nouns. Listed in base form; inflections are derived.
_ISE = [
    'standardise', 'unstandardise', 'normalise', 'summarise', 'organise', 'generalise',
    'characterise', 'harmonise', 'synthesise', 'hypothesise', 'decarbonise', 'utilise',
    'prioritise', 'recognise', 'emphasise', 'minimise', 'maximise', 'specialise',
    'categorise', 'parameterise', 'mobilise', 'stabilise', 'formalise', 'finalise',
    'realise', 'penalise', 'equalise', 'legitimise', 'marginalise', 'incentivise',
    'optimise', 'visualise', 'itemise', 'contextualise', 'systematise',
    'operationalise', 'modernise', 'nationalise', 'privatise', 'subsidise',
]

# Everything else, as literal (British, American) pairs.
_LITERAL = [
    ('per cent', 'percent'),
    ('neighbourhood', 'neighborhood'), ('neighbouring', 'neighboring'),
    ('neighbours', 'neighbors'), ('neighbour', 'neighbor'),
    ('centred', 'centered'), ('centres', 'centers'), ('centre', 'center'),
    ('kilometres', 'kilometers'), ('kilometre', 'kilometer'),
    ('metres', 'meters'), ('metre', 'meter'),
    ('programmes', 'programs'), ('programme', 'program'),
    ('behavioural', 'behavioral'), ('behaviours', 'behaviors'), ('behaviour', 'behavior'),
    ('artefacts', 'artifacts'), ('artefact', 'artifact'),
    ('modelling', 'modeling'), ('modelled', 'modeled'),
    ('labelling', 'labeling'), ('labelled', 'labeled'),
    ('favour', 'favor'), ('labour', 'labor'), ('colour', 'color'),
    ('rigour', 'rigor'), ('vigour', 'vigor'), ('odour', 'odor'), ('humour', 'humor'),
    ('defence', 'defense'), ('offence', 'offense'), ('licence', 'license'),
    ('practise', 'practice'),
    ('whilst', 'while'), ('amongst', 'among'), ('towards', 'toward'),
    ('ageing', 'aging'), ('judgement', 'judgment'), ('enrolment', 'enrollment'),
    ('fuelled', 'fueled'), ('signalling', 'signaling'), ('cancelled', 'canceled'),
    ('travelling', 'traveling'), ('catalogue', 'catalog'), ('analogue', 'analog'),
    ('sceptical', 'skeptical'), ('sceptic', 'skeptic'),
    ('sulphur', 'sulfur'), ('aluminium', 'aluminum'), ('storey', 'story'),
    ('learnt', 'learned'), ('spelt', 'spelled'), ('burnt', 'burned'),
    ('fibre', 'fiber'), ('litre', 'liter'), ('theatre', 'theater'),
]


def _match_case(template: str, word: str) -> str:
    """Return `word` cased like `template`."""
    if template.isupper():
        return word.upper()
    if template[:1].isupper():
        return word[:1].upper() + word[1:]
    return word


def _build():
    rules = []
    for verb in _ISE:
        stem_br, stem_am = verb[:-1], verb[:-3] + 'iz'   # ...ise -> ...iz
        rules.append((re.compile(r'\b' + stem_br + r'(e|es|ed|ing|ation|ations)\b', re.I),
                      stem_am))
    for br, am in _LITERAL:
        rules.append((re.compile(r'\b' + re.escape(br) + r'\b', re.I), am))
    return rules


_RULES = _build()


def americanize(text: str) -> str:
    """Return `text` with British spellings replaced by American ones."""
    for pattern, replacement in _RULES:
        def repl(m, replacement=replacement):
            suffix = m.group(1) if m.lastindex else ''
            return _match_case(m.group(0), replacement + suffix)
        text = pattern.sub(repl, text)
    return text
