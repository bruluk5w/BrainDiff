from typing import Dict, Callable, Optional

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QSplitter, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy, \
    QSlider, QComboBox
from vtkmodules.vtkCommonDataModel import vtkImageData, vtkColor3ub

from BrainWebLabelColorWidget import BrainWebLabelColorWidget
from InterchangeableViewHelper import InterchangeableView, SmoothType
from RenderWidget import SynchronizedRenderWidget
from common import DataView, combo_box_add_enum_items


class PreservingDataView(DataView):

    @property
    def name(self):
        return 'Juxtaposition/Interchangeable'

    def __init__(self, image: vtkImageData, gpu_limit: int, parent=None):
        super().__init__(gpu_limit, parent)
        self._interchangeableView: Optional[InterchangeableView] = None
        self.__template_image = image
        self.__render_widgets: Dict[int, SynchronizedRenderWidget] = {}
        self.setLayout(layout := QVBoxLayout())
        self.__create_settings_ui(layout)

        # Split between visualisation specific setting and actual visualisation
        layout.addWidget(splitter := QSplitter())
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.setChildrenCollapsible(False)
        self.__label_color_widget = BrainWebLabelColorWidget()
        self.__label_color_widget.set_opacity(2, 25)  # let's not confront the user at first with a black screen
        self.__label_color_widget.set_opacity(8, 50)
        self.__label_color_widget.opacity_changed += self._update_iso_opacities
        self.__label_color_widget.color_changed += self._update_iso_colors
        splitter.addWidget(self.__label_color_widget)

        self.__grid_container = QWidget()
        splitter.addWidget(self.__grid_container)

        self._camera_reset = False

    def __create_settings_ui(self, parent_layout: QVBoxLayout):
        def new_layout():
            parent_layout.addWidget(container := QWidget())
            container.setLayout(layout := QHBoxLayout())
            container.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            return layout, container

        layout, _ = new_layout()

        def button(text: str, cb: Callable, toggled=False, layout=layout) -> QPushButton:
            btn = QPushButton(text=text)
            btn.setCheckable(True)
            if toggled:
                btn.toggle()
            btn.toggled.connect(cb)
            btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            layout.addWidget(btn)
            return btn

        self.__shaded_btn = button('Shaded', self._set_shaded)
        self.__progressive_bt = button('Use Progressive Rendering', self._set_progressive, True)
        self.__progressive_bt.setToolTip('Turn off if CPU renderers stay blurry. May stall the the application if the '
                                         'load is to heavy for the system. If possible, for best performance increase '
                                         'the GPU memory limit in the settings.')
        self.__interchangeable_btn = button('Interchangeable', self._set_interchangeable)

        layout, self._interchangeable_settings_container = new_layout()
        self.__interchangeable_slider = slider = QSlider(orientation=Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(0)
        slider.valueChanged.connect(self._set_page)
        layout.addWidget(slider)
        self.__interchangeable_smooth_type = box = QComboBox()
        combo_box_add_enum_items(box, SmoothType)
        box.currentIndexChanged.connect(self._set_smooth_type)
        layout.addWidget(box)
        self._interchangeable_settings_container.hide()

    @property
    def is_interchangeable(self):
        return self._interchangeableView is not None

    def _set_page(self, value: float):
        if self.is_interchangeable:
            self._interchangeableView.set_page(value)

    @property
    def smooth_type(self):
        return self.__interchangeable_smooth_type.currentData(Qt.UserRole)

    def _set_smooth_type(self, idx: int):
        if self.is_interchangeable:
            smooth_type = self.__interchangeable_smooth_type.itemData(idx, Qt.UserRole)
            assert smooth_type == self.smooth_type
            self._interchangeableView.smooth_type = smooth_type

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
        is_gpu = sum(r.mem_size for r in self.__render_widgets.values() if r.active) < self._gpu_mem_limit
        if idx in self.__render_widgets:
            render_widget = self.__render_widgets[idx]
            render_widget.set_volume(volume)
            render_widget.is_gpu = is_gpu
            render_widget.active = True

        else:
            image = vtkImageData()
            image.CopyStructure(self.__template_image)
            render_widget = SynchronizedRenderWidget(
                is_gpu, image, volume, idx, self.__label_color_widget.colors, self.__label_color_widget.opacities,
                shaded=self.__shaded_btn.isChecked(), progressive=self.__progressive_bt.isChecked(),
                off_screen=self.is_interchangeable
            )

            render_widget.active = True
            if not self._camera_reset:
                SynchronizedRenderWidget.reset_camera()
                self._camera_reset = True

            self.__render_widgets[idx] = render_widget

        self._layout_renderers()

        if self.is_interchangeable:
            self._interchangeableView.add(self.__render_widgets[idx])
            self.__interchangeable_slider.setMaximum(self._interchangeableView.count)

    def remove_volume(self, idx: int):
        if idx in self.__render_widgets:
            renderer = self.__render_widgets[idx]
            if self.is_interchangeable:
                self._interchangeableView.remove(self.__render_widgets[idx])
                self.__interchangeable_slider.setMaximum(self._interchangeableView.count)

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

    def _set_progressive(self, value: bool):
        for renderer in self.__render_widgets.values():
            renderer.progressive = value

    def _set_interchangeable(self, value: bool):
        if self.is_interchangeable != value:
            if value:
                for renderer in self.__render_widgets.values():
                    renderer.off_screen = True
                self._interchangeableView = InterchangeableView(self.__grid_container, self.smooth_type)
                self._layout_renderers()
                for renderer in (r for r in self.__render_widgets.values() if r.active):
                    self._interchangeableView.add(renderer)

                self.__interchangeable_slider.setMaximum(self._interchangeableView.count)
                self._interchangeable_settings_container.show()
            else:
                for renderer in (r for r in self.__render_widgets.values() if r.active):
                    self._interchangeableView.remove(renderer)

                for renderer in self.__render_widgets.values():
                    renderer.off_screen = False

                self._interchangeableView.finalize()
                self._interchangeableView = None
                self._interchangeable_settings_container.hide()
                self._layout_renderers()

    def _layout_renderers(self):
        for renderer in self.__render_widgets.values():
            renderer.setParent(None)

        if self.is_interchangeable:
            rect = self.__grid_container.contentsRect()
            for renderer in (t for t in self.__render_widgets.values() if t.active):
                renderer.setGeometry(rect)
                renderer.setParent(self.__grid_container)
        else:
            if self.__grid_container.layout() is not None:
                # reparent layout and child widgets to temporary which will be deleted the proper way
                QWidget().setLayout(self.__grid_container.layout())
                self.__grid_container.setLayout(None)

            self.__grid_container.setLayout(layout := QGridLayout())
            layout.setSpacing(0)
            layout.setContentsMargins(0, 0, 0, 0)
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
