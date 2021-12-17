from typing import Callable

from PySide6.QtCore import QThread, SIGNAL, Signal


class DataLoader(QThread):

    progress = Signal(int)
    done = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__length = 20

    def __len__(self):
        return self.__length

    def run(self):
        import time
        for i in range(10):
            time.sleep(0.2)
            self.progress.emit(i + 1)

        self.done.emit()

    def __del__(self):
        self.exiting = True
        self.wait()

