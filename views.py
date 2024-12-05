import threading
import time
import mss
from pynput.mouse import Listener
from screeninfo import get_monitors
from PIL import Image, ImageDraw, ImageGrab
import io
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QDialog


class ViewManager:
    def __init__(self):
        self.mouse_position = (0, 0)
        self.d_width = 0
        self.d_height = 0
        self.screenshot_image = None  
        self.thread_pauser = 0.1
        self.display_image_size = 400
        self.zoom_factor = 2
        self.stop_event = threading.Event()  # stop threads
        self.ui_stop_event = threading.Event()  # stop UI update thread
        self.external_window_follow_mouse = False
        self.external_winndow = None

    def get_screen_resolution(self):
        monitors = get_monitors()
        main_monitor = monitors[0]
        self.d_width = main_monitor.width
        self.d_height = main_monitor.height
        print(f"Screen resolution for {main_monitor.name}, {self.d_width}, {self.d_height}")

    def get_mouse_position(self):
        return self.mouse_position
    
    def get_window_geometry(self):
        if self.external_window:
            self.window_geom = self.external_window.geometry()
            return self.window_geom

    def take_screenshot_timely_threader(self):
        print("Initialized continue screenshot taker threader")
        with mss.mss() as sct:
            while not self.stop_event.is_set():
                raw_screenshot = sct.grab(sct.monitors[0])
                screenshot_bytes = mss.tools.to_png(raw_screenshot.rgb, raw_screenshot.size)
                self.screenshot_image = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
                time.sleep(self.thread_pauser)

    def zoom_at_image(self, display_size=None):
        if not self.screenshot_image:
            return Image.new("RGB", (display_size, display_size), "black")
        try:
            screenshot_width, screenshot_height = self.screenshot_image.size
            mouse_x, mouse_y = self.get_mouse_position()
            crop_size = display_size // self.zoom_factor
            left = max(0, mouse_x - crop_size // 2)
            top = max(0, mouse_y - crop_size // 2)
            cropped_region = self.screenshot_image.crop((left, top, left + crop_size, top + crop_size))
            zoomed_region = cropped_region.resize((display_size, display_size), Image.Resampling.LANCZOS)
            return zoomed_region
        except Exception as e:
            print(f"Error: {e}")
            return Image.new("RGB", (display_size, display_size), "black")

    def start_threader_for_view(self):
        print("Initializing threads...")
        self.stop_event.clear()  # Reset the stop event
        self.get_screen_resolution()

        def on_move(x, y):
            self.mouse_position = (x, y)

        self.mouse_listener_thread = threading.Thread(target=lambda: Listener(on_move=on_move).run())
        self.mouse_listener_thread.daemon = True
        self.mouse_listener_thread.start()

        self.screenshot_thread = threading.Thread(target=self.take_screenshot_timely_threader)
        self.screenshot_thread.daemon = True
        self.screenshot_thread.start()

    def stop_threads(self):
        print("Stopping threads...")
        self.stop_event.set()  # Signal threads to stop
        self.ui_stop_event.set()  # Stop UI update thread
        
    def enable_mouse_follow(self):
        self.external_window_follow_mouse = True

    def disable_mouse_follow(self):
        self.external_window_follow_mouse = False

class NewWindowLens(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("New Window")
        self.resize(300, 200)

        # Create layout and add QLabel for displaying image
        self.layout = QVBoxLayout()
        self.image_label = QLabel("Image will appear here")
        self.layout.addWidget(self.image_label)

        self.setLayout(self.layout)

    def follow_mouse(self, x, y):
        self.move(x - self.width() // 2, y - self.height() // 2)

    def set_image(self, pixmap):
        self.image_label.setPixmap(pixmap)