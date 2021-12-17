from typing import Optional

from PySide6.QtWidgets import QApplication, QMainWindow, QProgressBar
from PySide6.QtCore import SIGNAL
from MainWidget import MainWidget
from DataLoader import DataLoader

__window: Optional[QMainWindow] = None
__app: Optional[QApplication] = None
__data_loader: Optional[QApplication] = None


def main():
    global __window, __app, __data_loader
    # every QT app needs an app
    __app = QApplication(['QVTKRenderWindowInteractor'])
    __window = QMainWindow()
    progress_bar = QProgressBar()
    progress_bar.setMinimum(0)
    __window.setCentralWidget(progress_bar)

    __data_loader = DataLoader()
    progress_bar.setMaximum(len(__data_loader))
    __data_loader.progress.connect(lambda p: progress_bar.setValue(p))
    __data_loader.done.connect(start_app)
    __data_loader.start()
    __window.show()
    __app.exec()


def start_app():
    global __window, __app,  __data_loader
    if len(__data_loader) == 0:
        print("No data found. Exiting.")
        __app.quit()
        return

    data = __data_loader.data
    image = __data_loader.image
    __data_loader = None
    app_widget = MainWidget(__app, image)
    app_widget.set_volume(data[0])
    __window.setCentralWidget(app_widget)


if __name__ == "__main__":
    main()
