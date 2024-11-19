from .file_service import FileService
from .service import Service
from .http_service import HTTPService
from .user_service import UserService
import re

class BaseService:
    def __init__(self, fields):
        self.http_service = HTTPService()
        self.user_service = UserService()
        self.service = Service()
        self.fields = fields
        self.logs_file = FileService('LoadLeadsLogs')

    def fill_custom_fields(self, custom_fields_values):
        self.logs_file.write_log_file('Начали заполнение пользовательских полей')
        if not isinstance(custom_fields_values, list):
            return

        custom_fields_ids = {field['id']: field for field in self.fields['custom_fields']}
        for custom_field_value in custom_fields_values:
            custom_field_id = custom_field_value.get('field_id')
            custom_field_name = custom_field_value.get('field_name', '') or ''
            field_code = custom_field_value.get('field_code', '') or ''
            custom_field = custom_fields_ids.get(custom_field_id)
            if not custom_field:
                continue

            for value in custom_field_value.get('values', []):
                if not value:
                    continue

                contains_enum = value.get('enum_id', 0)
                value_data = value.get('value', '')
                if not value_data:
                    continue

                is_phone_field = 'PHONE' in custom_field_name.upper() or 'ТЕЛЕФОН' in custom_field_name.upper() or 'PHONE' in field_code.upper() or 'ТЕЛЕФОН' in field_code.upper()
                if contains_enum:
                    if is_phone_field:
                        try:
                            extracted_value = self.__extract_phone_number(value_data)
                        except Exception as ex:
                            self.logs_file.write_log_file(f'Ошибка преобразования телефона {value_data}: {ex}')
                            extracted_value = ''
                        break
                    else:
                        extracted_value = value_data
                    
                    custom_field['values'].append(extracted_value)
                else:
                    if is_phone_field:
                        try:
                            extracted_value = self.__extract_phone_number(value_data)
                        except Exception as ex:
                            self.logs_file.write_log_file(f'Ошибка преобразования телефона {value_data}: {ex}')
                            extracted_value = ''
                        break
                    else:
                        extracted_value = value_data
                    
                    custom_field['values'].append(extracted_value)
        self.logs_file.write_log_file('Закончили заполнение пользовательских полей')

    def __extract_phone_number(self, phone_string):
        return re.sub(r'\D', '', phone_string)

    def process_common_fields(self):
        self.logs_file.write_log_file('Начали заполнение полей')
        self.fields['responsible_user'] = self.user_service.get_user_name(self.fields['responsible_user'])
        for custom_field in self.fields['custom_fields']:
            values = custom_field['values']
            if isinstance(values, str):
                continue
            
            if isinstance(values, list) and len(values) == 0:
                custom_field['values'] = ''
                continue
            
            try:
                if 'ДАТА' in custom_field['name'].upper():
                    custom_field['values'] = ', '.join(self.service.read_timestamp_date(str(value)) for value in values)
                elif 'СУММА' in custom_field['name'].upper():
                    custom_field['values'] = float(values[0])
                elif 'ТЕЛЕФОН' in custom_field['name'].upper():
                    custom_field['values'] = values[0]
                elif isinstance(values, list) and len(values) > 0:
                    custom_field['values'] = ', '.join(str(value) for value in values)
            except Exception as ex:
                self.logs_file.write_log_file(f'Ошибка заполнения пользовательского поля {custom_field["name"]}: {ex}')
                custom_field['values'] = ''

        self.logs_file.write_log_file('Закончили заполнение полей')