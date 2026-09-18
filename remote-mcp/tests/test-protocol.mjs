import fs from 'node:fs';
import http from 'node:http';
import assert from 'node:assert/strict';
import {PHP,loadPHPRuntime} from '@php-wasm/universal';
import {getPHPLoaderModule} from '@php-wasm/node-8-4';
import {Client} from '@modelcontextprotocol/sdk/client/index.js';
import {StreamableHTTPClientTransport} from '@modelcontextprotocol/sdk/client/streamableHttp.js';
const php=new PHP(await loadPHPRuntime(await getPHPLoaderModule()));
php.mkdir('/mcp');
for(const f of ['index.php','catalog-snapshot.json']) php.writeFile('/mcp/'+f,fs.readFileSync(new URL('../public/ai/mcp/'+f,import.meta.url)));
const checks=[];
const meta={'io.modelcontextprotocol/protocolVersion':'2026-07-28','io.modelcontextprotocol/clientInfo':{name:'protocol-harness',version:'1'},'io.modelcontextprotocol/clientCapabilities':{}};
function request(method,params={},modern=true){return {jsonrpc:'2.0',id:1,method,params:modern?{...params,_meta:meta}:params};}
async function run(name,req,{method='POST',headers={},status=200,check=()=>{},raw}={}){
 const h={'content-type':'application/json','accept':'application/json, text/event-stream',...headers};
 if(req?.params?._meta){h['mcp-protocol-version']??=req.params._meta['io.modelcontextprotocol/protocolVersion'];h['mcp-method']??=req.method;if(req.params.name||req.params.uri)h['mcp-name']??=req.params.name||req.params.uri;}
 const r=await php.run({scriptPath:'/mcp/index.php',method,headers:h,body:Buffer.from(raw??JSON.stringify(req))});
 assert.equal(r.errors,'',`${name}: PHP error`);assert.equal(r.httpStatusCode,status,`${name}: status ${r.text}`);
 const d=r.text?JSON.parse(r.text):null;check(d,r);checks.push({name,passed:true,status:r.httpStatusCode});return d;
}
await run('modern discovery',request('server/discover'),{check:d=>assert(d.result.supportedVersions.includes('2026-07-28'))});
await run('legacy initialize',request('initialize',{protocolVersion:'2025-11-25',clientInfo:{name:'harness',version:'1'},capabilities:{}},false),{check:d=>assert.equal(d.result.protocolVersion,'2025-11-25')});
await run('legacy initialized', {jsonrpc:'2.0',method:'notifications/initialized'},{status:202});
await run('modern tools schema',request('tools/list'),{check:d=>{assert.equal(d.result.tools.length,3);assert(d.result.tools.every(t=>t.annotations.readOnlyHint && !t.annotations.destructiveHint && !t.annotations.openWorldHint));}});
await run('exact catalog case',request('tools/call',{name:'lookup_firmware',arguments:{model_id:'s19j-xp',board_platform:'cv',version:'1.3.5'}}),{check:d=>{const x=d.result.structuredContent;assert.equal(x.status,'exact_record');assert.equal(x.records[0].sha256,'58d2b534595532214f19676f9eba6cd3ac1a9e59ede5eb519a3a8d2129f04dc3');assert.equal(x.records[0].size_bytes,12365068);}});
await run('ambiguity preserved',request('tools/call',{name:'lookup_firmware',arguments:{model_id:'s19j-xp'}}),{check:d=>assert.equal(d.result.structuredContent.record_count,6)});
await run('unknown model has no guessed match',request('tools/call',{name:'lookup_firmware',arguments:{model_id:'s19j-xp-made-up'}}),{check:d=>assert.equal(d.result.structuredContent.status,'model_not_found')});
await run('Russian ninja reference',request('tools/call',{name:'find_ninja_reference',arguments:{topic:'identify-control-board',language:'ru'}}),{check:d=>assert.equal(d.result.structuredContent.url,'https://vnish.ninja/ru/kb/control-board-identification/')});
const a={hashrate_th_s:115,power_w:3150,dev_fee_percent:2,hashprice_usd_per_th_day:.05,electricity_usd_per_kwh:.06};
await run('economic scenario A',request('tools/call',{name:'calculate_roi_scenario',arguments:a}),{check:d=>assert.equal(d.result.structuredContent.results.contribution_usd_day,1.099)});
await run('scenario uptime scales both terms',request('tools/call',{name:'calculate_roi_scenario',arguments:{...a,operating_hours_per_day:12}}),{check:d=>assert.equal(d.result.structuredContent.results.contribution_usd_day,.5495)});
await run('zero uptime',request('tools/call',{name:'calculate_roi_scenario',arguments:{...a,operating_hours_per_day:0}}),{check:d=>assert.equal(d.result.structuredContent.results.contribution_usd_day,0)});
await run('negative scenario retained',request('tools/call',{name:'calculate_roi_scenario',arguments:{...a,electricity_usd_per_kwh:.12}}),{check:d=>assert(d.result.structuredContent.results.contribution_usd_day<0)});
await run('negative value rejected',request('tools/call',{name:'calculate_roi_scenario',arguments:{...a,power_w:-1}}),{check:d=>assert(d.result.isError)});
await run('boolean value rejected',request('tools/call',{name:'calculate_roi_scenario',arguments:{...a,power_w:true}}),{check:d=>assert(d.result.isError)});
await run('unknown input rejected',request('tools/call',{name:'lookup_firmware',arguments:{model_id:'s19j-xp',url:'http://127.0.0.1/'}}),{check:d=>assert(d.result.isError)});
await run('oversized input rejected',request('tools/call',{name:'lookup_firmware',arguments:{model_id:'a'.repeat(65)}}),{check:d=>assert(d.result.isError)});
await run('unknown method',request('system/exec'),{status:404,check:d=>assert.equal(d.error.code,-32601)});
await run('unknown tool',request('tools/call',{name:'flash_firmware',arguments:{}}),{status:400,check:d=>assert.equal(d.error.code,-32602)});
await run('resource index',request('resources/read',{uri:'https://vnish.global/ai/mcp/model-index'}),{check:d=>assert.equal(JSON.parse(d.result.contents[0].text).models.length,47)});
await run('resource URI allowlist',request('resources/read',{uri:'file:///etc/passwd'}),{status:400,check:d=>assert.equal(d.error.code,-32602)});
await run('invalid Origin',request('ping'),{headers:{origin:'https://vnish.global.evil.example'},status:403});
await run('null Origin',request('ping'),{headers:{origin:'null'},status:403});
await run('allowed Origin',request('ping'),{headers:{origin:'https://claude.ai'}});
await run('GET rejected',null,{method:'GET',status:405});
await run('DELETE rejected',null,{method:'DELETE',status:405});
await run('preflight',null,{method:'OPTIONS',headers:{origin:'https://chatgpt.com'},status:204});
await run('wrong content-type',request('ping'),{headers:{'content-type':'text/plain'},status:415});
await run('HTML Accept rejected',request('ping'),{headers:{accept:'text/html'},status:406});
await run('oversized request',null,{raw:' '.repeat(32769),status:413});
await run('malformed JSON',null,{raw:'{',status:400,check:d=>assert.equal(d.error.code,-32700)});
await run('batch rejected',null,{raw:'[]',status:400,check:d=>assert.equal(d.error.code,-32600)});
await run('null id rejected',{...request('ping'),id:null},{status:400});
await run('fractional id rejected',{...request('ping'),id:1.5},{status:400,check:d=>{assert.equal(d.error.code,-32600);assert(!('id' in d));}});
await run('overflow id rejected before rounding',request('ping'),{raw:JSON.stringify(request('ping')).replace('"id":1','"id":9223372036854775809'),status:400,check:d=>{assert.equal(d.error.code,-32600);assert(!('id' in d));}});
await run('unsafe integer id rejected',request('ping'),{raw:JSON.stringify(request('ping')).replace('"id":1','"id":9007199254740992'),status:400,check:d=>assert.equal(d.error.code,-32600)});
await run('maximum safe integer id preserved',{...request('ping'),id:Number.MAX_SAFE_INTEGER},{check:d=>assert.equal(d.id,Number.MAX_SAFE_INTEGER)});
await run('negative safe integer id preserved',{...request('ping'),id:-Number.MAX_SAFE_INTEGER},{check:d=>assert.equal(d.id,-Number.MAX_SAFE_INTEGER)});
await run('zero id preserved',{...request('ping'),id:0},{check:d=>assert.equal(d.id,0)});
await run('string id preserved',{...request('ping'),id:'9223372036854775809'},{check:d=>assert.equal(d.id,'9223372036854775809')});
await run('integral JSON number preserved',request('ping'),{raw:JSON.stringify(request('ping')).replace('"id":1','"id":1.0'),check:d=>assert.equal(d.id,1)});

