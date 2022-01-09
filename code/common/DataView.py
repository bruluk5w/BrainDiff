import abc

import numpy as np
from PySide6.QtWidgets import QWidget


class WidgetMeta(type(QWidget), abc.ABCMeta):
    pass


class DataView(QWidget, metaclass=WidgetMeta):
    def __init__(self, gpu_limit: int, parent=None):
        super().__init__(parent=parent)
        self.__active = False
        self._gpu_mem_limit = gpu_limit

    def gpu_mem_limit_changed(self, limit: int):
        print('GPU memory limit changed to {} MB'.format(limit))
        self._gpu_mem_limit = limit

    @property
    def active(self):
        return self.__active

    @active.setter
    def active(self, value: bool):
        if value != self.__active:
            if value:
                self._activate()
            else:
                self._deactivate()

            self.__active = value

    @abc.abstractmethod
    def _activate(self):
        pass

    @abc.abstractmethod
    def _deactivate(self):
        pass

    @abc.abstractmethod
    def add_volume(self, idx: int, volume: np.ndarray):
        pass

    @abc.abstractmethod
    def remove_volume(self, idx: int):
        pass

    @property
    @abc.abstractmethod
    def name(self):
        pass