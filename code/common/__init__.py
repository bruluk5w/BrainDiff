from vtkmodules.vtkCommonDataModel import vtkColor3ub

from .Delegate import Delegate
from .LabelColorWidget import *


clamp = (lambda x, a, b: min(max(x, a), b))
