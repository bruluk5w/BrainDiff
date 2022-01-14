from functools import partial
from typing import Dict

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QVBoxLayout, QSplitter, QSizePolicy, QComboBox, QCheckBox
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkRenderingCore import vtkRenderer, vtkActor, vtkPolyDataMapper

from BrainWebLabelColorWidget import BrainWebLabelColorWidget
from FixedQVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from VolumeOperators import Operator, rebuild
from common import DataView, combo_box_add_enum_items, make_color_value, make_opacity_value
from common import FloatSlider


class ExplicitEncodingDataView(DataView):
    @property
    def name(self):
        return 'Explicit Encoding'

    def __init__(self, image: vtkImageData, gpu_limit: int, parent=None):
        super().__init__(gpu_limit, parent)
        self.__template_image = image
        self._volumes = {}
        self.__label_state: Dict[int, QCheckBox] = {}

        self.setLayout(layout := QVBoxLayout())
        self.__create_settings_ui(layout)
        layout.addWidget(splitter := QSplitter())
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        splitter.setChildrenCollapsible(False)
        self.__label_color_widget = BrainWebLabelColorWidget(inject_ui=self.__add_ui_to_label_color_widget)
        for i in range(len(self.__label_color_widget.opacities)):
            self.__label_color_widget.set_opacity(i, 127)  # let's not confront the user at first with a black screen

        self.__label_color_widget.opacity_changed += self._update_label_opacities
        self.__label_color_widget.color_changed += self._update_label_colors
        splitter.addWidget(self.__label_color_widget)

        self.__renderer_widget = QVTKRenderWindowInteractor()
        self.__renderer_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.__renderer_widget.adjustSize()
        splitter.addWidget(self.__renderer_widget)
        self.__renderer = vtkRenderer()
        self.__renderer.SetBackground(vtkNamedColors().GetColor3d('Black'))
        self.__renderer_widget.GetRenderWindow().SetAlphaBitPlanes(1)
        self.__renderer_widget.GetRenderWindow().SetMultiSamples(0)
        self.__renderer.SetUseDepthPeeling(1)
        self.__renderer.SetMaximumNumberOfPeels(100)
        self.__renderer.SetOcclusionRatio(0.06)
        self.__renderer_widget.GetRenderWindow().AddRenderer(self.__renderer)
        self.__actors: Dict[int, vtkActor] = {}
        self.__mappers: Dict[int, vtkPolyDataMapper] = {}
        self._operator_type = next(iter(Operator))
        self.__iso_slider.setHidden(self._operator_type != Operator.ADDITION)

        self.__renderer.AutomaticLightCreationOn()

        self.__renderer_widget.Initialize()
        self.__renderer_widget.Start()
        self.__camara_reset = False
        self.__flying_edges = None
        self.__label_state[3].toggle()

    def __add_ui_to_label_color_widget(self, idx: int, layout):
        self.__label_state[idx] = check_box = QCheckBox()
        check_box.toggled.connect(partial(self._toggle_label, idx))
        layout.addWidget(check_box)

    def __create_settings_ui(self, layout):
        self.__operator_type_box = box = QComboBox()
        layout.addWidget(box)
        combo_box_add_enum_items(box, Operator)
        box.currentIndexChanged.connect(self._set_operator_type)
        layout.addWidget(box)
        self.__iso_slider = slider = FloatSlider(0, 0, 0)
        slider.setMouseTracking(False)
        slider.value_changed += self._set_iso_value
        layout.addWidget(slider)
        box.setCurrentIndex(0)

    @property
    def operator_type(self) -> Operator:
        return self.__operator_type_box.currentData(Qt.UserRole)

    def _activate(self):
        print('activate')
        self.__renderer.Render()

    def _deactivate(self):
        print('deactivate')

    def add_volume(self, idx: int, volume: np.ndarray):
        self._volumes[idx] = volume
        self.__iso_slider.set_interval(0, len(self._volumes))
        self._update()

    def remove_volume(self, idx: int):
        del self._volumes[idx]
        self.__iso_slider.set_interval(0, len(self._volumes))
        self._update()

    def _set_operator_type(self, idx):
        new_operator = self.__operator_type_box.currentData(Qt.UserRole)
        if self._operator_type != new_operator:
            self._operator_type = new_operator
            self.__iso_slider.setHidden(new_operator != Operator.ADDITION)
            self._update()

    def _set_iso_value(self, value):
        self.__iso_slider.setMouseTracking(False)
        for fe in self.__flying_edges:
            fe.SetValue(0, value)
        QTimer.singleShot(10, self.__renderer.GetRenderWindow().Render)

    def _toggle_label(self, label: int, value):
        if not value:
            self.__renderer.RemoveActor(actor := self.__actors[label])
            self.__mappers[label].RemoveAllInputConnections(0)
            actor.SetMapper(None)
            del self.__actors[label]
            del self.__mappers[label]
            self.__renderer.GetRenderWindow().Render()
        else:
            self.__renderer.AddActor(actor := vtkActor())
            actor.GetProperty().SetColor(make_color_value(self.__label_color_widget.colors[label]))
            actor.GetProperty().SetOpacity(make_opacity_value(self.__label_color_widget.opacities[label]))
            actor.SetMapper(mapper := vtkPolyDataMapper())
            mapper.ScalarVisibilityOff()
            self.__actors[label] = actor
            self.__mappers[label] = mapper
            self._update()

        if not self.__camara_reset:
            self.__renderer.GetActiveCamera().Azimuth(60)
            self.__renderer.GetActiveCamera().Elevation(30)
            self.__renderer.GetActiveCamera().SetPosition(0, 200, 200)
            self.__renderer.ResetCamera()
            self.__camara_reset = True

    def _update_label_opacities(self, idx, value):
        if idx in self.__actors:
            self.__actors[idx].GetProperty().SetOpacity(make_opacity_value(value))
            self.__renderer.GetRenderWindow().Render()

    def _update_label_colors(self, idx, color):
        if idx in self.__actors:
            self.__actors[idx].GetProperty().SetColor(make_color_value(color))
            self.__renderer.GetRenderWindow().Render()

    def _update(self):
        labels = [i for i, check_box in self.__label_state.items() if check_box.isChecked()]
        self.__flying_edges = rebuild(list(self._volumes.values()), labels, self.operator_type, self.__template_image,
                                      self.__iso_slider.value)
        for fe, label in zip(self.__flying_edges, labels):
            self.__mappers[label].SetInputConnection(0, fe.GetOutputPort(0))

        self.__renderer_widget.Render()
