from persistence_manager import PersistenceManager
from schedule import Schedule
from settings import Settings, ThemeManager
from blocks import CustomBlocks
from main_window import MainWindow
from utils import GUIUtils
from notification_manager import NotificationManager

from PyQt5.QtWidgets import QApplication
import sys


def main():
    # create qt application
    app = QApplication(sys.argv)

    # load settings + persistence
    persistence_manager = PersistenceManager()

    settings = Settings()
    settings_data = persistence_manager.load_settings()
    settings.from_dict(settings_data)

    customs = CustomBlocks()
    templates = persistence_manager.load_custom_blocks()
    customs.from_dict(templates)

    # initialise schedule
    schedule = Schedule(settings)
    schedule_data = persistence_manager.load_data()
    schedule.from_dict(schedule_data)

    # gui setup
    theme_manager = ThemeManager()
    gui_utils = GUIUtils(theme_manager, settings)

    app.setStyle("Fusion")

    window = MainWindow(
        schedule,
        settings,
        persistence_manager,
        gui_utils,
        customs
    )
    window.show()
    
    notification_manager = NotificationManager(
                                schedule=schedule,
                                settings=settings,
                                utils=gui_utils,
                                parent=window
                            )

    gui_utils.apply_theme()

    # start qt event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
