import sys
import threading
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QLabel, QVBoxLayout, QWidget, QMessageBox, QPushButton
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from views import ViewManager

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zoomer Lens")
        self.resize(400, 400)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.content_label = QLabel("Welcome! Click a menu option to display content.")
        self.layout.addWidget(self.content_label)

        self.image_label = QLabel()
        self.layout.addWidget(self.image_label)

        self.vm = None
        self.ui_stop_event = threading.Event()
        self.ui_update_thread = None
        self.start_view_running_status = 0

        self.create_menu_bar()

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        view_menu = menu_bar.addMenu("View")
        start_view_action = QAction("Start View", self)
        start_view_action.triggered.connect(self.show_start_view)
        view_menu.addAction(start_view_action)

        help_menu = menu_bar.addMenu("Help")
        help_action = QAction("Hello Help", self)
        help_action.triggered.connect(self.show_hello_help)
        help_menu.addAction(help_action)

    def display_view_image_repeatedly(self):
        print("innitiallized image displayer threader")
        while not self.ui_stop_event.is_set():
            if self.vm:
                if self.vm.last_mouse_position != self.vm.get_mouse_position():
                    zoomed_image = self.vm.zoom_at_image(display_size=self.vm.display_image_size, geom_cords=self.geometry())
                    if zoomed_image:
                        image_data = zoomed_image.tobytes()
                        qimage = QImage(image_data, self.vm.display_image_size, self.vm.display_image_size,
                                        self.vm.display_image_size * 3, QImage.Format_RGB888)
                        pixmap = QPixmap.fromImage(qimage)
                        self.image_label.setPixmap(pixmap)
                time.sleep(self.vm.thread_pauser)

    def show_start_view(self):
        if self.start_view_running_status == 1:
            QMessageBox.warning(self, "Warning", "Magnifier is already running.")
            return

        if not self.vm:
            self.vm = ViewManager()
            self.vm.start_threader_for_view()

        self.ui_stop_event.clear()
        self.ui_update_thread = threading.Thread(target=self.display_view_image_repeatedly)
        self.ui_update_thread.daemon = True
        self.ui_update_thread.start()

        self.start_view_running_status = 1

    def show_hello_help(self):
        if self.start_view_running_status == 1:
            self.pause_all_threads_for_ui()
        self.content_label.setText("Hello Help: This is the content for the Help menu!")

    def pause_all_threads_for_ui(self):
        if self.vm:
            self.vm.stop_threads()
        self.ui_stop_event.set()
        self.start_view_running_status = 0


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())