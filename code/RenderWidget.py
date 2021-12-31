import numpy as np
import vtk
from PySide6.QtWidgets import QWidget, QVBoxLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPiecewiseFunction
from vtkmodules.vtkRenderingCore import vtkRenderer, vtkColorTransferFunction, vtkVolumeProperty, vtkVolume
from vtkmodules.vtkRenderingVolume import vtkGPUVolumeRayCastMapper, vtkFixedPointVolumeRayCastMapper


def convert(numpy_array):
    # If Deep is set to True, the array is deep-copied from numpy. This is not as efficient as the default
    # behavior and uses more memory but detaches the two array such that the numpy array can be released.
    return numpy_to_vtk(numpy_array.ravel(), deep=True, array_type=vtk.VTK_FLOAT)


class RenderWidget(QWidget):

    def __init__(self, is_gpu: bool, image: vtkImageData, volume: np.ndarray):
        super().__init__()
        self.__is_gpu = is_gpu
        self.__active = True
        self.image = image
        self.set_volume(volume)
        self.vertical_layout = QVBoxLayout(self)
        self.renderWindowWidget = QVTKRenderWindowInteractor()
        self.vertical_layout.addWidget(self.renderWindowWidget)

        self.ren = vtkRenderer()
        self.renderWindowWidget.GetRenderWindow().AddRenderer(self.ren)

        # Create transfer mapping scalar value to opacity.
        self.opacityTransferFunction = vtkPiecewiseFunction()
        self.opacityTransferFunction.AddPoint(20, 1.0)
        self.opacityTransferFunction.AddPoint(255, 1.0)

        # Create transfer mapping scalar value to color.
        self.colorTransferFunction = vtkColorTransferFunction()
        self.colorTransferFunction.AddRGBPoint(0.0, 0.0, 0.0, 1.0)
        self.colorTransferFunction.AddRGBPoint(64.0, 1.0, 0.0, 1.0)
        self.colorTransferFunction.AddRGBPoint(128.0, 0.0, 0.0, 1.0)
        self.colorTransferFunction.AddRGBPoint(192.0, 0.0, 1.0, 1.0)
        self.colorTransferFunction.AddRGBPoint(255.0, 0.0, 0.2, 1.0)

        # The property describes how the data will look.
        self.volumeProperty = vtkVolumeProperty()
        self.volumeProperty.SetColor(self.colorTransferFunction)
        self.volumeProperty.SetScalarOpacity(self.opacityTransferFunction)
        self.volumeProperty.ShadeOn()
        self.volumeProperty.SetInterpolationTypeToLinear()


        # The volume holds the mapper and the property and
        # can be used to position/orient the volume.
        self.volume = vtkVolume()
        self.volume.SetProperty(self.volumeProperty)

        self.__init_mapper()

        self.ren.AddVolume(self.volume)
        self.ren.SetBackground(vtkNamedColors().GetColor3d('Wheat'))
        self.ren.GetActiveCamera().Azimuth(45)
        self.ren.GetActiveCamera().Elevation(30)
        self.ren.ResetCameraClippingRange()
        self.ren.ResetCamera()

        self.renderWindowWidget.Initialize()
        self.renderWindowWidget.Start()

    @property
    def active(self):
        return self.__active

    @active.setter
    def active(self, value: bool):
        assert isinstance(value, bool)
        if self. __active != value:
            self.__active = value
            if self.__active:
                self.__init_mapper()
            else:
                self.__release_mapper()

    @property
    def is_gpu(self):
        return self.__is_gpu

    @is_gpu.setter
    def is_gpu(self, value: bool):
        assert isinstance(value, bool)
        if self.__is_gpu != value:
            self.__is_gpu = value
            self.__init_mapper()

    def __init_mapper(self):
        assert self.__active
        if self.__is_gpu:
            self.__init_as_gpu()
        else:
            self.__init_as_cpu()

    def __init_as_gpu(self):
        self.volumeMapper = vtkGPUVolumeRayCastMapper()
        self.volumeMapper.SetInputData(self.image)
        self.volume.SetMapper(self.volumeMapper)

    def __init_as_cpu(self):
        self.volumeMapper = vtkFixedPointVolumeRayCastMapper()
        self.volumeMapper.SetInputData(self.image)
        self.volume.SetMapper(self.volumeMapper)

    def __release_mapper(self):
        self.volumeMapper = None
        self.volume.SetMapper(None)

    @property
    def mem_size(self) -> int:
        """
        Returns memory size of volume in MB.
        """
        return self.image.GetActualMemorySize() >> 10

    def set_volume(self, volume: np.ndarray):
        self.image.GetPointData().SetScalars(convert(volume))
        print('setting volume of {} MB'.format(self.image.GetActualMemorySize() / 1024))
