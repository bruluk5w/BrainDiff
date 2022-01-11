from enum import IntEnum
from math import cos, pi

from PySide6.QtWidgets import QWidget, QVBoxLayout
from vtkmodules.vtkImagingCore import vtkImageBlend
from vtkmodules.vtkRenderingCore import vtkRenderWindow, vtkActor2D, vtkRenderer, vtkImageMapper

from RenderWidget import SynchronizedRenderWidget
from SynchronizedQVTKRenderWindowInteractor import SynchronizedQVTKRenderWindowInteractor
from common import InputForwardingRenderWindowInteractor, clamp


class SmoothType(IntEnum):
    DISCRETE = 0
    LINEAR = 1
    EASE = 2
    ALL = 3


class InterchangeableView:
    """
    Accepts RenderWidgets, composites their off-screen-rendered results and displays the result in a given widget.
    """

    def __init__(self, view_container: QWidget, smooth_type: SmoothType):
        """
        :param view_container: The widget in which the composited result is displayed
        """
        assert view_container is not None
        self._parent = view_container
        self._smooth_type = smooth_type

        self.graphics_target_window = None
        self.interactor = None
        self.composite_image_widget = None

        # image compositing setup
        self.imageRenderer = vtkRenderer()
        self.actor = vtkActor2D()
        self.imageRenderer.AddActor2D(self.actor)
        self.mapper = vtkImageMapper()
        self.actor.SetMapper(self.mapper)
        self.mapper.SetColorWindow(255)
        self.mapper.SetColorLevel(127.5)
        self._image_blend = vtkImageBlend()
        self._image_blend.SetBlendModeToCompound()
        self.imageRenderer.SetBackground(0, 0, 0)
        self.imageRenderer.ResetCamera()

        self.linked_renderer = None
        self.added_renderers = set()

        self._t = 0

    @property
    def count(self):
        return self._image_blend.GetNumberOfInputConnections(0)

    @property
    def smooth_type(self):
        return self._smooth_type

    @smooth_type.setter
    def smooth_type(self, value: bool):
        if self._smooth_type != value:
            self._smooth_type = value
            self.set_page(self._t)

    def set_page(self, page: float):
        n = self.count
        if self.smooth_type == SmoothType.DISCRETE:
            map_x = lambda x: 1 if -0.5 <= x < 0.5 else 0
        elif self.smooth_type == SmoothType.LINEAR:
            map_x = lambda x: 1 - abs(x)
        elif self.smooth_type == SmoothType.EASE:
            map_x = lambda x: 0.5 * (1 + cos(x * pi))
        else:
            map_x = None

        self._t = t = clamp(page, 0, n - 1)
        if self.smooth_type == SmoothType.ALL:
            opacities = [1] * n
        else:
            opacities = [
                map_x(x - t) if -1 <= x - t <= 1 else 0
                for x in range(n)
            ]

        for i, o in enumerate(opacities):
            self._image_blend.SetOpacity(i, o)

    def _get_opacity(self, v):
        pass

    def add(self, renderer: SynchronizedRenderWidget):
        assert renderer not in self.added_renderers
        self.added_renderers.add(renderer)
        n = len(self.added_renderers)

        if n == 1:
            self.mapper.SetInputConnection(0, self._image_blend.GetOutputPort())

        self._image_blend.AddInputConnection(0, renderer.off_screen_img_output)
        self.set_page(self._t)

        if self.linked_renderer is None:
            self._link(renderer)

    def remove(self, renderer: SynchronizedRenderWidget):
        if renderer not in self.added_renderers:
            return

        self.added_renderers.remove(renderer)
        if self.linked_renderer is renderer:
            self._unlink()

        if self._image_blend.GetNumberOfInputConnections(0) == 1:
            self.mapper.SetInputConnection(0, None)

        self._image_blend.RemoveInputConnection(0, renderer.off_screen_img_output)
        self.set_page(self._t)

        if self.linked_renderer is None and self.added_renderers:
            self._link(next(iter(self.added_renderers)))

    def _link(self, renderer):
        """
        _link and _unlink make sure that the input from self.composite_image_widget is always relayed to one of the
        synchronized 3D volume renderers.
        """
        self.linked_renderer = renderer
        # we draw the composited image to this vtk render window
        self.graphics_target_window = vtkRenderWindow()
        # but we route the input events from the QVTK render window widget to one of the synchronized volume rendering
        # interactors
        self.interactor = InputForwardingRenderWindowInteractor(renderer.renderWindowWidget.interactor)
        self.composite_image_widget = SynchronizedQVTKRenderWindowInteractor(rw=self.graphics_target_window,
                                                                             iren=self.interactor)
        # we still provide the vtk render window that we would normally supply, but it will only receive events for e.g.
        # resizing but no interactions
        self.interactor.SetRenderWindow(self.graphics_target_window)

        if self._parent.layout() is not None:
            QWidget().setLayout(self._parent.layout())
            self._parent.setLayout(None)

        self._parent.setLayout(QVBoxLayout())
        self._parent.layout().setContentsMargins(0, 0, 0, 0)
        self._parent.layout().addWidget(self.composite_image_widget)

        self.graphics_target_window.AddRenderer(self.imageRenderer)
        self.composite_image_widget.show()

    def _unlink(self):
        """
        _link and _unlink make sure that the input from self.composite_image_widget is always relayed to one of the
        synchronized 3D volume renderers.
        """
        self.composite_image_widget.hide()
        self.graphics_target_window.RemoveRenderer(self.imageRenderer)
        self.graphics_target_window.SetInteractor(None)
        self.imageRenderer.SetRenderWindow(None)
        self.composite_image_widget.setParent(None)
        QWidget().setLayout(self._parent.layout())
        self._parent.setLayout(None)
        self.interactor.SetRenderWindow(None)
        self.composite_image_widget.close()
        self.composite_image_widget = None
        self.interactor = None
        self.graphics_target_window = None
        self.linked_renderer = None

    def set_geometry(self, rect):
        self.composite_image_widget.setGeometry(rect)

    def finalize(self):
        # Todo: check reference counts
        assert self._image_blend.GetTotalNumberOfInputConnections() == 0
        self.mapper.SetInputConnection(0, None)
        self.actor.SetMapper(None)
        self.imageRenderer.RemoveActor2D(self.actor)
        self.actor = None
        self.imageRenderer = None
        self.mapper = None
        self._image_blend = None
        self._parent = None
