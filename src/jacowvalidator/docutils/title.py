from jacowvalidator.docutils.page import get_text, check_title_case
from jacowvalidator.docutils.styles import check_style_detail

STYLES = {
    'normal': {
        'type': 'Paper Title',
        'styles': {
            'jacow': 'JACoW_Paper Title',
            'normal': 'Paper Title',
        },
        'alignment': 'CENTER',
        'font_size': 14.0,
        'space_before': 0.0,
        'space_after': 3.0,
        'bold': True,
        'italic': None,
    }
}
EXTRA_RULES = [
    'Case: Title should contain greater than 70% of CAPITAL Letters, can’t be simple Title Case.',
]
HELP_INFO = 'SCEPaperTitle'


def get_title_details(p):
    title = get_text(p)
    title_detail = {
        'text': title,
        'original_text': p.text,
        'case_ok': check_title_case(title, 0.7),
    }
    return title_detail


def get_title_summary(p):
    style_compare = STYLES['normal']
    details = get_title_details(p)
    details.update(check_style_detail(p, style_compare))
    title_style_ok = p.style.name == style_compare['styles']['jacow']
    details.update({'title_style_ok': title_style_ok, 'style': p.style.name})

    extra_info = ''
    if not details['case_ok']:
        extra_info = '<p class="has-text-weight-bold has-text-danger">Title should be at least 70% uppercase</p>'

    return {
        'details': [details],
        'rules': STYLES,
        'extra_rules': EXTRA_RULES,
        'help_info': HELP_INFO,
        'extra_info': extra_info,
        'title': 'Title',
        'ok': details['style_ok'] and details['case_ok'],
        'message': 'Title issues',
        'anchor': 'title'
    }