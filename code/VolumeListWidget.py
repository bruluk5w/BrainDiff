from typing import List, Callable
from itertools import chain
import numpy as np
from PySide6.QtCore import QItemSelection, QItemSelectionRange
from PySide6.QtWidgets import QListWidgetItem, QListWidget, QAbstractItemView
from VolumeListItem import VolumeListItem


class VolumeListWidget(QListWidget):
    def __init__(self, volume_list: List[np.ndarray], parent=None,
                 selection_added_cb: Callable[[int, np.ndarray], None] = None,
                 selection_removed_cb: Callable[[int], None] = None):
        super().__init__(parent)
        self.__volume_list = volume_list
        self.__selection_added_cb = selection_added_cb
        self.__selection_removed_cb = selection_removed_cb
        self.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for idx in range(len(volume_list)):
            custom_widget = VolumeListItem(idx, self)
            custom_widget.set_text(str(idx))
            item = QListWidgetItem(self)
            item.setSizeHint(custom_widget.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, custom_widget)
            item.setSelected(custom_widget.selected)

    def __getitem__(self, idx):
        assert isinstance(idx, int)
        assert idx < len(self.__volume_list)
        return self.__volume_list[idx]

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        super().selectionChanged(selected, deselected)
        selected_indices = [s.row() for s in chain.from_iterable(s.indexes() for s in selected)]
        deselected_indices = [s.row() for s in chain.from_iterable(s.indexes() for s in deselected)]
        for idx in selected_indices:
            volume_list_item = self.itemWidget(self.item(idx))
            volume_list_item.selected = True
            if self.__selection_added_cb is not None:
                self.__selection_added_cb(idx, self[idx])

        for idx in deselected_indices:
            volume_list_item = self.itemWidget(self.item(idx))
            volume_list_item.selected = False
            if self.__selection_removed_cb is not None:
                self.__selection_removed_cb(idx)
