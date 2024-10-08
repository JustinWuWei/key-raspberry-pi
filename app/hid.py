from dataclasses import dataclass, field
import os
from typing import List, Dict
import threading
import logging
import time
import json


@dataclass
class KeyboardEmulator:
    hid_path: str
    dir_path = './recordDir/'
    logger: logging.Logger  # 接收传入的 Logger
    current_keys: List[int] = field(default_factory=list)  # 当前按住的按键
    control_keys: int = 0  # 修饰键状态
    recording: List[Dict] = field(default_factory=list)  # 用于存储录制的按键事件
    is_record: bool = False
    is_stop_playback: threading.Event = field(default_factory=threading.Event)  # 用于控制按键回放


    def send(self):
        """
        发送当前按键状态到 HID 设备，包括修饰键和普通按键。
        """
        buf = [0] * 8
        buf[0] = self.control_keys  # 设置修饰键的状态
        # 设置按键状态，最多支持 6 个按键
        for i in range(min(len(self.current_keys), 6)):
            buf[2 + i] = self.current_keys[i]
        # 写入 HID 报告
        with open(self.hid_path, 'wb+') as hid_handle:
            hid_handle.write(bytearray(buf))
        self.logger.info('Send buf %s ', buf )


    def press_key(self, control_keys=0, hid_keycode=None):
        """
        处理按下按键的动作，更新按键状态。
        
        :param control_keys: 修饰键状态（可选）
        :param hid_keycode: 普通按键键码（可选）
        """
        # 更新修饰键状态
        self.control_keys = control_keys

        # 如果是普通按键，将其添加到 current_keys 中（确保按键不会重复添加）
        if hid_keycode and hid_keycode not in self.current_keys:
            self.current_keys.append(hid_keycode)

        # 发送更新后的按键状态
        self.send()
        if self.is_record:
            self.__record_event(control_keys, hid_keycode, "press")


    def release_key(self, control_keys=0, hid_keycode=None):
        """
        处理松开按键的动作，更新按键状态。
        
        :param control_keys: 修饰键状态（可选）
        :param hid_keycode: 普通按键键码（可选）
        """
        # 更新修饰键状态，使用按位与操作清除相应的修饰键
        self.control_keys = control_keys


        # 如果是普通按键，从 current_keys 中移除
        if hid_keycode and hid_keycode in self.current_keys:
            self.current_keys.remove(hid_keycode)

        # 发送更新后的按键状态
        self.send()
        if self.is_record:
            self.__record_event(control_keys, hid_keycode, "release")


    def release_all(self):
        """
        释放所有按键和修饰键。
        """
        self.current_keys.clear()
        self.control_keys = 0
        self.send()

    def start_record(self):
        self.recording = []
        self.is_record = True


    def save_record(self, saveFileName = "testRecord.json"):
        """
        保存录制的按键事件到文件。
        """
        self.is_record = False
         # 计算每个事件相对于第一个事件的时间差，转成相对时间戳
        if self.recording:
            start_time = self.recording[0]['timestamp']
            for event in self.recording:
                event['timestamp'] -= start_time

        if not os.path.exists(self.dir_path):
            os.mkdir(self.dir_path)
        file_full_path = os.path.join(self.dir_path, saveFileName)
        with open(file_full_path, 'w') as f:
            json.dump(self.recording, f, indent=4)
        self.recording = []
        self.logger.info(f"Recording saved to {file_full_path}")


    def load_recording(self, loadFileName = "testRecord.json"):
        """
        从文件加载录制的按键事件。
        """
        file_full_path = os.path.join(self.dir_path, loadFileName)
        with open(file_full_path, 'r') as f:
            self.recording = json.load(f)
        
        self.logger.info(f"Recording loaded from {file_full_path}")


    def __play_recording(self):
        """
        按照录制的顺序播放按键事件。
        """
        if not self.recording:
            self.logger.warning("No recording loaded.")
            return

        start_time = time.time()
        self.is_stop_playback.clear()  # 重置停止事件

        for event in self.recording:
            if self.is_stop_playback.is_set():
                self.logger.info("Playback stopped.")
                self.release_all()
                break
            # 计算需要等待的时间
            time_to_wait = event['timestamp'] - (time.time() - start_time)
            if time_to_wait > 0:
                time.sleep(time_to_wait)
            
            if event['event'] == "press":
                self.press_key(event['control_keys'], event['keycode'])
            elif event['event'] == "release":
                self.release_key(event['control_keys'], event['keycode'])
        self.logger.info("Finished playing recording.")


    def start_playback(self):
        """
        开始按键回放
        """
        playback_thread = threading.Thread(target=self.__play_recording)
        playback_thread.start()


    def stop_playback(self):
        """
        结束按键回放
        """
        self.is_stop_playback.set()


    def __record_event(self,control_keys, hid_keycode, event_type):
        event = {
            "timestamp": time.time(),
            "event": event_type,
            "control_keys": control_keys,
            "keycode": hid_keycode
        }
        self.recording.append(event)
        self.logger.info(f"Recorded event: {event}")
