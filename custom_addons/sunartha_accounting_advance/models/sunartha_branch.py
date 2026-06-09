from odoo import api, fields, models


class SunarBranch(models.Model):
    _name = 'sunartha.branch'
    _description = 'Branch'
    _order = 'code'

    code = fields.Char(string='Kode', required=True, index=True)
    name = fields.Char(string='Nama', required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.code} - {rec.name}" if rec.code and rec.name else rec.name or rec.code or ''

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Kode branch harus unik per perusahaan.'),
    ]
