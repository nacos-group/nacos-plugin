/* Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 */
'use strict';
const {test}=require('node:test'), assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm'), path=require('node:path');
require('../src/nacos_registry/ui/model.js');
const crypto=require('node:crypto');
const M=globalThis.NacosModel, state=context=>({context,profile:{id:'example'},installations:[],connections:[]});
require('../src/nacos_registry/ui/settings-model.js');
const S=globalThis.NacosSettingsModel;
test('discovery preferences default to ask and keep connection configuration separate',()=>{
 assert.equal(S.discoveryPolicy({}), 'ask');
 assert.deepEqual(S.discoveryPolicies, ['ask','auto','never']);
 for(const policy of S.discoveryPolicies){
  assert.equal(S.discoveryPolicy({discovery:{installPolicy:policy}}),policy);
  assert.ok(S.t({ask:'policyAsk',auto:'policyAuto',never:'policyNever'}[policy], 'en-US'));
 }
 const p=profile(),d=S.draft(p);S.serialize(d);assert.deepEqual(p,profile());
});
function profile(){return {id:'stable',displayName:'Team',identityId:'account-a',namespaceId:'public',
 clientUrl:'https://registry.example.org/nacos',adminUrl:'https://registry.example.org/nacos',
 clientAuth:{type:'login',usernameEnv:'CLIENT_USER',passwordEnv:'CLIENT_PASSWORD'},
 adminAuth:{type:'login',usernameEnv:'CLIENT_USER',passwordEnv:'CLIENT_PASSWORD'},
 allowedOperations:['read','install'],scanRoots:[],installRoots:[]};}
