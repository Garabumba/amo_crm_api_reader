import pandas as pd
import re
from transliterate import translit
import os
import numpy as np
from sys import argv

class CSVService:
    def __init__(self, data_list):
        self.data_list = data_list

    def save_data_to_csv(self):
        flattened_data_list = [self.__extract_data(data) for data in self.data_list]
        df = pd.DataFrame(flattened_data_list)
        df.columns = [self.__process_column_names(col) for col in df.columns]
        for column in df.columns:
            for idx, value in enumerate(df[column]):
                if isinstance(value, str):
                    if re.match(r'\d{4}[-/]\d{2}[-/]\d{2}|\d{4}[.]\d{2}[.]\d{2}', value):
                        try:
                            df.at[idx, column] = pd.to_datetime(value).strftime('%Y-%m-%d')
                        except Exception:
                            pass
                    else:
                        df.at[idx, column] = value
                elif isinstance(value, (int, float)):
                    try:
                        df.at[idx, column] = int(value) if isinstance(value, float) and value.is_integer() else value
                    except Exception as ex:
                        df.at[idx, column] = 0
                        pass

        for column in df.columns:
            if df[column].dtype == float:
                try:
                    df[column] = df[column].fillna(0).astype(int)
                except ValueError:
                    pass
        
        float_cols = df.select_dtypes(include=['float64']).columns
        df[float_cols] = df[float_cols].map(np.int64)

        script, city = argv
        parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
        output_file = os.path.join(parent_dir, f'leads_csv/{city}.csv')
        df.to_csv(output_file, index=False, encoding='utf-8-sig', sep=';', quotechar='"', quoting=1)

    def __extract_data(self, data, prefix=""):
        result = {}
        if isinstance(data, dict):
            for key, value in data.items():
                if key == 'custom_fields' and isinstance(value, list):
                    for field in value:
                        field_name = field.get('name', '')
                        field_value = field.get('values', '')
                        if field_name:
                            result[f"{prefix}{field_name}"] = field_value
                elif isinstance(value, (dict, list)):
                    result.update(self.__extract_data(value, prefix=f'{prefix}{key}_'))
                else:
                    result[f'{prefix}{key}'] = value
        
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                result.update(self.__extract_data(item, prefix=f'{prefix}{idx}_'))
        
        return result

    def __process_column_names(self, column_name):
        transliterated = translit(column_name, 'ru', reversed=True)
        transliterated = transliterated.replace(' ', '_')
        clean_name = re.sub(r'[^\w_]', '', transliterated)
        return clean_name