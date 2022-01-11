from functools import partial
from typing import NamedTuple, List, Sequence

from PySide6.QtGui import Qt, QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QPushButton, QSizePolicy, QColorDialog
from vtkmodules.vtkCommonDataModel import vtkColor3ub

from .Delegate import Delegate

clamp = (lambda x, a, b: min(max(x, a), b))


def seq_to_qt_color(col: Sequence[int]) -> QColor:
    assert len(col) >= 3, all(0 <= c <= 255 for c in col)
    return QColor(col[0], col[1], col[2])


def qt_to_vtk_color(col: QColor) -> vtkColor3ub:
    value = (col.red(), col.green(), col.blue())
    assert all(0 <= c <= 255 for c in value)
    vtk_color = vtkColor3ub()
    vtk_color[0], vtk_color[1], vtk_color[2] = value
    return vtk_color


def set_widget_bg_color(widget: QWidget, col: vtkColor3ub):
    widget.setStyleSheet('background-color: rgb({}, {}, {})'.format(col[0], col[1], col[2]))


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

        self.__color_buttons = []
        self.__sliders = []
        for i, label_setting in enumerate(self.__label_settings):
            self.__label_colors.append(label_setting.default_color)

            self.layout().addWidget(btn := QPushButton())
            btn.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            set_widget_bg_color(btn, label_setting.default_color)
            btn.setLayout(layout := QVBoxLayout())
            btn.setAutoFillBackground(True)
            btn.pressed.connect(partial(self.__handle_color_button_pressed, i))
            self.__color_buttons.append(btn)

            layout.addWidget(iso_name := QLabel())
            iso_name.setText(' ' + label_setting.name)
            iso_name.setStyleSheet('background-color: rgb(255, 255, 255)')
            iso_name.setAutoFillBackground(True)

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

            layout.addWidget(slider := QSlider(Qt.Horizontal))
            slider.setTracking(False)
            slider.setMinimum(0)
            slider.setMaximum(255)
            slider.setValue(0)
            slider.valueChanged.connect(partial(self.__handle_opacity_changed, i))
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

    def set_opacity(self, idx, value):
        assert idx < len(self.__sliders)
        s = self.__sliders[idx]
        s.setValue(clamp(value, s.minimum(), s.maximum()))

    def __handle_opacity_changed(self, idx, value):
        self.__label_opacities[idx] = value
        self.opacity_changed(idx, value)

    def __handle_color_changed(self, idx, color: QColor):
        color = self.__label_colors[idx] = qt_to_vtk_color(color)
        set_widget_bg_color(self.__color_buttons[idx], color)
        self.color_changed(idx, color)

    def __handle_color_button_pressed(self, idx: int):
        color_picker = QColorDialog(
            seq_to_qt_color(self.__label_colors[idx]),
            parent=self
        )
        color_picker.setWindowTitle('Select Color for \'{}\''.format(self.__label_settings[idx].name))
        color_picker.setOption(QColorDialog.ShowAlphaChannel, False)
        color_picker.currentColorChanged.connect(partial(self.__handle_color_changed, idx))
        color_picker.show()
