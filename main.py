# This Python file uses the following encoding: utf-8
import sys
from PySide6.QtWidgets import QApplication

from wallpaper_downloader import WallpaperDownloader

# if __name__ == "__main__":
#     app = QApplication([])
#     widget = WallpaperDownloader(debug=False)
#     sys.exit(app.exec())
app = QApplication([])
widget = WallpaperDownloader(debug=False)
sys.exit(app.exec())
