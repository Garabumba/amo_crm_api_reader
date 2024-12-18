from .http_service import HTTPService
from .file_service import FileService

class CustomFieldsService:
    def __init__(self, custom_fields_url, prefix, fields, city):
        self.http_service = HTTPService(city)
        self.custom_fields_url = custom_fields_url
        self.prefix = prefix
        self.fields = fields
        self.logs_file = FileService(f'{city}_LoadLeadsLogs')
    
    def get_fields(self):
        page = 1
        self.logs_file.write_log_file(f'Начали получение пользовательских полей {self.prefix}')
        while True:
            try:
                status_code, response = self.http_service.execute_request(f'{self.custom_fields_url}?page={page}')
            except Exception as ex:
                self.logs_file.write_log_file(f'Ошибка запроса "/api/v4/contacts/{id}": {ex}')
                return 0, {}

            if status_code == 200:
                try:
                    self.__add_custom_fields(response)
                except Exception as ex:
                    file_service = FileService('LoadLeadsErrors')
                    file_service.write_log_file(f'Ошибка добавления пользовательских полей: {ex}')
                page += 1
            elif status_code == 204:
                break
            else:
                break
        self.logs_file.write_log_file(f'Закончили получение пользовательских полей {self.prefix}')

        return self.fields

    def __add_custom_fields(self, response):
        embedded = response.get('_embedded', {})
        custom_fields = embedded.get('custom_fields', [])

        if isinstance(custom_fields, list) and len(custom_fields) > 0:
            for custom_field in custom_fields:
                self.fields['custom_fields'].append(
                        {
                            'id': custom_field.get('id', 0),
                            'name': f"{self.prefix}_{custom_field.get('name', '')}",
                            'custom_field_type': custom_field.get('type', '').upper(),
                            'values': []
                        }
                    )