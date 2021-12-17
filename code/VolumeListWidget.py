from typing import List

import numpy as np
from PySide6.QtWidgets import QWidget, QListWidgetItem, QListWidget
from VolumeListItem import VolumeListItem


class VolumeListWidget(QListWidget):
    def __init__(self, volume_list: List[np.ndarray], parent=None):
        super().__init__(parent)
        self.__volume_list = volume_list
        for idx in range(len(volume_list)):
            custom_widget = VolumeListItem(idx, self)
            custom_widget.set_text(str(idx))
            item = QListWidgetItem(self)
            item.setSizeHint(custom_widget.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, custom_widget)

    def __getitem__(self, item):
        assert isinstance(item, int)
        assert item < len(self.__volume_list)
        return self.__volume_list[item]
