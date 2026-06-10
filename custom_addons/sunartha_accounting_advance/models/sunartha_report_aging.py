from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SunarthaReportAging(models.TransientModel):
    _name = 'sunartha.report.aging'
    _description = 'AR/AP Aging Report'

    partner_type = fields.Selection([
        ('receivable', 'Accounts Receivable (AR)'),
        ('payable', 'Accounts Payable (AP)'),
    ], string='Type', required=True, default='receivable')
    as_of_date = fields.Date(
        string='As of Date', required=True, default=fields.Date.today)
    branch_id = fields.Many2one('sunartha.branch', string='Branch')
    ledger_id = fields.Many2one('sunartha.ledger', string='Ledger')
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', readonly=True)
    line_ids = fields.One2many(
        'sunartha.report.aging.line', 'report_id', string='Lines')

    def action_generate(self):
        self.ensure_one()
        self.line_ids.unlink()

        account_type = ('asset_receivable' if self.partner_type == 'receivable'
                        else 'liability_payable')

        domain = [
            ('transaction_id.state', '=', 'posted'),
            ('transaction_id.company_id', '=', self.company_id.id),
            ('account_id.account_type', '=', account_type),
            ('transaction_id.transaction_date', '<=', self.as_of_date),
        ]
        if self.branch_id:
            domain.append(('branch_id', '=', self.branch_id.id))
        if self.ledger_id:
            domain.append(('transaction_id.ledger_id', '=', self.ledger_id.id))

        lines = self.env['sunartha.journal.transaction.line'].search(domain)

        partner_data = {}
        for line in lines:
            partner = line.transaction_id.partner_id
            partner_key = partner.id if partner else 0

            if partner_key not in partner_data:
                partner_data[partner_key] = {
                    'partner_id': partner.id if partner else False,
                    'partner_name': partner.name if partner else '(No Partner)',
                    'account_id': line.account_id.id if line.account_id else False,
                    'account_name': line.account_id.name if line.account_id else '',
                    'current': 0.0,
                    'b1_30': 0.0,
                    'b31_60': 0.0,
                    'b61_90': 0.0,
                    'b91_120': 0.0,
                    'over_120': 0.0,
                }

            d = partner_data[partner_key]
            # Use due_date if set, otherwise transaction_date
            ref_date = line.transaction_id.due_date or line.transaction_id.transaction_date
            days = (self.as_of_date - ref_date).days

            # AR: debit - credit = amount owed to us
            # AP: credit - debit = amount we owe
            net = (line.debit_amount - line.credit_amount
                   if self.partner_type == 'receivable'
                   else line.credit_amount - line.debit_amount)

            if days <= 0:
                d['current'] += net
            elif days <= 30:
                d['b1_30'] += net
            elif days <= 60:
                d['b31_60'] += net
            elif days <= 90:
                d['b61_90'] += net
            elif days <= 120:
                d['b91_120'] += net
            else:
                d['over_120'] += net

        rows = []
        for d in sorted(partner_data.values(), key=lambda x: x['partner_name']):
            total = (d['current'] + d['b1_30'] + d['b31_60'] +
                     d['b61_90'] + d['b91_120'] + d['over_120'])
            if abs(total) < 0.01:
                continue
            rows.append({
                'report_id': self.id,
                'partner_id': d['partner_id'],
                'partner_name': d['partner_name'],
                'account_id': d['account_id'],
                'account_name': d['account_name'],
                'bucket_current': d['current'],
                'bucket_1_30': d['b1_30'],
                'bucket_31_60': d['b31_60'],
                'bucket_61_90': d['b61_90'],
                'bucket_91_120': d['b91_120'],
                'bucket_over_120': d['over_120'],
                'total': total,
            })

        if rows:
            self.env['sunartha.report.aging.line'].create(rows)

        reload_action = {
            'type': 'ir.actions.act_window',
            'res_model': 'sunartha.report.aging',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
        if not rows:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Tidak Ada Data'),
                    'message': _('Tidak ada Journal Transaction yang diposting dengan akun AR/AP '
                                 'untuk filter yang dipilih.'),
                    'type': 'warning',
                    'sticky': True,
                    'next': reload_action,
                },
            }
        return reload_action


class SunarthaReportAgingLine(models.TransientModel):
    _name = 'sunartha.report.aging.line'
    _description = 'AR/AP Aging Report Line'
    _order = 'partner_name'

    report_id = fields.Many2one(
        'sunartha.report.aging', ondelete='cascade', index=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    partner_name = fields.Char(string='Partner Name')
    account_id = fields.Many2one('account.account', string='Account')
    account_name = fields.Char(string='Account Name')
    bucket_current = fields.Monetary(string='Current', default=0.0)
    bucket_1_30 = fields.Monetary(string='1-30 Days', default=0.0)
    bucket_31_60 = fields.Monetary(string='31-60 Days', default=0.0)
    bucket_61_90 = fields.Monetary(string='61-90 Days', default=0.0)
    bucket_91_120 = fields.Monetary(string='91-120 Days', default=0.0)
    bucket_over_120 = fields.Monetary(string='>120 Days', default=0.0)
    total = fields.Monetary(string='Total', default=0.0)
    currency_id = fields.Many2one(
        'res.currency', related='report_id.currency_id', readonly=True)
