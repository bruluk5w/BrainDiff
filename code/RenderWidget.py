from typing import List, Union, Set

import numpy as np
import vtk
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPiecewiseFunction, vtkColor3ub
from vtkmodules.vtkRenderingCore import vtkRenderer, vtkColorTransferFunction, vtkVolumeProperty, vtkVolume, vtkCamera, \
    vtkLight
from vtkmodules.vtkRenderingVolumeOpenGL2 import vtkSmartVolumeMapper

from SynchronizedQVTKRenderWindowInteractor import SynchronizedQVTKRenderWindowInteractor
from common import clamp


def convert(numpy_array):
    # If Deep is set to True, the array is deep-copied from numpy. This is not as efficient as the default
    # behavior and uses more memory but detaches the two array such that the numpy array can be released.
    return numpy_to_vtk(numpy_array.ravel(), deep=True, array_type=vtk.VTK_FLOAT)


def _make_opacity_value(x):
    return x / 255


def _make_color_value(c: vtkColor3ub):
    return [c[0] / 255, c[1] / 255, c[2] / 255]


def init_color_transfer_function(func: vtkColorTransferFunction, values: List[vtkColor3ub]):
    func.AllowDuplicateScalarsOn()
    max_x = len(values)
    for idx, value in enumerate(values):
        v = [value[i] / 255 for i in range(3)]
        func.AddRGBPoint(clamp(idx - 0.5, 0, max_x), *v)
        func.AddRGBPoint(clamp(idx + 0.5, 0, max_x), *v)


def init_opacity_transfer_function(func: vtkPiecewiseFunction, values: List[float]):
    func.AllowDuplicateScalarsOn()
    max_x = len(values)
    for idx, value in enumerate(values):
        v = _make_opacity_value(value)
        func.AddPoint(clamp(idx - 0.5, 0, max_x), v)
        func.AddPoint(clamp(idx + 0.5, 0, max_x), v)


