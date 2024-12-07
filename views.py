import threading
import time
import mss
from pynput.mouse import Listener
from PIL import Image, ImageDraw
import io


class ViewManager:
    def __init__(self):
        self.mouse_position = (0, 0)
        self.screenshot_image = None
        self.thread_pauser = 0.1
        self.display_image_size = 400
        self.zoom_factor = 2
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.last_mouse_position = (0, 0)

    def get_mouse_position(self):
        with self.lock:
            return self.mouse_position

    def set_mouse_position(self, x, y):
        with self.lock:
            self.mouse_position = (x, y)

    def take_screenshot_timely_threader(self):
        """Continuously capture the screen."""
        print("initlilized screennshot taker threader")
        with mss.mss() as sct:
            while not self.stop_event.is_set():
                try:
                    mouse_x, mouse_y = self.get_mouse_position()
                    if (mouse_x, mouse_y) != self.last_mouse_position:
                        # print("Taking screenshot...")
                        screenshot = sct.grab(sct.monitors[0])
                        screenshot_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)
                        with self.lock:
                            self.screenshot_image = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
                        self.last_mouse_position = (mouse_x, mouse_y)
                    # else:
                    #     print("Mouse position unchanged; not updating screenshot.")
                except Exception as e:
                    print(f"Error capturing screenshot: {e}")
                time.sleep(self.thread_pauser)

    
    def zoom_at_image(self, display_size=None, geom_cords=None):
        if not self.screenshot_image:
            return Image.new("RGB", (display_size, display_size), "black")
        try:
            window_width = geom_cords.width()
            window_height = geom_cords.height()
            window_x = geom_cords.x()
            window_y = geom_cords.y()
            screenshot_width, screenshot_height = self.screenshot_image.size
            mouse_x, mouse_y = self.get_mouse_position()
            last_mouse_position = self.last_mouse_position
            if (mouse_x,mouse_y) == (last_mouse_position):
                # print("not zooming")
                return None
            if window_x <= mouse_x <= (window_x + window_width) and window_y <= mouse_y <= (window_y + window_height):
                # print("not zooming")
                return None
            crop_size = display_size // self.zoom_factor
            left = max(0, mouse_x - crop_size // 2)
            top = max(0, mouse_y - crop_size // 2)
            right = min(screenshot_width, left + crop_size)
            bottom = min(screenshot_height, top + crop_size)
            cropped_region = self.screenshot_image.crop((left, top, right, bottom))
            zoomed_region = cropped_region.resize((display_size, display_size), Image.Resampling.LANCZOS)
            self.last_mouse_position = (mouse_x,mouse_y)
            return zoomed_region
        except Exception as e:
            print(f"Error: {e}")
            return Image.new("RGB", (display_size, display_size), "black")

    def start_threader_for_view(self):
        """Start threads for mouse tracking and screenshot capture."""
        print("Starting threads...")
        def on_move(x, y):
            self.set_mouse_position(x, y)

        self.stop_event.clear()

        # Start mouse listener thread
        self.mouse_listener_thread = threading.Thread(target=lambda: Listener(on_move=on_move).run())
        self.mouse_listener_thread.daemon = True
        self.mouse_listener_thread.start()
        print("innitialized mouse position threader")

        # Start screenshot capture thread
        self.screenshot_thread = threading.Thread(target=self.take_screenshot_timely_threader)
        self.screenshot_thread.daemon = True
        self.screenshot_thread.start()

    def stop_threads(self):
        """Stop all threads."""
        print("Stopping threads...")
        self.stop_event.set()
        if hasattr(self, 'mouse_listener_thread') and self.mouse_listener_thread.is_alive():
            self.mouse_listener_thread.join(timeout=1)
        if hasattr(self, 'screenshot_thread') and self.screenshot_thread.is_alive():
            self.screenshot_thread.join(timeout=1)
