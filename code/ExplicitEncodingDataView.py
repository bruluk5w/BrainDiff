import numpy as np
from vtkmodules.vtkCommonDataModel import vtkImageData

from common import DataView


class ExplicitEncodingDataView(DataView):
    @property
    def name(self):
        return 'Explicit Encoding'

    def _activate(self):
        print('activate')

    def __init__(self, image: vtkImageData, gpu_limit: int, parent=None):
        super().__init__(gpu_limit, parent)
        self.__template_image = image

    def _deactivate(self):
        print('deactivate')

    def add_volume(self, idx: int, volume: np.ndarray):
        print('add volume')

    def remove_volume(self, idx: int):
        print('remove volume')

    def gpu_mem_limit_changed(self, limit: int):
        super().gpu_mem_limit_changed(limit)

