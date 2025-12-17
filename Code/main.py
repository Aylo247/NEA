from persitencemanager import PersistenceManager
from schedule import Schedule
from settings import Settings, ThemeManager
from UI import MainWindow, SettingsView
from PyQt5.QtWidgets import QApplication
import sys

def main():
    app = QApplication(sys.argv)

    settings = Settings()
    persistence = PersistenceManager()
    thememanager = ThemeManager()

    # Load saved settings if they exist
    loaded = persistence.load_settings()
    if loaded:
        settings.from_dict(loaded)
    window = SettingsView(settings, persistence, thememanager)
    window.setWindowTitle("Settings Test")
    window.resize(400, 300)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 
