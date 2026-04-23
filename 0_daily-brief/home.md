---
cssclasses:
  - dashboard
---

```dataviewjs
const C = {
  bg:'#1d2021', surface:'#282828', border:'#3c3836',
  cyan:'#89b482', purple:'#d3869b', green:'#a9b665',
  amber:'#e78a4e', red:'#ea6962', text:'#d4be98', muted:'#7c6f64',
  gcyan:'rgba(137,180,130,0.15)', gpurple:'rgba(211,134,155,0.15)',
};
const SCOL = { 'todo':C.muted,'in-progress':C.cyan,'waiting':C.amber,'done':C.green,'cancelled':C.red };
const PCOL = { 'urgent':C.red,'high':C.amber,'medium':C.cyan,'low':C.muted };

function slug2title(s) { return (s||'').split('-').map(w=>w?w[0].toUpperCase()+w.slice(1):'').join(' '); }
function todayStr()    { const d=new Date(); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); }
function fmtDue(due)   { return due?.toFormat ? due.toFormat('yyyy-MM-dd') : String(due).slice(0,10); }

const allTasks    = dv.pages('"tasks"').where(p=>!p.file.path.includes('tasks/archive/')&&p.tags&&(Array.isArray(p.tags)?p.tags.some(t=>t.replace('#','')=='task'):String(p.tags).includes('task'))).array();
const tokenPages  = dv.pages('"system/tokens"').where(p=>p.date&&p.total_tokens).sort(p=>p.date,'asc').array();
const today       = todayStr();
const todayMeetings = dv.pages('"meetings"').where(p=>p.file.name.startsWith(today)).sort(p=>p.file.name,'asc').array();
const now        = new Date();
const dateStr    = now.toLocaleDateString('en-GB',{weekday:'long',day:'numeric',month:'long',year:'numeric'});

const briefFile = app.vault.getAbstractFileByPath('0_daily-brief/daily-brief.md');
const briefRaw  = briefFile ? await app.vault.cachedRead(briefFile) : '';
function parseBrief(raw) {
  const s={};
  for(const part of raw.split(/^## /m).slice(1)){const nl=part.indexOf('\n');s[part.slice(0,nl).trim()]=part.slice(nl+1).trim();}
  return s;
}
const brief = parseBrief(briefRaw);

function listCards(content,color){
  const lines=(content||'').split('\n').filter(l=>l.trim()&&!l.startsWith('---'));
  if(!lines.length) return `<div style="font-size:.72em;color:${C.muted};font-style:italic;padding:4px 0">Nothing yet</div>`;
  return lines.map(l=>{
    const done=/~~|done/.test(l);
    const text=l.replace(/^\d+\.\s*/,'').replace(/^-\s*/,'')
      .replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>')
      .replace(/~~(.*?)~~/g,'<s style="opacity:.4">$1</s>')
      .replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g,(_,p,a)=>`<span style="color:${C.cyan};cursor:pointer" onclick="app.workspace.openLinkText('${p.replace(/'/g,"\\'")}','',false)">${a||slug2title(p)}</span>`);
    return `<div style="background:${C.bg};border:1px solid ${color}${done?'22':'44'};border-left:3px solid ${done?C.muted:color};border-radius:5px;padding:6px 10px;margin-bottom:5px;font-size:.78em;color:${done?C.muted:C.text};line-height:1.4">${text}</div>`;
  }).join('');
}

