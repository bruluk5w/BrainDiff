from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QCheckBox


class VolumeListItem(QWidget):
    def __init__(self, volume_idx: int, parent=None):
        super().__init__(parent)
        self.__volume_idx = volume_idx
        self.__horizontal_layout = QHBoxLayout()
        self.__label = QLabel()
        self.__check_box = QCheckBox()
        self.__horizontal_layout.addWidget(self.__check_box)
        self.__horizontal_layout.addWidget(self.__label)
        self.setLayout(self.__horizontal_layout)

    @property
    def idx(self):
        return self.__volume_idx

    def set_text(self, text: str):
        self.__label.setText(text)
