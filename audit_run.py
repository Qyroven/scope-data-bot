"""Independent output audit: hash/locator/content/vector consistency, not factual truth."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

from data_pipeline import tokens, valid_vector
from engine import save_json
from trace import explain


def audit(folder):
    folder=Path(folder).resolve()
    manifest=json.loads((folder/'data/manifest.json').read_text())
    chunks=json.loads((folder/'data/chunks.json').read_text())
    checks=[]
    def check(label, passed): checks.append({'check':label,'pass':bool(passed)})
    check('index hash',hashlib.sha256((folder/'data/index.sqlite').read_bytes()).hexdigest()==manifest['index_sha256'])
    check('unique chunk IDs',len({c['id'] for c in chunks})==len(chunks))
    with sqlite3.connect(f"file:{folder/'data/index.sqlite'}?mode=ro",uri=True) as db:
        rows={ident:(json.loads(metadata),json.loads(vector)) for ident,metadata,vector in db.execute('SELECT * FROM chunks')}
    check('manifest/chunks/index counts',len(rows)==len(chunks)==manifest['chunk_count'])
    for chunk in chunks:
        ident=chunk['id']
        metadata,vector=rows[ident]
        valid_vector(vector,manifest['dimensions'])
        check(ident+' index metadata',metadata==chunk)
        check(ident+' token budget',tokens(chunk['text'])==chunk['tokens'] and chunk['tokens']<=500)
        doc=json.loads((folder/chunk['parsed_path']).read_text())
        loc=chunk['locator']
        prefix=chunk.get('prefix',doc.get('title','')[:300]+'\n')
        body=chunk['text'][len(prefix):]
        check(ident+' prefix',chunk['text'].startswith(prefix))
        if loc.get('field')=='text':
            check(ident+' original text span',body==doc['text'][loc['char_start']:loc['char_end']])
        elif 'page' in loc:
            page=next(p for p in doc['pages'] if p['page']==loc['page'])
            check(ident+' original page span',body==page['text'][loc['char_start']:loc['char_end']])
        elif loc.get('representation')=='row_with_headers':
            row=json.loads(body)
            table=doc['tables'][loc['table']]
            grid=table['grid_cell_indices'][loc['row']]
            check(ident+' row and column positions',row['row']==loc['row'] and len(row['cells'])==len(grid))
            for cell in row['cells']:
                source_index=grid[cell['column']]
                check(ident+' source cell '+str(cell['column']),source_index==cell['cell_index'] and
                      cell['text']==(table['cells'][source_index]['text'] if source_index is not None else None))
        elif 'row' in loc and 'table' not in loc:
            text=json.dumps(doc['rows'][loc['row']],ensure_ascii=False)
            check(ident+' source observation',body==text[loc['char_start']:loc['char_end']])
        else:
            check(ident+' unsupported locator',False)
        back=explain(folder,chunk['trace_id'])
        check(ident+' lineage hashes',all(n['artifact_integrity'] is not False for n in back['backward_trace']))
    result={'status':'pass' if all(c['pass'] for c in checks) else 'fail', 'chunks':len(chunks),
            'checks':checks,'limitations':'Validates preservation and lineage against saved parser output. Does not independently verify source facts, source authority or parser fidelity to rendered PDF/HTML.'}
    save_json(folder/'data/audit.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    args=parser.parse_args()
    result=audit(args.run)
    print(json.dumps({'status':result['status'],'chunks':result['chunks'],'checks':len(result['checks'])}))
    raise SystemExit(0 if result['status']=='pass' else 2)
