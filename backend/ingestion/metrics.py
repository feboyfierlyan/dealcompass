"""Deterministic descriptive metrics for an open prospect at the fixed snapshot."""

from datetime import date
from pathlib import PurePosixPath

from backend.ingestion.dataset import Dataset, SNAPSHOT_DATE, SourceRecord, get_dataset


def evidence_id(record: SourceRecord) -> str:
    """Return the canonical direct-row evidence ID, preserving its source key."""
    return f'{PurePosixPath(record.source_file).name}:{record.source_id}'


def summarize_deal(
    deal_id: str, snapshot_date: str = '2026-10-01', *, dataset: Dataset | None = None,
) -> dict:
    """Count dated focus-account events; external emails do not prove buyer replies.

    Undated/invalid-date rows remain separate evidence, not dated events. Missing
    creation dates leave an explicitly unknown lower bound on the account query.
    Counts describe recorded interactions, not completeness of real-world contact.
    """
    if snapshot_date != SNAPSHOT_DATE.isoformat():
        raise ValueError('Only the fixed business snapshot 2026-10-01 is supported')
    dataset = dataset if dataset is not None else get_dataset()
    record = dataset.by_id['crm_deals.csv'][deal_id]
    deal = record.values
    account_id = deal['account_id']
    account = dataset.by_id['crm_accounts.csv'].get(account_id)
    if (deal.get('status') != 'Terbuka' or account is None
            or account.values.get('tipe') != 'prospek'):
        raise KeyError(deal_id)

    unknowns = []
    deal_evidence_id = evidence_id(record)

    def source_date(value: object, field: str, source_id: str) -> date | None:
        if type(value) is date:
            return value
        reason = 'missing' if value is None else 'invalid'
        unknowns.append(f'{source_id}: {field} is {reason}; date is unknown.')
        return None

    created = source_date(deal.get('dibuat'), 'dibuat', deal_evidence_id)
    stage_since = source_date(deal.get('stage_sejak'), 'stage_sejak', deal_evidence_id)
    deal_age = None
    stage_age = None
    if created is None:
        unknowns.append('Deal creation cutoff is unknown; interactions use account scope with since=null.')
    elif created > SNAPSHOT_DATE:
        unknowns.append(f'{deal_evidence_id}: dibuat is after the snapshot; deal age is unknown.')
    else:
        deal_age = (SNAPSHOT_DATE - created).days
    if stage_since is not None:
        if stage_since > SNAPSHOT_DATE:
            unknowns.append(f'{deal_evidence_id}: stage_sejak is after the snapshot; stage age is unknown.')
        elif created is not None and stage_since < created:
            unknowns.append(f'{deal_evidence_id}: stage_sejak precedes dibuat; stage age is unknown.')
        else:
            stage_age = (SNAPSHOT_DATE - stage_since).days

    groups = {
        name: {'count': 0, 'last_date': None, 'last_evidence_ids': [], 'evidence_ids': []}
        for name in ('customer', 'internal', 'unclassified')
    }
    undated = []
    for interaction in dataset.tables['interactions.jsonl']:
        row = interaction.values
        if row.get('account_id') != account_id:
            continue
        interaction_id = evidence_id(interaction)
        event_date = source_date(row.get('tanggal'), 'tanggal', interaction_id)
        if event_date is not None and (
            event_date > SNAPSHOT_DATE or (created is not None and event_date < created)
        ):
            continue
        kind = row.get('tipe')
        if kind in ('email', 'catatan_meeting'):
            group_name = 'customer'
        elif kind == 'email_internal':
            group_name = 'internal'
        else:
            group_name = 'unclassified'
            unknowns.append(f'{interaction_id}: interaction type {kind!r} is unclassified; customer/internal scope is unknown.')
        if event_date is None:
            undated.append(interaction_id)
            continue
        group = groups[group_name]
        group['count'] += 1
        group['evidence_ids'].append(interaction_id)
        event_iso = event_date.isoformat()
        if group['last_date'] is None or event_iso > group['last_date']:
            group['last_date'] = event_iso
            group['last_evidence_ids'] = [interaction_id]
        elif event_iso == group['last_date']:
            group['last_evidence_ids'].append(interaction_id)

    for group in groups.values():
        group['evidence_ids'].sort()
        group['last_evidence_ids'].sort()
    latest = max((group['last_date'] for group in groups.values() if group['last_date']), default=None)
    latest_ids = sorted({identifier for group in groups.values() if group['last_date'] == latest
                         for identifier in group['last_evidence_ids']})
    return {
        'deal_id': deal_id,
        'account_id': account_id,
        'snapshot_date': snapshot_date,
        'created_date': created.isoformat() if created is not None else None,
        'stage_since': stage_since.isoformat() if stage_since is not None else None,
        'deal_age_days': deal_age,
        'stage_age_days': stage_age,
        'age_evidence_ids': [deal_evidence_id],
        'interactions': {
            'total_count': sum(group['count'] for group in groups.values()),
            'last_date': latest,
            'last_evidence_ids': latest_ids,
            **groups,
            'undated_evidence_ids': sorted(undated),
        },
        'query_scope': {
            'source_file': dataset.source_files['interactions.jsonl'],
            'account_id': account_id,
            'since': created.isoformat() if created is not None else None,
            'through': snapshot_date,
        },
        'unknowns': sorted(unknowns),
    }
