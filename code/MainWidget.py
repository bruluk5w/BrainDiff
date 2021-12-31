from typing import List, Dict, Tuple, NamedTuple

import numpy as np
from PySide6.QtWidgets import QWidget, QSplitter, QGridLayout, QVBoxLayout
from vtkmodules.vtkCommonDataModel import vtkImageData

from RenderWidget import RenderWidget
from VolumeListWidget import VolumeListWidget


class MainWidget(QWidget):

    def __init__(self, image: vtkImageData, volume_list: List[np.ndarray], gpu_mem_limit: int):
        super().__init__()
        self.__gpu_mem_limit = gpu_mem_limit
        self.__template_image = image
        self.__render_widgets: Dict[int, RenderWidget] = {}
        self.__volume_list_widget = VolumeListWidget(volume_list,
                                                     selection_added_cb=self.add_volume,
                                                     selection_removed_cb=self.remove_volume)
        self.__vertical_layout = QVBoxLayout(self)

        self.__splitter = QSplitter()
        self.__splitter.setChildrenCollapsible(False)
        self.__splitter.addWidget(self.__volume_list_widget)
        self.__wrapper = QWidget()
        self.__grid_layout = QGridLayout(self)
        self.__wrapper.setLayout(self.__grid_layout)
        self.__splitter.addWidget(self.__wrapper)
        self.__vertical_layout.addWidget(self.__splitter)
        # if you don't want the 'q' key to exit comment this.
        # self.renderWidget.AddObserver("ExitEvent", lambda o, e, a=app: a.quit())

        self.__volume_list_widget.item(0).setSelected(True)

    def add_volume(self, idx: int, volume: np.ndarray):
        print('Volume {} added.'.format(idx))
        is_gpu = sum(r.mem_size for r in self.__render_widgets.values() if r.active) < self.__gpu_mem_limit
        if idx in self.__render_widgets:
            renderer = self.__render_widgets[idx]
            renderer.set_volume(volume)
            if not renderer.active:
                renderer.is_gpu = is_gpu
                renderer.active = True
                self.__grid_layout.addWidget(renderer)
        else:
            image = vtkImageData()
            image.CopyStructure(self.__template_image)
            render_widget = RenderWidget(is_gpu, image, volume)
            render_widget.active = True
            self.__render_widgets[idx] = render_widget
            self.__grid_layout.addWidget(render_widget)

    def remove_volume(self, idx: int):
        print('Volume {} removed.'.format(idx))
        if idx in self.__render_widgets:
            renderer = self.__render_widgets[idx]
            self.__grid_layout.removeWidget(renderer)
            renderer.active = False
        else:
            print('Error: no volume {} that could be removed.'.format(idx))

    def gpu_mem_limit_changed(self, limit: int):
        print('GPU memory limit changed to {} MB'.format(limit))
        self.__gpu_mem_limit = limit
        used_mem = 0
        for render_widget in self.__render_widgets.values():
            used_mem += render_widget.mem_size
            render_widget.is_gpu = used_mem < limit
