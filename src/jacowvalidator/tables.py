import re
from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, _Row, Table
from docx.text.paragraph import Paragraph


def iter_block_items(parent):
    """
    Generate a reference to each paragraph and table child within *parent*,
    in document order. Each returned value is an instance of either Table or
    Paragraph. *parent* would most commonly be a reference to a main
    Document object, but also works for a _Cell object, which itself can
    contain paragraphs and tables.
    """
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    elif isinstance(parent, _Row):
        parent_elm = parent._tr
    else:
        raise ValueError("something's not right")
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


# Table captions are actually titles, this means that they are in Title Case, and don’t have a “.”
# At the end, well unless exceeds 2 lines.  The table caption is centred if 1 line (“Table Caption” Style),
# and Justified if 2 or more (“Table Caption Multi Line” Style.  The table caption must appear above the Table.
#
# All tables must be numbered in the order they appear in the document and not skip a number in the sequence.
#
# All tables start with “Table n:”.
# All tables must be referred to in the main text and use “Table n”.
def check_table_titles(doc):
    prev = None
    table_details = []
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            prev = block
        elif isinstance(block, Table):
            # exclude those with only 1 column, since not likely to be real tables.
            if len(block.columns) == 1:
                continue

            # check whether there is data in table
            text_found = False
            for row in block.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if paragraph.text.strip() is not '':
                            text_found = True
                            break

            if text_found:
                table_details.append({'table': block, 'title': prev})

    refs = []
    for paragraph in doc.paragraphs:
        if paragraph.style.name not in ['Caption', 'Table Caption', 'Table Caption Multi Line']:
            # Check for table names
            result = re.findall(r'Table \d', paragraph.text)
            if result is not None:
                for f in result:
                    refs.append(f)

    titles = []
    count = 1
    for table in table_details:
        title = table['title']
        format_check_1 = re.search(r'^Table \d:', title.text.strip()) is not None
        format_check_2 = re.search(r'\.$', title.text.strip()) is None

        # allow whitespace between the number and : for the order check
        order_regex = r"^Table " + re.escape(str(count)) + r"\s*:"
        order_check = re.search(order_regex, title.text.strip()) is not None

        used_check = refs.count('Table ' + str(count))

        titles.append({
            'id': count,
            'text': title.text,
            'text_format_ok': format_check_1 and format_check_2,
            'used': used_check,
            'order_ok': order_check,
            'style': title.style.name,
            'style_ok': title.style.name in ['Caption', 'Table Caption', 'Table Caption Multi Line'],
            'table': f"rows: {len(table['table'].rows)}, columns: {len(table['table'].columns)}"
        })
        count = count+1

    return titles