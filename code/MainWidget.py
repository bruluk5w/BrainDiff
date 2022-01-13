from typing import List

import numpy as np
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget, QSplitter, QVBoxLayout, QTabWidget, QSizePolicy
from vtkmodules.vtkCommonDataModel import vtkImageData

from PreservingDataView import PreservingDataView
from VolumeListWidget import VolumeListWidget
from ExplicitEncodingDataView import ExplicitEncodingDataView


class MainWidget(QWidget):

    def __init__(self, image: vtkImageData, volume_list: List[np.ndarray], gpu_mem_limit: int):
        super().__init__()
        self.__volume_list_widget = VolumeListWidget(volume_list,
                                                     selection_added_cb=self.add_volume,
                                                     selection_removed_cb=self.remove_volume)
        # Main Split
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(splitter := QSplitter())
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.__volume_list_widget)

        self.__dataViews = QTabWidget()
        splitter.addWidget(self.__dataViews)
        max_width = QGuiApplication.primaryScreen().size().width()
        splitter.setSizes([self.__volume_list_widget.sizeHint().width(), max_width])

        self.__dataViews.addTab(view := PreservingDataView(image, gpu_mem_limit), view.name)
        self.__dataViews.addTab(view := ExplicitEncodingDataView(image, gpu_mem_limit), view.name)
        self.__last_tab_idx = 0

        self.__active_volumes = {}

        self.__dataViews.currentChanged.connect(self._handle_data_view_changed)
        self.__dataViews.setCurrentIndex(self.__last_tab_idx)
        self.__volume_list_widget.item(0).setSelected(True)

    def _handle_data_view_changed(self, idx: int):
        for i in self.__active_volumes:
            self.__dataViews.widget(self.__last_tab_idx).remove_volume(i)

        self.__dataViews.widget(self.__last_tab_idx).active = False
        self.__last_tab_idx = idx
        self.__dataViews.widget(self.__last_tab_idx).active = True
        for i, volume in self.__active_volumes.items():
            self.__dataViews.widget(self.__last_tab_idx).add_volume(i, volume)

    def add_volume(self, idx: int, volume: np.ndarray):
        print('Volume {} added.'.format(idx))
        self.__active_volumes[idx] = volume
        self.__dataViews.currentWidget().add_volume(idx, volume)

    def remove_volume(self, idx: int):
        print('Volume {} removed.'.format(idx))
        del self.__active_volumes[idx]
        self.__dataViews.currentWidget().remove_volume(idx)

    def gpu_mem_limit_changed(self, limit: int):
        print('GPU memory limit changed to {} MB'.format(limit))
        for idx in range(self.__dataViews.count()):
            self.__dataViews.widget(idx).gpu_mem_limit_changed(limit)

    def closeEvent(self, event):
        super().closeEvent(event)
        for idx in range(self.__dataViews.count()):
            self.__dataViews.widget(idx).close()
