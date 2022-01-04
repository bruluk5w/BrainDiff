from typing import List, Dict

import numpy as np
from PySide6.QtWidgets import QWidget, QSplitter, QGridLayout, QVBoxLayout, QPushButton
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonDataModel import vtkImageData

from RenderWidget import SynchronizedRenderWidget
from VolumeListWidget import VolumeListWidget





class MainWidget(QWidget):

    def __init__(self, image: vtkImageData, volume_list: List[np.ndarray], gpu_mem_limit: int):
        super().__init__()
        self.__color_list = [vtkNamedColors().GetColor3d("Black"),  # 0 Volume Border
                             vtkNamedColors().GetColor3d("Banana"),  # 1 Cerebrospinal Fluid
                             vtkNamedColors().GetColor3d("Gray"),  # 2 Gray Matter
                             vtkNamedColors().GetColor3d("White"),  # 3 White Matter
                             vtkNamedColors().GetColor3d("Raspberry"),  # 4 Fat
                             vtkNamedColors().GetColor3d("Tomato"),  # 5 Muscle
                             vtkNamedColors().GetColor3d("Flesh"),  # 6 Muscle/Skin
                             vtkNamedColors().GetColor3d("Wheat"),  # 7 Skull
                             vtkNamedColors().GetColor3d("Blue"),  # 8 Vessels
                             vtkNamedColors().GetColor3d("Mint"),  # 9 Around Fat
                             vtkNamedColors().GetColor3d("Peacock"),  # 10 Dura Matter
                             vtkNamedColors().GetColor3d("Salmon")]  # 11 Bone Marrow
        self.__active_regions = [4, 10]
        self.__gpu_mem_limit = gpu_mem_limit
        self.__template_image = image
        self.__render_widgets: Dict[int, SynchronizedRenderWidget] = {}
        self.__volume_list_widget = VolumeListWidget(volume_list,
                                                     selection_added_cb=self.add_volume,
                                                     selection_removed_cb=self.remove_volume)
        self.__vertical_layout = QVBoxLayout(self)

        self.__list_splitter = QSplitter()
        self.__list_splitter.setChildrenCollapsible(False)
        self.__list_splitter.addWidget(self.__volume_list_widget)
        self.__region_selection = QWidget(self)
        self.__region_selection_layout = QVBoxLayout(self.__region_selection)
        self.__dummybutton = QPushButton("Adjust Regions")
        self.__dummybutton.clicked.connect(lambda: self.add_shown_regions())
        self.__region_selection_layout.addWidget(self.__dummybutton)
        self.__list_splitter.addWidget(self.__region_selection)

        self.__main_splitter = QSplitter()
        self.__main_splitter.setChildrenCollapsible(False)
        self.__main_splitter.addWidget(self.__list_splitter)
        self.__grid_container = QWidget()
        self.__main_splitter.addWidget(self.__grid_container)
        self.__vertical_layout.addWidget(self.__main_splitter)

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
        else:
            image = vtkImageData()
            image.CopyStructure(self.__template_image)
            render_widget = SynchronizedRenderWidget(is_gpu, image, volume, idx, self.__color_list, self.__active_regions)
            render_widget.active = True
            self.__render_widgets[idx] = render_widget

        self.layout()

    def remove_volume(self, idx: int):
        print('Volume {} removed.'.format(idx))
        if idx in self.__render_widgets:
            renderer = self.__render_widgets[idx]
            renderer.active = False
        else:
            print('Error: no volume {} that could be removed.'.format(idx))

        self.layout()

    def add_shown_regions(self):
        self.__active_regions = [5, 9]
        for i, renderer in enumerate(t for t in self.__render_widgets.values()):
            renderer.update_shown_regions(self.__active_regions)


    def layout(self):
        for renderer in self.__render_widgets.values():
            renderer.setParent(None)

        # reparent layout and child widgets to temporary which will be deleted the proper way
        QWidget().setLayout(self.__grid_container.layout())

        layout = QGridLayout()
        layout.setSpacing(0)
        self.__grid_container.setLayout(layout)
        num_widgets = sum(1 for r in self.__render_widgets.values() if r.active)
        layout_side_size = _next_square(num_widgets)
        for i, renderer in enumerate(t for t in self.__render_widgets.values() if t.active):
            row = i // layout_side_size
            layout.addWidget(renderer, row, i - layout_side_size * row)

    def gpu_mem_limit_changed(self, limit: int):
        print('GPU memory limit changed to {} MB'.format(limit))
        self.__gpu_mem_limit = limit
        used_mem = 0
        for render_widget in self.__render_widgets.values():
            used_mem += render_widget.mem_size
            render_widget.is_gpu = used_mem < limit

    def closeEvent(self, event):
        super().closeEvent(event)
        for renderer in self.__render_widgets.values():
            renderer.close()


def _next_square(n: int):
    i = 0
    while i * i < n:
        i += 1

    return i
