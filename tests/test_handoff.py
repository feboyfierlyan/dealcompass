import unittest
from scripts.check_handoff import HEADINGS, validate_changes, validate_note

NOTE = '\n\n'.join(f'## {h}\nKeterangan aktual.' for h in HEADINGS)

class HandoffTests(unittest.TestCase):
    def test_code_without_handoff_is_rejected(self):
        self.assertTrue(validate_changes(['backend/graph/context.py'], 'bima/data-graph', lambda _: NOTE))

    def test_other_person_note_does_not_satisfy_requirement(self):
        errors = validate_changes(['backend/graph/context.py', 'docs/handoffs/BOY.md'], 'bima/data-graph', lambda _: NOTE)
        self.assertTrue(any('BIMA.md' in x for x in errors))

    def test_empty_heading_is_rejected(self):
        self.assertTrue(validate_note(NOTE.replace('## Blocker\nKeterangan aktual.', '## Blocker')))

    def test_same_owner_code_with_note_passes(self):
        self.assertEqual(validate_changes(['backend/decision/analyze.py', 'docs/handoffs/ICAL.md'], 'ical/decision-jev', lambda _: NOTE), [])

    def test_shared_dependency_and_other_owner_code_rejected(self):
        errors = validate_changes(['frontend/package.json', 'backend/main.py', 'docs/handoffs/BOY.md'], 'boy/frontend', lambda _: NOTE)
        self.assertEqual(len(errors), 2)

    def test_original_dataset_is_protected_even_for_main(self):
        self.assertTrue(validate_changes(['dataset_kasirnusa/crm_deals.csv', 'docs/handoffs/MAIN.md'], 'main/review', lambda _: NOTE))

