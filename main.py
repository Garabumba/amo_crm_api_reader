from services.lead_service import LeadService
from services.http_service import HTTPService
from services.custom_fields_service import CustomFieldsService
from services.file_service import FileService
from services.csv_service import CSVService
import copy

logs_file = FileService('LoadLeadsLogs')

custom_fields_service = CustomFieldsService(
        '/api/v4/leads/custom_fields', 
        'lead', 
        {
            'id': '',
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
            'contact_ids': '',
            'company_ids': '',
            'contacts': [],
            'etap_sdelki': '',
            'pipeline': '',
            'companies': [],
            'custom_fields': []
        }
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
        }
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
        }
    )
contact_fields = custom_fields_service.get_fields()
http_service = HTTPService()
data_list = []
page = 1

while True:
    try:
        status_code, response = http_service.execute_request(f'/api/v4/leads?limit=250&with=source_id,catalog_elements,contacts,loss_reason&filter[pipeline_id]=7665806&page={page}')#with=contacts&limit=100filter[id]=17522845')
        if status_code == 200:    
            embedded = response.get('_embedded', {})
            leads = embedded.get('leads', [])
            for lead in leads:
                logs_file.write_log_file(f'Начали обработку сделки {lead.get('id')}')
                l = LeadService(copy.deepcopy(lead_fields), copy.deepcopy(contact_fields), copy.deepcopy(company_fields))
                data_list.append(l.get_leads(lead))
                
            page += 1
        else:
            break
    except Exception as ex:
        logs_file.write_log_file(f'Ошибка запроса "/api/v4/leads?limit=1&with=source_id,catalog_elements,contacts,loss_reason&filter[pipeline_id]=7665806&page={page}": {ex}')
        break

csv_service = CSVService(data_list)
csv_service.save_data_to_csv()