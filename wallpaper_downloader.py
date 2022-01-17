import os
import threading
from pathlib import Path
from PIL import ImageFont, ImageDraw

from PySide6 import QtGui
from PySide6.QtWidgets import QComboBox, QGridLayout, QMainWindow, QSpinBox, QStatusBar, QLabel, QPushButton
from PySide6.QtCore import QFile, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QImage, QPixmap

from categorys_chooser import CategorysChooser
from widgets import ClickedQLabel
import utils


class WallpaperDownloader(QMainWindow):
    def __init__(self,debug=False):
        self.debug = debug
        
        super(WallpaperDownloader, self).__init__()
        self.load_ui()
        self.set_listener()
        
        self.thread_loaddata = threading.Thread(target=self.load_data)
        self.category_idx = 0
        self.category_loaded = False
        
        # if self.thread_loaddata.is_alive():
        #     self.
        self.thread_loaddata.start()

    def load_ui(self):
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "wallpaper_downloader.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        self.window = loader.load(ui_file)
        ui_file.close()
        self.setCentralWidget(self.window)
        self.setWindowTitle(self.window.windowTitle())
        self.resize(self.window.size())
        self.show()

        self.setStatusBar(self.findChild(QStatusBar,'statusbar'))
        
        self.sem_previewloading = threading.Semaphore(1)
        self.previewloading_num = 0
        self.status_previewloading = QLabel("正在加载：{} 张图片".format(self.previewloading_num),self)
        self.statusBar().addPermanentWidget(self.status_previewloading)
        
        self.sem_download = threading.Semaphore(1)
        self.download_num = 0
        self.status_download = QLabel("正在下载：{} 张图片".format(self.download_num),self)
        self.statusBar().addPermanentWidget(self.status_download)
        
        self.combobox_order = self.findChild(QComboBox,'comboBox_order')
        self.combobox_order.addItems(['new','hot'])
        
        self.gridLayout = self.findChild(QGridLayout,'gridLayout')
        
        ori_labels = [(self.findChild(QLabel,'label_'+str(i))) 
                       for i in range(1,12+1)]
        self.labels = [ClickedQLabel(oril) for oril in ori_labels]
        for oril,l in zip(ori_labels,self.labels):
            self.gridLayout.replaceWidget(oril,l)
        
        self.btn_choose = self.findChild(QPushButton,'pushButton')
        
        self.btn_prepage = self.findChild(QPushButton,'pushButton_2')
        self.btn_postpage = self.findChild(QPushButton,'pushButton_3')
        self.spinbox_page = self.findChild(QSpinBox,'spinBox')

        self.category_chooser = CategorysChooser(self)

    def load_data(self):
        if self.debug:
            print('分类 {} 加载中...'.format(self.category_idx))
        if not self.category_loaded:
            self.categorys = utils.getCategorys()
            self.category_loaded = True
        self.wallpapers = utils.getWallpapers(self.categorys[self.category_idx]['id'],
                                              page=self.spinbox_page.value(),
                                              pagesize=len(self.labels),
                                              order=self.combobox_order.currentText())
        imgload_th = [threading.Thread(target=self.load_img,args=(i,'（图{}）'.format(i+1))) 
                      for i in range(len(self.labels))]
        for idx in range(len(self.labels)):
            imgload_th[idx].start()

    def set_listener(self):
        self.btn_choose.clicked.connect(lambda:self.category_chooser.show())
        
        for idx,label in enumerate(self.labels):
            label.leftbutton_clicked.connect(lambda idx=idx:self.download_wallpaper_thd(idx))
            
        for idx,label in enumerate(self.category_chooser.labels):
            label.leftbutton_clicked.connect(lambda idx=idx:self.choose_category(idx))
            label.rightbutton_clicked.connect(lambda idx=idx:self.download_category_cover_trd(idx))
            
        self.combobox_order.currentIndexChanged.connect(self.load_data)
        # self.spinbox_page.valueChanged.connect(self.load_data)
        self.btn_postpage.clicked.connect(lambda:self.page_switch(+1))
        self.btn_prepage.clicked.connect(lambda:self.page_switch(-1))

    def load_img(self,idx,text=None,debug=False):
        self.sem_previewloading.acquire()
        self.previewloading_num += 1
        self.status_previewloading.setText("正在加载：{} 张图片".format(self.previewloading_num))
        self.sem_previewloading.release()
        url = self.wallpapers[idx]["preview"]
        img = utils.getImageFromUrl(url,resize=(600,360))
        if text is not None:
            draw = ImageDraw.Draw(img)
            setFont = ImageFont.truetype('source/SourceHanSerifSC-Bold.otf',30)
            draw.text((40,40),text,font=setFont,fill='#000000',direction=None)
        img = QImage(img.convert('RGB').tobytes(),
                     img.size[0],
                     img.size[1],
                     QImage.Format_RGB888)
        img = QPixmap(img)
        img = img.scaled(self.labels[0].size(),
                         Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                         Qt.TransformationMode.SmoothTransformation)
        self.labels[idx].setPixmap(img)

        self.statusBar().showMessage("图片 {} 加载成功".format(idx+1))
        self.sem_previewloading.acquire()
        self.previewloading_num -= 1
        self.status_previewloading.setText("正在加载：{} 张图片".format(self.previewloading_num))
        self.sem_previewloading.release()
        if debug:
            print("index {} have loaded.".format(idx))
        
    def choose_category(self,idx):
        self.btn_choose.setText('选择分类（{}）'.format(self.categorys[idx]['rname']))
        self.category_idx = idx
        self.load_data()
        self.category_chooser.hide()
        
    def page_switch(self,switch_num=1):
        self.spinbox_page.setValue(self.spinbox_page.value()+switch_num)
        self.load_data()
            
    def download_wallpaper_thd(self,idx=1):
        dl_thd = threading.Thread(
            target=self.download_wallpaper,
            args=(idx,))
        dl_thd.start()
        
    def download_wallpaper(self,idx):
        self.sem_download.acquire()
        self.download_num += 1
        self.status_download.setText("正在下载：{} 张图片".format(self.download_num))
        self.sem_download.release()
        utils.download_wallpaper_byidx(rname=self.categorys[self.category_idx]['rname'],
                                 wallpapers=self.wallpapers,
                                 idx=idx,
                                 debug=True)
        self.statusBar().showMessage("图片 {} 下载完成".format(idx+1))
        self.sem_download.acquire()
        self.download_num -= 1
        self.status_download.setText("正在下载：{} 张图片".format(self.download_num))
        self.sem_download.release()
        
    def download_category_cover_trd(self,idx):
        dl_thd = threading.Thread(
            target=self.download_category_cover,
            args=(idx,))
        dl_thd.start()
        
    def download_category_cover(self,idx,debug=False):
        self.sem_download.acquire()
        self.download_num += 1
        self.status_download.setText("正在下载：{} 张图片".format(self.download_num))
        self.sem_download.release()
        category = self.categorys[idx]
        cover = category['cover']
        url = utils.getDlUrlFromURL(cover)
        utils.download_wallpaper(category['rname'],
                                 url,
                                 category['picasso_cover'],
                                 debug=debug)
        self.statusBar().showMessage("图片 {} 下载完成".format(category['rname']))
        self.sem_download.acquire()
        self.download_num -= 1
        self.status_download.setText("正在下载：{} 张图片".format(self.download_num))
        self.sem_download.release()
        
    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == Qt.Key_Enter:
            self.load_data()
        return super().keyPressEvent(event)
        
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.category_chooser.close()
        return super().closeEvent(event)