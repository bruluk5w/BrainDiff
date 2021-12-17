import numpy as np
import vtk
from PySide6.QtWidgets import QWidget, QVBoxLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPiecewiseFunction
from vtkmodules.vtkRenderingCore import vtkRenderer, vtkColorTransferFunction, vtkVolumeProperty, vtkVolume
from vtkmodules.vtkRenderingVolume import vtkGPUVolumeRayCastMapper


class RenderWidget(QWidget):

    def __init__(self, image: vtkImageData):
        super().__init__()
        self.image = image

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

        # The mapper / ray cast function know how to render the data.
        self.volumeMapper = vtkGPUVolumeRayCastMapper()
        self.volumeMapper.SetInputData(image)

        # The volume holds the mapper and the property and
        # can be used to position/orient the volume.
        self.volume = vtkVolume()
        self.volume.SetMapper(self.volumeMapper)
        self.volume.SetProperty(self.volumeProperty)

        self.ren.AddVolume(self.volume)
        self.ren.SetBackground(vtkNamedColors().GetColor3d('Wheat'))
        self.ren.GetActiveCamera().Azimuth(45)
        self.ren.GetActiveCamera().Elevation(30)
        self.ren.ResetCameraClippingRange()
        self.ren.ResetCamera()

        self.renderWindowWidget.Initialize()
        self.renderWindowWidget.Start()


    def numpyToVTK(self, numpyArray):
        # If Deep is set to True, the array is deep-copied from from numpy. This is not as efficient as the default
        # behavior and uses more memory but detaches the two array such that the numpy array can be released.
        return numpy_to_vtk(numpyArray.ravel(), deep=True, array_type=vtk.VTK_FLOAT)

    def set_volume(self, volume: np.ndarray):
        volume_data = self.numpyToVTK(volume)  # type: vtkFloatArray
        self.image.GetPointData().SetScalars(volume_data)