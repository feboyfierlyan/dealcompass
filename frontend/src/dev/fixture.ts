// Development-only UI fixtures. Evidence is copied from the named source records.
// Graph is a small projection of the real backend context. Recommendation is illustrative, never a Jev result.
import { ApiError } from '../lib/api';
import type { DealApi } from '../lib/api';
import type { DealList, DealContext, Recommendation } from '../lib/contracts';
export const fixtureList = {
  "schema_version": "v1",
  "snapshot_date": "2026-10-01",
  "items": [
    {
      "deal_id": "DL-001",
      "account_id": "P01",
      "account_name": "Grup Ritel Mandala",
      "stage": "Proposal",
      "stage_age_days": 20,
      "annual_value": 252000000,
      "owner_id": "E06",
      "rank": null,
      "analysis_status": "not_analyzed"
    },
    {
      "deal_id": "DL-002",
      "account_id": "P02",
      "account_name": "Teras Kafe Group",
      "stage": "Demo",
      "stage_age_days": 45,
      "annual_value": 63000000,
      "owner_id": "E07",
      "rank": null,
      "analysis_status": "not_analyzed"
    },
    {
      "deal_id": "DL-003",
      "account_id": "P03",
      "account_name": "Klinik Pratama Medika",
      "stage": "Discovery",
      "stage_age_days": 10,
      "annual_value": 37800000,
      "owner_id": "E08",
      "rank": null,
      "analysis_status": "not_analyzed"
    },
    {
      "deal_id": "DL-004",
      "account_id": "P04",
      "account_name": "Nirwana Hotel & Resto",
      "stage": "Negosiasi",
      "stage_age_days": 30,
      "annual_value": 147000000,
      "owner_id": "E06",
      "rank": null,
      "analysis_status": "not_analyzed"
    },
    {
      "deal_id": "DL-005",
      "account_id": "P05",
      "account_name": "PT Distribusi Sumber Rejeki",
      "stage": "Lead",
      "stage_age_days": 5,
      "annual_value": 168000000,
      "owner_id": "E07",
      "rank": null,
      "analysis_status": "not_analyzed"
    }
  ]
} satisfies DealList;
export const fixtureContext = {
  "schema_version": "v1",
  "snapshot_date": "2026-10-01",
  "deal": {
    "deal_id": "DL-002",
    "account_id": "P02",
    "account_name": "Teras Kafe Group",
    "stage": "Demo",
    "stage_age_days": 45,
    "annual_value": 63000000,
    "owner_id": "E07",
    "rank": null,
    "analysis_status": "not_analyzed"
  },
  "evidence": [
    {
      "id": "crm_accounts.csv:C23",
      "source_file": "dataset_kasirnusa/crm_accounts.csv",
      "source_id": "C23",
      "date": null,
      "excerpt": "{\"account_id\": \"C23\", \"nama\": \"Kafe Senja\", \"tipe\": \"pelanggan\", \"industri\": \"F&B\", \"kota\": \"Mojokerto\", \"paket\": \"Starter\", \"jumlah_outlet\": \"6\", \"account_owner_id\": \"E03\", \"champion_contact_id\": \"K095\", \"nps_terakhir\": \"8\", \"health_score_dashboard\": \"Hijau\"}",
      "evidence_type": "direct"
    },
    {
      "id": "crm_accounts.csv:P02",
      "source_file": "dataset_kasirnusa/crm_accounts.csv",
      "source_id": "P02",
      "date": null,
      "excerpt": "{\"account_id\": \"P02\", \"nama\": \"Teras Kafe Group\", \"tipe\": \"prospek\", \"industri\": \"F&B\", \"kota\": \"Malang\", \"paket\": \"\", \"jumlah_outlet\": \"15\", \"account_owner_id\": \"E07\", \"champion_contact_id\": \"\", \"nps_terakhir\": \"\", \"health_score_dashboard\": \"\"}",
      "evidence_type": "direct"
    },
    {
      "id": "crm_deals.csv:DL-002",
      "source_file": "dataset_kasirnusa/crm_deals.csv",
      "source_id": "DL-002",
      "date": "2026-07-25",
      "excerpt": "{\"deal_id\": \"DL-002\", \"account_id\": \"P02\", \"tipe\": \"baru\", \"stage\": \"Demo\", \"stage_sejak\": \"2026-08-17\", \"dibuat\": \"2026-07-25\", \"owner_id\": \"E07\", \"outlet\": \"15\", \"nilai_tahunan\": \"63000000\", \"status\": \"Terbuka\", \"alasan_kalah\": \"\", \"kompetitor\": \"KasirPro\"}",
      "evidence_type": "direct"
    },
    {
      "id": "crm_deals.csv:DL-006",
      "source_file": "dataset_kasirnusa/crm_deals.csv",
      "source_id": "DL-006",
      "date": "2025-01-20",
      "excerpt": "{\"deal_id\": \"DL-006\", \"account_id\": \"C23\", \"tipe\": \"baru\", \"stage\": \"Closed Lost\", \"stage_sejak\": \"2025-03-14\", \"dibuat\": \"2025-01-20\", \"owner_id\": \"E07\", \"outlet\": \"6\", \"nilai_tahunan\": \"25200000\", \"status\": \"Kalah\", \"alasan_kalah\": \"Harga\", \"kompetitor\": \"KasirPro\"}",
      "evidence_type": "direct"
    },
    {
      "id": "crm_deals.csv:DL-007",
      "source_file": "dataset_kasirnusa/crm_deals.csv",
      "source_id": "DL-007",
      "date": "2025-08-11",
      "excerpt": "{\"deal_id\": \"DL-007\", \"account_id\": \"C23\", \"tipe\": \"baru\", \"stage\": \"Closed Won\", \"stage_sejak\": \"2025-09-08\", \"dibuat\": \"2025-08-11\", \"owner_id\": \"E07\", \"outlet\": \"6\", \"nilai_tahunan\": \"25200000\", \"status\": \"Menang\", \"alasan_kalah\": \"\", \"kompetitor\": \"KasirPro\"}",
      "evidence_type": "direct"
    },
    {
      "id": "decision_log.csv:D-2025-02",
      "source_file": "dataset_kasirnusa/decision_log.csv",
      "source_id": "D-2025-02",
      "date": "2025-03-04",
      "excerpt": "{\"decision_id\": \"D-2025-02\", \"tanggal\": \"2025-03-04\", \"tipe\": \"diskon\", \"account_id\": \"C23\", \"deal_id\": \"DL-006\", \"diminta_oleh\": \"E07\", \"diputuskan_oleh\": \"E01\", \"keputusan\": \"Ditolak\", \"nilai\": \"20%\", \"alasan\": \"Di atas batas 15%; menyamai harga kompetitor merusak harga pasar. Deal kemudian kalah karena harga.\", \"bukti_interaction_id\": \"\", \"fitur_dijanjikan\": \"\", \"status_janji\": \"\"}",
      "evidence_type": "direct"
    },
    {
      "id": "decision_log.csv:D-2025-06",
      "source_file": "dataset_kasirnusa/decision_log.csv",
      "source_id": "D-2025-06",
      "date": "2025-08-12",
      "excerpt": "{\"decision_id\": \"D-2025-06\", \"tanggal\": \"2025-08-12\", \"tipe\": \"pengecualian\", \"account_id\": \"C23\", \"deal_id\": \"DL-007\", \"diminta_oleh\": \"E07\", \"diputuskan_oleh\": \"E01\", \"keputusan\": \"Disetujui\", \"nilai\": \"Paket Starter tanpa diskon, pilot 6 outlet\", \"alasan\": \"Pendekatan alternatif setelah kalah Maret: mulai dari Starter, naik paket bila puas. Deal menang Sep 2025.\", \"bukti_interaction_id\": \"\", \"fitur_dijanjikan\": \"\", \"status_janji\": \"\"}",
      "evidence_type": "direct"
    },
    {
      "id": "interactions.jsonl:I0296",
      "source_file": "dataset_kasirnusa/interactions.jsonl",
      "source_id": "I0296",
      "date": "2026-08-17",
      "excerpt": "{\"interaction_id\": \"I0296\", \"tanggal\": \"2026-08-17\", \"tipe\": \"catatan_meeting\", \"account_id\": \"P02\", \"dari\": \"citra@kasirnusa.id\", \"ke\": \"\", \"peserta\": \"K076;E07\", \"subjek\": \"Demo Teras Kafe\", \"isi\": \"Pak Teddy suka produknya tetapi menilai harga terlalu tinggi. KasirPro menawarkan harga sekitar 20% lebih murah.\", \"membalas_id\": \"\"}",
      "evidence_type": "direct"
    },
    {
      "id": "interactions.jsonl:I0348",
      "source_file": "dataset_kasirnusa/interactions.jsonl",
      "source_id": "I0348",
      "date": "2026-09-28",
      "excerpt": "{\"interaction_id\": \"I0348\", \"tanggal\": \"2026-09-28\", \"tipe\": \"email_internal\", \"account_id\": \"P02\", \"dari\": \"citra@kasirnusa.id\", \"ke\": \"andi@kasirnusa.id\", \"peserta\": \"\", \"subjek\": \"Permintaan diskon 20% Teras Kafe\", \"isi\": \"Pak Andi, untuk menutup Teras Kafe saya usul diskon 20% agar menyamai KasirPro. Mohon keputusan.\", \"membalas_id\": \"\"}",
      "evidence_type": "direct"
    }
  ],
  "graph": {
    "nodes": [
      {
        "id": "D-2025-02",
        "label": "D-2025-02",
        "type": "decision"
      },
      {
        "id": "D-2025-06",
        "label": "D-2025-06",
        "type": "decision"
      },
      {
        "id": "DL-002",
        "label": "DL-002",
        "type": "deal"
      },
      {
        "id": "E07",
        "label": "Citra Ayuningtyas",
        "type": "employee"
      },
      {
        "id": "I0296",
        "label": "Demo Teras Kafe",
        "type": "interaction"
      },
      {
        "id": "I0348",
        "label": "Permintaan diskon 20% Teras Kafe",
        "type": "interaction"
      },
      {
        "id": "P02",
        "label": "Teras Kafe Group",
        "type": "account"
      }
    ],
    "edges": [
      {
        "id": "deal_for:DL-002:P02:crm_deals.csv:DL-002",
        "source": "DL-002",
        "target": "P02",
        "relation": "deal_for",
        "evidence_ids": [
          "crm_deals.csv:DL-002"
        ],
        "evidence_type": "direct",
        "valid_from": "2026-07-25",
        "valid_to": null
      },
      {
        "id": "interaction_for:I0296:P02:interactions.jsonl:I0296",
        "source": "I0296",
        "target": "P02",
        "relation": "interaction_for",
        "evidence_ids": [
          "interactions.jsonl:I0296"
        ],
        "evidence_type": "direct",
        "valid_from": "2026-08-17",
        "valid_to": null
      },
      {
        "id": "interaction_for:I0348:P02:interactions.jsonl:I0348",
        "source": "I0348",
        "target": "P02",
        "relation": "interaction_for",
        "evidence_ids": [
          "interactions.jsonl:I0348"
        ],
        "evidence_type": "direct",
        "valid_from": "2026-09-28",
        "valid_to": null
      },
      {
        "id": "owned_by:DL-002:E07:crm_deals.csv:DL-002",
        "source": "DL-002",
        "target": "E07",
        "relation": "owned_by",
        "evidence_ids": [
          "crm_deals.csv:DL-002"
        ],
        "evidence_type": "direct",
        "valid_from": "2026-07-25",
        "valid_to": null
      },
      {
        "id": "owned_by:P02:E07:crm_accounts.csv:P02",
        "source": "P02",
        "target": "E07",
        "relation": "owned_by",
        "evidence_ids": [
          "crm_accounts.csv:P02"
        ],
        "evidence_type": "direct",
        "valid_from": null,
        "valid_to": null
      },
      {
        "id": "participant:I0296:E07:interactions.jsonl:I0296",
        "source": "I0296",
        "target": "E07",
        "relation": "participant",
        "evidence_ids": [
          "interactions.jsonl:I0296"
        ],
        "evidence_type": "direct",
        "valid_from": "2026-08-17",
        "valid_to": null
      },
      {
        "id": "requested_by:D-2025-02:E07:decision_log.csv:D-2025-02",
        "source": "D-2025-02",
        "target": "E07",
        "relation": "requested_by",
        "evidence_ids": [
          "decision_log.csv:D-2025-02"
        ],
        "evidence_type": "direct",
        "valid_from": "2025-03-04",
        "valid_to": null
      },
      {
        "id": "requested_by:D-2025-06:E07:decision_log.csv:D-2025-06",
        "source": "D-2025-06",
        "target": "E07",
        "relation": "requested_by",
        "evidence_ids": [
          "decision_log.csv:D-2025-06"
        ],
        "evidence_type": "direct",
        "valid_from": "2025-08-12",
        "valid_to": null
      },
      {
        "id": "candidate:DL-002:D-2025-02:same_competitor:crm_deals.csv:DL-002;crm_deals.csv:DL-006;decision_log.csv:D-2025-02",
        "source": "DL-002",
        "target": "D-2025-02",
        "relation": "candidate_precedent_same_competitor",
        "evidence_ids": [
          "crm_deals.csv:DL-002",
          "crm_deals.csv:DL-006",
          "decision_log.csv:D-2025-02"
        ],
        "evidence_type": "inferred",
        "valid_from": "2025-03-04",
        "valid_to": null
      },
      {
        "id": "candidate:DL-002:D-2025-02:same_competitor:crm_deals.csv:DL-002;crm_deals.csv:DL-007;decision_log.csv:D-2025-02",
        "source": "DL-002",
        "target": "D-2025-02",
        "relation": "candidate_precedent_same_competitor",
        "evidence_ids": [
          "crm_deals.csv:DL-002",
          "crm_deals.csv:DL-007",
          "decision_log.csv:D-2025-02"
        ],
        "evidence_type": "inferred",
        "valid_from": "2025-03-04",
        "valid_to": null
      },
      {
        "id": "candidate:DL-002:D-2025-02:shared_industry:crm_accounts.csv:C23;crm_accounts.csv:P02;decision_log.csv:D-2025-02",
        "source": "DL-002",
        "target": "D-2025-02",
        "relation": "candidate_precedent_shared_industry",
        "evidence_ids": [
          "crm_accounts.csv:C23",
          "crm_accounts.csv:P02",
          "decision_log.csv:D-2025-02"
        ],
        "evidence_type": "inferred",
        "valid_from": "2025-03-04",
        "valid_to": null
      },
      {
        "id": "candidate:DL-002:D-2025-06:same_competitor:crm_deals.csv:DL-002;crm_deals.csv:DL-006;decision_log.csv:D-2025-06",
        "source": "DL-002",
        "target": "D-2025-06",
        "relation": "candidate_precedent_same_competitor",
        "evidence_ids": [
          "crm_deals.csv:DL-002",
          "crm_deals.csv:DL-006",
          "decision_log.csv:D-2025-06"
        ],
        "evidence_type": "inferred",
        "valid_from": "2025-08-12",
        "valid_to": null
      },
      {
        "id": "candidate:DL-002:D-2025-06:same_competitor:crm_deals.csv:DL-002;crm_deals.csv:DL-007;decision_log.csv:D-2025-06",
        "source": "DL-002",
        "target": "D-2025-06",
        "relation": "candidate_precedent_same_competitor",
        "evidence_ids": [
          "crm_deals.csv:DL-002",
          "crm_deals.csv:DL-007",
          "decision_log.csv:D-2025-06"
        ],
        "evidence_type": "inferred",
        "valid_from": "2025-08-12",
        "valid_to": null
      },
      {
        "id": "candidate:DL-002:D-2025-06:shared_industry:crm_accounts.csv:C23;crm_accounts.csv:P02;decision_log.csv:D-2025-06",
        "source": "DL-002",
        "target": "D-2025-06",
        "relation": "candidate_precedent_shared_industry",
        "evidence_ids": [
          "crm_accounts.csv:C23",
          "crm_accounts.csv:P02",
          "decision_log.csv:D-2025-06"
        ],
        "evidence_type": "inferred",
        "valid_from": "2025-08-12",
        "valid_to": null
      }
    ]
  },
  "candidate_decisions": [
    {
      "decision_id": "D-2025-02",
      "tanggal": "2025-03-04",
      "tipe": "diskon",
      "account_id": "C23",
      "deal_id": "DL-006",
      "diminta_oleh": "E07",
      "diputuskan_oleh": "E01",
      "keputusan": "Ditolak",
      "nilai": "20%",
      "alasan": "Di atas batas 15%; menyamai harga kompetitor merusak harga pasar. Deal kemudian kalah karena harga.",
      "bukti_interaction_id": "",
      "fitur_dijanjikan": "",
      "status_janji": ""
    },
    {
      "decision_id": "D-2025-06",
      "tanggal": "2025-08-12",
      "tipe": "pengecualian",
      "account_id": "C23",
      "deal_id": "DL-007",
      "diminta_oleh": "E07",
      "diputuskan_oleh": "E01",
      "keputusan": "Disetujui",
      "nilai": "Paket Starter tanpa diskon, pilot 6 outlet",
      "alasan": "Pendekatan alternatif setelah kalah Maret: mulai dari Starter, naik paket bila puas. Deal menang Sep 2025.",
      "bukti_interaction_id": "",
      "fitur_dijanjikan": "",
      "status_janji": ""
    }
  ],
  "unknowns": [
    "DATA CONTOH PENGEMBANGAN: proyeksi kecil graph backend untuk memeriksa UI. Bukan seluruh konteks; analisis replay di bawah tetap contoh manual."
  ]
} satisfies DealContext;
export const fixtureRecommendation = {
  "schema_version": "v1",
  "deal_id": "DL-002",
  "action": "Fixture UI — evaluasi pilot pada sebagian outlet sebagai alternatif penawaran.",
  "owner_id": "E07",
  "milestone": "Skenario pengembangan: konfirmasi kebutuhan, lingkup pilot, dan kriteria keberhasilan bersama pelanggan.",
  "evidence_ids": [
    "interactions.jsonl:I0296",
    "interactions.jsonl:I0348"
  ],
  "precedent_ids": [
    "D-2025-02",
    "D-2025-06"
  ],
  "precedent_comparison": [
    "Fixture UI: C23 memiliki riwayat penolakan diskon 20% dan pendekatan Starter yang kemudian diikuti deal menang.",
    "Fixture UI: P02 merencanakan 15 outlet; pilot harus menetapkan sebagian outlet sesuai batas paket. Riwayat C23 tidak menjamin hasil yang sama."
  ],
  "approvals_needed": [
    "Jika diskon di atas 10% tetap diajukan, persetujuan VP Sales dan pencatatan harus diverifikasi."
  ],
  "unknowns": [
    "Fixture UI, bukan keluaran model atau analisis backend."
  ],
  "engine_mode": "replay"
} satisfies Recommendation;
async function respond<T>(data: T, signal: AbortSignal): Promise<T> {
  if (signal.aborted) throw new DOMException('Dibatalkan', 'AbortError');
  return structuredClone(data);
}
export const fixtureApi: DealApi = {
  list: signal => respond(fixtureList, signal),
  context: (id, signal) => {
    if (id !== 'DL-002') return Promise.reject(new ApiError(501, 'Fixture detail hanya disiapkan untuk P02.'));
    return respond(fixtureContext, signal);
  },
  analyze: (id, signal) => {
    if (id !== 'DL-002') return Promise.reject(new ApiError(501, 'Fixture analisis hanya disiapkan untuk P02.'));
    return respond(fixtureRecommendation, signal);
  },
};
