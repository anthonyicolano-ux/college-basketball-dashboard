// Pure coverage check; no access to passwords, sessions, network, or KV.
export function playerTeamsCovered(players, teams) {
  if (!Array.isArray(players) || !Array.isArray(teams) || teams.length === 0) return false;
  const names = new Set();
  for (const row of teams) {
    if (!row || typeof row.team !== 'string' || !row.team.trim() || names.has(row.team)) return false;
    names.add(row.team);
  }
  return players.every(row => row && typeof row.team === 'string' && names.has(row.team));
}
