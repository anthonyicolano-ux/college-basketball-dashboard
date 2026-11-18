// Synthetic Worker route regression tests. No real records, network or secrets.
import test from 'node:test';
import assert from 'node:assert/strict';
import worker from './worker.js';

const metadata = {schemaVersion:1,season:2027,seasonLabel:'2026–27',demo:false,
  approvedForPrivateDisplay:true,source:'synthetic fixture',scope:'synthetic tests only',
  generatedAt:'2026-11-17T00:00:00Z'};
const team = i => ({team:'Fixture '+i,conference:'Fixture Conference',wins:2,losses:1,
  games:3,ppg:70,oppPpg:65,offRating:105,defRating:98,netRating:7,scoringMargin:5});
const player = i => ({name:'Fixture Player '+i,team:'Fixture '+(i%30),
  conference:'Fixture Conference',games:3,minutes:60,points:30,rebounds:12,assists:6,
  internalSecret:'must not leak'});
const dataset = rows => ({...metadata,rows});
const mock = (teams,players) => ({
  ACCESS_PASSWORD:'test-password',SESSION_SECRET:'test-secret',
  ASSETS:{fetch:async()=>new Response('demo fallback')},
  PRIVATE_DATA:{get:async key => key==='teams'?JSON.stringify(teams):
    key==='players'?JSON.stringify(players):null}
});
async function authCookie(env) {
  const form = new FormData();form.set('password','test-password');
  const response = await worker.fetch(new Request('https://example.test/unlock',
    {method:'POST',body:form}),env);
  assert.equal(response.status,303);
  return response.headers.get('set-cookie').split(';')[0];
}
async function get(env,path,cookie) {
  return worker.fetch(new Request('https://example.test'+path,
    {headers:{cookie}}),env);
}

test('unauthenticated data is protected',async()=>{
  const response=await worker.fetch(new Request('https://example.test/data/teams.json'),
    mock(dataset(Array.from({length:30},(_,i)=>team(i))),dataset(Array.from({length:250},(_,i)=>player(i)))));
  assert.match(await response.text(),/Shared password/);
});

test('approved expanded teams return metadata and projected rows',async()=>{
  const env=mock(dataset(Array.from({length:30},(_,i)=>({...team(i),internalSecret:'hidden'}))),
    dataset(Array.from({length:250},(_,i)=>player(i))));
  const response=await get(env,'/data/teams.json',await authCookie(env));
  assert.equal(response.status,200);
  const data=await response.json();
  assert.equal(data.rows.length,30);
  assert.equal(data.approvedForPrivateDisplay,true);
  assert.equal(data.source,'synthetic fixture');
  assert.equal(data.rows[0].internalSecret,undefined);
});

test('approved expanded players are projected',async()=>{
  const env=mock(dataset(Array.from({length:30},(_,i)=>team(i))),
    dataset(Array.from({length:250},(_,i)=>player(i))));
  const response=await get(env,'/data/players.json',await authCookie(env));
  const data=await response.json();
  assert.equal(data.rows.length,250);
  assert.equal(data.rows[0].internalSecret,undefined);
  assert.equal(data.approvedForPrivateDisplay,true);
});

test('unapproved expanded players fail closed',async()=>{
  const teams=dataset(Array.from({length:30},(_,i)=>team(i)));
  const players=dataset(Array.from({length:250},(_,i)=>player(i)));
  players.approvedForPrivateDisplay=false;
  const env=mock(teams,players);
  const response=await get(env,'/data/players.json',await authCookie(env));
  assert.equal(response.status,503);
  assert.doesNotMatch(await response.text(),/Fixture Player/);
});

test('unapproved expanded teams do not expose KV rows',async()=>{
  const teams=dataset(Array.from({length:30},(_,i)=>team(i)));
  teams.approvedForPrivateDisplay=false;
  const env=mock(teams,dataset(Array.from({length:250},(_,i)=>player(i))));
  const response=await get(env,'/data/teams.json',await authCookie(env));
  assert.equal(await response.text(),'demo fallback');
});
