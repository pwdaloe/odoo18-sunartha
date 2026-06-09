from odoo import api, fields, models


class SunarthaJournalTransactionLine(models.Model):
    _name = 'sunartha.journal.transaction.line'
    _description = 'Journal Transaction Line'
    _order = 'sequence, id'

    transaction_id = fields.Many2one(
        'sunartha.journal.transaction', string='Transaction',
        ondelete='cascade', index=True, required=True)
    sequence = fields.Integer(default=10)
    account_id = fields.Many2one(
        'account.account', string='Account', required=True,
        domain="[('deprecated', '=', False)]")
    description = fields.Char(string='Description')
    subaccount = fields.Char(string='Subaccount')
    transaction_date = fields.Date(string='Transaction Date')
    debit_amount = fields.Monetary(string='Debit Amount', default=0.0)
    credit_amount = fields.Monetary(string='Credit Amount', default=0.0)
    transaction_description = fields.Char(string='Transaction Description')
    branch_id = fields.Many2one('sunartha.branch', string='Branch')
    currency_id = fields.Many2one(
        'res.currency', related='transaction_id.currency_id', store=True)
    company_id = fields.Many2one(
        'res.company', related='transaction_id.company_id', store=True)

    @api.onchange('debit_amount')
    def _onchange_debit(self):
        if self.debit_amount and self.debit_amount > 0:
            self.credit_amount = 0.0

    @api.onchange('credit_amount')
    def _onchange_credit(self):
        if self.credit_amount and self.credit_amount > 0:
            self.debit_amount = 0.0
