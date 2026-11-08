import csv
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from project import (ASSISTANTS,make_cases,read_prices,write_csv,partitions,
                     evaluate,aggregate,save_experiment,score_experiment)


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.prices = self.root/'prices.csv'
        # A known 1%-per-observation path makes return and baseline checks exact.
        from datetime import date,timedelta
        self.days = [(date(2025,1,1)+timedelta(days=i)).isoformat() for i in range(200)]
        self.rows = [{'date':d,'index':index,'close':100*1.01**i}
                     for index in ('A','B') for i,d in enumerate(self.days)]
        write_csv(self.prices,self.rows)
        self.cases = make_cases(self.prices,'test',(3,5,10),20,10)

    def predictions(self,models=ASSISTANTS,metadata=True,exact=True):
        rows = []
        for c in self.cases:
            for m in models:
                r = {'prompt_id':c['prompt_id'],'model':m,
                     'predicted_return_pct':c['_actual_pct'] if exact else 0}
                if metadata:
                    r.update(model_version='UNIT-TEST-FIXTURE',collected_at_utc='2026-01-01T00:00:00Z')
                rows.append(r)
        path = self.root/'predictions.csv'
        write_csv(path,rows)
        return path

    def test_hand_calculated_returns_and_baseline(self):
        for c in self.cases:
            expected = 100*(1.01**c['horizon_trading_days']-1)
            self.assertAlmostEqual(c['_actual_pct'],expected,places=10)
            self.assertAlmostEqual(c['momentum_baseline_pct'],expected,places=10)

    def test_split_boundaries_purge_future_labels(self):
        for split in ('train','test','validation'):
            cases = make_cases(self.prices,split,(3,5,10),20,10,True)
            start,end = partitions(self.days)[split]
            for c in cases:
                self.assertTrue(start <= self.days.index(c['as_of_date']) < end)
                self.assertTrue(start <= self.days.index(c['target_date']) < end)

    def test_identical_origins_across_horizons(self):
        origins = {}
        for h in (3,5,10):
            origins[h] = {(c['index'],c['as_of_date']) for c in self.cases if c['horizon_trading_days']==h}
        self.assertEqual(origins[3],origins[5]);self.assertEqual(origins[5],origins[10])

    def test_prompts_contain_only_past(self):
        for c in self.cases:
            lines = c['prompt'].split('date,close\n')[1].splitlines()
            self.assertEqual(len(lines),20)
            self.assertEqual(lines[-1].split(',')[0],c['as_of_date'])
            self.assertTrue(all(l.split(',')[0] <= c['as_of_date'] for l in lines))
            self.assertNotIn(c['target_date'],c['prompt'])

    def test_validation_locked(self):
        with self.assertRaisesRegex(ValueError,'held out'):
            make_cases(self.prices,'validation')

    def test_perfect_forecast_metrics(self):
        rows = evaluate(self.cases,self.predictions(),ASSISTANTS)
        scores = {r['model']:r for r in aggregate(rows,['model'])}
        for m in ASSISTANTS:
            self.assertEqual(scores[m]['mae_percentage_points'],0)
            self.assertEqual(scores[m]['rmse_percentage_points'],0)
            self.assertEqual(scores[m]['direction_accuracy'],1)
        self.assertEqual(scores['Zero baseline']['direction_accuracy'],0)

    def test_missing_model_rejected(self):
        with self.assertRaisesRegex(ValueError,'Incomplete'):
            evaluate(self.cases,self.predictions(models=('ChatGPT',)),ASSISTANTS)

    def test_nonfinite_and_duplicate_rejected(self):
        path = self.predictions()
        with path.open() as f: rows = list(csv.DictReader(f))
        rows[0]['predicted_return_pct'] = 'nan'
        write_csv(path,rows)
        with self.assertRaisesRegex(ValueError,'Invalid percentage'):
            evaluate(self.cases,path,ASSISTANTS)
        path = self.predictions()
        with path.open() as f: rows = list(csv.DictReader(f))
        rows.append(rows[0]);write_csv(path,rows)
        with self.assertRaisesRegex(ValueError,'duplicate'):
            evaluate(self.cases,path,ASSISTANTS)

    def test_metadata_required(self):
        with self.assertRaisesRegex(ValueError,'model_version'):
            evaluate(self.cases,self.predictions(metadata=False),ASSISTANTS)

    def test_invalid_calendar_duplicate_and_price(self):
        rows = self.rows[:-1]
        write_csv(self.prices,rows)
        with self.assertRaisesRegex(ValueError,'identical trading dates'): read_prices(self.prices)
        write_csv(self.prices,self.rows+[self.rows[0]])
        with self.assertRaisesRegex(ValueError,'Duplicate'): read_prices(self.prices)
        rows = [r.copy() for r in self.rows];rows[0]['close'] = -1
        write_csv(self.prices,rows)
        with self.assertRaisesRegex(ValueError,'Invalid'): read_prices(self.prices)

    def test_future_prices_do_not_change_prompt_or_momentum(self):
        c = self.cases[0]
        changed = [r.copy() for r in self.rows]
        for r in changed:
            if r['date'] > c['as_of_date']: r['close'] *= 2
        write_csv(self.prices,changed)
        modified = {r['prompt_id']:r for r in make_cases(self.prices,'test',(3,5,10),20,10)}[c['prompt_id']]
        self.assertEqual(modified['prompt'],c['prompt'])
        self.assertEqual(modified['momentum_baseline_pct'],c['momentum_baseline_pct'])
        self.assertNotEqual(modified['_actual_pct'],c['_actual_pct'])

    def test_end_to_end_and_integrity(self):
        out = self.root/'experiment'
        save_experiment(self.prices,out,'test',(3,5,10),20,10)
        score_experiment(self.prices,out,self.predictions())
        self.assertTrue((out/'metrics_by_index_horizon.csv').is_file())
        self.assertTrue((out/'REPORT.md').is_file())
        with (out/'prompts.csv').open() as f:
            self.assertNotIn('_actual_pct',csv.DictReader(f).fieldnames)
        with self.assertRaisesRegex(ValueError,'already exists'):
            save_experiment(self.prices,out,'test',(3,5,10),20,10)
        (out/'prompts.csv').write_text('changed')
        with self.assertRaisesRegex(ValueError,'Prompts changed'):
            score_experiment(self.prices,out,self.predictions())

    def test_price_integrity(self):
        out = self.root/'experiment'
        save_experiment(self.prices,out,'test',(3,5,10),20,10)
        with self.prices.open('a') as f: f.write('\n')
        with self.assertRaisesRegex(ValueError,'Price file changed'):
            score_experiment(self.prices,out,self.predictions())


if __name__ == '__main__': unittest.main()
