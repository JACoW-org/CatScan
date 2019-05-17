from jacowvalidator.docutils.styles import check_style_detail

STYLES = {
    'normal': {
        'type': 'Abstract Heading',
        'styles': {
            'jacow': 'JACoW_Abstract_Heading',
            'normal': 'Abstract_Heading',
        },
        'alignment': None,
        'font_size': 12.0,
        'space_before': 0.0,
        'space_after': 3.0,
        'bold': None,
        'italic': True,
    }
}
EXTRA_RULES = [
    "Text must be <b>Abstract</b>",
]
HELP_INFO = 'SCEAbsract'


def get_abstract_detail(p):
    abstract_detail = {
        'text': p.text,
        'original_text': p.text,
    }
    return abstract_detail


def get_abstract_summary(p):
    style_compare = STYLES['normal']
    details = get_abstract_detail(p)
    details.update(check_style_detail(p, style_compare))
    title_style_ok = p.style.name == style_compare['styles']['jacow']
    details.update({'title_style_ok': title_style_ok, 'style': p.style.name})

    return {
        'details': [details],
        'rules': STYLES,
        'extra_rules': EXTRA_RULES,
        'help_info': HELP_INFO,
        'title': 'Abstract Heading',
        'ok': details['style_ok'],
        'message': 'Abstract issues',
        'anchor': 'abstract'
    }
