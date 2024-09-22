from dataclasses import dataclass, field
from typing import List
import logging

@dataclass
class KeyboardEmulator:
    hid_path: str
    current_keys: List[int] = field(default_factory=list)  # 当前按住的按键
    control_keys: int = 0  # 修饰键状态
    logger: logging.Logger  # 接收传入的 Logger


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
        self.control_keys |= control_keys

        # 如果是普通按键，将其添加到 current_keys 中（确保按键不会重复添加）
        if hid_keycode and hid_keycode not in self.current_keys:
            self.current_keys.append(hid_keycode)

        # 发送更新后的按键状态
        self.send()

    def release_key(self, control_keys=0, hid_keycode=None):
        """
        处理松开按键的动作，更新按键状态。
        
        :param control_keys: 修饰键状态（可选）
        :param hid_keycode: 普通按键键码（可选）
        """
        # 更新修饰键状态，使用按位与操作清除相应的修饰键
        self.control_keys &= ~control_keys

        # 如果是普通按键，从 current_keys 中移除
        if hid_keycode and hid_keycode in self.current_keys:
            self.current_keys.remove(hid_keycode)

        # 发送更新后的按键状态
        self.send()

    def release_all(self):
        """
        释放所有按键和修饰键。
        """
        self.current_keys.clear()
        self.control_keys = 0
        self.send()

# def send(hid_path, control_keys, *hid_keycodes):
#     with open(hid_path, 'wb+') as hid_handle:
#         buf = [0] * 8
#         buf[0] = control_keys
#         for index, hid_keycode in enumerate(hid_keycodes):
#             if index > 5:
#                 return
#             buf[2+index] = hid_keycode
#         hid_handle.write(bytearray(buf))

def reset(hid_path):
    with open(hid_path, 'wb+') as hid_handle:
        hid_handle.write(bytearray([0] * 8))