import re
from itertools import chain
from jacowvalidator.docutils.styles import check_style

RE_REFS_LIST = re.compile(r'^\[([\d]+)\]')
RE_REFS_LIST_TAB = re.compile(r'^\[([\d]+)\]\t')
RE_REFS_INTEXT = re.compile(r'(?<!^)\[([\d ,-]+)\]')


REFERENCE_DETAILS = {
    'styles': {
        'jacow': 'JACoW_References when ≤ 9',
    },
    'alignment': 'JUSTIFY',
    'font_size': 9.0,
    'space_before': 0.0,
    'space_after': 3.0,
    'hanging_indent':  0.0,
    'first_line_indent': -14.75,  # 0.52 cm,
}

REFERENCE_LESS_DETAILS = {
    'styles': {
        'jacow': 'JACoW_Reference #1-9 when >= 10 Refs',
    },
    'alignment': 'JUSTIFY',
    'font_size': 9.0,
    'space_before': 0.0,
    'space_after': 3.0,
    'hanging_indent': 4.53,  # 0.16 cm,  57600
    'first_line_indent': -14.75,  # 0.52 cm,
}

REFERENCE_MORE_DETAILS = {
    'styles': {
        'jacow': 'JACoW_Reference #10 onwards',
    },
    'alignment': 'JUSTIFY',
    'font_size': 9.0,
    'space_before': 0.0,
    'space_after': 3.0,
    'hanging_indent':  0.0,
    'first_line_indent': -18.7,  # 0.68 cm,
}


def _ref_to_int(ref):
    try:
        return [int(ref)]
    except ValueError:
        if ',' in ref:
            return list(
                chain.from_iterable(_ref_to_int(i) for i in ref.split(',') if i.strip())
            )
        elif '-' in ref:
            return list(range(*(int(v) + i for i, v in enumerate(ref.split('-')))))
        raise


def extract_references(doc, strict_styles=False):
    data = iter(doc.paragraphs)
    references_in_text = []

    # don't start looking until abstract header
    for p in data:
        if p.text.strip().lower() == 'abstract':
            break
    else:
        raise Exception('Abstract header not found')

    # find all references in text and references list
    references_list = []
    ref_list_start = 0
    for i, p in enumerate(data):
        for ref in RE_REFS_INTEXT.findall(p.text):
            references_in_text.append(_ref_to_int(ref))

        refs = RE_REFS_LIST.findall(p.text.strip())
        if refs:
            for ref in refs:
                if int(ref) == 1:
                    ref_list_start = i
                references_list.append(
                    dict(id=int(ref), text=p.text.strip(), style=p.style.name, p=p)
                )
        elif ref_list_start > 0:
            should_find = references_list[-1]['id'] + 1
            if str(should_find) in p.text.strip()[:4]:  # only look in first 4 chars
                references_list.append(
                    dict(
                        id=should_find,
                        text=p.text.strip(),
                        style=p.style.name,
                        p=p,
                        text_ok=False,
                        text_error=f"Number format wrong should be [{should_find}]"
                    )
                )

    # check references in body are in correct order
    stack = [0]
    seen = []
    out_of_order = set()
    for _range in references_in_text:
        for _ref in _range:
            if _ref in stack:
                continue
            if _ref - stack[-1] == 1:
                stack.append(_ref)
            elif _ref not in seen:
                seen.append(_ref)
        for _ref in seen.copy():
            if _ref - stack[-1] == 1:
                stack.append(_ref)
                seen.remove(_ref)
        if len(seen) > 0:
            out_of_order.update(seen)

    # get a set of references so we know which ones are used
    used_references = set(chain.from_iterable(references_in_text))

    # check reference styles, order etc
    ref_count = len(references_list)
    seen = set()
    for i, ref in enumerate(references_list, 1):
        if ref['id'] in seen:
            ref['duplicate'] = True
            ref['unique_ok'] = False
        else:
            ref['unique_ok'] = True
        seen.add(ref['id'])
        ref['order_ok'] = i == ref['id'] and i not in out_of_order
        ref['used_ok'] = i in used_references
        ref['text_ok'] = True

        if not RE_REFS_LIST_TAB.search(ref['text']):
            ref['text_error'] = f"Number format error should be [{i}] followed by a tab"
            ref['text_ok'] = False

        if ref_count <= 9:
            style_ok, detail = check_style(ref['p'], REFERENCE_DETAILS)
            if strict_styles:
                ref['style_ok'] = ref['style'] == 'JACoW_Reference when <= 9 Refs'
                if not ref['style_ok']:
                    ref['style'] = f"{ref['style']} should be 'JACoW_Reference when <= 9 Refs'"
            else:
                ref['style_ok'] = style_ok
        else:
            if i <= 9:
                style_ok, detail = check_style(ref['p'], REFERENCE_LESS_DETAILS)
                if strict_styles:
                    ref['style_ok'] = ref['style'] == 'JACoW_Reference #1-9 when >= 10 Refs'
                    if not ref['style_ok']:
                        ref['style'] = f"{ref['style']} should be 'JACoW_Reference #1-9 when >= 10 Refs'"
                else:
                    ref['style_ok'] = style_ok

            else:
                style_ok, detail = check_style(ref['p'], REFERENCE_MORE_DETAILS)
                if strict_styles:
                    ref['style_ok'] = ref['style'] == 'JACoW_Reference #10 onwards'
                    if not ref['style_ok']:
                        ref['style'] = f"{ref['style']} should be 'JACoW_Reference #10 onwards'"
                else:
                    ref['style_ok'] = style_ok
        ref.update(detail)

    return references_in_text, references_list
