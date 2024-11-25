import time
import requests
from errors.http_errors import RefreshTokenError
from .file_service import FileService
import requests_cache
from sys import argv

class HTTPService:
    def __init__(self):
        script, city = argv
        self.city = city
        if city == 'msc':
            self.file_service = FileService('msc_config.json')
        elif city == 'spb':
            self.file_service = FileService('spb_config.json')
        self.file = self.file_service.read_json_from_file()

    def execute_request(self, query_path, method='GET', data=None, use_cache=True):
        url = f"{self.file.get('BASE_URL')}{query_path}"
        token = self.file.get('BEARER_TOKEN')

        if use_cache:
            if self.city == 'msc':
                requests_cache.install_cache('msc_cache', expire_after=10800)
            elif self.city == 'spb':
                requests_cache.install_cache('spb_cache', expire_after=10800)
            
            response = requests_cache.CachedSession().request(
                url=url,
                method=method.upper(),
                headers={'Authorization': token},
                data=data
            )
        else:
            response = requests.request(
                url=url,
                method=method.upper(),
                headers={'Authorization': token},
                data=data
            )
        logs_file = FileService('LoadLeadsLogs')
        logs_file.write_log_file(f'URL: "{query_path}"\nКод ответа: {response.status_code}\nОтвет: {response.content}')

        if response.status_code == 401:
            self.__get_new_token()
            token = self.file.get('BEARER_TOKEN')
            response = requests.request(
                url=url,
                method=method.upper(),
                headers={'Authorization': token},
                data=data
            )

        elif response.status_code == 429:
            time.sleep(7)
            response = requests.request(
                url=url,
                method=method.upper(),
                headers={'Authorization': token},
                data=data
            )

        return response.status_code, response.json() if response.content else None

    def __get_new_token(self):
        data = {
            'client_id': self.file.get('CLIENT_ID'),
            'client_secret': self.file.get('CLIENT_SECRET'),
            'grant_type': 'refresh_token',
            'refresh_token': self.file.get('REFRESH_TOKEN'),
            'redirect_uri': self.file.get('REDIRECT_URI')
        }
        try:
            status_code, response = self.execute_request(query_path='/oauth2/access_token', method='POST', data=data, use_cache=False)

            if status_code == 200:
                self.file["BEARER_TOKEN"] = f"Bearer {response.get('access_token', '')}"
                self.file["REFRESH_TOKEN"] = response.get('refresh_token', '')
                self.file_service.save_json_in_file(self.file)
            else:
                raise RefreshTokenError(f'Обновление токена. Ошибка {status_code}. {response}')
        except Exception as ex:
            logs_file = FileService('LoadLeadsLogs')
            logs_file.write_log_file(f'Обновление токена. Ошибка: {ex}')