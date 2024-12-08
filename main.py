from services.lead_service import LeadService
from services.http_service import HTTPService
from services.custom_fields_service import CustomFieldsService
from services.file_service import FileService
from services.csv_service import CSVService
import copy
from sys import argv

def start(city):
    logs_file = FileService(f'{city}_LoadLeadsLogs')

    custom_fields_service = CustomFieldsService(
        '/api/v4/leads/custom_fields', 
        'lead', 
        {
            'id': 0,
            'name': '',
            'price': '',
            'responsible_user': '',
            'created_at': '',
            'created_by': '',
            'updated_at': '',
            'updated_by': '',
            'closed_at': '',
            'tags': '',
            'pipeline': '',
            'status_id': '',
            'contacts': [],
            'etap_sdelki': '',
            'pipeline': '',
            'companies': [],
            'custom_fields': [],
            'klinika': 'МСК Волконский'
        },
        city
    )
    lead_fields = custom_fields_service.get_fields()
    
    custom_fields_service = CustomFieldsService(
            '/api/v4/companies/custom_fields', 
            'company', 
            {
                'id': 0,
                'name': '',
                'responsible_user': '',
                'custom_fields': []
            },
            city
        )
    company_fields = custom_fields_service.get_fields()

    custom_fields_service = CustomFieldsService(
            '/api/v4/contacts/custom_fields', 
            'contact', 
            {
                'id': 0,
                'name': '',
                'responsible_user': '',
                'custom_fields': []
            },
            city
        )
    contact_fields = custom_fields_service.get_fields()
    http_service = HTTPService(city)
    data_list = []
    page = 1

    while True:
        try:
            if city == 'spb':
                status_code, response = http_service.execute_request(f'/api/v4/leads?limit=250&with=source_id,catalog_elements,contacts,loss_reason&filter[pipeline_id]=4959088&page={page}')
            elif city == 'msc':
                status_code, response = http_service.execute_request(f'/api/v4/leads?limit=250&with=source_id,catalog_elements,contacts,loss_reason&filter[pipeline_id]=7665806&page={page}')
            
            if status_code == 200:    
                embedded = response.get('_embedded', {})
                leads = embedded.get('leads', [])
                for lead in leads:
                    logs_file.write_log_file(f'Начали обработку сделки {lead.get("id")}')
                    lead_service = LeadService(copy.deepcopy(lead_fields), copy.deepcopy(contact_fields), copy.deepcopy(company_fields), city)
                    data_list.append(lead_service.get_leads(lead))
                    
                page += 1
            else:
                break
        except Exception as ex:
            logs_file.write_log_file(f'Ошибка запроса "/api/v4/leads?limit=1&with=source_id,catalog_elements,contacts,loss_reason&filter[pipeline_id]=4959088&page={page}": {ex}')
            break

    try:
        logs_file.write_log_file(f'Начали запись csv файла')
        csv_service = CSVService(data_list)
        csv_service.save_data_to_csv()
        logs_file.write_log_file(f'Закончили запись csv файла')
    except Exception as ex:
        logs_file.write_log_file(f'Ошибка записи csv: {ex}')

if __name__ == '__main__':
    try:
        script, city = argv
        if city in ['msc', 'spb']:
            start(city)
        else:
            print('Unknown city')
    except:
        print('No city parametr')