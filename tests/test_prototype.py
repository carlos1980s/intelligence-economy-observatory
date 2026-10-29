import csv
from dataclasses import replace
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from gpu_index.data import ROOT,CORE,LEGACY,aws_quotes,load_quotes,export_quotes,available_facts,read_csv
from gpu_index.index import matched_index,replacement_cost
from gpu_index.models import MonthlyModel,MODELS,synthetic_panel,evaluate,summarize,validate_panel
from gpu_index.adapters import extract_aws
from gpu_index.interfaces import Workload,ForwardContract
from gpu_index.__main__ import build

class IndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.q=aws_quotes(ROOT/'inputs/aws_gpu_2024_2026_expanded10.csv')
    def result(self,qs=None,cohort=CORE): return matched_index(self.q if qs is None else qs,'2024-10','2026-10',cohort)
    def test_golden_core(self):
        r=self.result();self.assertAlmostEqual(r['laspeyres'],84.59609438567942,places=10)
        self.assertAlmostEqual(r['members'][0]['ratio'],55.04/98.32)
        self.assertEqual(r['members'][1]['ratio'],.67)
        self.assertEqual(r['coverage'],1)
    def test_eight_is_separate(self):
        r=self.result(cohort=LEGACY);self.assertAlmostEqual(r['laspeyres'],90.37255899104963)
        self.assertEqual(r['cohort_size'],8);self.assertEqual(self.result()['cohort_size'],5)
    def test_geometric_not_budget(self):
        r=self.result();self.assertLess(r['geometric'],r['laspeyres'])
        expected=100*math.exp((math.log(55.04/98.32)+math.log(.67))/5)
        self.assertAlmostEqual(r['geometric'],expected)
    def test_actual_quantities(self):
        r=self.result();c=replacement_cost(r)
        self.assertAlmostEqual(sum(x['instance_hours']*x['baseline_price'] for x in c['quantities']),1e12,places=2)
        self.assertAlmostEqual(sum(x['instance_hours']*x['target_price'] for x in c['quantities']),845960943856.7942,places=2)
    def test_missing_never_reweights(self):
        qs=[q for q in self.q if not(q.instance==CORE[0] and q.period=='2026-10')]
        r=self.result(qs);self.assertEqual(r['coverage'],.8);self.assertIsNone(r['laspeyres'])
        with self.assertRaises(ValueError):replacement_cost(r)
    def test_no_prelaunch_fill(self):
        with self.assertRaises(ValueError):replace(self.q[0],launch_date='2025-01-01').validate()
        with self.assertRaises(ValueError):matched_index(self.q,'2023-01','2026-10',CORE)
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):self.result(self.q+[self.q[0]])
    def test_segment_not_merged(self):
        qs=self.q+[replace(self.q[0],commitment='interruptible_spot')]
        with self.assertRaises(ValueError):self.result(qs)
        with self.assertRaises(ValueError):self.result(self.q+[replace(self.q[0],provider_category='aggregator')])
    def test_bundle_changes_break_match(self):
        qs=[replace(q,host_bundle='different host') if q.period=='2026-10' and q.instance==CORE[0] else q for q in self.q]
        self.assertEqual(self.result(qs)['coverage'],.8)
    def test_stale_and_modelled_not_observed(self):
        for field,value in [('freshness','stale'),('evidence','MODELLED')]:
            qs=[replace(q,**{field:value}) if q.period=='2026-10' and q.instance==CORE[0] else q for q in self.q]
            r=self.result(qs);self.assertIsNone(r['laspeyres']);self.assertEqual(r['coverage'],.8)
            self.assertAlmostEqual(r['observed_weight']+r['modelled_weight']+r['stale_weight']+r['unavailable_weight'],1)
            self.assertEqual(r['stale_weight'] if field=='freshness' else r['modelled_weight'],.2)
    def test_publication_gate(self):
        with self.assertRaises(ValueError):matched_index(self.q,'2024-10','2026-10',CORE,as_of='2024-10-31')
        r=matched_index(self.q,'2024-10','2026-10',CORE,as_of='2026-10-01');self.assertEqual(r['coverage'],0)
    def test_zero_invalid_and_term_duration(self):
        for kwargs in [dict(price=0),dict(price=float('nan')),dict(commitment='term',commitment_months=0),dict(source_hash='bad')]:
            with self.assertRaises(ValueError):replace(self.q[0],**kwargs).validate()
    def test_roundtrip_exact(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'q.csv';export_quotes(p,self.q);self.assertEqual(load_quotes(p),self.q)

class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=synthetic_panel()
    def test_reproducible_scenario(self):self.assertEqual(self.rows,synthetic_panel())
    def test_aws_jump_not_forced_on_neo(self):
        train=[r for r in self.rows if r['month']<'2025-06']
        neo=next(r for r in self.rows if r['provider']=='NeoA' and r['gpu']=='H100' and r['month']=='2025-05')
        policy=MonthlyModel('policy_jump_adjusted').fit(train)
        flat=MonthlyModel('constant_aws_spread').fit(train)
        self.assertLess(abs(policy.predict_change(neo,-.4)),.05)
        self.assertAlmostEqual(flat.predict_change(neo,-.4),-.4)
    def test_future_does_not_change_train_fit(self):
        train=[r for r in self.rows if r['month']<'2025-01']
        modified=[dict(r,log_price=r['log_price']+100) if r['month']>='2025-01' else r for r in self.rows]
        a=MonthlyModel('pooled_spread').fit(train)
        b=MonthlyModel('pooled_spread').fit([r for r in modified if r['month']<'2025-01'])
        self.assertEqual(a.sm,b.sm);self.assertEqual(a.sigma,b.sigma)
    def test_heldout_excluded(self):
        train=[r for r in self.rows if r['provider']!='NeoC']
        m=MonthlyModel('policy_jump_adjusted').fit(train)
        self.assertFalse(any(k[1]=='NeoC' for k in m.pm))
        scores=evaluate(self.rows,holdout_provider='NeoC')
        self.assertTrue(all(r['provider']=='NeoC' for r in scores));self.assertEqual(len(scores),216)
    def test_all_models_have_two_blocks_and_intervals(self):
        scores=evaluate(self.rows)
        self.assertEqual({r['model'] for r in scores},set(MODELS))
        self.assertEqual({r['block'] for r in scores},{'first','second'})
        for r in summarize(scores):self.assertGreaterEqual(r['coverage_90'],0);self.assertLessEqual(r['coverage_90'],1)
    def test_prelaunch_duplicate_and_gap(self):
        with self.assertRaises(ValueError):validate_panel(self.rows+[self.rows[0]])
        with self.assertRaises(ValueError):validate_panel([dict(self.rows[0],launch_month='2025-01')])
        m=MonthlyModel('own_price_random_walk').fit(self.rows)
        with self.assertRaises(ValueError):m.predict(self.rows[0],'2024-03',3)
    def test_positive_predictions(self):
        for name in MODELS:
            m=MonthlyModel(name).fit(self.rows);p=m.predict(self.rows[0],'2024-02',self.rows[0]['anchor'])
            self.assertGreater(p['lower'],0);self.assertLess(p['lower'],p['price']);self.assertLess(p['price'],p['upper'])

class AdapterAndInterfaceTests(unittest.TestCase):
    def test_filing_gate(self):
        rows=[dict(sec_acceptance_utc=s) for s in ('2025-02-01T23:00:00Z','2024-10-30T22:00:00Z','')]
        self.assertEqual(available_facts(rows,'2024-10-31T23:59:59Z'),[rows[1]])
        with self.assertRaises(ValueError):available_facts(rows,'2024-10-31')
    def test_financial_input_present(self):
        rs=read_csv(ROOT/'inputs/gpu_calibration_financial_fact_vintages.csv')
        self.assertEqual(len(rs),727);self.assertEqual(sum(bool(r['sec_acceptance_utc']) for r in rs),697)
    def test_bounded_archive_stream(self):
        data=b'"FormatVersion","v1.0"\n"SKU","Instance Type","TermType","PricePerUnit"\n"a","p5.48xlarge","OnDemand","98.32"\n"b","other","OnDemand","1"\n'
        a=extract_aws(io.BytesIO(data),CORE,max_bytes=1000)
        self.assertTrue(a['scan_complete']);self.assertEqual(len(a['rows']),1)
        b=extract_aws(io.BytesIO(data),CORE,max_bytes=50)
        self.assertFalse(b['scan_complete']);self.assertLessEqual(b['bytes_scanned'],50)
    def test_workload(self):
        w=Workload('task','quality',100,'version1',1000,10,True)
        self.assertEqual(w.cost_per_accepted_unit(),.01)
        with self.assertRaises(ValueError):replace(w,compatible=False).cost_per_accepted_unit()
    def test_contract_scaffold_honest(self):
        with self.assertRaises(NotImplementedError):ForwardContract('2027-01-01',12,1024,1e6,'unknown','unknown',False).value()

class IntegrationTests(unittest.TestCase):
    def test_build_reproducible_and_exports(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            build(ROOT/'inputs',Path(a));build(ROOT/'inputs',Path(b))
            for p in Path(a).iterdir():self.assertEqual(p.read_bytes(),(Path(b)/p.name).read_bytes(),p.name)
            html=(Path(a)/'report.html').read_text()
            self.assertIn('84.596094',html);self.assertIn('SYNTHETIC TESTS ONLY',html)
            self.assertIn('Linear level axis begins at zero',html);self.assertEqual(len(load_quotes(Path(a)/'quotes.csv')),20)
    def test_cli_paths(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)
            def run(*args,expected=0):
                r=subprocess.run([sys.executable,'-m','gpu_index',*map(str,args)],cwd=ROOT,capture_output=True,text=True)
                self.assertEqual(r.returncode,expected,r.stderr);return r
            run('--help');run('build','--out',d/'build')
            run('validate',d/'build/quotes.csv')
            run('model-lab','--out',d/'lab')
            run('fit',d/'lab/synthetic_monthly_panel.json','--out',d/'fit.json')
            run('facts','--as-of','2024-10-31T23:59:59Z','--out',d/'facts.csv')
            run('facts','--as-of','invalid','--out',d/'bad.csv',expected=2)
            run('validate',d/'missing.csv',expected=2)

if __name__=='__main__':unittest.main()
