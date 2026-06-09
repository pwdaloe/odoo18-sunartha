from odoo import api, fields, models


class SunarthaAccountApprovalRequest(models.Model):
    _name = 'sunartha.account.approval.request'
    _description = 'Permintaan Approval Jurnal'
    _order = 'date_requested desc'
    _rec_name = 'name'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Nomor', readonly=True, copy=False, default='New', index=True)
    move_id = fields.Many2one(
        'account.move', string='Jurnal', required=True,
        ondelete='cascade', index=True)
    move_name = fields.Char(related='move_id.name', string='No. Jurnal', store=True)
    move_date = fields.Date(related='move_id.date', string='Tanggal Jurnal', store=True)
    move_amount = fields.Monetary(
        related='move_id.amount_total', string='Total Jurnal',
        currency_field='currency_id')
    currency_id = fields.Many2one(
        related='move_id.currency_id', string='Mata Uang')
    journal_id = fields.Many2one(
        related='move_id.journal_id', string='Journal', store=True)
    requester_id = fields.Many2one(
        'res.users', string='Diajukan Oleh', required=True,
        default=lambda self: self.env.user)
    approver_id = fields.Many2one(
        'res.users', string='Diproses Oleh', readonly=True)
    state = fields.Selection([
        ('pending', 'Menunggu'),
        ('approved', 'Disetujui'),
        ('rejected', 'Ditolak'),
    ], string='Status', default='pending', tracking=True)
    notes = fields.Text(string='Catatan / Alasan Tolak')
    date_requested = fields.Datetime(
        string='Tgl Pengajuan', default=fields.Datetime.now, readonly=True)
    date_responded = fields.Datetime(
        string='Tgl Diproses', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'sunartha.account.approval.request') or 'New'
        return super().create(vals_list)
