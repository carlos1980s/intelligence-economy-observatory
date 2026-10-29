/** Normalized contract 2026-10-29.1. Scenario quantities/prices are indices, never dollars or world tasks. */
export const DEFAULTS=Object.freeze({A:1,B:1,K:1.5,epsilon:1,eta:1,rho:1,costIndex:100});
export function validate(x){for(const k of Object.keys(DEFAULTS))if(typeof x[k]!== 'number'||!Number.isFinite(x[k]))throw new Error(`Invalid ${k}`);
 for(const k of ['A','B','K','epsilon','eta','costIndex'])if(x[k]<=0)throw new Error(`${k} must be positive`);if(x.rho<0||x.rho>1)throw new Error('Pass-through must be between zero and one');return x;}
export function costShifter(x){validate(x);return (x.costIndex/100)**x.rho;}
export function demand(p,x){validate(x);if(!Number.isFinite(p)||p<=0)throw new Error('Positive price required');return x.A*p**(-x.epsilon);}
export function marginalCost(q,x){validate(x);if(!Number.isFinite(q)||q<0||q>x.K)throw new Error('Quantity outside deliverable capacity');return costShifter(x)*(q/x.B)**(1/x.eta);}
export function inverseDemand(q,x){validate(x);if(q<=0)return null;return (x.A/q)**(1/x.epsilon);}
export function equilibrium(x){validate(x);const c=costShifter(x),pu=(x.A/x.B)**(1/(x.epsilon+x.eta))*c**(x.eta/(x.epsilon+x.eta)),qu=x.A*pu**(-x.epsilon),bound=qu>x.K;
 const q=bound?x.K:qu,p=bound?(x.A/x.K)**(1/x.epsilon):pu,mc=marginalCost(q,x);
 if(![q,p,mc].every(Number.isFinite))throw new Error('Scenario outside numerical range');
 return {quantity:q,price:p,marginalCost:mc,scarcityRent:bound?Math.max(0,p-mc):0,capacityBound:bound,costShifter:c};}
export function sensitivity(x){const r=[];for(const A of [.8,1.2])for(const B of [.8,1.2])for(const K of [.8,1.2])r.push(equilibrium({...x,A:x.A*A,B:x.B*B,K:x.K*K}));
 return {quantity:[Math.min(...r.map(v=>v.quantity)),Math.max(...r.map(v=>v.quantity))],price:[Math.min(...r.map(v=>v.price)),Math.max(...r.map(v=>v.price))],label:'Eight corners: demand A, productivity B and deliverable capacity K ±20%; assumption envelope, not a confidence interval'};}
export function freshness(timestamp,now=Date.now(),maxDays=7){const t=Date.parse(timestamp);if(!Number.isFinite(t)||t>now+300000)return 'unavailable';return now-t>maxDays*86400000?'stale':'recent snapshot';}
// Exact decimal arithmetic for billed token-price conventions; no binary rounding of source rates.
function decimal(value){const match=String(value).match(/^(\d+)(?:\.(\d*))?(?:e([+-]?\d+))?$/i);if(!match)throw new Error('Invalid decimal rate');let scale=(match[2]||'').length-Number(match[3]||0);if(scale>30||scale< -12||match[1].length>40)throw new Error('Decimal rate outside supported precision');let n=BigInt(match[1]+(match[2]||''));if(scale<0){n*=10n**BigInt(-scale);scale=0;}return {n,scale};}
function add(a,b){let scale=Math.max(a.scale,b.scale);return {n:a.n*10n**BigInt(scale-a.scale)+b.n*10n**BigInt(scale-b.scale),scale};}
function multiply(a,b){return {n:a.n*b.n,scale:a.scale+b.scale};}
function decimalString(a){let str=a.n.toString().padStart(a.scale+1,'0');if(a.scale)str=str.slice(0,-a.scale)+'.'+str.slice(-a.scale);return str.includes('.')?str.replace(/0+$/,'').replace(/\.$/,''):str;}
export function tokenCost(model,input,output,cache=0){
 if(!Number.isInteger(input)||!Number.isInteger(output)||input<0||output<0||cache<0||cache>1)throw new Error('Invalid token workload');
 if(model.context_length&&input+output>model.context_length)throw new Error('Workload exceeds listed context window');
 const base=model.pricing;let rates={...base};
 const overrides=base.overrides||[];
 const priceKeys=new Set(['prompt','completion','input_cache_read','input_cache_write','input_cache_write_1h','request','image','audio','web_search','input_audio_cache','internal_reasoning','min_prompt_tokens']);
 for(const override of overrides){
  if(!Number.isFinite(override.min_prompt_tokens)||Object.keys(override).some(k=>!priceKeys.has(k)))throw new Error('Unsupported conditional price tier');
  if(input>override.min_prompt_tokens)rates={...rates,...override};
 }
 function rate(k){const v=Number(rates[k]);if(rates[k]===undefined||!Number.isFinite(v)||v<0)throw new Error(`Unavailable ${k} price`);return v;}
 rate('prompt');rate('completion');if(cache)rate('input_cache_read');
 const costExact=add(add(multiply(multiply(decimal(input),decimal(1-cache)),decimal(rates.prompt)),multiply(multiply(decimal(input),decimal(cache)),decimal(cache?rates.input_cache_read:rates.prompt))),multiply(decimal(output),decimal(rates.completion)));
 return {cost:Number(decimalString(costExact)),cost_decimal:decimalString(costExact),rates,
  convention:'Text-only input/output convention; excludes tools, images, audio, retries, provider routing and quality differences'};
}
