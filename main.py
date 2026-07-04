import sys
import sqlite3
import os
from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


class Database:
    def __init__(self, db_path=None):
        """Инициализация базы данных"""
        if db_path is None:
            db_dir = Path(__file__).parent / "db"
            db_dir.mkdir(exist_ok=True)
            db_path = db_dir / "autoservice.db"
        
        self.db_path = str(db_path)
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        self.init_test_data()
        
    def connect(self):
        """Подключение к БД"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Ошибка подключения к БД: {e}")
    
    def create_tables(self):
        """Создание таблиц, если их нет"""

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Автомобили (
                идентификатор_автомобиля INTEGER PRIMARY KEY AUTOINCREMENT,
                vin TEXT UNIQUE NOT NULL,
                имя_владельца TEXT NOT NULL,
                марка TEXT NOT NULL,
                модель TEXT NOT NULL,
                год_выпуска INTEGER NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Заказы_на_работы (
                идентификатор_заказа INTEGER PRIMARY KEY AUTOINCREMENT,
                идентификатор_автомобиля INTEGER NOT NULL,
                название_услуги TEXT,
                дата_работ TEXT NOT NULL,
                стоимость_запчастей REAL DEFAULT 0,
                стоимость_ремонта REAL,
                FOREIGN KEY (идентификатор_автомобиля) 
                    REFERENCES Автомобили(идентификатор_автомобиля) 
                    ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Статистика (
                id INTEGER PRIMARY KEY,
                max_ремонт REAL,
                min_ремонт REAL,
                max_запчасти REAL,
                min_запчасти REAL,
                общая_стоимость REAL
            )
        ''')
        
        self.conn.commit()
        self.create_triggers()
    
    def create_triggers(self):
        """Создание триггеров для обновления статистики"""
        self.cursor.execute("DROP TRIGGER IF EXISTS update_stats_after_insert")
        self.cursor.execute("DROP TRIGGER IF EXISTS update_stats_after_delete")
        self.cursor.execute("DROP TRIGGER IF EXISTS update_stats_after_update")

        self.cursor.execute('''
            CREATE TRIGGER update_stats_after_insert
            AFTER INSERT ON Заказы_на_работы
            BEGIN
                INSERT OR REPLACE INTO Статистика (id, max_ремонт, min_ремонт, max_запчасти, min_запчасти, общая_стоимость)
                SELECT 
                    1,
                    COALESCE(MAX(стоимость_ремонта), 0),
                    COALESCE(MIN(стоимость_ремонта), 0),
                    COALESCE(MAX(стоимость_запчастей), 0),
                    COALESCE(MIN(стоимость_запчастей), 0),
                    COALESCE(SUM(стоимость_ремонта + стоимость_запчастей), 0)
                FROM Заказы_на_работы;
            END
        ''')

        self.cursor.execute('''
            CREATE TRIGGER update_stats_after_delete
            AFTER DELETE ON Заказы_на_работы
            BEGIN
                INSERT OR REPLACE INTO Статистика (id, max_ремонт, min_ремонт, max_запчасти, min_запчасти, общая_стоимость)
                SELECT 
                    1,
                    COALESCE(MAX(стоимость_ремонта), 0),
                    COALESCE(MIN(стоимость_ремонта), 0),
                    COALESCE(MAX(стоимость_запчастей), 0),
                    COALESCE(MIN(стоимость_запчастей), 0),
                    COALESCE(SUM(стоимость_ремонта + стоимость_запчастей), 0)
                FROM Заказы_на_работы;
            END
        ''')

        self.cursor.execute('''
            CREATE TRIGGER update_stats_after_update
            AFTER UPDATE ON Заказы_на_работы
            BEGIN
                INSERT OR REPLACE INTO Статистика (id, max_ремонт, min_ремонт, max_запчасти, min_запчасти, общая_стоимость)
                SELECT 
                    1,
                    COALESCE(MAX(стоимость_ремонта), 0),
                    COALESCE(MIN(стоимость_ремонта), 0),
                    COALESCE(MAX(стоимость_запчастей), 0),
                    COALESCE(MIN(стоимость_запчастей), 0),
                    COALESCE(SUM(стоимость_ремонта + стоимость_запчастей), 0)
                FROM Заказы_на_работы;
            END
        ''')
        
        self.conn.commit()
    
    def init_test_data(self):
        """Заполнение тестовыми данными"""
        self.cursor.execute("SELECT COUNT(*) FROM Автомобили")
        if self.cursor.fetchone()[0] > 0:
            self.update_statistics()
            return

        cars = [
            ('WVWZZZ1JZ3W123456', 'Иванов Петр', 'Volkswagen', 'Golf', 2015),
            ('JHMGD18509S123456', 'Сидорова Анна', 'Honda', 'Civic', 2018),
            ('1HGCM82633A123456', 'Петров Сергей', 'Honda', 'Accord', 2020),
            ('5NPDH4AE7DH123456', 'Козлова Елена', 'Hyundai', 'Elantra', 2017),
            ('JTDBE32K900123456', 'Смирнов Алексей', 'Toyota', 'Corolla', 2019)
        ]
        
        for car in cars:
            self.cursor.execute(
                "INSERT INTO Автомобили (vin, имя_владельца, марка, модель, год_выпуска) VALUES (?, ?, ?, ?, ?)",
                car
            )

        orders = [
            (1, 'Замена масла', '2026-01-15', 1500.00, 800.00),
            (1, 'Замена тормозных колодок', '2026-02-10', 3500.00, 1200.00),
            (2, 'Диагностика двигателя', '2026-01-20', 0.00, 2500.00),
            (2, 'Замена свечей зажигания', '2026-03-05', 2000.00, 900.00),
            (3, 'Замена ремня ГРМ', '2026-01-25', 4500.00, 3000.00),
            (3, 'Замена масла', '2026-02-15', 1500.00, 800.00),
            (4, 'Ремонт подвески', '2026-02-01', 6000.00, 3500.00),
            (4, 'Замена тормозной жидкости', '2026-03-10', 800.00, 600.00),
            (5, 'Замена аккумулятора', '2026-01-30', 5000.00, 700.00),
            (5, 'Диагностика электроники', '2026-02-20', 0.00, 2000.00)
        ]
        
        for order in orders:
            self.cursor.execute(
                "INSERT INTO Заказы_на_работы (идентификатор_автомобиля, название_услуги, дата_работ, стоимость_запчастей, стоимость_ремонта) VALUES (?, ?, ?, ?, ?)",
                order
            )
        
        self.conn.commit()
        self.update_statistics()
    
    def update_statistics(self):
        """Обновление статистики вручную"""
        self.cursor.execute('''
            INSERT OR REPLACE INTO Статистика (id, max_ремонт, min_ремонт, max_запчасти, min_запчасти, общая_стоимость)
            SELECT 
                1,
                COALESCE(MAX(стоимость_ремонта), 0),
                COALESCE(MIN(стоимость_ремонта), 0),
                COALESCE(MAX(стоимость_запчастей), 0),
                COALESCE(MIN(стоимость_запчастей), 0),
                COALESCE(SUM(стоимость_ремонта + стоимость_запчастей), 0)
            FROM Заказы_на_работы
        ''')
        self.conn.commit()
    
    def get_all_cars(self):
        """Получение всех автомобилей"""
        self.cursor.execute("SELECT * FROM Автомобили ORDER BY идентификатор_автомобиля")
        return self.cursor.fetchall()
    
    def get_orders_by_car(self, car_id):
        """Получение заказов для автомобиля"""
        self.cursor.execute(
            "SELECT * FROM Заказы_на_работы WHERE идентификатор_автомобиля = ? ORDER BY дата_работ DESC",
            (car_id,)
        )
        return self.cursor.fetchall()
    
    def search_cars(self, make=None, owner=None, year_from=None, year_to=None):
        """Поиск автомобилей"""
        query = "SELECT * FROM Автомобили WHERE 1=1"
        params = []
        
        if make:
            query += " AND марка LIKE ?"
            params.append(f"%{make}%")
        if owner:
            query += " AND имя_владельца LIKE ?"
            params.append(f"%{owner}%")
        if year_from:
            query += " AND год_выпуска >= ?"
            params.append(year_from)
        if year_to:
            query += " AND год_выпуска <= ?"
            params.append(year_to)
        
        query += " ORDER BY идентификатор_автомобиля"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def add_car(self, vin, owner, make, model, year):
        """Добавление автомобиля"""
        try:
            self.cursor.execute(
                "INSERT INTO Автомобили (vin, имя_владельца, марка, модель, год_выпуска) VALUES (?, ?, ?, ?, ?)",
                (vin, owner, make, model, year)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def delete_car(self, car_id):
        """Удаление автомобиля (каскадное удаление заказов)"""
        self.cursor.execute("DELETE FROM Автомобили WHERE идентификатор_автомобиля = ?", (car_id,))
        self.conn.commit()
    
    def add_order(self, car_id, service, date, parts_cost, repair_cost):
        """Добавление заказа"""
        self.cursor.execute(
            "INSERT INTO Заказы_на_работы (идентификатор_автомобиля, название_услуги, дата_работ, стоимость_запчастей, стоимость_ремонта) VALUES (?, ?, ?, ?, ?)",
            (car_id, service, date, parts_cost, repair_cost)
        )
        self.conn.commit()
    
    def delete_order(self, order_id):
        """Удаление заказа"""
        self.cursor.execute("DELETE FROM Заказы_на_работы WHERE идентификатор_заказа = ?", (order_id,))
        self.conn.commit()
    
    def get_statistics(self):
        """Получение статистики"""
        self.cursor.execute("SELECT * FROM Статистика WHERE id = 1")
        return self.cursor.fetchone()
    
    def close(self):
        """Закрытие соединения"""
        if self.conn:
            self.conn.close()

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()
        self.load_cars()
        self.update_stats()
        
    def init_ui(self):
        """Создание интерфейса"""
        self.setWindowTitle("Автосервис - Управление заказами")
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(800, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        search_group = QGroupBox("Поиск")
        search_layout = QHBoxLayout()
        
        self.search_make = QLineEdit()
        self.search_make.setPlaceholderText("Введите марку")
        self.search_owner = QLineEdit()
        self.search_owner.setPlaceholderText("Введите владельца")
        
        self.year_from = QSpinBox()
        self.year_from.setRange(1990, 2026)
        self.year_from.setValue(1990)
        self.year_to = QSpinBox()
        self.year_to.setRange(1990, 2026)
        self.year_to.setValue(2026)
        
        self.btn_search = QPushButton("Поиск")
        self.btn_search.clicked.connect(self.search_cars)
        self.btn_reset = QPushButton("Сбросить")
        self.btn_reset.clicked.connect(self.reset_search)
        
        search_layout.addWidget(QLabel("Марка:"))
        search_layout.addWidget(self.search_make)
        search_layout.addWidget(QLabel("Владелец:"))
        search_layout.addWidget(self.search_owner)
        search_layout.addWidget(QLabel("Год от:"))
        search_layout.addWidget(self.year_from)
        search_layout.addWidget(QLabel("до:"))
        search_layout.addWidget(self.year_to)
        search_layout.addWidget(self.btn_search)
        search_layout.addWidget(self.btn_reset)
        search_layout.addStretch()
        
        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)

        cars_group = QGroupBox("Автомобили")
        cars_layout = QVBoxLayout()
        
        self.cars_table = QTableWidget()
        self.cars_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.cars_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.cars_table.setColumnCount(6)
        self.cars_table.setHorizontalHeaderLabels(["ID", "VIN", "Владелец", "Марка", "Модель", "Год"])
        self.cars_table.horizontalHeader().setStretchLastSection(True)
        self.cars_table.itemSelectionChanged.connect(self.on_car_selected)
        
        cars_buttons = QHBoxLayout()
        self.btn_add_car = QPushButton("Добавить автомобиль")
        self.btn_add_car.clicked.connect(self.add_car)
        self.btn_delete_car = QPushButton("Удалить автомобиль")
        self.btn_delete_car.clicked.connect(self.delete_car)
        cars_buttons.addWidget(self.btn_add_car)
        cars_buttons.addWidget(self.btn_delete_car)
        cars_buttons.addStretch()
        
        cars_layout.addWidget(self.cars_table)
        cars_layout.addLayout(cars_buttons)
        cars_group.setLayout(cars_layout)
        main_layout.addWidget(cars_group)
    
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
  
        orders_group = QGroupBox("Заказы на работы")
        orders_layout = QVBoxLayout()
        
        self.orders_table = QTableWidget()
        self.orders_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.orders_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.orders_table.setColumnCount(6)
        self.orders_table.setHorizontalHeaderLabels(["ID", "ID Авто", "Услуга", "Дата", "Запчасти", "Ремонт"])
        self.orders_table.horizontalHeader().setStretchLastSection(True)
        
        orders_buttons = QHBoxLayout()
        self.btn_add_order = QPushButton("Добавить заказ")
        self.btn_add_order.clicked.connect(self.add_order)
        self.btn_delete_order = QPushButton("Удалить заказ")
        self.btn_delete_order.clicked.connect(self.delete_order)
        orders_buttons.addWidget(self.btn_add_order)
        orders_buttons.addWidget(self.btn_delete_order)
        orders_buttons.addStretch()
        
        orders_layout.addWidget(self.orders_table)
        orders_layout.addLayout(orders_buttons)
        orders_group.setLayout(orders_layout)
        bottom_layout.addWidget(orders_group, 2)
       
        stats_group = QGroupBox("Статистика")
        stats_layout = QVBoxLayout()
        
        self.lbl_max_repair = QLabel("Макс. стоимость ремонта: 0.00 ₽")
        self.lbl_max_repair.setStyleSheet("font-weight: bold;")
        self.lbl_min_repair = QLabel("Мин. стоимость ремонта: 0.00 ₽")
        self.lbl_min_repair.setStyleSheet("font-weight: bold;")
        self.lbl_max_parts = QLabel("Макс. стоимость запчастей: 0.00 ₽")
        self.lbl_max_parts.setStyleSheet("font-weight: bold;")
        self.lbl_min_parts = QLabel("Мин. стоимость запчастей: 0.00 ₽")
        self.lbl_min_parts.setStyleSheet("font-weight: bold;")
        self.lbl_total = QLabel("Общая стоимость: 0.00 ₽")
        self.lbl_total.setStyleSheet("font-weight: bold; font-size: 14px; color: #2E7D32;")
        
        stats_layout.addWidget(self.lbl_max_repair)
        stats_layout.addWidget(self.lbl_min_repair)
        stats_layout.addWidget(self.lbl_max_parts)
        stats_layout.addWidget(self.lbl_min_parts)
        stats_layout.addStretch()
        stats_layout.addWidget(self.lbl_total)
        
        stats_group.setLayout(stats_layout)
        bottom_layout.addWidget(stats_group, 1)
        
        main_layout.addWidget(bottom_widget)

        self.apply_styles()
        self.search_make.returnPressed.connect(self.search_cars)
        self.search_owner.returnPressed.connect(self.search_cars)
    
    def apply_styles(self):
        """Применение стилей"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 13px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton#btn_delete_car, QPushButton#btn_delete_order {
                background-color: #f44336;
            }
            QPushButton#btn_delete_car:hover, QPushButton#btn_delete_order:hover {
                background-color: #da190b;
            }
            QPushButton#btn_search {
                background-color: #008CBA;
            }
            QPushButton#btn_search:hover {
                background-color: #007399;
            }
            QPushButton#btn_reset {
                background-color: #555555;
            }
            QPushButton#btn_reset:hover {
                background-color: #444444;
            }
            QTableView {
                selection-background-color: #4CAF50;
                selection-color: white;
                gridline-color: #d3d3d3;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #d3d3d3;
            }
            QSpinBox, QLineEdit {
                padding: 4px;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
        """)
    
    def load_cars(self, cars_data=None):
        """Загрузка автомобилей в таблицу"""
        if cars_data is None:
            cars_data = self.db.get_all_cars()
        
        self.cars_table.setRowCount(len(cars_data))
        for i, car in enumerate(cars_data):
            for j in range(6):
                item = QTableWidgetItem(str(car[j]))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.cars_table.setItem(i, j, item)
        
        self.cars_table.resizeColumnsToContents()
    
    def load_orders(self, car_id):
        """Загрузка заказов для выбранного автомобиля"""
        orders = self.db.get_orders_by_car(car_id)
        
        self.orders_table.setRowCount(len(orders))
        for i, order in enumerate(orders):
            for j in range(6):
                item = QTableWidgetItem(str(order[j]))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.orders_table.setItem(i, j, item)
        
        self.orders_table.resizeColumnsToContents()
    
    def on_car_selected(self):
        """Обработка выбора автомобиля"""
        selected = self.cars_table.currentRow()
        if selected >= 0:
            car_id = self.cars_table.item(selected, 0).text()
            self.load_orders(int(car_id))
            self.update_stats()
    
    def search_cars(self):
        """Поиск автомобилей"""
        make = self.search_make.text().strip()
        owner = self.search_owner.text().strip()
        year_from = self.year_from.value()
        year_to = self.year_to.value()
        
        cars = self.db.search_cars(make, owner, year_from, year_to)
        self.load_cars(cars)
        self.orders_table.setRowCount(0)
    
    def reset_search(self):
        """Сброс поиска"""
        self.search_make.clear()
        self.search_owner.clear()
        self.year_from.setValue(1990)
        self.year_to.setValue(2026)
        self.load_cars()
        self.orders_table.setRowCount(0)
    
    def add_car(self):
        """Добавление автомобиля"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить автомобиль")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        vin_edit = QLineEdit()
        vin_edit.setPlaceholderText("Уникальный VIN код")
        owner_edit = QLineEdit()
        owner_edit.setPlaceholderText("ФИО владельца")
        make_edit = QLineEdit()
        make_edit.setPlaceholderText("Марка")
        model_edit = QLineEdit()
        model_edit.setPlaceholderText("Модель")
        year_edit = QSpinBox()
        year_edit.setRange(1990, 2026)
        year_edit.setValue(2020)
        
        layout.addRow("VIN:", vin_edit)
        layout.addRow("Владелец:", owner_edit)
        layout.addRow("Марка:", make_edit)
        layout.addRow("Модель:", model_edit)
        layout.addRow("Год выпуска:", year_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not vin_edit.text() or not owner_edit.text() or not make_edit.text() or not model_edit.text():
                QMessageBox.warning(self, "Ошибка", "Все поля должны быть заполнены!")
                return
            
            success = self.db.add_car(
                vin_edit.text(),
                owner_edit.text(),
                make_edit.text(),
                model_edit.text(),
                year_edit.value()
            )
            
            if success:
                self.load_cars()
                QMessageBox.information(self, "Успех", "Автомобиль добавлен!")
            else:
                QMessageBox.warning(self, "Ошибка", "Автомобиль с таким VIN уже существует!")
    
    def delete_car(self):
        """Удаление автомобиля"""
        selected = self.cars_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль для удаления!")
            return
        
        car_id = self.cars_table.item(selected, 0).text()
        car_info = f"{self.cars_table.item(selected, 3).text()} {self.cars_table.item(selected, 4).text()}"
        
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Удалить автомобиль {car_info} и все связанные заказы?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_car(int(car_id))
            self.load_cars()
            self.orders_table.setRowCount(0)
            self.update_stats()
            QMessageBox.information(self, "Успех", "Автомобиль удален!")
    
    def add_order(self):
        """Добавление заказа"""
        selected = self.cars_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль для добавления заказа!")
            return
        
        car_id = self.cars_table.item(selected, 0).text()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить заказ")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        service_edit = QLineEdit()
        service_edit.setPlaceholderText("Название услуги")
        
        date_edit = QDateEdit()
        date_edit.setDate(QDate.currentDate())
        date_edit.setCalendarPopup(True)
        
        parts_edit = QDoubleSpinBox()
        parts_edit.setRange(0, 100000)
        parts_edit.setPrefix("₽ ")
        parts_edit.setDecimals(2)
        
        repair_edit = QDoubleSpinBox()
        repair_edit.setRange(0, 100000)
        repair_edit.setPrefix("₽ ")
        repair_edit.setDecimals(2)
        
        layout.addRow("Услуга:", service_edit)
        layout.addRow("Дата работ:", date_edit)
        layout.addRow("Стоимость запчастей:", parts_edit)
        layout.addRow("Стоимость ремонта:", repair_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not service_edit.text():
                QMessageBox.warning(self, "Ошибка", "Укажите название услуги!")
                return
            
            self.db.add_order(
                int(car_id),
                service_edit.text(),
                date_edit.date().toString("yyyy-MM-dd"),
                parts_edit.value(),
                repair_edit.value()
            )
            
            self.load_orders(int(car_id))
            self.update_stats()
            QMessageBox.information(self, "Успех", "Заказ добавлен!")
    
    def delete_order(self):
        """Удаление заказа"""
        selected = self.orders_table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ для удаления!")
            return
        
        order_id = self.orders_table.item(selected, 0).text()
        
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            "Удалить выбранный заказ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_order(int(order_id))
            
            car_selected = self.cars_table.currentRow()
            if car_selected >= 0:
                car_id = self.cars_table.item(car_selected, 0).text()
                self.load_orders(int(car_id))
            
            self.update_stats()
            QMessageBox.information(self, "Успех", "Заказ удален!")
    
    def update_stats(self):
        """Обновление информационной панели"""
        stats = self.db.get_statistics()
        if stats:
            self.lbl_max_repair.setText(f"Макс. стоимость ремонта: {stats[1] or 0:.2f} ₽")
            self.lbl_min_repair.setText(f"Мин. стоимость ремонта: {stats[2] or 0:.2f} ₽")
            self.lbl_max_parts.setText(f"Макс. стоимость запчастей: {stats[3] or 0:.2f} ₽")
            self.lbl_min_parts.setText(f"Мин. стоимость запчастей: {stats[4] or 0:.2f} ₽")
            self.lbl_total.setText(f"Общая стоимость: {stats[5] or 0:.2f} ₽")
    
    def closeEvent(self, event):
        """Закрытие приложения"""
        self.db.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    try:
        app.setWindowIcon(QIcon("icons/app.ico"))
    except:
        pass
    
    window = MainApp()
    window.show()
    sys.exit(app.exec())