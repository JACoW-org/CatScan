from flask import Blueprint
import json

blueprint = Blueprint('filters', __name__)


@blueprint.app_template_filter('tick_cross')
def tick_cross(s):
    if s == 1 or s is True:
        return '<span class="background-dark-tick">✓</span>'
    elif s == 2:
        return '<span class="background-dark-question"><i class="fas fa-question"></i></span>'
    else:
        return '<span class="background-dark-cross">✗</span>'


@blueprint.app_template_filter('pastel_background_style')
def pastel_background_style(s):
    if s == 1 or s is True:
        return 'background-jacow-tick'
    elif s == 2:
        return 'background-jacow-question'
    else:
        return "background-jacow-cross"


@blueprint.app_template_filter('display_report')
def display_report(s):
    report = json.loads(s)
    return report


@blueprint.app_template_filter('first_value_in_dict')
def first_value_in_dict(s):
    return [value for index, value in s.items()][0]
