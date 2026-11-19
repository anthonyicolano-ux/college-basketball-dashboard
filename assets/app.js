'use strict';
const $ = id => document.getElementById(id);
const mode = document.body.dataset.mode;
const columns = mode === 'players' ? [
 ['name','Player','text'],['team','Team','text'],['conference','Conf.','text'],['games','GP'],['minutes','MIN'],['points','PTS'],['rebounds','REB'],['offRebounds','OREB'],['defRebounds','DREB'],['assists','AST'],['steals','STL'],['blocks','BLK'],['turnovers','TO'],['fgMade','FGM'],['fgAttempted','FGA'],['fgPct','FG%'],['threeMade','3PM'],['threeAttempted','3PA'],['threePct','3P%'],['ftMade','FTM'],['ftAttempted','FTA'],['ftPct','FT%']
] : [
 ['team','Team','text'],['conference','Conf.','text'],['wins','W'],['losses','L'],['games','GP'],['ppg','PPG'],['oppPpg','Opp PPG'],['offRating','Off/100'],['defRating','Def/100'],['netRating','Net/100'],['scoringMargin','Margin/G'],['pace','Pace'],['fgPct','FG%'],['threePct','3P%'],['ftPct','FT%'],['eFg','eFG%'],['tsPct','TS%'],['rebounds','REB/G'],['offRebounds','OREB/G'],['defRebounds','DREB/G'],['oppRebounds','Opp REB/G'],['reboundingMargin','REB Margin'],['assists','AST/G'],['turnovers','TO/G']
];
let rows = [], currentSort = mode === 'players' ? 'points' : 'offRating', ascending = false, perGame = true;
const number = v => (typeof v === 'number' && Number.isFinite(v)) ? v : null;
function render(){
 const filter = $('search').value.trim().toLowerCase(); const conf = $('conference').value; const minGames = Number($('minGames')?.value || 0); const team = mode === 'players' ? $('team').value : '';
 const filtered = rows.filter(r=>(Number(r.games) >= minGames) && (!conf || r.conference === conf) && (!team || r.team === team) && (!filter || `${r.name||''} ${r.team||''} ${r.conference||''}`.toLowerCase().includes(filter)));
 const sorted = [...filtered].sort((a,b)=>{const va=displayValue(a,currentSort),vb=displayValue(b,currentSort);const missingA=va==null,missingB=vb==null;if(missingA||missingB)return Number(missingA)-Number(missingB);const cmp=typeof va === 'string' ? String(va).localeCompare(String(vb)) : va-vb;return ascending?cmp:-cmp;});
 $('count').textContent = `${filtered.length} ${mode === 'players' ? 'players' : 'teams'}`;
 const head=$('head');head.replaceChildren();const hr=document.createElement('tr');columns.forEach(([key,label])=>{const th=document.createElement('th');th.scope='col';const b=document.createElement('button');b.className='sort';b.textContent=label+(currentSort===key?(ascending?' ↑':' ↓'):'');b.addEventListener('click',()=>{if(currentSort===key)ascending=!ascending;else{currentSort=key;ascending=key==='team'||key==='name'||key==='conference'}render()});th.append(b);hr.append(th)});head.append(hr);
 const body=$('body');body.replaceChildren();for(const r of sorted){const tr=document.createElement('tr');for(const [key,,type] of columns){const td=document.createElement('td');const v=displayValue(r,key);td.textContent=v==null?'—':type==='text'?String(v):['games','wins','losses'].includes(key)?String(v):v.toLocaleString(undefined,{maximumFractionDigits:1,minimumFractionDigits:1});tr.append(td)}body.append(tr)}
 if(!filtered.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=columns.length;td.textContent='No matching records. Try a different filter.';tr.append(td);body.append(tr)}
}
function displayValue(row,key){let v=row[key];if(mode==='players'&&['minutes','points','rebounds','offRebounds','defRebounds','assists','steals','blocks','turnovers','fgMade','fgAttempted','threeMade','threeAttempted','ftMade','ftAttempted'].includes(key)&&perGame){const g=number(row.games);v=g>0&&number(v)!==null?v/g:null}return v===undefined?null:v}
function updateTeamOptions(){
 if(mode!=='players')return;
 const selector=$('team'), previous=selector.value, conf=$('conference').value;
 const teams=[...new Set(rows.filter(r=>!conf||r.conference===conf).map(r=>r.team).filter(Boolean))].sort();
 selector.replaceChildren();const all=document.createElement('option');all.value='';all.textContent='All teams';selector.append(all);
 for(const team of teams){const option=document.createElement('option');option.value=team;option.textContent=team;selector.append(option)}
 selector.value=teams.includes(previous)?previous:'';
}
async function init(){
 const status=$('status');try{const sr=await fetch('data/refresh-status.json',{cache:'no-store'});const refresh=sr.ok?await sr.json():null;const release=typeof refresh?.release==='string'&&/^[a-f0-9]{16}-[a-f0-9]{16}$/.test(refresh.release)?refresh.release:null;const dataUrl='data/'+(mode==='players'?'players':'teams')+'.json'+(release?'?release='+encodeURIComponent(release):'');const response=await fetch(dataUrl,{cache:'no-store'});if(!response.ok)throw Error('No dashboard dataset is published');const data=await response.json();if(data.schemaVersion!==1||!Array.isArray(data.rows)||typeof data.demo!=='boolean'||data.season!==2027)throw Error('Dataset format or season not supported');
 if(!data.demo && (data.approvedForPrivateDisplay!==true||typeof data.generatedAt!=='string'||!data.generatedAt||typeof data.scope!=='string'||!data.scope||!data.source))throw Error('Real dataset lacks explicit private-display approval or provenance');
 if(release && data.release!==release)throw Error('Dataset release does not match pinned refresh status');
 rows=data.rows;
 const cs=[...new Set(rows.map(x=>x.conference).filter(Boolean))].sort();for(const c of cs){const o=document.createElement('option');o.value=c;o.textContent=c;$('conference').append(o)}
 updateTeamOptions();
 status.textContent=`${data.demo?'DEMO: synthetic figures only. Not actual NCAA statistics.':'APPROVED PRIVATE DATASET: descriptive statistics, coverage may be incomplete.'} · Season ${data.seasonLabel} · ${data.scope||'scope not specified'} · Data generated ${data.generatedAt||'unknown'}.`;
 if(refresh){$('refresh').textContent=`Latest attempt: ${refresh.outcome||'not run'}. Last successful data update: ${refresh.lastSuccessAt||'none'}.`}
 if(data.demo){document.querySelectorAll('.demo').forEach(x=>x.hidden=false)}render();
 }catch(err){status.textContent='No approved data published yet. No provider requests were made. '+err.message;$('count').textContent='0 records';}
}
$('search').addEventListener('input',render);$('conference').addEventListener('change',()=>{updateTeamOptions();render()});
if(mode==='players')$('team').addEventListener('change',render);
if($('view')){$('view').addEventListener('change',e=>{perGame=e.target.value==='perGame';render()})}
if($('minGames'))$('minGames').addEventListener('change',render);
init();
