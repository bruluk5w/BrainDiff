from PySide6.QtWidgets import QApplication, QMainWindow
from MainWidget import MainWidget


def main():
    """A simple example that uses the QVTKRenderWindowInteractor class."""
    # every QT app needs an app
    app = QApplication(['QVTKRenderWindowInteractor'])
    window = QMainWindow()
    app_widget = MainWidget(app)
    window.setCentralWidget(app_widget)
    window.show()

    app.exec()


if __name__ == "__main__":
    main()