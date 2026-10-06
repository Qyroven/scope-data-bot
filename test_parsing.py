import json
import tempfile
import unittest
from pathlib import Path

from bot import ValidationError, expand_worldbank_catalog, extract_document, plan_scope
from parsing import html_tables
from trace import TraceStore, explain


class TableTests(unittest.TestCase):
    def test_merged_cells_keep_headers_caption_empty_cell_and_exact_money(self):
        source = '''<html><body><h2>Dân số (người)</h2><table><caption>Bảng 1</caption>
          <tr><th rowspan="2">Năm</th><th colspan="2">Việt Nam</th></tr>
          <tr><th>Dân số</th><th>Ghi chú</th></tr>
          <tr><td>2024</td><td>100.987.686</td><td></td></tr></table></body></html>'''
        table = html_tables(source)[0]
        self.assertEqual(table['caption'], 'Bảng 1')
        self.assertEqual(table['section'], 'Dân số (người)')
        self.assertEqual(table['grid_cell_indices'], [[0, 1, 1], [0, 2, 3], [4, 5, 6]])
        self.assertEqual(table['cells'][5]['text'], '100.987.686')
        self.assertEqual(table['cells'][6]['text'], '')
        self.assertEqual(table['cells'][5]['locator'], '/html/body/table/tr[3]/td[2]')

    def test_navigation_and_script_do_not_enter_tables(self):
        source = '<html><body><nav><table><tr><td>menu</td></tr></table></nav><table><tr><td>42<script>malicious</script></td></tr></table></body></html>'
        tables = html_tables(source)
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0]['cells'][0]['text'], '42')

    def test_invalid_or_overlapping_spans_fail_without_silent_repair(self):
        for source in [
            '<table><tr><td rowspan="4">x</td></tr></table>',
            '<table><tr><td colspan="101">x</td></tr></table>',
            '<table><tr><td>x</td><td rowspan="2">y</td></tr><tr><td colspan="2">z</td></tr></table>',
        ]:
            with self.subTest(source=source), self.assertRaises(ValidationError):
                html_tables(source)

    def test_html_document_retains_structured_table_and_source_locator(self):
        source = '<html><head><title>Dân số Việt Nam</title></head><body><article><h1>Dân số Việt Nam</h1><p>' + ('Số liệu dân số Việt Nam được công bố theo năm, đơn vị người. ' * 5) + '</p><table><tr><th>Năm</th><th>Dân số (người)</th></tr><tr><td>2024</td><td>100987686</td></tr></table></article></body></html>'
        doc = extract_document(source.encode(), 'text/html', 'utf-8', 'https://example.org/population')
        self.assertEqual(doc['tables'][0]['cells'][3]['text'], '100987686')
        self.assertIn('/td[2]', doc['tables'][0]['cells'][3]['locator'])

    def test_short_table_is_retained_without_requiring_long_prose(self):
        source = b'<html><body><table><tr><th>Year</th><th>Population</th></tr><tr><td>2024</td><td>100987686</td></tr></table></body></html>'
        doc = extract_document(source, 'text/html', 'utf-8', 'https://example.org/table')
        self.assertEqual(doc['tables'][0]['cells'][3]['text'], '100987686')

    def test_csv_bom_does_not_corrupt_header_or_numeric_string(self):
        source = '\ufeffyear,amount\n2024,9999999999999999.0001\n'
        doc = extract_document(source.encode(), 'text/csv', 'utf-8', 'https://example.org/table.csv')
        self.assertEqual(doc['table'][0][0], 'year')
        self.assertEqual(doc['table'][1][1], '9999999999999999.0001')


class CatalogTests(unittest.TestCase):
    def expand(self, folder, items, meta=None, topic='Dân số Việt Nam 2020–2024'):
        trace = TraceStore(folder)
        origin = trace.node('search', 'Actual search evidence', parents=[])
        candidates = [{'url': 'https://datacatalog.worldbank.org/search/dataset/0037655',
                       'search_queries': ['Vietnam population data'], 'lineage_ids': [origin['id']]}]
        class HTTP:
            pass
        http = HTTP()
        http.trace = trace
        body = json.dumps([meta or {'page': 1, 'pages': 1, 'total': len(items)}, items]).encode()
        def fetch(url, kind):
            (folder / 'catalog.json').write_bytes(body)
            artifact = trace.artifact('catalog.json', parents=[origin['id']], stage='crawl')
            return body, {'raw_path': 'catalog.json', 'trace_id': artifact['id']}
        http.fetch = fetch
        expand_worldbank_catalog(http, plan_scope(topic), candidates)
        return candidates, trace

    def test_catalog_selects_total_instead_of_growth_and_retains_origin(self):
        items = [{'id': 'growth', 'name': 'Population growth (annual %)', 'source': {'id': '2'}},
                 {'id': 'total', 'name': 'Population, total', 'source': {'id': '2'}}]
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            candidates, trace = self.expand(folder, items)
            self.assertEqual(candidates[-1]['url'], 'https://data.worldbank.org/indicator/total?locations=VN')
            trace.save()
            result = explain(folder, candidates[-1]['lineage_ids'][0])
            self.assertIn('search', {n['stage'] for n in result['backward_trace']})

    def test_ambiguous_and_incomplete_catalog_never_emits_dataset_candidate(self):
        item = {'id': 'total', 'name': 'Population, total', 'source': {'id': '2'}}
        for items, meta in [([item, item], None), ([item], {'pages': 2, 'total': 5})]:
            with tempfile.TemporaryDirectory() as directory:
                candidates, trace = self.expand(Path(directory), items, meta)
                self.assertEqual(len(candidates), 1)
                self.assertTrue(trace.issues)
                self.assertIn('catalog_error', candidates[0])

    def test_changed_scope_selects_life_expectancy_without_changing_code(self):
        items = [{'id': 'life', 'name': 'Life expectancy at birth, total (years)', 'source': {'id': '2'}}]
        with tempfile.TemporaryDirectory() as directory:
            candidates, _ = self.expand(Path(directory), items, topic='Tuổi thọ Việt Nam 2020–2024')
            self.assertEqual(candidates[-1]['url'], 'https://data.worldbank.org/indicator/life?locations=VN')
