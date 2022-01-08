from typing import Callable

from common import Delegate
from .EditableIntervalSlider import EditableIntervalSlider
from .Popup import Popup


class Settings:
    def __init__(self):
        self.__gpu_mem_limit = 1 << 10
        self.__on_gpu_mem_limit_changed = Delegate()

    def set_gpu_mem_limit_ui(self):
        SetGpuMemLimitUI(self)

    @property
    def gpu_mem_limit(self):
        return self.__gpu_mem_limit

    @gpu_mem_limit.setter
    def gpu_mem_limit(self, value):
        self.__gpu_mem_limit = value
        self.__on_gpu_mem_limit_changed(value)

    @property
    def gpu_mem_limit_changed(self):
        return self.__on_gpu_mem_limit_changed

    @gpu_mem_limit_changed.setter
    def gpu_mem_limit_changed(self, value):
        assert value is self.__on_gpu_mem_limit_changed


class SetGpuMemLimitUI(Popup):
    def __init__(self, settings: Settings, cb: Callable[[], None] = None):
        super().__init__(cb, "Set GPU Memory Limit")
        self.__settings = settings
        self.__slider = EditableIntervalSlider(minimum=0, maximum=8192, unit='MB')
        self.layout().addWidget(self.__slider)
        self.__slider.set_value(self.__settings.gpu_mem_limit)
        self.__slider.value_changed.connect(self.set_value)
        self.show()

    def set_value(self, v):
        self.__settings.gpu_mem_limit = v
