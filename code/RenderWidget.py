from typing import List

import numpy as np
import vtk
import vtkmodules
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QLabel
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPiecewiseFunction
from vtkmodules.vtkRenderingCore import vtkRenderer, vtkColorTransferFunction, vtkVolumeProperty, vtkVolume, vtkCamera
from vtkmodules.vtkRenderingVolumeOpenGL2 import vtkSmartVolumeMapper

from SynchronizedQVTKRenderWindowInteractor import SynchronizedQVTKRenderWindowInteractor


def convert(numpy_array):
    # If Deep is set to True, the array is deep-copied from numpy. This is not as efficient as the default
    # behavior and uses more memory but detaches the two array such that the numpy array can be released.
    return numpy_to_vtk(numpy_array.ravel(), deep=True, array_type=vtk.VTK_FLOAT)


class SynchronizedRenderWidget(QWidget):
    camera = vtkCamera()

    def __init__(self, is_gpu: bool, image: vtkImageData, volume: np.ndarray,
                 volume_idx: int, color_list: List[vtkmodules.vtkCommonDataModel.vtkColor3d], iso_opacities: List[float]):
        super().__init__()

        self.__volume_idx = volume_idx
        self.__is_gpu = is_gpu
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

        # Create transfer mapping scalar value to color according to color list and iso 0-11
        self.colorTransferFunction = vtkColorTransferFunction()
        for i in range(12):
            self.colorTransferFunction.AddRGBPoint(i, color_list[i][0], color_list[i][1], color_list[i][2])

        # The property describes how the data will look.
        self.volumeProperty = vtkVolumeProperty()
        self.volumeProperty.SetColor(self.colorTransferFunction)
        self.opacityTransferFunction = None
        self.update_iso_opacities(iso_opacities)
        self.volumeProperty.ShadeOn()
        self.volumeProperty.SetInterpolationTypeToLinear()

        # The volume holds the mapper and the property and
        # can be used to position/orient the volume.
        self.volume = vtkVolume()
        self.volume.SetProperty(self.volumeProperty)
        self.volumeMapper = vtkSmartVolumeMapper()

        self.renderWindowWidget = None
        self.__active = False
        self.active = True

        self.ren.AddVolume(self.volume)
        self.ren.SetBackground(vtkNamedColors().GetColor3d('Black'))
        self.ren.GetActiveCamera().Azimuth(45)
        self.ren.GetActiveCamera().Elevation(30)
        self.ren.ResetCameraClippingRange()
        self.ren.ResetCamera()

    @property
    def active(self):
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
            self.adjust_volume_mapper()

    def adjust_volume_mapper(self):
        if self.__is_gpu:
            self.volumeMapper.SetRequestedRenderModeToGPU()
        else:
            self.volumeMapper.SetRequestedRenderModeToRayCast()
            if self.active:
                self.volumeMapper.ReleaseGraphicsResources(self.renderWindowWidget.GetRenderWindow())

    def update_iso_opacities(self, iso_opacities: List[float]):
        self.opacityTransferFunction = vtkPiecewiseFunction()
        for i in range(12):
            self.opacityTransferFunction.AddPoint(i, iso_opacities[i])
        self.volumeProperty.SetScalarOpacity(self.opacityTransferFunction)

    def __init(self, volume_idx: int):
        assert not self.__active

        self.renderWindowWidget = SynchronizedQVTKRenderWindowInteractor()
        self.renderWindowWidget.setToolTip("Volume "+str(volume_idx+1))
        self.renderWindowWidget.GetRenderWindow().AddRenderer(self.ren)
        self.volumeMapper.SetInputDataObject(0, self.image)
        self.volume.SetMapper(None)
        self.adjust_volume_mapper()

        self.volume.SetMapper(self.volumeMapper)

        self.renderWindowWidget.Initialize()
        self.renderWindowWidget.Start()

        self.vertical_layout.replaceWidget(self.__dummy_widget, self.renderWindowWidget)
        self.__active = True

    def __release(self):
        assert self.__active
        self.__active = False
        self.vertical_layout.replaceWidget(self.renderWindowWidget, self.__dummy_widget)
        self.volume.SetMapper(None)
        self.volumeMapper.SetInputDataObject(0, None)
        self.renderWindowWidget.GetRenderWindow().RemoveRenderer(self.ren)
        self.renderWindowWidget.close()
        self.renderWindowWidget = None

    @property
    def mem_size(self) -> int:
        """
        Returns memory size of volume in MB.
        """
        return self.image.GetActualMemorySize() >> 10

    def set_volume(self, volume: np.ndarray):
        self.image.GetPointData().SetScalars(convert(volume))
        print('setting volume of {} MB'.format(self.image.GetActualMemorySize() / 1024))

    def closeEvent(self, evt):
        super().closeEvent(evt)
        if self.active:
            self.active = False
