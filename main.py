import sys
import threading
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QLabel, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from views import ViewManager  # Import ViewManager class from views.py
from PIL import Image

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Navbar Example with Image")
        self.resize(400, 400)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        self.content_label = QLabel("Welcome! Click a menu option to display content.")
        self.layout.addWidget(self.content_label)
        self.image_label = None
        self.content_label = None
        self.create_menu_bar()
        self.start_view_running_status = 0
        self.ui_stop_event = threading.Event()  # Stop event for the UI update thread
        self.ui_update_thread = None

    def create_menu_bar(self):
        """Create the menu bar and add options to it."""
        menu_bar = self.menuBar()
        view_menu = menu_bar.addMenu("View")
        start_view_action = QAction("Start View", self)
        start_view_action.triggered.connect(self.show_start_view)
        view_menu.addAction(start_view_action)

        help_menu = menu_bar.addMenu("Help")
        help_action = QAction("Hello Help", self)
        help_action.triggered.connect(self.show_hello_help)
        help_menu.addAction(help_action)

    def display_view_image_repeatedly_threader(self):
        print("Initialized display view image threader")
        while not self.ui_stop_event.is_set():  # Checking for the stop signal
            image = self.vm.zoom_at_image(display_size=self.vm.display_image_size)
            if image:
                image_data = image.tobytes()
                qimage = QImage(image_data, self.vm.display_image_size, self.vm.display_image_size,
                                self.vm.display_image_size * 3, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage)
                if self.image_label:
                    self.image_label.setPixmap(pixmap)
            time.sleep(self.vm.thread_pauser)

    def show_start_view(self):
        if self.start_view_running_status == 1:
            msg = QMessageBox()
            msg.setWindowTitle("Warning")
            msg.setText("Magnifier is already running.")
            msg.setIcon(QMessageBox.Warning)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setDefaultButton(QMessageBox.Ok)
            result = msg.exec_()
            if result == QMessageBox.Ok:
                print("Duplicate request detected.")
        
        if self.start_view_running_status == 0:
            if self.content_label:
                self.content_label.clear()
            self.image_label = QLabel("Zoomed-in Image Here")
            self.layout.addWidget(self.image_label)
            self.vm = ViewManager()

            # Start threads for the magnifier
            screenshot_view_thread = threading.Thread(target=self.vm.start_threader_for_view)
            screenshot_view_thread.daemon = True
            screenshot_view_thread.start()

            # Restart the UI update thread
            if self.ui_update_thread and self.ui_update_thread.is_alive():
                print("Stopping the old UI update thread...")
                self.ui_stop_event.set()
                self.ui_update_thread.join(timeout=5)
                self.ui_update_thread = None  # Reset thread reference

            # Initialize new thread for UI update
            self.ui_stop_event.clear()  # Clear the stop event
            self.ui_update_thread = threading.Thread(target=self.display_view_image_repeatedly_threader)
            self.ui_update_thread.daemon = True
            self.ui_update_thread.start()

            self.start_view_running_status = 1

    def show_hello_help(self):
        """Display the Hello Help content."""
        if self.start_view_running_status == 1:
            print("Stopping UI update thread...")
            self.vm.stop_threads()  # Stop all threads in ViewManager
            self.ui_stop_event.set()  # Signal the UI update thread to stop

            # Wait for the UI update thread to terminate safely
            self.ui_update_thread.join(timeout=5)  # Timeout after 5 seconds
            if self.ui_update_thread.is_alive():
                print("UI update thread did not terminate within the timeout")
            else:
                print("UI update thread stopped successfully.")

            self.image_label.clear()
            self.layout.removeWidget(self.image_label)
            self.image_label.deleteLater()
            self.image_label = None
            self.start_view_running_status = 0
        if self.content_label:
            self.content_label.setText("Hello Help: This is the content for the Help menu!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
