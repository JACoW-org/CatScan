from pathlib import Path
from docx import Document

from jacowvalidator.test_utils import replace_identifying_text
from jacowvalidator.docutils.references import extract_references
from jacowvalidator.docutils.doc import parse_paragraphs

test_dir = Path(__file__).parent / 'data'


def test_convert_document():
    doc = Document(test_dir / 'jacow_template_a4.docx')
    ref, ref_list = extract_references(doc)
    summary = parse_paragraphs(doc)

    new_doc = Document(test_dir / 'jacow_template_a4.docx')
    replace_identifying_text(new_doc)
    new_ref, new_ref_list = extract_references(new_doc)
    new_summary = parse_paragraphs(new_doc)

    # compare converted to original
    assert len(ref) == len(new_ref), \
        f"Reference in text count of {len(ref)} does not match original of {len(new_ref)}"
    assert len(ref_list) == len(new_ref_list), \
        f"Reference count of {len(ref_list)} does not match original of {len(new_ref_list)}"

    # compare title, author, abstract
    for index, detail in summary.items():
        for i, item in detail.items():
            if i in ['ok', 'message']:
                assert summary[index][i] == new_summary[index][i], f"{index} - {i} in summary does not match"
            if i in ['details']:
                count = 0
                for data in item:
                    for j, datum in data.items():
                        if j.endswith('_ok'):
                            assert summary[index][i][count][j] == new_summary[index][i][count][j], \
                                f"{index} - {i} - {j} in summary does not match"
                    count = count + 1
