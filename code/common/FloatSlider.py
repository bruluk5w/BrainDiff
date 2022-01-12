from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QSlider, QHBoxLayout, QLabel
from .Delegate import Delegate
from .LabelColorWidget import clamp

RANGE_MAX = 1 << 30
RANGE_MIN = -RANGE_MAX
RANGE = RANGE_MAX - RANGE_MIN


class FloatSlider(QWidget):

    def __init__(self, value: float = 0, minimum: float = 0, maximum: float = 100, orientation=Qt.Horizontal,
                 parent=None):
        super().__init__(parent)
        assert minimum <= value <= maximum
        self._slider = QSlider(orientation)
        self._slider.setMinimum(RANGE_MIN)
        self._slider.setMaximum(RANGE_MAX)
        self._slider.valueChanged.connect(self.handle_value_changed)
        self._value_changed = Delegate()
        self._min = float(minimum)
        self._max = float(maximum)
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self._slider)
        self._label = QLabel()
        self.layout().addWidget(self._label)
        self.set_value(value)

    def set_interval(self, minimum, maximum):
        assert minimum <= maximum
        v = self.value
        self._min = float(minimum)
        self._max = float(maximum)
        self.set_value(v)

    @property
    def range(self) -> float:
        return self._max - self._min

    @property
    def value(self) -> float:
        return self._min + self.range * (float(self._slider.value()) - RANGE_MIN) / RANGE

    def handle_value_changed(self, value):
        v = self.value
        self._set_label(v)
        self._value_changed(v)

    def set_value(self, value):
        value = clamp(value, self._min, self._max)
        if self.range == 0:
            v = RANGE_MIN
        else:
            v = RANGE_MIN + RANGE * (value - self._min) / self.range

        self._slider.setValue(round(v))
        self._set_label(self.value)

    def _set_label(self, value):
        self._label.setText("{:.2f}".format(value))

    @property
    def value_changed(self):
        return self._value_changed

    @value_changed.setter
    def value_changed(self, value):
        assert value is self._value_changed
