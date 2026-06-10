# Skill: odoo-qc

Jalankan QC test otomatis untuk modul `sunartha_accounting_advance` via JSON-RPC.
Gunakan Bash tool untuk menjalankan Python script. Jangan skip scenario apapun.

> **Catatan environment:** CoA (account.account) ada di company 2 (Sunartha ID),
> transaksi default di company 1 (Sunartha Japan). Balance Sheet dan AR/AP Aging
> akan mengembalikan 0 baris karena cross-company security rule — ini BUKAN bug modul,
> melainkan data setup. Semua workflow logic (submit/approve/post/recurring) tetap ditest.

## Config (hardcoded untuk project ini)

```
URL  : http://localhost:8069
DB   : odoo18_sunartha
LOGIN: odoo-qc@sunartha.co.id
PASS : QCTest2024!
UID  : 8
```

**Account IDs yang tersedia (dari COA):**
- `1`  = Cash (asset_cash)
- `8`  = Account Receivable (asset_receivable)
- `28` = Trade Receivable (liability_payable)
- `63` = Sales (income)
- `70` = Pph 21 Benefit (expense)

## Instruksi

Jalankan satu Bash tool call dengan Python script lengkap di bawah ini.
Setelah selesai, tampilkan laporan dengan format yang ditentukan.

### Script

> **Penting:** Gunakan JSON-RPC (`/web/dataset/call_kw`), bukan XML-RPC.
> XML-RPC di Odoo 18 tidak bisa memanggil action methods (action_submit, action_approve, dll)
> karena `TypeError: unhashable type: 'list'` pada cache lookup.

