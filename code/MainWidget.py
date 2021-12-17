import vtk
import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonCore import vtkFloatArray
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction, vtkImageData
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper, vtkRenderer, vtkColorTransferFunction, \
    vtkVolumeProperty, vtkVolume
# load implementations for rendering and interaction factory classes
import vtkmodules.vtkRenderingOpenGL2
import vtkmodules.vtkInteractionStyle
from vtkmodules.vtkRenderingVolume import vtkGPUVolumeRayCastMapper

from QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from PySide6.QtWidgets import QVBoxLayout, QPushButton, QWidget


import RenderWidget


class MainWidget(QWidget):

    def __init__(self, app, image: vtkImageData):
        super().__init__()
        self.image = image
        self.vertical_layout = QVBoxLayout(self)
        self.button = QPushButton(text="Push Me", )
        self.button.clicked.connect(lambda: print("hello world"))
        self.vertical_layout.addWidget(self.button)
        self.renderWidget = RenderWidget.RenderWidget(image)
        self.vertical_layout.addWidget(self.renderWidget)

        # if you don't want the 'q' key to exit comment this.
        # self.renderWidget.AddObserver("ExitEvent", lambda o, e, a=app: a.quit())
