from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SunarthaAccountingPeriod(models.Model):
    _name = 'sunartha.accounting.period'
    _description = 'Accounting Period'
    _order = 'date_start desc'
    _rec_name = 'name'

    name = fields.Char(string='Period', required=True)
    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)
    state = fields.Selection([
        ('open', 'Open'),
        ('locked', 'Locked'),
    ], string='Status', default='open')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True)
    locked_by = fields.Many2one('res.users', string='Locked By', readonly=True, copy=False)
    locked_at = fields.Datetime(string='Locked At', readonly=True, copy=False)
    note = fields.Text(string='Notes')

    _sql_constraints = [
        ('unique_period_company', 'unique(date_start, company_id)',
         'Periode dengan tanggal mulai yang sama sudah ada untuk company ini.'),
    ]

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start > rec.date_end:
                raise UserError(_('Tanggal mulai harus sebelum tanggal akhir.'))

    def action_lock(self):
        self._check_manager()
        for rec in self:
            if rec.state == 'locked':
                continue
            rec.write({
                'state': 'locked',
                'locked_by': self.env.user.id,
                'locked_at': fields.Datetime.now(),
            })

    def action_unlock(self):
        self._check_manager()
        for rec in self:
            if rec.state == 'open':
                continue
            rec.write({
                'state': 'open',
                'locked_by': False,
                'locked_at': False,
            })

    def _check_manager(self):
        manager_group = self.env.ref(
            'sunartha_accounting_advance.group_accounting_advance_manager',
            raise_if_not_found=False)
        if manager_group and manager_group not in self.env.user.groups_id:
            raise UserError(_('Hanya Manager yang bisa mengunci/membuka periode.'))

    @api.model
    def get_locked_period_for_date(self, date, company_id=None):
        """Return locked period record if date falls in a locked period, else empty recordset."""
        company_id = company_id or self.env.company.id
        return self.search([
            ('date_start', '<=', date),
            ('date_end', '>=', date),
            ('company_id', '=', company_id),
            ('state', '=', 'locked'),
        ], limit=1)
