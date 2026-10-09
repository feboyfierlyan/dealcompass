"""SYNTHETIC/MOCK ranking contracts, not business-ranking evaluations or live smoke."""
from copy import deepcopy
import unittest

from backend.api.priorities import validate_priorities
from backend.decision.analyze import analyze_deal_trace
from backend.graph.analysis import analyze_pipeline_initial
from backend.graph.context import build_deal_context


def mock_priorities(contexts, diagnostics) -> dict:
    """Arbitrary reverse-input MOCK ordering with real sources and rules actions.

    This fixture computes no ranking method and makes no ranking-quality claim.
    It is reusable by the real-HTTP mock smoke, separately from live integration.
    """
    reports = {report['deal_id']: report for report in diagnostics}
    items = []
    for rank, context in enumerate(reversed(contexts), 1):
        recommendation, trace = analyze_deal_trace(context, mode='rules')
        registry = {record.id: record.model_dump() for record in context.evidence}
        for record in reports[context.deal.deal_id]['evidence']:
            if record['id'] in registry and registry[record['id']] != record:
                raise ValueError('Synthetic fixture has conflicting source records.')
            registry[record['id']] = deepcopy(record)
        paths = []
        if context.graph.edges:
            edge = context.graph.edges[0]
            paths.append(dict(node_ids=[edge.source, edge.target], edge_ids=[edge.id],
                              evidence_ids=list(edge.evidence_ids), fixture_note='Original directed edge, MOCK selection.'))
        items.append(dict(deal_id=context.deal.deal_id, account_id=context.deal.account_id,
            rank=rank, priority_kind='discovery' if trace.analysis_status == 'insufficient_evidence' else 'acceleration',
            analysis_status=trace.analysis_status,
            rationale=['SYNTHETIC/MOCK: reverse input order only; not a sales priority conclusion.'],
            factors=[dict(name='mock_order', value=None, effect='Unknown business ordering; not scored.', evidence_ids=[])],
            recommendation=recommendation.model_dump(), evidence_ids=sorted(registry),
            evidence=list(registry.values()), evidence_paths=paths,
            limitations=['SYNTHETIC/MOCK ordering is arbitrary; no business ranking has been computed.',
                         'Source coverage does not establish missing business facts.'],
            fixture_label='SYNTHETIC/MOCK'))
    return dict(schema_version='v1', snapshot_date='2026-10-01', engine_mode='rules',
        methodology=dict(id='synthetic-contract-fixture', label='SYNTHETIC/MOCK — not a ranking method',
            description='Arbitrary reverse-input ordering tests wire validation only, not business ranking.',
            ordered_rules=['Reverse supplied contexts for the MOCK fixture only.'],
            tie_breakers=[], limitations=['No business ordering or historical outcome validation.']),
        items=items, limitations=['SYNTHETIC/MOCK: not validated against historical closing outcomes; not closing probabilities.'],
        fixture_label='SYNTHETIC/MOCK')


def make_synthetic_priority_inputs():
    """Load the complete real canonical prospect set, without any Jev calls."""
    reports = analyze_pipeline_initial()['deals']
    contexts = [build_deal_context(report['deal_id']) for report in reports]
    return contexts, reports, mock_priorities(contexts, reports)


class PrioritiesContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contexts, cls.diagnostics, cls.fixture = make_synthetic_priority_inputs()

    def assert_invalid(self, payload, contexts=None, diagnostics=None):
        with self.assertRaises(ValueError):
            validate_priorities(payload, self.contexts if contexts is None else contexts,
                                self.diagnostics if diagnostics is None else diagnostics)


    def test_missing_duplicate_and_invalid_rank_order(self):
        mutations = [lambda p: p['items'].pop(),
                     lambda p: p['items'].__setitem__(1, deepcopy(p['items'][0])),
                     lambda p: p['items'][0].__setitem__('rank', True),
                     lambda p: p['items'][0].__setitem__('rank', 1.0),
                     lambda p: p['items'][-1].__setitem__('rank', 6),
                     lambda p: p['items'].reverse()]
        for mutate in mutations:
            payload = deepcopy(self.fixture)
            mutate(payload)
            with self.subTest(mutation=mutate):
                self.assert_invalid(payload)

    def test_invalid_account_snapshot_engine_and_status(self):
        for field, value in [('account_id', 'FOREIGN'), ('analysis_status', 'not_analyzed'),
                             ('priority_kind', 'closing')]:
            payload = deepcopy(self.fixture)
            payload['items'][0][field] = value
            self.assert_invalid(payload)
        for field, value in [('schema_version', 'v2'), ('snapshot_date', '2026-10-02'), ('engine_mode', 'jev')]:
            payload = deepcopy(self.fixture)
            payload[field] = value
            self.assert_invalid(payload)
        for field, value in [('deal_id', 'FOREIGN'), ('engine_mode', 'replay'), ('schema_version', 'v2')]:
            payload = deepcopy(self.fixture)
            payload['items'][0]['recommendation'][field] = value
            self.assert_invalid(payload)

    def test_missing_required_fields_and_invalid_factors(self):
        for field in ('rationale', 'factors', 'recommendation', 'evidence_paths', 'limitations'):
            payload = deepcopy(self.fixture)
            del payload['items'][0][field]
            self.assert_invalid(payload)
        for field in ('precedent_comparison', 'approvals_needed', 'unknowns', 'owner_id'):
            payload = deepcopy(self.fixture)
            del payload['items'][0]['recommendation'][field]
            self.assert_invalid(payload)
        for value in (True, float('nan'), float('inf'), [], {}):
            payload = deepcopy(self.fixture)
            payload['items'][0]['factors'][0]['value'] = value
            self.assert_invalid(payload)
        for value in (0, 1.5, 'unknown', None):
            payload = deepcopy(self.fixture)
            payload['items'][0]['factors'][0]['value'] = value
            self.assertIs(validate_priorities(payload, self.contexts, self.diagnostics), payload)

    def test_conflicting_and_fabricated_source_and_missing_nested_reference(self):
        reports = deepcopy(self.diagnostics)
        context = self.contexts[0]
        report = next(r for r in reports if r['deal_id'] == context.deal.deal_id)
        report['evidence'].append(dict(context.evidence[0].model_dump(), excerpt='SECRET provider payload'))
        self.assert_invalid(deepcopy(self.fixture), diagnostics=reports)
        payload = deepcopy(self.fixture)
        payload['items'][0]['evidence'][0]['excerpt'] = 'fabricated'
        self.assert_invalid(payload)
        payload = deepcopy(self.fixture)
        payload['items'][0]['evidence'].append(dict(payload['items'][0]['evidence'][0], id='fabricated:source'))
        self.assert_invalid(payload)
        payload = deepcopy(self.fixture)
        payload['items'][0]['evidence'].append(deepcopy(payload['items'][0]['evidence'][0]))
        self.assert_invalid(payload)
        payload = deepcopy(self.fixture)
        payload['items'][0]['recommendation']['extra_provenance'] = {'nested_evidence_ids': ['fabricated:source']}
        self.assert_invalid(payload)
        payload = deepcopy(self.fixture)
        payload['items'][0]['evidence'].pop()
        self.assert_invalid(payload)

    def test_reverse_traversal_of_original_edge_is_accepted(self):
        # R8: walking an original edge against its arrow is a valid traversal; the edge is not rewritten.
        payload = deepcopy(self.fixture)
        item = next(item for item in payload['items'] if item['evidence_paths'])
        item['evidence_paths'][0]['node_ids'].reverse()
        self.assertIs(validate_priorities(payload, self.contexts, self.diagnostics), payload)
        context = next(c for c in self.contexts if c.deal.deal_id == 'DL-002')
        edges = {(e.source, e.target, e.relation): e for e in context.graph.edges}
        deal_for = next(e for (s, t, r), e in edges.items() if (s, t, r) == ('DL-002', 'P02', 'deal_for'))
        interaction_for = next(e for (s, t, r), e in edges.items() if (s, t, r) == ('I0348', 'P02', 'interaction_for'))
        payload = deepcopy(self.fixture)
        target = next(i for i in payload['items'] if i['deal_id'] == 'DL-002')
        ids = sorted(set(deal_for.evidence_ids) | set(interaction_for.evidence_ids))
        target['evidence_paths'] = [dict(node_ids=['DL-002', 'P02', 'I0348'], edge_ids=[deal_for.id, interaction_for.id],
                                         evidence_ids=ids)]
        registered = {e['id'] for e in target['evidence']}
        self.assertLessEqual(set(ids), registered)
        self.assertIs(validate_priorities(payload, self.contexts, self.diagnostics), payload)
        self.assertEqual((interaction_for.source, interaction_for.target), ('I0348', 'P02'))

    def test_paths_reject_disconnected_fabricated_shortcut_and_missing_edge_sources(self):
        context = next(c for c in self.contexts if c.deal.deal_id == 'DL-002')
        by_key = {(e.source, e.target, e.relation): e for e in context.graph.edges}
        deal_for, interaction_for = by_key[('DL-002', 'P02', 'deal_for')], by_key[('I0348', 'P02', 'interaction_for')]
        for change in ('self_pair', 'disconnected_order', 'edge', 'node', 'shortcut', 'length', 'coverage'):
            payload = deepcopy(self.fixture)
            item = next(item for item in payload['items'] if item['evidence_paths'])
            path = item['evidence_paths'][0]
            if change == 'self_pair':
                path['node_ids'][1] = path['node_ids'][0]
            elif change == 'disconnected_order':
                item = next(i for i in payload['items'] if i['deal_id'] == 'DL-002')
                # Same original edges, but P02 -> DL-002 -> I0348: DL-002 and I0348 are not joined by interaction_for.
                item['evidence_paths'] = [dict(node_ids=['P02', 'DL-002', 'I0348'], edge_ids=[deal_for.id, interaction_for.id],
                                               evidence_ids=sorted(set(deal_for.evidence_ids) | set(interaction_for.evidence_ids)))]
            elif change == 'edge':
                path['edge_ids'][0] = 'fabricated-edge'
            elif change == 'node':
                path['node_ids'][1] = 'fabricated-node'
            elif change == 'shortcut':
                context = next(c for c in self.contexts if c.deal.deal_id == item['deal_id'])
                path['node_ids'][1] = next(node.id for node in context.graph.nodes
                                           if node.id not in path['node_ids'])
            elif change == 'length':
                path['node_ids'].append(path['node_ids'][0])
            else:
                path['evidence_ids'] = []
            with self.subTest(change=change):
                self.assert_invalid(payload)

    def test_foreign_precedent_and_nonfinite_extra_fields(self):
        payload = deepcopy(self.fixture)
        payload['items'][0]['recommendation']['precedent_ids'].append('FOREIGN')
        self.assert_invalid(payload)
        for value in (float('nan'), float('inf'), float('-inf')):
            payload = deepcopy(self.fixture)
            payload['items'][0]['evidence'][0]['extra_provenance'] = {'number': value}
            self.assert_invalid(payload)
            payload = deepcopy(self.fixture)
            payload['extra'] = {'number': value}
            self.assert_invalid(payload)

    def test_envelope_and_methodology_sources_must_also_be_registered(self):
        for location in ('methodology', 'root'):
            payload = deepcopy(self.fixture)
            target = payload['methodology'] if location == 'methodology' else payload
            target['extra_provenance'] = {'source_evidence_ids': ['SYNTHETIC:unresolved']}
            with self.subTest(location=location):
                self.assert_invalid(payload)

    def test_inputs_are_paired_by_id_and_mismatches_rejected(self):
        self.assertIs(validate_priorities(self.fixture, list(reversed(self.contexts)),
                                         list(reversed(self.diagnostics))), self.fixture)
        self.assert_invalid(self.fixture, diagnostics=self.diagnostics[:-1])
        self.assert_invalid(self.fixture, contexts=self.contexts + [self.contexts[0]])
        reports = deepcopy(self.diagnostics)
        reports[0]['snapshot_date'] = '2026-10-02'
        self.assert_invalid(self.fixture, diagnostics=reports)
        reports = deepcopy(self.diagnostics)
        reports[0]['account_id'] = 'FOREIGN'
        self.assert_invalid(self.fixture, diagnostics=reports)
