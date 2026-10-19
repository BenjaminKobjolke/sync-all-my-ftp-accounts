"""Manual check: a menu still takes arrow keys after a subprocess inherited the console."""

import subprocess

from ftp_sync import menu
from ftp_sync.app_logger import AppLogger

first = menu.show_menu(["one", "two", "three"], "Menu 1 - use arrow keys, Enter")
subprocess.run(["cmd", "/c", "echo subprocess with inherited console ran"], check=True)
second = menu.show_multiselect(["a", "b", "c"], "Menu 2 - arrows + Space, Enter")
AppLogger.info(f"Selected {first} and {second} - arrow keys worked in both menus.")
