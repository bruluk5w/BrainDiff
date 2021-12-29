from typing import Optional

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QMainWindow

from LoadingWidget import LoadingWidget
from MainWidget import MainWidget

__window: Optional[QMainWindow] = None
__app: Optional[QApplication] = None


def main():
    global __window, __app
    # every QT app needs an app
    __app = QApplication(['QVTKRenderWindowInteractor'])
    __app.setApplicationDisplayName('BrainDiff')
    __app.setApplicationName('BrainDiff')

    __window = QMainWindow()

    loading_widget = LoadingWidget(lambda: start_app(loading_widget.result))

    __window.setCentralWidget(loading_widget)
    __window.show()
    __app.exec()


def start_app(result):
    global __window, __app
    if result is None:
        print("No data found. Exiting.")
        __app.quit()
        return

    data, image = result
    app_widget = MainWidget(__app, image, data)
    # app_widget.set_volume(data[0])
    __window.setCentralWidget(app_widget)
    screen_size = __app.primaryScreen().availableGeometry().size()
    __window.resize(screen_size * 0.7)
    pos = screen_size * 0.15
    __window.move(pos.width(), pos.height())


if __name__ == "__main__":
    main()
