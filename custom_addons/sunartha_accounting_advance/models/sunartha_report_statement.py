from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SunarthaReportStatement(models.TransientModel):
    _name = 'sunartha.report.statement'
    _description = 'Financial Statement Report'
    _rec_name = 'title'

    report_type = fields.Selection([
        ('balance_sheet', 'Balance Sheet'),
        ('profit_loss', 'Profit and Loss'),
        ('cash_flow', 'Cash Flow Statement'),
    ], string='Report Type', required=True, default='balance_sheet')
    title = fields.Char(string='Title', compute='_compute_title')
    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='As of Date', required=True, default=fields.Date.today)
    branch_id = fields.Many2one('sunartha.branch', string='Branch')
    ledger_id = fields.Many2one('sunartha.ledger', string='Ledger')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', readonly=True)
    enable_comparison = fields.Boolean(string='Perbandingan')
    comparison_type = fields.Selection([
        ('prior_month', 'Bulan Sebelumnya'),
        ('prior_year', 'Tahun Sebelumnya'),
        ('custom', 'Custom'),
    ], string='Bandingkan Dengan', default='prior_year')
    comparison_date_from = fields.Date(string='Comparison From')
    comparison_date_to = fields.Date(string='Comparison To')
    line_ids = fields.One2many(
        'sunartha.report.statement.line', 'report_id', string='Report Lines')

    @api.depends('report_type')
    def _compute_title(self):
        labels = {
            'balance_sheet': 'Balance Sheet',
            'profit_loss': 'Profit and Loss',
            'cash_flow': 'Cash Flow Statement',
        }
        for rec in self:
            rec.title = labels.get(rec.report_type, 'Financial Report')

    def _get_comparison_dates(self):
        if not self.enable_comparison:
            return None, None
        if self.comparison_type == 'custom':
            return self.comparison_date_from, self.comparison_date_to
        delta = (relativedelta(months=1) if self.comparison_type == 'prior_month'
                 else relativedelta(years=1))
        cmp_to = self.date_to - delta
        cmp_from = (self.date_from - delta) if self.date_from else None
        return cmp_from, cmp_to

    def _get_line_domain(self, extra=None):
        domain = [
            ('transaction_id.state', '=', 'posted'),
            ('transaction_id.company_id', '=', self.company_id.id),
        ]
        if self.branch_id:
            domain.append(('branch_id', '=', self.branch_id.id))
        if self.ledger_id:
            domain.append(('transaction_id.ledger_id', '=', self.ledger_id.id))
        if extra:
            domain.extend(extra)
        return domain

    def _aggregate_by_account(self, domain):
        lines = self.env['sunartha.journal.transaction.line'].search(domain)
        result = {}
        for line in lines:
            acc = line.account_id
            if not acc:
                continue
            if acc.id not in result:
                result[acc.id] = {
                    'code': acc.code or '',
                    'name': acc.name or '',
                    'debit': 0.0,
                    'credit': 0.0,
                }
            result[acc.id]['debit'] += line.debit_amount
            result[acc.id]['credit'] += line.credit_amount
        return result

    def _build_merged_accounts(self, cur_domain, cmp_domain=None):
        """Merge current + comparison into one dict with debit_prev/credit_prev keys."""
        cur = self._aggregate_by_account(cur_domain)
        prev = self._aggregate_by_account(cmp_domain) if cmp_domain else {}
        merged = {}
        for acc_id, data in cur.items():
            merged[acc_id] = dict(data, debit_prev=0.0, credit_prev=0.0)
        for acc_id, data in prev.items():
            if acc_id in merged:
                merged[acc_id]['debit_prev'] = data['debit']
                merged[acc_id]['credit_prev'] = data['credit']
            else:
                merged[acc_id] = {
                    'code': data['code'],
                    'name': data['name'],
                    'debit': 0.0,
                    'credit': 0.0,
                    'debit_prev': data['debit'],
                    'credit_prev': data['credit'],
                }
        return merged

    def action_generate(self):
        self.ensure_one()
        self.line_ids.unlink()
        if self.report_type == 'balance_sheet':
            self._generate_balance_sheet()
        elif self.report_type == 'profit_loss':
            self._generate_profit_loss()
        else:
            self._generate_cash_flow()
        reload_action = {
            'type': 'ir.actions.act_window',
            'res_model': 'sunartha.report.statement',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
        if not self.line_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Tidak Ada Data'),
                    'message': _('Tidak ada Journal Transaction yang diposting untuk filter yang dipilih. '
                                 'Pastikan ada transaksi dengan status Posted dan akun dengan tipe yang sesuai.'),
                    'type': 'warning',
                    'sticky': True,
                    'next': reload_action,
                },
            }
        return reload_action

    def _make_section_line(self, seq, label):
        return {
            'report_id': self.id,
            'sequence': seq,
            'section': label,
            'account_code': '',
            'account_name': '',
            'debit': 0.0,
            'credit': 0.0,
            'balance': 0.0,
            'balance_prev': 0.0,
            'variance': 0.0,
            'variance_pct': 0.0,
            'is_section': True,
            'is_total': False,
        }

    def _make_total_line(self, seq, label, balance, balance_prev=0.0):
        variance = balance - balance_prev
        variance_pct = round(variance / balance_prev * 100, 1) if abs(balance_prev) > 0.01 else 0.0
        return {
            'report_id': self.id,
            'sequence': seq,
            'section': label,
            'account_code': '',
            'account_name': '',
            'debit': 0.0,
            'credit': 0.0,
            'balance': balance,
            'balance_prev': balance_prev,
            'variance': variance,
            'variance_pct': variance_pct,
            'is_section': False,
            'is_total': True,
        }

    def _make_account_line(self, seq, acc_data, balance, balance_prev=0.0):
        variance = balance - balance_prev
        variance_pct = round(variance / balance_prev * 100, 1) if abs(balance_prev) > 0.01 else 0.0
        return {
            'report_id': self.id,
            'sequence': seq,
            'section': '',
            'account_code': acc_data['code'],
            'account_name': acc_data['name'],
            'debit': acc_data.get('debit', 0.0),
            'credit': acc_data.get('credit', 0.0),
            'balance': balance,
            'balance_prev': balance_prev,
            'variance': variance,
            'variance_pct': variance_pct,
            'is_section': False,
            'is_total': False,
        }

    def _generate_balance_sheet(self):
        _, cmp_to = self._get_comparison_dates()
        sections = [
            ('ASSETS', [
                'asset_receivable', 'asset_cash', 'asset_current',
                'asset_non_current', 'asset_prepayments', 'asset_fixed',
            ], 1),
            ('LIABILITIES', [
                'liability_payable', 'liability_credit_card',
                'liability_current', 'liability_non_current',
            ], -1),
            ('EQUITY', ['equity', 'equity_unaffected'], -1),
        ]
        rows = []
        seq = 10
        for label, types, sign in sections:
            cur_domain = self._get_line_domain([
                ('account_id.account_type', 'in', types),
                ('transaction_id.transaction_date', '<=', self.date_to),
            ])
            cmp_domain = self._get_line_domain([
                ('account_id.account_type', 'in', types),
                ('transaction_id.transaction_date', '<=', cmp_to),
            ]) if cmp_to else None

            accounts = self._build_merged_accounts(cur_domain, cmp_domain)
            if not accounts:
                continue

            rows.append(self._make_section_line(seq, label))
            seq += 1
            section_balance = 0.0
            section_prev = 0.0
            for acc in sorted(accounts.values(), key=lambda x: x['code']):
                bal = sign * (acc['debit'] - acc['credit'])
                prev = sign * (acc.get('debit_prev', 0.0) - acc.get('credit_prev', 0.0))
                section_balance += bal
                section_prev += prev
                rows.append(self._make_account_line(seq, acc, bal, prev))
                seq += 1
            rows.append(self._make_total_line(
                seq, f'Total {label.title()}', section_balance, section_prev))
            seq += 1
        if rows:
            self.env['sunartha.report.statement.line'].create(rows)

    def _generate_profit_loss(self):
        if not self.date_from:
            raise UserError(_('Date From wajib diisi untuk Profit and Loss.'))
        cmp_from, cmp_to = self._get_comparison_dates()
        sections = [
            ('REVENUE', ['income', 'income_other'], -1),
            ('EXPENSES', ['expense', 'expense_depreciation', 'expense_direct_cost'], 1),
        ]
        rows = []
        seq = 10
        section_totals = {}
        section_totals_prev = {}
        for label, types, sign in sections:
            cur_domain = self._get_line_domain([
                ('account_id.account_type', 'in', types),
                ('transaction_id.transaction_date', '>=', self.date_from),
                ('transaction_id.transaction_date', '<=', self.date_to),
            ])
            cmp_domain = self._get_line_domain([
                ('account_id.account_type', 'in', types),
                ('transaction_id.transaction_date', '>=', cmp_from),
                ('transaction_id.transaction_date', '<=', cmp_to),
            ]) if cmp_from and cmp_to else None

            accounts = self._build_merged_accounts(cur_domain, cmp_domain)
            section_total = 0.0
            section_total_prev = 0.0
            if accounts:
                rows.append(self._make_section_line(seq, label))
                seq += 1
                for acc in sorted(accounts.values(), key=lambda x: x['code']):
                    amt = sign * (acc['debit'] - acc['credit'])
                    amt_prev = sign * (acc.get('debit_prev', 0.0) - acc.get('credit_prev', 0.0))
                    section_total += amt
                    section_total_prev += amt_prev
                    rows.append(self._make_account_line(seq, acc, amt, amt_prev))
                    seq += 1
                rows.append(self._make_total_line(
                    seq, f'Total {label.title()}', section_total, section_total_prev))
                seq += 1
            section_totals[label] = section_total
            section_totals_prev[label] = section_total_prev

        net = section_totals.get('REVENUE', 0.0) - section_totals.get('EXPENSES', 0.0)
        net_prev = section_totals_prev.get('REVENUE', 0.0) - section_totals_prev.get('EXPENSES', 0.0)
        rows.append(self._make_total_line(seq, 'NET INCOME / (LOSS)', net, net_prev))
        if rows:
            self.env['sunartha.report.statement.line'].create(rows)

    def _generate_cash_flow(self):
        if not self.date_from:
            raise UserError(_('Date From wajib diisi untuk Cash Flow Statement.'))
        cmp_from, cmp_to = self._get_comparison_dates()
        cash_types = ['asset_cash']
        rows = []
        seq = 10

        def _sum_cash(domain):
            ls = self.env['sunartha.journal.transaction.line'].search(domain)
            return sum(l.debit_amount - l.credit_amount for l in ls)

        opening_balance = _sum_cash(self._get_line_domain([
            ('account_id.account_type', 'in', cash_types),
            ('transaction_id.transaction_date', '<', self.date_from),
        ]))
        opening_prev = _sum_cash(self._get_line_domain([
            ('account_id.account_type', 'in', cash_types),
            ('transaction_id.transaction_date', '<', cmp_from),
        ])) if cmp_from else 0.0

        cur_domain = self._get_line_domain([
            ('account_id.account_type', 'in', cash_types),
            ('transaction_id.transaction_date', '>=', self.date_from),
            ('transaction_id.transaction_date', '<=', self.date_to),
        ])
        cmp_domain = self._get_line_domain([
            ('account_id.account_type', 'in', cash_types),
            ('transaction_id.transaction_date', '>=', cmp_from),
            ('transaction_id.transaction_date', '<=', cmp_to),
        ]) if cmp_from and cmp_to else None

        period_accounts = self._build_merged_accounts(cur_domain, cmp_domain)

        rows.append(self._make_section_line(seq, 'CASH POSITION'))
        seq += 1
        rows.append(self._make_account_line(
            seq,
            {'code': '', 'name': 'Opening Balance', 'debit': 0.0, 'credit': 0.0},
            opening_balance, opening_prev,
        ))
        seq += 1

        inflow = []
        outflow = []
        for acc in sorted(period_accounts.values(), key=lambda x: x['code']):
            net = acc['debit'] - acc['credit']
            net_prev = acc.get('debit_prev', 0.0) - acc.get('credit_prev', 0.0)
            (inflow if net >= 0 else outflow).append((acc, net, net_prev))

        total_inflow = sum(n for _, n, _ in inflow)
        total_inflow_prev = sum(p for _, _, p in inflow)
        total_outflow = sum(n for _, n, _ in outflow)
        total_outflow_prev = sum(p for _, _, p in outflow)

        if inflow:
            rows.append(self._make_section_line(seq, 'CASH INFLOW'))
            seq += 1
            for acc, net, net_prev in inflow:
                rows.append(self._make_account_line(seq, acc, net, net_prev))
                seq += 1
            rows.append(self._make_total_line(seq, 'Total Inflow', total_inflow, total_inflow_prev))
            seq += 1

        if outflow:
            rows.append(self._make_section_line(seq, 'CASH OUTFLOW'))
            seq += 1
            for acc, net, net_prev in outflow:
                rows.append(self._make_account_line(seq, acc, net, net_prev))
                seq += 1
            rows.append(self._make_total_line(seq, 'Total Outflow', total_outflow, total_outflow_prev))
            seq += 1

        closing = opening_balance + total_inflow + total_outflow
        closing_prev = opening_prev + total_inflow_prev + total_outflow_prev
        rows.append(self._make_total_line(seq, 'CLOSING BALANCE', closing, closing_prev))

        if rows:
            self.env['sunartha.report.statement.line'].create(rows)


class SunarthaReportStatementLine(models.TransientModel):
    _name = 'sunartha.report.statement.line'
    _description = 'Financial Statement Report Line'
    _order = 'sequence, id'

    report_id = fields.Many2one(
        'sunartha.report.statement', string='Report',
        ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    section = fields.Char(string='Section')
    account_code = fields.Char(string='Code')
    account_name = fields.Char(string='Account Name')
    debit = fields.Monetary(string='Debit', default=0.0)
    credit = fields.Monetary(string='Credit', default=0.0)
    balance = fields.Monetary(string='Balance', default=0.0)
    balance_prev = fields.Monetary(string='Prior Period', default=0.0)
    variance = fields.Monetary(string='Variance', default=0.0)
    variance_pct = fields.Float(string='Var%', digits=(8, 1), default=0.0)
    currency_id = fields.Many2one(
        'res.currency', related='report_id.currency_id', readonly=True)
    is_section = fields.Boolean(default=False)
    is_total = fields.Boolean(default=False)
