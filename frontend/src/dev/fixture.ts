// Development-only UI fixtures. Evidence is copied from the named source records.
// Graph and Recommendation are illustrative, never backend/Jev results.
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
      "id": "I0296",
      "source_file": "dataset_kasirnusa/interactions.jsonl",
      "source_id": "I0296",
      "date": "2026-08-17",
      "excerpt": "Pak Teddy suka produknya tetapi menilai harga terlalu tinggi. KasirPro menawarkan harga sekitar 20% lebih murah.",
      "evidence_type": "direct"
    },
    {
      "id": "I0348",
      "source_file": "dataset_kasirnusa/interactions.jsonl",
      "source_id": "I0348",
      "date": "2026-09-28",
      "excerpt": "Pak Andi, untuk menutup Teras Kafe saya usul diskon 20% agar menyamai KasirPro. Mohon keputusan.",
      "evidence_type": "direct"
    },
    {
      "id": "D-2025-02",
      "source_file": "dataset_kasirnusa/decision_log.csv",
      "source_id": "D-2025-02",
      "date": "2025-03-04",
      "excerpt": "Ditolak · 20% · Di atas batas 15%; menyamai harga kompetitor merusak harga pasar. Deal kemudian kalah karena harga.",
      "evidence_type": "direct"
    },
    {
      "id": "D-2025-06",
      "source_file": "dataset_kasirnusa/decision_log.csv",
      "source_id": "D-2025-06",
      "date": "2025-08-12",
      "excerpt": "Disetujui · Paket Starter tanpa diskon, pilot 6 outlet · Pendekatan alternatif setelah kalah Maret: mulai dari Starter, naik paket bila puas. Deal menang Sep 2025.",
      "evidence_type": "direct"
    },
    {
      "id": "crm-DL-002",
      "source_file": "dataset_kasirnusa/crm_deals.csv",
      "source_id": "DL-002",
      "date": "2026-08-17",
      "excerpt": "DL-002 · P02 · Demo · 15 outlet · nilai_tahunan 63000000 · owner_id E07 · kompetitor KasirPro",
      "evidence_type": "direct"
    }
  ],
  "graph": {
    "nodes": [
      {
        "id": "DL-002",
        "label": "Deal Teras Kafe",
        "type": "deal"
      },
      {
        "id": "P02",
        "label": "Teras Kafe Group",
        "type": "account"
      },
      {
        "id": "K076",
        "label": "Teddy Kurniawan",
        "type": "contact"
      },
      {
        "id": "I0296",
        "label": "Demo & hambatan harga",
        "type": "interaction"
      },
      {
        "id": "I0348",
        "label": "Permintaan diskon 20%",
        "type": "interaction"
      },
      {
        "id": "D-2025-02",
        "label": "Diskon ditolak · C23",
        "type": "decision"
      },
      {
        "id": "D-2025-06",
        "label": "Pilot Starter · C23",
        "type": "decision"
      }
    ],
    "edges": [
      {
        "id": "e-account",
        "source": "DL-002",
        "target": "P02",
        "relation": "Deal milik prospek",
        "evidence_ids": [
          "crm-DL-002"
        ],
        "evidence_type": "direct",
        "valid_from": null,
        "valid_to": null
      },
      {
        "id": "e-demo",
        "source": "DL-002",
        "target": "I0296",
        "relation": "Konteks demo",
        "evidence_ids": [
          "I0296"
        ],
        "evidence_type": "direct",
        "valid_from": "2026-08-17",
        "valid_to": null
      },
      {
        "id": "e-owner",
        "source": "I0296",
        "target": "K076",
        "relation": "Peserta demo",
        "evidence_ids": [
          "I0296"
        ],
        "evidence_type": "direct",
        "valid_from": "2026-08-17",
        "valid_to": null
      },
      {
        "id": "e-request",
        "source": "DL-002",
        "target": "I0348",
        "relation": "Permintaan persetujuan",
        "evidence_ids": [
          "I0348"
        ],
        "evidence_type": "direct",
        "valid_from": "2026-09-28",
        "valid_to": null
      },
      {
        "id": "e-precedent-1",
        "source": "DL-002",
        "target": "D-2025-02",
        "relation": "Fixture: kandidat pembanding harga",
        "evidence_ids": [
          "I0296",
          "D-2025-02"
        ],
        "evidence_type": "inferred",
        "valid_from": null,
        "valid_to": null
      },
      {
        "id": "e-precedent-2",
        "source": "DL-002",
        "target": "D-2025-06",
        "relation": "Fixture: kandidat pendekatan pilot",
        "evidence_ids": [
          "I0296",
          "D-2025-06"
        ],
        "evidence_type": "inferred",
        "valid_from": null,
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
    "Fixture UI: persetujuan atas permintaan diskon P02 belum dibuktikan oleh record yang ditampilkan.",
    "Fixture UI: kesediaan pelanggan mengikuti pilot sebagian outlet belum diketahui."
  ]
} satisfies DealContext;
export const fixtureRecommendation = {
  "schema_version": "v1",
  "deal_id": "DL-002",
  "action": "Fixture UI — evaluasi pilot pada sebagian outlet sebagai alternatif penawaran.",
  "owner_id": "E07",
  "milestone": "Skenario pengembangan: konfirmasi kebutuhan, lingkup pilot, dan kriteria keberhasilan bersama pelanggan.",
  "evidence_ids": [
    "I0296",
    "I0348"
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
