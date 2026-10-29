/** Explicit factual fields only; descriptions and benchmark corpora never copied. */
export const SELECTED_IDS=['google/gemini-2.5-flash','google/gemini-2.5-pro','deepseek/deepseek-chat-v3-0324','meta-llama/llama-3.3-70b-instruct','openai/gpt-4o-mini','openai/gpt-4o'];
export function selectModels(payload){
 if(!Array.isArray(payload?.data))throw new Error('Invalid models response');
 const seen=new Set(),rows=[];
 for(const m of payload.data){if(!SELECTED_IDS.includes(m.id)||m.id.includes(':')||!m.architecture?.output_modalities?.includes('text'))continue;if(seen.has(m.id))throw new Error('Duplicate exact model ID');seen.add(m.id);
  if(typeof m.canonical_slug!=='string'||!m.pricing)throw new Error('Missing canonical slug or pricing');
  if(m.pricing.overrides?.some(o=>Object.keys(o).some(k=>/time|day|schedule|utc/i.test(k))))throw new Error('Scheduled price excluded until explicit request-time normalization');
  for(const key of ['prompt','completion'])if(m.pricing[key]===undefined||!Number.isFinite(Number(m.pricing[key]))||Number(m.pricing[key])<0)throw new Error('Unavailable token rate');
  if(Number(m.pricing.prompt)===0&&Number(m.pricing.completion)===0)continue;
  rows.push({provider_basis:'top-provider offered catalog rate; provider identity may change',id:m.id,canonical_slug:m.canonical_slug,context_length:m.context_length??null,pricing:structuredClone(m.pricing),expiration_date:m.expiration_date??null,
   input_modalities:m.architecture?.input_modalities??[],output_modalities:m.architecture?.output_modalities??[],tokenizer:m.architecture?.tokenizer??null,reasoning_configuration:null,published_at_utc:null,effective_at_utc:null,
   service_variant:'synchronous catalog base',pricing_tier:'base; conditional overrides retained',series_identity:[m.id,m.canonical_slug,'synchronous','text','catalog-top-provider'].join('|'),input_modality:'text',output_modality:'text',service_tier:m.id.includes(':batch')?'batch':'catalog default; provider route unspecified',source_url:'https://openrouter.ai/api/v1/models',unit:'USD/token',evidence:'OBSERVED catalog tariff',capacity_verified:false});
 }return rows.sort((a,b)=>SELECTED_IDS.indexOf(a.id)-SELECTED_IDS.indexOf(b.id));
}
async function boundedText(response){if(!response.body?.getReader){const text=await response.text();if(new TextEncoder().encode(text).length>4*1024*1024)throw new Error('Source response exceeds 4 MiB budget');return text;}const reader=response.body.getReader(),chunks=[];let total=0;for(;;){const {done,value}=await reader.read();if(done)break;total+=value.length;if(total>4*1024*1024){await reader.cancel();throw new Error('Source response exceeds 4 MiB budget');}chunks.push(value);}const bytes=new Uint8Array(total);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}return new TextDecoder().decode(bytes);}
export async function refreshCatalog(lastGood,{fetcher=fetch,policy,now=()=>new Date().toISOString()}={}){
 if(policy?.automated_refresh_allowed!==true)return {...lastGood,refresh_state:'blocked by source policy',last_attempt_at:null,error:'Source reuse/automation review pending; stored data are not a live stream'};
 try{const response=await fetcher('https://openrouter.ai/api/v1/models',{signal:AbortSignal.timeout(15000),credentials:'omit',cache:'no-store'});
  if(!response.ok)throw new Error(`Source HTTP ${response.status}`);
  const text=await boundedText(response);
  const payload=JSON.parse(text);const rows=selectModels(payload);if(!rows.length)throw new Error('No selected models available');
  const observed=now(),hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))).map(x=>x.toString(16).padStart(2,'0')).join('');
  const observations=rows.map(r=>({...r,source_id:'openrouter_models',retrieved_at_utc:observed,observation_period_start:observed,observation_period_end:observed,published_at_utc:null,effective_at_utc:null,currency:'USD',geography:'top provider route unspecified',population:'six exact incumbent model ID examples; not market representative',series_definition_version:'2026-10-29.2',evidence_class:'observed',raw_sha256:hash,value:{input_usd_per_million:Number(r.pricing.prompt)*1e6,output_usd_per_million:Number(r.pricing.completion)*1e6},status:'top-provider offered catalog snapshot; not executed price',license_note:'Selected factual fields and attribution only; approved use must remain within source policy',fixed_basket_eligible:false,derived_blended_3_to_1_usd_per_million:1e6*(.75*Number(r.pricing.prompt)+.25*Number(r.pricing.completion))}));
  return {schema_version:1,streaming:false,universe_rows_at_capture:payload.data.length,universe_definition:'Default text-output model catalog; not all modalities or a representative market',observed_at:observed,models:observations,observations,parser_version:'2026-10-29.2',coverage:{expected:SELECTED_IDS.length,observed:observations.length,missing_ids:SELECTED_IDS.filter(id=>!observations.some(r=>r.id===id))},refresh_state:'success',last_attempt_at:observed,source:'OpenRouter top-provider offered catalog; not executed prices'};
 }catch(e){return {...lastGood,refresh_state:'failed; last-good snapshot retained',last_attempt_at:now(),error:String(e.message).slice(0,180)};}
}
