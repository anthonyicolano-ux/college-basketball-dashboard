'use strict';
const $ = id => document.getElementById(id);
const mode = document.body.dataset.mode;
const columns = mode === 'players' ? [
 ['name','Player','text'],['team','Team','text'],['conference','Conf.','text'],['games','GP'],['minutes','MIN'],['points','PTS'],['rebounds','REB'],['assists','AST'],['steals','STL'],['blocks','BLK'],['turnovers','TO'],['fgMade','FGM'],['fgAttempted','FGA'],['fgPct','FG%'],['threeMade','3PM'],['threeAttempted','3PA'],['threePct','3P%'],['ftMade','FTM'],['ftAttempted','FTA'],['ftPct','FT%']
] : [
 ['team','Team','text'],['conference','Conf.','text'],['wins','W'],['losses','L'],['games','GP'],['ppg','PPG'],['oppPpg','Opp PPG'],['offRating','Off/100'],['defRating','Def/100'],['netRating','Net/100'],['scoringMargin','Margin/G'],['pace','Pace'],['fgPct','FG%'],['threePct','3P%'],['ftPct','FT%'],['eFg','eFG%'],['tsPct','TS%'],['rebounds','REB/G'],['assists','AST/G'],['turnovers','TO/G']
];
let rows = [], currentSort = mode === 'players' ? 'points' : 'offRating', ascending = false, perGame = true;
const number = v => (typeof v === 'number' && Number.isFinite(v)) ? v : null;
function render(){
 const filter = $('search').value.trim().toLowerCase(); const conf = $('conference').value;
 const filtered = rows.filter(r=>(!conf || r.conference === conf) && (!filter || `${r.name||''} ${r.team||''} ${r.conference||''}`.toLowerCase().includes(filter)));
 const sorted = [...filtered].sort((a,b)=>{const va=displayValue(a,currentSort),vb=displayValue(b,currentSort);const missingA=va==null,missingB=vb==null;if(missingA||missingB)return Number(missingA)-Number(missingB);const cmp=typeof va === 'string' ? String(va).localeCompare(String(vb)) : va-vb;return ascending?cmp:-cmp;});
 $('count').textContent = `${filtered.length} ${mode === 'players' ? 'players' : 'teams'}`;
 const head=$('head');head.replaceChildren();const hr=document.createElement('tr');columns.forEach(([key,label])=>{const th=document.createElement('th');th.scope='col';const b=document.createElement('button');b.className='sort';b.textContent=label+(currentSort===key?(ascending?' ↑':' ↓'):'');b.addEventListener('click',()=>{if(currentSort===key)ascending=!ascending;else{currentSort=key;ascending=key==='team'||key==='name'||key==='conference'}render()});th.append(b);hr.append(th)});head.append(hr);
 const body=$('body');body.replaceChildren();for(const r of sorted){const tr=document.createElement('tr');for(const [key,,type] of columns){const td=document.createElement('td');const v=displayValue(r,key);td.textContent=v==null?'—':type==='text'?String(v):['games','wins','losses'].includes(key)?String(v):v.toLocaleString(undefined,{maximumFractionDigits:1,minimumFractionDigits:1});tr.append(td)}body.append(tr)}
 if(!filtered.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=columns.length;td.textContent='No matching records. Try a different filter.';tr.append(td);body.append(tr)}
}
function displayValue(row,key){let v=row[key];if(mode==='players'&&['minutes','points','rebounds','assists','steals','blocks','turnovers','fgMade','fgAttempted','threeMade','threeAttempted','ftMade','ftAttempted'].includes(key)&&perGame){const g=number(row.games);v=g>0&&number(v)!==null?v/g:null}return v===undefined?null:v}
async function init(){
 const status=$('status');try{const [response,sr]=await Promise.all([fetch('data/'+(mode==='players'?'players':'teams')+'.json',{cache:'no-store'}),fetch('data/refresh-status.json',{cache:'no-store'})]);if(!response.ok)throw Error('No dashboard dataset is published');const data=await response.json();if(data.schemaVersion!==1||!Array.isArray(data.rows))throw Error('Dataset format not supported');rows=data.rows;
 const cs=[...new Set(rows.map(x=>x.conference).filter(Boolean))].sort();for(const c of cs){const o=document.createElement('option');o.value=c;o.textContent=c;$('conference').append(o)}
 status.textContent=`${data.demo?'DEMO: synthetic figures only. Not actual NCAA statistics.':'Data published'} · Season ${data.seasonLabel} · ${data.scope||'scope not specified'} · Data generated ${data.generatedAt||'unknown'}.`;
 if(sr.ok){const s=await sr.json();$('refresh').textContent=`Latest attempt: ${s.outcome||'not run'}. Last successful data update: ${s.lastSuccessAt||'none'}.`}
 if(data.demo){document.querySelectorAll('.demo').forEach(x=>x.hidden=false)}render();
 }catch(err){status.textContent='No approved data published yet. No provider requests were made. '+err.message;$('count').textContent='0 records';}
}
$('search').addEventListener('input',render);$('conference').addEventListener('change',render);
if($('view')){$('view').addEventListener('change',e=>{perGame=e.target.value==='perGame';render()})}
init();
