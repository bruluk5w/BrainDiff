from typing import List

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

from PySide6.QtWidgets import QVBoxLayout, QPushButton, QWidget, QHBoxLayout, QSplitter, QSizePolicy
from VolumeListWidget import VolumeListWidget


import RenderWidget


class MainWidget(QWidget):

    def __init__(self, app, image: vtkImageData, volume_list: List[np.ndarray]):
        super().__init__()
        self.__vertical_layout = QVBoxLayout(self)
        self.__renderWidget = RenderWidget.RenderWidget(image)
        self.__renderWidget.sizePolicy().setHorizontalPolicy(QSizePolicy.Maximum)
        self.__volume_list_widget = VolumeListWidget(volume_list,
                                                     selection_added_cb=self.add_volume,
                                                     selection_removed_cb=self.remove_volume)

        self.__splitter = QSplitter()
        self.__splitter.setChildrenCollapsible(False)
        self.__splitter.addWidget(self.__volume_list_widget)
        self.__splitter.addWidget(self.__renderWidget)
        self.__vertical_layout.addWidget(self.__splitter)
        # if you don't want the 'q' key to exit comment this.
        # self.renderWidget.AddObserver("ExitEvent", lambda o, e, a=app: a.quit())

    def add_volume(self, idx: int, volume: np.ndarray):
        print('Volume {} added.'.format(idx))

    def remove_volume(self, idx: int, volume: np.ndarray):
        print('Volume {} removed.'.format(idx))
