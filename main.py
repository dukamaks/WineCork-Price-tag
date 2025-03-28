import os
import re
import glob
import asyncio
import json
import webbrowser

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit,
    QMessageBox, QScrollArea, QScrollBar, QCheckBox, QProgressBar,
    QTextEdit, QLCDNumber, QSpinBox, QComboBox, QHBoxLayout, QGridLayout,
    QDialog, QDialogButtonBox
)
from PyQt5.QtCore import QRunnable, QThreadPool, Qt, QSize, pyqtSignal, QFileSystemWatcher
from PyQt5.QtGui import QPixmap
import sys

from cogs.archive import create_archive
from cogs.generate import form1, form2, add_newlines
from cogs.logger import logging
from cogs.excel import ExcelHandler
from cogs.database import DatabaseHandler
from cogs.search import goodwine_search, load_img


class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fn(*self.args, **self.kwargs))
        loop.close()


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super(ClickableLabel, self).__init__(parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


class GalleryWindow(QWidget):
    def __init__(self, main_window, db_handler, parent=None):
        super(GalleryWindow, self).__init__(parent)
        self.main_window = main_window
        self.db_handler = db_handler
        self.setWindowTitle("Галерея")

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        self.container = QWidget()
        self.scroll_area.setWidget(self.container)

        self.container_layout = QGridLayout()
        self.container.setLayout(self.container_layout)
        self.labels = []

        self.setMinimumSize(800, 600)
        self.setWindowFlags(Qt.Window)

        output_path = os.path.join(os.getcwd(), "output")
        if os.path.exists(output_path):
            self.watcher = QFileSystemWatcher()
            self.watcher.addPath(output_path)
            self.watcher.directoryChanged.connect(self.load_images)
            logging.debug("Наблюдатель за папкой 'output/' добавлен.")
        else:
            logging.error("Папка 'output/' не существует.")
            QMessageBox.critical(self, "Ошибка", "Папка 'output/' не найдена.")
            return

        self.load_images()

    def load_images(self):
        logging.debug("Загрузка изображений в галерее.")
        for widget in self.labels:
            self.container_layout.removeWidget(widget)
            widget.deleteLater()
        self.labels = []

        try:
            image_files = [
                f for f in os.listdir("output/")
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))
            ]

            images_with_ids = []
            for f in image_files:
                try:
                    id_str = f.split('_')[0]
                    id_int = int(id_str)
                    images_with_ids.append((f, id_int))
                except ValueError:
                    logging.warning(f"Неверный формат имени файла: {f}. Ожидается формат 'ID_имя.png'.")
                    continue

            images_with_ids.sort(key=lambda x: x[1])
            sorted_image_files = [f for f, id in images_with_ids]

            if not sorted_image_files:
                logging.warning("В папке 'output/' нет изображений для отображения.")
                QMessageBox.information(self, "Галерея", "В папке 'output/' нет изображений для отображения.")
                return

        except Exception as e:
            logging.error(f"Ошибка при чтении папки 'output/': {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать папку 'output/': {e}")
            return

        for image_file in sorted_image_files:
            try:
                id_str = image_file.split('_')[0]
                idd = int(id_str)
            except ValueError:
                logging.warning(f"Неверный формат имени файла: {image_file}. Ожидается формат 'ID_имя.png'.")
                idd = None

            widget = QWidget()
            v_layout = QVBoxLayout()
            widget.setLayout(v_layout)

            label = ClickableLabel()
            pixmap = QPixmap(os.path.join("output/", image_file))
            if pixmap.isNull():
                logging.warning(f"Не удалось загрузить изображение: {image_file}")
                continue
            label.setPixmap(pixmap.scaled(QSize(200, 200), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            label.setAlignment(Qt.AlignCenter)
            label.setToolTip(image_file)
            label.clicked.connect(lambda f=image_file: self.open_edit_window(f))
            v_layout.addWidget(label)

            if idd is not None:
                id_label = QLabel(f"ID: {idd}")
                id_label.setAlignment(Qt.AlignCenter)
                v_layout.addWidget(id_label)

            self.labels.append(widget)

        self.update_layout()
        logging.debug("Изображения успешно загружены в галерею.")

    def update_layout(self):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        widget_width = 220
        spacing = self.container_layout.spacing()
        available_width = self.scroll_area.viewport().width()
        columns = max(1, available_width // (widget_width + spacing))

        for index, widget in enumerate(self.labels):
            row = index // columns
            col = index % columns
            self.container_layout.addWidget(widget, row, col)

    def resizeEvent(self, event):
        super(GalleryWindow, self).resizeEvent(event)
        self.update_layout()

    def open_edit_window(self, filename):
        logging.debug(f"Попытка открыть окно редактирования для файла: {filename}")
        try:
            id_str = filename.split('_')[0]
            idd = int(id_str)
            card = self.db_handler.find_one_card(_id=idd)
            if card:
                self.main_window.open_edit_add_window(card)
            else:
                QMessageBox.critical(self, "Ошибка", f"Карточка с ID {idd} не найдена в базе данных.")
        except ValueError:
            QMessageBox.critical(self, "Ошибка", f"Неверный формат имени файла: {filename}. Ожидается формат 'ID_имя.png'.")
        except Exception as e:
            logging.error(f"Ошибка при открытии окна редактирования для файла {filename}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть карточку для файла {filename}.")


class EditAddWindow(QWidget):
    def __init__(self, main_window, db_handler, card=None, parent=None):
        super(EditAddWindow, self).__init__(parent)
        self.main_window = main_window
        self.db_handler = db_handler
        self.card = card
        self.is_editing = card is not None

        self.setWindowTitle(f"Редактирование ценника №{card['_id']}" if self.is_editing else "Добавление ценника")
        self.setFixedSize(400, 600)

        layout = QVBoxLayout()

        label_name = QLabel("Название:")
        layout.addWidget(label_name)
        self.entry_name = QTextEdit()
        if self.is_editing:
            self.entry_name.setText(add_newlines(card["name"])[0])
        layout.addWidget(self.entry_name)

        label_weight = QLabel("Вес:")
        layout.addWidget(label_weight)
        self.entry_weight = QLineEdit()
        if self.is_editing:
            self.entry_weight.setText(str(card["weight"]))
        layout.addWidget(self.entry_weight)

        label_price = QLabel("Цена:")
        layout.addWidget(label_price)
        self.entry_price = QLineEdit()
        if self.is_editing:
            self.entry_price.setText(str(card["price"]))
        layout.addWidget(self.entry_price)

        label_old_price = QLabel("Старая цена (опционально):")
        layout.addWidget(label_old_price)
        self.entry_old_price = QLineEdit()
        if self.is_editing:
            self.entry_old_price.setText("" if (card['old_price'] is None) else str(card['old_price']))
        layout.addWidget(self.entry_old_price)

        label_country = QLabel("Страна:")
        layout.addWidget(label_country)
        self.combo_country = QComboBox()
        self.combo_country.addItem("")
        files = os.listdir('req/country')

        for file in files:
            if file.lower().endswith(('.jpg', '.png')):
                country_name = os.path.splitext(file)[0]
                self.combo_country.addItem(country_name)

        if self.is_editing and card.get('country'):
            index = self.combo_country.findText(str(card['country']).upper())
            if index != -1:
                self.combo_country.setCurrentIndex(index)
        layout.addWidget(self.combo_country)

        self.checkbox_save_copy = QCheckBox("Сохранить как копию")
        layout.addWidget(self.checkbox_save_copy)

        self.checkbox_per = QCheckBox("Убрать процент?")
        layout.addWidget(self.checkbox_per)

        button_layout = QHBoxLayout()

        self.button_open_browser = QPushButton("Открыть в браузере")
        self.button_open_browser.setFixedSize(150, 25)
        self.button_open_browser.clicked.connect(self.open_in_browser_manual)
        button_layout.addWidget(self.button_open_browser)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        self.button_auto_search = QPushButton("Авто поиск")
        self.button_auto_search.setFixedSize(150, 25)
        self.button_auto_search.clicked.connect(self.auto_search)
        button_layout.addWidget(self.button_auto_search)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.button_save = QPushButton("Сохранить")
        self.button_save.clicked.connect(self.save_changes)
        layout.addWidget(self.button_save)

        self.setLayout(layout)

    def auto_search(self):
        query = self.entry_name.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "Внимание", "Введите название для поиска.")
            return

        result = goodwine_search(query)

        if result:
            self.show_search_result(result)
        else:
            QMessageBox.information(self, "Результат поиска", "Ничего не найдено.")


    def show_search_result(self, result):
        dialog = QDialog(self)
        dialog.setWindowTitle("Результат поиска")

        dialog.resize(600, 400)

        layout = QVBoxLayout(dialog)

        main_layout = QHBoxLayout()

        info_layout = QVBoxLayout()

        name_label = QLabel(result['name'])
        name_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(name_label)

        country_flag_label = QLabel()
        country_flag_pixmap = QPixmap(result['custom_attributes']['country_flag'])
        country_flag_label.setPixmap(country_flag_pixmap)
        info_layout.addWidget(country_flag_label)

        country_label = QLabel(result['custom_attributes']['country'])
        country_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(country_label)

        main_layout.addLayout(info_layout)

        image_label = QLabel()
        image_url = result['small_image']['url']
        image_pixmap = QPixmap()
        image_label.setPixmap(image_pixmap)
        image_label.setAlignment(Qt.AlignTop)

        main_layout.addWidget(image_label)

        layout.addLayout(main_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok, dialog)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.exec_()



    def open_in_browser_manual(self):
        query = self.entry_name.toPlainText().strip().replace(" ", "+")
        if not query:
            QMessageBox.warning(self, "Внимание", "Введите название для поиска.")
            return
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open_new(url)

    def save_changes(self):
        new_name = self.entry_name.toPlainText().strip()
        new_weight = self.entry_weight.text().strip()
        new_price = self.entry_price.text().strip()
        new_old_price = self.entry_old_price.text().strip()
        new_country = self.combo_country.currentText().strip()
        copy = self.checkbox_save_copy.isChecked()
        per = self.checkbox_per.isChecked()

        if not new_name or not new_weight or not new_price:
            QMessageBox.warning(self, "Внимание", "Поля Название, Вес и Цена обязательны.")
            return

        try:
            new_price = int(new_price)
            new_old_price = int(new_old_price) if new_old_price else None
        except ValueError:
            QMessageBox.warning(self, "Внимание", "Вес и Цена должны быть числами.")
            return

        try:
            if self.is_editing:
                update_fields = {
                    "name": new_name,
                    "weight": new_weight,
                    "price": new_price,
                    "old_price": new_old_price,
                    "country": new_country if new_country else None
                }

                self.db_handler.update_card(self.card["_id"], update_fields)
                logging.info(f"Карточка {self.card['_id']} обновлена.")

                copy_value = "_copy" if copy else ""
                files = glob.glob(f"output/{self.card['_id']}{copy_value}*")
                for i in files:
                    try:
                        os.remove(i)
                        logging.debug(f"Удалён файл: {i}")
                    except Exception as e:
                        logging.error(f"Ошибка при удалении файла {i}: {e}")

                if new_old_price:
                    form2(str(f"{self.card['_id']}{copy_value}"), new_name, new_weight, int(new_price), int(new_old_price), per, bypass_text=True)
                else:
                    form1(str(f"{self.card['_id']}{copy_value}"), new_name, new_weight, f"{new_price} ГРН", new_country, bypass_text=True)

                QMessageBox.information(self, "Успех", f"Карточка с ID {self.card['_id']} успешно обновлена.")
            else:
                new_id = self.db_handler.get_last_document_id() + 1

                new_card = {
                    "_id": new_id,
                    "name": new_name,
                    "weight": new_weight,
                    "price": new_price,
                    "old_price": new_old_price,
                    "country": new_country if new_country else None
                }

                self.db_handler.db.insert_one(new_card)
                logging.info(f"Создана новая карточка с ID {new_id}.")

                copy_value = "_copy" if copy else ""
                if new_old_price:
                    form2(str(new_id) + copy_value, new_name, new_weight, new_price, new_old_price, per, bypass_text=True)
                else:
                    form1(str(new_id) + copy_value, new_name, new_weight, f"{new_price} ГРН", new_country, bypass_text=True)

            self.close()

            if self.main_window.gallery_window:
                self.main_window.gallery_window.load_images()

        except Exception as e:
            if self.is_editing:
                logging.error(f"Ошибка при обновлении карточки {self.card['_id']}: {e}")
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить изменения.")
            else:
                logging.error(f"Ошибка при добавлении новой карточки: {e}")
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить новую карточку.")


class MyWindow(QWidget):
    def __init__(self, db_handler):
        super().__init__()

        self.db_handler = db_handler
        self.setWindowTitle("WineCork")
        self.layout = QVBoxLayout()

        self.radio_mode1 = QPushButton("Автоматические ценники")
        self.radio_mode1.clicked.connect(lambda: self.on_mode_selected(1))
        self.layout.addWidget(self.radio_mode1)

        self.radio_mode2 = QPushButton("Поиск по названию")
        self.radio_mode2.clicked.connect(lambda: self.on_mode_selected(2))
        self.layout.addWidget(self.radio_mode2)

        self.radio_mode3 = QPushButton("Повторить из бд")
        self.radio_mode3.clicked.connect(lambda: self.on_mode_selected(3))
        self.layout.addWidget(self.radio_mode3)

        self.radio_mode4 = QPushButton("Архивировать все")
        self.radio_mode4.clicked.connect(lambda: self.on_mode_selected(4))
        self.layout.addWidget(self.radio_mode4)

        self.radio_mode5 = QPushButton("Галерея")
        self.radio_mode5.clicked.connect(lambda: self.on_mode_selected(5))
        self.layout.addWidget(self.radio_mode5)

        self.radio_mode6 = QPushButton("Ручное добавление")
        self.radio_mode6.clicked.connect(lambda: self.on_mode_selected(6))
        self.layout.addWidget(self.radio_mode6)

        self.spinBox = QSpinBox(self)
        self.spinBox.setMaximum(10000)
        self.layout.addWidget(self.spinBox)

        self.entry_search_text = QLineEdit()
        self.entry_search_text.setPlaceholderText("Текст для поиска")
        self.layout.addWidget(self.entry_search_text)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.layout.addWidget(self.progress_bar)

        self.setLayout(self.layout)
        self.threadpool = QThreadPool()

        self.gallery_window = None

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def on_mode_selected(self, mode):
        if mode == 1:
            self.handle_automatic_price_tags()
        elif mode == 2:
            self.handle_search_by_name()
        elif mode == 3:
            self.handle_repeat_from_db()
        elif mode == 4:
            self.handle_archive_all()
        elif mode == 5:
            self.open_gallery()
        elif mode == 6:
            self.open_edit_add_window()
        else:
            QMessageBox.warning(self, "Внимание", "Неизвестный режим работы.")
            logging.warning(f"Попытка выбрать неизвестный режим: {mode}")

    def handle_automatic_price_tags(self):
        bd = []
        excel_handler = ExcelHandler(db_handler=self.db_handler)
        data_from_excel = excel_handler.excl_to_list()
        self.progress_bar.setMaximum(len(data_from_excel))
        last_id = self.db_handler.get_last_document_id()
        idd = last_id
        for id, row_data in enumerate(data_from_excel):
            product = self.db_handler.find_one_card(name=row_data[0], weight=row_data[3], price=row_data[1])
            if product:
                if row_data[4]:
                    form2(product["_id"], row_data[0], row_data[3], row_data[1], row_data[4])
                else:
                    form1(product["_id"], row_data[0], row_data[3], f"{row_data[1]} ГРН", row_data[2])
            else:
                idd += 1
                bd.append({
                    "_id": idd,
                    "name": row_data[0],
                    "weight": row_data[3],
                    "price": row_data[1],
                    "old_price": row_data[4],
                    "country": row_data[2]
                })
                if row_data[4]:
                    form2(idd, row_data[0], row_data[3], row_data[1], row_data[4])
                else:
                    form1(idd, row_data[0], row_data[3], f"{row_data[1]} ГРН", row_data[2])
            self.progress_bar.setValue(id + 1)
        logging.info(f"{len(data_from_excel)} ценников созданы")
        if bd:
            self.db_handler.insert_many_cards(bd)
            logging.info(f"В базу данных записано {len(bd)} ценников")

    def handle_search_by_name(self):
        text = self.entry_search_text.text()
        if not text:
            QMessageBox.warning(self, "Внимание", "Введите текст для поиска.")
            return
        data = self.db_handler.find_cards_by_name(text)
        self.result_window = QScrollArea()
        self.result_window.setWindowTitle("Результаты поиска")
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel("Результаты поиска:")
        layout.addWidget(label)

        for item in data:
            result_text = (
                f"ID: {item['_id']}\n"
                f"Название: {item['name']}\n"
                f"Вес: {item['weight']}\n"
                f"Цена: {item['price']}\n"
                f"Старая цена: {item['old_price'] if item['old_price'] else 'Нет'}\n"
                f"Страна: {item['country'] if item['country'] else 'Не указана'}\n\n"
            )
            item_label = QLabel(result_text)
            layout.addWidget(item_label)
            edit_button = QPushButton("Редактировать")
            edit_button.clicked.connect(lambda _, item=item: self.open_edit_add_window(item))
            layout.addWidget(edit_button)
        self.result_window.setWidget(widget)
        self.result_window.setWidgetResizable(True)
        v_scroll_bar = QScrollBar(self.result_window)
        self.result_window.setVerticalScrollBar(v_scroll_bar)

        self.result_window.show()

    def handle_repeat_from_db(self):
        try:
            idd = int(self.spinBox.text())
            cart = self.db_handler.find_one_card(_id=idd)
            if cart:
                self.open_edit_add_window(cart)
            else:
                QMessageBox.critical(self, "Ошибка", "Такого ID не найдено.")
        except ValueError:
            QMessageBox.critical(self, "Ошибка", "Введите корректный ID.")

    def handle_archive_all(self):
        try:
            create_archive("output/")
            logging.success("Архив создан")
            QMessageBox.information(self, "Архивация", "Архив успешно создан.")
        except Exception as e:
            logging.error(f"Ошибка при архивации: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать архив: {e}")

    def open_edit_add_window(self, card=None):
        self.edit_add_window = EditAddWindow(self, self.db_handler, card)
        self.edit_add_window.show()

    def open_gallery(self):
        logging.debug("Создание галереи")
        if self.gallery_window is None:
            self.gallery_window = GalleryWindow(self, self.db_handler)
        self.gallery_window.show()
        self.gallery_window.raise_()
        self.gallery_window.activateWindow()


def main():
    db_handler = DatabaseHandler()
    old_id = db_handler.get_estimated_count()
    logging.info(f"Загружено из базы данных {old_id} значений.")

    app = QApplication(sys.argv)
    window = MyWindow(db_handler)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
