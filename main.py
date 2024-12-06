import sys
import threading
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QLabel, QVBoxLayout, QWidget, QMessageBox, QPushButton
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from views import ViewManager, NewWindowLens

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
        self.start_view_running_status = 0
        self.ui_stop_event = threading.Event()
        self.ui_update_thread = None
        self.inactivity_timer = None  
        self.dupllicatepixmap = None
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

    def display_view_image_repeatedly_threader(self, location):
        """ Update image in the given QLabel location repeatedly """
        print("Initialized display view image threader")
        while not self.ui_stop_event.is_set():
            geom_cords = self.geometry()
            image = self.vm.zoom_at_image(display_size=self.vm.display_image_size,geom_cords=geom_cords)
            if image:
                image_data = image.tobytes()
                qimage = QImage(image_data, self.vm.display_image_size, self.vm.display_image_size,
                                self.vm.display_image_size * 3, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage)
                if location:
                    location.setPixmap(pixmap)# Update the image in the QLabel
                    self.dupllicatepixmap = pixmap
            time.sleep(self.vm.thread_pauser)

    def show_start_view(self):
        if self.start_view_running_status == 1:
            QMessageBox.warning(self, "Warning", "Magnifier is already running.")
            return

        if self.start_view_running_status == 0:
            if self.content_label:
                self.content_label.clear()
            self.image_label = QLabel("Zoomed-in Image Here")
            self.layout.addWidget(self.image_label)
            self.vm = ViewManager()

            screenshot_view_thread = threading.Thread(target=self.vm.start_threader_for_view)
            screenshot_view_thread.daemon = True
            screenshot_view_thread.start()

            if self.ui_update_thread and self.ui_update_thread.is_alive():
                self.ui_stop_event.set()
                self.ui_update_thread.join(timeout=5)
                self.ui_update_thread = None  

            self.ui_stop_event.clear()
            self.ui_update_thread = threading.Thread(target=self.display_view_image_repeatedly_threader, args=(self.image_label,))
            self.ui_update_thread.daemon = True
            self.ui_update_thread.start()

            self.start_view_running_status = 1
            self.button = QPushButton("Open New Window")
            self.button.clicked.connect(self.open_new_window)
            self.layout.addWidget(self.button)

    def pause_all_threads_for_ui(self):
        print("Stopping UI update thread...")
        self.vm.stop_threads()
        self.ui_stop_event.set()
        
        if self.ui_update_thread and self.ui_update_thread.is_alive():
            self.ui_update_thread.join(timeout=5)

        if self.image_label:
            self.image_label.clear()
            self.layout.removeWidget(self.image_label)
            self.image_label.deleteLater()
            self.image_label = None
        
        label = QLabel("External window started!")
        self.layout.addWidget(label)
        self.start_view_running_status = 0
        return 1

    def open_new_window(self):
        def move_and_display_window():
            while self.vm.external_window_follow_mouse:
                x, y = self.vm.mouse_position
                self.new_window.follow_mouse(x, y)
                self.new_window.image_label.setPixmap(self.dupllicatepixmap)
                time.sleep(self.vm.thread_pauser)

        self.vm.external_window_follow_mouse = True
        self.new_window = NewWindowLens()
        self.vm.external_window = self.new_window
        self.new_window.show()
        threading.Thread(target=move_and_display_window, daemon=True).start()

    def show_hello_help(self):
        if self.start_view_running_status == 1:
            self.pause_all_threads_for_ui()
        if self.content_label:
            self.content_label.setText("Hello Help: This is the content for the Help menu!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
    
    # next task