function tableCards(content,color){
  const rows=(content||'').split('\n').filter(l=>l.startsWith('|')&&!l.match(/^[\s|:-]+$/));
  if(rows.length<2) return listCards(content,color);
  const headers=rows[0].split('|').map(h=>h.trim().toLowerCase()).filter(Boolean);
  return rows.slice(1).map(row=>{
    const cells=row.split('|').map(c=>c.trim()).filter(Boolean);
    const obj=Object.fromEntries(headers.map((h,i)=>[h,cells[i]||'']));
    const taskRaw=obj['task']||'';
    const taskName=(taskRaw.match(/\[\[([^\]|]+)/)||[])[1]||taskRaw;
    const status=obj['status']||'',priority=obj['priority']||'',tag=obj['tag']||'',sprint=obj['sprint']||'';
    const sc=SCOL[status]||C.muted,pc=PCOL[priority]||C.muted,isDone=/done|✓/.test(status);
    return `<div class="db-brief-card" style="border:1px solid ${sc}33;border-left:3px solid ${isDone?C.muted:sc};${isDone?'opacity:.45':''}" onclick="app.workspace.openLinkText('${taskName.replace(/'/g,"\\'")}','',false)">
      <div style="font-size:.78em;color:${C.text};font-weight:600;margin-bottom:3px">${slug2title(taskName)}</div>
      <div style="display:flex;gap:5px;flex-wrap:wrap;align-items:center">
        ${tag?`<span style="font-size:.6em;padding:1px 5px;border-radius:3px;background:${C.border};color:${C.muted}">${tag.toUpperCase()}</span>`:''}
        ${priority?`<span style="font-size:.6em;padding:1px 5px;border-radius:3px;background:${pc}22;color:${pc};border:1px solid ${pc}44">${priority}</span>`:''}
        ${sprint&&sprint!=='—'?`<span style="font-size:.6em;padding:1px 5px;border-radius:3px;background:${C.cyan}22;color:${C.cyan}">${sprint}</span>`:''}
        <span style="font-size:.6em;padding:1px 5px;border-radius:3px;background:${sc}22;color:${sc};margin-left:auto">${status}</span>
      </div>
    </div>`;
  }).join('');
}

function briefCol(icon,heading,content,color,isTable=false){
  const cards=isTable?tableCards(content,color):listCards(content,color);
  const count=isTable?(content||'').split('\n').filter(l=>l.startsWith('|')&&!l.match(/^[\s|:-]+$/)).length-1:(content||'').split('\n').filter(l=>l.trim()&&!l.startsWith('---')).length;
  return `<div style="flex:1;min-width:0">
    <div style="font-size:.65em;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:${color};border-bottom:2px solid ${color};padding-bottom:5px;margin-bottom:8px;text-shadow:0 0 8px ${color}40">
      ${icon} ${heading} <span style="opacity:.55">(${Math.max(0,count)})</span>
    </div>
    <div style="max-height:260px;overflow-y:auto;padding-right:2px">${cards}</div>
  </div>`;
}

function briefLines(content, color) {
  const rows = (content||'').split('\n').filter(l=>l.startsWith('|')&&!l.match(/^[\s|:-]+$/));
  if (rows.length >= 2) {
    const headers = rows[0].split('|').map(h=>h.trim().toLowerCase()).filter(Boolean);
    const items = rows.slice(1).map(row => {
      const cells = row.split('|').map(c=>c.trim()).filter(Boolean);
      const obj = Object.fromEntries(headers.map((h,i)=>[h,cells[i]||'']));
      const taskRaw = obj['task']||'';
      const taskName = (taskRaw.match(/\[\[([^\]|]+)/)||[])[1]||taskRaw;
      const status = obj['status']||'', sc = SCOL[status]||C.muted;
      return `<div style="padding:5px 0 5px 10px;border-left:2px solid ${color}44;margin-bottom:5px;font-size:.8em;color:${C.text};line-height:1.4;cursor:pointer;display:flex;justify-content:space-between;align-items:center" onclick="app.workspace.openLinkText('${taskName.replace(/'/g,"\\'")}','',false)">
        <span>${slug2title(taskName)}</span>
        ${status?`<span style="font-size:.85em;color:${sc};margin-left:8px;white-space:nowrap">${status}</span>`:''}
      </div>`;
    });
    if (!items.length) return `<div style="font-size:.75em;color:${C.muted};font-style:italic;padding:2px 0 2px 10px">Nothing yet</div>`;
    return items.join('');
  }
  const lines = (content||'').split('\n').filter(l=>l.trim()&&!l.startsWith('---'));
  if (!lines.length) return `<div style="font-size:.75em;color:${C.muted};font-style:italic;padding:2px 0 2px 10px">Nothing yet</div>`;
  return lines.map(l => {
    const text = l.replace(/^\d+\.\s*/,'').replace(/^-\s*/,'')
      .replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>')
      .replace(/~~(.*?)~~/g,'<s style="opacity:.4">$1</s>')
      .replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g,(_,p,a)=>`<span style="color:${C.cyan};cursor:pointer" onclick="app.workspace.openLinkText('${p.replace(/'/g,"\\'")}','',false)">${a||slug2title(p)}</span>`);
    return `<div style="padding:5px 0 5px 10px;border-left:2px solid ${color}44;margin-bottom:5px;font-size:.8em;color:${C.text};line-height:1.4">${text}</div>`;
  }).join('');
}

function briefSection(icon, heading, content, color) {
  const rows = (content||'').split('\n').filter(l=>l.startsWith('|')&&!l.match(/^[\s|:-]+$/));
  const count = rows.length >= 2 ? rows.length - 1
    : (content||'').split('\n').filter(l=>l.trim()&&!l.startsWith('---')).length;
  return `<div style="margin-bottom:18px">
    <div style="font-size:.63em;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:${color};margin-bottom:7px;padding-bottom:4px;border-bottom:1px solid ${color}33">${icon} ${heading} <span style="opacity:.5">(${Math.max(0,count)})</span></div>
    ${briefLines(content, color)}
  </div>`;
}

// ── clickup ──
const cuCfg    = dv.page('system/clickup-config');
const cuToken  = cuCfg?.token || '';
const cuFolder = cuCfg?.sprints_folder_id || '901513280010';
const CU_STATUS = {'to do':C.muted,'open':C.muted,'in progress':C.cyan,'in review':C.purple,'done':C.green,'complete':C.green,'blocked':C.red,'on hold':C.amber};
const CU_PRI    = {'1':C.red,'2':C.amber,'3':C.cyan,'4':C.muted};

async function cuFetch(url){
  try{
    const{requestUrl}=require('obsidian');
    const r=await requestUrl({url,headers:{Authorization:cuToken},throw:false});
    console.log('cuFetch',r.status,url.split('?')[0],r.status!==200?JSON.stringify(r.json).slice(0,200):'');
    return r.status===200?r.json:null;
  }catch(e){console.error('cuFetch:',e);return null;}
}

let cuSprint=null,cuTasks=[];
if(cuToken&&cuToken!=='PASTE_YOUR_TOKEN_HERE'){
  const lists=await cuFetch(`https://api.clickup.com/api/v2/folder/${cuFolder}/list?archived=false`);
  if(lists?.lists?.length){
    cuSprint=lists.lists.map(l=>({...l,num:parseInt((l.name.match(/sprint\s*(\d+)/i)||[])[1]||0)})).sort((a,b)=>b.num-a.num)[0];
    if(cuSprint){
      const data=await cuFetch(`https://api.clickup.com/api/v2/list/${cuSprint.id}/task?page=0&include_closed=false`);
      cuTasks=data?.tasks||[];
    }
  }
}

function cuCard(task){
  const st=(task.status?.status||'').toLowerCase(),sc=CU_STATUS[st]||C.muted;
  const due=task.due_date?new Date(+task.due_date).toISOString().slice(5,10):'';
  const assignee=task.assignees?.[0]?.username||'';
  const url=task.url||`https://app.clickup.com/t/${task.id}`;
  return `<div class="db-card" style="border-left:3px solid ${sc}" onclick="window.open('${url}','_blank')">
    <div style="font-size:.78em;color:${C.text};font-weight:600;margin-bottom:5px;line-height:1.3">${task.name}</div>
    <div style="display:flex;gap:5px;align-items:center;flex-wrap:wrap">
      <span style="font-size:.6em;padding:1px 6px;border-radius:3px;background:${sc}22;color:${sc}">${st}</span>
      ${due?`<span style="font-size:.6em;color:${C.amber};margin-left:auto">📅 ${due}</span>`:''}
      ${assignee?`<span style="font-size:.6em;color:${C.muted}">${assignee}</span>`:''}
    </div>
  </div>`;
}

function cuCol(label,color,tasks){
  return `<div style="flex:1;min-width:0">
    <div class="db-col-hdr" style="color:${color};border-bottom:2px solid ${color};text-shadow:0 0 8px ${color}40">${label} <span style="opacity:.6">(${tasks.length})</span></div>
    <div style="max-height:300px;overflow-y:auto;padding-right:2px">
      ${tasks.length?tasks.map(cuCard).join(''):`<div style="font-size:.72em;color:${C.muted};padding:8px 0;font-style:italic">All clear ✓</div>`}
    </div>
  </div>`;
}

function cuSprintBoard(){
  if(!cuToken||cuToken==='PASTE_YOUR_TOKEN_HERE') return `<div style="color:${C.amber};font-size:.8em;padding:8px">Add token to <span style="color:${C.cyan};cursor:pointer" onclick="app.workspace.openLinkText('system/clickup-config','',false)">system/clickup-config.md</span></div>`;
  if(!cuSprint) return `<div style="color:${C.muted};font-size:.8em;padding:8px">Could not fetch sprint — check token.</div>`;
  const todo=cuTasks.filter(t=>['to do','open'].includes((t.status?.status||'').toLowerCase()));
  const inProg=cuTasks.filter(t=>(t.status?.status||'').toLowerCase()==='in progress');
  const inRev=cuTasks.filter(t=>(t.status?.status||'').toLowerCase()==='in review');
  const done=cuTasks.filter(t=>['done','complete','closed'].includes((t.status?.status||'').toLowerCase()));
  const pct=cuTasks.length?Math.round((done.length/cuTasks.length)*100):0;
  return `<div style="display:flex;align-items:center;gap:16px;margin-bottom:12px">
    <div style="font-size:.82em;font-weight:700;color:${C.cyan}">${cuSprint.name}</div>
    <div style="flex:1;height:5px;background:${C.border};border-radius:3px;overflow:hidden">
      <div style="height:100%;width:${pct}%;background:linear-gradient(90deg,${C.cyan},${C.purple});box-shadow:0 0 8px ${C.gcyan}"></div>
    </div>
    <div style="font-size:.72em;color:${C.muted}">${done.length}/${cuTasks.length} · <span style="color:${C.cyan}">${pct}%</span></div>
  </div>
  <div style="display:flex;gap:12px">
    ${cuCol('TODO',C.muted,todo)}${cuCol('IN PROGRESS',C.cyan,inProg)}${cuCol('IN REVIEW',C.purple,inRev)}${cuCol('DONE',C.green,done)}
  </div>`;
}

// ── stats ──
const active    = allTasks.filter(t=>t.status==='in-progress');
const waiting   = allTasks.filter(t=>t.status==='waiting');
const overdue   = allTasks.filter(t=>t.due&&fmtDue(t.due)<today&&!['done','cancelled'].includes(t.status));
const sprintAll  = allTasks.filter(t=>t.clickup_list==='sprint');
const sprintDone = sprintAll.filter(t=>t.status==='done').length;
const sprintPct  = sprintAll.length?Math.round((sprintDone/sprintAll.length)*100):0;
const totalWork  = allTasks.filter(t=>!(t.tags||[]).includes('personal')).length;
const doneWork   = allTasks.filter(t=>t.status==='done'&&!(t.tags||[]).includes('personal')).length;
const donePct    = totalWork?Math.round((doneWork/totalWork)*100):0;
const todayTok   = tokenPages.find(t=>t.file.stem===today);
const week7Cost  = tokenPages.slice(-7).reduce((s,t)=>s+(t.cost_usd||0),0);

function ring(pct,color,label,sub){
  const r=28,circ=2*Math.PI*r,dash=(pct/100)*circ;
  return `<div class="db-ring">
    <svg width="72" height="72" viewBox="0 0 72 72">
      <circle cx="36" cy="36" r="${r}" fill="none" stroke="${C.border}" stroke-width="5"/>
      <circle cx="36" cy="36" r="${r}" fill="none" stroke="${color}" stroke-width="5" stroke-dasharray="${dash.toFixed(1)} ${circ.toFixed(1)}" stroke-linecap="round" transform="rotate(-90 36 36)" style="filter:drop-shadow(0 0 6px ${color})"/>
      <text x="36" y="40" text-anchor="middle" font-size="13" font-weight="700" fill="${color}" font-family="monospace">${pct}%</text>
    </svg>
    <div style="font-size:.7em;color:${C.text};font-weight:600;text-align:center">${label}</div>
    <div style="font-size:.65em;color:${C.muted}">${sub}</div>
  </div>`;
}

function projectBars(){
  const proj={};
  allTasks.filter(t=>!(t.tags||[]).includes('personal')&&t.status!=='cancelled')
    .forEach(t=>(t.tags||[]).map(x=>x.replace('#','')).filter(x=>!['task','idea','itu','vault','personal','comms','work'].includes(x))
      .forEach(tag=>{
        if(!proj[tag]) proj[tag]={total:0,done:0,active:0};
        proj[tag].total++;
        if(t.status==='done') proj[tag].done++;
        if(t.status==='in-progress') proj[tag].active++;
      }));
  const rows=Object.entries(proj).filter(([,v])=>v.total>1).sort((a,b)=>b[1].total-a[1].total).slice(0,6);
  if(!rows.length) return `<div style="color:${C.muted};font-size:.8em">No projects found</div>`;
  return rows.map(([tag,v])=>{
    const pct=Math.round((v.done/v.total)*100);
    return `<div class="db-proj" onclick="app.workspace.openLinkText('${tag}','',false)">
      <div style="display:flex;justify-content:space-between;margin-bottom:4px">
        <span style="font-size:.75em;color:${C.text};font-weight:600">${tag.toUpperCase()}</span>
        <span style="font-size:.68em;color:${C.muted}">${v.done}/${v.total} · <span style="color:${C.cyan}">${v.active} active</span></span>
      </div>
      <div style="height:6px;background:${C.border};border-radius:3px;overflow:hidden">
        <div class="db-bar-fill" style="height:100%;width:${pct}%;background:linear-gradient(90deg,${C.cyan},${C.purple});border-radius:3px;box-shadow:0 0 8px ${C.gcyan}"></div>
      </div>
    </div>`;
  }).join('');
}

function tokenChart(){
  const last7=tokenPages.slice(-7);
  if(!last7.length) return `<div style="color:${C.muted};font-size:.8em">No token data yet</div>`;
  const max=Math.max(...last7.map(t=>t.total_tokens||0),1),W=34,G=8,H=70;
  const bars=last7.map((t,i)=>{
    const bh=Math.max(4,((t.total_tokens||0)/max)*H),x=i*(W+G),y=H-bh,day=(t.file?.stem||'').slice(5);
    const k=Math.round((t.total_tokens||0)/1000),isToday=t.file?.stem===today,col=isToday?C.purple:C.cyan;
    return `<rect x="${x}" y="${y}" width="${W}" height="${bh}" rx="3" fill="${col}" fill-opacity="0.7" style="filter:drop-shadow(0 0 4px ${col})"/>
      <text x="${x+W/2}" y="${H+13}" text-anchor="middle" font-size="9" fill="${C.muted}">${day}</text>
      ${k?`<text x="${x+W/2}" y="${y-5}" text-anchor="middle" font-size="8" fill="${col}">${k}k</text>`:''}`;
  }).join('');
  return `<svg width="${last7.length*(W+G)-G}" height="${H+20}" style="overflow:visible">${bars}</svg>`;
}

function networkChips(){
  const rl=app.metadataCache.resolvedLinks,counts={};
  for(const links of Object.values(rl)) for(const[to,n]of Object.entries(links)) counts[to]=(counts[to]||0)+n;
  return Object.entries(counts).filter(([p])=>!p.startsWith('.obsidian')&&!p.startsWith('system/tokens'))
    .sort((a,b)=>b[1]-a[1]).slice(0,14).map(([path,count])=>{
      const name=path.split('/').pop().replace(/\.md$/,'');
      return `<span class="db-chip" style="border:1px solid ${count>5?C.cyan:C.border};color:${count>5?C.cyan:C.muted};background:${C.surface}" onclick="app.workspace.openLinkText('${name.replace(/'/g,"\\'")}','',false)">${slug2title(name)} <sup style="opacity:.5">${count}</sup></span>`;
    }).join('');
}

// ── SVG icons ──
const SVG = {
  daily:    '<path d="M8 2v3M16 2v3M3.5 9.09h17M21 8.5V17c0 3-1.5 5-5 5H8c-3.5 0-5-2-5-5V8.5c0-3 1.5-5 5-5h8c3.5 0 5 2 5 5z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
  task:     '<path d="M9 11l3 3L22 4M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
  meeting:  '<path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="1.5"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
  brief:    '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
  clickup:  '<path d="M3 9l4 4 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M3 15l4 4 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M14 5l4 4 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M14 11l4 4 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
  terminal: '<polyline points="4 17 10 11 4 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><line x1="12" y1="19" x2="20" y2="19" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
  claude:   '<defs><linearGradient id="cld-px" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#e8a070"/><stop offset="55%" stop-color="#c05040"/><stop offset="100%" stop-color="#d46868"/></linearGradient></defs><path d="M3 1L21 1L21 3L23 3L23 19L18 19L18 24L6 24L6 19L1 19L1 3L3 3Z" fill="url(#cld-px)"/><rect x="6" y="8" width="4" height="4" fill="#180806"/><rect x="14" y="8" width="4" height="4" fill="#180806"/>',
  journal:  '<path d="M4 19.5A2.5 2.5 0 016.5 17H20M4 19.5V4.5A2.5 2.5 0 016.5 2H20v20H6.5A2.5 2.5 0 014 19.5z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
  crm:      '<circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="1.5"/><path d="M20 21a8 8 0 10-16 0" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
  idea:     '<circle cx="12" cy="12" r="5" stroke="currentColor" stroke-width="1.5" fill="none"/><path d="M12 2v2M12 20v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M2 12h2M20 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
};

function svgIconBtn(svgPath,label,color,id='',onclickStr=''){
  return `<div class="db-icon-btn"${id?` id="${id}"`:''}${onclickStr?` onclick="${onclickStr}"`:''}><svg class="db-icon-svg" style="color:${color}" viewBox="0 0 24 24" fill="none">${svgPath}</svg><span class="db-icon-label">${label}</span></div>`;
}

// native modal input — prompt() is unreliable in Obsidian's renderer
const { Modal } = require('obsidian');
class InputModal extends Modal {
  constructor(app, heading, placeholder, cb) {
    super(app); this._h=heading; this._p=placeholder; this._cb=cb;
  }
  onOpen() {
    this.contentEl.createEl('h2',{text:this._h,attr:{style:'margin-bottom:10px;font-size:1.05em'}});
    const inp = this.contentEl.createEl('input',{type:'text',placeholder:this._p,
      attr:{style:'width:100%;padding:8px 12px;border-radius:6px;border:1px solid var(--background-modifier-border);background:var(--background-primary);color:var(--text-normal);font-size:.95em;outline:none;box-sizing:border-box'}});
    inp.focus();
    const submit = () => { const v=inp.value.trim(); if(v) this._cb(v); this.close(); };
    inp.addEventListener('keydown', e => { if(e.key==='Enter') submit(); if(e.key==='Escape') this.close(); });
    const btn = this.contentEl.createEl('button',{text:'Create',
      attr:{style:'margin-top:10px;padding:7px 20px;border-radius:6px;background:var(--interactive-accent);color:var(--text-on-accent);border:none;cursor:pointer;font-weight:600;font-size:.9em'}});
    btn.addEventListener('click', submit);
  }
  onClose() { this.contentEl.empty(); }
}

function tmplCard(icon,title,desc,id,btnLabel,btnColor){
  return `<div class="db-tmpl">
    <div class="db-tmpl-title">${icon} ${title}</div>
    <div class="db-tmpl-desc">${desc}</div>
    <span id="${id}" class="db-tmpl-btn" style="color:${btnColor};border-color:${btnColor}55;background:${btnColor}0e">${btnLabel}</span>
  </div>`;
}

// nav helper: TFolder has .children, TFile has .extension
window._vaultNav = path => {
  const f = app.vault.getAbstractFileByPath(path);
  if (!f) { new Notice('Not found: ' + path); return; }
  if (f.children !== undefined) {
    // It's a folder — reveal in Obsidian file explorer sidebar
    const feLeaf = app.workspace.getLeavesOfType('file-explorer')[0];
    if (feLeaf) { app.workspace.revealLeaf(feLeaf); feLeaf.view.revealInFolder(f); }
  } else {
    app.workspace.getLeaf().openFile(f);
  }
};

window._openClaude = async () => {
  if (!termCmd) { new Notice('No terminal plugin found'); return; }
  app.commands.executeCommandById(termCmd);
  // Wait for terminal + xterm.js to fully initialise
  await new Promise(r => setTimeout(r, 1500));

  // Terminal opens as a floating window — not a workspace leaf.
  // xterm.js uses a hidden textarea for keyboard input; dispatch keydown events to it.
  const tas = document.querySelectorAll('.xterm-helper-textarea');
  const ta = tas[tas.length - 1]; // last = most recently opened terminal
  if (!ta) { new Notice('Terminal opened — type "claude" to start'); return; }

  ta.focus();
  await new Promise(r => setTimeout(r, 100));

  // xterm.js ignores synthetic keydown for printable chars; paste event is handled directly
  const dt = new DataTransfer();
  dt.setData('text/plain', 'claude');
  ta.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true}));

  await new Promise(r => setTimeout(r, 50));
  ta.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true}));
};

