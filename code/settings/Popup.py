from typing import Callable, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QGridLayout


class Popup(QWidget):
    popups: List['Popup'] = []

    def __init__(self, cb: Callable[[], None], title: str = None, parent=None):
        super().__init__(parent)
        self.__cb = cb
        self.setLayout(QGridLayout())
        self.adjustSize()
        self.setWindowFlags(Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)
        self.setWindowTitle(title)
        Popup.popups.append(self)

    def closeEvent(self, event):
        super().closeEvent(event)
        Popup.popups.remove(self)
        if self.__cb is not None:
            self.__cb()

    @classmethod
    def close_all(cls):
        for p in cls.popups:
            p.close()
