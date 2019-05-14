"""For verifying that an uploaded file matches an entry from the spms
   references csv file and if so, verifies that the title and authors match """

import os
import csv
import re
from jacowvalidator.docutils.authors import get_author_list

RE_MULTI_SPACE = re.compile(r' +')


class PaperNotFoundError(Exception):
    """Raised when the paper submitted by a user has no matching entry in the
    spms references list of papers"""
    pass


class ColumnNotFoundError(Exception):
    """Raised when the spms references csv file doesn't have a column this
    function expected"""
    pass


class CSVPathNotDeclared(Exception):
    """Raised when the PATH_TO_JACOW_REFERENCES_CSV environment variable is
    not set"""
    pass


class CSVFileNotFound(Exception):
    """Raised when the file pointed to by the PATH_TO_JACOW_REFERENCES_CSV
    environment variable doesnt exist"""
    pass


# runs conformity checks against the references csv file and returns a dict of
# results, eg: result = { title_match: True, authors_match: False }
def reference_csv_check(filename_minus_ext, title, authors):
    result = {
        'title_match': False, 'authors_match': False,
    }
    if 'PATH_TO_JACOW_REFERENCES_CSV' not in os.environ:
        raise CSVPathNotDeclared("The environment variable "
                                 "PATH_TO_JACOW_REFERENCES_CSV is not "
                                 "set! Unable to locate references.csv file for "
                                 "title checking")
    if not os.path.isfile(os.environ['PATH_TO_JACOW_REFERENCES_CSV']):
        raise CSVFileNotFound(f"No file was found at the location {os.environ['PATH_TO_JACOW_REFERENCES_CSV']}")
    # the encoding value is one that should work for most documents.
    # the encoding for a file can be detected with the command:
    #    ` file -i FILE `
    with open(os.environ['PATH_TO_JACOW_REFERENCES_CSV'], encoding="ISO-8859-1") as f:
        reader = csv.reader(f)
        reading_header_row = True
        match_found = False
        for spms_row in reader:
            if reading_header_row:
                reading_header_row = False
                header = spms_row
                title_col = header.index("title")
                paper_col = header.index("paper")
                authors_col = header.index("authors")
                # confirm those headers existed as expected:
                for heading in ['title_col', 'paper_col', 'authors_col']:
                    # (if they didn't exist, the vars will be undefined)
                    if heading not in locals():
                        raise ColumnNotFoundError(f"could not identify {heading} column in references csv")
            else:
                if filename_minus_ext == spms_row[paper_col]:
                    reference_title = RE_MULTI_SPACE.sub(' ', spms_row[title_col].upper())
                    title_match = title.upper().strip('*') == reference_title
                    report, authors_match = get_author_list_report(authors, spms_row[authors_col])

                    # builds the data for display, match_ok determines the colour of the cell
                    # True for green, False for red, 2 for amber.
                    summary_list = [{
                        'type': 'Author',
                        'match_ok': 2 if result['match'] and not result['exact'] else result['match'],
                        'docx': result['docx'],
                        'spms': result['spms']} for result in report]

                    return {
                        'title': {
                            'match': title_match,
                            'docx': title,
                            'spms': reference_title
                        },
                        'author': {
                            'match': authors_match,
                            'docx': authors,
                            'spms': spms_row[authors_col],
                            'docx_list': get_author_list(authors),
                            'spms_list': get_author_list(spms_row[authors_col]),
                            'report': report
                        },
                        'summary': [{
                            'type': 'Title',
                            'match_ok': title_match,
                            'docx': title,
                            'spms': reference_title
                        }, {
                            'type': 'Extracted Author List',
                            'match_ok': authors_match,
                            'docx': authors,
                            'spms': spms_row[authors_col],
                        }, *summary_list],
                    }

        # if not returned by now its because the paper wasn't found in the list
        if 'SPMS_DEBUG' in os.environ and os.environ['SPMS_DEBUG'] == 'True':
            return {
                'title': {
                    'match': False,
                    'docx': title.upper(),
                    'spms': 'No matching paper found in the spms csv file'
                },
                'author': {
                    'match': False,
                    'docx': authors,
                    'spms': 'No matching paper found in the spms csv file',
                    'docx_list': list(),
                    'spms_list': list(),
                    'report': list()
                },
                'summary': [{
                    'type': 'title',
                    'match': False,
                    'docx': title.upper(),
                    'spms': 'No matching paper found in the spms csv file'
                    }, {
                    'type': 'author',
                    'match': False,
                    'docx': authors,
                    'spms': 'No matching paper found in the spms csv file',
                }],

            }
        else:
            raise PaperNotFoundError("No matching paper found in the spms csv file")


