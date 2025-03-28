from .logger import logging
from .autodetect import w_detect

import os
import xlrd


class ExcelHandler:
    def __init__(self, directory="excel/", db_handler=None):
        self.directory = directory
        self.db_handler = db_handler

    def excl_to_list(self):
        listt = []
        excel_files = [f for f in os.listdir(self.directory) if f.endswith(('.xlsx', '.xls'))]
        for file_name in excel_files:
            file_path = os.path.join(self.directory, file_name)
            logging.debug(f"Чтение файла: {file_name}")
            try:
                workbook = xlrd.open_workbook(file_path)
                sheet = workbook.sheet_by_index(0)
            except Exception as e:
                logging.error(f"Не удалось открыть файл {file_name}: {e}")
                continue

            name_cord = [2, 1]
            while True:
                if name_cord[1] == 10:
                    name_cord[1] = 1
                    name_cord[0] += 9
                try:
                    name = sheet.cell_value(name_cord[0], name_cord[1])
                    if name == "":
                        break
                except Exception as e:
                    logging.error(f"Ошибка чтения ячейки ({name_cord[0]}, {name_cord[1]}) в файле {file_name}: {e}")
                    break
                if name:
                    try:
                        price = sheet.cell_value(name_cord[0] + 3, name_cord[1])
                        try:
                            old_price = sheet.cell_value(name_cord[0] + 3, name_cord[1] + 1)
                            if int(old_price) < int(price):
                                pass  # Логика может быть уточнена
                            else:
                                old_price_kost = old_price
                                price_kost = price
                                old_price = price_kost
                                price = old_price_kost
                        except:
                            old_price = None
                        country = sheet.cell_value(name_cord[0] + 2, name_cord[1])
                        new_name, mass = w_detect(name)
                        name_cord[1] += 3
                        listt.append([new_name, int(price), country, mass, int(old_price) if old_price else None])
                    except Exception as e:
                        logging.error(f"Ошибка обработки данных в файле {file_name}: {e}")
        logging.success(f"Найдено {len(listt)} ценников")
        return listt