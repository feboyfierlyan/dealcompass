"""Check that the benchmark evaluator rejects corrupt provenance and policy output."""
import copy
import unittest
from evaluation.deal_benchmark.run import audit, grade, load_frozen

class BenchmarkEvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.context={'snapshot_date':'2026-10-10','deal':{'deal_id':'D','owner_id':'E'},'evidence':[{'id':'ev'}],'candidate_decisions':[], 'graph':{'nodes':[{'id':'D'},{'id':'A'}],'edges':[{'id':'edge','source':'D','target':'A','evidence_type':'direct','evidence_ids':['ev']}]}}
        self.envelope={'snapshot_date':'2026-10-10','recommendation':{'deal_id':'D','owner_id':'E','action':'USULAN: minta diskon','milestone':'Get decision','evidence_ids':['ev'],'precedent_ids':[],'approvals_needed':['VP Sales: approval required'],'precedent_comparison':[]},'analysis':{'evidence_paths':[{'node_ids':['D','A'],'edge_ids':['edge'],'evidence_ids':['ev']}]}}
    def test_valid_and_reverse_traversal_preserve_original_edge(self):
        self.assertTrue(all(audit(self.context,self.envelope).values()))
        self.envelope['analysis']['evidence_paths'][0]['node_ids']=['A','D']
        self.assertTrue(audit(self.context,self.envelope)['supporting_paths_resolve'])
    def test_nonexistent_citation_and_precedent_are_rejected(self):
        self.envelope['recommendation'].update(evidence_ids=['missing'],precedent_ids=['invented'])
        result=audit(self.context,self.envelope)
        self.assertFalse(result['citation_ids_resolve']);self.assertFalse(result['precedent_ids_resolve'])
    def test_path_order_and_evidence_must_match_edge(self):
        self.context['graph']['nodes'].append({'id':'X'})
        self.envelope['analysis']['evidence_paths'][0]['node_ids']=['D','X']
        self.assertFalse(audit(self.context,self.envelope)['supporting_paths_resolve'])
        self.envelope['analysis']['evidence_paths'][0]['node_ids']=['D','A']
        self.envelope['analysis']['evidence_paths'][0]['evidence_ids']=[]
        self.assertFalse(audit(self.context,self.envelope)['supporting_paths_resolve'])
    def test_wrong_owner_and_missing_required_gate_fail(self):
        case={'expected':{'action_family':'price','vp_gate':True,'comparison_required':False,'capacity_exception_required':False}}
        self.envelope['recommendation'].update(owner_id='OTHER',approvals_needed=[])
        result=grade(case,self.context,self.envelope)
        self.assertFalse(result['owner']);self.assertFalse(result['approval_gate_screen'])
    def test_frozen_suite_has_sixteen_unique_new_deals(self):
        package,cases,manifest=load_frozen()
        self.assertEqual(len(cases),16)
        self.assertEqual(len({c['deal_id'] for c in cases}),16)
        self.assertEqual({c['deal_id'] for c in cases},{d['deal_id'] for d in package['tables']['crm_deals.csv']})
        self.assertTrue(manifest['files'])

class HumanReviewTests(unittest.TestCase):
    def test_unreviewed_never_counts_as_correct(self):
        from evaluation.deal_benchmark.human import summarize, CRITERIA
        rows=[{'case_id':'B01','arm':'hybrid','reviewer':'','notes':'',**{k:None for k in CRITERIA}}]
        for result in summarize(rows).values():self.assertEqual(result,{'passed':0,'reviewed':0,'unreviewed':1})
    def test_completed_review_requires_reviewer_and_reason(self):
        from evaluation.deal_benchmark.human import summarize, CRITERIA
        row={'case_id':'B01','arm':'hybrid','reviewer':'','notes':'',**{k:True for k in CRITERIA}}
        with self.assertRaises(ValueError):summarize([row])
        row.update(reviewer='Independent reviewer',notes='Source span checked')
        self.assertEqual(summarize([row])['action_acceptable']['reviewed'],1)
    def test_duplicate_review_cannot_inflate_denominator(self):
        from evaluation.deal_benchmark.human import summarize, CRITERIA
        row={'case_id':'B01','arm':'hybrid','reviewer':'R','notes':'Reason',**{k:True for k in CRITERIA}}
        with self.assertRaises(ValueError):summarize([row,row])
