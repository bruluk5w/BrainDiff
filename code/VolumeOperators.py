from enum import IntEnum
from typing import List, Sequence

import numpy as np
import vtk
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkFiltersCore import vtkMarchingCubes
from vtkmodules.vtkFiltersGeneral import vtkDiscreteFlyingEdges3D

from common import convert


class Operator(IntEnum):
    UNION = 0
    INTERSECTION = 1
    ADDITION = 2


def rebuild(volumes: Sequence[np.ndarray], labels: List[int], operator: Operator, template_image, iso_value: float):
    if not volumes or not labels:
        return []

    shape = volumes[0].shape
    assert all(v.shape == shape for v in volumes)

    if operator == Operator.UNION:
        numpy_type = np.bool
        reduction_op = np.bitwise_or.reduce
        vtk_type = vtk.VTK_UNSIGNED_CHAR
    elif operator == Operator.INTERSECTION:
        numpy_type = np.bool
        reduction_op = np.bitwise_and.reduce
        vtk_type = vtk.VTK_UNSIGNED_CHAR
    elif operator == Operator.ADDITION:
        numpy_type = np.ubyte
        reduction_op = np.sum
        vtk_type = vtk.VTK_UNSIGNED_CHAR
    else:
        raise RuntimeError('Unknown volume operator')

    source = np.stack(volumes, axis=-1)
    fes = []
    for label in labels:
        result = reduction_op(source == label, axis=3, dtype=numpy_type)
        image = vtkImageData()
        image.CopyStructure(template_image)
        image.GetPointData().SetScalars(convert(result, dtype=vtk_type))
        fe = vtkMarchingCubes() # vtkDiscreteFlyingEdges3D()
        fe.SetNumberOfContours(1)
        if operator == Operator.ADDITION:
            fe.SetValue(0, iso_value)
        else:
            fe.SetValue(0, 1)

        fe.SetInputDataObject(0, image)
        image.Modified()
        fes.append(fe)

    return fes
