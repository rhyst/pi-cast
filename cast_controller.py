import pychromecast
from memoization import cached
from funcy import some, first
from collections import namedtuple
import time

CastDevice = namedtuple("CastDevice", ["id", "uuid", "type", "name", "address", "port"])

class CastController:
    device = None
    browser = None
    media_controller = None
    available_devices = []

    def __init__(self, device_name = None):
        self.get_devices()
        if device_name or len(self.available_devices):
            self.set_device(device_name or self.available_devices[0].name)
    
    @cached(ttl=300)
    def get_devices(self):
        chromecasts, browser = pychromecast.discover_chromecasts()
        pychromecast.discovery.stop_discovery(browser)
        self.available_devices = list(map(lambda x: CastDevice(*x), chromecasts))
        return chromecasts

    def set_device(self, device_name):
        chromecasts, self.browser = pychromecast.get_listed_chromecasts(
            friendly_names=[device_name or self.available_devices[0].name]
        )
        self.device = first(chromecasts) 
        if self.device:
            self.device.wait()
        return self.device

    def get_status(self):
        if not self.device:
            return {"connected": False}
        self.device.wait()
        print(self.device)
        print(self.device.status)
        print(self.device.media_controller.status.player_state)
        return {
            "connected": True,
            "name": self.device.name,
            "is_idle": self.device.status.app_id is None,
            "display_name": self.device.status.display_name,
            "status_text": self.device.status.status_text,
            "volume": int(self.device.status.volume_level * 100),
            "playing": self.device.media_controller.status.player_state == "PLAYING"
        }

    def play(self, url, media_type, title=None):    
        if not self.device:
            return
        print("Playing " + url)
        self.device.media_controller.play_media(url, media_type, title=title)
        t = 5
        while (self.device.status.app_id is None or self.device.status.status_text == 'Default Media Receiver') and t > 0:
            time.sleep(0.1)
            t = t - 0.1
        self.device.media_controller.block_until_active()
        self.device.wait()

    def pause(self):    
        if not self.device:
            return
        self.device.media_controller.pause()
        self.device.wait()
    
    def resume(self):    
        if not self.device:
            return
        self.device.media_controller.play()
        self.device.wait()

    def stop(self):
        if not self.device:
            return
        self.device.quit_app()
        t = 5
        while self.device.status.app_id is not None and t > 0:
            time.sleep(0.1)
            t = t - 0.1

    def set_volume(self, level):
        if not self.device:
            return
        self.device.set_volume(level)
        self.device.wait()

    def quit(self):
        if self.browser:
            pychromecast.discovery.stop_discovery(self.browser)
