from typing import Optional

from PySide6.QtWidgets import QApplication

from .DataView import DataView
from .Delegate import Delegate
from .LabelColorWidget import *

clamp = (lambda x, a, b: min(max(x, a), b))


__app: Optional[QApplication] = None


def get_app() -> Optional[QApplication]:
    return __app


def set_app(app: QApplication):
    global __app
    __app = app