await run('metadata capabilities required',{jsonrpc:'2.0',id:1,method:'ping',params:{_meta:{'io.modelcontextprotocol/protocolVersion':'2026-07-28'}}},{status:400,check:d=>assert.equal(d.error.code,-32602)});
await run('header method mismatch',request('ping'),{headers:{'mcp-method':'tools/call'},status:400,check:d=>assert.equal(d.error.code,-32020)});
await run('header name mismatch',request('tools/call',{name:'lookup_firmware',arguments:{model_id:'s19j-xp'}}),{headers:{'mcp-name':'bad'},status:400,check:d=>assert.equal(d.error.code,-32020)});
await run('encoded header accepted',request('tools/call',{name:'lookup_firmware',arguments:{model_id:'s19j-xp'}}),{headers:{'mcp-name':'=?base64?'+Buffer.from('lookup_firmware').toString('base64')+'?='}});
await run('unsupported version',request('ping'),{headers:{'mcp-protocol-version':'1999-01-01'},status:400,check:d=>assert.equal(d.error.code,-32020)});
await run('unsupported modern version',{...request('ping'),params:{_meta:{...meta,'io.modelcontextprotocol/protocolVersion':'2099-01-01'}}},{status:400,check:d=>{assert.equal(d.error.code,-32022);assert(d.error.data.supported.includes('2026-07-28'));}});
let queue=Promise.resolve();
const server=http.createServer(async(req,res)=>{
 const chunks=[];for await(const c of req)chunks.push(c);
 const call=async()=>{
  const h=Object.fromEntries(Object.entries(req.headers).filter(([k,v])=>typeof v==='string'));
  const r=await php.run({scriptPath:'/mcp/index.php',method:req.method,headers:h,body:Buffer.concat(chunks)});
  res.writeHead(r.httpStatusCode,Object.fromEntries(Object.entries(r.headers).filter(([k])=>!['transfer-encoding','content-length'].includes(k.toLowerCase())).map(([k,v])=>[k,v])));res.end(r.bytes);
 };
 queue=queue.then(call,call);
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const client=new Client({name:'official-sdk-test',version:'1.0'},{capabilities:{}});
try{
 await client.connect(new StreamableHTTPClientTransport(new URL(`http://127.0.0.1:${server.address().port}/mcp`)));
 const tools=await client.listTools();assert.equal(tools.tools.length,3);
 const result=await client.callTool({name:'lookup_firmware',arguments:{model_id:'s19j-xp',board_platform:'cv',version:'1.3.5'}});assert.equal(result.structuredContent.status,'exact_record');
 const resources=await client.listResources();assert.equal(resources.resources.length,3);
 const method=await client.readResource({uri:'https://vnish.global/ai/mcp/scenario-method'});assert(JSON.parse(method.contents[0].text).formula);
 checks.push({name:'official SDK 1.30.0 StreamableHTTPClientTransport initialize/list/call/resources',passed:true});
}finally{await client.close();await new Promise(resolve=>server.close(resolve));php.exit();}
const receipt={tested_at:new Date().toISOString(),runtime:'PHP 8.4 via @php-wasm 3.1.54',endpoint_sha256:(await import('node:crypto')).createHash('sha256').update(fs.readFileSync(new URL('../public/ai/mcp/index.php',import.meta.url))).digest('hex'),passed:checks.length,checks};
fs.mkdirSync(new URL('../test-results/',import.meta.url),{recursive:true});
fs.writeFileSync(new URL('../test-results/protocol-tests.json',import.meta.url),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({passed:receipt.passed,official_sdk:'passed'}));
