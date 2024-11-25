from .base_service import BaseService
from .company_service import CompanyService

class ContactService(BaseService):
    def __init__(self, fields, company_fields):
        super().__init__(fields)
        self.company_service = CompanyService(company_fields)

    def get_contact(self, id):
        try:
            status_code, response = self.http_service.execute_request(f'/api/v4/contacts/{id}')
        except Exception as ex:
            self.logs_file.write_log_file(f'Ошибка запроса "/api/v4/contacts/{id}": {ex}')
            return self.fields
        
        if status_code == 200:
            try:
                self.__fill_contact_info(response)
            except Exception as ex:
                self.logs_file.write_log_file(f'Ошибка заполнения полей контакта: {ex}')
                return self.fields
            try:
                self._process_common_fields()
                return self.fields
            except Exception as ex:
                self.logs_file.write_log_file(f'Ошибка преобразования полей контакта: {ex}')
                return self.fields
        elif status_code == 204:
            return self.fields
        else:
            return self.fields

    def __fill_contact_info(self, response):
        embedded = response.get('_embedded', {})
        companies = embedded.get('companies', [])

        self.fields['id'] = response.get('id', 0)
        self.fields['name'] = response.get('name', '')
        self.fields['responsible_user'] = response.get('responsible_user_id', 0)
        self.fields['companies'] = [company.get('id', 0) for company in companies]

        try:
            self._fill_custom_fields(response.get('custom_fields_values', []))
        except Exception as ex:
            self.logs_file.write_log_file(f'Ошибка заполнения пользовательских полей контакта: {ex}')
        
        companies = []
        for company_id in self.fields['companies']:
            try:
                companies.append(self.company_service.get_company(company_id))
            except Exception as ex:
                self.logs_file.write_log_file(f'Ошибка получения кампаний контакта: {ex}')
        
        if len(companies) > 0:
            self.fields['companies'] = companies
        else:
            try:
                self.company_service._process_common_fields()
            except Exception as ex:
                self.logs_file.write_log_file(f'Ошибка проебразования полей кампаний контакта: {ex}')

            self.fields['companies'] = [self.company_service.fields]