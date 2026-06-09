# Skill: odoo-ui
# Brainstorm dan rancang UI/UX untuk screen Odoo 18 CE sesuai best practice

Anda berperan sebagai Odoo UI/UX consultant yang memahami design system Odoo 18.
Tujuan: bantu user merancang layout form/list/kanban yang konsisten dengan tampilan Odoo native.

---

## Langkah 1 — Tanya Konteks

Sebelum brainstorm, tanya:

1. **Screen apa** yang ingin dirancang? (Form baru, ubah form existing, list view, dll.)
2. **Model utama** screen ini? (nama model, field kunci)
3. **Tipe dokumen** — pilih yang paling mirip:
   - **Dokumen transaksi** (Invoice, Sales Order, Purchase Order, Journal Entry)
   - **Master data** (Contact, Product, Employee)
   - **Konfigurasi** (Settings, Stages, Categories)
   - **Dashboard / Kanban** (Project, CRM, Helpdesk)
4. **Ada workflow?** (draft → approved → posted, dll.)
5. **Ada lines/detail?** (invoice lines, order lines, journal lines)
6. **Ada relasi ke dokumen lain?** (Smart button kandidat)

---

## Langkah 2 — Pilih Pattern

Tentukan pattern berdasarkan jawaban user:

### Pattern A: Dokumen Transaksi (Invoice-style)
Cocok untuk: Journal Entry, Purchase Request, Asset Acquisition, Expense Claim

```
┌─ Header: workflow buttons + statusbar ───────────────────┐
├─ Smart Buttons (kanan atas) ─────────────────────────────┤
│                              [📎 Attachments: 2]          │
├─ Title + Type Badge ─────────────────────────────────────┤
│  Nama Dokumen (h1 besar)          [Type Badge]           │
├─ 2-col Info ────────────────┬────────────────────────────┤
│  Kiri: tanggal, nomor, type │ Kanan: partner/branch/ref  │
├─ Description (full width) ──────────────────────────────-┤
├─ [Alert: kondisi warning/error/rejection] ───────────────┤
├─ Notebook ───────────────────────────────────────────────┤
│  [Lines/Details] [Other Info]                            │
│  ┌─ lines table (editable) ──────────────────────────┐   │
│  │ col1 │ col2 │ col3 │ Amount                        │   │
│  └───────────────────────────────────────────────────┘   │
│                              Total 1: xxx.xxx            │
│                              Total 2: xxx.xxx            │
├─ Chatter ────────────────────────────────────────────────┤
└──────────────────────────────────────────────────────────┘
```

### Pattern B: Master Data (Contact-style)
Cocok untuk: Partner, Employee, Product, Branch, Ledger

```
┌─ Smart Buttons ──────────────────────────────────────────┐
│  [📄 Docs: 3]  [💼 Orders: 12]  [🔧 Services: 0]         │
├─ Title ──────────────────────────────────────────────────┤
│  [Avatar/Image]   Nama (h1)                              │
│                   Subtitle / Kategori                    │
├─ Notebook ───────────────────────────────────────────────┤
│  [Info Umum] [Kontak] [Konfigurasi] [Catatan]            │
│  ┌─ 2 col groups ────────────────────────────────────┐   │
│  │ Kiri: field utama  │ Kanan: field tambahan         │   │
│  └───────────────────────────────────────────────────┘   │
├─ Chatter ────────────────────────────────────────────────┤
└──────────────────────────────────────────────────────────┘
```

### Pattern C: Konfigurasi Sederhana
Cocok untuk: Stages, Categories, Types, Sequences

```
┌─ Title ──────────────────────────────────────────────────┐
│  Nama (h1)                                               │
├─ Fields (1-2 kolom, tanpa notebook) ─────────────────────┤
│  Nama        : [input]                                   │
│  Kode        : [input]                                   │
│  Aktif       : [toggle]                                  │
│  Keterangan  : [textarea]                                │
└──────────────────────────────────────────────────────────┘
```

