import sys

from os import listdir
from os.path import isfile, join

import numpy
import vtk
from vtkmodules.util.numpy_support import vtk_to_numpy, numpy_to_vtk
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction, vtkImageData
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper, vtkRenderer, vtkColorTransferFunction, \
    vtkVolumeProperty, vtkVolume
from vtkmodules.vtkIOMINC import vtkMINCImageReader
# load implementations for rendering and interaction factory classes
import vtkmodules.vtkRenderingOpenGL2
import vtkmodules.vtkInteractionStyle
from vtkmodules.vtkRenderingVolume import vtkFixedPointVolumeRayCastMapper

from QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from PySide6.QtWidgets import QVBoxLayout, QPushButton, QWidget


class MainWidget(QWidget):

    def numpyToVTK(self, numpyArray):
        # If Deep is set to True, the array is deep-copied from from numpy. This is not as efficient as the default
        # behavior and uses more memory but detaches the two array such that the numpy array can be released.
        return numpy_to_vtk(numpyArray.ravel(), deep=True, array_type=vtk.VTK_FLOAT)

    def loadDataAsNumpy(self):
        dataPath = "../Data/"
        dataFiles = [f for f in listdir(dataPath) if isfile(join(dataPath, f))]

        npDataList = []
        self.reader = vtkMINCImageReader()

        for file in dataFiles:
            self.reader.SetFileName(dataPath+file)
            image = self.reader.GetOutputDataObject(0)  # type: vtkImageData
            self.reader.Update()
            ext = image.GetExtent()
            dim = (ext[1] - ext[0] + 1, ext[3] - ext[2] + 1, ext[5] - ext[4] + 1)
            npDataList.append(vtk_to_numpy(image.GetPointData().GetScalars()).reshape(dim))

        return npDataList

    def __init__(self, app):
        super().__init__()
        self.vertical_layout = QVBoxLayout(self)
        self.button = QPushButton(text="Push Me", )
        self.button.clicked.connect(lambda: print("hello world"))
        self.vertical_layout.addWidget(self.button)
        self.renderWidget = QVTKRenderWindowInteractor()
        self.vertical_layout.addWidget(self.renderWidget)

        # if you don't want the 'q' key to exit comment this.
        self.renderWidget.AddObserver("ExitEvent", lambda o, e, a=app: a.quit())

        self.ren = vtkRenderer()
        self.renderWidget.GetRenderWindow().AddRenderer(self.ren)

        numpyDataList = self.loadDataAsNumpy()
        image = self.numpyToVTK(numpyDataList[0])  # type: vtkImageData

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
        self.volumeMapper = vtkFixedPointVolumeRayCastMapper()
        self.volumeMapper.SetInputConnection(self.reader.GetOutputPort())

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

        self.renderWidget.Initialize()
        self.renderWidget.Start()
