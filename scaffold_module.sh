#!/bin/bash
# Script untuk membuat modul custom baru

BASE_DIR="/Users/purwandaru/Documents/Odoo 18 Sunartha"

if [ -z "$1" ]; then
    echo "Usage: ./scaffold_module.sh <nama_modul>"
    exit 1
fi

"$BASE_DIR/venv/bin/python" "$BASE_DIR/odoo/odoo-bin" scaffold "$1" "$BASE_DIR/custom_addons/"
echo "Modul '$1' berhasil dibuat di: $BASE_DIR/custom_addons/$1"
