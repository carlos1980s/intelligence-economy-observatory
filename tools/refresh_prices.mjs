/** Manual operator-only refresh. No account, key, timer or policy bypass flag. */
import {readFile,writeFile,rename,mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {refreshCatalog} from '../site/assets/catalog.mjs';
const data=fileURLToPath(new URL('../site/data/',import.meta.url));
const policy=JSON.parse(await readFile(data+'source-policy.json','utf8'));
const previous=JSON.parse(await readFile(data+'prices.json','utf8'));
const result=await refreshCatalog(previous,{policy});
// A blocked policy does not mutate the retained research capture or make a request.
if(policy.automated_refresh_allowed!==true){console.error(result.error);process.exitCode=2;}
else{if(result.refresh_state==='success'&&previous.observed_at!==result.observed_at){await mkdir(data+'history',{recursive:true});const vintage=String(previous.observed_at).replace(/[^0-9TZ]/g,'_');await writeFile(data+'history/'+vintage+'.json',JSON.stringify(previous,null,2)+'\n',{flag:'wx'}).catch(e=>{if(e.code!=='EEXIST')throw e;});}await writeFile(data+'prices.json.tmp',JSON.stringify(result,null,2)+'\n');await rename(data+'prices.json.tmp',data+'prices.json');console.log(JSON.stringify({status:result.refresh_state,observed_at:result.observed_at,records:result.models?.length||0}));if(result.refresh_state!=='success')process.exitCode=2;}
