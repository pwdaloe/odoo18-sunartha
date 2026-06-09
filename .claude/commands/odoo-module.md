# Skill: odoo-module
# Generate modul Odoo 18 CE — Standalone App, Extension, atau Bridge

Anda berperan sebagai developer Odoo 18 CE senior.
Ikuti best practice Odoo 18: ORM API terbaru, naming convention, CE-compatible patterns.

## Project Context
- Odoo: 18 Community Edition
- Custom addons path: `custom_addons/`
- Active modules: Sales, Purchase, Inventory, CRM, Expenses, Employees, Maintenance, Calendar, Contacts, Project, Accounting Advance
- Model references: sale.order, purchase.order, stock.picking, crm.lead, hr.employee, hr.expense, maintenance.request, project.project, project.task, res.partner, calendar.event, sunartha.journal.transaction

---

## Langkah 1 — Tanya Mode

**Selalu tanya ini pertama kali:**

> "Modul apa yang ingin dibuat? Pilih mode:
>
> **A. Standalone App** — App baru muncul di menu utama (seperti Sales, Invoicing)
> Model baru dari nol, punya icon dan top-level menu sendiri.
>
> **B. Extension** — Tambah field/logic/view ke modul Odoo existing
> Tidak butuh app baru, cukup inherit model/view yang ada.
> *(Akan menggunakan pendekatan `/odoo-inherit`)*
>
> **C. Bridge** — Connector antara dua modul
> Menghubungkan data dari dua modul berbeda (misal: Sale Order ↔ Project Task)."

Jika user menyebut `/odoo-spec` sebelumnya, baca spec tersebut dan tentukan mode otomatis.

---

## MODE A — Standalone App

### A1. Clarification Questions

Ajukan semua pertanyaan ini sebelum generate:

1. **Nama teknis** (snake_case): `sunartha_[nama]`
2. **Nama tampilan** di menu utama?
3. **Deskripsi** satu kalimat fungsinya?
4. **Models** — berapa model? Header + lines? Master data?
5. **Fields wajib** per model?
6. **Workflow approval?** (draft → submitted → approved → posted)
7. **Views**: form + list wajib. Tambah kanban untuk dashboard?
8. **Master data** yang perlu dikonfigurasi? (Branch, Category, Type, dll)
9. **Auto-numbering?** Format prefix? (contoh: `GL/2026/06/0001`)
10. **PDF Report?**
11. **CE-strict?** (hindari dependency Enterprise seperti `account_accountant`)

Jika ada pertanyaan tentang UI/UX layout, gunakan skill `/odoo-ui` untuk brainstorming visual sebelum generate.

### A2. File Structure

```
custom_addons/[module_name]/
├── __init__.py
├── __manifest__.py
├── static/
│   └── description/
│       └── icon.png                    ← auto-generate dengan Python
├── models/
│   ├── __init__.py
│   ├── [main_model].py
│   ├── [line_model].py                 ← jika ada header+lines
│   ├── [master_model].py               ← jika ada master data
│   └── [reject_wizard].py             ← jika ada approval
├── views/
│   ├── [main_model]_views.xml
│   ├── [master_model]_views.xml
│   ├── [wizard]_views.xml
│   └── menu.xml
├── security/
│   ├── security.xml
│   └── ir.model.access.csv
├── data/
│   └── sequence_data.xml
└── reports/                            ← opsional
    ├── report_action.xml
    └── report_[name].xml
```

Tampilkan rencana ini ke user dan tanya konfirmasi sebelum generate.

### A3. Coding Standards

#### __manifest__.py
```python
{
    'name': 'Nama App',
    'version': '18.0.1.0.0',
    'category': 'Category',
    'summary': 'Deskripsi singkat — CE compatible',
    'author': 'Sunartha',
    'website': 'https://sunartha.co.id',
    'depends': ['base', 'mail'],        # hanya yang benar-benar dipakai
    'data': [...],
    'installable': True,
    'application': True,                # WAJIB True untuk standalone app
    'license': 'LGPL-3',
}
```

#### icon.png — Auto-generate
Selalu buat `static/description/icon.png` via Python script (128x128 px).
Jangan biarkan kosong — app tidak akan tampil baik di home menu tanpa icon.

```python
# Generate minimal valid PNG 128x128
import struct, zlib
def make_png(w, h, bg_rgb, fg_rgb): ...
```

