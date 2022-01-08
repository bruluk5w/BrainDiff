from typing import NamedTuple, List, Sequence

from PySide6.QtGui import QPalette, Qt, QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider
from vtkmodules.vtkCommonDataModel import vtkColor3ub

from common import Delegate
from functools import partial


def seq_to_qt_color(col: Sequence[int]) -> QColor:
    assert len(col) >= 3, all(0 <= c <= 255 for c in col)
    return QColor(col[0], col[1], col[2])


def seq_to_vtk_color(col: Sequence[int]) -> vtkColor3ub:
    assert len(col) >= 3, all(0 <= c <= 255 for c in col)
    vtk_color = vtkColor3ub()
    vtk_color[0] = col[0]
    vtk_color[1] = col[1]
    vtk_color[2] = col[2]
    return vtk_color


LabelSetting = NamedTuple('LabelSetting', (
    ('label', int),
    ('name', str),
    ('default_color', vtkColor3ub)
))


class LabelColorWidget(QWidget):
    """
    Provides editing for colors per each integer label
    """

    def __init__(self, label_settings: List[LabelSetting], parent=None):
        super().__init__(parent)
        self.__label_settings = label_settings
        self.__on_opacity_changed = Delegate()
        self.__on_color_changed = Delegate()

        self.__label_opacities = [0 for i in range(len(label_settings))]
        self.__label_colors = []
        # Iso Opacity Sliders
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(0)

        self.__sliders = []
        palette = QPalette()
        for i, label_setting in enumerate(self.__label_settings):
            self.__label_colors.append(label_setting.default_color)

            iso_name = QLabel()
            iso_name.setText(' ' + label_setting.name)
            iso_name.setAutoFillBackground(True)
            self.layout().addWidget(iso_name)

            """
            palette.setColor(iso_name.backgroundRole(),
                             QColor(self.__color_list[i][0] * 255, self.__color_list[i][1] * 255, self.__color_list[i][2] * 255))
            # Make Text Black or White depending on if color is mostly bright or mostly dark
            if self.__color_list[i][0] + self.__color_list[i][1] + self.__color_list[i][2] > 1.5:
                palette.setColor(iso_name.foregroundRole(), "Black")
            else:
                palette.setColor(iso_name.foregroundRole(), "Ghost White")
            iso_name.setPalette(palette)
            """

            slider = QSlider(Qt.Horizontal)
            palette.setColor(slider.backgroundRole(), seq_to_qt_color(label_setting.default_color))
            slider.setPalette(palette)
            slider.setAutoFillBackground(True)
            slider.setTracking(False)
            slider.setMinimum(0)
            slider.setMaximum(255)
            slider.setValue(0)
            slider.valueChanged.connect(partial(self.__handle_opacity_changed, i))
            self.layout().addWidget(slider)
            self.__sliders.append(slider)

    @property
    def opacities(self):
        return self.__label_opacities

    @property
    def colors(self):
        return self.__label_colors

    @property
    def opacity_changed(self):
        return self.__on_opacity_changed

    @opacity_changed.setter
    def opacity_changed(self, value):
        assert value is self.__on_opacity_changed

    @property
    def color_changed(self):
        return self.__on_color_changed

    @color_changed.setter
    def color_changed(self, value):
        assert value is self.__on_color_changed

    def __handle_opacity_changed(self, idx, value):
        self.__label_opacities[idx] = value
        self.opacity_changed(idx, value)

    def __handle_color_changed(self, idx, color: QColor):
        self.__label_colors[idx] = seq_to_vtk_color(color)
        self.color_changed(idx, color)
