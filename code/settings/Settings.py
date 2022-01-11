from typing import Callable

from PySide6.QtWidgets import QLabel
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
        self.layout().addWidget(label := QLabel())
        label.setWordWrap(True)
        label.setText('This sets the amount of raw volume data that the application may load to GPU memory. Above this '
                      'limit slower CPU renderers will be used. Note that this limit does not incldue any additional '
                      'framebufferes or other resources. For example, the application may consume significantly more '
                      'GPU memory when run fullscreen on a 4k monitor. Overallocation my lead to the application being '
                      'terminated.')
        self.layout().addWidget(slider := EditableIntervalSlider(minimum=0, maximum=8192, unit='MB'))
        slider.set_value(self.__settings.gpu_mem_limit)
        slider.value_changed.connect(self.set_value)
        self.show()

    def set_value(self, v):
        self.__settings.gpu_mem_limit = v
