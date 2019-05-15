import os
from jacowvalidator.docutils.styles import check_style_detail, VALID_STYLES, VALID_NON_JACOW_STYLES
from jacowvalidator.docutils.page import get_text, check_title_case
from jacowvalidator.docutils.margins import check_sections
from jacowvalidator.docutils.styles import check_jacow_styles
from jacowvalidator.docutils.references import extract_references
from jacowvalidator.docutils.heading import get_headings
from jacowvalidator.docutils.paragraph import get_paragraphs
from jacowvalidator.docutils.figures import extract_figures
from jacowvalidator.docutils.languages import (get_language_tags, get_language_tags_location, VALID_LANGUAGES)
from jacowvalidator.docutils.tables import check_table_titles
from jacowvalidator.spms import reference_csv_check


class AbstractNotFoundError(Exception):
    """Raised when the paper submitted by a user has no matching entry in the
    spms references list of papers"""
    pass


DETAILS = {
    'Heading': {
        'Section': {
            'type': 'Section Heading',
            'styles': {
                'jacow': 'JACoW_Section Heading',
                'normal': 'Section Heading',
            },
            'alignment': 'CENTER',
            'font_size': 12.0,
            'space_before': 9.0,
            'space_after': 3.0,
            'bold': True,
            'italic': None,
            'case': 'uppercase',
        },
        'Subsection': {
            'type': 'Section Heading',
            'styles': {
                'jacow': 'JACoW_Subsection Heading',
                'normal': 'Subsection Heading',
            },
            'alignment': None,
            'font_size': 12.0,
            'space_before': 6.0,
            'space_after': 3.0,
            'bold': None,
            'italic': True,
            'case': 'initialcaps',
        },
        'Third': {
            'type': 'Section Heading',
            'styles': {
                'jacow': 'JACoW_Third - Level Heading',
                'normal': 'Third - Level Heading',
            },
            'alignment': None,
            'font_size': 10.0,
            'space_before': 6.0,
            'space_after': 0.0,
            'bold': True,
            'italic': None,
            'case': 'initialcaps',
        },
    },
    'Paragraph': {
        'type': 'Body Text Indent',
        'styles': {
            'jacow': 'JACoW_Body Text Indent',
            'normal': 'Body Text Indent',
        },
        'alignment': 'JUSTIFY',
        'font_size': 10.0,
        'space_before': 0.0,
        'space_after': 0.0,
        'first_line_indent': 9.35  # 0.33cm
    },
    'Figure': {
        'SingleLine': {
            'type': 'Figure - Single Line',
            'styles': {
                'jacow': 'Figure Caption',
                'normal': 'Caption',
            },
            'alignment': 'CENTER',
            'font_size': 10.0,
            'space_before': 3.0,
            'space_after': ['>=', 3.0],
            'bold': None,
            'italic': None,
        },
        'MultiLine': {
            'type': 'Figure - Multi Line',
            'styles': {
                'jacow': 'Figure Caption Multi Line',
            },
            'alignment': 'JUSTIFY',
            'font_size': 10.0,
            'space_before': 3.0,
            'space_after': ['>=', 3.0],
            'bold': None,
            'italic': None,
        }
    },
    'Reference': {
        'LessThanNineTotal': {
            'type': 'References when ≤ 9',
            'styles': {
                'jacow': 'JACoW_References when ≤ 9',
            },
            'alignment': 'JUSTIFY',
            'font_size': 9.0,
            'space_before': 0.0,
            'space_after': 3.0,
            'hanging_indent':  0.0,
            'first_line_indent': -14.75,  # 0.52 cm,
        },
        'LessThanNine': {
            'type': 'Reference #1-9 when >= 10 Refs',
            'styles': {
                'jacow': 'JACoW_Reference #1-9 when >= 10 Refs',
            },
            'alignment': 'JUSTIFY',
            'font_size': 9.0,
            'space_before': 0.0,
            'space_after': 3.0,
            'hanging_indent': 0,  # 0.16 cm,
            'first_line_indent': -14.75,  # 0.52 cm,
        },
        'MoreThanNine': {
            'type': 'Reference #10 onwards',
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
    },
    'Table': {
        'SingleLine': {
            'type': 'Table - Single Line',
            'styles': {
                'jacow': 'Table Caption',
            },
            'alignment': 'CENTER',
            'font_size': 10.0,
            'space_before': ['>=', 3.0],
            'space_after': 3.0,
            'bold': None,
            'italic': None,
        },
        'MultiLine': {
            'type': 'Table - Multi Line',
            'styles': {
                'jacow': 'Table Caption Multi Line',
            },
            'alignment': 'JUSTIFY',
            'font_size': 10.0,
            'space_before': ['>=', 3.0],
            'space_after': 3.0,
            'bold': None,
            'italic': None,
        }
    },
    'Title': {
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
    },
    'Authors': {
        'type': 'Author List',
        'styles': {
            'jacow': 'JACoW_Author List',
            'normal': 'Author List',
        },
        'alignment': 'CENTER',
        'font_size': 12.0,
        'space_before': 9.0,
        'space_after': 12.0,
        'bold': None,
        'italic': None,
    },
    'Abstract': {
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
    },
}


def get_title_details(p):
    title = get_text(p)
    title_detail = {
        'text': title,
        'original_text': p.text,
        'case_ok': check_title_case(title, 0.7),
    }
    return title_detail


def get_author_details(p):
    superscript_removed_text = ''  # remove superscript footnotes
    for r in p.runs:
        superscript_removed_text += r.text if not r.font.superscript else ''
    author_detail = {
        'text': superscript_removed_text,
        'original_text': p.text,
    }
    return author_detail


def get_abstract_detail(p):
    abstract_detail = {
        'text': p.text,
        'original_text': p.text,
    }
    return abstract_detail


def parse_all_paragraphs(doc):
    all_paragraphs = []
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip():
            style_ok = p.style.name in VALID_STYLES or p.style.name in VALID_NON_JACOW_STYLES
            if not style_ok:
                style_ok = 2
            all_paragraphs.append({
                'index': i,
                'style': p.style.name,
                'text': get_text(p),
                'style_ok': style_ok,
                'in_table': 'No',
            })

    # search for paragraphs in tables
    count = 1
    show_all = True
    for t in doc.tables:
        if len(t.rows) > 2 and not show_all:
            continue
        for r in t.rows:
            if len(r.cells) > 2 and not show_all:
                continue
            cell_count = 1
            for c in r.cells:
                for p in c.paragraphs:
                    if p.text.strip():
                        style_ok = p.style.name in VALID_STYLES or p.style.name in VALID_NON_JACOW_STYLES
                        if not style_ok:
                            style_ok = 2
                        all_paragraphs.append({
                            'index': 0,
                            'style': p.style.name,
                            'text': get_text(p),
                            'style_ok': style_ok,
                            'in_table': f"Table {count}:<br/>row {r._index + 1}, col {cell_count}"
                        })
                cell_count = cell_count + 1
        count = count + 1
    return all_paragraphs


def parse_paragraphs(doc):
    title_index = abstract_index = reference_index = -1
    title_style_ok = False

    summary = {}
    for i, p in enumerate(doc.paragraphs):
        # first paragraph is the title
        text = p.text.strip()
        if not text:
            continue

        # first non empty paragraph is the title
        # TODO fix since it can go over more than paragraph
        if title_index == -1:
            title_index = i
            details = get_title_details(p)
            details.update(check_style_detail(p, DETAILS['Title']))
            title_style_ok = p.style.name == DETAILS['Title']['styles']['jacow']
            details.update({'title_style_ok': title_style_ok, 'style': p.style.name})
            summary['Title'] = {
                'details': [details],
                'rules': DETAILS['Title'],
                'title': 'Title',
                'ok': details['style_ok'] and details['case_ok'],
                'message': 'Title issues',
                'anchor': 'title'
            }

        # find abstract heading
        if text.lower() == 'abstract':
            abstract_index = i
            details = get_abstract_detail(p)
            details.update(check_style_detail(p, DETAILS['Abstract']))
            title_style_ok = p.style.name == DETAILS['Abstract']['styles']['jacow']
            details.update({'title_style_ok': title_style_ok, 'style': p.style.name})
            summary['Abstract'] = {
                'details': [details],
                'rules': DETAILS['Abstract'],
                'title': 'Abstract Heading',
                'ok': details['style_ok'],
                'message': 'Abstract issues',
                'anchor': 'abstract'
            }

        # all headings, paragraphs captions, figures, tables, equations should be between these two
        # if abstract_index > 0 and reference_index == -1:
        #     print(i)
        #     # check if a known jacow style
        #     for section_type, section_data in DETAILS.items():
        #         if 'styles' in section_data:
        #             if p.style.name in section_data['styles']['jacow']:
        #                 found = f"{section_type} - {p.style.name}"
        #                 print(found)
        #                 break
        #             elif p.style.name in section_data['styles']['normal']:
        #                 found = f"{section_type} -- {p.style.name}"
        #                 print(found)
        #                 break
        #         else:
        #             for sub_type, sub_data in section_data.items():
        #                 if p.style.name in sub_data['styles']['jacow']:
        #                     found = f"{section_type} - {sub_type} - {p.style.name}"
        #                     print(found)
        #                 elif 'normal' in sub_data['styles'] and p.style.name in sub_data['styles']['normal']:
        #                     found = f"{section_type} -- {sub_type} -- {p.style.name}"
        #                     print(found)
        #                     break

        # find reference heading
        if text.lower() == 'references':
            reference_index = i
            break

    # if abstract not found
    if abstract_index == -1:
        raise AbstractNotFoundError("Abstract header not found")

        # abstract_index = 2
        # summary['Abstract'] = {
        #     'details': [],
        #     'rules': DETAILS['Abstract'],
        #     'title': 'Abstract Heading',
        #     'ok': False,
        #     'message': 'Abstract issues',
        #     'anchor': 'abstract'
        # }

    # authors is all the text between title and abstract heading
    author_details = []
    for p in doc.paragraphs[title_index+1: abstract_index]:
        if p.text.strip():
            detail = get_author_details(p)
            detail.update(check_style_detail(p, DETAILS['Authors']))
            title_style_ok = p.style.name == DETAILS['Authors']['styles']['jacow']
            detail.update({'title_style_ok': title_style_ok, 'style': p.style.name})
            author_details.append(detail)

    summary['Authors'] = {
        'details': author_details,
        'rules': DETAILS['Authors'],
        'title': 'Author',
        'ok': all([tick['style_ok'] for tick in author_details]),
        'message': 'Author issues',
        'anchor': 'author'
    }

    return summary


def create_upload_variables(doc, paper_name):
    summary = {}
    doc_summary = parse_paragraphs(doc)

    # get style details
    jacow_styles = check_jacow_styles(doc)
    summary['Styles'] = {
        'title': 'JACoW Styles',
        'ok': all([tick['style_ok'] for tick in jacow_styles]),
        'message': 'Styles issues',
        'details': jacow_styles,
        'anchor': 'styles'
    }

    # get page size and margin details
    sections = check_sections(doc)
    ok = all([tick['margins_ok'] for tick in sections]) and all([tick['col_ok'] for tick in sections])
    summary['Margins'] = {
        'title': 'Page Size and Margins',
        'ok': ok,
        'message': 'Margins',
        'details': sections,
        'anchor': 'pagesize'
    }

    language_summary = get_language_tags(doc)
    languages = get_language_tags_location(doc)
    summary['Languages'] = {
        'title': 'Languages',
        'ok': len([languages[lang] for lang in languages if languages[lang] not in VALID_LANGUAGES]) == 0,
        'message': 'Language issues',
        'details': language_summary,
        'extra': languages,
        'anchor': 'language'
    }

    # get parsed document summary of styles
    all_summary = parse_all_paragraphs(doc)
    ok = all([tick['style_ok'] is True for tick in all_summary])
    if not ok:
        ok = 2
    summary['List'] = {
        'title': 'Parsed Document',
        'ok': ok,
        'message': 'Not using only JACoW Styles',
        'details': all_summary,
        'anchor': 'list',
        'showTotal': True,
    }

    summary['Title'] = doc_summary['Title']
    title = doc_summary['Title']['details'][0]

    summary['Authors'] = doc_summary['Authors']
    authors = doc_summary['Authors']['details']

    summary['Abstract'] = doc_summary['Abstract']
    # summary['Headings'] = doc_summary['Headings']

    headings = get_headings(doc)
    summary['Headings'] = {
        'title': 'Headings',
        'ok': all([tick['style_ok'] is True for tick in headings]),
        'message': 'Heading issues',
        'details': headings,
        'anchor': 'heading',
        'showTotal': True,
    }

    paragraphs = get_paragraphs(doc)
    summary['Paragraphs'] = {
        'title': 'Paragraphs',
        'ok': all([tick['style_ok'] for tick in paragraphs]),
        'message': 'Paragraph issues',
        'details': paragraphs,
        'anchor': 'paragraph',
        'showTotal': True,
    }

    references_in_text, references_list = extract_references(doc)
    # Use checks first
    ok = references_list and all([
            all([tick['text_ok'], tick['used_ok'], tick['order_ok'], tick['unique_ok']])
            for tick in references_list])

    # Check style use checks pass
    if ok:
        for tick in references_list:
            if not tick['style_ok']:
                # If find a false then the result is false
                ok = False
                break
            elif tick['style_ok'] == 2:
                # If find a 2 (?) then result is 2 unless a false is found later
                ok = 2

    summary['References'] = {
        'title': 'References',
        'ok': ok,
        'message': 'Reference issues',
        'details': references_list,
        'anchor': 'references',
        'showTotal': True,
    }

    figures = extract_figures(doc)
    ok = True
    # Use checks first
    for _, sub in figures.items():
        ok = ok and all(
            [item['caption_ok'] and item['unique_ok'] and item['used_ok'] and item['found_ok'] for item in sub]
        )

    # Check style use checks pass
    if ok:
        for _, sub in figures.items():
            # Break out of outer loop too if false
            if not ok:
                break

            for item in sub:
                if not item['style_ok']:
                    # If find a false then the result is false
                    ok = False
                    break
                elif item['style_ok'] == 2:
                    # If find a 2 (?) then result is 2 unless a false is found later
                    ok = 2

    summary['Figures'] = {
        'title': 'Figures',
        'ok': ok,
        'message': 'Figure issues',
        'details': figures,
        'anchor': 'figures',
        'showTotal': True,
    }

    table_titles = check_table_titles(doc)
    # Use checks first
    ok = all([
            all([tick['text_format_ok'], tick['order_ok'], tick['style_ok'], tick['order_ok']])
            for tick in table_titles])

    # Check style use checks pass
    if ok:
        for tick in table_titles:
            if not tick['style_ok']:
                # If find a false then the result is false
                ok = False
                break
            elif tick['style_ok'] == 2:
                # If find a 2 (?) then result is 2 unless a false is found later
                ok = 2

    summary['Tables'] = {
        'title': 'Tables',
        'ok': ok,
        'message': 'Table issues',
        'details': table_titles,
        'anchor': 'tables',
        'showTotal': True,
    }

    return summary, authors, title


def create_spms_variables(paper_name, authors, title):
    summary = {}
    if "URL_TO_JACOW_REFERENCES_CSV" in os.environ:
        reference_csv_url = os.environ["URL_TO_JACOW_REFERENCES_CSV"]
        author_text = ''.join([a['text'] + ", " for a in authors])
        reference_csv_details = reference_csv_check(paper_name, title['text'], author_text)
        summary['SPMS'] = {
            'title': 'SPMS Abstract Title Author Check',
            'ok': reference_csv_details['title']['match'] and reference_csv_details['author']['match'],
            'message': 'SPMS Abstract Title Author Check issues',
            'details': reference_csv_details['summary'],
            'anchor': 'spms'
        }
    else:
        reference_csv_details = False

    return summary, reference_csv_details




