<?php
declare(strict_types=1);
/* VNISH Global public-data MCP. No credentials, device access, writes, or network fetches. */
const VG_VERSION = '1.0.0';
const VG_PROTOCOLS = ['2026-07-28', '2025-11-25', '2025-06-18', '2025-03-26'];
const VG_MAX_BODY = 32768;
const VG_ORIGINS = ['https://vnish.global', 'https://vnish.ninja', 'https://roiasic.com', 'https://chatgpt.com', 'https://claude.ai'];

function vg_info(): array {
    return ['name'=>'vnish-global-operator', 'title'=>'VNISH Global Operator', 'version'=>VG_VERSION,
        'websiteUrl'=>'https://vnish.global/ai/connect/'];
}
function vg_error(int $status, int $code, string $message, $id = null, ?array $data = null): void {
    http_response_code($status);
    $out = ['jsonrpc'=>'2.0', 'error'=>['code'=>$code,'message'=>$message]];
    if ($id !== null) $out['id'] = $id;
    if ($data !== null) $out['error']['data'] = $data;
    echo json_encode($out, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    exit;
}
function vg_result($id, array $result, string $protocol): void {
    if ($protocol === '2026-07-28') {
        $result['resultType'] = 'complete';
        $result['_meta'] = ['io.modelcontextprotocol/serverInfo'=>vg_info()];
    }
    echo json_encode(['jsonrpc'=>'2.0','id'=>$id,'result'=>(object)$result], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_PRESERVE_ZERO_FRACTION);
    exit;
}
function vg_schema(array $properties, array $required = []): array {
    return ['type'=>'object','properties'=>(object)$properties,'required'=>$required,'additionalProperties'=>false];
}
function vg_tools(): array {
    $annotations = ['readOnlyHint'=>true,'destructiveHint'=>false,'idempotentHint'=>true,'openWorldHint'=>false];
    $number = function(string $description, float $max): array {
        return ['type'=>'number','minimum'=>0,'maximum'=>$max,'description'=>$description];
    };
    return [
        ['name'=>'lookup_firmware','title'=>'Look up a VNISH Global catalog record',
         'description'=>'Find records in a dated snapshot of the public vnish.global firmware catalog. Use the exact model ID; narrow by board code and version if known. Returns file size, SHA-256 and source links. A catalog record does not establish device compatibility, package authenticity, or successful hardware testing. Does not download or install firmware.',
         'inputSchema'=>vg_schema([
             'model_id'=>['type'=>'string','minLength'=>1,'maxLength'=>64,'pattern'=>'^[a-z0-9-]+$','description'=>'Exact catalog model ID, for example s19j-xp. Read the model-index resource for all IDs.'],
             'board_platform'=>['type'=>'string','enum'=>['aml','bb','cv','xil']],
             'version'=>['type'=>'string','enum'=>['1.3.4','1.3.5']]
         ],['model_id']),'annotations'=>$annotations],
        ['name'=>'find_ninja_reference','title'=>'Find a VNISH Ninja reference',
         'description'=>'Return a selected public VNISH Ninja guide about control-board identification, installation SSH errors, or return-to-stock preparation. A reference is not a device-specific installation or recovery instruction. No device connection or action is performed.',
         'inputSchema'=>vg_schema([
             'topic'=>['type'=>'string','enum'=>['identify-control-board','ssh-error-install','return-to-stock']],
             'language'=>['type'=>'string','enum'=>['en','ru'],'default'=>'en']
         ],['topic']),'annotations'=>$annotations],
        ['name'=>'calculate_roi_scenario','title'=>'Calculate an ROI ASIC daily scenario',
         'description'=>'Calculate hypothetical daily revenue after an illustrative time/hashrate-based developer fee and electricity cost using user-supplied inputs. H*q*(hours/24)*(1-f/100) - (W/1000)*hours*t. This is a scenario, not a profit forecast or a statement of actual VNISH fees. Use pre-fee gross hashrate; do not deduct the fee twice.',
         'inputSchema'=>vg_schema([
             'hashrate_th_s'=>$number('Gross pre-fee hashrate, TH/s. The daily hashprice input must use the same hashrate basis.',100000000),
             'power_w'=>$number('Average wall power while operating, watts.',1000000000),
             'dev_fee_percent'=>$number('Scenario fee as a percent of gross daily revenue. This tool does not supply an actual firmware fee.',100),
             'hashprice_usd_per_th_day'=>$number('Gross daily revenue for one TH/s, USD/(TH/s)/day. Supply it yourself; no market data is fetched.',1000000),
             'electricity_usd_per_kwh'=>$number('Electricity price in USD/kWh.',1000),
             'operating_hours_per_day'=>['type'=>'number','minimum'=>0,'maximum'=>24,'default'=>24,'description'=>'Hours per day at the stated hashrate and wall power. Revenue and electricity scale by this same uptime assumption.']
         ],['hashrate_th_s','power_w','dev_fee_percent','hashprice_usd_per_th_day','electricity_usd_per_kwh']),'annotations'=>$annotations]
    ];
}
function vg_resources(): array {
    return [
        ['uri'=>'https://vnish.global/ai/mcp/model-index','name'=>'model-index','title'=>'Catalog model IDs','mimeType'=>'application/json'],
        ['uri'=>'https://vnish.global/ai/mcp/snapshot-info','name'=>'snapshot-info','title'=>'Catalog snapshot provenance and limits','mimeType'=>'application/json'],
        ['uri'=>'https://vnish.global/ai/mcp/scenario-method','name'=>'scenario-method','title'=>'ROI ASIC scenario formula and assumptions','mimeType'=>'application/json']
    ];
}
function vg_catalog(): array {
    static $catalog = null;
    if ($catalog === null) {
        $raw = @file_get_contents(__DIR__.'/catalog-snapshot.json');
        if ($raw === false) throw new RuntimeException('Catalog snapshot unavailable');
        $catalog = json_decode($raw, true, 32, JSON_THROW_ON_ERROR);
        if (!isset($catalog['snapshot'],$catalog['models'],$catalog['builds'])) throw new RuntimeException('Catalog snapshot invalid');
    }
    return $catalog;
}
function vg_method(): array {
    return [
        'formula'=>'gross_revenue_usd_day = hashrate_th_s * hashprice_usd_per_th_day * operating_hours_per_day / 24; after_fee_revenue_usd_day = gross_revenue_usd_day * (1 - dev_fee_percent / 100); electricity_kwh_day = power_w / 1000 * operating_hours_per_day; electricity_cost_usd_day = electricity_kwh_day * electricity_usd_per_kwh; contribution_usd_day = after_fee_revenue_usd_day - electricity_cost_usd_day',
        'assumptions'=>['User-supplied, hypothetical inputs; no live price, difficulty or pool data.','Hashrate is gross before the modeled fee. Already-net pool revenue or hashrate must not be reduced by the fee again.','Fee is modeled as a proportional reduction of revenue; actual implementation can differ.','Operating hours scale revenue and energy equally; idle energy outside those hours is excluded.','Contribution excludes hardware cost, depreciation, pool fees, cooling, taxes, repairs and other costs. It is not net profit or ROI.'],
        'source_urls'=>['https://roiasic.com/academy/videos/dev-fee-electricity/','https://roiasic.com/kb/dev-fee/']
    ];
}
function vg_validate(stdClass $arguments, array $schema): ?string {
    $args = get_object_vars($arguments);
    $properties = (array)$schema['properties'];
    foreach ($schema['required'] as $name) if (!array_key_exists($name,$args)) return 'Missing argument: '.$name;
    foreach ($args as $name=>$value) {
        if (!array_key_exists($name,$properties)) return 'Unknown argument: '.$name;
        $s = $properties[$name];
        if ($s['type']==='string') {
            if (!is_string($value)) return $name.' must be a string';
            if (isset($s['minLength']) && strlen($value)<$s['minLength']) return $name.' is too short';
            if (isset($s['maxLength']) && strlen($value)>$s['maxLength']) return $name.' is too long';
            if (isset($s['pattern']) && preg_match('~'.$s['pattern'].'~D',$value)!==1) return $name.' has an invalid format';
            if (isset($s['enum']) && !in_array($value,$s['enum'],true)) return $name.' must be one of: '.implode(', ',$s['enum']);
        } else {
            if ((!is_int($value) && !is_float($value)) || !is_finite((float)$value)) return $name.' must be a finite number';
            if ($value < $s['minimum'] || $value > $s['maximum']) return $name.' is outside the supported range';
        }
    }
    return null;
}
function vg_tool(string $name, stdClass $arguments): array {
    $a = get_object_vars($arguments);
    if ($name==='lookup_firmware') {
        $c = vg_catalog();
        $model = null;
        foreach ($c['models'] as $m) if ($m['id']===$a['model_id']) $model=$m;
        if ($model===null) return ['status'=>'model_not_found','requested_model_id'=>$a['model_id'],'snapshot'=>$c['snapshot'],'model_index_resource'=>'https://vnish.global/ai/mcp/model-index','records'=>[]];
        $records=[];
        foreach ($c['builds'] as $b) {
            if ($b['model_id']!==$a['model_id']) continue;
            if (isset($a['board_platform']) && $b['board_platform']['code']!==$a['board_platform']) continue;
            if (isset($a['version']) && $b['version']!==$a['version']) continue;
            $records[]=['build_id'=>$b['id'],'model_id'=>$b['model_id'],'model_name'=>$model['name'],'board_platform'=>$b['board_platform']['code'],'install_method'=>$b['install_method'],'version'=>$b['version'],'channel'=>$b['channel'],'file_name'=>$b['file_name'],'size_bytes'=>$b['size_bytes'],'sha256'=>$b['sha256'],'download_url'=>'https://vnish.global'.$b['download_path'],'catalog_url'=>'https://vnish.global/api/v1/firmware-catalog.json','route_url'=>'https://vnish.global/install/'.$b['route_id'].'/'];
        }
        usort($records,function(array $a,array $b): int { return strcmp($a['build_id'],$b['build_id']); });
        return ['status'=>count($records)===1?'exact_record':(count($records)>1?'multiple_records':'no_matching_record'),'snapshot'=>$c['snapshot'],'record_count'=>count($records),'records'=>array_slice($records,0,20),'limits'=>['Select the exact board and install route before considering a package. A similar model name is insufficient.','SHA-256 is copied from the catalog; this lookup does not hash a download, authenticate its publisher, or verify installation success.','Snapshot data may differ from the current catalog. The tool performs no network lookup.']];
    }
    if ($name==='find_ninja_reference') {
        $language=$a['language']??'en';
        $map=[
            'identify-control-board'=>['slug'=>'control-board-identification','en'=>'Identify an Antminer control board','ru'=>'Определение контрольной платы Antminer'],
            'ssh-error-install'=>['slug'=>'ssh-error-install','en'=>'Installation SSH errors','ru'=>'Ошибки SSH при установке'],
            'return-to-stock'=>['slug'=>'return-to-stock','en'=>'Preparation for return to stock firmware','ru'=>'Подготовка к возврату на стоковую прошивку']
        ];
        $entry=$map[$a['topic']];
        return ['topic'=>$a['topic'],'language'=>$language,'title'=>$entry[$language],'url'=>'https://vnish.ninja/'.($language==='ru'?'ru/':'').'kb/'.$entry['slug'].'/','scope'=>'Selected public reference. Read its prerequisites and identify the exact model and control board. This tool does not determine whether an installation or recovery method applies to your device.'];
    }
    $hours=$a['operating_hours_per_day']??24;
    $gross=$a['hashrate_th_s']*$a['hashprice_usd_per_th_day']*$hours/24;
    $after=$gross*(1-$a['dev_fee_percent']/100);
    $kwh=$a['power_w']/1000*$hours;
    $energy=$kwh*$a['electricity_usd_per_kwh'];
    $a['operating_hours_per_day']=$hours;
    return ['scenario_inputs'=>$a,'results'=>['gross_revenue_usd_day'=>round($gross,8),'modeled_fee_usd_day'=>round($gross-$after,8),'after_fee_revenue_usd_day'=>round($after,8),'electricity_kwh_day'=>round($kwh,8),'electricity_cost_usd_day'=>round($energy,8),'contribution_usd_day'=>round($after-$energy,8)],'method'=>vg_method()];
}
function vg_header_value(string $value): ?string {
    if (preg_match('/[^\x09\x20-\x7e]/',$value)) return null;
    if (strncmp($value,'=?base64?',9)===0 && substr($value,-2)==='?=') {
        $decoded=base64_decode(substr($value,9,-2),true);
        return $decoded===false?null:$decoded;
    }
    return $value;
}

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('Vary: Origin');
$origin=$_SERVER['HTTP_ORIGIN']??null;
if ($origin!==null) {
    if (!in_array($origin,VG_ORIGINS,true)) vg_error(403,-32600,'Origin is not allowed');
    header('Access-Control-Allow-Origin: '.$origin);
    header('Access-Control-Allow-Methods: POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, Accept, MCP-Protocol-Version, Mcp-Method, Mcp-Name, Mcp-Session-Id');
    header('Access-Control-Max-Age: 600');
}
$httpMethod=$_SERVER['REQUEST_METHOD']??'';
if ($httpMethod==='OPTIONS') { http_response_code(204); exit; }
if ($httpMethod!=='POST') { header('Allow: POST, OPTIONS'); vg_error(405,-32600,'Use POST for MCP. Connection guide: https://vnish.global/ai/connect/'); }
if (strtolower(trim(explode(';',$_SERVER['CONTENT_TYPE']??'')[0]))!=='application/json') vg_error(415,-32600,'Content-Type must be application/json');
$accept=strtolower($_SERVER['HTTP_ACCEPT']??'');
if (strpos($accept,'application/json')===false && strpos($accept,'*/*')===false) vg_error(406,-32600,'Accept must allow application/json and should also list text/event-stream');
if (isset($_SERVER['CONTENT_LENGTH']) && (int)$_SERVER['CONTENT_LENGTH']>VG_MAX_BODY) vg_error(413,-32600,'Request body exceeds 32768 bytes');
$raw=file_get_contents('php://input',false,null,0,VG_MAX_BODY+1);
if ($raw===false || strlen($raw)>VG_MAX_BODY) vg_error(413,-32600,'Request body exceeds 32768 bytes');
try { $request=json_decode($raw,false,32,JSON_THROW_ON_ERROR); }
catch (JsonException $e) { vg_error(400,-32700,'Invalid JSON'); }
if (!$request instanceof stdClass) vg_error(400,-32600,'Send one JSON-RPC object; batches are not supported');
$id=$request->id??null;
// Reject IDs that JSON/IEEE-754 clients cannot round-trip without changing correlation.
if (property_exists($request,'id') && !is_string($id)) {
    if ((!is_int($id) && !is_float($id)) || !is_finite((float)$id) || floor((float)$id)!==(float)$id || $id < -9007199254740991 || $id > 9007199254740991) {
        vg_error(400,-32600,'Request id must be a string or a safe integer');
    }
}
if (($request->jsonrpc??null)!=='2.0' || !isset($request->method) || !is_string($request->method) || $request->method==='') vg_error(400,-32600,'Invalid JSON-RPC request',$id);
$method=$request->method;
$params=property_exists($request,'params')?$request->params:new stdClass();
if (!$params instanceof stdClass) vg_error(400,-32602,'params must be an object',$id);
if (isset($params->_meta) && !$params->_meta instanceof stdClass) vg_error(400,-32602,'_meta must be an object',$id);
$meta=$params->_meta??new stdClass();
$headerVersion=$_SERVER['HTTP_MCP_PROTOCOL_VERSION']??null;
$bodyVersion=$meta->{'io.modelcontextprotocol/protocolVersion'}??null;
if ($bodyVersion!==null && !is_string($bodyVersion)) vg_error(400,-32602,'Protocol version must be a string',$id);
$protocol=$bodyVersion??$headerVersion??'2025-03-26';
if ($method==='initialize' && $bodyVersion===null) {
    if (!isset($params->protocolVersion) || !is_string($params->protocolVersion) || !isset($params->capabilities) || !$params->capabilities instanceof stdClass || !isset($params->clientInfo) || !$params->clientInfo instanceof stdClass || !is_string($params->clientInfo->name??null) || !is_string($params->clientInfo->version??null)) vg_error(400,-32602,'initialize requires protocolVersion, capabilities object and clientInfo name/version',$id);
    $protocol=in_array($params->protocolVersion,array_slice(VG_PROTOCOLS,1),true)?$params->protocolVersion:'2025-11-25';
}
if (!in_array($protocol,VG_PROTOCOLS,true)) vg_error(400,-32022,'Unsupported protocol version',$id,['supported'=>VG_PROTOCOLS,'requested'=>$protocol]);
$modern=$protocol==='2026-07-28';
if ($modern) {
    if ($bodyVersion===null || !property_exists($meta,'io.modelcontextprotocol/clientCapabilities') || !$meta->{'io.modelcontextprotocol/clientCapabilities'} instanceof stdClass) vg_error(400,-32602,'Modern MCP requires protocolVersion and clientCapabilities in params._meta',$id);
    if (isset($meta->{'io.modelcontextprotocol/clientInfo'}) && (!$meta->{'io.modelcontextprotocol/clientInfo'} instanceof stdClass || !is_string($meta->{'io.modelcontextprotocol/clientInfo'}->name??null) || !is_string($meta->{'io.modelcontextprotocol/clientInfo'}->version??null))) vg_error(400,-32602,'clientInfo requires name and version strings',$id);
    if ($headerVersion!==$bodyVersion || ($_SERVER['HTTP_MCP_METHOD']??null)!==$method) vg_error(400,-32020,'Missing or mismatched MCP-Protocol-Version or Mcp-Method header',$id);
    if (in_array($method,['tools/call','resources/read','prompts/get'],true)) {
        $source=$method==='resources/read'?($params->uri??null):($params->name??null);
        $nameHeader=vg_header_value($_SERVER['HTTP_MCP_NAME']??'');
        if (!is_string($source) || $nameHeader!==$source) vg_error(400,-32020,'Missing or mismatched Mcp-Name header',$id);
    }
}
if ($id===null) {
    if (!$modern && in_array($method,['notifications/initialized','notifications/cancelled','notifications/progress'],true)) { http_response_code(202); exit; }
    vg_error(400,-32600,'Unsupported notification');
}
try {
    $capabilities=['tools'=>['listChanged'=>false],'resources'=>['subscribe'=>false,'listChanged'=>false]];
    $instructions='Read-only public references for vnish.global, vnish.ninja and roiasic.com. Catalog results are dated metadata, not hardware verification. Scenario outputs use user-supplied assumptions and are not profit forecasts. No device access, installation, authentication, or writes.';
    if ($method==='initialize' && !$modern) vg_result($id,['protocolVersion'=>$protocol,'capabilities'=>$capabilities,'serverInfo'=>vg_info(),'instructions'=>$instructions],$protocol);
    if ($method==='server/discover' && $modern) vg_result($id,['supportedVersions'=>VG_PROTOCOLS,'capabilities'=>$capabilities,'instructions'=>$instructions],$protocol);
    if ($method==='ping') vg_result($id,[],$protocol);
    if (in_array($method,['tools/list','resources/list','resources/templates/list'],true)) {
        if (isset($params->cursor)) vg_error(400,-32602,'This complete small list has no pagination cursor',$id);
        $key=$method==='tools/list'?'tools':($method==='resources/list'?'resources':'resourceTemplates');
        vg_result($id,[$key=>$method==='tools/list'?vg_tools():($method==='resources/list'?vg_resources():[])],$protocol);
    }
    if ($method==='resources/read') {
        if (!is_string($params->uri??null)) vg_error(400,-32602,'uri must be a string',$id);
        $known=array_column(vg_resources(),'uri');
        $index=array_search($params->uri,$known,true);
        if ($index===false) vg_error(400,-32602,'Unknown resource URI; use resources/list',$id);
        $c=vg_catalog();
        $data=$index===0?['snapshot'=>$c['snapshot'],'models'=>array_map(function(array $m): array {return ['id'=>$m['id'],'name'=>$m['name']];},$c['models'])]:($index===1?$c['snapshot']:vg_method());
        vg_result($id,['contents'=>[['uri'=>$params->uri,'mimeType'=>'application/json','text'=>json_encode($data,JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE)]]],$protocol);
    }
    if ($method==='tools/call') {
        $definition=null;
        foreach (vg_tools() as $t) if (($params->name??null)===$t['name']) $definition=$t;
        if ($definition===null) vg_error(400,-32602,'Unknown tool name; use tools/list',$id);
        $args=$params->arguments??new stdClass();
        $error=$args instanceof stdClass?vg_validate($args,$definition['inputSchema']):'arguments must be an object';
        if ($error!==null) vg_result($id,['content'=>[['type'=>'text','text'=>$error]],'isError'=>true],$protocol);
        $data=vg_tool($params->name,$args);
        $result=['content'=>[['type'=>'text','text'=>json_encode($data,JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE)]],'isError'=>false];
        if ($protocol!=='2025-03-26') $result['structuredContent']=$data;
        vg_result($id,$result,$protocol);
    }
    vg_error($modern?404:200,-32601,'Method not found',$id);
} catch (Throwable $e) {
    vg_error(500,-32603,'The bundled public reference could not be read. Please retry later.',$id);
}
