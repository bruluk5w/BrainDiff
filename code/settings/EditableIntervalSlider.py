from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSlider, QHBoxLayout, QSpinBox, QSizePolicy, QLabel


class EditableIntervalSlider(QWidget):
    def __init__(self, value=0, minimum=0, maximum=100, parent=None, orientation=Qt.Horizontal, tracking=False):
        super().__init__(parent)
        assert minimum <= value <= maximum
        self.__slider = QSlider(orientation)
        self.__slider.setTracking(tracking)
        self.__slider.setMinimum(minimum)
        self.__slider.setMaximum(maximum)
        self.__slider.setValue(value)
        self.__main_layout = QVBoxLayout()
        self.sizePolicy().setVerticalPolicy(QSizePolicy.Minimum)
        self.setLayout(self.__main_layout)
        self.__main_layout.addWidget(self.__slider)
        self.__horizontal_layout = QHBoxLayout()
        self.__main_layout.addLayout(self.__horizontal_layout)
        self.__min_edit = QSpinBox()
        self.__min_edit.setAccelerated(True)
        self.__min_edit.setMaximum(1 << 30)
        self.__min_edit.setValue(minimum)
        self.__horizontal_layout.addWidget(self.__min_edit, alignment=Qt.AlignLeft | Qt.AlignTop)
        self.__value_label = QLabel()
        self.__value_label.setText(str(self.__slider.value()))
        self.__slider.sliderMoved.connect(self.__slider_moved)
        self.__horizontal_layout.addWidget(self.__value_label)
        self.__min_edit.sizePolicy().setHorizontalPolicy(QSizePolicy.Maximum)
        self.__max_edit = QSpinBox()
        self.__max_edit.setAccelerated(True)
        self.__max_edit.setMaximum(1 << 30)
        self.__max_edit.setValue(maximum)
        self.__horizontal_layout.addWidget(self.__max_edit, alignment=Qt.AlignRight | Qt.AlignTop)

        self.__min_edit.valueChanged.connect(self.__set_minimum)
        self.__max_edit.valueChanged.connect(self.__set_maximum)

    @property
    def value_changed(self):
        return self.__slider.valueChanged

    def set_value(self, value):
        if value < self.__min_edit.value():
            self.__set_minimum(value, force=True)
        if value > self.__max_edit.value():
            self.__set_maximum(value, force=True)

        self.__slider.setValue(value)
        self.__slider_moved(value)

    def __set_minimum(self, value, force=False):
        if force:
            self.__min_edit.setValue(value)

        if value > self.__max_edit.value():
            self.__max_edit.setValue(value)

        if value > self.__slider.value():
            self.__slider.setValue(value)
            self.__slider_moved(value)

        self.__slider.setMinimum(value)

    def __set_maximum(self, value, force=False):
        if force:
            self.__max_edit.setValue(value)

        if value < self.__min_edit.value():
            self.__min_edit.setValue(value)

        if value < self.__slider.value():
            self.__slider.setValue(value)
            self.__slider_moved(value)

        self.__slider.setMaximum(value)

    def __slider_moved(self, pos):
        self.__value_label.setText(str(pos))
