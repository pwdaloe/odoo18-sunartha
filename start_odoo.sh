#!/bin/bash
# Script untuk menjalankan Odoo 18 CE - Sunartha

BASE_DIR="/Users/purwandaru/Documents/Odoo 18 Sunartha"

echo "Starting Odoo 18 Community Edition..."
echo "URL: http://localhost:8069"
echo "Tekan Ctrl+C untuk menghentikan."
echo ""

"$BASE_DIR/venv/bin/python" "$BASE_DIR/odoo/odoo-bin" \
    --config="$BASE_DIR/odoo.conf" \
    "$@"
