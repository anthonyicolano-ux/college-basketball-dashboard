"""Generate SYNTHETIC dashboard test records: never real sports statistics."""
from datetime import datetime, timezone
import json
from pathlib import Path
from metrics import safe_rate, effective_fg, true_shooting, per_game, validate_dataset
ROOT = Path(__file__).resolve().parents[1]
NOW = datetime.now(timezone.utc).isoformat(timespec='seconds')
def write(name, rows):
    doc={'schemaVersion':1,'season':2027,'seasonLabel':'2026–27 (SYNTHETIC DEMO)','scope':'Fictional Division I-style sample; no real teams or games','generatedAt':NOW,'demo':True,'rows':rows}
    validate_dataset(doc)
    (ROOT/'data'/name).write_text(json.dumps(doc,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def main():
    teams=[]; players=[]
    names=[('North Valley','North','Fictional A',7,2,711,621,585,590,248,540,92,225,123,166),('Lake Institute','Lake','Fictional A',5,4,662,651,610,602,234,531,75,207,119,158),('Cedar State','Cedar','Fictional B',8,1,744,604,598,603,273,560,101,249,97,137),('West Metro','West','Fictional B',4,5,620,681,606,594,227,524,64,207,102,153),('Pine Coast','Pine','Fictional C',6,3,692,644,595,598,254,548,88,234,96,142),('Red Mesa','Mesa','Fictional C',3,6,596,711,605,610,221,539,66,218,88,129)]
    # Fictional opponent-allowed per-game figures, aligned with the current demo.
    # They are deliberately synthetic, not inferred from any real NCAA games.
    opponent_demo = [
        (6.53,31.68,42.81,33.76,12.02,13.97),
        (8.22,35.32,45.54,35.84,13.58,12.28),
        (6.33,31.26,42.50,33.52,11.84,14.17),
        (8.61,36.16,46.17,36.32,13.94,11.89),
        (7.50,33.78,44.39,34.96,12.92,13.00),
        (9.00,37.00,46.80,36.80,14.30,11.50),
    ]
    assert len(opponent_demo) == len(names)
    for idx,(team,prefix,conf,w,l,pts,opp,poss,opp_poss,fgm,fga,tpm,tpa,ftm,fta) in enumerate(names):
        games=w+l
        teams.append({'team':team,'conference':conf,'games':games,'wins':w,'losses':l,'ppg':per_game(pts,games),'oppPpg':per_game(opp,games),'offRating':safe_rate(pts,poss,100),'defRating':safe_rate(opp,opp_poss,100),'pace':per_game(poss,games),'fgPct':safe_rate(fgm,fga,100),'threePct':safe_rate(tpm,tpa,100),'ftPct':safe_rate(ftm,fta,100),'eFg':effective_fg(fgm,tpm,fga),'tsPct':true_shooting(pts,fga,fta),'rebounds':per_game(310+idx*6,games),'assists':per_game(115+idx*5,games),'turnovers':per_game(93+idx*6,games)})
        opp_three_made,opp_three_pct,opp_fg_pct,opp_rebounds,opp_assists,opp_turnovers = opponent_demo[idx]
        teams[-1].update({
            'threeMade': per_game(tpm, games),
            'oppThreeMade': opp_three_made,
            'oppThreePct': opp_three_pct,
            'oppFgPct': opp_fg_pct,
            'oppRebounds': opp_rebounds,
            'oppAssists': opp_assists,
            'turnoversForced': opp_turnovers,
            'oppTurnovers': opp_turnovers,
        })
        for j in range(3):
            pfgm=38+j*15+idx;pfg=91+j*27+idx*2;p3m=13+j*6;p3a=36+j*14;pftm=17+j*8;pfta=23+j*10
            players.append({'name':f'{prefix} Demo Player {j+1}','team':team,'conference':conf,'games':games,'minutes':games*(19+j*6),'points':pfgm*2+p3m+pftm,'rebounds':games*(3+j*2),'assists':games*(1+j),'steals':games+j*3,'blocks':j*3+idx,'turnovers':games+j*4,'fgPct':safe_rate(pfgm,pfg,100),'threePct':safe_rate(p3m,p3a,100),'ftPct':safe_rate(pftm,pfta,100)})
    write('teams.json',teams);write('players.json',players)
    (ROOT/'data'/'refresh-status.json').write_text(json.dumps({'schemaVersion':1,'outcome':'demo only — no live API attempted','lastSuccessAt':None,'lastAttemptAt':None},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
