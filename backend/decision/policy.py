"""Aturan bisnis deterministik ICAL-01. Semua uang dalam IDR integer.

Setiap konstanta menyebut sumbernya. Modul ini tidak membaca dataset;
konteks deal datang dari DealContext (Bima).
"""
from datetime import date, timedelta

# contracts_billing.csv kolom harga_per_outlet_bulan (seluruh 40 kontrak = 350000).
PRICE_PER_OUTLET_MONTH_IDR = 350_000
# dataset_kasirnusa/README.md, crm_accounts.paket: Starter maks 10, Growth maks 25, Enterprise tanpa batas.
PACKAGE_OUTLET_LIMITS: dict[str, int | None] = {'Starter': 10, 'Growth': 25, 'Enterprise': None}
# dataset_kasirnusa/README.md: diskon di atas 10% wajib disetujui VP Sales dan dicatat di decision_log.
DISCOUNT_APPROVAL_THRESHOLD_PCT = 10
DISCOUNT_APPROVER_ROLE = 'VP Sales'


def annual_value_idr(outlets: int, discount_pct: int = 0) -> int:
    """Nilai tahunan = outlet x harga/bulan x 12 x (100 - diskon)/100, integer."""
    if outlets < 0 or not 0 <= discount_pct <= 100:
        raise ValueError('outlet harus >= 0 dan diskon 0..100')
    gross = outlets * PRICE_PER_OUTLET_MONTH_IDR * 12
    net, rem = divmod(gross * (100 - discount_pct), 100)
    if rem:
        raise ValueError('hasil tidak bulat dalam rupiah; periksa input')
    return net


def requires_vp_approval(discount_pct: int) -> bool:
    return discount_pct > DISCOUNT_APPROVAL_THRESHOLD_PCT


def fits_package(package: str, outlets: int) -> bool:
    limit = PACKAGE_OUTLET_LIMITS[package]
    return limit is None or outlets <= limit


def smallest_package(outlets: int) -> str:
    return next(p for p in PACKAGE_OUTLET_LIMITS if fits_package(p, outlets))


def stage_start(snapshot_date: str, stage_age_days: int) -> str:
    return (date.fromisoformat(snapshot_date) - timedelta(days=stage_age_days)).isoformat()


def rupiah(value: int) -> str:
    return 'Rp' + f'{value:,}'.replace(',', '.')
