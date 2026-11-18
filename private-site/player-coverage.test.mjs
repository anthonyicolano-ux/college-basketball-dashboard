import test from 'node:test';
import assert from 'node:assert/strict';
import {playerTeamsCovered} from './player-coverage.mjs';

const teams = Array.from({length:30},(_,i)=>({team:'Fixture '+i}));
const players = Array.from({length:250},(_,i)=>({team:'Fixture '+(i%30)}));

test('matching expanded coverage accepted',()=>{
  assert.equal(playerTeamsCovered(players,teams),true);
});
test('unknown player team rejected',()=>{
  assert.equal(playerTeamsCovered([...players,{team:'Unknown'}],teams),false);
});
test('duplicate team names rejected',()=>{
  assert.equal(playerTeamsCovered(players,[...teams,teams[0]]),false);
});
test('empty or malformed coverage rejected',()=>{
  assert.equal(playerTeamsCovered(players,[]),false);
  assert.equal(playerTeamsCovered([{team:null}],teams),false);
});

test('full-size synthetic coverage accepts 365 teams and 5500 players',()=>{
  const fullTeams=Array.from({length:365},(_,i)=>({team:'Team '+i}));
  const fullPlayers=Array.from({length:5500},(_,i)=>({team:'Team '+(i%365)}));
  assert.equal(playerTeamsCovered(fullPlayers,fullTeams),true);
});

test('full-size synthetic coverage rejects one unmatched player',()=>{
  const fullTeams=Array.from({length:365},(_,i)=>({team:'Team '+i}));
  const fullPlayers=Array.from({length:5500},(_,i)=>({team:'Team '+(i%365)}));
  fullPlayers[5499]={team:'Outside Coverage'};
  assert.equal(playerTeamsCovered(fullPlayers,fullTeams),false);
});
