from PySide6.QtCore import QSize
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QSizePolicy, QStyle


class VolumeListItem(QWidget):
    def __init__(self, volume_idx: int, parent=None):
        super().__init__(parent)
        self.__volume_idx = volume_idx
        self.__horizontal_layout = QHBoxLayout()
        self.__label = QLabel()
        self.__icon_label = QLabel()
        self.__horizontal_layout.addWidget(self.__icon_label)
        self.__horizontal_layout.addWidget(self.__label)
        self.setLayout(self.__horizontal_layout)
        self.selected = False
        self.sizePolicy().setHorizontalPolicy(QSizePolicy.Minimum)

    @property
    def idx(self):
        return self.__volume_idx

    def set_text(self, text: str):
        self.__label.setText(text)

    @property
    def selected(self):
        return self.__selected

    @selected.setter
    def selected(self, value: bool):
        self.__selected = value
        icon = self.style().standardIcon(QStyle.SP_DialogApplyButton if self.selected else QStyle.SP_DialogCancelButton)
        self.__icon_label.setPixmap(icon.pixmap(QSize(10, 10)))
