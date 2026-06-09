# Skill: push-github
# Commit dan push perubahan ke GitHub — dengan proteksi credential otomatis

Anda bertugas melakukan git commit + push ke remote `origin` (https://github.com/pwdaloe/odoo18-sunartha)
dengan aman. Repo ini **public** — jangan pernah commit file credential.

## KEAMANAN — Wajib Dicek Sebelum Apapun

File yang TIDAK BOLEH masuk git (sudah di .gitignore, tapi verifikasi ulang):
- `odoo.conf` — berisi `db_password` dan `admin_passwd`
- `venv/` — virtual environment Python
- `logs/` — log Odoo
- `.local/` — data Odoo lokal
- `*.secret`, `.env`

## Langkah Kerja

### Langkah 1 — Verifikasi keamanan
Jalankan:
```bash
git -C "/Users/purwandaru/Documents/Odoo 18 Sunartha" status --short
```

Periksa output: jika ada file berikut di staged/unstaged area, **BERHENTI dan peringatkan user**:
- `odoo.conf`
- file di `venv/`
- file di `logs/`
- file di `.local/`
- file berekstensi `.secret` atau nama `.env`

Jika ada file sensitif, tampilkan peringatan merah dan JANGAN lanjutkan.

### Langkah 2 — Tampilkan diff ringkas
```bash
git -C "/Users/purwandaru/Documents/Odoo 18 Sunartha" diff --stat HEAD
git -C "/Users/purwandaru/Documents/Odoo 18 Sunartha" status --short
```

Tampilkan kepada user: file apa saja yang akan di-commit.

### Langkah 3 — Buat commit message
Dari $ARGUMENTS ambil pesan commit jika ada. Jika tidak ada, analisis perubahan:
- Jika ada modul baru di `custom_addons/` → `feat: add [module_name] module`
- Jika ada perubahan pada modul existing → `feat([module_name]): [deskripsi singkat]`
- Jika hanya update README → `docs: update README`
- Jika fix bug → `fix([module_name]): [deskripsi]`
- Jika update skill/config → `chore: update dev config`

Format: [type]([scope]): [deskripsi] — max 72 karakter, bahasa Inggris.

### Langkah 4 — Stage dan commit
```bash
cd "/Users/purwandaru/Documents/Odoo 18 Sunartha" && \
  git add -A && \
  git status --short
```

Tampilkan staged files, lalu konfirmasi ke user:
"File di atas akan di-commit dengan pesan: `[commit message]`. Lanjutkan? (y/n)"

Jika user jawab **y** atau **ya** atau langsung `$ARGUMENTS` berisi pesan commit tanpa interaksi, lanjutkan.

### Langkah 5 — Commit
```bash
git -C "/Users/purwandaru/Documents/Odoo 18 Sunartha" commit -m "[commit message]"
```

### Langkah 6 — Push ke GitHub
```bash
git -C "/Users/purwandaru/Documents/Odoo 18 Sunartha" push origin main
```

Jika error karena branch tidak ada: coba `git push -u origin main`
Jika error karena diverged history: tampilkan error dan tanya user apakah mau `git pull --rebase` dulu.

### Langkah 7 — Konfirmasi
Setelah push sukses, tampilkan:
- Commit hash
- Branch yang di-push
- Link ke repo: https://github.com/pwdaloe/odoo18-sunartha
- Ringkasan: berapa file changed, berapa insertions/deletions

## Penggunaan

```
/push-github                        → auto-detect perubahan, tanya pesan commit
/push-github feat: add maritime     → langsung commit + push dengan pesan ini
/push-github "docs: update README"  → commit dengan pesan spesifik
```

## Catatan Penting
- Repo ini PUBLIC — verifikasi .gitignore sebelum setiap push
- Branch utama: `main`
- Remote: `origin` → https://github.com/pwdaloe/odoo18-sunartha
- Submodule `odoo/` tidak di-push ulang (hanya pointer commit yang berubah)