const termCmd = Object.keys(app.commands.commands).find(k=>k.startsWith('terminal:')&&k.includes('integrated'))
  || Object.keys(app.commands.commands).find(k=>k.startsWith('terminal:')&&k.includes('open'))
  || Object.keys(app.commands.commands).find(k=>k.startsWith('terminal:')) || '';

// ── render ──
const html = `
<style>
.dashboard .metadata-container,.dashboard .inline-title,.dashboard .embedded-backlinks{display:none!important}
#oz-dash *{box-sizing:border-box}
#oz-dash ::-webkit-scrollbar{width:4px}
#oz-dash ::-webkit-scrollbar-track{background:${C.surface}}
#oz-dash ::-webkit-scrollbar-thumb{background:${C.border};border-radius:2px}
#oz-dash{background:${C.bg};color:${C.text};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:0;border-radius:10px;overflow:visible;min-height:90vh}
.db-sec{background:${C.surface};border:1px solid ${C.border};border-radius:8px;padding:14px 16px;transition:border-color .2s,box-shadow .2s}
.db-sec:hover{box-shadow:0 0 16px ${C.amber}0a}
.db-ttl{font-size:.68em;font-weight:800;letter-spacing:.1em;text-transform:uppercase;margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid ${C.border}}
@keyframes warm-pulse{from{text-shadow:0 0 8px ${C.amber}99,0 0 16px ${C.amber}44}to{text-shadow:0 0 18px ${C.amber}cc,0 0 36px ${C.amber}55}}
#db-clock{animation:warm-pulse 3s ease-in-out infinite alternate}
.db-stat-chip{display:inline-flex;align-items:center;gap:7px;padding:6px 14px;border-radius:8px;border:1px solid transparent;cursor:default}
.db-search-input{width:100%;background:${C.surface};border:1px solid ${C.border};border-radius:20px;padding:8px 16px 8px 36px;color:${C.text};font-size:.82em;outline:none;transition:border-color .2s,box-shadow .2s}
.db-search-input:focus{border-color:${C.cyan}88;box-shadow:0 0 14px ${C.cyan}22}
.db-search-input::placeholder{color:${C.muted}}
.db-search-results{position:absolute;top:calc(100% + 6px);left:0;right:0;background:${C.surface};border:1px solid ${C.border};border-radius:12px;z-index:200;overflow:hidden;display:none;box-shadow:0 8px 24px rgba(0,0,0,.6)}
.db-search-result{padding:8px 14px;cursor:pointer;transition:background .12s}
.db-search-result:hover{background:${C.cyan}18}
.db-icon-grid{display:flex;gap:8px;margin-bottom:16px}
.db-icon-btn{flex:1;display:flex;flex-direction:column;align-items:center;gap:9px;padding:24px 12px;border-radius:10px;cursor:pointer;border:1px solid ${C.border};background:${C.surface};transition:transform .15s,border-color .15s,box-shadow .15s;min-width:0}
.db-icon-btn:hover{transform:translateY(-3px) scale(1.04);border-color:currentColor;box-shadow:0 4px 16px rgba(0,0,0,.3)}
.db-icon-svg{width:36px;height:36px;transition:filter .2s}
.db-icon-btn:hover .db-icon-svg{filter:drop-shadow(0 0 6px currentColor)}
.db-icon-label{font-size:.76em;font-weight:600;color:${C.muted};white-space:nowrap;transition:color .15s;text-align:center}
.db-icon-btn:hover .db-icon-label{color:${C.text}}
.db-card{background:${C.bg};border:1px solid ${C.border};border-radius:6px;padding:8px 10px;margin-bottom:6px;cursor:pointer;transition:transform .15s,border-color .15s,box-shadow .15s}
.db-card:hover{transform:translateY(-1px);border-color:${C.cyan}55;box-shadow:0 0 10px ${C.cyan}18,0 2px 8px rgba(0,0,0,.3)}
.db-brief-card{background:${C.bg};border-radius:5px;padding:6px 10px;margin-bottom:5px;cursor:pointer;transition:transform .15s,box-shadow .15s,border-color .15s}
.db-brief-card:hover{transform:translateY(-1px);box-shadow:0 0 8px ${C.amber}22}
.db-proj{margin-bottom:10px;cursor:pointer;padding:6px 8px;border-radius:6px;transition:background .15s}
.db-proj:hover{background:${C.amber}08}
.db-proj:hover .db-bar-fill{box-shadow:0 0 10px ${C.amber}66!important}
.db-chip{display:inline-block;padding:3px 9px;margin:3px;border-radius:20px;cursor:pointer;font-size:.72em;transition:transform .15s,box-shadow .15s}
.db-chip:hover{transform:scale(1.06);box-shadow:0 0 8px ${C.cyan}44}
.db-ring{display:flex;flex-direction:column;align-items:center;gap:4px;transition:transform .2s}
.db-ring:hover{transform:scale(1.05)}
.db-col-hdr{font-size:.68em;font-weight:800;letter-spacing:.09em;padding-bottom:5px;margin-bottom:8px}
.db-tmpl{background:${C.bg};border:1px solid ${C.border};border-radius:8px;padding:10px 12px;margin-bottom:8px;transition:transform .15s,border-color .15s,box-shadow .15s}
.db-tmpl:hover{border-color:${C.amber}44;box-shadow:0 0 10px ${C.amber}18;transform:translateY(-1px)}
.db-tmpl-title{font-size:.8em;font-weight:700;color:${C.text};margin-bottom:3px}
.db-tmpl-desc{font-size:.7em;color:${C.muted};line-height:1.4;margin-bottom:8px}
.db-tmpl-btn{font-size:.68em;padding:4px 12px;border-radius:6px;cursor:pointer;font-weight:700;transition:filter .15s;border:1px solid transparent;display:inline-block}
.db-tmpl-btn:hover{filter:brightness(1.3)}
.db-divider{height:1px;background:linear-gradient(to right,transparent,${C.border},${C.cyan}55,${C.border},transparent);margin:0 0 16px;box-shadow:0 0 6px ${C.cyan}18}
</style>

<div style="padding:16px 20px 0;overflow:visible" id="oz-dash">

  <!-- HEADER -->
  <div style="background:linear-gradient(135deg,${C.surface},${C.bg});border:1px solid ${C.border};border-radius:10px;padding:16px 20px;margin-bottom:16px">
    <div style="display:flex;align-items:flex-start;gap:16px;flex-wrap:wrap">

      <!-- Clock + greeting -->
      <div style="flex-shrink:0;min-width:160px">
        <span id="db-clock" style="font-size:2.8em;font-weight:800;color:${C.amber};font-family:monospace;letter-spacing:.04em;line-height:1">--:--:--</span>
        <div id="db-greet" style="font-size:.82em;color:${C.text};font-weight:500;margin-top:4px"></div>
        <div style="font-size:.7em;color:${C.muted};margin-top:2px">${dateStr}</div>
      </div>

      <!-- Status chips -->
      <div style="flex:1;display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding-top:6px">
        ${cuSprint ? `<div class="db-stat-chip" style="border-color:${C.green}55;background:${C.green}0e">
          <span style="font-size:.8em;font-weight:700;color:${C.green}">${cuSprint.name}</span>
          <span style="font-size:.75em;color:${C.muted}">${Math.round((cuTasks.filter(t=>['done','complete','closed'].includes((t.status?.status||'').toLowerCase())).length/(cuTasks.length||1))*100)}%</span>
        </div>` : ''}
      </div>

      <!-- Search -->
      <div id="db-search-wrap" style="flex:1;position:relative;flex-shrink:0">
        <div style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:${C.muted};font-size:.8em;pointer-events:none">🔍</div>
        <input id="db-search" class="db-search-input" placeholder="Search vault..." autocomplete="off" spellcheck="false"/>
        <div id="db-search-results" class="db-search-results"></div>
      </div>

    </div>
  </div>

  <!-- SVG QUICK NAV -->
  <div class="db-icon-grid">
    ${svgIconBtn(SVG.brief,   'Brief',    C.green,  '', "_vaultNav('0_daily-brief/daily-brief.md')")}
    ${svgIconBtn(SVG.daily,   'Daily',    C.cyan,   'db-icon-daily',  '')}
    ${termCmd ? svgIconBtn(SVG.claude, 'Claude', C.purple, '', `window._openClaude()`) : ''}
    ${svgIconBtn(SVG.clickup, 'ClickUp',  C.amber,  '', "window.open('https://app.clickup.com')")}
  </div>

  <!-- STATS ROW -->
  <div class="db-sec" style="display:flex;gap:20px;align-items:center;justify-content:space-around;flex-wrap:wrap;padding:16px;margin-bottom:16px">
    ${cuTasks.length
      ? ring(Math.round((cuTasks.filter(t=>['done','complete','closed'].includes((t.status?.status||'').toLowerCase())).length/cuTasks.length)*100),C.cyan,cuSprint?.name||'Sprint',`${cuTasks.filter(t=>['done','complete','closed'].includes((t.status?.status||'').toLowerCase())).length}/${cuTasks.length} done`)
      : ring(sprintPct,C.cyan,'Sprint',`${sprintDone}/${sprintAll.length} done`)}
    ${ring(donePct,C.purple,'All Tasks',`${doneWork}/${totalWork} done`)}
    <div style="display:flex;flex-direction:column;gap:10px">
      <div style="display:flex;align-items:center;gap:10px"><div style="width:8px;height:8px;border-radius:50%;background:${C.cyan};box-shadow:0 0 6px ${C.cyan}"></div><span style="font-size:.8em;color:${C.muted}">In progress</span><span style="font-size:1.1em;font-weight:700;color:${C.cyan};margin-left:auto">${active.length}</span></div>
      <div style="display:flex;align-items:center;gap:10px"><div style="width:8px;height:8px;border-radius:50%;background:${C.amber};box-shadow:0 0 6px ${C.amber}"></div><span style="font-size:.8em;color:${C.muted}">Waiting</span><span style="font-size:1.1em;font-weight:700;color:${C.amber};margin-left:auto">${waiting.length}</span></div>
      <div style="display:flex;align-items:center;gap:10px"><div style="width:8px;height:8px;border-radius:50%;background:${C.red};box-shadow:0 0 6px ${C.red}"></div><span style="font-size:.8em;color:${C.muted}">Overdue</span><span style="font-size:1.1em;font-weight:700;color:${C.red};margin-left:auto">${overdue.length}</span></div>
    </div>
  </div>

  <!-- MAIN GRID -->
  <div style="display:flex;flex-direction:column;gap:14px;margin-bottom:16px">

    <div class="db-sec">
      <div class="db-ttl" style="color:${C.cyan}">⚡ Sprint Board
        ${cuSprint?`<span style="float:right;font-size:.75em;color:${C.muted};cursor:pointer;font-weight:400" onclick="window.open('https://app.clickup.com/${cuCfg?.workspace_id||''}','_blank')">open in ClickUp →</span>`:''}
      </div>
      ${cuSprintBoard()}
    </div>

    <div style="display:grid;grid-template-columns:4fr 1fr;gap:14px;align-items:start">
      <div class="db-sec">
        <div class="db-ttl" style="color:${C.green}">📋 Daily Brief
          <span onclick="_vaultNav('0_daily-brief/daily-brief.md')" style="float:right;font-size:.75em;color:${C.muted};cursor:pointer;font-weight:400;letter-spacing:0">open →</span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:28px">
          <div>
            ${briefSection('🎯','Priorities', brief["Today's Priorities"], C.cyan)}
            ${briefSection('❓','Questions', brief['Questions for User'], C.purple)}
          </div>
          <div>
            ${briefSection('⚡','Attention', brief['Tasks Needing Attention'], C.amber)}
            ${(()=>{
              const meetItems = todayMeetings.length
                ? todayMeetings.map(p=>`<div style="padding:5px 0 5px 10px;border-left:2px solid ${C.amber}44;margin-bottom:5px;font-size:.8em;color:${C.text};line-height:1.4;cursor:pointer" onclick="app.workspace.openLinkText('${p.file.name.replace(/'/g,"\\'")}','',false)">${p.file.name.slice(11)}</div>`).join('')
                : `<div style="font-size:.75em;color:${C.muted};font-style:italic;padding:2px 0 2px 10px">No meetings today</div>`;
              return `<div style="margin-bottom:18px">
                <div style="font-size:.63em;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:${C.amber};margin-bottom:7px;padding-bottom:4px;border-bottom:1px solid ${C.amber}33">📅 Meetings <span style="opacity:.5">(${todayMeetings.length})</span></div>
                ${meetItems}
              </div>`;
            })()}
          </div>
        </div>
      </div>
      <div class="db-sec">
        <div class="db-ttl" style="color:${C.amber}">📄 Quick Create</div>
        ${tmplCard('🗓','Meeting Note','Agenda, attendees, action items','db-tmpl-meeting','+ Create',C.amber)}
        ${tmplCard('📖','Journal Entry','Evergreen note on a topic','db-tmpl-journal','+ Create',C.purple)}
        ${tmplCard('👤','CRM Contact','Person or company note','db-tmpl-crm','+ Create',C.cyan)}
      </div>
    </div>

    <!-- CHANGELOG -->
    <div class="db-sec">
      <div class="db-ttl" style="color:${C.muted}">📜 Changelog
        <span onclick="_vaultNav('0_daily-brief/daily-brief.md')" style="float:right;font-size:.75em;color:${C.muted};cursor:pointer;font-weight:400;letter-spacing:0">open brief →</span>
      </div>
      ${briefLines(brief['Changelog'], C.muted)}
    </div>

  </div>

  <!-- FOOTER -->
  <div style="border-top:1px solid ${C.border};padding:10px 0;display:flex;justify-content:space-between;font-size:.68em;color:${C.muted};margin-bottom:8px">
    <span>ozv2 · ${allTasks.length} tasks · ${sprintAll.length} in sprint</span>
    <span>Rendered ${now.toLocaleTimeString()}</span>
  </div>
