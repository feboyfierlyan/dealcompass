"""Deal summaries from the shared typed source snapshot."""

from datetime import date

from backend.contracts import DealSummary
from backend.ingestion.dataset import Dataset, SourceRecord, get_dataset


def deal_summary(
    record: SourceRecord, dataset: Dataset, snapshot_date: date | None = None,
) -> DealSummary:
    from backend.ingestion.scope import snapshot_date as active_snapshot
    snapshot_date = snapshot_date or active_snapshot()
    deal = record.values
    account = dataset.by_id['crm_accounts.csv'][deal['account_id']].values
    return DealSummary(
        deal_id=deal['deal_id'],
        account_id=deal['account_id'],
        account_name=account['nama'],
        stage=deal['stage'],
        stage_age_days=(snapshot_date - deal['stage_sejak']).days,
        annual_value=deal['nilai_tahunan'],
        owner_id=deal['owner_id'],
    )


def list_deals() -> list[DealSummary]:
    dataset = get_dataset()
    return [
        deal_summary(record, dataset)
        for record in dataset.tables['crm_deals.csv']
        if record.values['status'] == 'Terbuka'
        and dataset.by_id['crm_accounts.csv'][record.values['account_id']].values['tipe'] == 'prospek'
    ]
