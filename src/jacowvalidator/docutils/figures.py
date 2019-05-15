import re
from collections import OrderedDict
from itertools import chain
from jacowvalidator.docutils.styles import check_style

RE_FIG_TITLES = re.compile(r'(^Figure \d+[.:])')
RE_WRONG_TITLES = re.compile(r'(^Fig.\s?\d+|^Figure\s?\d+[.\s]+)')
RE_FIG_IN_TEXT = re.compile(r'(Fig.\s?\d+|Figure\s?\d+[.\s]+)')

FIGURE_DETAILS = {
    'styles': {
        'jacow': 'Figure Caption',
    },
    'alignment': 'CENTER',
    'font_size': 10.0,
    'space_before': 3.0,
    'space_after': ['>=', 3.0],
    'bold': None,
    'italic': None,
    'desc': 'Single Line',
}

FIGURE_MULTI_DETAILS = {
    'styles': {
        'jacow': 'Figure Caption Multi Line',
    },
    'alignment': 'JUSTIFY',
    'font_size': 10.0,
    'space_before': 3.0,
    'space_after': ['>=', 3.0],
    'bold': None,
    'italic': None,
    'desc': 'Multi Line',
}


def _fig_to_int(s):
    return int(''.join(filter(str.isdigit, s)))


def extract_figures(doc):
    figures_refs = []
    figures_captions = []
    wrong_captions = []

    def _find_figure_captions(p):
        for f in RE_FIG_TITLES.findall(p.text.strip()):
            figure_compare = FIGURE_DETAILS
            # 55 chars is approx where it changes from 1 line to 2 lines
            text = p.text.strip()
            if len(text) > 55:
                figure_compare = FIGURE_MULTI_DETAILS

            style_ok, detail = check_style(p, figure_compare)
            style_name = p.style.name
            if p.style.name not in ['Figure Caption', 'Caption Multi Line', 'Caption']:
                final_style_ok = 2
            else:
                final_style_ok = style_ok and p.style.name in ['Figure Caption', 'Caption Multi Line', 'Caption']

            if 40 < len(text) < 80:
                final_style_ok = 2
                style_name = f"'{style_name}' checking against type '{figure_compare['styles']['jacow']}'"

            _id = _fig_to_int(f)
            figure_detail = dict(
                id=_id,
                name=f,
                text=text,
                style=style_name,
                style_ok=final_style_ok,
            )
            figure_detail.update(detail)
            figures_captions.append(figure_detail)

        # find test for wrong versions
        for f in RE_WRONG_TITLES.findall(p.text.strip()):
            figure_compare = FIGURE_DETAILS
            # 55 chars is approx where it changes from 1 line to 2 lines
            text = p.text.strip()
            if len(text) > 55:
                figure_compare = FIGURE_MULTI_DETAILS

            style_ok, detail = check_style(p, figure_compare)
            style_name = p.style.name
            if p.style.name not in ['Figure Caption', 'Caption Multi Line', 'Caption']:
                final_style_ok = 2
            else:
                final_style_ok = style_ok and p.style.name in ['Figure Caption', 'Caption Multi Line', 'Caption']

            if 40 < len(text) < 80:
                final_style_ok = 2
                style_name = f"'{style_name}' checking against type '{figure_compare['styles']['jacow']}'"

            _id = _fig_to_int(f)
            figure_detail = dict(
                id=_id,
                name=f,
                text=text,
                style=style_name,
                style_ok=final_style_ok,
            )
            figure_detail.update(detail)
            wrong_captions.append(figure_detail)

    for p in doc.paragraphs:
        # find references to figures
        for f in iter(f.strip() for f in RE_FIG_IN_TEXT.findall(p.text)):
            if f.endswith('.') and p.text.strip().startswith(f):
                # probably a figure caption with . instead of :
                continue
            figures_refs.append(dict(id=_fig_to_int(f), name=f))

        # find figure captions
        _find_figure_captions(p)

    # search for figure captions in tables
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                for p in c.paragraphs:
                    _find_figure_captions(p)

    figures = OrderedDict()
    # no figure found means there is probably an error with parsing though.
    if len(figures_refs) == 0 and len(figures_captions) == 0 and len(wrong_captions) == 0:
        _last = 0
    else:
        _last = max(
            chain.from_iterable(
                [
                    (fig['id'] for fig in figures_captions),
                    (fig['id'] for fig in wrong_captions),
                    (fig['id'] for fig in figures_refs),
                ]
            )
        )

    for i in range(1, _last + 1):
        caption = [c for c in figures_captions if c['id'] == i]
        wrong = [c for c in wrong_captions if c['id'] == i]
        figures[i] = []
        if caption:
            for c in caption:
                refs = list(f['name'] for f in figures_refs if f['id'] == i)
                figure = {
                    'id': i,
                    'refs': refs,
                    'unique_ok': len(caption) == 1,
                    'found_ok': len(caption) > 0,
                    'caption_ok': len(caption) == 1 and c['name'].endswith(':'),
                    'used_ok': len(refs) > 0
                }
                figure.update(**c)
                figures[i].append(figure)
        elif wrong:
            for c in wrong:
                refs = list(f['name'] for f in figures_refs if f['id'] == i)
                figure = {
                    'id': i,
                    'refs': refs,
                    'unique_ok': len(wrong) == 1,
                    'found_ok': len(wrong) > 0,
                    'caption_ok': False,
                    'used_ok': len(refs) > 0
                }
                figure.update(**c)
                figures[i].append(figure)
        else:
            refs = list(f['name'] for f in figures_refs if f['id'] == i)
            figures[i].append({
                'id': i,
                'refs': refs,
                'unique_ok': len(caption) == 1,
                'found_ok': len(caption) > 0,
                'caption_ok': len(caption) == 1 and c['name'].endswith(':'),
                'used_ok': len(refs) > 0
            })


    return figures
