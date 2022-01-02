from typing import Optional

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QApplication, QMenu

from LoadingWidget import LoadingWidget
from MainWidget import MainWidget
from settings import Settings
from settings.Popup import Popup


class MainWindow(QMainWindow):
    def __init__(self, app: QApplication,  parent=None):
        super().__init__(parent)
        self.__loading_widget = LoadingWidget(lambda: self.start_app(self.__loading_widget.result))
        self.__main_widget: Optional[MainWidget] = None
        self.__app = app
        self.__settings = Settings()
        self.__settings.gpu_mem_limit_changed += self.gpu_mem_limit_changed
        self._create_actions()
        self._create_menu_bar()
        self.setCentralWidget(self.__loading_widget)
        self.show()

    def start_app(self, result):
        if result is None:
            print("No data found. Exiting.")
            self.__app.quit()
            return

        self.__loading_widget = None

        data, image = result
        self.__main_widget = MainWidget(image, data, self.__settings.gpu_mem_limit)
        self.setCentralWidget(self.__main_widget)
        screen_size = self.__app.primaryScreen().availableGeometry().size()
        self.resize(screen_size * 0.7)
        pos = screen_size * 0.15
        self.move(pos.width(), pos.height())

    def _create_actions(self):
        self._set_gpu_mem_action = QAction("&Set GPU Memory Usage", self)
        self._set_gpu_mem_action.triggered.connect(self.__settings.set_gpu_mem_limit_ui)

    def _create_menu_bar(self):
        menu = self.menuBar()
        settings = menu.addMenu("&Settings")
        settings.addAction(self._set_gpu_mem_action)

    def gpu_mem_limit_changed(self, limit: int):
        if self.__main_widget is not None:
            self.__main_widget.gpu_mem_limit_changed(limit)

    def closeEvent(self, event):
        super().closeEvent(event)
        self.__main_widget.close()
        Popup.close_all()
