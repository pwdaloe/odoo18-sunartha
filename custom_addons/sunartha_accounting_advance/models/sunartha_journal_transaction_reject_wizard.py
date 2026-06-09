from odoo import fields, models, _
from odoo.exceptions import UserError


class SunarthaJournalTransactionRejectWizard(models.TransientModel):
    _name = 'sunartha.journal.transaction.reject.wizard'
    _description = 'Wizard Penolakan Journal Transaction'

    transaction_ids = fields.Many2many(
        'sunartha.journal.transaction',
        'sunartha_jtrx_reject_rel',
        'wizard_id', 'transaction_id',
        string='Transaksi')
    rejection_reason = fields.Text(string='Alasan Penolakan', required=True)

    def action_confirm_reject(self):
        if not self.rejection_reason:
            raise UserError(_('Alasan penolakan wajib diisi.'))
        for trx in self.transaction_ids:
            trx.write({
                'state': 'rejected',
                'rejection_reason': self.rejection_reason,
            })
            trx.message_post(
                body=_('Transaksi <b>ditolak</b> oleh <b>%s</b>.<br/>Alasan: %s') % (
                    self.env.user.name, self.rejection_reason),
                subtype_xmlid='mail.mt_comment',
            )
        return {'type': 'ir.actions.act_window_close'}
