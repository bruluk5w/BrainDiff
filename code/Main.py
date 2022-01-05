from typing import Optional

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMainWindow

from MainWindow import MainWindow

__app: Optional[QApplication] = None


def main():
    global __app
    # every QT app needs an app
    __app = QApplication(['QVTKRenderWindowInteractor'])
    __app.setApplicationDisplayName('BrainDiff')
    __app.setApplicationName('BrainDiff')

    font = QFont("Liberation Mono")
    font.setStyleHint(QFont.Monospace)
    __app.setFont(font)

    __window = MainWindow(__app)
    __app.exec()


if __name__ == "__main__":
    main()
