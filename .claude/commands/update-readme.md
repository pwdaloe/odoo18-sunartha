# Skill: update-readme
# Update README.md project dari kondisi aktual custom_addons yang ada

Anda bertugas memperbarui README.md di root project Odoo 18 Sunartha secara otomatis
berdasarkan kondisi aktual `custom_addons/` — tanpa bertanya dulu, langsung kerjakan.

## Konteks Project
- Project path: `/Users/purwandaru/Documents/Odoo 18 Sunartha`
- Custom addons: `custom_addons/`
- Odoo versi: 18 Community Edition
- Repo GitHub: https://github.com/pwdaloe/odoo18-sunartha

## Langkah Kerja

### 1. Scan custom_addons
Gunakan Bash tool untuk:
```bash
ls /Users/purwandaru/Documents/Odoo 18 Sunartha/custom_addons/
```
Untuk setiap subdirektori yang ditemukan, baca file `__manifest__.py`-nya.

### 2. Ekstrak informasi dari setiap __manifest__.py
Kumpulkan:
- `name` — nama modul
- `version` — versi
- `summary` — deskripsi singkat
- `depends` — dependency list
- `category` — kategori
- `author`
- `installable` — apakah bisa diinstall

### 3. Baca README.md yang ada (jika ada)
Gunakan Read tool untuk membaca isi README.md saat ini agar tidak kehilangan
informasi yang mungkin sudah ada dan tidak bisa di-generate otomatis
(seperti catatan arsitektur khusus, keputusan desain, catatan deployment).

### 4. Tulis ulang README.md

Generate README.md lengkap dengan format berikut:

```markdown
# Odoo 18 Sunartha

[Deskripsi project]

## Cara Menjalankan

[instruksi]

## Struktur Project

[struktur folder]

## Custom Modules

[tabel atau daftar semua modul]

### [Nama Modul 1]
[detail]

### [Nama Modul 2]
[detail]

...

## Dependency Antar Modul

[diagram dependency jika lebih dari 1 modul custom]

## Modul Odoo yang Diaktifkan

[daftar modul Odoo standard yang aktif]

## Catatan Pengembangan

[preserve catatan penting dari README sebelumnya yang tidak bisa di-generate otomatis]
```

### 5. Format yang harus diikuti untuk setiap modul custom

```markdown
### [Nama Modul] (`[technical_name]`)
**Versi:** `[version]`
**Kategori:** [category]
**Summary:** [summary]

**Fitur utama:**
- [fitur 1 — derive dari summary dan nama model di models/]
- [fitur 2]

**Dependencies:** `[dep1]`, `[dep2]`

**Models baru:**
| Model | Deskripsi |
|-------|-----------|
| `model.name` | ... |

**Cara install/update:**
\`\`\`bash
./start_odoo.sh -u [technical_name] --stop-after-init
\`\`\`
```

### 6. Untuk mendapatkan daftar model dari setiap modul
Baca file Python di `models/` setiap modul dan ekstrak:
- `_name` — technical model name
- `_description` — deskripsi model
- `_inherit` — jika inherit model existing

### 7. Tulis ke disk
Gunakan Write tool untuk menulis README.md yang sudah diperbarui.
Setelah selesai, tampilkan ringkasan singkat: berapa modul terdokumentasi,
berapa model yang tercantum, apakah ada perubahan dari versi sebelumnya.

## Catatan Penting
- Jangan hapus bagian "Catatan Pengembangan" dari README yang sudah ada
- Jika README belum ada, buat dari nol
- Selalu cantumkan tanggal terakhir update di footer README
- Format tanggal: DD Bulan YYYY (contoh: 09 Juni 2026)
- Gunakan bahasa Indonesia untuk semua narasi
