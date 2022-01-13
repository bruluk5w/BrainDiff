from vtkmodules.vtkRenderingCore import vtkRenderWindowInteractor
from vtkmodules.vtkRenderingUI import vtkGenericRenderWindowInteractor


class InputForwardingRenderWindowInteractor(vtkRenderWindowInteractor):

    def __init__(self, target_interactor: vtkGenericRenderWindowInteractor, *args, **kv):
        super().__init__(*args, **kv)
        self._target_interactor = target_interactor

    def SetSize(self, _arg1, _arg2):
        # only forward input events, resizing is forwarded to target render window
        super().SetSize(_arg1, _arg2)
        super().GetRenderWindow().SetSize(_arg1, _arg2)
        return self._target_interactor.SetSize(_arg1, _arg2)

    def ConfigureEvent(self):
        # only forward input events, resizing is forwarded to target render window
        return super().ConfigureEvent()

    def Render(self, *args, **kv):
        # forward render event to both
        super().GetRenderWindow().Render()
        return self._target_interactor.Render(*args, **kv)

    def GetRenderWindow(self):
        # return target window for behaviour as if we were interacting with the target window
        return self._target_interactor.GetRenderWindow()

    def AddObserver(self, *args, **kv):
        return self._target_interactor.AddObserver(*args, **kv)

    def RemoveObserver(self, __a):
        return self._target_interactor.RemoveObserver(__a)

    def SetEventInformation(self, *args,  **kv):
        # super().SetEventInformation(*args, **kv)
        return self._target_interactor.SetEventInformation(*args, **kv)

    def EnterEvent(self):
        # super().EnterEvent()
        return self._target_interactor.EnterEvent()

    def RightButtonPressEvent(self):
        # super().RightButtonPressEvent()
        return self._target_interactor.RightButtonPressEvent()

    def CharEvent(self):
        # super().CharEvent()
        return self._target_interactor.CharEvent()

    def KeyPressEvent(self):
        # super().KeyPressEvent()
        return self._target_interactor.KeyPressEvent()

    def KeyReleaseEvent(self):
        # super().KeyReleaseEvent()
        return self._target_interactor.KeyReleaseEvent()

    def MouseMoveEvent(self):
        # super().MouseMoveEvent()
        return self._target_interactor.MouseMoveEvent()

    def RightButtonReleaseEvent(self):
        # super().RightButtonReleaseEvent()
        return self._target_interactor.RightButtonReleaseEvent()

    def LeaveEvent(self):
        # super().LeaveEvent()
        return self._target_interactor.LeaveEvent()

    def LeftButtonPressEvent(self):
        # super().LeftButtonPressEvent()
        return self._target_interactor.LeftButtonPressEvent()

    def LeftButtonReleaseEvent(self):
        # super().LeftButtonReleaseEvent()
        return self._target_interactor.LeftButtonReleaseEvent()

    def MiddleButtonPressEvent(self):
        # super().MiddleButtonPressEvent()
        return self._target_interactor.MiddleButtonPressEvent()

    def MiddleButtonReleaseEvent(self):
        # super().MiddleButtonReleaseEvent()
        return self._target_interactor.MiddleButtonReleaseEvent()

    def MouseWheelBackwardEvent(self):
        # super().MouseWheelBackwardEvent()
        return self._target_interactor.MouseWheelBackwardEvent()

    def MouseWheelForwardEvent(self):
        # super().MouseWheelForwardEvent()
        return self._target_interactor.MouseWheelForwardEvent()

    def TimerEvent(self):
        return self._target_interactor.TimerEvent()

    def GetInteractorStyle(self):
        return self._target_interactor.GetInteractorStyle()
