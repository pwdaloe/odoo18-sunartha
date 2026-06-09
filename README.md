# Odoo 18 Community Edition - Sunartha

Project Odoo 18 CE untuk PT Sunartha.

## Instalasi

### 1. Clone repository
```bash
git clone --recurse-submodules https://github.com/pwdaloe/odoo18-sunartha.git
cd odoo18-sunartha
```

### 2. Setup konfigurasi
```bash
cp odoo.conf.example odoo.conf
# Edit odoo.conf sesuaikan db_password dan admin_passwd
```

### 3. Buat virtual environment
```bash
python3.11 -m venv venv
venv/bin/pip install --upgrade pip wheel
venv/bin/pip install -r odoo/requirements.txt
```

### 4. Jalankan Odoo
```bash
./start_odoo.sh
```

Buka browser: http://localhost:8069

## Struktur Project

```
odoo18-sunartha/
├── odoo/            — Odoo 18 CE source (git submodule)
├── custom_addons/   — Modul custom Sunartha
├── venv/            — Python virtual environment (tidak di-commit)
├── logs/            — Log file (tidak di-commit)
├── odoo.conf        — Konfigurasi server (tidak di-commit)
├── odoo.conf.example — Template konfigurasi
├── start_odoo.sh    — Script menjalankan Odoo
└── scaffold_module.sh — Script membuat modul baru
```

## Membuat Modul Custom

```bash
./scaffold_module.sh nama_modul
```

## Modul yang Diaktifkan

- Sales, Purchase, Inventory
- CRM, Project
- Employees, Expenses
- Maintenance, Calendar, Contacts