def get_author_list_report(docx_text, spms_text):
    """Compares two lists of authors (one sourced from the uploaded docx file
    and one sourced from the corresponding paper's entry in the SPMS references
    csv file) and produces a dict array report of the form:
        [
            {
            match: True,
            exact: True,
            docx: "Y. Z. Gómez Martínez",
            spms: "Y. Gomez Martinez"
            },
            {
            match: True,
            exact: False,
            docx: "T. X. Therou",
            spms: "T. Therou"
            },
            {
            match: False,
            exact: False,
            docx: "A. Tiller",
            spms: ""
            },
        ]
    """
    extracted_docx_authors = get_author_list(docx_text)
    extracted_spms_authors = get_author_list(spms_text)
    # extracted_docx_authors = ['Y. Z. Gómez Martínez', 'T. X. Therou', 'A. Tiller']
    docx_list = build_comparison_author_objects(extracted_docx_authors)
    spms_list = build_comparison_author_objects(extracted_spms_authors)
    # docx_list = [
    # {
    #   original-value: 'Y. Z. Gómez Martínez',
    #   compare-value: 'Y. Z. Gomez Martinez',
    #   compare-first-last: 'Y. Gomez Martinez',
    #   compare-last: 'Gomez Martinez'
    # }, ... ]

    # create lists needed for matching and sorting:

    spms_matched = list()
    spms_unmatched = list()
    docx_matched = list()
    results = list()

    # perform first round of matching, looking for exact matches:

    all_authors_match = True  # assume they all match until left with unpaired authors
    for spms_author in spms_list[:]:
        docx_author = next((docx_author for docx_author in docx_list if docx_author['compare-value'] == spms_author['compare-value']), None)
        if docx_author:
            docx_matched.append(docx_author)
            docx_list.remove(docx_author)
            spms_matched.append(spms_author)
            spms_list.remove(spms_author)
            results.append({'docx': docx_author['original-value'],
                            'spms': spms_author['original-value'],
                            'exact': True,
                            'match': True})
        else:
            spms_unmatched.append(spms_author)
            spms_list.remove(spms_author)

    # Move remaining authors in docx_list to docx_unmatched:

    docx_unmatched = docx_list

    # if any unmatched authors remain, perform second round of matching, looking for loose matches (missing initials)

    for spms_author in spms_unmatched[:]:
        docx_author = next((docx_author for docx_author in docx_unmatched if docx_author['compare-first-last'] == spms_author['compare-first-last'] or docx_author['compare-transliterated'] == spms_author['compare-transliterated']), None)
        if docx_author:
            docx_matched.append(docx_author)
            docx_unmatched.remove(docx_author)
            spms_matched.append(spms_author)
            spms_unmatched.remove(spms_author)
            results.append({'docx': docx_author['original-value'],
                            'spms': spms_author['original-value'],
                            'exact': False,
                            'match': True})
    # after all matching rounds completed, any authors remaining in the
    # unmatched lists are added to results with a match value of false:

    for spms_author in spms_unmatched:
        results.append({'docx': '',
                        'spms': spms_author['original-value'],
                        'exact': False,
                        'match': False})
        all_authors_match = False

    for docx_author in docx_unmatched:
        results.append({'docx': docx_author['original-value'],
                        'spms': '',
                        'exact': False,
                        'match': False})
        all_authors_match = False

    return results, all_authors_match


def build_comparison_author_objects(author_names):
    author_compare_objects = list()
    for author in author_names:
        original_value = author
        compare_value = normalize_author_name(author)
        compare_first_last = get_first_last_only(compare_value)
        compare_last = get_surname(compare_first_last)
        compare_transliterated = transliterate_accents(compare_first_last)
        author_compare_objects.append(
            {
                'original-value': original_value,
                'compare-value': compare_value,
                'compare-first-last': compare_first_last,
                'compare-transliterated': compare_transliterated,
                'compare-last': compare_last
            })
    return author_compare_objects


