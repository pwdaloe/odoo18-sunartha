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
│   ├── sunartha_account_base/       — Fondasi akuntansi PSAK Indonesia
│   └── sunartha_accounting_advance/ — Full Custom GL Engine + Reporting
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
./start_odoo.sh -d odoo18_sunartha -u sunartha_account_base --stop-after-init
```

**Menu di Odoo:**
`Akuntansi → Sunartha → Approval Jurnal / Ekspor CoreTax DJP / Laporan Keuangan PSAK`

---

### Accounting Advance (`sunartha_accounting_advance`)

**Versi:** `18.0.1.2.0`
**Kategori:** Accounting
**Summary:** Full Custom GL Engine — Journal Transactions, Period Locking, Recurring, AR/AP Aging, Comparative Financial Reports — CE compatible

**Arsitektur:** Full Custom GL — semua pencatatan AR/AP/GL melalui `sunartha.journal.transaction`, tidak mixing dengan `account.move` Odoo native.

**Fitur utama:**
- Custom Journal Transaction terpisah dari `account.move` — lebih fleksibel untuk multi-branch
- Master data Branch dan Ledger sebagai dimensi analitik tambahan
- Workflow approval: Draft → Submitted → Approved → Posted (dengan Reject)
- **Period Locking** — kunci periode akuntansi agar tidak bisa di-post setelah dikunci
- **Recurring Journal** — template jurnal berulang dengan frekuensi bulanan/kuartalan/tahunan
- **Comparative Financial Reports** — Balance Sheet, P&L, Cash Flow dengan kolom perbandingan periode
- **AR/AP Aging Report** — aging schedule per partner dengan bucket 0/1-30/31-60/61-90/91-120/>120 hari
- Partner dan Due Date pada Journal Transaction sebagai fondasi AR/AP reporting
- Filter laporan per Branch dan Ledger
- 2 level akses: Pengguna dan Manager

**Dependencies:** `account`, `mail`, `base`

**Models:**

| Model | Tipe | Deskripsi |
|-------|------|-----------|
| `sunartha.branch` | Baru | Master data cabang/divisi perusahaan |
| `sunartha.ledger` | Baru | Master data buku besar/ledger tambahan |
| `sunartha.journal.transaction` | Baru | Header jurnal transaksi dengan approval workflow, partner, due_date |
| `sunartha.journal.transaction.line` | Baru | Baris jurnal: akun, debit, kredit, branch |
| `sunartha.journal.transaction.reject.wizard` | Wizard | Dialog penolakan transaksi dengan alasan |
| `sunartha.accounting.period` | Baru | Periode akuntansi dengan fitur kunci/buka |
| `sunartha.recurring.journal` | Baru | Template jurnal berulang dengan jadwal otomatis |
| `sunartha.recurring.journal.line` | Baru | Baris template jurnal berulang |
| `sunartha.report.statement` | Wizard | Generator laporan keuangan (Balance Sheet / P&L / Cash Flow + perbandingan) |
| `sunartha.report.statement.line` | Wizard | Baris output laporan keuangan dengan kolom variance |
| `sunartha.report.aging` | Wizard | Generator AR/AP Aging Report |
| `sunartha.report.aging.line` | Wizard | Baris aging per partner dengan bucket hari |

**Menu di Odoo:**
```
Accounting Advance
├── Dashboard
├── Journal
│   ├── Journal Transactions     — semua transaksi
│   ├── Menunggu Persetujuan     — (Manager)
│   └── Recurring Journals       — (Manager)
├── Reporting
│   ├── Statement Reports
│   │   ├── Balance Sheet        — snapshot per tanggal, opsional perbandingan
│   │   ├── Profit and Loss      — periode date_from s/d date_to
│   │   └── Cash Flow Statement  — perubahan saldo akun kas
│   └── Aging Reports
│       ├── AR Aging             — piutang per partner
│       └── AP Aging             — utang per partner
└── Configuration
    ├── Accounting Periods       — (Manager) kunci/buka periode
    ├── Master Data
    │   ├── Branch
    │   └── Ledger
    └── Accounting
        ├── Chart of Accounts
        ├── Taxes
        ├── Journals
        └── Currencies
```

**Cara install/update:**
```bash
./start_odoo.sh -d odoo18_sunartha -u sunartha_accounting_advance --stop-after-init
```

> **Catatan:** Jika menambah file Python baru, wajib restart server terlebih dahulu sebelum upgrade.
> `pkill -f "odoo-bin" && ./start_odoo.sh -d odoo18_sunartha -u sunartha_accounting_advance`

---

## Dependency Modul

```
Odoo CE (account, mail, base)
    ↓
l10n_id
    ↓
sunartha_account_base          ← SELESAI (v18.0.1.0.0)
sunartha_accounting_advance    ← SELESAI (v18.0.1.2.0)