#### menu.xml — Standalone Pattern
```xml
<!-- Root menu: WAJIB punya web_icon -->
<menuitem id="menu_[app]_root"
          name="Nama App"
          web_icon="[module],static/description/icon.png"
          sequence="55"/>

<!-- WAJIB: minimal 1 child menu TANPA groups agar app selalu terlihat -->
<menuitem id="menu_[app]_dashboard"
          name="Dashboard"
          parent="menu_[app]_root"
          action="action_[model]_dashboard"
          sequence="10"/>
          <!-- TIDAK ada attribute groups di sini -->

<!-- Menu lain boleh pakai groups -->
<menuitem id="menu_[app]_config"
          name="Konfigurasi"
          parent="menu_[app]_root"
          sequence="90"
          groups="[module].group_[app]_manager"/>
```

> **CRITICAL:** Jika SEMUA child menu punya `groups` restriction dan user tidak ada di group tersebut,
> seluruh app tidak akan muncul di home menu. Selalu biarkan minimal 1 menu tanpa restriction.

#### security.xml — Custom Groups (bukan base.group_system)
```xml
<record id="group_[app]_user" model="res.groups">
    <field name="name">User</field>
    <field name="category_id" ref="base.module_category_[category]"/>
    <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
</record>

<record id="group_[app]_manager" model="res.groups">
    <field name="name">Manager</field>
    <field name="category_id" ref="base.module_category_[category]"/>
    <field name="implied_ids" eval="[(4, ref('[module].group_[app]_user'))]"/>
</record>
```

#### Main Model
```python
class [ModelName](models.Model):
    _name = '[module].[model]'
    _description = '[Description]'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(default='New', readonly=True, copy=False, index=True)

    # Odoo 18: override _compute_display_name, bukan name_get
    @api.depends('name', 'description')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.name} - {rec.description}" if rec.description else rec.name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('[module].[model]') or 'New'
        return super().create(vals_list)
```

#### Many2many — Relation Table Name
```python
# WAJIB set relation= jika gabungan nama model > 63 karakter
# PostgreSQL limit: 63 karakter untuk nama tabel
field_ids = fields.Many2many(
    '[model.long.name]',
    '[short_rel_table_name]',   # max ~40 karakter
    'source_id', 'target_id',
    string='...')
```

---

### A4. Form View — Invoice-Style Layout (Standard)

**Gunakan template ini untuk semua form view dokumen transaksi.**
Template ini sudah terbukti bekerja di Odoo 18 CE (diuji di sunartha_accounting_advance).

```xml
<form string="[Model Name]">
    <header>
        <!-- Urutan: primary left, destructive/secondary right -->
        <button name="action_submit" string="Submit" type="object"
                class="btn-warning" invisible="state != 'draft'"/>
        <button name="action_approve" string="Approve" type="object"
                class="btn-success"
                groups="[module].group_[app]_manager"
                invisible="state != 'submitted'"/>
        <button name="action_reject" string="Reject" type="object"
                class="btn-danger"
                groups="[module].group_[app]_manager"
                invisible="state != 'submitted'"/>
        <button name="action_post" string="Post" type="object"
                class="btn-primary"
                groups="[module].group_[app]_manager"
                invisible="state != 'approved'"/>
        <button name="action_reset_draft" string="Reset ke Draft" type="object"
                invisible="state != 'submitted' and state != 'rejected'"/>
        <field name="state" widget="statusbar"
               statusbar_visible="draft,submitted,approved,posted"/>
    </header>
    <sheet>

        <!-- Smart Buttons — hanya jika ada relasi ke dokumen lain -->
        <div class="oe_button_box" name="button_box">
            <button name="action_view_related" type="object"
                    class="oe_stat_button" icon="fa-list"
                    invisible="related_count == 0">
                <field name="related_count" widget="statinfo" string="Terkait"/>
            </button>
        </div>

        <!-- Title + Type/Category Badge -->
        <div class="oe_title">
            <h1><field name="name" readonly="1"/></h1>
            <field name="type_field" widget="badge"
                   decoration-info="type_field == 'type_a'"
                   decoration-warning="type_field == 'type_b'"
                   decoration-success="type_field == 'type_c'"
                   decoration-muted="type_field == 'type_d'"
                   readonly="state != 'draft'"/>
        </div>

        <!-- 2-column Header: Informasi | Referensi -->
        <group>
            <group string="Informasi">
                <field name="date" readonly="state != 'draft'"/>
                <field name="period" readonly="1"/>
                <field name="reference" readonly="1"/>
                <field name="type_field" readonly="state != 'draft'"/>
            </group>
            <group string="Referensi">
                <field name="branch_id" readonly="state != 'draft'"/>
                <field name="currency_id" readonly="state != 'draft'"
                       options="{'no_create': True}"/>
                <field name="company_id"
                       groups="base.group_multi_company" readonly="1"/>
                <field name="user_id" readonly="1"/>
            </group>
        </group>

        <!-- Description -->
        <group string="Keterangan">
            <field name="description" nolabel="1"
                   placeholder="Keterangan..."
                   readonly="state != 'draft'"/>
        </group>

        <!-- Alert: rejection / warning — muncul conditional -->
        <div class="alert alert-danger mb-0" role="alert"
             invisible="not rejection_reason">
            <span class="fw-bold">Ditolak: </span>
            <field name="rejection_reason" nolabel="1" readonly="1"
                   class="d-inline"/>
        </div>

        <!-- Notebook -->
        <notebook>
            <!-- Tab 1: SELALU tab pertama, konten utama -->
            <page string="Detail" name="details">

                <!-- Lines (jika model punya header+lines) -->
                <field name="line_ids" readonly="state != 'draft'">
                    <list editable="bottom"
                          decoration-muted="amount == 0">
                        <field name="sequence" widget="handle"/>
                        <field name="product_id" options="{'no_create': True}"/>
                        <field name="description"/>
                        <field name="quantity" sum="Total Qty"/>
                        <field name="unit_price"/>
                        <field name="currency_id" column_invisible="1"/>
                        <field name="amount" sum="Total"/>
                    </list>
                </field>

                <!-- Totals: rata kanan bawah, mirip Invoice -->
                <div class="clearfix mt-2">
                    <group class="oe_subtotal_footer oe_right col-6 offset-6">
                        <field name="amount_total" readonly="1" string="Total"/>
                    </group>
                </div>

            </page>

            <!-- Tab 2: Other Info — approval, audit, config sekunder -->
            <page string="Other Info" name="other_info">
                <group>
                    <group string="Persetujuan">
                        <field name="approver_id" readonly="1"/>
                        <field name="approval_date" readonly="1"/>
                    </group>
                </group>
            </page>
        </notebook>
    </sheet>

    <!-- WAJIB: <chatter/> bukan <div class="oe_chatter"> -->
    <chatter/>
</form>
```

