import sys
import threading
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QLabel, QVBoxLayout, QWidget, QMessageBox, QComboBox
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

        # Main UI elements
        self.content_label = QLabel("Welcome! Click a menu option to display content.")
        self.layout.addWidget(self.content_label)

        self.image_label = QLabel()
        self.layout.addWidget(self.image_label)

        self.vm = None
        self.ui_stop_event = threading.Event()
        self.ui_update_thread = None
        self.start_view_running_status = 0

        self.lens_size_combobox = None
        self.zoom_size_combobox = None

        self.create_menu_bar()

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # Create View menu
        view_menu = menu_bar.addMenu("View")
        start_view_action = QAction("Start View", self)
        start_view_action.triggered.connect(self.show_start_view)
        view_menu.addAction(start_view_action)

        # Create Help menu
        help_menu = menu_bar.addMenu("Help")
        help_action = QAction("Hello Help", self)
        help_action.triggered.connect(self.show_hello_help)
        help_menu.addAction(help_action)

    def change_lens_size(self):
        value = int(self.lens_size_combobox.currentText())
        self.vm.display_image_size = value
        self.content_label.setText(f"Ring size: {value}")

    def change_lens_zoom_size(self):
        value = int(self.zoom_size_combobox.currentText())
        self.vm.zoom_factor = value
        self.content_label.setText(f"Zoom size: {value}")

    def display_view_image_repeatedly(self):
        print("initialized image displayer thread")
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

        # Clear UI for new View
        self.clear_ui_for_new_view()

        # Initialize ViewManager if it's not already running
        if not self.vm:
            self.vm = ViewManager(main_window=self)
            self.vm.start_threader_for_view()

        # Dynamically create sliders
        self.lens_size_combobox = QComboBox()
        self.lens_size_combobox.addItems([str(size) for size in [100, 150, 200, 250, 300, 350, 400, 450, 500]])
        self.lens_size_combobox.currentIndexChanged.connect(self.change_lens_size)

        self.zoom_size_combobox = QComboBox()
        self.zoom_size_combobox.addItems([str(zoom) for zoom in range(1, 11)])
        self.zoom_size_combobox.currentIndexChanged.connect(self.change_lens_zoom_size)

        # Add sliders dynamically to UI
        self.layout.addWidget(self.lens_size_combobox)
        self.layout.addWidget(self.zoom_size_combobox)

        self.ui_stop_event.clear()
        self.ui_update_thread = threading.Thread(target=self.display_view_image_repeatedly)
        self.ui_update_thread.daemon = True
        self.ui_update_thread.start()

        self.start_view_running_status = 1

    def show_hello_help(self):
        self.pause_all_threads_for_ui()
        self.clear_ui_for_new_view()
        self.content_label.setText("Hello Help: This is the content for the Help menu!")

    def pause_all_threads_for_ui(self):
        if self.vm:
            self.vm.stop_threads()
        self.ui_stop_event.set()
        if self.ui_update_thread and self.ui_update_thread.is_alive():
            self.ui_update_thread.join()
        self.start_view_running_status = 0

    def clear_ui_for_new_view(self):
        """
        Clears UI elements and resets view-related UI.
        This ensures a clean slate for View and Help switching.
        """
        self.content_label.setText("Welcome! Click a menu option to display content.")
        self.image_label.clear()

        # Remove dynamically added lens/zoom combo boxes
        if self.lens_size_combobox:
            self.layout.removeWidget(self.lens_size_combobox)
            self.lens_size_combobox.deleteLater()
            self.lens_size_combobox = None

        if self.zoom_size_combobox:
            self.layout.removeWidget(self.zoom_size_combobox)
            self.zoom_size_combobox.deleteLater()
            self.zoom_size_combobox = None

        self.ui_stop_event.set()
        if self.ui_update_thread and self.ui_update_thread.is_alive():
            self.ui_update_thread.join()
        self.ui_stop_event.clear()
        self.start_view_running_status = 0


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
