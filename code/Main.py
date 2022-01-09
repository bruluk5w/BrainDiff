from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from MainWindow import MainWindow
from common import set_app


def main():
    # every QT app needs an app
    app = QApplication(['QVTKRenderWindowInteractor'])
    set_app(app)
    app.setApplicationDisplayName('BrainDiff')
    app.setApplicationName('BrainDiff')

    font = QFont("Liberation Mono")
    font.setStyleHint(QFont.Monospace)
    app.setFont(font)

    __window = MainWindow(app)
    app.exec()


if __name__ == "__main__":
    main()