Rencana modul standalone berikutnya:
sunartha_consolidation         ← PLANNED — konsolidasi & eliminasi multi-entitas (PSAK 65)
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

### Arsitektur Full Custom GL
`sunartha_accounting_advance` menggunakan pendekatan **Full Custom GL Engine**: semua data akuntansi
(AR, AP, GL, payment) disimpan di `sunartha.journal.transaction`, **tidak mixing** dengan native `account.move`.

Konsekuensi desain:
- AR/AP Aging query dari `sunartha.journal.transaction.line` saja
- Reports query dari custom model, bukan Odoo native
- Tidak ada duplicate entry di dua model berbeda
- `partner_id` dan `due_date` di header transaksi sebagai fondasi AR/AP reporting

### Arsitektur Multi-Industri
Sistem dibangun dengan pendekatan **layered + standalone modules**:
1. **`sunartha_account_base`** — fondasi PSAK + pajak, dipakai semua industri
2. **`sunartha_accounting_advance`** — full custom GL engine + laporan keuangan on-screen
3. **`sunartha_consolidation`** *(planned, standalone)* — Konsolidasi & eliminasi multi-entitas (PSAK 65)
4. **`sunartha_maritime`** *(planned, standalone)* — Shipping Maritime: voyage, charter, bunker, PDA
5. **`sunartha_cold_chain`** *(planned, standalone)* — Logistics: cold storage, fleet, delivery order

### Multi-Company
Semua entitas berjalan di **satu instance Odoo** dengan fitur multi-company.
Modul konsolidasi akan membaca data dari semua company dan menghasilkan laporan eliminasi.

### PSAK yang Diimplementasi
- **PSAK 1** — Penyajian Laporan Keuangan (Neraca, L/R Komprehensif)
- **PSAK 2** — Laporan Arus Kas (metode tidak langsung)
- **PSAK 46** — Pajak Penghasilan (akun pajak tangguhan)
- **PSAK 65** — Konsolidasi *(akun NCI disiapkan, logika di modul terpisah)*
- **PSAK 73** — Sewa *(akun hak-guna disiapkan, untuk charter kapal)*

### Approval Jurnal (sunartha_account_base)
Threshold dikonfigurasi per journal di:
`Akuntansi → Konfigurasi → Jurnal → tab "Konfigurasi Approval"`

### QC Test Otomatis (`/odoo-qc`)
Skill `/odoo-qc` tersedia di `.claude/commands/odoo-qc.md` untuk verifikasi modul setelah upgrade.

**Test user:** `odoo-qc@sunartha.co.id` (uid=8, group=Manager, company=Sunartha Japan)

**Cakupan test:**
- Journal Transaction workflow: Create → Submit → Approve → Post + guard unbalanced
- Recurring Journal: Create template → Generate Now + guard template kosong
- Financial Statements: Balance Sheet, P&L, Cash Flow
- AR/AP Aging: Generate report per partner

**Catatan:** Balance Sheet dan AR/AP Aging mengembalikan 0 baris di test environment karena
CoA (`account.account`) ada di company 2 (Sunartha ID) sementara transaksi default di company 1
(Sunartha Japan) — bukan bug modul. Semua workflow logic tetap pass.

**Jalankan:** `/odoo-qc` di Claude Code (pastikan Odoo sudah running di `localhost:8069`)

> **Catatan teknis:** XML-RPC di Odoo 18 tidak bisa memanggil action methods
> (`action_submit`, `action_approve`, dll) — skill menggunakan JSON-RPC endpoint
> `/web/dataset/call_kw` dengan session cookie.

### Recurring Journal Cron
Scheduled action **"Sunartha: Generate Recurring Journals"** terdefinisi di `data/recurring_cron.xml`
dan otomatis aktif saat install/upgrade modul — interval 1 hari, memanggil `_cron_generate_recurring()`.

> **Catatan Odoo 18:** Field `numbercall` dan `doall` pada `ir.cron` sudah dihapus di Odoo 18.
> Gunakan hanya `interval_number`, `interval_type`, dan `active`.

---

## Rencana Pekerjaan Ke Depan

### Tier 2 — Fitur Accounting Advance Berikutnya
- [ ] **Fixed Assets & Depreciation** (`sunartha_fixed_assets` — standalone module)
  - Aset tetap dengan jadwal penyusutan
  - Docking schedule untuk kapal
- [ ] **Bank Reconciliation** — rekonsiliasi saldo bank vs buku
- [ ] **Bukti Potong PPh 23/26** — cetak bukti potong sesuai format DJP
- [ ] **Multi-currency / Restatement** — pencatatan mata uang asing + restatement sesuai PSAK

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

*Terakhir diperbarui: 10 Juni 2026*
*Generate otomatis oleh `/update-readme`*

<!-- changelog
2026-06-10: Fix catatan recurring cron (sebelumnya salah catat tidak bisa via XML), tambah dokumentasi /odoo-qc skill dan QC test user
-->

