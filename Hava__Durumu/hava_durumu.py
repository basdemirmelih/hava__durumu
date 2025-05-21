import sys
import requests
import datetime
import sqlite3 
import os 
# Qt plugin yolunu manuel olarak ayarlayın
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = r'C:\Users\HUAWEİ\AppData\Local\Programs\Python\Python313\Lib\site-packages\PyQt5\Qt5\plugins'
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QMessageBox, QFrame,
    QGridLayout, QScrollArea, QInputDialog, QStyle,
    QAction
)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt, QSettings, QSize

DEFAULT_API_KEY_PLACEHOLDER = "YOUR_OPENWEATHERMAP_API_KEY"
PROVIDED_API_KEY = "e1b60a89616c68dd09eb7e4a916706e4"
APP_NAME = "Hava Durumu"
ORGANIZATION_NAME = "MyWeatherApp"
APP_VERSION = "1.5.0" 
DATABASE_NAME = "weather_app_data.db"

SEARCH_SYMBOL = "🔍"
THEME_MOON_SYMBOL = "🌙"
THEME_SUN_SYMBOL = "☀️" 
SETTINGS_SYMBOL = "⚙️" 
API_KEY_SYMBOL = "🔑"
EXIT_SYMBOL = "🚪" 
SUNRISE_SUNSET_SYMBOL = "🌅"
ATMOSPHERE_SYMBOL = "☁️" 
INFO_SYMBOL = "ℹ️" 
ABOUT_SYMBOL = "❓"
THEME_MENU_SYMBOL = "🎨"
FAVORITE_EMPTY_SYMBOL = "☆"
FAVORITE_FULL_SYMBOL = "★"
HISTORY_SYMBOL = "📜"
FAVORITES_MENU_SYMBOL = "⭐"


LIGHT_THEME_COLORS = {
    "window_bg": "#F0F4F7", "text_color": "#2c3e50", "input_bg": "white",
    "input_border": "#bdc3c7", "button_bg": "#3498db", "button_text": "white",
    "button_hover_bg": "#2980b9", "button_pressed_bg": "#1f618d", "frame_bg": "#FFFFFF",
    "frame_border": "#dde5ea", "forecast_card_bg": "#FAFAFA", "forecast_card_border": "#E0E0E0",
    "forecast_date_text": "#2980b9", "forecast_temp_text": "#2c3e50",
    "forecast_desc_text": "#555555", "status_text_color": "#555555",
    "icon_placeholder_text_color": "#7f8c8d",
    "menu_bar_bg": "#EAEAEA", "menu_bar_text": "#2c3e50",
    "menu_item_bg_selected": "#3498db", "menu_item_text_selected": "white",
    "feels_like_color": "#e67e22" 
}

DARK_THEME_COLORS = {
    "window_bg": "#2c3e50", "text_color": "#ecf0f1", "input_bg": "#34495e",
    "input_border": "#566573", "input_text_color": "#ecf0f1", "button_bg": "#3498db",
    "button_text": "white", "button_hover_bg": "#2980b9", "button_pressed_bg": "#1f618d",
    "frame_bg": "#34495e", "frame_border": "#415a72", "forecast_card_bg": "#2f4050",
    "forecast_card_border": "#4a6572", "forecast_date_text": "#5dade2",
    "forecast_temp_text": "#ecf0f1", "forecast_desc_text": "#bdc3c7",
    "status_text_color": "#bdc3c7", "icon_placeholder_text_color": "#7f8c8d",
    "menu_bar_bg": "#34495e", "menu_bar_text": "#ecf0f1",
    "menu_item_bg_selected": "#5dade2", "menu_item_text_selected": "#2c3e50",
    "feels_like_color": "#f39c12" 
}


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country TEXT,
            is_favorite INTEGER DEFAULT 0,
            last_searched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, country) 
        )
    """)
    conn.commit()
    conn.close()

def add_or_update_city_search(city_name, country_code):
    if not city_name: return
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO cities (name, country, last_searched_at) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(name, country) DO UPDATE SET last_searched_at=CURRENT_TIMESTAMP
        """, (city_name, country_code if country_code else ""))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Veritabanı hatası (add_or_update_city_search): {e}")
    finally:
        conn.close()

def toggle_favorite_status(city_name, country_code):
    if not city_name: return False
    conn = get_db_connection()
    cursor = conn.cursor()
    new_status = False
    try:
        cursor.execute("SELECT is_favorite FROM cities WHERE name=? AND country=?", (city_name, country_code if country_code else ""))
        row = cursor.fetchone()
        if row:
            current_is_favorite = row['is_favorite']
            new_is_favorite = 1 - current_is_favorite
            cursor.execute("UPDATE cities SET is_favorite=? WHERE name=? AND country=?", 
                           (new_is_favorite, city_name, country_code if country_code else ""))
            conn.commit()
            new_status = bool(new_is_favorite)
        else:

            cursor.execute("""
                INSERT INTO cities (name, country, is_favorite, last_searched_at) 
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            """, (city_name, country_code if country_code else ""))
            conn.commit()
            new_status = True
    except sqlite3.Error as e:
        print(f"Veritabanı hatası (toggle_favorite_status): {e}")
    finally:
        conn.close()
    return new_status


def is_city_favorite(city_name, country_code):
    if not city_name: return False
    conn = get_db_connection()
    cursor = conn.cursor()
    is_fav = False
    try:
        cursor.execute("SELECT is_favorite FROM cities WHERE name=? AND country=?", (city_name, country_code if country_code else ""))
        row = cursor.fetchone()
        if row and row['is_favorite'] == 1:
            is_fav = True
    except sqlite3.Error as e:
        print(f"Veritabanı hatası (is_city_favorite): {e}")
    finally:
        conn.close()
    return is_fav