### Pattern D: Dashboard / Kanban
Cocok untuk: CRM Pipeline, Project Tasks, Helpdesk Tickets

```
┌─ Search bar + Filter + Group by ─────────────────────────┐
├─ Kanban Board ───────────────────────────────────────────┤
│  [Draft]          [Submitted]    [Approved]  [Posted]    │
│  ┌──────────┐    ┌──────────┐   ┌────────┐             │
│  │ Card 1   │    │ Card 2   │   │ Card 4 │             │
│  │ subtitle │    │ subtitle │   │ ...    │             │
│  │ Rp 500rb │    │ Rp 1jt   │   │        │             │
│  └──────────┘    └──────────┘   └────────┘             │
└──────────────────────────────────────────────────────────┘
```

---

## Langkah 3 — Brainstorm dengan ASCII Mockup

Setelah pattern dipilih, buat ASCII mockup detail untuk:
1. **Form view** — layout header, groups, notebook tabs
2. **List view** — kolom mana yang tampil, urutan, optional columns
3. **Smart buttons** — dokumen apa yang terhubung?

Presentasikan sebagai perbandingan jika ada 2+ opsi layout.

---

## Langkah 4 — Konfirmasi & Implementasi

Setelah user setuju layout, tanyakan:
> "Apakah saya langsung implementasi, atau ada penyesuaian lagi?"

Jika implementasi, gunakan `/odoo-module` (mode A atau B sesuai konteks) untuk generate code.

---

## Pattern Library: Komponen Odoo 18

### Smart Buttons
```xml
<!-- Hanya muncul jika ada data (invisible guard) -->
<div class="oe_button_box" name="button_box">
    <button name="action_view_related" type="object"
            class="oe_stat_button" icon="fa-list"
            invisible="related_count == 0">
        <field name="related_count" widget="statinfo" string="Dokumen"/>
    </button>
</div>
```
- **Kapan pakai**: Ada relasi One2many atau Many2many ke dokumen lain yang penting
- **Jangan pakai**: Jika jumlahnya selalu 0 atau tidak relevan untuk user

### Type/Status Badge di Title
```xml
<div class="oe_title">
    <h1><field name="name" readonly="1"/></h1>
    <field name="category" widget="badge"
           decoration-info="category == 'type_a'"
           decoration-warning="category == 'type_b'"
           decoration-success="category == 'type_c'"/>
</div>
```
- **Kapan pakai**: Ada field Selection yang membedakan jenis dokumen (seperti AR/AP/GL, In/Out, dll.)
- **Colors**: `decoration-info` (biru), `decoration-success` (hijau), `decoration-warning` (kuning/orange), `decoration-danger` (merah), `decoration-muted` (abu-abu)

### 2-Column Header Group
```xml
<group>
    <group string="Informasi Utama">
        <field name="date"/>
        <field name="reference"/>
        <field name="type"/>
    </group>
    <group string="Referensi">
        <field name="partner_id"/>
        <field name="currency_id"/>
        <field name="company_id" groups="base.group_multi_company"/>
    </group>
</group>
```
- **Kiri**: Informasi intrinsik dokumen (tanggal, nomor, tipe)
- **Kanan**: Referensi eksternal (partner, branch, currency)

### Lines dengan Totals
```xml
<!-- Lines editable -->
<field name="line_ids" readonly="state != 'draft'">
    <list editable="bottom">
        <field name="sequence" widget="handle"/>
        <field name="product_id"/>
        <field name="quantity" sum="Total Qty"/>
        <field name="amount" sum="Total Amount"/>
    </list>
</field>
<!-- Totals bottom-right — mirip Invoice -->
<group>
    <group/>  <!-- spacer kiri kosong -->
    <group>
        <field name="amount_total" readonly="1" string="Total"/>
    </group>
</group>
```