def normalize_author_name(author_name):
    """returns a normalized name suitable for comparing"""
    # ensure periods are followed by a space:
    normalized_name = author_name.replace('.', '. ').replace('  ', ' ')
    # remove hyphens (sometimes inconsistently applied):
    normalized_name = normalized_name.replace('-', '')
    # remove asterisks (sometimes included in docx authors text):
    normalized_name = normalized_name.replace('*', '')
    # remove formatting characters occasionally observed:
    normalized_name = normalized_name.replace('†', '')
    # strip possible extra whitespace:
    normalized_name = normalized_name.strip()
    return normalized_name


def get_first_last_only(normalized_author_name):
    """given an author name returns a version with only the first initial
    eg: given 'T. J. Z. Bytes' returns 'T. Bytes' """
    first_intial = normalized_author_name[:2]
    surname = get_surname(normalized_author_name)
    return ' '.join((first_intial, surname))


def get_surname(author_name):
    """finds the index of the last period in the string then returns the substring
    starting 2 positions forward from that period"""
    return author_name[author_name.rfind('.')+2:]


def clone_list(list_to_clone):
    new_list = list()
    for item in list_to_clone:
        new_list.append(item)
    return new_list


def insert_spaces_after_periods(author_list_to_adjust):
    new_list = list()
    for author in author_list_to_adjust:
        fixed_author = author.replace('.', '. ')  # ensure each period is followed by a space
        fixed_author = fixed_author.replace('  ', ' ')  # remove any duplicate spaces that were made
        new_list.append(fixed_author)
    return new_list


def normalize_author_names(author_list_to_clean):
    new_list = list()
    for author in author_list_to_clean:
        new_list.append(normalize_author_name(author))
    return new_list

