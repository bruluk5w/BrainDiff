
from PySide6.QtWidgets import QWidget, QVBoxLayout
from vtkmodules.vtkImagingCore import vtkImageBlend
from vtkmodules.vtkRenderingCore import vtkRenderWindow, vtkActor2D, vtkRenderer, vtkImageMapper

from RenderWidget import SynchronizedRenderWidget
from SynchronizedQVTKRenderWindowInteractor import SynchronizedQVTKRenderWindowInteractor
from common import InputForwardingRenderWindowInteractor


class InterchangeableView:
    """
    Accepts RenderWidgets, composits their off-screen-rendered results and displays the result in a given widget.
    """
    def __init__(self, view_container: QWidget):
        """
        :param view_container: The widget in which the composited result is displayed
        """
        assert view_container is not None
        self._parent = view_container

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

    def add(self, renderer: SynchronizedRenderWidget):
        assert renderer not in self.added_renderers
        self.added_renderers.add(renderer)
        n = len(self.added_renderers)

        if n == 1:
            self.mapper.SetInputConnection(0, self._image_blend.GetOutputPort())

        for i in range(n):
            self._image_blend.SetOpacity(i, 1/n)

        self._image_blend.AddInputConnection(0, renderer.off_screen_img_output)

        if self.linked_renderer is None:
            self._link(renderer)

    def remove(self, renderer: SynchronizedRenderWidget):
        if renderer not in self.added_renderers:
            return

        self.added_renderers.remove(renderer)
        if self.linked_renderer is renderer:
            self._unlink()

        if self._image_blend.GetTotalNumberOfInputConnections() == 1:
            self.mapper.SetInputConnection(0, None)

        self._image_blend.RemoveInputConnection(0, renderer.off_screen_img_output)

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
