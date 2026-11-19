import test from 'node:test';
import assert from 'node:assert/strict';
import release from '../assets/release.js';

const a='a'.repeat(16)+'-'+'b'.repeat(16);

test('legacy status keeps legacy dataset URL',()=>{
  assert.equal(release.select({outcome:'pilot'}),null);
  assert.equal(release.url('teams',null),'data/teams.json');
});

test('pins the same release on both pages',()=>{
  const id=release.select({release:a});
  assert.equal(release.url('teams',id),'data/teams.json?release='+a);
  assert.equal(release.url('players',id),'data/players.json?release='+a);
  assert.doesNotThrow(()=>release.verify({release:a},id));
});

test('rejects invalid pointer and mismatched dataset',()=>{
  assert.throws(()=>release.select({release:'invalid'}),/Invalid private release/);
  assert.throws(()=>release.verify({release:'other'},a),/does not match/);
});