# below taken from https://stackoverflow.com/questions/6837148/change-foreign-characters-to-their-normal-equivalent
ACCENTED_CHARS_DICT = {'á': 'a', 'Á': 'A', 'à': 'a', 'À': 'A', 'ă': 'a',
                       'Ă': 'A', 'â': 'a', 'Â': 'A', 'å': 'a', 'Å': 'A',
                       'ã': 'a', 'Ã': 'A', 'ą': 'a', 'Ą': 'A', 'ā': 'a',
                       'Ā': 'A', 'ä': 'ae', 'Ä': 'AE', 'æ': 'ae', 'Æ': 'AE',
                       'ḃ': 'b', 'Ḃ': 'B', 'ć': 'c', 'Ć': 'C', 'ĉ': 'c',
                       'Ĉ': 'C', 'č': 'c', 'Č': 'C', 'ċ': 'c', 'Ċ': 'C',
                       'ç': 'c', 'Ç': 'C', 'ď': 'd', 'Ď': 'D', 'ḋ': 'd',
                       'Ḋ': 'D', 'đ': 'd', 'Đ': 'D', 'ð': 'dh', 'Ð': 'Dh',
                       'é': 'e', 'É': 'E', 'è': 'e', 'È': 'E', 'ĕ': 'e',
                       'Ĕ': 'E', 'ê': 'e', 'Ê': 'E', 'ě': 'e', 'Ě': 'E',
                       'ë': 'e', 'Ë': 'E', 'ė': 'e', 'Ė': 'E', 'ę': 'e',
                       'Ę': 'E', 'ē': 'e', 'Ē': 'E', 'ḟ': 'f', 'Ḟ': 'F',
                       'ƒ': 'f', 'Ƒ': 'F', 'ğ': 'g', 'Ğ': 'G', 'ĝ': 'g',
                       'Ĝ': 'G', 'ġ': 'g', 'Ġ': 'G', 'ģ': 'g', 'Ģ': 'G',
                       'ĥ': 'h', 'Ĥ': 'H', 'ħ': 'h', 'Ħ': 'H', 'í': 'i',
                       'Í': 'I', 'ì': 'i', 'Ì': 'I', 'î': 'i', 'Î': 'I',
                       'ï': 'i', 'Ï': 'I', 'ĩ': 'i', 'Ĩ': 'I', 'į': 'i',
                       'Į': 'I', 'ī': 'i', 'Ī': 'I', 'ĵ': 'j', 'Ĵ': 'J',
                       'ķ': 'k', 'Ķ': 'K', 'ĺ': 'l', 'Ĺ': 'L', 'ľ': 'l',
                       'Ľ': 'L', 'ļ': 'l', 'Ļ': 'L', 'ł': 'l', 'Ł': 'L',
                       'ṁ': 'm', 'Ṁ': 'M', 'ń': 'n', 'Ń': 'N', 'ň': 'n',
                       'Ň': 'N', 'ñ': 'n', 'Ñ': 'N', 'ņ': 'n', 'Ņ': 'N',
                       'ó': 'o', 'Ó': 'O', 'ò': 'o', 'Ò': 'O', 'ô': 'o',
                       'Ô': 'O', 'ő': 'o', 'Ő': 'O', 'õ': 'o', 'Õ': 'O',
                       'ø': 'oe', 'Ø': 'OE', 'ō': 'o', 'Ō': 'O', 'ơ': 'o',
                       'Ơ': 'O', 'ö': 'oe', 'Ö': 'OE', 'ṗ': 'p', 'Ṗ': 'P',
                       'ŕ': 'r', 'Ŕ': 'R', 'ř': 'r', 'Ř': 'R', 'ŗ': 'r',
                       'Ŗ': 'R', 'ś': 's', 'Ś': 'S', 'ŝ': 's', 'Ŝ': 'S',
                       'š': 's', 'Š': 'S', 'ṡ': 's', 'Ṡ': 'S', 'ş': 's',
                       'Ş': 'S', 'ș': 's', 'Ș': 'S', 'ß': 'SS', 'ť': 't',
                       'Ť': 'T', 'ṫ': 't', 'Ṫ': 'T', 'ţ': 't', 'Ţ': 'T',
                       'ț': 't', 'Ț': 'T', 'ŧ': 't', 'Ŧ': 'T', 'ú': 'u',
                       'Ú': 'U', 'ù': 'u', 'Ù': 'U', 'ŭ': 'u', 'Ŭ': 'U',
                       'û': 'u', 'Û': 'U', 'ů': 'u', 'Ů': 'U', 'ű': 'u',
                       'Ű': 'U', 'ũ': 'u', 'Ũ': 'U', 'ų': 'u', 'Ų': 'U',
                       'ū': 'u', 'Ū': 'U', 'ư': 'u', 'Ư': 'U', 'ü': 'ue',
                       'Ü': 'UE', 'ẃ': 'w', 'Ẃ': 'W', 'ẁ': 'w', 'Ẁ': 'W',
                       'ŵ': 'w', 'Ŵ': 'W', 'ẅ': 'w', 'Ẅ': 'W', 'ý': 'y',
                       'Ý': 'Y', 'ỳ': 'y', 'Ỳ': 'Y', 'ŷ': 'y', 'Ŷ': 'Y',
                       'ÿ': 'y', 'Ÿ': 'Y', 'ź': 'z', 'Ź': 'Z', 'ž': 'z',
                       'Ž': 'Z', 'ż': 'z', 'Ż': 'Z', 'þ': 'th', 'Þ': 'Th',
                       'µ': 'u', 'а': 'a', 'А': 'a', 'б': 'b', 'Б': 'b',
                       'в': 'v', 'В': 'v', 'г': 'g', 'Г': 'g', 'д': 'd',
                       'Д': 'd', 'е': 'e', 'Е': 'E', 'ё': 'e', 'Ё': 'E',
                       'ж': 'zh', 'Ж': 'zh', 'з': 'z', 'З': 'z', 'и': 'i',
                       'И': 'i', 'й': 'j', 'Й': 'j', 'к': 'k', 'К': 'k',
                       'л': 'l', 'Л': 'l', 'м': 'm', 'М': 'm', 'н': 'n',
                       'Н': 'n', 'о': 'o', 'О': 'o', 'п': 'p', 'П': 'p',
                       'р': 'r', 'Р': 'r', 'с': 's', 'С': 's', 'т': 't',
                       'Т': 't', 'у': 'u', 'У': 'u', 'ф': 'f', 'Ф': 'f',
                       'х': 'h', 'Х': 'h', 'ц': 'c', 'Ц': 'c', 'ч': 'ch',
                       'Ч': 'ch', 'ш': 'sh', 'Ш': 'sh', 'щ': 'sch', 'Щ': 'sch',
                       'ъ': '', 'Ъ': '', 'ы': 'y', 'Ы': 'y', 'ь': '', 'Ь': '',
                       'э': 'e', 'Э': 'e', 'ю': 'ju', 'Ю': 'ju', 'я': 'ja',
                       'Я': 'ja'}


def transliterate_accents(name):
    name_copy = name
    for letter in name:
        if ord(letter) > 127:
            if letter in ACCENTED_CHARS_DICT:
                print('replacing', letter)
                print("with", ACCENTED_CHARS_DICT[letter])
                name_copy = name_copy.replace(letter, ACCENTED_CHARS_DICT[letter])
                print(name_copy)
    return name_copy
