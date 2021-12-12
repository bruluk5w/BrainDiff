# coding=utf-8

import sys

from vtkmodules.vtkFiltersSources import vtkConeSource
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper, vtkRenderer
# load implementations for rendering and interaction factory classes
import vtkmodules.vtkRenderingOpenGL2
import vtkmodules.vtkInteractionStyle

import QVTKRenderWindowInteractor as QVTK
QVTKRenderWindowInteractor = QVTK.QVTKRenderWindowInteractor

if QVTK.PyQtImpl == 'PySide6':
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget
elif QVTK.PyQtImpl == 'PySide2':
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QApplication, QMainWindow
else:
    from PySide.QtCore import Qt
    from PySide.QtGui import QApplication, QMainWindow


class SampleWidget(QWidget):
    def __init__(self, app):
        super().__init__()
        self.vertical_layout = QVBoxLayout(self)
        self.button = QPushButton(text="Push Me", )
        self.button.clicked.connect(lambda: print("hello world"))
        self.vertical_layout.addWidget(self.button)
        self.renderWidget = QVTKRenderWindowInteractor()
        self.vertical_layout.addWidget(self.renderWidget)

        # if you don't want the 'q' key to exit comment this.
        self.renderWidget.AddObserver("ExitEvent", lambda o, e, a=app: a.quit())

        self.ren = vtkRenderer()
        self.renderWidget.GetRenderWindow().AddRenderer(self.ren)

        self.cone = vtkConeSource()
        self.cone.SetResolution(8)

        self.coneMapper = vtkPolyDataMapper()
        self.coneMapper.SetInputConnection(self.cone.GetOutputPort())

        self.coneActor = vtkActor()
        self.coneActor.SetMapper(self.coneMapper)

        self.ren.AddActor(self.coneActor)

        # show the widget
        #window.show()

        self.renderWidget.Initialize()
        self.renderWidget.Start()


def QVTKRenderWidgetConeExample(argv):
    """A simple example that uses the QVTKRenderWindowInteractor class."""
    # every QT app needs an app
    app = QApplication(['QVTKRenderWindowInteractor'])
    window = QMainWindow()
    ourAppWidget = SampleWidget(app)
    window.setCentralWidget(ourAppWidget)
    window.show()

    # create the widget


    # start event processing
    # Source: https://doc.qt.io/qtforpython/porting_from2.html
    # 'exec_' is deprecated and will be removed in the future.
    # Use 'exec' instead.
    try:
        app.exec()
    except AttributeError:
        app.exec_()


if __name__ == "__main__":
    QVTKRenderWidgetConeExample(sys.argv)
