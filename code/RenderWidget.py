from typing import List, Union, Set

import numpy as np
from PySide6.QtGui import QColor, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPiecewiseFunction, vtkColor3ub
from vtkmodules.vtkCommonExecutionModel import vtkAlgorithmOutput
from vtkmodules.vtkRenderingCore import vtkRenderer, vtkColorTransferFunction, vtkVolumeProperty, vtkVolume, vtkCamera, \
    vtkLight, vtkWindowToImageFilter
from vtkmodules.vtkRenderingVolumeOpenGL2 import vtkSmartVolumeMapper

from SynchronizedQVTKRenderWindowInteractor import SynchronizedQVTKRenderWindowInteractor, HookedInteractor
from common import clamp, convert, make_opacity_value, make_color_value


def init_color_transfer_function(func: vtkColorTransferFunction, values: List[vtkColor3ub]):
    func.AllowDuplicateScalarsOn()
    max_x = len(values)
    for idx, value in enumerate(values):
        v = make_color_value(value)
        func.AddRGBPoint(clamp(idx - 0.5, 0, max_x), *v)
        func.AddRGBPoint(clamp(idx + 0.5, 0, max_x), *v)


def init_opacity_transfer_function(func: vtkPiecewiseFunction, values: List[float]):
    func.AllowDuplicateScalarsOn()
    max_x = len(values)
    for idx, value in enumerate(values):
        v = make_opacity_value(value)
        func.AddPoint(clamp(idx - 0.5, 0, max_x), v)
        func.AddPoint(clamp(idx + 0.5, 0, max_x), v)


class SynchronizedRenderWidget(QWidget):
    camera = vtkCamera()
    active_widgets: Set['SynchronizedRenderWidget'] = set()

    @classmethod
    def reset_camera(cls):
        if cls.active_widgets:
            r = next(iter(cls.active_widgets)).ren
            r.ResetCamera()
            r.GetActiveCamera().Azimuth(45)
            r.GetActiveCamera().Elevation(30)
            r.ResetCameraClippingRange()

    def __init__(self, is_gpu: bool, image: vtkImageData, volume: np.ndarray, volume_idx: int, color_list: List[QColor],
                 iso_opacities: List[float], shaded=False, progressive=True, off_screen=False):
        super().__init__()

        self.__volume_idx = volume_idx
        self.__is_gpu = is_gpu
        self.__shaded = not shaded
        self.__active = False
        self.__off_screen = not off_screen

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
        light.SetColor(0.5, 0.5, 0.5)
        light.SetLightTypeToCameraLight()
        self.ren.AddLight(light)
        self.ren.SetAmbient(0.1, 0.1, 0.1)
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
        self.progressive = progressive
        self.__window_to_image_filter = None
        self.off_screen = off_screen

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
    def off_screen(self):
        return self.__off_screen

    @off_screen.setter
    def off_screen(self, value):
        if self.__off_screen != value:
            self.__off_screen = value
            if self.active:
                self._set_off_screen(self.__off_screen)

    @property
    def off_screen_img_output(self) -> vtkAlgorithmOutput:
        assert self.off_screen and self.active
        return self.__window_to_image_filter.GetOutputPort()

    @property
    def active(self) -> bool:
        return self.__active

    @active.setter
    def active(self, value: bool):
        assert isinstance(value, bool)
        if self.__active != value:
            if self.__active:
                self.__release()
            else:
                self.__init(self.__volume_idx)

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
        val = make_opacity_value(label_opacity)
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
        val = make_color_value(label_color)
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
        if self.__off_screen:
            self._set_off_screen(True)
        self.active_widgets.add(self)
        self.show()

    def __release(self):
        assert self.__active
        self.volumeMapper.ReleaseGraphicsResources(self.renderWindowWidget.GetRenderWindow())
        self.active_widgets.remove(self)
        self.__active = False
        self.vertical_layout.replaceWidget(self.renderWindowWidget, self.__dummy_widget)
        self.volume.SetMapper(None)
        self.volumeMapper.SetInputDataObject(0, None)
        if self.__off_screen:
            self._set_off_screen(False)

        self.renderWindowWidget.GetRenderWindow().RemoveRenderer(self.ren)
        self.renderWindowWidget.close()
        self.renderWindowWidget = None

        self.hide()

    def _set_off_screen(self, value: bool):
        if value:
            assert self.active

        self.renderWindowWidget.GetRenderWindow().SetOffScreenRendering(value)
        self.setAttribute(Qt.WA_DontShowOnScreen, value)
        if value:
            self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
            f = self.__window_to_image_filter = vtkWindowToImageFilter()
            f.ReadFrontBufferOff()
            f.SetInput(self.renderWindowWidget.GetRenderWindow())
            f.Modified()
            f.Update(0)
            HookedInteractor.on_change += self._update_offscreen_rendering
        else:
            HookedInteractor.on_change -= self._update_offscreen_rendering
            if self.__window_to_image_filter is not None:
                self.__window_to_image_filter.SetInput(None)
                self.__window_to_image_filter = None

            self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

    def _update_offscreen_rendering(self, event_src):
        self.__window_to_image_filter.Modified()
        self.__window_to_image_filter.Update(0)

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
