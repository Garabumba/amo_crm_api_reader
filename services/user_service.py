from .http_service import HTTPService
from .file_service import FileService

class UserService:
    def __init__(self, city):
        self.city = city
    
    def get_user_name(self, id):
        if not id:
            return ''
        http_service = HTTPService(self.city)
        
        try:
            status_code, response = http_service.execute_request(f'/api/v4/users/{id}')
            if status_code == 200:
                return response.get('name', '')
            else:
                file_service = FileService(f'{self.city}_LoadLeadsLogs')
                file_service.write_log_file(f'Ошибка получения пользователя {id}: {response}')
                return ''
        except Exception as ex:
            file_service = FileService(f'{self.city}_LoadLeadsLogs')
            file_service.write_log_file(f'Ошибка получения пользователя {id}: {ex}')
            return ''