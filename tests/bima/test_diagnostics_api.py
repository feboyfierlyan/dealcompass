"""Lossless API validator tests with real contexts; corruptions are synthetic."""
from copy import deepcopy
import json
import unittest

from backend.api.diagnostics import validate_deal_diagnostic, validate_pipeline_diagnostic
from backend.api.provenance import collect_evidence_ids, validate_evidence_registry, validate_json
from backend.graph.analysis import analyze_deal_initial, analyze_pipeline_initial
from backend.graph.context import build_deal_context
from backend.ingestion.dataset import get_dataset


class DiagnosticValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = analyze_pipeline_initial()
        cls.contexts = [build_deal_context(report['deal_id']) for report in cls.pipeline['deals']]
        cls.reports = {report['deal_id']: report for report in cls.pipeline['deals']}
        cls.context_map = {context.deal.deal_id: context for context in cls.contexts}


    def test_pipeline_preserves_nested_reports_and_not_assessed_nulls(self):
        report = {'schema_version': 'v1', **deepcopy(self.pipeline)}
        result = validate_pipeline_diagnostic(report, list(reversed(self.contexts)))
        self.assertTrue(all('schema_version' not in deal for deal in result['deals']))
        assessment = result['statistical_assessment']
        self.assertEqual(assessment['status'], 'not_assessed')
        for field in ('method', 'threshold', 'outlier_deal_ids'):
            self.assertIsNone(assessment[field])

    def test_every_direct_excerpt_matches_original_source_row(self):
        dataset = get_dataset()
        for context in self.contexts:
            result = validate_deal_diagnostic(deepcopy(self.reports[context.deal.deal_id]), context)
            registry = {record['id']: record for record in result['evidence']}
            self.assertLessEqual(collect_evidence_ids(result), registry.keys())
            for identifier, record in registry.items():
                with self.subTest(evidence=identifier):
                    filename, source_id = identifier.split(':', 1)
                    source = dataset.by_id[filename][source_id]
                    self.assertEqual(record['source_file'], source.source_file)
                    self.assertEqual(record['source_id'], source.source_id)
                    self.assertEqual(json.loads(record['excerpt']), source.raw)
                    self.assertEqual(record['evidence_type'], 'direct')

    def test_additional_root_nested_and_evidence_provenance_is_retained(self):
        report = deepcopy(self.reports['DL-002'])
        identifier = report['evidence'][0]['id']
        report['extension'] = {'scope': {'audit_evidence_ids': [identifier]}, 'nullable': None}
        report['metrics']['query_scope']['additional_provenance'] = {'checked': True}
        report['findings'][0]['additional_provenance'] = {'source_evidence_ids': [identifier]}
        report['evidence'][0]['additional_provenance'] = {'line_locator': 'synthetic annotation; not business evidence'}
        before = deepcopy(report)
        self.assertEqual(validate_deal_diagnostic(report, self.context_map['DL-002']), before)

    def test_p05_zero_null_and_unknown_boundaries_remain_successful(self):
        report = deepcopy(self.reports['DL-005'])
        result = validate_deal_diagnostic(report, self.context_map['DL-005'])
        interactions = result['metrics']['interactions']
        self.assertEqual(interactions['total_count'], 0)
        self.assertIsNone(interactions['last_date'])
        self.assertEqual(interactions['last_evidence_ids'], [])
        for group in ('customer', 'internal', 'unclassified'):
            self.assertEqual(interactions[group]['count'], 0)
            self.assertIsNone(interactions[group]['last_date'])
        gap = next(finding for finding in result['findings'] if finding['category'] == 'data_gap')
        self.assertEqual(gap['search_scope'], report['metrics']['query_scope'])

    def test_synthetic_missing_required_report_and_metric_fields_are_rejected(self):
        for path in (('metrics',), ('findings',), ('reference_candidates',), ('boundaries',), ('evidence',),
                     ('metrics', 'unknowns'), ('metrics', 'query_scope'),
                     ('metrics', 'interactions', 'customer', 'count'),
                     ('metrics', 'interactions', 'customer', 'last_date'),
                     ('metrics', 'interactions', 'customer', 'last_evidence_ids')):
            with self.subTest(path=path):
                report = deepcopy(self.reports['DL-002'])
                target = report
                for key in path[:-1]:
                    target = target[key]
                del target[path[-1]]
                with self.assertRaises(ValueError):
                    validate_deal_diagnostic(report, self.context_map['DL-002'])

    def test_synthetic_scope_and_version_corruption_is_rejected(self):
        for path, value in ((('snapshot_date',), '2026-09-01'), (('account_id',), 'P01'),
                            (('deal_id',), 'DL-001'), (('schema_version',), 'v2'),
                            (('metrics', 'account_id'), 'P01'), (('metrics', 'deal_id'), 'DL-001'),
                            (('metrics', 'snapshot_date'), '2026-09-01'),
                            (('metrics', 'query_scope', 'account_id'), 'P01'),
                            (('metrics', 'query_scope', 'through'), '2026-09-01')):
            with self.subTest(path=path):
                report = deepcopy(self.reports['DL-002'])
                target = report
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                with self.assertRaises(ValueError):
                    validate_deal_diagnostic(report, self.context_map['DL-002'])

    def test_synthetic_canonical_evidence_corruption_is_rejected(self):
        for field, value in (('id', 'synthetic:unknown'), ('source_id', 'synthetic-key'),
                             ('source_file', 'synthetic.csv'), ('excerpt', '{"synthetic": true}'),
                             ('date', '1900-01-01'), ('evidence_type', 'inferred')):
            with self.subTest(field=field):
                report = deepcopy(self.reports['DL-002'])
                report['evidence'][0][field] = value
                with self.assertRaises(ValueError):
                    validate_deal_diagnostic(report, self.context_map['DL-002'])

    def test_synthetic_duplicate_missing_and_unregistered_evidence_are_rejected(self):
        duplicate = deepcopy(self.reports['DL-002'])
        duplicate['evidence'].append(deepcopy(duplicate['evidence'][0]))
        missing = deepcopy(self.reports['DL-002'])
        missing['evidence'] = []
        unresolved = deepcopy(self.reports['DL-002'])
        unresolved['extra'] = {'deep': [{'audit_evidence_ids': ['synthetic:unknown']}]}
        invalid_ids = deepcopy(self.reports['DL-002'])
        invalid_ids['extra'] = {'audit_evidence_ids': 'not-an-array'}
        for report in (duplicate, missing, unresolved, invalid_ids):
            with self.assertRaises(ValueError):
                validate_deal_diagnostic(report, self.context_map['DL-002'])

    def test_synthetic_nested_nonfinite_values_are_rejected(self):
        for number in (float('nan'), float('inf'), float('-inf')):
            with self.subTest(number=repr(number)):
                report = deepcopy(self.reports['DL-002'])
                report['extra'] = {'nested': [{'number': number}]}
                with self.assertRaises(ValueError):
                    validate_deal_diagnostic(report, self.context_map['DL-002'])
                with self.assertRaises(ValueError):
                    validate_json(report)

    def test_synthetic_pipeline_missing_duplicate_scope_and_statistical_corruption(self):
        variants = []
        report = deepcopy(self.pipeline)
        report['deals'].pop()
        variants.append(report)
        report = deepcopy(self.pipeline)
        report['deals'][-1] = deepcopy(report['deals'][0])
        variants.append(report)
        for field, value in (('snapshot_date', '2026-09-01'), ('account_id', 'synthetic-account')):
            report = deepcopy(self.pipeline)
            report['deals'][0][field] = value
            variants.append(report)
        for field, value in (('evidence_ids', ['synthetic:unknown']), ('sample_size', 4),
                             ('method', 'synthetic-method'), ('threshold', float('inf'))):
            report = deepcopy(self.pipeline)
            report['statistical_assessment'][field] = value
            variants.append(report)
        report = deepcopy(self.pipeline)
        del report['statistical_assessment']['outlier_deal_ids']
        variants.append(report)
        for index, report in enumerate(variants):
            with self.subTest(synthetic_corruption=index), self.assertRaises(ValueError):
                validate_pipeline_diagnostic(report, self.contexts)

    def test_pipeline_statistical_context_union_and_extra_fields_are_retained(self):
        report = deepcopy(self.pipeline)
        identifier = self.contexts[0].evidence[0].id
        report['statistical_assessment']['additional_evidence_ids'] = [identifier]
        report['additional_provenance'] = {'snapshot_basis': 'real canonical contexts'}
        before = deepcopy(report)
        self.assertEqual(validate_pipeline_diagnostic(report, self.contexts), before)

    def test_registry_requires_strict_evidence_schema(self):
        canonical = self.contexts[0].evidence[0].model_dump()
        record = {**canonical, 'additional_provenance': {'nullable': None}}
        invalid = {**record, 'source_id': 123}
        with self.assertRaises(ValueError):
            validate_evidence_registry([invalid], {canonical['id']: canonical})
        with self.assertRaises(ValueError):
            collect_evidence_ids({'nested': {'source_evidence_ids': [123]}})


if __name__ == '__main__':
    unittest.main()
