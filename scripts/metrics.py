"""Basketball math and publication schema checks; no provider connection."""
import math

def safe_rate(numerator, denominator, scale=1):
    if not all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in (numerator,denominator)) or denominator<=0:
        return None
    return scale*numerator/denominator

def per_game(value, games):return safe_rate(value,games)
def effective_fg(fgm, three_made, fga):
    if fgm is None or three_made is None:return None
    return safe_rate(fgm+0.5*three_made,fga,100)
def true_shooting(points,fga,fta):
    if any(x is None for x in (points,fga,fta)):return None
    return safe_rate(points,2*(fga+0.44*fta),100)
def validate_dataset(data):
    if data.get('schemaVersion')!=1 or not isinstance(data.get('season'),int) or not isinstance(data.get('rows'),list):raise ValueError('Invalid dashboard schema')
    if not data.get('demo',False):raise ValueError('Live dataset publication disabled pending explicit rights clearance')
    for row in data['rows']:
        if not isinstance(row,dict) or not isinstance(row.get('team'),str):raise ValueError('Invalid row')
        if any(isinstance(v,float) and not math.isfinite(v) for v in row.values()):raise ValueError('Non-finite data')
    return True
