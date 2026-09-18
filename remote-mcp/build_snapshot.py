import json, pathlib, re, hashlib
p=pathlib.Path(__file__).parent
src=(p/'data/source-catalog.json').read_bytes()
r=json.loads((p/'data/catalog-provenance.json').read_text())
c=json.loads(src)
assert len(c['builds'])==c['counts']['builds']
models={m['id']:m['name'] for m in c['models']}
for b in c['builds']:
 assert b['model_id'] in models
 assert re.fullmatch(r'[a-f0-9]{64}',b['sha256'])
 assert b['size_bytes']>0 and re.fullmatch(r'[a-z0-9.+_-]+',b['id'])
 assert b['download_path'].startswith('/downloads/firmware/') and '..' not in b['download_path']
 assert re.fullmatch(r'[a-z0-9-]+',b['route_id'])
 assert b['board_platform']['code'] in ['aml','cv','bb','xil']
out={'snapshot':{'retrieved_at':r['retrieved_at'],'source_url':r['source_url'],'source_sha256':hashlib.sha256(src).hexdigest(),'models':len(models),'builds':len(c['builds']),'scope':'Published catalog metadata. No hardware acceptance or live availability claim.'},'models':c['models'],'builds':c['builds']}
(p/'public/ai/mcp/catalog-snapshot.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
print(out['snapshot'])
