from odoo import fields, models, _
from odoo.exceptions import UserError


class SunarthaApprovalRejectWizard(models.TransientModel):
    _name = 'sunartha.account.approval.reject.wizard'
    _description = 'Wizard Penolakan Jurnal'

    move_ids = fields.Many2many('account.move', string='Jurnal')
    reject_reason = fields.Text(string='Alasan Penolakan', required=True)

    def action_reject(self):
        moves = self.move_ids
        if not moves:
            moves = self.env['account.move'].browse(
                self._context.get('active_ids', []))
        if not moves:
            raise UserError(_('Tidak ada jurnal yang dipilih.'))

        for move in moves:
            if move.x_approval_state != 'waiting':
                raise UserError(
                    _('Jurnal "%s" tidak dalam status menunggu persetujuan.') % move.name)
            move.write({
                'x_approval_state': 'rejected',
                'x_approval_notes': self.reject_reason,
            })
            move.x_approval_request_ids.filtered(
                lambda r: r.state == 'pending'
            ).write({
                'state': 'rejected',
                'approver_id': self.env.user.id,
                'date_responded': fields.Datetime.now(),
                'notes': self.reject_reason,
            })
            move.message_post(
                body=_('Jurnal <b>ditolak</b> oleh <b>%s</b>.<br/>'
                       'Alasan: %s') % (self.env.user.name, self.reject_reason),
                subtype_xmlid='mail.mt_comment',
            )
        return {'type': 'ir.actions.act_window_close'}
