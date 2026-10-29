from dataclasses import replace
from datetime import timedelta
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from gpu_index.data import ROOT,read_csv,aws_quotes,export_quotes
from gpu_index.finance import feature_snapshot,monthly_features,origin_for,release_time,feature_map
from gpu_index.challengers import FinancialChallenger,compare,summary
from gpu_index.models import synthetic_panel,increments,known_before,validate_panel,MonthlyModel
from gpu_index.eligibility import quote_id,import_history,report

CFG=json.loads((ROOT/'schemas/financial_features.json').read_text())
FACTS=read_csv(ROOT/'inputs/gpu_calibration_financial_fact_vintages.csv')


def fact(end,value,accession='a',accepted='2025-02-01T10:00:00Z',filed='2025-02-01'):
    year=int(end[:4]);return dict(company='NVDA',tag='Revenues',unit='USD',start=f'{year}-01-01',end=end,value=str(value),
        accession=accession,sec_acceptance_utc=accepted,filed_date=filed,filing_document_url='https://example.org/filing',source_url='https://example.org/facts')

class FinancialFeaturesTests(unittest.TestCase):
    def test_no_acceptance_or_future_release(self):
        rows=[fact('2024-12-31',200),fact('2023-12-31',100)]
        early=feature_snapshot(rows,CFG,'2025-02-01T20:00:00Z')
        self.assertIsNone(early[0]['value'])
        late=feature_snapshot(rows,CFG,'2025-02-02T00:00:00Z')
        self.assertAlmostEqual(late[0]['value'],math.log(2))
        rows[0]['sec_acceptance_utc']='';self.assertIsNone(feature_snapshot(rows,CFG,'2025-02-02T00:00:00Z')[0]['value'])
    def test_both_filed_and_acceptance_dates_respected(self):
        r=fact('2024-12-31',200,accepted='2025-02-03T10:00:00Z')
        self.assertEqual(release_time(r).isoformat(),'2025-02-03T10:00:00+00:00')
        r['filed_date']='2025-02-04';self.assertEqual(release_time(r).day,4)
    def test_same_accession_prevents_splice(self):
        rows=[fact('2024-12-31',200,'new'),fact('2023-12-31',100,'old')]
        self.assertIsNone(feature_snapshot(rows,CFG,'2025-02-10T00:00:00Z')[0]['value'])
    def test_latest_eligible_restatement(self):
        rows=[fact('2024-12-31',200),fact('2023-12-31',100),fact('2024-12-31',300,'b','2026-02-01T10:00:00Z','2026-02-01'),fact('2023-12-31',100,'b','2026-02-01T10:00:00Z','2026-02-01')]
        self.assertAlmostEqual(feature_snapshot(rows,CFG,'2025-03-01T00:00:00Z')[0]['value'],math.log(2))
        self.assertAlmostEqual(feature_snapshot(rows,CFG,'2026-03-01T00:00:00Z')[0]['value'],math.log(3))
    def test_stale_quarter_currency_and_nonpositive_rejected(self):
        base=[fact('2024-12-31',200),fact('2023-12-31',100)]
        for field,value in [('unit','RUB'),('start','2024-10-01'),('value','0')]:
            rows=[dict(base[0],**{field:value}),base[1]]
            self.assertIsNone(feature_snapshot(rows,CFG,'2025-03-01T00:00:00Z')[0]['value'])
        self.assertIsNone(feature_snapshot(base,CFG,'2027-03-01T00:00:00Z')[0]['value'])
    def test_issuer_blocks_and_nebius_disabled(self):
        rs=feature_snapshot(FACTS,CFG,'2026-10-01T00:00:00Z')
        self.assertEqual(len({r['block'] for r in rs}),4);self.assertFalse(rs[-1]['available'])
        self.assertEqual({r['company'] for r in rs if r['available']},{'NVDA','AVGO','CRWV'})
    def test_future_fact_changes_do_not_change_features(self):
        changed=[dict(r,value='99999999999') if r['filed_date']>'2024-10-31' else r for r in FACTS]
        self.assertEqual(feature_snapshot(FACTS,CFG,'2024-10-31T23:59:59Z'),feature_snapshot(changed,CFG,'2024-10-31T23:59:59Z'))
    def test_monthly_origin_and_future_feature_rejected(self):
        r=monthly_features(FACTS,CFG,['2024-11'])[0]
        self.assertEqual(r['as_of'],'2024-10-31T23:59:59.999999+00:00')
        with self.assertRaises(ValueError):feature_map([dict(r,release_utc='2024-11-01T00:00:00Z')])
        with self.assertRaises(ValueError):feature_map([dict(r,release_utc='',value=.1)])

class ChallengerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=synthetic_panel();cls.features=monthly_features(FACTS,CFG,[r['month'] for r in cls.rows])
    def test_no_finance_exact_baseline(self):
        m=FinancialChallenger([]).fit(self.rows,self.features);r=increments(self.rows)[-1]
        self.assertEqual(m.predict_change(r,r['da'],r['month']),m.base.predict_change(r,r['da']))
    def test_train_only_standardization(self):
        train=[r for r in self.rows if r['month']<'2025-01']
        mutated=[dict(r,value=1e9) if r['target_month']>='2025-01' and r['value'] is not None else r for r in self.features]
        a=FinancialChallenger(['nvda_revenue_yoy']).fit(train,self.features)
        b=FinancialChallenger(['nvda_revenue_yoy']).fit(train,mutated)
        self.assertEqual(a.parameters(),b.parameters())
    def test_missing_does_not_get_fabricated(self):
        m=FinancialChallenger(['crwv_revenue_yoy']).fit([r for r in self.rows if r['month']<'2025-01'],self.features)
        self.assertEqual(m.active,[]);self.assertEqual(m.vector('2024-01'),[])
    def test_regularization_and_segment_separation(self):
        rows=[r for r in self.rows if r['provider']=='NeoA' and r['gpu']=='H100']
        features=[];price=0
        for i,r in enumerate(rows):
            x=math.sin(i);price+=.1*x;r['log_price']=price
            features.append(dict(target_month=r['month'],feature='fixture_signal',value=x,release_utc='',evidence='ASSUMED synthetic feature fixture'))
        small=FinancialChallenger(['fixture_signal'],ridge=.1).fit(rows,features)
        large=FinancialChallenger(['fixture_signal'],ridge=1000).fit(rows,features)
        self.assertGreater(abs(small.coef['neocloud'][0]),abs(large.coef['neocloud'][0]))
        self.assertEqual(small.effective_months['neocloud'],29)
    def test_all_ablations_and_provider_holdout(self):
        scores=compare(self.rows,self.features,CFG,holdout='NeoC')
        variants={r['variant'] for r in scores}
        self.assertIn('no_finance',variants);self.assertIn('drop_NVIDIA',variants);self.assertIn('only_Broadcom',variants)
        self.assertTrue(all(r['provider']=='NeoC' for r in scores))
        self.assertEqual({r['block'] for r in summary(scores)},{'first','second'})
    def test_late_rental_quote_not_training_information(self):
        r=dict(self.rows[0],publication_date='2025-01-01')
        self.assertFalse(known_before(r,'2025-01'));self.assertTrue(known_before(r,'2025-02'))

class ProviderImportTests(unittest.TestCase):
    def fixtures(self):
        q=aws_quotes(ROOT/'inputs/aws_gpu_2024_2026_expanded10.csv')[0]
        quotes=[replace(q,period=m,publication_date=m+'-28',observation_date=m+'-28',effective_date=m+'-01',
            launch_date='2020-01-01',interconnect='NVLink qualified fixture',price=10+i) for i,m in enumerate(['2024-01','2024-02'])]
        bindings=[dict(quote_id=quote_id(q),anchor_quote_id=quote_id(q)) for q in quotes]
        rights={'AWS':dict(local_research_allowed=True,terms_source_url='https://example.org/fixture-terms',checked_date='2026-10-28')}
        return quotes,bindings,rights
    def test_real_import_schema_and_lineage(self):
        qs,bs,rights=self.fixtures();panel,lineage=import_history(qs,bs,rights)
        self.assertEqual(len(panel),2);self.assertEqual(len(lineage),2);self.assertEqual(len(increments(panel)),1)
        self.assertEqual(panel[0]['evidence'],'OBSERVED');self.assertIn('configuration_id',panel[0])
    def test_unknown_qualification_blocks_not_silently_imputed(self):
        qs,bs,rights=self.fixtures()
        with self.assertRaises(ValueError):import_history(qs,bs,{})
        qs=[replace(q,interconnect='unknown') for q in qs];bs=[dict(quote_id=quote_id(q),anchor_quote_id=quote_id(q)) for q in qs]
        with self.assertRaises(ValueError):import_history(qs,bs,rights)
    def test_current_endpoints_ineligible(self):
        qs=aws_quotes(ROOT/'inputs/aws_gpu_2024_2026_expanded10.csv');r=report(qs)
        self.assertEqual(r['summary']['consecutive_monthly_pairs'],0);self.assertEqual(r['summary']['eligible_quotes'],0)
    def test_same_architecture_distinct_bundles_not_merged(self):
        qs,bs,rights=self.fixtures();panel,_=import_history(qs,bs,rights)
        expanded=panel+[dict(r,configuration_id='second_bundle',log_price=r['log_price']+1) for r in panel]
        validate_panel(expanded);self.assertEqual(len(increments(expanded)),2)
    def test_cli_new_paths(self):
        qs,bs,rights=self.fixtures()
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);export_quotes(p/'quotes.csv',qs)
            from gpu_index.data import write_csv
            write_csv(p/'bindings.csv',bs);(p/'rights.json').write_text(json.dumps(rights))
            commands=[['financial-features','--as-of','2024-10-31T23:59:59Z','--out',p/'features.json'],
                ['financial-lab','--out',p/'lab','--holdout-provider','NeoC'],
                ['eligibility',p/'quotes.csv','--rights',p/'rights.json','--out',p/'eligible'],
                ['import-history',p/'quotes.csv','--bindings',p/'bindings.csv','--rights',p/'rights.json','--out',p/'imported']]
            for args in commands:
                r=subprocess.run([sys.executable,'-m','gpu_index',*map(str,args)],cwd=ROOT,capture_output=True,text=True)
                self.assertEqual(r.returncode,0,r.stderr)

if __name__=='__main__':unittest.main()