def get_favorite_cities():
    conn = get_db_connection()
    cursor = conn.cursor()
    favorites = []
    try:
        cursor.execute("SELECT name, country FROM cities WHERE is_favorite=1 ORDER BY name ASC")
        favorites = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Veritabanı hatası (get_favorite_cities): {e}")
    finally:
        conn.close()
    return favorites

def get_recent_searches(limit=10):
    conn = get_db_connection()
    cursor = conn.cursor()
    recents = []
    try:
        cursor.execute("SELECT name, country FROM cities ORDER BY last_searched_at DESC LIMIT ?", (limit,))
        recents = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Veritabanı hatası (get_recent_searches): {e}")
    finally:
        conn.close()
    return recents


class WeatherApp(QMainWindow):
    def __init__(self): 
        super().__init__()
        self.settings = QSettings(ORGANIZATION_NAME, APP_NAME) 
        self.current_theme = self.settings.value("theme", "light")
        self.api_key = DEFAULT_API_KEY_PLACEHOLDER
        self.last_current_data = None 
        self.current_city_tuple = None 

        init_db() 

        self.setWindowTitle(APP_NAME)
        self.setGeometry(100, 100, 530, 800) 
        
        self.init_ui_elements() 
        self.update_app_icon() 
        self.init_menu_bar() 
        self.apply_styles()
        self.update_theme_dependent_symbols() 
        self.handle_initial_api_key_setup()

    def init_ui_elements(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.statusBar().setFont(QFont("Arial", 8))
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        
        top_bar_layout = QHBoxLayout()
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("Şehir adı girin (örn: Istanbul)")
        self.city_input.setFont(QFont("Arial", 11))
        self.city_input.returnPressed.connect(self.fetch_weather_data_for_current_city)
        top_bar_layout.addWidget(self.city_input, 1)

        self.search_button = QPushButton() 
        self.search_button.setFont(QFont("Arial", 12))
        self.search_button.setFixedSize(40,40)
        self.search_button.setToolTip("Hava Durumunu Getir")
        self.search_button.clicked.connect(self.fetch_weather_data_for_current_city)
        top_bar_layout.addWidget(self.search_button)

        self.theme_button = QPushButton() 
        self.theme_button.setFont(QFont("Arial", 12))
        self.theme_button.setFixedSize(40,40)
        self.theme_button.clicked.connect(self.toggle_theme)
        top_bar_layout.addWidget(self.theme_button)
        
        self.settings_button = QPushButton() 
        self.settings_button.setFont(QFont("Arial", 12))
        self.settings_button.setFixedSize(40,40)
        self.settings_button.setToolTip("API Anahtarını Değiştir")
        self.settings_button.clicked.connect(self.prompt_for_api_key_change)
        top_bar_layout.addWidget(self.settings_button)
        self.main_layout.addLayout(top_bar_layout)

        self.current_weather_frame = QFrame()
        self.current_weather_frame.setObjectName("currentWeatherFrame")
        current_weather_layout = QGridLayout(self.current_weather_frame)
        
        header_layout = QHBoxLayout() 
        self.city_name_label = QLabel("...")
        self.city_name_label.setFont(QFont("Arial", 18, QFont.Bold))
        header_layout.addWidget(self.city_name_label, 1) 

        self.favorite_button = QPushButton(FAVORITE_EMPTY_SYMBOL)
        self.favorite_button.setFont(QFont("Arial", 14)) 
        self.favorite_button.setFixedSize(40, 40)
        self.favorite_button.setToolTip("Favorilere Ekle/Çıkar")
        self.favorite_button.clicked.connect(self.toggle_current_city_favorite)
        self.favorite_button.setVisible(False) 
        header_layout.addWidget(self.favorite_button)
        current_weather_layout.addLayout(header_layout, 0, 0, 1, 3)

        self.weather_icon_label = QLabel()
        self.weather_icon_label.setFixedSize(100, 100)
        self.weather_icon_label.setAlignment(Qt.AlignCenter)
        self.weather_icon_label.setObjectName("weatherIconLabel")
        current_weather_layout.addWidget(self.weather_icon_label, 1, 0, 2, 1, Qt.AlignCenter)
        self.temp_label = QLabel("--°C")
        self.temp_label.setFont(QFont("Arial", 32, QFont.Bold))
        current_weather_layout.addWidget(self.temp_label, 1, 1, 1, 2)
        self.condition_label = QLabel("---")
        self.condition_label.setFont(QFont("Arial", 12, QFont.StyleItalic))
        current_weather_layout.addWidget(self.condition_label, 2, 1, 1, 2)
        details_font = QFont("Arial", 10)
        self.feels_like_label = QLabel("Hissedilen: --°C")
        self.feels_like_label.setFont(details_font)
        self.feels_like_label.setObjectName("feelsLikeLabelDistinct")
        current_weather_layout.addWidget(self.feels_like_label, 3, 0, 1, 1)
        self.humidity_label = QLabel("Nem: --%")
        self.humidity_label.setFont(details_font)
        current_weather_layout.addWidget(self.humidity_label, 3, 1, 1, 1)
        self.pressure_label = QLabel("Basınç: -- hPa")
        self.pressure_label.setFont(details_font)
        current_weather_layout.addWidget(self.pressure_label, 3, 2, 1, 1)
        self.wind_label = QLabel("Rüzgar: -- m/s")
        self.wind_label.setFont(details_font)
        current_weather_layout.addWidget(self.wind_label, 4, 0, 1, 3)
        self.sunrise_label = QLabel("GD: --:--")
        self.sunrise_label.setFont(details_font)
        current_weather_layout.addWidget(self.sunrise_label, 5, 0, 1, 1)
        self.sunset_label = QLabel("GB: --:--")
        self.sunset_label.setFont(details_font)
        self.sunset_label.setAlignment(Qt.AlignRight)
        current_weather_layout.addWidget(self.sunset_label, 5, 1, 1, 2)
        self.main_layout.addWidget(self.current_weather_frame)
        forecast_title_label = QLabel("Günlük Tahminler")
        forecast_title_label.setFont(QFont("Arial", 14, QFont.Bold))
        forecast_title_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(forecast_title_label)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("scrollArea")
        self.forecast_widget = QWidget()
        self.forecast_layout_container = QVBoxLayout(self.forecast_widget)
        self.forecast_layout_container.setSpacing(8)
        self.scroll_area.setWidget(self.forecast_widget)
        self.main_layout.addWidget(self.scroll_area, 1)
        self.status_label_widget = QLabel("Uygulama başlatıldı.")
        self.status_label_widget.setFont(QFont("Arial", 8, QFont.StyleItalic))
        self.statusBar().addWidget(self.status_label_widget, 1)

    def update_app_icon(self):
        icon_to_set = QIcon() 
        if hasattr(QStyle, 'SP_ComputerIcon'):
            icon_to_set = self.style().standardIcon(QStyle.SP_ComputerIcon)
        self.setWindowIcon(icon_to_set)

    def update_theme_dependent_symbols(self):
        self.search_button.setText(SEARCH_SYMBOL)
        self.settings_button.setText(SETTINGS_SYMBOL)
        if self.current_theme == "light":
            self.theme_button.setText(THEME_MOON_SYMBOL)
            self.theme_button.setToolTip("Koyu Temaya Geç")
        else:
            self.theme_button.setText(THEME_SUN_SYMBOL)
            self.theme_button.setToolTip("Açık Temaya Geç")
        self.update_toggle_theme_action_text()
        self.update_favorite_button_status() 
    def init_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&Dosya")
        change_api_action = QAction(f"{API_KEY_SYMBOL} &API Anahtarını Değiştir...", self)
        change_api_action.setStatusTip("OpenWeatherMap API anahtarınızı değiştirin veya güncelleyin")
        change_api_action.triggered.connect(self.prompt_for_api_key_change)
        file_menu.addAction(change_api_action)
        file_menu.addSeparator()
        exit_action = QAction(f"{EXIT_SYMBOL} &Çıkış", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Uygulamadan çık")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        theme_menu = menu_bar.addMenu("&Tema")
        self.toggle_theme_menu_action = QAction("Temayı Değiştir", self) 
        self.toggle_theme_menu_action.triggered.connect(self.toggle_theme)
        theme_menu.addAction(self.toggle_theme_menu_action)

        self.favorites_menu = menu_bar.addMenu(f"{FAVORITES_MENU_SYMBOL} &Favoriler")
        self.populate_favorites_menu()

        self.history_menu = menu_bar.addMenu(f"{HISTORY_SYMBOL} &Geçmiş")
        self.populate_history_menu()

        extra_info_menu = menu_bar.addMenu("&Ek Bilgiler")
        sunrise_sunset_action = QAction(f"{SUNRISE_SUNSET_SYMBOL} Gündoğumu & Günbatımı", self)
        sunrise_sunset_action.setStatusTip("Seçili şehir için gündoğumu ve günbatımı saatlerini gösterir")
        sunrise_sunset_action.triggered.connect(self.show_sunrise_sunset_details)
        extra_info_menu.addAction(sunrise_sunset_action)
        atmospheric_action = QAction(f"{ATMOSPHERE_SYMBOL} Atmosfer Detayları", self)
        atmospheric_action.setStatusTip("Nem, basınç gibi atmosferik detayları gösterir")
        atmospheric_action.triggered.connect(self.show_atmospheric_details)
        extra_info_menu.addAction(atmospheric_action)
        
        help_menu = menu_bar.addMenu("&Yardım")
        api_instructions_action = QAction(f"{INFO_SYMBOL} API Anahtarı &Talimatları", self)
        api_instructions_action.setStatusTip("OpenWeatherMap API anahtarının nasıl alınacağını gösterir")
        api_instructions_action.triggered.connect(self.show_api_instructions_dialog)
        help_menu.addAction(api_instructions_action)
        about_action = QAction(f"{ABOUT_SYMBOL} &Hakkında", self)
        about_action.setStatusTip(f"{APP_NAME} hakkında bilgi göster")
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
        self.update_toggle_theme_action_text()

    def populate_favorites_menu(self):
        self.favorites_menu.clear()
        favorites = get_favorite_cities()
        if favorites:
            for city_row in favorites:
                city_name = city_row['name']
                country_code = city_row['country']
                action_text = f"{city_name}" + (f", {country_code}" if country_code else "")
                action = QAction(action_text, self)
                action.triggered.connect(lambda checked, cn=city_name, cc=country_code: self.load_weather_from_menu(cn, cc))
                self.favorites_menu.addAction(action)
        else:
            no_fav_action = QAction("Favori şehir yok", self)
            no_fav_action.setEnabled(False)
            self.favorites_menu.addAction(no_fav_action)

    def populate_history_menu(self):
        self.history_menu.clear()
        recents = get_recent_searches()
        if recents:
            for city_row in recents:
                city_name = city_row['name']
                country_code = city_row['country']
                action_text = f"{city_name}" + (f", {country_code}" if country_code else "")
                action = QAction(action_text, self)
                action.triggered.connect(lambda checked, cn=city_name, cc=country_code: self.load_weather_from_menu(cn, cc))
                self.history_menu.addAction(action)
        else:
            no_hist_action = QAction("Arama geçmişi yok", self)
            no_hist_action.setEnabled(False)
            self.history_menu.addAction(no_hist_action)
            
    def load_weather_from_menu(self, city_name, country_code):
   
        search_term = f"{city_name},{country_code}" if country_code else city_name
        self.city_input.setText(search_term)
        self.fetch_weather_data(search_term)


    def degrees_to_cardinal(self, d):
        if d is None: return ""
        dirs = ["K", "KKD", "KD", "DKD", "D", "DGD", "GD", "GGD","G", "GGB", "GB", "BGB", "B", "BKB", "KB", "KKB"]
        try:
            ix = round(float(d) / (360. / len(dirs))) 
            return dirs[ix % len(dirs)]
        except (TypeError, ValueError): return ""


    def format_time_from_timestamp(self, timestamp, timezone_offset):
        if timestamp is None or timezone_offset is None: return "--:--"
        try:
            utc_dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
            local_dt = utc_dt + datetime.timedelta(seconds=int(timezone_offset)) # offset'i int yap
            return local_dt.strftime('%H:%M')
        except Exception as e:
            print(f"Zaman formatlama hatası: {e}")
            return "--:--"
        
    def show_sunrise_sunset_details(self):
        self.apply_styles()
        if self.last_current_data:
            city_name = self.last_current_data.get('name', 'Bilinmeyen Şehir')
            sys_data = self.last_current_data.get('sys', {})
            sunrise_ts = sys_data.get('sunrise')
            sunset_ts = sys_data.get('sunset')
            timezone_offset = self.last_current_data.get('timezone')
            sunrise_str = self.format_time_from_timestamp(sunrise_ts, timezone_offset)
            sunset_str = self.format_time_from_timestamp(sunset_ts, timezone_offset)
            QMessageBox.information(self, f"{city_name} - Gündoğumu/Günbatımı",
                                    f"<b>Gündoğumu:</b> {sunrise_str}\n"
                                    f"<b>Günbatımı:</b> {sunset_str}")
        else:
            QMessageBox.warning(self, "Bilgi Yok", "Gündoğumu ve günbatımı bilgilerini görmek için lütfen önce bir şehir arayın.")

    def show_atmospheric_details(self):
        self.apply_styles()
        if self.last_current_data:
            city_name = self.last_current_data.get('name', 'Bilinmeyen Şehir')
            main_data = self.last_current_data.get('main', {})
            humidity = main_data.get('humidity', '--')
            pressure = main_data.get('pressure', '--')
            visibility_km = "--"
            if 'visibility' in self.last_current_data:
                try:
                    visibility_km = f"{int(self.last_current_data['visibility']) / 1000:.1f} km"
                except (ValueError, TypeError):
                    visibility_km = "-- km"
            QMessageBox.information(self, f"{city_name} - Atmosfer Detayları",
                                    f"<b>Nem:</b> {humidity}%\n"
                                    f"<b>Basınç:</b> {pressure} hPa\n"
                                    f"<b>Görüş Mesafesi:</b> {visibility_km}")
        else:
            QMessageBox.warning(self, "Bilgi Yok", "Atmosferik detayları görmek için lütfen önce bir şehir arayın.")
            
    def update_toggle_theme_action_text(self):
        if hasattr(self, 'toggle_theme_menu_action'):
            symbol = THEME_MOON_SYMBOL if self.current_theme == 'light' else THEME_SUN_SYMBOL
            action_text = f"{symbol} {'Koyu' if self.current_theme == 'light' else 'Açık'} Temaya Geç"
            tooltip_text = "Koyu temaya geç" if self.current_theme == 'light' else "Açık temaya geç"
            self.toggle_theme_menu_action.setText(action_text)
            self.toggle_theme_menu_action.setStatusTip(tooltip_text)

    def show_about_dialog(self):
        self.apply_styles()
        QMessageBox.about(self,
                          f"{APP_NAME} Hakkında", 
                          f"<b>{APP_NAME}</b><br>" 
                          f"Sürüm: {APP_VERSION}<br><br>"
                          f"Bu uygulama OpenWeatherMap API'sini kullanarak hava durumu bilgilerini gösterir.<br><br>"
                          f"Veri Kaynağı: OpenWeatherMap<br>"
                          f"Tarih: {datetime.date.today().strftime('%d %B %Y')}")

    def show_api_instructions_dialog(self):
        self.apply_styles()
        instructions = (
            "OpenWeatherMap API Anahtarı Gereklidir.\n\n"
            "**Nasıl API Anahtarı Alınır?**\n"
            "1. openweathermap.org web sitesini ziyaret edin.\n"
            "2. Ücretsiz bir hesap oluşturun veya giriş yapın.\n"
            "3. Giriş yaptıktan sonra, kullanıcı adınıza tıklayarak açılan menüden 'My API keys' sekmesine gidin.\n"
            "4. Buradan API anahtarınızı kopyalayabilirsiniz.\n\n"
            "**Geçici Anahtar Kullanımı:**\n"
            "Uygulama ilk açıldığında veya API anahtarınız yoksa, "
            f"geçici bir anahtar (**{PROVIDED_API_KEY}**) kullanmanız önerilir. "
            "Bu anahtarın gelecekte çalışmama veya kısıtlanma ihtimali olduğunu unutmayın."
        )
        QMessageBox.information(self, "API Anahtarı Talimatları", instructions)

    def toggle_theme(self):
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.settings.setValue("theme", self.current_theme)
        self.apply_styles()
        self.update_app_icon() 
        self.update_theme_dependent_symbols()

    def apply_styles(self):
        theme = LIGHT_THEME_COLORS if self.current_theme == "light" else DARK_THEME_COLORS
        input_text_color_style = f"color: {theme.get('input_text_color', theme['text_color'])};" if self.current_theme == "dark" else ""
        weather_icon_placeholder_style = f"color: {theme['icon_placeholder_text_color']};"
        feels_like_style = f"color: {theme['feels_like_color']}; font-weight: bold;"
        menu_style = f"""
            QMenuBar {{
                background-color: {theme.get("menu_bar_bg", theme["frame_bg"])};
                color: {theme.get("menu_bar_text", theme["text_color"])};
            }}
            QMenuBar::item {{
                background-color: transparent; padding: 4px 8px;
            }}
            QMenuBar::item:selected {{
                background-color: {theme.get("menu_item_bg_selected", theme["button_hover_bg"])};
                color: {theme.get("menu_item_text_selected", theme["button_text"])};
            }}
            QMenu {{
                background-color: {theme.get("menu_bar_bg", theme["frame_bg"])};
                color: {theme.get("menu_bar_text", theme["text_color"])};
                border: 1px solid {theme["input_border"]};
            }}
            QMenu::item {{ padding: 4px 20px; }}
            QMenu::item:selected {{
                background-color: {theme.get("menu_item_bg_selected", theme["button_hover_bg"])};
                color: {theme.get("menu_item_text_selected", theme["button_text"])};
            }}
            QMenu::separator {{
                height: 1px; background-color: {theme["input_border"]};
                margin-left: 10px; margin-right: 5px;
            }}
        """
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {theme["window_bg"]}; }}
            QStatusBar {{ color: {theme["status_text_color"]}; font-size: 8pt;}}
            QStatusBar QLabel {{ color: {theme["status_text_color"]}; }}
            QLabel {{ color: {theme["text_color"]}; }} 
            QLabel#feelsLikeLabelDistinct {{ {feels_like_style} }}
            QLineEdit {{
                padding: 8px; border: 1px solid {theme["input_border"]}; border-radius: 4px;
                background-color: {theme["input_bg"]}; font-size: 11pt; {input_text_color_style}
            }}
            QPushButton {{
                background-color: {theme["button_bg"]}; color: {theme["button_text"]}; padding: 8px;
                border-radius: 4px; font-weight: bold; border: none;
            }}
            QPushButton:hover {{ background-color: {theme["button_hover_bg"]}; }}
            QPushButton:pressed {{ background-color: {theme["button_pressed_bg"]}; }}
            QFrame#currentWeatherFrame {{
                background-color: {theme["frame_bg"]}; border-radius: 8px; padding: 12px;
                border: 1px solid {theme["frame_border"]};
            }}
            QLabel#weatherIconLabel {{ {weather_icon_placeholder_style} }}
            QScrollArea#scrollArea {{ border: none; background-color: transparent; }}
            QScrollArea#scrollArea QWidget {{ background-color: transparent; }}
            QFrame.forecastCard {{
                background-color: {theme["forecast_card_bg"]}; border: 1px solid {theme["forecast_card_border"]};
                border-radius: 6px; padding: 8px; margin-bottom: 3px;
            }}
            QLabel.forecastDate {{ font-weight: bold; font-size: 10pt; color: {theme["forecast_date_text"]}; }}
            QLabel.forecastTemp {{ font-size: 9pt; color: {theme["forecast_temp_text"]}; }}
            QLabel[objectName^="condition_label"], 
            QLabel[objectName^="humidity_label"], QLabel[objectName^="wind_label"],
            QLabel[objectName^="pressure_label"], QLabel[objectName^="sunrise_label"], QLabel[objectName^="sunset_label"] 
            {{ color: {theme["text_color"]}; }}
            QInputDialog {{ background-color: {theme["frame_bg"]}; }}
            QInputDialog QLabel {{ color: {theme["text_color"]}; }}
            QMessageBox {{ background-color: {theme["frame_bg"]}; }}
            QMessageBox QLabel {{ color: {theme["text_color"]}; }}
            {menu_style} 
        """)

    def handle_initial_api_key_setup(self):
        dialog_title = "Hoş Geldiniz! API Anahtarı Gerekli"
        instructions = (
            "Merhaba! " + APP_NAME + " uygulamasını kullanmak için bir OpenWeatherMap API Anahtarı gereklidir.\n\n"
            "**Nasıl API Anahtarı Alınır?**\n"
            "1. openweathermap.org web sitesini ziyaret edin.\n"
            "2. Ücretsiz bir hesap oluşturun veya giriş yapın.\n"
            "3. Giriş yaptıktan sonra, kullanıcı adınıza tıklayarak açılan menüden 'My API keys' sekmesine gidin.\n"
            "4. Buradan API anahtarınızı kopyalayabilirsiniz.\n\n"
            "**Geçici Anahtar Kullanımı:**\n"
            "Eğer hemen bir anahtar almakla uğraşmak istemiyorsanız, aşağıdaki geçici anahtarı kullanabilirsiniz. "
            "Bu anahtarın gelecekte çalışmama veya kısıtlanma ihtimali olduğunu unutmayın.\n"
            f"Önerilen Geçici Anahtar: **{PROVIDED_API_KEY}**\n\n"
            "Lütfen API anahtarınızı aşağıdaki alana girin veya önerilen geçici anahtarı kullanın:"
        )
        self.apply_styles() 
        text, ok = QInputDialog.getText(self, dialog_title, instructions,
                                        QLineEdit.Normal, PROVIDED_API_KEY)
        if ok and text.strip():
            self.api_key = text.strip()
            self.settings.setValue("api_key", self.api_key)
            self.statusBar().showMessage("API Anahtarı başarıyla kaydedildi.", 3000)
            QMessageBox.information(self, "API Anahtarı", f"API anahtarınız ('{self.api_key[:7]}...') kaydedildi.\nUygulama şimdi bu anahtarı kullanacak.")
            self.load_weather_for_last_city()
        else:
            self.api_key = DEFAULT_API_KEY_PLACEHOLDER
            self.settings.setValue("api_key", self.api_key)
            message = "API Anahtarı girilmedi. Uygulama API anahtarı olmadan hava durumu verilerini alamaz."
            if ok and not text.strip():
                message = "API Anahtarı boş bırakılamaz. Uygulama API anahtarı olmadan hava durumu verilerini alamaz."
            self.apply_styles() 
            QMessageBox.warning(self, "API Anahtarı Gerekli", message)
            self.statusBar().showMessage("API Anahtarı gerekli. Ayarlardan giriniz.", 5000)
            self.display_initial_message("API Anahtarı gerekli. Lütfen bir anahtar girin.")

    def prompt_for_api_key_change(self):
        current_key_in_settings = self.settings.value("api_key", DEFAULT_API_KEY_PLACEHOLDER)
        key_to_display_in_dialog = PROVIDED_API_KEY
        if current_key_in_settings and current_key_in_settings != DEFAULT_API_KEY_PLACEHOLDER:
            key_to_display_in_dialog = current_key_in_settings
        instructions = (
            "OpenWeatherMap API Anahtarı Ayarı.\n\n"
            f"Mevcut anahtarınız (eğer varsa): {key_to_display_in_dialog if key_to_display_in_dialog != PROVIDED_API_KEY else '(önerilen geçici anahtar)'}\n"
            "Değiştirmek istemiyorsanız ve mevcut anahtarınız geçerliyse 'İptal'e basebilirsiniz.\n\n"
            "Nasıl API Anahtarı Alınır?\n"
            "1. openweathermap.org web sitesini ziyaret edin.\n"
            "2. Ücretsiz bir hesap oluşturun veya giriş yapın.\n"
            "3. 'My API keys' sekmesinden anahtarınızı alın.\n\n"
            f"Alternatif Geçici Anahtar (eğer kendinize ait yoksa): {PROVIDED_API_KEY}\n\n"
            "Lütfen yeni API anahtarınızı girin veya mevcut olanı düzenleyin:"
        )
        self.apply_styles() 
        text, ok = QInputDialog.getText(self, "API Anahtarını Değiştir", instructions,
                                        QLineEdit.Normal, key_to_display_in_dialog)
        if ok and text.strip():
            new_key = text.strip()
            if new_key != self.api_key: 
                self.api_key = new_key
                self.settings.setValue("api_key", self.api_key)
                self.statusBar().showMessage("API Anahtarı güncellendi.", 3000)
                QMessageBox.information(self,"API Anahtarı", "API anahtarınız güncellendi.")
                self.load_weather_for_last_city() 
            else:
                self.statusBar().showMessage("API Anahtarı değiştirilmedi.", 3000)
            return True 
        elif ok and not text.strip():
            QMessageBox.warning(self, "API Anahtarı Hatası", "API Anahtarı boş bırakılamaz.")
            return False 
        else: 
            self.statusBar().showMessage("API anahtarı değiştirme işlemi iptal edildi.", 3000)
            return False

    def load_weather_for_last_city(self):
        if self.api_key and self.api_key != DEFAULT_API_KEY_PLACEHOLDER:
            last_city_info = self.settings.value("last_city_info", None)
            city_to_load = "Istanbul" # Varsayılan
            country_to_load = ""
            if last_city_info and isinstance(last_city_info, dict):
                city_to_load = last_city_info.get("name", "Istanbul")
                country_to_load = last_city_info.get("country", "")
            
            display_text = f"{city_to_load},{country_to_load}" if country_to_load else city_to_load
            self.city_input.setText(display_text)
            self.fetch_weather_data(city_to_load, country_to_load) 
        else:
            self.statusBar().showMessage("API Anahtarı eksik veya geçersiz.", 5000)
            self.display_initial_message("API Anahtarı yapılandırılmadı. Lütfen ayarlardan girin.")

    def display_initial_message(self, message="Lütfen bir şehir arayın veya API anahtarı girin."):
        self.last_current_data = None
        self.current_city_tuple = None
        self.favorite_button.setVisible(False)
        self.city_name_label.setText(APP_NAME) 
        self.temp_label.setText("--°C")
        self.condition_label.setText(message)
        self.weather_icon_label.setText("🔑") 
        self.weather_icon_label.setFont(QFont("Arial", 30)) 
        self.feels_like_label.setText("Hissedilen: --°C")
        self.humidity_label.setText("Nem: --%")
        self.wind_label.setText("Rüzgar: -- m/s")
        self.pressure_label.setText("Basınç: -- hPa")
        if hasattr(self, 'sunrise_label'): self.sunrise_label.setText("GD: --:--")
        if hasattr(self, 'sunset_label'): self.sunset_label.setText("GB: --:--")
        for i in reversed(range(self.forecast_layout_container.count())):
            widget_item = self.forecast_layout_container.itemAt(i)
            if widget_item:
                widget = widget_item.widget()
                if widget: widget.deleteLater()
                else: self.forecast_layout_container.removeItem(widget_item)
        self.populate_favorites_menu() # Menüleri de güncelle
        self.populate_history_menu()

    def fetch_weather_data_for_current_city(self):
        city_text = self.city_input.text().strip()
        if not city_text:
            QMessageBox.warning(self, "Giriş Hatası", "Lütfen bir şehir adı girin.")
            return
        
        parts = city_text.split(',')
        city_name = parts[0].strip()
        country_code = parts[1].strip() if len(parts) > 1 else None
        self.fetch_weather_data(city_name, country_code)


    def fetch_weather_data(self, city, country_code=None):
        if not self.api_key or self.api_key == DEFAULT_API_KEY_PLACEHOLDER:
            self.statusBar().showMessage("API Anahtarı eksik. Lütfen ayarlardan girin.", 5000)
            if self.prompt_for_api_key_change(): 
                 self.fetch_weather_data(city, country_code) 
            else: 
                self.display_initial_message("API Anahtarı girilmedi veya geçersiz.")
            return

        query_param = f"{city},{country_code}" if country_code else city
        self.statusBar().showMessage(f"{query_param} için hava durumu alınıyor...", 0)
        self.weather_icon_label.setText("🔄"); self.weather_icon_label.setFont(QFont("Arial", 30))
        QApplication.processEvents()
        try:
            current_weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={query_param}&appid={self.api_key}&units=metric&lang=tr"
            response_current = requests.get(current_weather_url, timeout=10)
            response_current.raise_for_status()
            current_data = response_current.json()
            
            fetched_city_name = current_data.get('name')
            fetched_country_code = current_data.get('sys', {}).get('country')
            self.last_current_data = current_data 
            self.current_city_tuple = (fetched_city_name, fetched_country_code)

            add_or_update_city_search(fetched_city_name, fetched_country_code)
            self.settings.setValue("last_city_info", {"name": fetched_city_name, "country": fetched_country_code})


            forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={query_param}&appid={self.api_key}&units=metric&lang=tr"
            response_forecast = requests.get(forecast_url, timeout=10)
            response_forecast.raise_for_status()
            forecast_data = response_forecast.json()
            
            self.update_ui(current_data, forecast_data)
            self.statusBar().showMessage(f"{query_param} için hava durumu güncellendi.", 3000)
            self.favorite_button.setVisible(True)
            self.update_favorite_button_status()
            self.populate_favorites_menu()
            self.populate_history_menu()

        except requests.exceptions.HTTPError as http_err:
            self.last_current_data = None 
            self.current_city_tuple = None
            self.favorite_button.setVisible(False)
            self.weather_icon_label.setText("⚠") 
            if http_err.response.status_code == 401: 
                QMessageBox.critical(self, "API Hatası", "Girilen API Anahtarı geçersiz veya hatalı.\nLütfen geçerli bir anahtar girin.")
                self.statusBar().showMessage("Geçersiz API Anahtarı.", 5000)
                if self.prompt_for_api_key_change(): 
                    self.fetch_weather_data(city, country_code) 
                else:
                    self.display_initial_message("API Anahtarı geçersiz.")
            elif http_err.response.status_code == 404: 
                QMessageBox.warning(self, "Bulunamadı", f"'{query_param}' şehri bulunamadı. Lütfen şehir adını kontrol edin.")
                self.statusBar().showMessage(f"'{query_param}' şehri bulunamadı.", 5000)
                self.display_initial_message(f"'{query_param}' bulunamadı.")
            else: 
                QMessageBox.critical(self, "HTTP Hatası", f"Bir HTTP hatası oluştu: {http_err}")
                self.statusBar().showMessage(f"HTTP Hatası: {http_err.response.status_code}", 5000)
                self.display_initial_message("Servis hatası.")
        except requests.exceptions.RequestException as e: 
            self.last_current_data = None 
            self.current_city_tuple = None
            self.favorite_button.setVisible(False)
            self.weather_icon_label.setText("❌") 
            QMessageBox.critical(self, "Bağlantı Sorunu", f"Hava durumu bilgisi alınamadı. İnternet bağlantınızı kontrol edin.\nDetay: {e}")
            self.statusBar().showMessage("Bağlantı Sorunu.", 5000)
            self.display_initial_message("Bağlantı sorunu.")
        except Exception as e: 
            self.last_current_data = None 
            self.current_city_tuple = None
            self.favorite_button.setVisible(False)
            self.weather_icon_label.setText("❗") 
            QMessageBox.critical(self, "Genel Hata", f"Beklenmedik bir hata oluştu: {e}")
            self.statusBar().showMessage("Beklenmedik bir hata.", 5000)
            self.display_initial_message("Beklenmedik hata.")
            import traceback
            print(traceback.format_exc())

    def update_ui(self, current_data, forecast_data):
        self.city_name_label.setText(f"{current_data.get('name', 'N/A')}, {current_data.get('sys', {}).get('country', 'N/A')}")
        self.temp_label.setText(f"{current_data.get('main', {}).get('temp', '--'):.0f}°C")
        weather_info_list = current_data.get('weather', [{}])
        if weather_info_list and weather_info_list[0]:
            self.condition_label.setText(weather_info_list[0].get('description', '---').capitalize())
            icon_code = weather_info_list[0].get('icon')
            if icon_code:
                icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
                try:
                    image_data = requests.get(icon_url, timeout=5).content
                    pixmap = QPixmap(); pixmap.loadFromData(image_data)
                    self.weather_icon_label.setPixmap(pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                except Exception as e:
                    self.weather_icon_label.setText("🖼🚫"); 
                    self.statusBar().showMessage(f"Ana ikon yüklenemedi: {e}", 3000)
                    print(f"Ana ikon yüklenemedi: {e}")
            else: self.weather_icon_label.setText("...")
        else:
            self.condition_label.setText("---"); self.weather_icon_label.setText("...")
        main_data = current_data.get('main', {})
        self.feels_like_label.setText(f"Hissedilen: {main_data.get('feels_like', '--'):.0f}°C")
        self.humidity_label.setText(f"Nem: {main_data.get('humidity', '--')}%")
        self.pressure_label.setText(f"Basınç: {main_data.get('pressure', '--')} hPa")
        wind_data = current_data.get('wind', {})
        wind_speed = wind_data.get('speed', '--')
        wind_deg = wind_data.get('deg')
        wind_direction_str = self.degrees_to_cardinal(wind_deg)
        try:
            self.wind_label.setText(f"Rüzgar: {float(wind_speed):.1f} m/s {wind_direction_str}")
        except (ValueError, TypeError):
             self.wind_label.setText(f"Rüzgar: {wind_speed} m/s {wind_direction_str}")
        sys_data = current_data.get('sys', {})
        sunrise_ts = sys_data.get('sunrise')
        sunset_ts = sys_data.get('sunset')
        timezone_offset = current_data.get('timezone')
        self.sunrise_label.setText(f"GD: {self.format_time_from_timestamp(sunrise_ts, timezone_offset)}")
        self.sunset_label.setText(f"GB: {self.format_time_from_timestamp(sunset_ts, timezone_offset)}")
        for i in reversed(range(self.forecast_layout_container.count())):
            widget_item = self.forecast_layout_container.itemAt(i)
            if widget_item:
                widget = widget_item.widget();
                if widget: widget.deleteLater()
                else: self.forecast_layout_container.removeItem(widget_item)
        processed_days = set()
        forecast_items_added = 0
        api_timezone_offset_seconds = forecast_data.get('city', {}).get('timezone', 0)
        for item in forecast_data.get('list', []):
            if forecast_items_added >= 5: break
            dt_utc = datetime.datetime.fromtimestamp(item.get('dt', 0), tz=datetime.timezone.utc)
            local_dt = dt_utc + datetime.timedelta(seconds=api_timezone_offset_seconds)
            day_key = local_dt.strftime("%Y-%m-%d")
            if local_dt.date() == datetime.datetime.now(datetime.timezone.utc).astimezone(local_dt.tzinfo).date():
                continue 
            if day_key not in processed_days:
                processed_days.add(day_key)
                forecast_items_added += 1
                day_name_tr_map = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
                day_name_tr = day_name_tr_map[local_dt.weekday()]
                date_display = local_dt.strftime(f"%d %b ({day_name_tr})")
                temp_daily = f"{item.get('main', {}).get('temp', '--'):.0f}°C"
                daily_weather_info = item.get('weather', [{}])
                icon_daily_code = daily_weather_info[0].get('icon') if daily_weather_info and daily_weather_info[0] else None
                desc_daily = daily_weather_info[0].get('description', 'N/A').capitalize() if daily_weather_info and daily_weather_info[0] else "N/A"
                card = QFrame(); card.setObjectName("forecastCard")
                card_layout = QGridLayout(card)
                date_label = QLabel(date_display); date_label.setObjectName("forecastDate")
                card_layout.addWidget(date_label, 0, 0, 1, 2)
                icon_label_d = QLabel(); icon_label_d.setFixedSize(40, 40); icon_label_d.setAlignment(Qt.AlignCenter)
                if icon_daily_code:
                    try:
                        d_icon_url = f"http://openweathermap.org/img/wn/{icon_daily_code}.png"
                        d_img_data = requests.get(d_icon_url, timeout=3).content
                        d_pixmap = QPixmap(); d_pixmap.loadFromData(d_img_data)
                        icon_label_d.setPixmap(d_pixmap.scaled(40,40,Qt.KeepAspectRatio,Qt.SmoothTransformation))
                    except Exception as e_icon: 
                        icon_label_d.setText("🖼🚫");
                        self.statusBar().showMessage(f"Tahmin ikonu {icon_daily_code} yüklenemedi.", 2000)
                        print(f"Tahmin ikonu yüklenemedi ({icon_daily_code}): {e_icon}")
                else: icon_label_d.setText(".")
                card_layout.addWidget(icon_label_d, 1, 0)
                temp_label_d = QLabel(temp_daily); temp_label_d.setObjectName("forecastTemp"); temp_label_d.setFont(QFont("Arial", 10, QFont.Bold))
                card_layout.addWidget(temp_label_d, 1, 1)
                desc_label_d = QLabel(desc_daily); desc_label_d.setFont(QFont("Arial", 9)); desc_label_d.setObjectName("forecastDesc")
                card_layout.addWidget(desc_label_d, 2, 0, 1, 2)
                self.forecast_layout_container.addWidget(card)
        if forecast_items_added > 0:
             self.forecast_layout_container.addStretch()

    def toggle_current_city_favorite(self):
        if self.current_city_tuple:
            city_name, country_code = self.current_city_tuple
            new_status = toggle_favorite_status(city_name, country_code)
            self.update_favorite_button_status()
            self.populate_favorites_menu() 
            status_message = f"'{city_name}' favorilerden {'çıkarıldı' if not new_status else 'eklendi'}."
            self.statusBar().showMessage(status_message, 3000)
        else:
            self.statusBar().showMessage("Favori işlemi için geçerli bir şehir yok.", 3000)


    def update_favorite_button_status(self):
        if self.current_city_tuple:
            city_name, country_code = self.current_city_tuple
            if is_city_favorite(city_name, country_code):
                self.favorite_button.setText(FAVORITE_FULL_SYMBOL)
                self.favorite_button.setToolTip(f"{city_name} favorilerden çıkar")
            else:
                self.favorite_button.setText(FAVORITE_EMPTY_SYMBOL)
                self.favorite_button.setToolTip(f"{city_name} favorilere ekle")
            self.favorite_button.setVisible(True)
        else:
            self.favorite_button.setVisible(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WeatherApp()
    window.show()
    sys.exit(app.exec_())