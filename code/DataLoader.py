from os import listdir
from os.path import isfile, join
from vtkmodules.util.numpy_support import vtk_to_numpy
from PySide6.QtCore import QThread, Signal
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkIOMINC import vtkMINCImageReader
from vtkmodules.vtkImagingCore import vtkImageCast


class DataLoader(QThread):

    progress = Signal(int)
    done = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__data_path = "../Data/"
        self.__dataFiles = [f for f in listdir(self.__data_path) if isfile(join(self.__data_path, f))]
        self.__npDataList = []
        self.__image = None

    def __len__(self):
        return len(self.__dataFiles)

    @property
    def data(self):
        return self.__npDataList

    @property
    def image(self) -> vtkImageData:
        return self.__image

    def run(self):
        reader = vtkMINCImageReader()
        image_cast = vtkImageCast()
        image_cast.SetInputConnection(0, reader.GetOutputPort())
        image_cast.SetOutputScalarTypeToUnsignedChar()
        for idx, file in enumerate(self.__dataFiles):
            reader.SetFileName(self.__data_path + file)
            reader.Update()
            image_cast.Update()
            image = image_cast.GetOutputDataObject(0)  # type: vtkImageData
            ext = image.GetExtent()
            dim = (ext[1] - ext[0] + 1, ext[3] - ext[2] + 1, ext[5] - ext[4] + 1)
            self.__npDataList.append(vtk_to_numpy(image.GetPointData().GetScalars()).reshape(dim))
            self.progress.emit(idx + 1)

        self.__image = image
        self.done.emit()

