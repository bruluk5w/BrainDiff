from typing import Callable

from PySide6.QtWidgets import QVBoxLayout, QWidget, QProgressBar, QLabel

from DataLoader import DataLoader


class LoadingWidget(QWidget):

    def __init__(self, cb: Callable[[], None]):
        super().__init__()
        self.__data_loader = DataLoader()
        self.__cb = cb
        self.__ready = False
        self.__label = QLabel()
        self.__label.setText("Loading...")
        self.vertical_layout = QVBoxLayout(self)
        self.vertical_layout.addWidget(self.__label)
        self.__progress_bar = QProgressBar()
        self.__progress_bar.setMinimum(0)
        self.__progress_bar.setMaximum(len(self.__data_loader))
        self.__progress_bar.setValue(0)
        self.__data_loader.progress.connect(lambda p: self.__progress_bar.setValue(p))
        self.vertical_layout.addWidget(self.__progress_bar)
        self.__data_loader.done.connect(self.__done)
        self.__data_loader.start()

    @property
    def result(self):
        if len(self.__data_loader) == 0 or not self.__done:
            return None

        return self.__data_loader.data, self.__data_loader.image

    def __done(self):
        self.__ready = True
        if self.__cb is not None:
            self.__cb()