class SynchronizedRenderWidget(QWidget):
    camera = vtkCamera()
    active_widgets: Set['SynchronizedRenderWidget'] = set()

    @classmethod
    def reset_camera(cls):
        if cls.active_widgets:
            next(iter(cls.active_widgets)).ren.ResetCamera()

    def __init__(self, is_gpu: bool, image: vtkImageData, volume: np.ndarray, volume_idx: int, color_list: List[QColor],
                 iso_opacities: List[float], shaded=False, progressive=True):
        super().__init__()

        self.__volume_idx = volume_idx
        self.__is_gpu = is_gpu
        self.__shaded = not shaded
        self.__active = False

        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.__dummy_widget = QWidget()
        self.image = image
        self.set_volume(volume)

        self.vertical_layout = QVBoxLayout(self)
        self.vertical_layout.setSpacing(0)
        self.vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.vertical_layout.addWidget(self.__dummy_widget)

        self.ren = vtkRenderer()
        self.ren.SetActiveCamera(self.camera)
        light = vtkLight()
        light.SetColor(1, 1, 1)
        self.ren.AddLight(light)
        # Create transfer mapping scalar value to color according to color list and iso 0-11
        self.colorTransferFunction = vtkColorTransferFunction()
        init_color_transfer_function(self.colorTransferFunction, color_list)
        self.opacityTransferFunction = vtkPiecewiseFunction()
        init_opacity_transfer_function(self.opacityTransferFunction, iso_opacities)

        # The property describes how the data will look.
        self.volumeProperty = vtkVolumeProperty()
        self.volumeProperty.SetInterpolationTypeToNearest()
        self.volumeProperty.SetColor(self.colorTransferFunction)
        self.volumeProperty.SetScalarOpacity(self.opacityTransferFunction)
        # The volume holds the mapper and the property and
        # can be used to position/orient the volume.
        self.volume = vtkVolume()
        self.volume.SetProperty(self.volumeProperty)
        self.volumeMapper = vtkSmartVolumeMapper()
        self.volumeMapper.SetInteractiveAdjustSampleDistances(False)

        self.renderWindowWidget: Union[None, SynchronizedQVTKRenderWindowInteractor] = None
        self.active = True
        self.shaded = shaded
        self.ren.AddVolume(self.volume)
        self.ren.SetBackground(vtkNamedColors().GetColor3d('Black'))
        self.ren.GetActiveCamera().Azimuth(45)
        self.ren.GetActiveCamera().Elevation(30)
        self.ren.ResetCameraClippingRange()
        self.progressive = progressive

    @property
    def progressive(self) -> bool:
        return self.volumeMapper.GetAutoAdjustSampleDistances()

    @progressive.setter
    def progressive(self, value):
        if value != self.progressive:
            self.volumeMapper.SetAutoAdjustSampleDistances(value)
            self.volumeMapper.SetSampleDistance(-1)
            if self.active:
                self.renderWindowWidget.on_change(None)

    @property
    def active(self) -> bool:
        return self.__active

    @active.setter
    def active(self, value: bool):
        assert isinstance(value, bool)
        if self.__active != value:
            if self.__active:
                self.__release()
                self.hide()
            else:
                self.__init(self.__volume_idx)
                self.show()

            assert self.__active == value

    @property
    def is_gpu(self):
        return self.__is_gpu

    @is_gpu.setter
    def is_gpu(self, value: bool):
        assert isinstance(value, bool)
        if self.__is_gpu != value:
            self.__is_gpu = value
            self._adjust_volume_mapper()

    def _adjust_volume_mapper(self):
        if self.__is_gpu:
            self.volumeMapper.SetRequestedRenderModeToGPU()
        else:
            self.volumeMapper.SetRequestedRenderModeToRayCast()
            if self.active:
                self.volumeMapper.ReleaseGraphicsResources(self.renderWindowWidget.GetRenderWindow())

    @property
    def shaded(self):
        return self.__shaded

    @shaded.setter
    def shaded(self, value):
        if value != self.__shaded:
            if value:
                self.volumeProperty.ShadeOn()
                self.volumeProperty.SetDiffuse(0, 2)
            else:
                self.volumeProperty.ShadeOff()

            if self.active:
                self.renderWindowWidget.on_change(None)

        self.__shaded = value

    def update_label_opacity(self, idx: int, label_opacity: float):
        val = _make_opacity_value(label_opacity)
        node = [0.0] * 4
        self.opacityTransferFunction.GetNodeValue(idx * 2, node)
        node[1] = val
        self.opacityTransferFunction.SetNodeValue(idx * 2, node)
        self.opacityTransferFunction.GetNodeValue(idx * 2 + 1, node)
        node[1] = val
        self.opacityTransferFunction.SetNodeValue(idx * 2 + 1, node)
        if self.active:
            self.renderWindowWidget.on_change(None)

    def update_label_color(self, idx: int, label_color: vtkColor3ub):
        val = _make_color_value(label_color)
        node = [0.0] * 6
        self.colorTransferFunction.GetNodeValue(idx * 2, node)
        node[1:4] = val
        self.colorTransferFunction.SetNodeValue(idx * 2, node)
        self.colorTransferFunction.GetNodeValue(idx * 2 + 1, node)
        node[1:4] = val
        self.colorTransferFunction.SetNodeValue(idx * 2 + 1, node)
        if self.active:
            self.renderWindowWidget.on_change(None)

    def __init(self, volume_idx: int):
        assert not self.__active

        self.renderWindowWidget = SynchronizedQVTKRenderWindowInteractor()
        self.renderWindowWidget.setToolTip("Volume " + str(volume_idx + 1))
        self.renderWindowWidget.GetRenderWindow().AddRenderer(self.ren)
        self.volumeMapper.SetInputDataObject(0, self.image)
        self._adjust_volume_mapper()

        self.volume.SetMapper(self.volumeMapper)

        self.renderWindowWidget.Initialize()
        self.renderWindowWidget.Start()

        self.vertical_layout.replaceWidget(self.__dummy_widget, self.renderWindowWidget)
        self.__active = True
        self.active_widgets.add(self)

    def __release(self):
        assert self.__active
        self.volumeMapper.ReleaseGraphicsResources(self.renderWindowWidget.GetRenderWindow())
        self.active_widgets.remove(self)
        self.__active = False
        self.vertical_layout.replaceWidget(self.renderWindowWidget, self.__dummy_widget)
        self.volume.SetMapper(None)
        self.volumeMapper.SetInputDataObject(0, None)
        self.renderWindowWidget.GetRenderWindow().RemoveRenderer(self.ren)
        self.renderWindowWidget.close()
        self.renderWindowWidget = None

    @property
    def mem_size(self) -> float:
        """
        Returns memory size of volume in MB.
        """
        return self.image.GetActualMemorySize() / (1 << 10)

    def set_volume(self, volume: np.ndarray):
        self.image.GetPointData().SetScalars(convert(volume))
        print('setting volume of {} MB'.format(self.image.GetActualMemorySize() / 1024))

    def closeEvent(self, evt):
        super().closeEvent(evt)
        if self.active:
            self.active = False
