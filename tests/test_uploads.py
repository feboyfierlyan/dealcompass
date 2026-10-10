"""New-data acceptance: isolated sources, changing inputs, provenance, upload boundaries."""
import copy
import io
import json
import os
import tempfile
import unittest
import zipfile
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.api.uploads import template


class UploadTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.env=patch.dict(os.environ,{'DEALCOMPASS_UPLOAD_DIR':self.temp.name,'DEALCOMPASS_ENGINE_MODE':'rules'})
        self.env.start();self.addCleanup(self.env.stop)
        self.client=TestClient(app)

    def upload(self,data=None):
        r=self.client.post('/api/import',json=data or template())
        self.assertEqual(r.status_code,200,r.text)
        return r.json(),{'X-DealCompass-Workspace':r.json()['workspace_id']}

    def test_unseen_ids_snapshot_graph_and_approval(self):
        result,h=self.upload();self.assertEqual(result['deal_count'],1)
        listing=self.client.get('/api/deals',headers=h).json()
        self.assertEqual(listing['snapshot_date'],'2026-10-10')
        self.assertEqual(listing['items'][0]['deal_id'],'OPP01')
        self.assertEqual(listing['items'][0]['stage_age_days'],9)
        c=self.client.get('/api/deals/OPP01',headers=h).json()
        evidence={e['id'] for e in c['evidence']};nodes={n['id'] for n in c['graph']['nodes']}
        for edge in c['graph']['edges']:
            self.assertIn(edge['source'],nodes);self.assertIn(edge['target'],nodes)
            self.assertTrue(set(edge['evidence_ids'])<=evidence)
        a=self.client.post('/api/deals/OPP01/analysis',headers=h).json()
        self.assertEqual(a['analysis']['provider_requests'],0)
        self.assertTrue(a['recommendation']['approvals_needed'])
        self.assertTrue(set(a['recommendation']['evidence_ids'])<=evidence)
        p=self.client.get('/api/pipeline/priorities',headers=h)
        self.assertEqual(p.status_code,200);self.assertEqual(len(p.json()['items']),1)
        self.assertEqual(len(self.client.get('/api/deals').json()['items']),5)
        self.assertEqual(self.client.get('/api/deals/OPP01').status_code,404)

    def test_changed_conversation_changes_result_and_fingerprint(self):
        _,h1=self.upload()
        changed=template();changed['tables']['interactions.jsonl'][0]['isi']='Kami masih mengevaluasi kebutuhan internal. Belum ada jadwal.'
        _,h2=self.upload(changed)
        a=self.client.post('/api/deals/OPP01/analysis',headers=h1).json()
        b=self.client.post('/api/deals/OPP01/analysis',headers=h2).json()
        self.assertNotEqual(a['analysis']['context_fingerprint'],b['analysis']['context_fingerprint'])
        self.assertTrue(a['recommendation']['approvals_needed']);self.assertFalse(b['recommendation']['approvals_needed'])

    def test_changed_pipeline_changes_priority(self):
        data=template(); t=data['tables']
        for filename in list(t):
            row=json.loads(json.dumps(t[filename][0]).replace('01','02').replace('jamie@','taylor@').replace('Jamie Lee','Taylor Smith').replace('Northstar Retail','Second Retail'))
            # Keep dates unchanged when replacing IDs.
            for field,value in t[filename][0].items():
                if field in ('stage_sejak','dibuat','tanggal'):row[field]=value
            t[filename].append(row)
        t['crm_deals.csv'][1]['nilai_tahunan']='300000000'
        _,h1=self.upload(data)
        p1=self.client.get('/api/pipeline/priorities',headers=h1).json()
        self.assertEqual(p1['items'][0]['deal_id'],'OPP02')
        t['crm_deals.csv'][0]['nilai_tahunan']='500000000'
        _,h2=self.upload(data);p2=self.client.get('/api/pipeline/priorities',headers=h2).json()
        self.assertEqual(p2['items'][0]['deal_id'],'OPP01')

    def test_workspace_isolation_under_concurrent_reads(self):
        _,one=self.upload();data=template();data['tables']['crm_accounts.csv'][0]['nama']='Separate Client'
        _,two=self.upload(data)
        def read(h):return self.client.get('/api/deals',headers=h).json()['items'][0]['account_name']
        with ThreadPoolExecutor(max_workers=4) as pool:
            names=list(pool.map(read,[one,two]*5))
        self.assertEqual(names,['Northstar Retail','Separate Client']*5)

    def test_no_jev_export_without_upload_consent(self):
        _,h=self.upload()
        with patch.dict(os.environ,{'DEALCOMPASS_ENGINE_MODE':'jev'}),patch('backend.integrations.jev.client_from_env') as provider:
            result=self.client.post('/api/deals/OPP01/analysis',headers=h).json()
            self.assertEqual(result['analysis']['outcome'],'rules_only');provider.assert_not_called()

    def test_csv_transcript_zip_round_trip(self):
        kit=self.client.get('/api/import/template.zip')
        r=self.client.post('/api/import',content=kit.content,headers={'Content-Type':'application/zip'})
        self.assertEqual(r.status_code,200,r.text);self.assertEqual(r.json()['deal_count'],1)

    def test_six_new_deals_have_complete_ranking_and_diagnostics(self):
        data=template(); original=copy.deepcopy(data['tables'])
        for i in range(2,7):
            for filename,rows in original.items():
                row=json.dumps(rows[0])
                for prefix in ('ACME','SELLER','BUYER','OPP','CALL'):
                    row=row.replace(prefix+'01',prefix+f'{i:02d}')
                row=row.replace('jamie@',f'jamie{i}@').replace('alex@',f'alex{i}@')
                data['tables'][filename].append(json.loads(row))
        _,h=self.upload(data)
        ranking=self.client.get('/api/pipeline/priorities',headers=h)
        self.assertEqual(ranking.status_code,200,ranking.text)
        self.assertEqual(sorted(r['rank'] for r in ranking.json()['items']),list(range(1,7)))
        diagnostics=self.client.get('/api/pipeline/initial-analysis',headers=h)
        self.assertEqual(diagnostics.status_code,200,diagnostics.text)
        self.assertEqual(len(diagnostics.json()['deals']),6)

    def test_reject_invalid_references_dates_duplicates_and_large_uploads(self):
        for field,value in [('owner_id','MISSING'),('stage_sejak','2027-01-01'),('nilai_tahunan','-1')]:
            data=template();data['tables']['crm_deals.csv'][0][field]=value
            self.assertEqual(self.client.post('/api/import',json=data).status_code,422)
        data=template();data['tables']['crm_deals.csv']*=2
        self.assertEqual(self.client.post('/api/import',json=data).status_code,422)
        self.assertEqual(self.client.post('/api/import',content=b'x'*2_000_001).status_code,413)
        self.assertEqual(self.client.get('/api/deals',headers={'X-DealCompass-Workspace':'../dataset_kasirnusa'}).status_code,404)

    def test_reject_zip_path_traversal_and_missing_transcripts_are_explicit(self):
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z:z.writestr('../overwrite.csv','x')
        self.assertEqual(self.client.post('/api/import',content=buf.getvalue(),headers={'Content-Type':'application/zip'}).status_code,422)
        data=template();del data['tables']['interactions.jsonl']
        result,h=self.upload(data);self.assertTrue(any('No conversations' in w for w in result['warnings']))
        a=self.client.post('/api/deals/OPP01/analysis',headers=h).json()
        self.assertEqual(a['analysis']['analysis_status'],'insufficient_evidence')