**Notes:**
- Hapus bagian yang tidak dipakai (smart buttons jika tidak ada relasi, lines jika model sederhana)
- Tambah `decoration-*` di badge sesuai nilai Selection field
- Tab "Other Info" wajib ada jika ada approval workflow — simpan approver/date di sana
- `<chatter/>` HARUS di luar `<sheet>`, langsung di bawahnya

---

### A5. List View — Standard Pattern

```xml
<list string="[Model Name]"
      decoration-muted="state == 'cancelled' or state == 'posted'"
      decoration-warning="state == 'submitted'"
      decoration-success="state == 'approved'"
      decoration-danger="state == 'rejected'">

    <!-- Kolom wajib: identifier + type badge + tanggal + amount + status -->
    <field name="name"/>
    <field name="type_field" widget="badge"
           decoration-info="type_field == 'type_a'"
           decoration-warning="type_field == 'type_b'"
           decoration-success="type_field == 'type_c'"/>
    <field name="date"/>

    <!-- Kolom penting: tampil by default -->
    <field name="partner_id"/>
    <field name="currency_id" column_invisible="1"/>
    <field name="amount_total"/>

    <!-- Kolom opsional: user bisa toggle -->
    <field name="user_id" optional="hide"/>
    <field name="approver_id" optional="show"/>

    <!-- Status selalu paling kanan -->
    <field name="state" widget="badge"
           decoration-muted="state == 'draft'"
           decoration-warning="state == 'submitted'"
           decoration-success="state == 'approved'"
           decoration-info="state == 'posted'"
           decoration-danger="state == 'rejected'"/>
</list>
```

---

### A6. Views — Odoo 18 Syntax Rules

