import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from metrics import safe_rate,per_game,effective_fg,true_shooting,validate_dataset
class MetricTests(unittest.TestCase):
 def test_null_not_zero(self):
  self.assertIsNone(safe_rate(None,10));self.assertIsNone(safe_rate(4,0));self.assertIsNone(per_game(20,0))
 def test_efg(self):self.assertAlmostEqual(effective_fg(30,10,70),50)
 def test_ts(self):self.assertAlmostEqual(true_shooting(80,70,20),80/(2*(70+8.8))*100)
 def test_rate(self):self.assertEqual(safe_rate(12,16,100),75)
 def test_live_publication_blocked(self):
  with self.assertRaisesRegex(ValueError,'publication disabled'):validate_dataset({'schemaVersion':1,'season':2027,'rows':[{'team':'Test'}]})
 def test_demo_valid(self):self.assertTrue(validate_dataset({'schemaVersion':1,'season':2027,'demo':True,'rows':[{'team':'Test'}]}))
if __name__=='__main__':unittest.main()
