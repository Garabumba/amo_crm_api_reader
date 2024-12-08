from .base_service import BaseService

class CompanyService(BaseService):
    def __init__(self, fields, city):
        super().__init__(fields, city)

    def get_company(self, id):
        try:
            status_code, response = self.http_service.execute_request(f'/api/v4/companies/{id}')
        except Exception as ex:
            self.logs_file.write_log_file(f'Ошибка запроса "/api/v4/companies/{id}": {ex}')
            return self.fields

        if status_code == 200:
            try:
                self.__fill_company_info(response)
            except Exception as ex:
                self.logs_file.write_log_file(f'Ошибка заполнения полей кампании: {ex}')
                return self.fields
            
            try:
                self._process_common_fields()
                return self.fields
            except Exception as ex:
                self.logs_file.write_log_file(f'Ошибка преобразования полей кампании: {ex}')
                return self.fields
        elif status_code == 204:
            return self.fields
        else:
            return self.fields

    def __fill_company_info(self, response):
        self.fields['id'] = response.get('id', 0)
        self.fields['name'] = response.get('name', '')
        self.fields['responsible_user'] = response.get('responsible_user_id', 0)

        try:
            self._fill_custom_fields(response.get('custom_fields_values', []))
        except Exception as ex:
            self.logs_file.write_log_file(f'Ошибка заполнения пользовательских полей кампании: {ex}')