```xml
<!-- ✅ BENAR: readonly expression -->
<field name="x" readonly="state != 'draft'"/>
<field name="x" readonly="state != 'draft' and state != 'new'"/>

<!-- ❌ SALAH di Odoo 18: -->
<!-- <field name="x" readonly="state not in ('draft', 'new')"/> -->

<!-- ✅ BENAR: invisible expression -->
<field name="x" invisible="not field_id"/>
<button ... invisible="state != 'submitted' and state != 'rejected'"/>

<!-- ❌ SALAH di Odoo 18: -->
<!-- invisible="state not in ('submitted', 'rejected')" -->

<!-- ✅ BENAR: badge decoration -->
<field name="state" widget="badge"
       decoration-muted="state == 'draft'"
       decoration-warning="state == 'submitted'"
       decoration-success="state == 'approved'"
       decoration-info="state == 'posted'"
       decoration-danger="state == 'rejected'"/>

<!-- ❌ SALAH: decoration-secondary tidak valid di Odoo 18 -->

<!-- ✅ BENAR: list row decoration -->
<list decoration-warning="state == 'a' or state == 'b'">
<!-- ❌ SALAH: -->
<!-- <list decoration-warning="state in ('a', 'b')"> -->

<!-- ✅ BENAR: chatter di Odoo 18 -->
<chatter/>

<!-- ❌ SALAH / lama — render sebagai raw list view di Odoo 18: -->
<!-- <div class="oe_chatter">
    <field name="message_follower_ids"/>
    <field name="activity_ids"/>
    <field name="message_ids"/>
</div> -->
```

#### CE-Compatible Account Domain
```python
# ✅ BENAR di Odoo 18 CE:
account_id = fields.Many2one('account.account',
    domain="[('deprecated', '=', False)]")

# ❌ SALAH — company_id tidak ada di account.account Odoo 18 CE:
# domain="[('deprecated','=',False), ('company_id','=',parent.company_id)]"
```

---

## MODE B — Extension

Gunakan pendekatan `odoo-inherit`. Tanya user:

1. **Model mana** yang di-extend? (sale.order, hr.employee, dll)
2. **Apa yang ditambahkan?** (field, method, view, tab, button)
3. **Di modul mana** diletakkan? (modul existing atau buat baru)

Lalu ikuti pattern dari skill `/odoo-inherit`:
- Model inheritance: `_inherit = 'model.name'`
- View inheritance: `inherit_id` + XPath `position="after/before/inside"`
- Method override: selalu `super()` kecuali ada alasan kuat

Buat modul baru minimal jika tidak ada modul yang sesuai:
```
custom_addons/[module_name]/
├── __init__.py
├── __manifest__.py          ← application: False
├── models/
│   ├── __init__.py
│   └── [model]_extend.py
└── views/
    └── [model]_views_extend.xml
```

---

## MODE C — Bridge Module

Menghubungkan dua modul yang tidak saling kenal.

### C1. Clarification Questions

1. **Modul A dan B** yang ingin dihubungkan?
2. **Record mana yang di-link?** (sale.order ↔ project.task, hr.employee ↔ crm.lead, dll)
3. **Relasi:** one-to-one, one-to-many, atau many-to-many?
4. **Arah sync data:** A → B, B → A, atau dua arah?
5. **Trigger:** manual (tombol) atau otomatis (saat create/confirm/post)?
6. **Field yang di-copy/sync?**

### C2. File Structure

```
custom_addons/[module_name]/
├── __init__.py
├── __manifest__.py          ← application: False, depends: [module_a, module_b]
├── models/
│   ├── __init__.py
│   ├── [model_a]_extend.py  ← tambah relasi ke model B
│   └── [model_b]_extend.py  ← tambah relasi ke model A
└── views/
    ├── [model_a]_views.xml  ← tambah tab/field di form A
    └── [model_b]_views.xml  ← tambah tab/field di form B
```

### C3. Bridge Pattern
```python
# Di model A — tambah relasi ke B
class ModelAExtend(models.Model):
    _inherit = 'module_a.model'

    bridge_ids = fields.One2many(
        'module_b.model', 'source_a_id', string='Related B')
    bridge_count = fields.Integer(compute='_compute_bridge_count')

    @api.depends('bridge_ids')
    def _compute_bridge_count(self):
        for rec in self:
            rec.bridge_count = len(rec.bridge_ids)

    def action_view_bridge(self):
        """Smart button — buka list B terkait."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'module_b.model',
            'view_mode': 'list,form',
            'domain': [('source_a_id', '=', self.id)],
            'context': {'default_source_a_id': self.id},
        }
```

### C4. Smart Button Pattern (View)
```xml
<div class="oe_button_box" name="button_box">
    <button name="action_view_bridge" type="object"
            class="oe_stat_button" icon="fa-link"
            invisible="bridge_count == 0">
        <field name="bridge_count" widget="statinfo" string="B Records"/>
    </button>
</div>
```

---

## Common Pitfalls — Selalu Cek Sebelum Generate

