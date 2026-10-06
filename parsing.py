"""Local HTML table extraction. Cell strings and original locations stay intact."""
from lxml import html

from engine import ValidationError


def html_tables(document):
    tree = html.fromstring(document)
    for element in tree.xpath('//script|//style|//noscript'):
        element.drop_tree()
    tables = tree.xpath('//table[not(ancestor::table or ancestor::nav or ancestor::footer or ancestor::aside)]')
    if len(tables) > 100:
        raise ValidationError("HTML quá 100 bảng")
    result = []
    for table in tables:
        path = tree.getroottree().getpath(table)
        rows = table.xpath('./tr|./thead/tr|./tbody/tr|./tfoot/tr')
        cells, grid, occupied = [], [], {}
        if len(rows) > 1000:
            raise ValidationError("HTML table quá 1000 hàng")
        for row_index, row in enumerate(rows):
            column = 0
            for element in row.xpath('./th|./td'):
                while (row_index, column) in occupied:
                    column += 1
                try:
                    rowspan = int(element.get('rowspan', '1'))
                    colspan = int(element.get('colspan', '1'))
                except ValueError as error:
                    raise ValidationError("HTML table span không phải số nguyên") from error
                if rowspan == 0:  # HTML: span through the remaining rows of this group.
                    group_rows = element.getparent().getparent().xpath('./tr')
                    group_position = group_rows.index(row) if row in group_rows else row_index
                    rowspan = len(group_rows) - group_position if group_rows else len(rows) - row_index
                if not 1 <= rowspan <= 100 or not 1 <= colspan <= 100 or column + colspan > 100:
                    raise ValidationError("HTML table span/cột vượt giới hạn")
                if row_index + rowspan > len(rows):
                    raise ValidationError("HTML table rowspan vượt số hàng")
                text = ' '.join(element.text_content().split())
                index = len(cells)
                if index >= 10000:
                    raise ValidationError("HTML table quá 10000 ô")
                cells.append({'row': row_index, 'column': column, 'text': text,
                              'rowspan': rowspan, 'colspan': colspan, 'header': element.tag == 'th',
                              'locator': tree.getroottree().getpath(element)})
                for r in range(row_index, row_index + rowspan):
                    for c in range(column, column + colspan):
                        if (r, c) in occupied:
                            raise ValidationError("HTML table ô gộp chồng nhau")
                        occupied[r, c] = index
                column += colspan
        width = max((c for _, c in occupied), default=-1) + 1
        if not cells:
            continue
        for r in range(len(rows)):
            grid.append([occupied.get((r, c)) for c in range(width)])
        headings = table.xpath('preceding::*[self::h1 or self::h2 or self::h3]')
        caption = ' '.join(' '.join(table.xpath('./caption//text()')).split())
        result.append({'caption': caption,
                       'section': ' '.join(headings[-1].text_content().split()) if headings else '',
                       'locator': path, 'cells': cells, 'grid_cell_indices': grid,
                       'row_count': len(rows), 'column_count': width,
                       'status': 'extracted_structure_not_verified'})
    return result
