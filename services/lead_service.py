from .base_service import BaseService
from .contact_service import ContactService
from .company_service import CompanyService
import copy

class LeadService(BaseService):
    def __init__(self, lead_fields, contact_fields, company_fields, city):
        super().__init__(lead_fields, city)
        self.contact_fields = contact_fields
        self.company_fields = company_fields

    def get_leads(self, lead):
        try:
            self.__fill_lead_info(lead)
        except Exception as ex:
            self.logs_file.write_log_file(f'Ошибка заполнения полей сделки: {ex}')
            return self.fields
        
        try:
            self._process_lead()
            return self.fields
        except Exception as ex:
            self.logs_file.write_log_file(f'Ошибка преобразования полей сделки: {ex}')
            return self.fields

    def _process_lead(self):
        super()._process_common_fields()
        self.fields['created_at'] = self.service.read_timestamp_date(self.fields['created_at'])
        self.fields['created_by'] = self.user_service.get_user_name(self.fields['created_by'])
        self.fields['updated_at'] = self.service.read_timestamp_date(self.fields['updated_at'])
        self.fields['updated_by'] = self.user_service.get_user_name(self.fields['updated_by'])
        self.fields['closed_at'] = self.service.read_timestamp_date(self.fields['closed_at'])
        self.fields['tags'] = ', '.join(tag.get('name', '') for tag in self.fields['tags'])

    def __fill_lead_info(self, lead):
        lead_embedded = lead.get('_embedded', {})
        self.fields['id'] = lead.get('id', 0)
        self.fields['name'] = lead.get('name', '')
        self.fields['price'] = lead.get('price', 0)
        self.fields['responsible_user'] = lead.get('responsible_user_id', 0)
        self.fields['created_at'] = lead.get('created_at', '')
        self.fields['created_by'] = lead.get('created_by', 0)
        self.fields['updated_at'] = lead.get('updated_at', '')
        self.fields['updated_by'] = lead.get('updated_by', 0)
        self.fields['closed_at'] = lead.get('closed_at', '')
        self.fields['tags'] = lead_embedded.get('tags', [])
        self.fields['pipeline'] = lead.get('pipeline_id', 0)
        self.fields['status_id'] = lead.get('status_id', '')
        self.fields['contacts'] = [contact.get('id', 0) for contact in lead_embedded.get('contacts', [])]
        self.fields['companies'] = [company.get('id', 0) for company in lead_embedded.get('companies', [])]
        try:
            self._fill_custom_fields(lead.get('custom_fields_values', []))
        except Exception as ex:
            self.logs_file.write_log_file(f'Ошибка заполнения пользовательских полей сделки: {ex}')
        
        try:
            self.__fill_pipelines()
        except Exception as ex:
            self.logs_file.write_log_file(f'Ошибка заполнения воронки и этапа сделки: {ex}')

        contacts = []
        for contact_id in self.fields['contacts']:
            contact_service = ContactService(copy.deepcopy(self.contact_fields), copy.deepcopy(self.company_fields), self.city)
            try:
                contacts.append(contact_service.get_contact(contact_id))
            except Exception as ex:
                self.logs_file.write_log_file(f'Ошибка заполнения полей контакта сделки: {ex}')
        
        if len(contacts) > 0:
            self.fields['contacts'] = contacts
        else:
            contact_service = ContactService(copy.deepcopy(self.contact_fields), copy.deepcopy(self.company_fields), self.city)
            try:
                contact_service._process_common_fields()
            except Exception as ex:
                self.logs_file.write_log_file(f'Ошибка преобразования полей контакта сделки: {ex}')
            self.fields['contacts'] = [contact_service.fields]

        companies = []
        for company_id in self.fields['companies']:
            company_service = CompanyService(copy.deepcopy(self.company_fields), self.city)
            try:
                companies.append(company_service.get_company(company_id))
            except Exception as ex:
                self.logs_file.write_log_file(f'Ошибка заполнения полей камании сделки: {ex}')
        
        if len(companies) > 0:
            self.fields['companies'] = companies
        else:
            company_service = CompanyService(copy.deepcopy(self.company_fields), self.city)
            try:
                company_service._process_common_fields()
            except Exception as ex:
                self.logs_file.write_log_file(f'Ошибка преобразования полей кампании сделки: {ex}')
            self.fields['companies'] = [company_service.fields]

    def __fill_pipelines(self):
        self.logs_file.write_log_file('Начали заполнение воронки и этапа сделки')
        status_id = self.fields['status_id']
        pipeline_id = self.fields['pipeline']

        if not status_id and not pipeline_id:
            self.fields['etap_sdelki'] = ''
            self.fields['pipeline'] = ''
            self.logs_file.write_log_file('Закончили заполнение воронки и этапа сделки')
            return
        elif not pipeline_id:
            self.fields['etap_sdelki'] = ''
            self.fields['pipeline'] = ''
            self.logs_file.write_log_file('Закончили заполнение воронки и этапа сделки')
            return
        elif not status_id:
            try:
                status_code, response = self.http_service.execute_request(f'/api/v4/leads/pipelines/{pipeline_id}')
                if status_code == 200:
                    self.fields['pipeline'] = response.get('name', '')
                    self.fields['etap_sdelki'] = ''
                    self.logs_file.write_log_file('Закончили заполнение воронки и этапа сделки')
                    return
                self.logs_file.write_log_file('Закончили заполнение воронки и этапа сделки')
                return
            except Exception as ex:
                self.logs_file.write_log_file(f'Ошибка запроса "/api/v4/leads/pipelines/{pipeline_id}": {ex}')
                return

        try:
            status_code, response = self.http_service.execute_request(f'/api/v4/leads/pipelines/{pipeline_id}')
            if status_code == 200:
                self.fields['pipeline'] = response.get('name', '')
                self.logs_file.write_log_file('Закончили заполнение воронки')
        except Exception as ex:
            self.logs_file.write_log_file(f'Ошибка запроса "/api/v4/leads/pipelines/{pipeline_id}": {ex}')

        try:
            status_code, response = self.http_service.execute_request(f'/api/v4/leads/pipelines/{pipeline_id}/statuses/{status_id}')
            if status_code == 200:
                self.fields['etap_sdelki'] = response.get('name', '')
            
            self.logs_file.write_log_file('Закончили заполнение этапа сделки')
        except Exception as ex:
            self.logs_file.write_log_file(f'Ошибка запроса "/api/v4/leads/pipelines/{pipeline_id}/statuses/{status_id}": {ex}')