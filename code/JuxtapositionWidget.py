from typing import Dict

import numpy as np
from PySide6.QtWidgets import QWidget, QSplitter, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy
from vtkmodules.vtkCommonDataModel import vtkImageData, vtkColor3ub

from BrainWebLabelColorWidget import BrainWebLabelColorWidget
from RenderWidget import SynchronizedRenderWidget
from common import DataView


class JuxtapositionWidget(DataView):

    @property
    def name(self):
        return 'Juxtaposition'

    def __init__(self, image: vtkImageData, gpu_limit: int, parent=None):
        super().__init__(gpu_limit, parent)
        self.__template_image = image
        self.__render_widgets: Dict[int, SynchronizedRenderWidget] = {}
        self.setLayout(layout := QVBoxLayout())

        layout.addWidget(container := QWidget())
        container.setLayout(settings_layout := QHBoxLayout())
        container.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.__shaded_btn = QPushButton(text='Shaded')
        self.__shaded_btn.setCheckable(True)
        self.__shaded_btn.toggled.connect(self._set_shaded)
        settings_layout.addWidget(self.__shaded_btn)

        # Split between visualisation specific setting and actual visualisation
        layout.addWidget(splitter := QSplitter())
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.setChildrenCollapsible(False)
        self.__label_color_widget = BrainWebLabelColorWidget()
        self.__label_color_widget.opacities[1] = 50  # let's not confront the user at first with a black screen
        self.__label_color_widget.opacity_changed += self._update_iso_opacities
        self.__label_color_widget.color_changed += self._update_iso_colors
        splitter.addWidget(self.__label_color_widget)

        self.__grid_container = QWidget()
        splitter.addWidget(self.__grid_container)

        self._camera_reset = False

    def gpu_mem_limit_changed(self, limit: int):
        super().gpu_mem_limit_changed(limit)
        used_mem = 0
        for render_widget in self.__render_widgets.values():
            used_mem += render_widget.mem_size
            render_widget.is_gpu = used_mem < self._gpu_mem_limit

    def _activate(self):
        pass

    def _deactivate(self):
        pass

    def add_volume(self, idx: int, volume: np.ndarray):
        print('Volume {} added.'.format(idx))
        is_gpu = sum(r.mem_size for r in self.__render_widgets.values() if r.active) < self._gpu_mem_limit
        if idx in self.__render_widgets:
            renderer = self.__render_widgets[idx]
            renderer.set_volume(volume)
            if not renderer.active:
                renderer.is_gpu = is_gpu
                renderer.active = True
        else:
            image = vtkImageData()
            image.CopyStructure(self.__template_image)
            render_widget = SynchronizedRenderWidget(
                is_gpu, image, volume, idx, self.__label_color_widget.colors, self.__label_color_widget.opacities,
                shaded=self.__shaded_btn.isChecked()
            )

            render_widget.active = True
            if not self._camera_reset:
                SynchronizedRenderWidget.reset_camera()
                self._camera_reset = True

            self.__render_widgets[idx] = render_widget

        self._layout_renderers()

    def remove_volume(self, idx: int):
        if idx in self.__render_widgets:
            renderer = self.__render_widgets[idx]
            renderer.active = False
        else:
            print('Error: no volume {} that could be removed.'.format(idx))

        self._layout_renderers()

    def _update_iso_opacities(self, idx: int, opacity: float):
        for renderer in self.__render_widgets.values():
            renderer.update_label_opacity(idx, opacity)

    def _update_iso_colors(self, idx: int, color: vtkColor3ub):
        for renderer in self.__render_widgets.values():
            renderer.update_label_color(idx, color)

    def _set_shaded(self, value: bool):
        for renderer in self.__render_widgets.values():
            renderer.shaded = value

    def _layout_renderers(self):
        for renderer in self.__render_widgets.values():
            renderer.setParent(None)

        # reparent layout and child widgets to temporary which will be deleted the proper way
        QWidget().setLayout(self.__grid_container.layout())

        layout = QGridLayout()
        layout.setSpacing(0)
        self.__grid_container.setLayout(layout)
        num_widgets = sum(1 for r in self.__render_widgets.values() if r.active)
        layout_side_size = _next_square(num_widgets)
        for i, renderer in enumerate(t for t in self.__render_widgets.values() if t.active):
            row = i // layout_side_size
            layout.addWidget(renderer, row, i - layout_side_size * row)

    def closeEvent(self, event):
        for renderer in self.__render_widgets.values():
            renderer.close()


def _next_square(n: int):
    i = 0
    while i * i < n:
        i += 1

    return i
