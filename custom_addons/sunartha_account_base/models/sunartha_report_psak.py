from odoo import api, fields, models, _


class SunarthaReportPsak(models.TransientModel):
    _name = 'sunartha.report.psak'
    _description = 'Wizard Laporan Keuangan PSAK'

    report_type = fields.Selection([
        ('posisi_keuangan', 'Laporan Posisi Keuangan (Neraca)'),
        ('laba_rugi', 'Laporan Laba Rugi Komprehensif'),
        ('arus_kas', 'Laporan Arus Kas'),
    ], string='Jenis Laporan', required=True, default='posisi_keuangan')
    date_from = fields.Date(
        string='Dari Tanggal', required=True,
        default=lambda self: fields.Date.today().replace(day=1, month=1))
    date_to = fields.Date(
        string='Sampai Tanggal', required=True,
        default=fields.Date.today)
    company_id = fields.Many2one(
        'res.company', string='Perusahaan',
        default=lambda self: self.env.company, required=True)

    def _get_account_balances(self, account_types, cumulative=True):
        """Return list of {account, code, name, balance} for given account types."""
        domain = [
            ('account_id.account_type', 'in', account_types),
            ('parent_state', '=', 'posted'),
            ('company_id', '=', self.company_id.id),
        ]
        if not cumulative:
            domain.append(('date', '>=', self.date_from))
        domain.append(('date', '<=', self.date_to))

        result = self.env['account.move.line'].read_group(
            domain,
            ['account_id', 'balance:sum'],
            ['account_id'],
            orderby='account_id asc',
        )
        lines = []
        for r in result:
            account = self.env['account.account'].browse(r['account_id'][0])
            lines.append({
                'code': account.code,
                'name': account.name,
                'balance': r['balance'],
            })
        return lines

    def _get_balance_sheet_data(self):
        """Laporan Posisi Keuangan sesuai PSAK 1."""
        aset_lancar = self._get_account_balances(
            ['asset_cash', 'asset_receivable', 'asset_current', 'asset_prepayments'])
        aset_tidak_lancar = self._get_account_balances(
            ['asset_non_current', 'asset_fixed'])

        liab_jangka_pendek = self._get_account_balances(
            ['liability_payable', 'liability_credit_card', 'liability_current'])
        liab_jangka_panjang = self._get_account_balances(
            ['liability_non_current'])

        ekuitas = self._get_account_balances(['equity', 'equity_unaffected'])

        # Liabilitas & ekuitas: balance di DB adalah negatif (credit normal)
        for line in liab_jangka_pendek + liab_jangka_panjang + ekuitas:
            line['balance'] = -line['balance']

        return {
            'aset_lancar': aset_lancar,
            'total_aset_lancar': sum(l['balance'] for l in aset_lancar),
            'aset_tidak_lancar': aset_tidak_lancar,
            'total_aset_tidak_lancar': sum(l['balance'] for l in aset_tidak_lancar),
            'total_aset': sum(l['balance'] for l in aset_lancar + aset_tidak_lancar),
            'liab_jangka_pendek': liab_jangka_pendek,
            'total_liab_jangka_pendek': sum(l['balance'] for l in liab_jangka_pendek),
            'liab_jangka_panjang': liab_jangka_panjang,
            'total_liab_jangka_panjang': sum(l['balance'] for l in liab_jangka_panjang),
            'total_liabilitas': sum(l['balance'] for l in liab_jangka_pendek + liab_jangka_panjang),
            'ekuitas': ekuitas,
            'total_ekuitas': sum(l['balance'] for l in ekuitas),
        }

    def _get_pl_data(self):
        """Laporan Laba Rugi Komprehensif sesuai PSAK 1 — by fungsi."""
        pendapatan = self._get_account_balances(
            ['income', 'income_other'], cumulative=False)
        beban_pokok = self._get_account_balances(
            ['expense_direct_cost'], cumulative=False)
        beban_operasional = self._get_account_balances(
            ['expense'], cumulative=False)
        beban_penyusutan = self._get_account_balances(
            ['expense_depreciation'], cumulative=False)

        # Pendapatan: credit normal → negate
        for line in pendapatan:
            line['balance'] = -line['balance']

        total_pendapatan = sum(l['balance'] for l in pendapatan)
        total_beban_pokok = sum(l['balance'] for l in beban_pokok)
        laba_kotor = total_pendapatan - total_beban_pokok
        total_beban_operasional = sum(l['balance'] for l in beban_operasional)
        total_beban_penyusutan = sum(l['balance'] for l in beban_penyusutan)
        laba_operasional = laba_kotor - total_beban_operasional - total_beban_penyusutan
        return {
            'pendapatan': pendapatan,
            'total_pendapatan': total_pendapatan,
            'beban_pokok': beban_pokok,
            'total_beban_pokok': total_beban_pokok,
            'laba_kotor': laba_kotor,
            'beban_operasional': beban_operasional,
            'total_beban_operasional': total_beban_operasional,
            'beban_penyusutan': beban_penyusutan,
            'total_beban_penyusutan': total_beban_penyusutan,
            'laba_operasional': laba_operasional,
        }

    def _get_cashflow_data(self):
        """Laporan Arus Kas PSAK 2 — Metode Tidak Langsung."""
        pl_data = self._get_pl_data()
        laba_bersih = pl_data['laba_operasional']

        # Penyesuaian item non-kas: tambahkan kembali penyusutan
        penyusutan = pl_data['total_beban_penyusutan']

        # Perubahan modal kerja
        def _delta(account_types, sign=1):
            opening_domain = [
                ('account_id.account_type', 'in', account_types),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', self.company_id.id),
                ('date', '<', self.date_from),
            ]
            closing_domain = opening_domain[:-1] + [('date', '<=', self.date_to)]
            opening = sum(
                self.env['account.move.line'].search(opening_domain).mapped('balance'))
            closing = sum(
                self.env['account.move.line'].search(closing_domain).mapped('balance'))
            return (closing - opening) * sign

        delta_piutang = _delta(['asset_receivable'], sign=-1)
        delta_persediaan = _delta(['asset_current'], sign=-1)
        delta_hutang_usaha = _delta(['liability_payable'], sign=1)

        kas_operasi = laba_bersih + penyusutan + delta_piutang + delta_persediaan + delta_hutang_usaha

        # Aset tetap sebagai proxy investasi
        delta_aset_tetap = _delta(['asset_fixed'], sign=-1)
        kas_investasi = -delta_aset_tetap

        return {
            'laba_bersih': laba_bersih,
            'penyusutan': penyusutan,
            'delta_piutang': delta_piutang,
            'delta_persediaan': delta_persediaan,
            'delta_hutang_usaha': delta_hutang_usaha,
            'kas_operasi': kas_operasi,
            'kas_investasi': kas_investasi,
            'kas_pendanaan': 0.0,
            'kenaikan_penurunan_kas': kas_operasi + kas_investasi,
        }

    def action_print_report(self):
        self.ensure_one()
        report_map = {
            'posisi_keuangan': 'sunartha_account_base.action_report_posisi_keuangan',
            'laba_rugi': 'sunartha_account_base.action_report_laba_rugi',
            'arus_kas': 'sunartha_account_base.action_report_arus_kas',
        }
        return self.env.ref(report_map[self.report_type]).report_action(self)

    @api.onchange('report_type')
    def _onchange_report_type(self):
        if self.report_type in ('laba_rugi', 'arus_kas'):
            pass  # date_from sudah terisi default
