import calendar
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SunarthaRecurringJournal(models.Model):
    _name = 'sunartha.recurring.journal'
    _description = 'Recurring Journal Template'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ], string='Frequency', required=True, default='monthly')
    day_of_month = fields.Integer(
        string='Day of Month', default=1,
        help='Tanggal generate per periode. Otomatis menyesuaikan akhir bulan.')
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date')
    next_run_date = fields.Date(string='Next Run Date', default=fields.Date.today)
    state = fields.Selection([
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('ended', 'Ended'),
    ], string='Status', default='active')
    module = fields.Selection([
        ('ar', 'AR - Invoice'),
        ('ap', 'AP - Bills'),
        ('gl', 'GL - Journal Entry'),
    ], string='Module', required=True, default='gl')
    branch_id = fields.Many2one('sunartha.branch', string='Branch')
    ledger_id = fields.Many2one('sunartha.ledger', string='Ledger')
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True)
    description = fields.Text(string='Description Template')
    line_ids = fields.One2many(
        'sunartha.recurring.journal.line', 'recurring_id', string='Lines')
    generated_ids = fields.One2many(
        'sunartha.journal.transaction', 'recurring_id', string='Generated Transactions')
    generated_count = fields.Integer(
        string='Generated', compute='_compute_generated_count')

    @api.depends('generated_ids')
    def _compute_generated_count(self):
        for rec in self:
            rec.generated_count = len(rec.generated_ids)

    def _next_date_after(self, from_date):
        if self.frequency == 'monthly':
            d = from_date + relativedelta(months=1)
        elif self.frequency == 'quarterly':
            d = from_date + relativedelta(months=3)
        else:
            d = from_date + relativedelta(years=1)
        max_day = calendar.monthrange(d.year, d.month)[1]
        return d.replace(day=min(self.day_of_month, max_day))

    def action_generate_now(self):
        self.ensure_one()
        if self.state != 'active':
            raise UserError(_('Hanya template Active yang bisa digenerate.'))
        trx = self._do_generate(fields.Date.today())
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sunartha.journal.transaction',
            'res_id': trx.id,
            'view_mode': 'form',
        }

    def _do_generate(self, run_date):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('Template "%s" tidak memiliki baris jurnal.') % self.name)
        lines_vals = [(0, 0, {
            'account_id': l.account_id.id,
            'description': l.description or self.name,
            'debit_amount': l.debit_amount,
            'credit_amount': l.credit_amount,
            'branch_id': (l.branch_id.id if l.branch_id else
                          (self.branch_id.id if self.branch_id else False)),
        }) for l in self.line_ids]

        trx = self.env['sunartha.journal.transaction'].create({
            'module': self.module,
            'transaction_date': run_date,
            'branch_id': self.branch_id.id if self.branch_id else False,
            'ledger_id': self.ledger_id.id if self.ledger_id else False,
            'currency_id': self.currency_id.id,
            'description': self.description or self.name,
            'company_id': self.company_id.id,
            'recurring_id': self.id,
            'line_ids': lines_vals,
        })
        self.next_run_date = self._next_date_after(run_date)
        if self.date_end and self.next_run_date > self.date_end:
            self.state = 'ended'
        return trx

    def action_view_generated(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generated Transactions'),
            'res_model': 'sunartha.journal.transaction',
            'view_mode': 'list,form',
            'domain': [('recurring_id', '=', self.id)],
        }

    @api.model
    def _cron_generate_recurring(self):
        today = fields.Date.today()
        templates = self.search([
            ('state', '=', 'active'),
            ('next_run_date', '<=', today),
        ])
        for tmpl in templates:
            try:
                tmpl._do_generate(today)
            except Exception:
                pass


class SunarthaRecurringJournalLine(models.Model):
    _name = 'sunartha.recurring.journal.line'
    _description = 'Recurring Journal Line'
    _order = 'sequence, id'

    recurring_id = fields.Many2one(
        'sunartha.recurring.journal', ondelete='cascade', index=True)
    sequence = fields.Integer(default=10)
    account_id = fields.Many2one('account.account', string='Account', required=True)
    description = fields.Char(string='Description')
    debit_amount = fields.Monetary(string='Debit', default=0.0)
    credit_amount = fields.Monetary(string='Credit', default=0.0)
    branch_id = fields.Many2one('sunartha.branch', string='Branch')
    currency_id = fields.Many2one(
        'res.currency', related='recurring_id.currency_id', readonly=True)
