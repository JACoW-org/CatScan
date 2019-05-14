from pathlib import Path

from jacowvalidator.docutils.references import extract_references


test_dir = Path(__file__).parent / 'data'


def test_references():
    from docx import Document
    doc = Document(test_dir / 'test1.docx')

    # hard code known issues for the moment
    type_of_checks = ['used_ok', 'order_ok', 'style_ok']
    issues = {
        1: ['style_ok'],
        2: ['style_ok'],
        3: ['style_ok'],
        4: ['style_ok'],
        5: ['style_ok'],
        6: ['style_ok'],
        7: ['style_ok'],
        8: ['style_ok'],
        9: ['style_ok'],
        10: ['style_ok'],
        11: ['style_ok'],
        12: ['order_ok', 'style_ok'],
        13: ['style_ok'],
        14: ['style_ok'],
        15: ['style_ok'],
        16: ['style_ok'],
        17: ['style_ok'],
        18: ['style_ok'],
        19: ['used_ok', 'style_ok'],
        20: ['order_ok', 'style_ok'],
        21: ['order_ok', 'style_ok'],
        22: ['order_ok', 'style_ok'],
        23: ['order_ok', 'style_ok'],
        24: ['order_ok', 'style_ok'],
        25: ['order_ok', 'style_ok'],
        26: ['order_ok', 'style_ok'],
        27: ['order_ok', 'style_ok'],
        28: ['order_ok', 'style_ok'],
        29: ['order_ok', 'style_ok'],
        30: ['order_ok', 'style_ok'],
        31: ['order_ok', 'style_ok'],
        32: ['order_ok', 'style_ok'],
        33: ['order_ok', 'style_ok'],
        34: ['order_ok', 'style_ok'],
        35: ['order_ok', 'style_ok'],
        36: ['order_ok', 'style_ok'],
        37: ['order_ok', 'style_ok'],
        38: ['order_ok', 'style_ok'],
        39: ['order_ok', 'style_ok'],
        40: ['order_ok', 'style_ok'],
        41: ['order_ok', 'style_ok'],
        42: ['order_ok', 'style_ok'],
        43: ['order_ok', 'style_ok'],
        44: ['order_ok', 'style_ok'],
        45: ['order_ok', 'style_ok'],
    }

    references_in_text, references_list = extract_references(doc)
    assert len(references_list) == 45

    for item in references_list:
        # TODO optimise this
        for check in type_of_checks:
            if check in issues[item['id']]:
                assert item[check] is False, f"{item['id']} {check} check passes but it should fail"
            else:
                assert item[check], f"{item['id']} {check} check failed"
