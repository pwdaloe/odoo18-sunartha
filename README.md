# Odoo 18 Sunartha

Project Odoo 18 Community Edition untuk PT Sunartha — mencakup tiga lini bisnis:
**Shipping Maritime**, **Logistics Cold Chain**, dan **Laporan Keuangan Konsolidasi**.

Repo: [github.com/pwdaloe/odoo18-sunartha](https://github.com/pwdaloe/odoo18-sunartha)

---

## Cara Menjalankan

### Prasyarat
- macOS dengan Homebrew
- Python 3.11 (via Homebrew)
- [Postgres.app](https://postgresapp.com) (PostgreSQL 15) — harus berjalan sebelum Odoo
- wkhtmltopdf (untuk cetak PDF)

### Clone & Setup Pertama Kali
```bash
git clone --recurse-submodules https://github.com/pwdaloe/odoo18-sunartha.git
cd odoo18-sunartha

# Setup virtual environment
python3.11 -m venv venv
venv/bin/pip install --upgrade pip wheel
venv/bin/pip install -r odoo/requirements.txt

# Salin dan sesuaikan konfigurasi
cp odoo.conf.example odoo.conf
# Edit odoo.conf: isi db_password dan admin_passwd
```

### Menjalankan Odoo
```bash
# Pastikan Postgres.app sudah berjalan
./start_odoo.sh
```
Buka browser: **http://localhost:8069**

### Menghentikan Odoo
Tekan `Ctrl+C` di terminal.

---

## Struktur Project

```
odoo18-sunartha/
├── odoo/                  — Odoo 18 CE source (git submodule → github.com/odoo/odoo)
├── custom_addons/         — Modul custom Sunartha
│   ├── sunartha_account_base/      — Fondasi akuntansi PSAK Indonesia
│   └── sunartha_accounting_advance/ — Journal Transaction + Reporting
├── venv/                  — Python virtual environment (tidak di-commit)
├── logs/                  — Log file Odoo (tidak di-commit)
├── odoo.conf              — Konfigurasi server (tidak di-commit, ada credential)
├── odoo.conf.example      — Template konfigurasi tanpa credential
├── start_odoo.sh          — Script menjalankan Odoo
└── scaffold_module.sh     — Script membuat modul baru
```

### Membuat Modul Custom Baru
```bash
./scaffold_module.sh nama_modul
```

---

## Custom Modules

### Sunartha Accounting Base (`sunartha_account_base`)

**Versi:** `18.0.1.0.0`
**Kategori:** Accounting/Accounting
**Summary:** Fondasi akuntansi PSAK Indonesia — COA, PPh/PPN, approval jurnal, laporan PSAK 1 & 2

**Fitur utama:**
- Bagan Akun (COA) diperkaya untuk industri pelayaran, logistik, dan konsolidasi
- Konfigurasi pajak lengkap: PPN 11%/0%, PPh 23, PPh 4(2), PPh 26, PPh 22
- Workflow approval jurnal sebelum posting (threshold per-journal)
- Ekspor faktur ke format XML CoreTax DJP 2025
- Laporan keuangan PSAK 1 (Neraca, L/R Komprehensif) dan PSAK 2 (Arus Kas)
- 3 level akses: Pengguna, Approver, Manager

**Dependencies:** `account`, `l10n_id`, `mail`

**Models:**

| Model | Tipe | Deskripsi |
|-------|------|-----------|
| `account.move` | Inherit | Tambah approval workflow ke jurnal |
| `account.journal` | Inherit | Tambah konfigurasi threshold approval |
| `sunartha.account.approval.request` | Baru | Log riwayat semua permintaan approval jurnal |
| `sunartha.account.approval.reject.wizard` | Wizard | Dialog penolakan jurnal dengan alasan |
| `sunartha.coretax.export` | Baru | Batch export faktur pajak ke XML CoreTax DJP |
| `sunartha.report.psak` | Wizard | Generator laporan keuangan PSAK |

**Konfigurasi Pajak yang tersedia:**

| Kode | Nama | Rate |
|------|------|------|
| `PPN-K-11` | PPN Keluaran 11% | 11% |
| `PPN-M-11` | PPN Masukan 11% | 11% |
| `PPN-K-0-EXP` | PPN 0% Ekspor | 0% |
| `PPN-K-0-LAUT` | PPN 0% Jasa Pelayaran Domestik | 0% |
| `PPH23-JASA` | PPh 23 Jasa | 2% |
| `PPH23-SEWA-NON-TB` | PPh 23 Sewa Non Tanah/Bangunan | 2% |
| `PPH23-DIVIDEN` | PPh 23 Dividen | 15% |
| `PPH4-SEWA-TB` | PPh 4(2) Sewa Tanah/Bangunan | 10% |
| `PPH4-KONSTRUKSI-K/B` | PPh 4(2) Konstruksi | 2% / 4% |
| `PPH26-JASA-LN` | PPh 26 Jasa Luar Negeri | 20% |
| `PPH22-IMPOR` | PPh 22 Impor | 2.5% |

**Cara install/update:**
```bash
./start_odoo.sh -d odoo18_sunartha -u sunartha_account_base
```

**Menu di Odoo:**
`Akuntansi → Sunartha → Approval Jurnal / Ekspor CoreTax DJP / Laporan Keuangan PSAK`

---

### Accounting Advance (`sunartha_accounting_advance`)

**Versi:** `18.0.1.1.0`
**Kategori:** Accounting
**Summary:** Journal Transactions dengan approval workflow, Branch, Ledger — CE compatible

**Fitur utama:**
- Custom Journal Transaction terpisah dari `account.move` Odoo — lebih fleksibel untuk multi-branch
- Master data Branch dan Ledger sebagai dimensi analitik tambahan
- Workflow approval: Draft → Submitted → Posted (dengan opsi Reject)
- Laporan keuangan on-screen: Balance Sheet, Profit & Loss, Cash Flow Statement
- Filter laporan per Branch dan Ledger
- 2 level akses: Pengguna dan Manager

**Dependencies:** `account`, `mail`, `base`

**Models:**

| Model | Tipe | Deskripsi |
|-------|------|-----------|
| `sunartha.branch` | Baru | Master data cabang/divisi perusahaan |
| `sunartha.ledger` | Baru | Master data buku besar/ledger tambahan |
| `sunartha.journal.transaction` | Baru | Header jurnal transaksi dengan approval workflow |
| `sunartha.journal.transaction.line` | Baru | Baris jurnal: akun, debit, kredit, branch |
| `sunartha.journal.transaction.reject.wizard` | Wizard | Dialog penolakan transaksi dengan alasan |
| `sunartha.report.statement` | Wizard | Generator laporan keuangan (Balance Sheet / P&L / Cash Flow) |
| `sunartha.report.statement.line` | Wizard | Baris output laporan keuangan |

**Menu di Odoo:**
```
Accounting Advance
├── Journal Transactions
├── Reporting
│   └── Statement Reports
│       ├── Balance Sheet        — snapshot per tanggal
│       ├── Profit and Loss      — periode date_from s/d date_to
│       └── Cash Flow Statement  — perubahan saldo akun kas
└── Configuration
    ├── Branches
    └── Ledgers
```

**Cara install/update:**
```bash
./start_odoo.sh -d odoo18_sunartha -u sunartha_accounting_advance
```

> **Catatan:** Jika menambah file Python baru, wajib restart server terlebih dahulu sebelum upgrade.
> Gunakan perintah di atas (restart + upgrade sekaligus).

---

## Dependency Modul

```
Odoo CE (account, mail, base)
    ↓
l10n_id
    ↓
sunartha_account_base          ← SELESAI (v18.0.1.0.0)
sunartha_accounting_advance    ← SELESAI (v18.0.1.1.0)

Rencana modul standalone berikutnya:
sunartha_consolidation         ← PLANNED — konsolidasi & eliminasi multi-entitas
sunartha_maritime              ← PLANNED — Shipping Maritime
sunartha_cold_chain            ← PLANNED — Logistics Cold Chain
```

---

## Modul Odoo yang Diaktifkan

| Modul | Nama | Model Utama |
|-------|------|-------------|
| `sale_management` | Sales | `sale.order` |
| `purchase` | Purchase | `purchase.order` |
| `stock` | Inventory | `stock.picking`, `stock.move` |
| `crm` | CRM | `crm.lead` |
| `hr_expense` | Expenses | `hr.expense` |
| `hr` | Employees | `hr.employee` |
| `maintenance` | Maintenance | `maintenance.request` |
| `calendar` | Calendar | `calendar.event` |
| `contacts` | Contacts | `res.partner` |
| `project` | Project | `project.project`, `project.task` |
| `l10n_id` | Lokalisasi Indonesia | COA, pajak dasar |

---

## Catatan Pengembangan

### Arsitektur Multi-Industri
Sistem dibangun dengan pendekatan **layered modules**:
1. **`sunartha_account_base`** — fondasi PSAK + pajak, dipakai semua industri
2. **`sunartha_accounting_advance`** — journal transaction custom + laporan keuangan on-screen
3. **`sunartha_consolidation`** *(planned, standalone)* — Konsolidasi & eliminasi multi-entitas (PSAK 65)
4. **`sunartha_maritime`** *(planned)* — Shipping Maritime: voyage, charter, bunker, PDA
5. **`sunartha_cold_chain`** *(planned)* — Logistics: cold storage, fleet, delivery order

### Multi-Company
Semua entitas berjalan di **satu instance Odoo** dengan fitur multi-company.
Modul konsolidasi akan membaca data dari semua company dan menghasilkan laporan eliminasi.

### PSAK yang Diimplementasi
- **PSAK 1** — Penyajian Laporan Keuangan (Neraca, L/R Komprehensif)
- **PSAK 2** — Laporan Arus Kas (metode tidak langsung)
- **PSAK 46** — Pajak Penghasilan (akun pajak tangguhan)
- **PSAK 65** — Konsolidasi *(akun NCI disiapkan, logika di modul terpisah)*
- **PSAK 73** — Sewa *(akun hak-guna disiapkan, untuk charter kapal)*

### Approval Jurnal
Threshold dikonfigurasi per journal di:
`Akuntansi → Konfigurasi → Jurnal → tab "Konfigurasi Approval"`

---

## Rencana Pekerjaan Ke Depan

### Prioritas Dekat
- [ ] **Pengecekan tampilan laporan keuangan** — verifikasi output Balance Sheet, Profit & Loss, dan Cash Flow Statement di browser; pastikan angka, section header, dan total sudah benar sesuai data transaksi yang ada

### Modul Planned (Standalone)

#### `sunartha_consolidation` *(standalone module)*
Konsolidasi laporan keuangan multi-entitas sesuai PSAK 65:
- Definisi group konsolidasi (parent + subsidiaries)
- Entri eliminasi antar-entitas (intercompany)
- Laporan konsolidasi: Neraca, L/R, Arus Kas gabungan
- NCI (Non-Controlling Interest) calculation
- Tidak bergantung pada `sunartha_account_base` maupun `sunartha_accounting_advance`

#### `sunartha_maritime` *(standalone module)*
Operasi Shipping Maritime:
- Voyage management (pelayaran, rute, port call)
- Charter party (time charter, voyage charter)
- Bunker management
- Port Disbursement Account (PDA)
- Freight invoice

#### `sunartha_cold_chain` *(standalone module)*
Logistik Cold Chain:
- Cold storage management (rak, suhu, kapasitas)
- Fleet & delivery order
- Inbound/outbound tracking

---

*Terakhir diperbarui: 09 Juni 2026*
*Generate otomatis oleh `/update-readme`*
