from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    x_approval_threshold = fields.Monetary(
        string='Threshold Approval (Rp)',
        currency_field='currency_id',
        default=0.0,
        help='Jurnal dengan total >= nilai ini memerlukan persetujuan sebelum bisa diposting. '
             'Isi 0 untuk menonaktifkan approval pada jurnal ini.',
    )
    x_approver_group_id = fields.Many2one(
        'res.groups',
        string='Group Approver',
        help='Group pengguna yang berhak menyetujui jurnal pada journal ini.',
    )
