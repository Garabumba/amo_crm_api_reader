from .http_service import HTTPService
from .file_service import FileService

class UserService:
    def get_user_name(self, id):
        if not id:
            return ''
        http_service = HTTPService()
        
        try:
            status_code, response = http_service.execute_request(f'/api/v4/users/{id}')
            return response.get('name', '')
        except Exception as ex:
            file_service = FileService('LoadLeadsLogs')
            file_service.write_log_file(f'Ошибка получения пользователя {id}: {ex}')
            return ''