| # | Masalah | Solusi |
|---|---------|--------|
| 1 | App tidak muncul di home menu | Pastikan ada 1 child menu tanpa `groups` attribute |
| 2 | `decoration-secondary` error | Ganti dengan `decoration-muted` |
| 3 | `state in (...)` di decoration/invisible | Ganti dengan `state == 'a' or state == 'b'` |
| 4 | `state not in (...)` di readonly/invisible | Ganti dengan `state != 'a' and state != 'b'` |
| 5 | Relation table name > 63 karakter | Set parameter `relation='nama_rel_pendek'` di Many2many |
| 6 | `account.account` domain company_id | Field tidak ada di Odoo 18 CE, hapus filter company dari domain |
| 7 | `<field>` di dalam `<div>` di dalam `<group>` | Pindahkan field ke luar div, atau gunakan `<group>` langsung |
| 8 | `name_get` override | Diganti `_compute_display_name` di Odoo 18 |
| 9 | Depend `l10n_id_efaktur_coretax` atau Enterprise | Periksa dulu apakah modul ada di CE, jadikan opsional jika ragu |
| 10 | User tidak bisa akses modul setelah install | Assign user ke group via Settings → Users, atau lewat database |
| 11 | Chatter muncul sebagai raw list view | Ganti `<div class="oe_chatter">` dengan `<chatter/>` |
| 12 | Totals lines tidak rata kanan | Gunakan `<group class="oe_subtotal_footer oe_right col-6 offset-6">` |
| 13 | Groups modul tabrakan dengan Invoicing | Buat `ir.module.category` sendiri di security.xml (bukan pakai `base.module_category_accounting_accounting`) |
| 14 | `null value in column "model_id"` saat upgrade dengan model baru | Restart server dulu — Python baru tidak di-import tanpa restart. Lalu gunakan `search=` di security.xml, bukan CSV |
| 15 | `editable` attribute error di list view | `editable="0"` tidak valid di Odoo 18 — gunakan `editable="top"` / `editable="bottom"`, atau hapus atribut (read-only default) |

---

## Langkah Final (semua mode)

### Generate & Write
Setelah user konfirmasi struktur, langsung tulis **semua file sekaligus** ke disk.
Jangan generate satu per satu — tulis semua dalam satu respons.

### Upgrade & Test

#### ⚠️ WAJIB RESTART SERVER jika ada file Python baru

**Kapan harus restart:** Setiap kali menambah **file Python baru** ke modul (model baru, wizard baru, dll).

**Alasannya:** Odoo menggunakan `importlib.import_module()` dengan caching di `sys.modules`. Jika modul sudah pernah di-import (server sedang berjalan), file Python baru **tidak akan di-import ulang** meski sudah ada di disk. Akibatnya:
- Model baru tidak masuk ke `MetaModel.module_to_models`
- `init_models` tidak memproses model baru
- Tabel dan `ir.model` record tidak dibuat
- Semua referensi ke model baru di CSV/XML akan gagal dengan `null value in model_id`

**Cara restart + upgrade sekaligus (paling efisien):**
```bash
cd "/Users/purwandaru/Documents/Odoo 18 Sunartha"

# Hentikan server yang berjalan
pkill -f "odoo-bin"

# Restart + upgrade sekaligus
./start_odoo.sh -d odoo18_sunartha -u [module_name]
```

**Jika hanya edit file XML/CSV/view (tanpa tambah Python baru):** Upgrade dari UI sudah cukup, tidak perlu restart server.

```bash
# Cek hasil upgrade di log
grep -E "(ERROR|[module_name].*loaded)" logs/odoo.log | tail -10
```

#### Untuk modul BARU (belum pernah install):
1. Restart server: `pkill -f "odoo-bin" && ./start_odoo.sh`
2. Update module list dari UI: Apps → Update Apps List
3. Cari nama modul → klik Install

#### Untuk ir.model.access.csv — model BARU di modul yang sudah install

**Problem:** Saat pertama upgrade (sebelum restart), external ID `model_[nama_model]` belum ada di `ir.model.data`.

**Solusi:** Gunakan `search=` di `security.xml` untuk model baru (bukan CSV):
```xml
<!-- Di security.xml — untuk model yang ditambahkan di upgrade -->
<record id="access_[model]_user" model="ir.model.access">
    <field name="name">access.[model].user</field>
    <field name="model_id" search="[('model', '=', '[module].[model]')]"/>
    <field name="group_id" ref="[module].group_[app]_user"/>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="True"/>
    <field name="perm_create" eval="True"/>
    <field name="perm_unlink" eval="True"/>
</record>
```

Ini menggunakan lookup langsung ke tabel `ir.model` (bukan via `ir.model.data`), sehingga bekerja dengan benar setelah server restart + upgrade.

**Catatan:** Model yang sudah ada sejak install pertama tetap bisa pakai CSV seperti biasa.
