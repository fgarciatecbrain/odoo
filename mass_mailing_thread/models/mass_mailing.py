'''
Created on Jul 3, 2017

@author: fgarcia
'''
from openerp import api, fields, models, _, sql_db
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from openerp.exceptions import UserError

import logging
import threading
_logger = logging.getLogger(__name__)

class mass_mailing(models.Model):

    _name = 'mail.mass_mailing'
    _inherit = 'mail.mass_mailing'
  
    _threads_size = 4
    _thread_batch_size = 100
                

    
    @api.model
    def _process_mass_mailing_queue(self):
        """
            Redefinimos el proceso de cron de mass mailing 
            
            Este cron solo verifica si se han procesado todos los emails a enviar
            pero no envia ninguno pues el proceso se hace en otro cron 
            
        """
        now = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        mass_mailing_ids = self.search([('state', 'in', ('in_queue', 'sending')), '|', ('schedule_date', '<', now), ('schedule_date', '=', False)])

        for mass_mailing_record in mass_mailing_ids:

            if len(mass_mailing_record.get_remaining_recipients(mass_mailing_record)) > 0:
                if mass_mailing_record.state == 'in_queue':
                    mass_mailing_record.write({'state': 'sending'})

    

    @api.model
    def _ProcessMailThread(self, idthread, composer_values, rest_ids):

        new_cr = sql_db.db_connect(self.env.cr.dbname).cursor()
        uid, context = self.env.uid, self.env.context
        with api.Environment.manage():
            self.env = api.Environment(new_cr, uid, context)

            try:

                _logger.info('Begin Thread %s Send email %s' % (idthread, len(rest_ids)))
                
                composer = self.env['mail.compose.message'].with_context(active_ids=rest_ids).create(composer_values)
                composer.with_context(active_ids=rest_ids).send_mail(auto_commit=True)
                
                _logger.info('End Thread %s Send email %s' % (idthread, len(rest_ids)))
                    
            
            finally:
                new_cr.close()
    

    
    @api.model
    def _process_mass_mailing_queue_thread(self):
        
        threads_size = int(self.env['ir.config_parameter'].sudo().get_param('mail.threads_size')) or self._threads_size
        thread_batch_size = int(self.env['ir.config_parameter'].sudo().get_param('mail.thread_batch_size')) or self._thread_batch_size
        
        now = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        mass_mailing_ids = self.search([('state', '=',  'sending'), '|', ('schedule_date', '<', now), ('schedule_date', '=', False)])
        author_id = self.env.user.partner_id.id
        _logger.info('Begin Mass Mailing ')
        for mailing in mass_mailing_ids:
            
            remain_res_ids = mailing.get_remaining_recipients(mailing)
            if remain_res_ids:
                
                composer_values = {
                    'author_id': author_id,
                    'attachment_ids': [(4, attachment.id) for attachment in mailing.attachment_ids],
                    'body': mailing.convert_links()[mailing.id],
                    'subject': mailing.name,
                    'model': mailing.mailing_model,
                    'email_from': mailing.email_from,
                    'record_name': False,
                    'composition_mode': 'mass_mail',
                    'mass_mailing_id': mailing.id,
                    'mailing_list_ids': [(4, l.id) for l in mailing.contact_list_ids],
                    'no_auto_thread': mailing.reply_to_mode != 'thread',
                }
                if mailing.reply_to_mode == 'email':
                    composer_values['reply_to'] = mailing.reply_to
                
                mailing.body_html = self.env['mail.template']._replace_local_links(mailing.body_html)
                
                res_ids = remain_res_ids[0:threads_size * thread_batch_size]
                if len(res_ids) < threads_size:
                    threads_size = 1
                
                batch_size = len(res_ids) / threads_size;
                sliced_res_ids = [res_ids[i:i + batch_size] for i in range(0, len(res_ids), batch_size)]
                list_threads = []
                for thread_id in range(0,len(sliced_res_ids)):
                    t = threading.Thread(name=thread_id, target=self._ProcessMailThread, args=(thread_id, composer_values, sliced_res_ids[thread_id]))
                    list_threads.append(t)
                    t.start()
            
                # esperar que acaben todos los threads
                for t in list_threads:
                    t.join()

                if len(mailing.get_remaining_recipients(mailing)) == 0:
                    mailing.state = 'done'
            else:
                mailing.state = 'done'
        _logger.info('End Mass Mailing ')
    


    