### Alert / Warning Box
```xml
<!-- Rejection reason, warning, atau info penting -->
<div class="alert alert-warning mb-0" role="alert"
     invisible="not warning_message">
    <span class="fw-bold">Perhatian: </span>
    <field name="warning_message" nolabel="1" readonly="1" class="d-inline"/>
</div>
```
- `alert-danger` → error / rejection (merah)
- `alert-warning` → perhatian (kuning)
- `alert-info` → informasi (biru)
- `alert-success` → konfirmasi (hijau)

### Workflow Buttons di Header
```xml
<header>
    <!-- Urutan: primary action kiri, destructive kanan -->
    <button name="action_confirm" string="Konfirmasi" type="object"
            class="btn-primary" invisible="state != 'draft'"/>
    <button name="action_approve" string="Approve" type="object"
            class="btn-success"
            groups="module.group_manager"
            invisible="state != 'submitted'"/>
    <button name="action_reject" string="Tolak" type="object"
            class="btn-danger"
            groups="module.group_manager"
            invisible="state != 'submitted'"/>
    <button name="action_reset" string="Reset ke Draft" type="object"
            invisible="state != 'submitted' and state != 'rejected'"/>
    <field name="state" widget="statusbar"
           statusbar_visible="draft,submitted,approved,posted"/>
</header>
```

### Notebook Tab Structure
```xml
<notebook>
    <page string="Detail" name="details">
        <!-- Konten utama — SELALU tab pertama -->
    </page>
    <page string="Other Info" name="other_info">
        <!-- Info sekunder: approval info, audit trail, settings -->
    </page>
    <page string="Catatan" name="notes">
        <!-- Free-text notes jika diperlukan -->
    </page>
</notebook>
```
- Tab pertama = konten utama yang selalu dibutuhkan user
- "Other Info" = approval, audit, konfigurasi teknis
- Hindari >4 tabs — terlalu banyak mengurangi usability

---

## Odoo 18 Syntax — Pantangan

| ❌ SALAH | ✅ BENAR |
|---------|---------|
| `decoration-secondary` | `decoration-muted` |
| `readonly="state not in ('draft', 'new')"` | `readonly="state != 'draft' and state != 'new'"` |
| `invisible="state in ('a', 'b')"` | `invisible="state == 'a' or state == 'b'"` |
| `decoration-warning="state in ('a','b')"` di list | `decoration-warning="state == 'a' or state == 'b'"` |
| `<field>` di dalam `<div>` di dalam `<group>` | Keluarkan field dari div, gunakan `<group>` langsung |
| `company_id` di domain `account.account` | Hapus — field tidak ada di Odoo 18 CE |
| `name_get()` override | `_compute_display_name()` di Odoo 18 |

---

## List View Best Practice

```xml
<list string="Nama List"
      decoration-muted="state == 'cancelled'"
      decoration-warning="state == 'draft'"
      decoration-success="state == 'done'">

    <!-- Kolom wajib: identifier + status -->
    <field name="name"/>
    <field name="date"/>

    <!-- Kolom penting: tampil by default -->
    <field name="partner_id"/>
    <field name="amount_total"/>

    <!-- Kolom opsional: user bisa toggle -->
    <field name="user_id" optional="hide"/>
    <field name="reference" optional="show"/>

    <!-- Status selalu di kanan -->
    <field name="state" widget="badge"
           decoration-muted="state == 'draft'"
           decoration-success="state == 'done'"/>
</list>
```

### Panduan kolom:
- **Selalu tampil** (tanpa `optional`): identifier, tanggal, amount, status
- **`optional="show"`**: field yang sering dibutuhkan tapi bisa disembunyikan
- **`optional="hide"`**: field jarang dipakai, tersedia tapi tersembunyi default
- **Jangan tampilkan >8 kolom** — terlalu padat, gunakan `optional`

---

## Context: Project Sunartha

- Odoo: 18 Community Edition
- Custom addons path: `custom_addons/`
- Model kustom: `sunartha.journal.transaction`, `sunartha.branch`, `sunartha.ledger`
- Modules aktif: Sales, Purchase, Inventory, CRM, Expenses, Employees, Maintenance, Calendar, Contacts, Project, Accounting Advance