test('new drafts use detected defaults without changing the source or existing profiles',()=>{
 const defaults={id:'machine',identityId:'os-user',installRoots:['/home/user/.agents/skills'],scanRoots:[],codexConfig:'/home/user/.codex/config.toml'};
 const d=S.draft(null,defaults);assert.equal(d.profile.id,'machine');assert.equal(d.profile.identityId,'os-user');
 assert.equal(d.profile.codexConfig,defaults.codexConfig);assert.deepEqual(d.profile.installRoots,defaults.installRoots);
 d.profile.installRoots.push('/custom');assert.equal(defaults.installRoots.length,1);
 const p=profile();assert.deepEqual(S.draft(p,defaults).profile,p);
 assert.deepEqual(S.draft(p,defaults).profile.installRoots,[]);
});
test('directory prefill respects explicit choices and retains saved connection identities',()=>{
 const p=profile(),defaults={id:'machine',identityId:'os-user',installRoots:['/default'],codexConfig:'/default/config.toml'};
 const patch={installRoots:['/custom'],scanRoots:[],codexConfig:'/custom/config.toml'};
 const d=S.prefill(p,patch,defaults);assert.equal(d.profile.id,p.id);assert.equal(d.profile.identityId,p.identityId);
 assert.deepEqual(d.profile.installRoots,['/custom']);assert.deepEqual(d.profile.scanRoots,[]);
 assert.equal(d.profile.codexConfig,'/custom/config.toml');d.profile.installRoots.push('/another');
 assert.deepEqual(p.installRoots,[]);assert.deepEqual(patch.installRoots,['/custom']);
});
test('adding default roots preserves custom paths, deduplicates and keeps the root bound',()=>{
 const d=S.draft(profile());d.profile.installRoots=[' /custom ', '', '/default'];
 S.addDefaultRoots(d,'installRoots',{installRoots:['/default','/another']});
 assert.deepEqual(d.profile.installRoots,['/custom','/default','/another']);
 d.profile.scanRoots=Array.from({length:15},(_,i)=>'/custom/'+i);
 S.addDefaultRoots(d,'scanRoots',{scanRoots:['/default','/another']});assert.equal(d.profile.scanRoots.length,16);
 assert.equal(d.profile.scanRoots[0],'/custom/0');assert.equal(d.profile.scanRoots[15],'/default');
});
test('single connection editing preserves record identity and maps both API roles',()=>{
 const p=profile(),d=S.draft(p);assert.equal(d.separateAdmin,false);
 d.profile.displayName='Renamed';d.profile.clientUrl='https://other.example.org/nacos';
 d.profile.clientAuth={type:'token',tokenEnv:'REGISTRY_TOKEN'};const saved=S.serialize(d);
 assert.equal(saved.id,p.id);assert.equal(saved.identityId,p.identityId);
 assert.equal(saved.adminUrl,saved.clientUrl);assert.deepEqual(saved.adminAuth,saved.clientAuth);
 assert.equal(p.displayName,'Team');assert.equal(p.adminAuth.type,'login');assert.deepEqual(S.validate(saved),{});
});
test('independent management settings survive unrelated edits until explicitly combined',()=>{
 const p=profile();p.adminUrl='https://admin.example.org/nacos';p.adminAuth={type:'token',tokenEnv:'ADMIN_TOKEN'};
 const d=S.draft(p);assert.equal(d.separateAdmin,true);d.profile.clientAuth={type:'none'};
 const saved=S.serialize(d);assert.equal(saved.adminUrl,p.adminUrl);assert.deepEqual(saved.adminAuth,p.adminAuth);
 d.separateAdmin=false;assert.deepEqual(S.serialize(d).adminAuth,{type:'none'});
 const authOnly=profile();authOnly.adminAuth={type:'none'};assert.equal(S.draft(authOnly).separateAdmin,true);
});
test('settings validation locates malformed URLs and references without accepting secrets',()=>{
 const d=S.draft(profile());d.profile.clientUrl='https://user:password@registry.example.org';
 d.profile.clientAuth.passwordEnv='a password value';d.profile.scanRoots=['','relative/path'];
 const p=S.serialize(d),errors=S.validate(p,d.profile);
 assert.equal(errors.clientUrl,'invalidUrl');assert.equal(errors['clientAuth.passwordEnv'],'invalidEnv');
 assert.equal(errors.scanRoots1,'invalidPath');assert.equal(errors.scanRoots0,undefined);
});
test('operation labels follow the app locale while protocol scope keys remain unchanged',()=>{
 const p=profile();for(const key of S.scopes){assert.notEqual(S.t(key,'zh-CN'),key);assert.notEqual(S.t(key,'en-US'),key);}
 assert.equal(S.t('read','en-GB'),'Discover & read');assert.equal(S.t('read',null),'发现与读取');
 assert.deepEqual(S.serialize(S.draft(p)).allowedOperations,p.allowedOperations);
});
test('settings restores source through internal steps, but invalidates on context change',()=>{
 const w=new M.Workspace();w.receive(state('a'));w.view='discover';const d={kind:'install',draft:{root:'/example'}};
 w.detail=d;w.search.query='kept';w.enter('settings',400);w.enter('settings');
 assert.equal(w.leave(),400);assert.equal(w.detail,d);assert.equal(w.search.query,'kept');
 w.enter('settings',400);w.receive(state('b'));w.leave();assert.equal(w.detail,null);assert.equal(w.search.query,'');
});
test('nested local skills, upload and settings return to their own source and scroll',()=>{
 const w=new M.Workspace();w.receive(state('a'));w.view='owned';const detail={kind:'versions'};w.detail=detail;
 w.enter('local',120);w.enter('upload',560);w.enter('settings',240);
 assert.equal(w.leave(),240);assert.equal(w.subpage,'upload');
 assert.equal(w.leave(),560);assert.equal(w.subpage,'local');
 assert.equal(w.leave(),120);assert.equal(w.subpage,null);assert.equal(w.detail,detail);
 w.enter('local',120);w.enter('settings',560);w.receive(state('b'));
 assert.equal(w.leave(),0);assert.equal(w.subpage,'local');w.leave();assert.equal(w.detail,null);
});
test('returning from confirmation does not leave a duplicate step in the back stack',()=>{
 const w=new M.Workspace(),overview={kind:'overview'},input={kind:'install',draft:{version:'2'}},plan={kind:'plan'};
 w.open(overview);w.open(input);w.open(plan);w.returnTo(input);
 assert.equal(w.detail,input);assert.deepEqual(w.stack,[overview]);assert.equal(w.detail.draft.version,'2');
 w.open(plan);w.returnTo(input);w.back();assert.equal(w.detail,overview);w.back();assert.equal(w.detail,null);
});
test('discovery connection badges require matching type, version and source',()=>{
 const ref={registryId:'one',namespaceId:'public',name:'same',resourceType:'skill'};
 const s={installations:[{ref,version:'1',target:'/a'},{ref,version:'1',target:'/b'}],connections:[{ref:{...ref,resourceType:'mcp'},version:'1'}]};
 assert.equal(M.connectedMatches({name:'same',resourceType:'skill',version:'1'},s).length,2);
 assert.equal(M.connectedMatches({name:'same',resourceType:'mcp',version:'1'},s).length,1);
 for(const x of [{name:'same',resourceType:'skill'},{ref:{...ref,registryId:'two'},version:'1'},{ref,version:'2'}])
  assert.equal(M.connectedMatches(x,s).length,0);
});
test('discovery initially lists all, keeps visited results and resets on context changes',()=>{
 const w=new M.Workspace();assert.equal(w.needsSearch(),false);
 w.receive(state('a'));assert.equal(w.needsSearch(),true);
 assert.deepEqual(w.searchRequest(),{query:'',limit:20});
 w.search.loading=true;assert.equal(w.needsSearch(),false);
 w.search.loading=false;w.search.submitted=true;w.search.error='offline';
 assert.equal(w.needsSearch(),false); // No automatic retry loop after a failed read.
 w.view='connected';w.view='discover';assert.equal(w.needsSearch(),false);
 w.receive(state('b'));assert.equal(w.needsSearch(),true);
 w.enter('settings');assert.equal(w.needsSearch(),false);w.leave();assert.equal(w.needsSearch(),true);
 w.search.type='mcp';w.search.query='   ';assert.deepEqual(w.searchRequest(),{query:'',limit:20,resourceTypes:['mcp']});
});
test('load more keeps submitted filters while a new filter remains a draft',()=>{
 const w=new M.Workspace();w.receive(state('a'));
 w.search.applied={query:'',type:'skill'};w.search.cursor='opaque+/=';
 w.search.query='unsubmitted';w.search.type='agent';
 assert.deepEqual(w.searchRequest(true),{query:'',limit:20,resourceTypes:['skill'],cursor:'opaque+/='});
 assert.deepEqual(w.searchRequest(),{query:'unsubmitted',limit:20,resourceTypes:['agent']});
 w.search.loading=true;assert.equal(w.searchRequest(true),null);
 w.search.loading=false;w.search.cursor=null;assert.equal(w.searchRequest(true),null);
 w.receive(state('b'));assert.equal(w.searchRequest(true),null);assert.equal(w.search.applied,null);
});
test('stale responses cannot overwrite a newer query or context',()=>{
 const w=new M.Workspace();w.receive(state('a'));const a=w.begin('search'),b=w.begin('search');
 assert.equal(w.accepts('search',a),false);assert.equal(w.accepts('search',b),true);w.receive(state('b'));assert.equal(w.accepts('search',b),false);
});
test('writes are exclusive and failures release the lock',async()=>{
 const w=new M.Workspace();let release;const first=w.exclusive('apply',()=>new Promise(r=>release=r));
 await assert.rejects(w.exclusive('apply',()=>assert.fail('must not execute')),{kind:'busy'});release(1);assert.equal(await first,1);
 await assert.rejects(w.exclusive('apply',()=>{throw new Error('failure');}));assert.equal(w.busy.size,0);
});
test('pagination deduplicates only identical references',()=>{
 const a={name:'same',resourceType:'skill',version:'1'};assert.equal(M.append([a],[a,{...a,resourceType:'mcp'},{...a,version:'2'}]).length,3);
});
test('type and ownership determine menus',()=>{
 assert.ok(M.menu('skill','connected').some(x=>x[0]==='update'));assert.ok(!M.menu('mcp','connected').some(x=>x[0]==='update'));
 assert.ok(M.menu('agent','connected').some(x=>x[0]==='task'));assert.ok(!M.menu('skill','owned').some(x=>x[0]==='remove'));
});
test('cancellation and publication require positive state evidence',()=>{
 assert.equal(M.canCancel({taskHandle:'task',status:'working'}),true);
 for(const status of ['completed','failed','canceled','rejected'])assert.equal(M.canCancel({taskHandle:'task',status}),false);
 assert.equal(M.canCancel({taskHandle:'task',status:'working',cancelRequested:true}),false);
 assert.equal(M.canPublish({status:'reviewed'}),false);assert.equal(M.canPublish({status:'reviewed',publishPipelineInfo:'{"status":"APPROVED"}'}),true);
 assert.equal(M.canPublish({status:'reviewed',publishPipelineInfo:'invalid json'}),false);
});
function fixture(entrypoint){let listener;const outgoing=[],parent={postMessage:m=>outgoing.push(m)},context={parent,window:{addEventListener:(_,fn)=>listener=fn},setTimeout,clearTimeout,TextEncoder,Uint8Array,DataView,atob,btoa,crypto:crypto.webcrypto};
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../src/nacos_registry/ui/credential-crypto.js'),'utf8'),context);
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../src/nacos_registry/ui/bridge.js'),'utf8'),context);
 return {bridge:new context.NacosBridge(()=>{},entrypoint),context,outgoing,reply:m=>listener({source:parent,data:m}),foreign:m=>listener({source:{},data:m})};
}
test('page credentials remain outside the ordinary profile and map shared/independent roles',()=>{
 const d=S.draft(profile());d.profile.clientAuth={type:'login',source:'local'};
 const edits={clientAuth:{username:'sample',password:'private-sample'}};
 const p=S.serialize(d),changes=S.credentialChanges(d,edits);
 assert.ok(!JSON.stringify(p).includes('private-sample'));
 assert.deepEqual(changes.client,changes.admin);assert.deepEqual(S.validate(p,p,changes),{});
 assert.equal(S.validate(p)['clientAuth.password'],'missing');
 d.separateAdmin=true;assert.equal(S.credentialChanges(d,edits).admin,undefined);
 d.profile.clientAuth.credentialRef='a'.repeat(32);
 assert.equal(S.validate(S.serialize(d))['clientAuth.password'],undefined);
 const clear=S.credentialChanges(d,{clientAuth:{clear:true}});assert.deepEqual(clear.client,{clear:true});
});
test('nonsecret prefill preserves ordinary settings but drops credentials on destination change',()=>{
 const p=profile();p.clientAuth=p.adminAuth={type:'token',source:'local',credentialRef:'a'.repeat(32)};
 const d=S.prefill(p,{clientUrl:'https://new.example.org/nacos',password:'must-not-be-accepted'});
 assert.equal(d.profile.id,p.id);assert.equal(d.profile.clientAuth.credentialRef,undefined);
 assert.equal(d.profile.password,undefined);assert.equal(p.clientAuth.credentialRef,'a'.repeat(32));
 const split=S.prefill(p,{adminUrl:'https://admin.example.org/nacos'});assert.equal(split.separateAdmin,true);
});
test('launch result is received without trusting foreign messages',()=>{
 const f=fixture('thread'),result={structuredContent:{status:'ready',launchId:'one',route:'settings',draft:{namespaceId:'public'}}};
 f.foreign({jsonrpc:'2.0',method:'ui/notifications/tool-result',params:result});assert.equal(f.bridge.launch,undefined);
 f.reply({jsonrpc:'2.0',method:'ui/notifications/tool-result',params:result});assert.equal(f.bridge.launch.launchId,'one');
});
const rsa=crypto.generateKeyPairSync('rsa',{modulusLength:2048});
const encryptionSession=()=>({mode:'mcp-jwe-v1',sessionId:'A'.repeat(43),
 publicKey:rsa.publicKey.export({type:'spki',format:'der'}).toString('base64url')});