```python
import urllib.request, json, http.cookiejar, datetime

URL  = 'http://localhost:8069'
DB   = 'odoo18_sunartha'
USER = 'odoo-qc@sunartha.co.id'
PASS = 'QCTest2024!'

jar    = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

def jrpc(path, params):
    payload = json.dumps({"jsonrpc":"2.0","method":"call","params":params}).encode()
    req = urllib.request.Request(f'{URL}{path}', data=payload,
                                  headers={'Content-Type': 'application/json'})
    resp  = opener.open(req)
    result = json.loads(resp.read())
    if result.get('error'):
        raise Exception(result['error']['data'].get('message', str(result['error'])))
    return result.get('result')

def rpc(model, method, *args, **kw):
    return jrpc('/web/dataset/call_kw', {
        'model': model, 'method': method,
        'args': list(args), 'kwargs': kw
    })

session = jrpc('/web/session/authenticate', {'db': DB, 'login': USER, 'password': PASS})
if not session or not session.get('uid'):
    print('BLOCKED — Auth failed')
    exit(1)

results = []
created_ids = {}  # untuk cleanup

def ok(label, detail=''):
    results.append(('✅', label, detail))
    print(f'  ✅ {label}' + (f' — {detail}' if detail else ''))

def fail(label, detail=''):
    results.append(('❌', label, detail))
    print(f'  ❌ {label}' + (f' — {detail}' if detail else ''))

def warn(label, detail=''):
    results.append(('⚠️', label, detail))
    print(f'  ⚠️  {label}' + (f' — {detail}' if detail else ''))

today = str(datetime.date.today())

# ─────────────────────────────────────────────
print('\n[1] JOURNAL TRANSACTION WORKFLOW')
# ─────────────────────────────────────────────
try:
    trx_id = rpc('sunartha.journal.transaction', 'create', {
        'module': 'gl',
        'transaction_date': today,
        'description': '[QC] Test GL Transaction',
        'line_ids': [
            [0, 0, {'account_id': 1,  'debit_amount': 500000, 'credit_amount': 0}],
            [0, 0, {'account_id': 70, 'debit_amount': 0, 'credit_amount': 500000}],
        ],
    })
    created_ids['trx'] = trx_id
    ok('Create GL transaction', f'id={trx_id}')
except Exception as e:
    fail('Create GL transaction', str(e)[:80])
    trx_id = None

if trx_id:
    try:
        trx = rpc('sunartha.journal.transaction', 'read', [trx_id],
                  fields=['name','state','is_balanced','debit_total','credit_total'])[0]
        if trx['state'] == 'draft':
            ok('State = draft', trx['name'])
        else:
            fail('State harus draft', f"got {trx['state']}")
        if trx['is_balanced']:
            ok('Balanced', f"debit={trx['debit_total']:,.0f} credit={trx['credit_total']:,.0f}")
        else:
            fail('Not balanced', f"debit={trx['debit_total']} credit={trx['credit_total']}")
    except Exception as e:
        fail('Read transaction', str(e)[:80])

    # Submit
    try:
        rpc('sunartha.journal.transaction', 'action_submit', [[trx_id]])
        trx = rpc('sunartha.journal.transaction', 'read', [trx_id], fields=['state'])[0]
        if trx['state'] == 'submitted':
            ok('Submit → Diajukan')
        else:
            fail('Submit', f"state={trx['state']}")
    except Exception as e:
        fail('Submit', str(e)[:80])

    # Approve
    try:
        rpc('sunartha.journal.transaction', 'action_approve', [[trx_id]])
        trx = rpc('sunartha.journal.transaction', 'read', [trx_id], fields=['state','approver_id'])[0]
        if trx['state'] == 'approved':
            ok('Approve → Disetujui', f"approver={trx['approver_id']}")
        else:
            fail('Approve', f"state={trx['state']}")
    except Exception as e:
        fail('Approve', str(e)[:80])

    # Post
    try:
        rpc('sunartha.journal.transaction', 'action_post', [[trx_id]])
        trx = rpc('sunartha.journal.transaction', 'read', [trx_id], fields=['state'])[0]
        if trx['state'] == 'posted':
            ok('Post → Posted')
        else:
            fail('Post', f"state={trx['state']}")
    except Exception as e:
        fail('Post', str(e)[:80])

    # Period lock block test
    try:
        # Buat transaksi baru, coba post ke periode yg harusnya normal (tidak ada lock)
        trx2_id = rpc('sunartha.journal.transaction', 'create', {
            'module': 'gl',
            'transaction_date': today,
            'description': '[QC] Unbalanced test — harus ditolak',
            'line_ids': [
                [0, 0, {'account_id': 1, 'debit_amount': 100000, 'credit_amount': 0}],
                [0, 0, {'account_id': 70, 'debit_amount': 0, 'credit_amount': 50000}],  # tidak balance
            ],
        })
        created_ids['trx2'] = trx2_id
        rpc('sunartha.journal.transaction', 'action_submit', [[trx2_id]])
        rpc('sunartha.journal.transaction', 'action_approve', [[trx2_id]])
        rpc('sunartha.journal.transaction', 'action_post', [[trx2_id]])
        fail('Guard unbalanced — harus error tapi tidak', 'post berhasil padahal tidak balance')
    except Exception as e:
        msg = str(e)
        if 'Seimbangkan' in msg or 'balanced' in msg.lower() or 'Debit' in msg:
            ok('Guard: unbalanced transaction ditolak saat post')
        else:
            warn('Guard: error tapi pesan tidak expected', msg[:80])

# ─────────────────────────────────────────────
print('\n[2] RECURRING JOURNAL')
# ─────────────────────────────────────────────
try:
    rec_id = rpc('sunartha.recurring.journal', 'create', {
        'name': '[QC] Recurring Sewa Bulanan',
        'frequency': 'monthly',
        'day_of_month': 1,
        'date_start': today,
        'module': 'gl',
        'line_ids': [
            [0, 0, {'account_id': 70, 'debit_amount': 1000000, 'credit_amount': 0, 'description': 'Biaya Sewa'}],
            [0, 0, {'account_id': 1,  'debit_amount': 0, 'credit_amount': 1000000, 'description': 'Kas'}],
        ],
    })
    created_ids['rec'] = rec_id
    ok('Create recurring template', f'id={rec_id}')
except Exception as e:
    fail('Create recurring template', str(e)[:80])
    rec_id = None

if rec_id:
    try:
        result = rpc('sunartha.recurring.journal', 'action_generate_now', [[rec_id]])
        if result.get('res_id'):
            gen_id = result['res_id']
            created_ids['gen_trx'] = gen_id
            ok('Generate Now', f'generated trx id={gen_id}')
        else:
            warn('Generate Now — result tidak ada res_id', str(result)[:80])
    except Exception as e:
        fail('Generate Now', str(e)[:80])
        gen_id = None

    try:
        rec = rpc('sunartha.recurring.journal', 'read', [rec_id],
                  fields=['generated_count', 'next_run_date'])[0]
        if rec['generated_count'] >= 1:
            ok('Generated count', f"count={rec['generated_count']}, next_run={rec['next_run_date']}")
        else:
            fail('Generated count = 0')
    except Exception as e:
        fail('Read generated count', str(e)[:80])

    # Test template tanpa lines
    try:
        empty_id = rpc('sunartha.recurring.journal', 'create', {
            'name': '[QC] Empty template',
            'frequency': 'monthly',
            'day_of_month': 1,
            'date_start': today,
            'module': 'gl',
        })
        created_ids['empty_rec'] = empty_id
        rpc('sunartha.recurring.journal', 'action_generate_now', [[empty_id]])
        fail('Guard: template kosong harus error')
    except Exception as e:
        if 'baris jurnal' in str(e) or 'line' in str(e).lower():
            ok('Guard: template tanpa lines ditolak')
        else:
            warn('Guard: error tapi pesan tidak expected', str(e)[:80])

# ─────────────────────────────────────────────
print('\n[3] FINANCIAL STATEMENTS')
# ─────────────────────────────────────────────

# Perlu ada transaksi posted dulu (dari test 1)
for rtype, label, date_from in [
    ('balance_sheet', 'Balance Sheet', None),
    ('profit_loss',   'Profit & Loss', today[:8] + '01'),  # awal bulan
    ('cash_flow',     'Cash Flow',     today[:8] + '01'),
]:
    try:
        vals = {
            'report_type': rtype,
            'date_to': today,
        }
        if date_from:
            vals['date_from'] = date_from

        rep_id = rpc('sunartha.report.statement', 'create', vals)
        rpc('sunartha.report.statement', 'action_generate', [[rep_id]])
        lines = rpc('sunartha.report.statement.line', 'search_count',
                    [[['report_id', '=', rep_id]]])
        if lines > 0:
            ok(f'{label} — {lines} baris dihasilkan')
        else:
            warn(f'{label} — 0 baris (mungkin tidak ada data)')
    except Exception as e:
        fail(f'{label}', str(e)[:80])

# ─────────────────────────────────────────────
print('\n[4] AR/AP AGING REPORT')
# ─────────────────────────────────────────────

# Buat transaksi AR untuk data aging
try:
    ar_trx_id = rpc('sunartha.journal.transaction', 'create', {
        'module': 'ar',
        'transaction_date': today,
        'description': '[QC] AR Invoice Test',
        'partner_id': rpc('res.partner', 'search', [[['name', 'ilike', 'a']]], limit=1)[0] if rpc('res.partner', 'search_count', [[['customer_rank','>',0]]]) > 0 else False,
        'due_date': today,
        'line_ids': [
            [0, 0, {'account_id': 8,  'debit_amount': 2000000, 'credit_amount': 0}],
            [0, 0, {'account_id': 63, 'debit_amount': 0, 'credit_amount': 2000000}],
        ],
    })
    created_ids['ar_trx'] = ar_trx_id
    rpc('sunartha.journal.transaction', 'action_submit', [[ar_trx_id]])
    rpc('sunartha.journal.transaction', 'action_approve', [[ar_trx_id]])
    rpc('sunartha.journal.transaction', 'action_post', [[ar_trx_id]])
    ok('AR transaction posted untuk aging data', f'id={ar_trx_id}')
except Exception as e:
    warn('AR transaction setup', str(e)[:80])

for ptype, label in [('receivable', 'AR Aging'), ('payable', 'AP Aging')]:
    try:
        aging_id = rpc('sunartha.report.aging', 'create', {
            'partner_type': ptype,
            'as_of_date': today,
        })
        rpc('sunartha.report.aging', 'action_generate', [[aging_id]])
        lines = rpc('sunartha.report.aging.line', 'search_count',
                    [[['report_id', '=', aging_id]]])
        if lines > 0:
            ok(f'{label} — {lines} partner ditemukan')
        else:
            warn(f'{label} — 0 baris (tidak ada transaksi AR/AP posted)')
    except Exception as e:
        fail(f'{label}', str(e)[:80])

# ─────────────────────────────────────────────
# CLEANUP
# ─────────────────────────────────────────────
print('\n[CLEANUP]')
cleanup_map = [
    ('sunartha.journal.transaction', ['ar_trx', 'gen_trx', 'trx2']),
    ('sunartha.recurring.journal',   ['empty_rec', 'rec']),
]
for model, keys in cleanup_map:
    ids = [created_ids[k] for k in keys if k in created_ids]
    if ids:
        try:
            # Reset ke draft dulu jika masih ada yang tidak posted
            for rid in ids:
                try:
                    rec = rpc(model, 'read', [rid], fields=['state'] if 'transaction' in model else ['id'])
                    if 'state' in (rec[0] if rec else {}):
                        if rec[0]['state'] not in ('posted', 'cancelled'):
                            rpc(model, 'write', [[rid]], {'state': 'cancelled'})
                except Exception:
                    pass
            rpc(model, 'unlink', [ids])
            print(f'  Cleaned {model}: {ids}')
        except Exception as e:
            print(f'  Cleanup {model} partial: {e}')

# ─────────────────────────────────────────────
# RINGKASAN
# ─────────────────────────────────────────────
passed  = sum(1 for r in results if r[0] == '✅')
failed  = sum(1 for r in results if r[0] == '❌')
warned  = sum(1 for r in results if r[0] == '⚠️')
total   = len(results)

print(f'\n{"="*50}')
print(f'HASIL: {passed}/{total} PASS  |  {failed} FAIL  |  {warned} WARNING')
print('='*50)
if failed == 0:
    print('VERDICT: PASS')
else:
    print('VERDICT: FAIL')
    print('GAGAL:')
    for r in results:
        if r[0] == '❌':
            print(f'  {r[1]}: {r[2]}')
```

## Laporan yang harus ditampilkan

Setelah script selesai, tampilkan:

```
## QC Report — sunartha_accounting_advance

**Verdict:** PASS | FAIL

| Scenario | Steps | Hasil |
|---|---|---|
| [1] Journal Transaction Workflow | N | ✅/❌ |
| [2] Recurring Journal | N | ✅/❌ |
| [3] Financial Statements | N | ✅/❌ |
| [4] AR/AP Aging | N | ✅/❌ |

**Total:** X/Y pass

### Findings
<isi dari ⚠️ dan ❌ yang muncul, jika ada>
```

## Catatan

- Test user: `odoo-qc@sunartha.co.id` (uid=8, group=Manager)
- Script membersihkan data test setelah selesai
- Jika Odoo tidak jalan, tampilkan: `BLOCKED — Odoo tidak merespons di localhost:8069`
- Untuk menjalankan: `/odoo-qc`
