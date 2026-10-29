"""Self-contained public-source/site release tests. No private Library data needed."""
from pathlib import Path
import json
import tempfile
import unittest
from html.parser import HTMLParser
from tools.build_site import build
ROOT=Path(__file__).resolve().parents[1]

class Links(HTMLParser):
    def __init__(self):super().__init__();self.refs=[];self.ids=[];self.labels=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='label':self.labels.append(a.get('for'))
        for key in ('src','href'):
            if key in a:self.refs.append(a[key])

class WebsiteTests(unittest.TestCase):
    def test_all_local_assets_and_downloads_exist(self):
        doc=Links();doc.feed((ROOT/'site/index.html').read_text())
        for ref in doc.refs:
            if ref.startswith(('#','https://','http://')):continue
            self.assertTrue((ROOT/'site'/ref).is_file(),ref)
        self.assertEqual(len(doc.ids),len(set(doc.ids)))
        for label in doc.labels:self.assertIn(label,doc.ids)
    def test_observation_contract_and_null_metadata(self):
        obj=json.loads((ROOT/'site/data/prices.json').read_text());ids=[]
        required={'source_id','source_url','retrieved_at_utc','observation_period_start','observation_period_end','published_at_utc','effective_at_utc','unit','currency','geography','population','series_definition_version','evidence_class','raw_sha256','value','status','license_note'}
        for r in obj['observations']:
            self.assertFalse(required-set(r));self.assertEqual(r['evidence_class'],'observed');self.assertEqual(r['unit'],'USD/token');self.assertEqual(len(r['raw_sha256']),64);self.assertIsNone(r['effective_at_utc']);self.assertIsNone(r['published_at_utc']);self.assertNotIn('description',r);ids.append(r['id'])
        self.assertEqual(len(ids),len(set(ids)));self.assertFalse(obj['streaming'])
    def test_restricted_source_gate_and_no_schedule(self):
        p=json.loads((ROOT/'site/data/source-policy.json').read_text());self.assertTrue(p['automated_refresh_allowed']);self.assertFalse(p['recurring_collection_enabled']);self.assertIn('overview/models',p['permission_evidence_url'])
        for f in (ROOT/'.github/workflows').glob('*.yml'):
            self.assertNotIn('cron:',f.read_text())
        self.assertNotIn('push:',(ROOT/'.github/workflows/pages.yml').read_text())
    def test_model_labels_units_and_accessibility(self):
        s=(ROOT/'site/index.html').read_text()
        for text in ['CONDITIONAL SCENARIO','reference = 100','not a statistical confidence interval','No measured global demand curve','aria-live="polite"','Skip to research','November 2025']:
            self.assertIn(text.lower(),s.lower())
        self.assertNotIn('million baskets/year',s);self.assertNotIn('USD per successful basket',s)
    def test_public_build_excludes_private_original_inputs(self):
        with tempfile.TemporaryDirectory() as t:
            out=build(Path(t)/'dist');files=list(out.rglob('*'))
            self.assertTrue((out/'index.html').exists());self.assertFalse(any(p.suffix in {'.pdf','.docx','.pyc'} for p in files))
            self.assertFalse((out/'inputs').exists());self.assertFalse((out/'gpu_calibration_financial_fact_vintages.csv').exists())
    def test_no_external_scripts_or_credentials(self):
        s=(ROOT/'site/index.html').read_text();self.assertNotIn('<script src="https:',s)
        for p in (ROOT/'site').rglob('*'):
            if p.is_file():
                text=p.read_text()
                for secret in ['ghp_','github_pat_','sk-or-v1-','Bearer sk-']:self.assertNotIn(secret,text)
    def test_historical_index_not_global_or_reweighted(self):
        r=json.loads((ROOT/'site/data/gpu-index.json').read_text());self.assertAlmostEqual(r['value'],84.59609438567942);self.assertEqual(r['coverage'],1);self.assertEqual(r['providers'],1);self.assertFalse(r['capacity_verified'])
    def test_no_private_local_paths_in_public_tree(self):
        for p in (ROOT/'site').rglob('*'):
            if p.is_file():self.assertNotIn('/Users/',p.read_text())
    def test_builder_refuses_source_or_unmarked_nonempty_directory(self):
        for dest in [ROOT,ROOT/'site',ROOT/'site/nested']:
            with self.assertRaises(ValueError):build(dest)
        with tempfile.TemporaryDirectory() as t:
            dest=Path(t)/'existing';dest.mkdir();(dest/'unrelated.txt').write_text('preserve')
            with self.assertRaises(ValueError):build(dest)
            self.assertEqual((dest/'unrelated.txt').read_text(),'preserve')

if __name__=='__main__':unittest.main()
