from enum import IntEnum
from typing import Optional

from PySide6.QtWidgets import QApplication
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleJoystickActor, vtkInteractorStyleJoystickCamera, \
    vtkInteractorStyleTrackballActor, vtkInteractorStyleTrackballCamera, vtkInteractorStyleSwitch, \
    vtkInteractorStyleMultiTouchCamera

from .DataView import DataView
from .Delegate import Delegate
from .LabelColorWidget import *
from .InputForwardingRenderWindowInteractor import InputForwardingRenderWindowInteractor

clamp = (lambda x, a, b: min(max(x, a), b))

__app: Optional[QApplication] = None


def get_app() -> Optional[QApplication]:
    return __app


def set_app(app: QApplication):
    global __app
    __app = app


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
