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

    def _fill_custom_fields(self, custom_fields_values):
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
                        #break
                    else:
                        extracted_value = value_data
                    
                    custom_field['values'].append(extracted_value)
                else:
                    if is_phone_field:
                        try:
                            extracted_value = self.__extract_phone_number(value_data)
                        except Exception as ex:
                            self.logs_file.write_log_file(f'Ошибка преобразования телефона {value_data}: {ex}')
                            extracted_value = value_data
                        #break
                    else:
                        extracted_value = value_data
                    
                    custom_field['values'].append(extracted_value)
        self.logs_file.write_log_file('Закончили заполнение пользовательских полей')

    def __change_value_type(self, values, new_type):
        #https://www.amocrm.ru/developers/content/crm_platform/custom-fields#%D0%94%D0%BE%D1%81%D1%82%D1%83%D0%BF%D0%BD%D1%8B%D0%B5-%D1%82%D0%B8%D0%BF%D1%8B-%D0%BF%D0%BE%D0%BB%D0%B5%D0%B9
        try:
            if isinstance(values, str):
                return values, True
            
            if isinstance(values, list) and len(values) == 0:
                return '', True

            if new_type == 'SELECT' or new_type == 'MULTISELECT':
                if isinstance(values, list):
                    return ', '.join(values), True
                else:
                    return str(values), True
            elif new_type == 'TEXT' or new_type == 'TEXTAREA':
                return str(values[0]), True
            elif new_type == 'DATE' or new_type == 'DATE_TIME':
                return self.service.read_timestamp_date(str(values[0])), True
            elif new_type == 'NUMERIC':
                try:
                    return int(values[0]), True
                except:
                    return float(values[0]), True
            elif new_type == 'CHECKBOX':
                return bool(values[0]), True
            else:
                return values, False
        except Exception as ex:
            self.logs_file.write_log_file(f'Ошибка преобразования типа пользовательских полей: {ex}')
            return values, False

    def __extract_phone_number(self, phone_string):
        return re.sub(r'\D', '', phone_string)

    def _process_common_fields(self):
        self.logs_file.write_log_file('Начали заполнение полей')
        self.fields['responsible_user'] = self.user_service.get_user_name(self.fields['responsible_user'])
        for custom_field in self.fields['custom_fields']:
            values = custom_field['values']
            custom_field_type = custom_field['custom_field_type']
            values, is_value_type_changed = self.__change_value_type(values, custom_field_type)
            if is_value_type_changed:
                custom_field['values'] = values
            else:
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
                    elif 'ТЕЛЕФОН' in custom_field['name'].upper() or 'PHONE' in custom_field['name'].upper():
                        custom_field['values'] = values[0]
                    elif isinstance(values, list):
                        if isinstance(values[0], (int, float)):
                            custom_field['values'] = int(values[0])
                        else:
                            custom_field['values'] = ', '.join(str(value) for value in values)
                except Exception as ex:
                    self.logs_file.write_log_file(f'Ошибка заполнения пользовательского поля {custom_field["name"]}: {ex}')
                    custom_field['values'] = ''

        self.logs_file.write_log_file('Закончили заполнение полей')