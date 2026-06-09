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

    def action_generate(self):
        self.ensure_one()
        self.line_ids.unlink()
        if self.report_type == 'balance_sheet':
            self._generate_balance_sheet()
        elif self.report_type == 'profit_loss':
            self._generate_profit_loss()
        else:
            self._generate_cash_flow()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sunartha.report.statement',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

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
            'is_section': True,
            'is_total': False,
        }

    def _make_total_line(self, seq, label, balance):
        return {
            'report_id': self.id,
            'sequence': seq,
            'section': label,
            'account_code': '',
            'account_name': '',
            'debit': 0.0,
            'credit': 0.0,
            'balance': balance,
            'is_section': False,
            'is_total': True,
        }

    def _make_account_line(self, seq, acc_data, balance):
        return {
            'report_id': self.id,
            'sequence': seq,
            'section': '',
            'account_code': acc_data['code'],
            'account_name': acc_data['name'],
            'debit': acc_data['debit'],
            'credit': acc_data['credit'],
            'balance': balance,
            'is_section': False,
            'is_total': False,
        }

    def _generate_balance_sheet(self):
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
            domain = self._get_line_domain([
                ('account_id.account_type', 'in', types),
                ('transaction_id.transaction_date', '<=', self.date_to),
            ])
            accounts = self._aggregate_by_account(domain)
            if not accounts:
                continue
            rows.append(self._make_section_line(seq, label))
            seq += 1
            section_balance = 0.0
            for acc in sorted(accounts.values(), key=lambda x: x['code']):
                bal = sign * (acc['debit'] - acc['credit'])
                section_balance += bal
                rows.append(self._make_account_line(seq, acc, bal))
                seq += 1
            rows.append(self._make_total_line(seq, f'Total {label.title()}', section_balance))
            seq += 1
        if rows:
            self.env['sunartha.report.statement.line'].create(rows)

    def _generate_profit_loss(self):
        if not self.date_from:
            raise UserError(_('Date From wajib diisi untuk Profit and Loss.'))
        sections = [
            ('REVENUE', ['income', 'income_other'], -1),
            ('EXPENSES', ['expense', 'expense_depreciation', 'expense_direct_cost'], 1),
        ]
        rows = []
        seq = 10
        section_totals = {}
        for label, types, sign in sections:
            domain = self._get_line_domain([
                ('account_id.account_type', 'in', types),
                ('transaction_id.transaction_date', '>=', self.date_from),
                ('transaction_id.transaction_date', '<=', self.date_to),
            ])
            accounts = self._aggregate_by_account(domain)
            section_total = 0.0
            if accounts:
                rows.append(self._make_section_line(seq, label))
                seq += 1
                for acc in sorted(accounts.values(), key=lambda x: x['code']):
                    amt = sign * (acc['debit'] - acc['credit'])
                    section_total += amt
                    rows.append(self._make_account_line(seq, acc, amt))
                    seq += 1
                rows.append(self._make_total_line(seq, f'Total {label.title()}', section_total))
                seq += 1
            section_totals[label] = section_total
        net = section_totals.get('REVENUE', 0.0) - section_totals.get('EXPENSES', 0.0)
        rows.append(self._make_total_line(seq, 'NET INCOME / (LOSS)', net))
        if rows:
            self.env['sunartha.report.statement.line'].create(rows)

    def _generate_cash_flow(self):
        if not self.date_from:
            raise UserError(_('Date From wajib diisi untuk Cash Flow Statement.'))
        cash_types = ['asset_cash']
        rows = []
        seq = 10

        opening_domain = self._get_line_domain([
            ('account_id.account_type', 'in', cash_types),
            ('transaction_id.transaction_date', '<', self.date_from),
        ])
        opening_lines = self.env['sunartha.journal.transaction.line'].search(opening_domain)
        opening_balance = (
            sum(opening_lines.mapped('debit_amount')) -
            sum(opening_lines.mapped('credit_amount'))
        )

        period_domain = self._get_line_domain([
            ('account_id.account_type', 'in', cash_types),
            ('transaction_id.transaction_date', '>=', self.date_from),
            ('transaction_id.transaction_date', '<=', self.date_to),
        ])
        period_accounts = self._aggregate_by_account(period_domain)

        rows.append(self._make_section_line(seq, 'CASH POSITION'))
        seq += 1
        rows.append({
            'report_id': self.id,
            'sequence': seq,
            'section': '',
            'account_code': '',
            'account_name': 'Opening Balance',
            'debit': 0.0,
            'credit': 0.0,
            'balance': opening_balance,
            'is_section': False,
            'is_total': False,
        })
        seq += 1

        inflow = []
        outflow = []
        for acc in sorted(period_accounts.values(), key=lambda x: x['code']):
            net = acc['debit'] - acc['credit']
            (inflow if net >= 0 else outflow).append((acc, net))

        total_inflow = sum(n for _, n in inflow)
        total_outflow = sum(n for _, n in outflow)

        if inflow:
            rows.append(self._make_section_line(seq, 'CASH INFLOW'))
            seq += 1
            for acc, net in inflow:
                rows.append(self._make_account_line(seq, acc, net))
                seq += 1
            rows.append(self._make_total_line(seq, 'Total Inflow', total_inflow))
            seq += 1

        if outflow:
            rows.append(self._make_section_line(seq, 'CASH OUTFLOW'))
            seq += 1
            for acc, net in outflow:
                rows.append(self._make_account_line(seq, acc, net))
                seq += 1
            rows.append(self._make_total_line(seq, 'Total Outflow', total_outflow))
            seq += 1

        closing = opening_balance + total_inflow + total_outflow
        rows.append(self._make_total_line(seq, 'CLOSING BALANCE', closing))

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
    currency_id = fields.Many2one(
        'res.currency', related='report_id.currency_id', readonly=True)
    is_section = fields.Boolean(default=False)
    is_total = fields.Boolean(default=False)
