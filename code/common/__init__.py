from enum import IntEnum
from typing import Optional

import vtk
from PySide6.QtWidgets import QApplication, QComboBox
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleJoystickActor, vtkInteractorStyleJoystickCamera, \
    vtkInteractorStyleTrackballActor, vtkInteractorStyleTrackballCamera, vtkInteractorStyleSwitch, \
    vtkInteractorStyleMultiTouchCamera

from .DataView import DataView
from .Delegate import Delegate
from .FloatSlider import FloatSlider
from .InputForwardingRenderWindowInteractor import InputForwardingRenderWindowInteractor
from .LabelColorWidget import *

__app: Optional[QApplication] = None


def get_app() -> Optional[QApplication]:
    return __app


def set_app(app: QApplication):
    global __app
    __app = app


def convert(numpy_array, dtype=vtk.VTK_UNSIGNED_CHAR, deep=True):
    # If Deep is True, the array is deep-copied from numpy. This is not as efficient as the default
    # behavior and uses more memory but detaches the two arrays such that the numpy array can be released
    return numpy_to_vtk(numpy_array.ravel(), deep=deep, array_type=dtype)


def make_opacity_value(x):
    return x / 255


def make_color_value(c: vtkColor3ub):
    return [c[0] / 255, c[1] / 255, c[2] / 255]


class InteractorStyle(IntEnum):
    JOYSTICK_ACTOR = 0
    JOYSTICK_CAMERA = 1
    TRACKBALL_ACTOR = 2
    TRACKBALL_CAMERA = 3
    MULTI_TOUCH_CAMERA = 4


def get_interactor_style(style: vtkInteractorStyleSwitch) -> InteractorStyle:
    c = style.GetCurrentStyle()
    if isinstance(c, vtkInteractorStyleJoystickActor):
        return InteractorStyle.JOYSTICK_ACTOR
    elif isinstance(c, vtkInteractorStyleJoystickCamera):
        return InteractorStyle.JOYSTICK_CAMERA
    elif isinstance(c, vtkInteractorStyleTrackballActor):
        return InteractorStyle.TRACKBALL_ACTOR
    elif isinstance(c, vtkInteractorStyleTrackballCamera):
        return InteractorStyle.TRACKBALL_CAMERA
    elif isinstance(c, vtkInteractorStyleMultiTouchCamera):
        return InteractorStyle.MULTI_TOUCH_CAMERA
    else:
        raise Exception('Unknown vtk interactor style!')


def set_interactor_style(style: vtkInteractorStyleSwitch, s: InteractorStyle) -> None:
    if s == InteractorStyle.JOYSTICK_ACTOR:
        style.SetCurrentStyleToJoystickActor()
    elif s == InteractorStyle.JOYSTICK_CAMERA:
        style.SetCurrentStyleToJoystickCamera()
    elif s == InteractorStyle.TRACKBALL_ACTOR:
        style.SetCurrentStyleToTrackballActor()
    elif s == InteractorStyle.TRACKBALL_CAMERA:
        style.SetCurrentStyleToTrackballCamera()
    elif s == InteractorStyle.MULTI_TOUCH_CAMERA:
        style.SetCurrentStyleToMultiTouchCamera()
    else:
        raise Exception('Unknown vtk interactor style!')


def combo_box_add_enum_items(cb: QComboBox, enum):
    for e in enum:
        cb.addItem(e.name, e)