function ready(f,channel=encryptionSession()){
 f.reply({jsonrpc:'2.0',id:f.outgoing[0].id,result:{structuredContent:{status:'ready'},_meta:{'nacos/credentialChannel':channel}}});
}
function decrypt(envelope){
 const parts=envelope.split('.'),[header,wrapped,iv,cipher,tag]=parts.map(x=>Buffer.from(x,'base64url'));
 assert.deepEqual(JSON.parse(header),{alg:'RSA-OAEP-256',enc:'A256CBC-HS512',kid:'A'.repeat(43)});
 const cek=crypto.privateDecrypt({key:rsa.privateKey,oaepHash:'sha256',padding:crypto.constants.RSA_PKCS1_OAEP_PADDING},wrapped);
 const aad=Buffer.from(parts[0]),length=Buffer.alloc(8);length.writeBigUInt64BE(BigInt(aad.length*8));
 const expected=crypto.createHmac('sha512',cek.subarray(0,32)).update(Buffer.concat([aad,iv,cipher,length])).digest().subarray(0,32);
 assert.equal(crypto.timingSafeEqual(tag,expected),true);
 const decipher=crypto.createDecipheriv('aes-256-cbc',cek.subarray(32),iv);
 return JSON.parse(Buffer.concat([decipher.update(cipher),decipher.final()]));
}
test('page WebCrypto JWE interoperates with independent Node primitives and randomizes each save',async()=>{
 const f=fixture(),payload={profile:{id:'example'},changes:{client:{username:'sample',password:'synthetic-密码'}}};
 const first=await f.context.NacosCredentialCrypto.seal(encryptionSession(),payload);
 const second=await f.context.NacosCredentialCrypto.seal(encryptionSession(),payload);
 assert.deepEqual(decrypt(first),payload);assert.deepEqual(decrypt(second),payload);assert.notEqual(first,second);
});
test('credential bridge sends only ciphertext over MCP, with no page network access',async()=>{
 const f=fixture('thread');f.context.fetch=()=>assert.fail('no network access');
 const original=f.context.parent.postMessage;
 f.context.parent.postMessage=m=>{
  original(m);
  if(m.params?.name==='nacos_credentials_save'){
   assert.deepEqual(decrypt(m.params.arguments.envelope),{profile:{id:'example'},changes:{client:{token:'private-sample'}}});
   assert.equal(m.params.arguments._context,'expected');
   setImmediate(()=>f.reply({jsonrpc:'2.0',id:m.id,result:{structuredContent:{status:'configured'}}}));
  }
 };
 const pending=f.bridge.saveCredentials({id:'example'},{client:{token:'private-sample'}},'expected');
 assert.equal(f.outgoing[0].params.name,'nacos_credentials_begin');ready(f);
 assert.equal((await pending).status,'configured');assert.equal(f.outgoing.length,2);
 assert.equal(JSON.stringify(f.outgoing).includes('private-sample'),false);
});
test('invalid encryption metadata or unavailable crypto never falls back to plaintext',async()=>{
 for(const channel of [{url:'http://127.0.0.1:54321/configure'}, {...encryptionSession(),mode:'unknown'},
                        {...encryptionSession(),publicKey:'invalid'},encryptionSession()]){
  const f=fixture('thread');if(channel.mode==='mcp-jwe-v1'&&channel.publicKey===encryptionSession().publicKey)f.context.crypto=undefined;
  const pending=f.bridge.saveCredentials({}, {client:{token:'private-sample'}},'ctx');ready(f,channel);
  await assert.rejects(pending,e=>e.kind==='credential_crypto'&&!e.message.includes('private-sample'));
  assert.equal(f.outgoing.length,1);
 }
});
test('encrypted save failures have a fixed diagnostic and oversized input is not sent',async()=>{
 const f=fixture('thread'),original=f.context.parent.postMessage;
 f.context.parent.postMessage=m=>{
  original(m);if(m.params?.name==='nacos_credentials_save')
   setImmediate(()=>f.reply({jsonrpc:'2.0',id:m.id,result:{isError:true,structuredContent:{error:'credential_store',message:'private-sample'}}}));
 };
 const pending=f.bridge.saveCredentials({}, {client:{token:'private-sample'}},'ctx');ready(f);
 await assert.rejects(pending,e=>e.kind==='credential_store'&&!e.message.includes('private-sample'));
 await assert.rejects(f.context.NacosCredentialCrypto.seal(encryptionSession(),{value:'x'.repeat(32769)}),{kind:'credential_crypto'});
});
test('resource entrypoint works without optional host toolInfo or conversation identifiers',()=>{
 for (const displayMode of ['inline','fullscreen']) {
  const thread=fixture('thread').bridge,global=fixture('global').bridge;
  const host={hostCapabilities:{message:{text:{}}},hostContext:{displayMode}};
  thread.host=host;global.host=host;
  assert.equal(thread.canMessageCurrentConversation(),true);
  assert.equal(global.canMessageCurrentConversation(),false);
  host.hostContext.toolInfo={tool:{name:'nacos_open_center_panel'}};
  assert.equal(global.canMessageCurrentConversation(),false);
  host.hostCapabilities.message={};assert.equal(thread.canMessageCurrentConversation(),false);
 }
});
test('thread entry supports handoff after expansion without a conversation ID',()=>{
 const {bridge}=fixture();
 bridge.host={hostCapabilities:{message:{text:{}}},hostContext:{displayMode:'fullscreen',
  toolInfo:{tool:{name:'nacos_open_center_panel'}}}};
 assert.equal(bridge.canMessageCurrentConversation(),true);
 bridge.host.hostContext.toolInfo.tool={name:'qualified-tool',_meta:{'openai/ui':{entrypoints:[{type:'thread'}]}}};
 assert.equal(bridge.canMessageCurrentConversation(),true);
 bridge.host.hostCapabilities.message={};assert.equal(bridge.canMessageCurrentConversation(),false);
});
test('global and unknown fullscreen views cannot send to a conversation',async()=>{
 const f=fixture();f.bridge.host={hostCapabilities:{message:{text:{}}},hostContext:{displayMode:'fullscreen'}};
 assert.equal(f.bridge.canMessageCurrentConversation(),false);
 f.bridge.host.hostContext.displayMode='inline';assert.equal(f.bridge.canMessageCurrentConversation(),false);
 f.bridge.host.hostContext={displayMode:'inline',threadId:'internal-global-context',
  toolInfo:{tool:{name:'nacos_open_center'}}};
 assert.equal(f.bridge.canMessageCurrentConversation(),false);
 await assert.rejects(f.bridge.messageCurrentConversation('example'),{kind:'unsupported'});
 assert.equal(f.outgoing.length,0);
});
test('host context updates retain entrypoint when a thread app expands',()=>{
 const f=fixture();f.bridge.host={hostCapabilities:{message:{text:{}}},hostContext:{displayMode:'inline',
  toolInfo:{tool:{name:'nacos_open_center_panel'}}}};
 f.reply({jsonrpc:'2.0',method:'ui/notifications/host-context-changed',params:{displayMode:'fullscreen'}});
 assert.equal(f.bridge.canMessageCurrentConversation(),true);
 f.reply({jsonrpc:'2.0',method:'ui/notifications/host-context-changed',params:{toolInfo:{tool:{name:'nacos_open_center'}}}});
 assert.equal(f.bridge.canMessageCurrentConversation(),false);
});
test('handoff sends only the selected text, waits for acknowledgment and propagates refusal',async()=>{
 const f=fixture();f.bridge.host={hostCapabilities:{message:{text:{}}},hostContext:{displayMode:'inline',toolInfo:{tool:{name:'nacos_open_center_panel'}}}};
 const send=f.bridge.messageCurrentConversation('Use selected skill at /example/skill');
 assert.deepEqual(JSON.parse(JSON.stringify(f.outgoing[0].params)),{role:'user',content:[{type:'text',text:'Use selected skill at /example/skill'}]});
 assert.equal(f.outgoing[0].method,'ui/message'); // No new-conversation request or tools/call.
 f.reply({jsonrpc:'2.0',id:1,result:{}});await send;
 const denied=f.bridge.messageCurrentConversation('example');
 f.reply({jsonrpc:'2.0',id:2,error:{code:-32601,message:'No conversation'}});await assert.rejects(denied,{kind:'bridge'});
 const rejected=f.bridge.messageCurrentConversation('example');
 f.reply({jsonrpc:'2.0',id:3,result:{isError:true}});await assert.rejects(rejected,{kind:'bridge'});
});
test('bridge ignores requests and foreign messages, and supplies context',async()=>{
 const f=fixture(),p=f.bridge.call('status',{},'context'),r=f.outgoing[0];assert.equal(r.params.arguments._context,'context');
 f.reply(r);assert.equal(f.bridge.pending.size,1);f.foreign({jsonrpc:'2.0',id:r.id,result:{}});assert.equal(f.bridge.pending.size,1);
 f.reply({jsonrpc:'2.0',id:r.id,result:{structuredContent:{context:'context'}}});assert.equal((await p).context,'context');
});
test('bridge keeps structured conflict and uncertain operation evidence',async()=>{
 const f=fixture();let p=f.bridge.call('upload_plan'),r=f.outgoing.at(-1);
 f.reply({jsonrpc:'2.0',id:r.id,result:{isError:true,content:[{type:'text',text:JSON.stringify({error:'conflict',message:'bind',conflict:{requiresBind:true}})}]}});
 await assert.rejects(p,e=>e.kind==='conflict'&&e.value.conflict.requiresBind);
 p=f.bridge.call('apply');r=f.outgoing.at(-1);f.reply({jsonrpc:'2.0',id:r.id,result:{isError:true,structuredContent:{id:'op',status:'result_unknown'}}});assert.equal((await p).id,'op');
});
