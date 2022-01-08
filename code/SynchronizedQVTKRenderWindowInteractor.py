from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkRenderingCore import vtkRenderWindow
from vtkmodules.vtkRenderingUI import vtkGenericRenderWindowInteractor

from common import Delegate


class HookedInteractor(vtkGenericRenderWindowInteractor):
    on_change = Delegate()

    def Render(self, src=None):
        if src is not self:
            super().Render()
            if src is None:
                print('Interactor Render')
                self.on_change(self)

    def TimerEvent(self):
        super().TimerEvent()
        self.on_change(self)

    def MouseMoveEvent(self):
        super().MouseMoveEvent()
        self.on_change(self)

    def MouseWheelForwardEvent(self):
        super().MouseWheelForwardEvent()
        self.on_change(self)

    def MouseWheelBackwardEvent(self):
        super().MouseWheelBackwardEvent()
        self.on_change(self)


class SynchronizedQVTKRenderWindowInteractor(QVTKRenderWindowInteractor):
    on_key_press_event = Delegate()
    on_key_release_event = Delegate()

    def __init__(self, *k, **kw):
        assert 'iren' not in kw and 'rw' not in kw
        kw['iren'] = interactor = HookedInteractor()
        kw['rw'] = rw = vtkRenderWindow()
        interactor.SetRenderWindow(rw)

        super().__init__(*k, **kw)
        # self.on_render += self.handle_render
        # self.on_paint += self.handle_paint
        interactor.on_change += self.on_change
        self.on_key_press_event += self.keyPressEvent
        self.on_key_release_event += self.keyReleaseEvent

    def on_change(self, src):
        if src is not self._Iren:
            self._Iren.Render(src)

    def keyPressEvent(self, ev, src=None):
        if src is not self:
            super().keyPressEvent(ev)
            if src is None:
                self.on_key_press_event(ev, self)

    def keyReleaseEvent(self, ev, src=None):
        if src is not self:
            super().keyReleaseEvent(ev)
            if src is None:
                self.on_key_release_event(ev, self)