</div>`;

dv.container.innerHTML = html;

// ── template helper: read template file, substitute tags, create note ──
async function createFromTemplate(tmplPath, destPath, title) {
  const tmplFile = app.vault.getAbstractFileByPath(tmplPath);
  let content = tmplFile ? await app.vault.read(tmplFile) : '';
  content = content
    .replace(/<%[-~]?\s*tp\.date\.now\(["']YYYY-MM-DD["']\)\s*[-~]?%>/g, today)
    .replace(/<%[-~]?\s*tp\.file\.title\s*[-~]?%>/g, title);
  return await app.vault.create(destPath, content);
}

// ── daily note: open if exists, create from template if not ──
dv.container.querySelector('#db-icon-daily')?.addEventListener('click', async () => {
  const path = '1_inbox/' + today + '.md';
  let file = app.vault.getAbstractFileByPath(path);
  if (!file) file = await createFromTemplate('system/templates/daily-note.md', path, today);
  app.workspace.getLeaf().openFile(file);
});

// ── new task ──
dv.container.querySelector('#db-new-task')?.addEventListener('click', () => {
  new InputModal(app, 'New Task', 'e.g. review proposal draft', async raw => {
    const s = raw.toLowerCase().trim().replace(/\s+/g,'-').replace(/[^a-z0-9-]/g,'');
    if (!s) return;
    const path = 'tasks/'+s+'.md';
    const existing = app.vault.getAbstractFileByPath(path);
    if (existing) { app.workspace.getLeaf().openFile(existing); return; }
    const f = await createFromTemplate('system/templates/task.md', path, s);
    app.workspace.getLeaf().openFile(f);
  }).open();
});

// ── new meeting ──
const _newMeeting = () => {
  new InputModal(app, 'New Meeting', 'e.g. team sync', async desc => {
    const name = today + ' ' + desc;
    const path = 'meetings/' + name + '.md';
    if (!app.vault.getAbstractFileByPath('meetings')) await app.vault.createFolder('meetings');
    const existing = app.vault.getAbstractFileByPath(path);
    if (existing) { app.workspace.getLeaf().openFile(existing); return; }
    const f = await createFromTemplate('system/templates/meeting.md', path, name);
    app.workspace.getLeaf().openFile(f);
  }).open();
};
dv.container.querySelector('#db-new-meeting')?.addEventListener('click', _newMeeting);
dv.container.querySelector('#db-tmpl-meeting')?.addEventListener('click', _newMeeting);

// ── new journal entry ──
dv.container.querySelector('#db-tmpl-journal')?.addEventListener('click', () => {
  new InputModal(app, 'Journal Topic', 'e.g. barcelona move', async topic => {
    const slug = topic.toLowerCase().trim().replace(/\s+/g,'-').replace(/[^a-z0-9-]/g,'');
    const name = 'journal-'+slug;
    const path = '2_for-review/'+name+'.md';
    const existing = app.vault.getAbstractFileByPath(path);
    if (existing) { app.workspace.getLeaf().openFile(existing); return; }
    const f = await createFromTemplate('system/templates/journal.md', path, topic);
    app.workspace.getLeaf().openFile(f);
  }).open();
});

// ── new CRM contact ──
dv.container.querySelector('#db-tmpl-crm')?.addEventListener('click', () => {
  new InputModal(app, 'New Contact', 'Full name', async name => {
    const slug = name.toLowerCase().trim().replace(/\s+/g,'-').replace(/[^a-z0-9-]/g,'');
    const path = 'CRM/people/'+slug+'.md';
    const existing = app.vault.getAbstractFileByPath(path);
    if (existing) { app.workspace.getLeaf().openFile(existing); return; }
    const f = await createFromTemplate('system/templates/crm-contact.md', path, name);
    app.workspace.getLeaf().openFile(f);
  }).open();
});

// ── vault searchbar ──
const searchInput = dv.container.querySelector('#db-search');
const searchResults = dv.container.querySelector('#db-search-results');
if (searchInput) {
  const doSearch = q => {
    if (!q.trim()) { searchResults.style.display='none'; return; }
    const ql = q.toLowerCase();
    const files = app.vault.getFiles()
      .filter(f => !f.path.startsWith('.obsidian') && !f.path.startsWith('system/tokens') && f.path.toLowerCase().includes(ql))
      .sort((a,b) => {
        const an=a.basename.toLowerCase().includes(ql)?0:1, bn=b.basename.toLowerCase().includes(ql)?0:1;
        return an-bn;
      }).slice(0,8);
    if (!files.length) { searchResults.style.display='none'; return; }
    searchResults.innerHTML = files.map(f =>
      `<div class="db-search-result" data-path="${f.path}">
        <div style="font-size:.8em;font-weight:600;color:#d4be98">${f.basename}</div>
        <div style="font-size:.68em;color:#7c6f64">${f.parent?.path||''}</div>
      </div>`
    ).join('');
    searchResults.style.display = 'block';
    searchResults.querySelectorAll('.db-search-result').forEach(el => {
      el.addEventListener('click', () => {
        app.workspace.openLinkText(el.dataset.path,'',false);
        searchInput.value=''; searchResults.style.display='none';
      });
    });
  };
  searchInput.addEventListener('input', e => doSearch(e.target.value));
  searchInput.addEventListener('keydown', e => { if(e.key==='Escape'){searchInput.value='';searchResults.style.display='none';} });
  document.addEventListener('click', e => {
    if (!dv.container.querySelector('#db-search-wrap')?.contains(e.target)) searchResults.style.display='none';
  });
}

// ── live clock ──
const tick = () => {
  const n=new Date(),t=[n.getHours(),n.getMinutes(),n.getSeconds()].map(v=>String(v).padStart(2,'0')).join(':');
  const cl=dv.container.querySelector('#db-clock'); if(cl) cl.textContent=t;
  const gr=dv.container.querySelector('#db-greet'); if(gr){const h=n.getHours();gr.textContent=h<12?'🌅 Good morning, Oz':h<17?'☀️ Good afternoon, Oz':'🌙 Good evening, Oz';}
};
tick(); setInterval(tick,1000);
```
