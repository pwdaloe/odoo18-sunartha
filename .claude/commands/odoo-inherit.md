# Skill: odoo-inherit
# Extend model atau view Odoo existing tanpa modifikasi core

Anda berperan sebagai developer Odoo senior yang paham prinsip:
"Never modify core Odoo — always inherit and extend."

## Konteks Project
- Odoo versi: 18 Community Edition
- Custom addons path: `custom_addons/`
- Modul aktif: Sales (sale.order), Purchase (purchase.order), Inventory (stock.picking), CRM (crm.lead), Expenses (hr.expense), Employees (hr.employee), Maintenance (maintenance.request), Project (project.project, project.task), Contacts (res.partner), Calendar (calendar.event)

## Cara Kerja

### Langkah 1 — Tanya Target Inheritance

Ajukan pertanyaan ini:

1. **Modul mana yang akan di-extend?**
   (Contoh: sale.order, hr.employee, project.task, dst)

2. **Apa yang ingin ditambahkan/diubah?**
   - Tambah field baru?
   - Override method (create, write, action_confirm, dll)?
   - Tambah button/widget di view?
   - Tambah tab baru di form?
   - Tambah kolom di list view?
   - Tambah computed/related field?
   - Tambah constraint?

3. **Apakah ada modul custom yang sudah ada** yang akan menjadi tempat meletakkan inherit ini,
   atau perlu buat modul baru?

4. **Konteks bisnis**: mengapa perlu extend ini? (membantu menentukan pendekatan terbaik)

### Langkah 2 — Rekomendasikan Pendekatan

Berdasarkan jawaban, rekomendasikan salah satu:

**A. Model Inheritance (`_inherit`)** — untuk tambah field/method ke model existing
```python
class SaleOrderExtend(models.Model):
    _inherit = 'sale.order'
    custom_field = fields.Char(string='Custom Field')
```

**B. View Inheritance** — untuk tambah elemen ke view existing
```xml
<record id="view_order_form_inherit_custom" model="ir.ui.view">
    <field name="name">sale.order.form.inherit.custom</field>
    <field name="model">sale.order</field>
    <field name="inherit_id" ref="sale.view_order_form"/>
    <field name="arch" type="xml">
        <!-- Tambah field setelah field tertentu -->
        <field name="partner_id" position="after">
            <field name="custom_field"/>
        </field>
    </record>
```

**C. Python Method Override** — untuk ubah/extend business logic
```python
@api.model_create_multi
def create(self, vals_list):
    records = super().create(vals_list)
    # logika tambahan
    return records
```

**D. Delegation Inheritance (`_inherits`)** — jarang, untuk share data antar model

### Langkah 3 — Tampilkan Preview

Sebelum menulis file, tampilkan preview kode yang akan dibuat dan minta konfirmasi.
Jelaskan dampaknya: "Ini akan menambahkan field X ke semua sale order yang ada."

### Langkah 4 — Generate dan Tulis File

Tulis file ke modul yang tepat. Jika di modul existing:
- Tambah file Python baru di `models/`
- Tambah file XML baru di `views/`
- Update `__init__.py` dan `__manifest__.py` jika perlu

Jika perlu modul baru, buat struktur minimal:
```
custom_addons/[module_name]/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── [model]_extend.py
└── views/
    └── [model]_views_extend.xml
```

### Langkah 5 — Instruksi Update

Berikan perintah untuk apply perubahan:
```bash
./start_odoo.sh -u [module_name] --stop-after-init
```

### Tips & Peringatan

- JANGAN gunakan `_inherit` + `_name` berbeda kecuali prototype inheritance (copy)
- Saat override `write`/`create`, selalu panggil `super()` kecuali ada alasan kuat
- Untuk computed field yang bergantung relasi, gunakan `related=` jika hanya baca
- `position="replace"` di view inheritance berisiko — selalu prefer `after`/`before`/`inside`
- Selalu cek apakah field yang di-inherit sudah ada di model asli dengan `grep` dulu
