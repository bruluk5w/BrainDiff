# coding=utf-8

import sys

import vtk
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction
from vtkmodules.vtkFiltersSources import vtkConeSource
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper, vtkRenderer, vtkColorTransferFunction, \
    vtkVolumeProperty, vtkVolume
from vtkmodules.vtkIOMINC import vtkMINCImageReader
# load implementations for rendering and interaction factory classes
import vtkmodules.vtkRenderingOpenGL2
import vtkmodules.vtkInteractionStyle
from vtkmodules.vtkRenderingVolume import vtkFixedPointVolumeRayCastMapper

import QVTKRenderWindowInteractor as QVTK
QVTKRenderWindowInteractor = QVTK.QVTKRenderWindowInteractor

if QVTK.PyQtImpl == 'PySide6':
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget
elif QVTK.PyQtImpl == 'PySide2':
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QApplication, QMainWindow
else:
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication, QMainWindow


class SampleWidget(QWidget):
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

        self.reader = vtkMINCImageReader()
        self.reader.SetFileName("../Data/subject04_crisp_v.mnc")
        # print(Image.CanReadFile("../Data/subject04_crisp_v.mnc"))
        # reader.RescaleRealValuesOn()
        self.reader.Update()

        # image = vtk.vtkImageData()
        # image = reader.GetOutput()

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

        # renWin.SetSize(600, 600)
        # renWin.SetWindowName('SimpleRayCast')
        # renWin.Render()

        # self.cone = vtkConeSource()
        # self.cone.SetResolution(8)

        # self.coneMapper = vtkPolyDataMapper()
        # self.coneMapper.SetInputConnection(self.cone.GetOutputPort())

        # self.coneActor = vtkActor()
        # self.coneActor.SetMapper(self.coneMapper)

        # self.ren.AddActor(self.coneActor)

        self.renderWidget.Initialize()
        self.renderWidget.Start()


def QVTKRenderWidgetConeExample(argv):
    """A simple example that uses the QVTKRenderWindowInteractor class."""
    # every QT app needs an app
    app = QApplication(['QVTKRenderWindowInteractor'])
    window = QMainWindow()
    ourAppWidget = SampleWidget(app)
    window.setCentralWidget(ourAppWidget)
    window.show()

    # create the widget


    # start event processing
    # Source: https://doc.qt.io/qtforpython/porting_from2.html
    # 'exec_' is deprecated and will be removed in the future.
    # Use 'exec' instead.
    try:
        app.exec()
    except AttributeError:
        app.exec_()


if __name__ == "__main__":
    QVTKRenderWidgetConeExample(sys.argv)
