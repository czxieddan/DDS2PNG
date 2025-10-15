import os
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QWidget, QFileDialog, QPushButton, QVBoxLayout, QLabel,
    QProgressBar, QMessageBox, QHBoxLayout, QRadioButton, QCheckBox, QFrame
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QCursor
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

class SwitchButton(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 22)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self.isChecked():
            p.setBrush(QBrush(QColor("#4caf50")))
            p.setPen(QPen(QColor("#388e3c")))
        else:
            p.setBrush(QBrush(QColor("#e0e0e0")))
            p.setPen(QPen(QColor("#b0b0b0")))
        p.drawRoundedRect(1, 1, 38, 20, 10, 10)
        if self.isChecked():
            p.setBrush(QBrush(QColor("white")))
            p.setPen(Qt.NoPen)
            p.drawEllipse(20, 3, 16, 16)
        else:
            p.setBrush(QBrush(QColor("white")))
            p.setPen(Qt.NoPen)
            p.drawEllipse(4, 3, 16, 16)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle()
            self.clicked.emit()

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

class DDS2PNG(QWidget):
    def __init__(self):
        super().__init__()
        self.languages = {
            "English": {
                "title": "DDS/PNG Batch Converter",
                "mode_label": "Mode:",
                "dds2png": "DDS → PNG",
                "png2dds": "PNG → DDS",
                "keep_structure": "Keep original folder structure",
                "select_folder": "Select Folder",
                "select_output": "Select Output Folder",
                "start": "Start Conversion",
                "found": "Found {count} {ext} files",
                "select_folder_tip_dds": "Please select a folder containing DDS files",
                "select_folder_tip_png": "Please select a folder containing PNG files",
                "output_path": "Output Path: {path}",
                "default_output": "No output path selected, default set to: {path}",
                "done": "All conversions completed!",
                "task_done": "All conversions completed! Start a new task?",
                "yes": "Yes",
                "no": "No",
                "lang_tip": "EN",
                "product_name": "DDS TO PNG",
                "by": "by ",
                "project": "Project Address"
            },
            "中文": {
                "title": "DDS/PNG 批量互转工具",
                "mode_label": "转换模式：",
                "dds2png": "DDS → PNG",
                "png2dds": "PNG → DDS",
                "keep_structure": "保留原有文件夹结构",
                "select_folder": "选择文件夹",
                "select_output": "选择导出路径",
                "start": "开始转换",
                "found": "已找到 {count} 个{ext}文件",
                "select_folder_tip_dds": "请选择包含DDS文件的文件夹",
                "select_folder_tip_png": "请选择包含PNG文件的文件夹",
                "output_path": "导出路径: {path}",
                "default_output": "未选择导出路径，已默认设置为: {path}",
                "done": "全部转换完成！",
                "task_done": "全部转换完成！是否开始新任务？",
                "yes": "是",
                "no": "否",
                "lang_tip": "中",
                "product_name": "DDS TO PNG",
                "by": "by ",
                "project": "项目地址"
            }
        }
        self.current_lang = "English"
        self.init_ui()
        self.dds_files = []
        self.output_dir = ""
        self.mode = "dds2png"
        self.keep_structure = False
        self.input_root = ""

    def tr(self, key, **kwargs):
        return self.languages[self.current_lang][key].format(**kwargs)

    def init_ui(self):
        self.setWindowTitle(self.tr("title"))
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)

        lang_frame = QFrame()
        lang_frame.setFixedHeight(30)
        lang_layout = QHBoxLayout()
        lang_layout.setContentsMargins(0, 0, 0, 0)

        self.product_label = QLabel(self.tr("product_name"))
        font = self.product_label.font()
        font.setPointSize(13)
        font.setBold(True)
        self.product_label.setFont(font)
        lang_layout.addWidget(self.product_label)
        lang_layout.addStretch()

        self.lang_switch = SwitchButton()
        self.lang_switch.setChecked(False)
        self.lang_switch.setToolTip("Switch Language / 切换语言")
        self.lang_switch.stateChanged.connect(self.toggle_language)
        lang_layout.addWidget(self.lang_switch)

        self.lang_tip = QLabel(self.languages[self.current_lang]["lang_tip"])
        self.lang_tip.setFixedWidth(20)
        self.lang_tip.setAlignment(Qt.AlignCenter)
        lang_layout.addWidget(self.lang_tip)

        lang_frame.setLayout(lang_layout)
        main_layout.addWidget(lang_frame)

        mode_layout = QHBoxLayout()
        self.label_mode = QLabel(self.tr("mode_label"))
        self.radio_dds2png = QRadioButton(self.tr("dds2png"))
        self.radio_dds2png.setChecked(True)
        self.radio_png2dds = QRadioButton(self.tr("png2dds"))
        mode_layout.addWidget(self.label_mode)
        mode_layout.addWidget(self.radio_dds2png)
        mode_layout.addWidget(self.radio_png2dds)
        mode_layout.addStretch()
        main_layout.addLayout(mode_layout)

        self.radio_dds2png.toggled.connect(self.update_mode)
        self.radio_png2dds.toggled.connect(self.update_mode)

        self.check_keep_structure = QCheckBox(self.tr("keep_structure"))
        self.check_keep_structure.stateChanged.connect(self.update_structure_mode)
        main_layout.addWidget(self.check_keep_structure)

        self.label = QLabel(self.tr('select_folder_tip_dds'))
        main_layout.addWidget(self.label)

        self.btn_select_folder = QPushButton(self.tr('select_folder'))
        self.btn_select_folder.clicked.connect(self.select_folder)
        main_layout.addWidget(self.btn_select_folder)

        self.btn_select_output = QPushButton(self.tr('select_output'))
        self.btn_select_output.clicked.connect(self.select_output)
        main_layout.addWidget(self.btn_select_output)

        self.btn_convert = QPushButton(self.tr('start'))
        self.btn_convert.clicked.connect(self.convert_all)
        main_layout.addWidget(self.btn_convert)

        self.progress = QProgressBar()
        main_layout.addWidget(self.progress)

        bottom_frame = QFrame()
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.addStretch()

        self.by_label = QLabel(self.tr("by"))
        bottom_layout.addWidget(self.by_label)

        author_label = ClickableLabel('<a style="color:#1976d2;text-decoration:none;" href="#">CzXieDdan</a>')
        author_label.setOpenExternalLinks(False)
        author_label.clicked.connect(lambda: webbrowser.open("https://czxieddan.top/"))
        bottom_layout.addWidget(author_label)

        self.project_label = ClickableLabel(f'<a style="color:#388e3c;text-decoration:none;" href="#"> {self.tr("project")}</a>')  # 改为self.project_label
        self.project_label.setOpenExternalLinks(False)
        self.project_label.clicked.connect(lambda: webbrowser.open("https://github.com/czxieddan/DDS2PNG"))
        bottom_layout.addWidget(self.project_label)

        bottom_frame.setLayout(bottom_layout)
        main_layout.addWidget(bottom_frame)

        self.setLayout(main_layout)

    def toggle_language(self):
        if self.lang_switch.isChecked():
            self.current_lang = "中文"
        else:
            self.current_lang = "English"
        self.lang_tip.setText(self.languages[self.current_lang]["lang_tip"])
        self.setWindowTitle(self.tr("title"))
        self.label_mode.setText(self.tr("mode_label"))
        self.radio_dds2png.setText(self.tr("dds2png"))
        self.radio_png2dds.setText(self.tr("png2dds"))
        self.check_keep_structure.setText(self.tr("keep_structure"))
        self.btn_select_folder.setText(self.tr("select_folder"))
        self.btn_select_output.setText(self.tr("select_output"))
        self.btn_convert.setText(self.tr("start"))
        if self.mode == "dds2png":
            self.product_label.setText("DDS TO PNG")
        else:
            self.product_label.setText("PNG TO DDS")
        self.by_label.setText(self.tr("by"))
        self.project_label.setText(f' {self.tr("project")}')
        if self.dds_files:
            ext = '.dds' if self.mode == "dds2png" else '.png'
            self.label.setText(self.tr('found', count=len(self.dds_files), ext=ext.upper()))
        elif self.output_dir:
            self.label.setText(self.tr('output_path', path=self.output_dir))
        else:
            if self.mode == "dds2png":
                self.label.setText(self.tr('select_folder_tip_dds'))
            else:
                self.label.setText(self.tr('select_folder_tip_png'))

    def update_mode(self):
        prev_input_root = self.input_root
        prev_output_dir = self.output_dir

        if self.radio_dds2png.isChecked():
            self.mode = "dds2png"
            self.product_label.setText("DDS TO PNG")
            self.label.setText(self.tr('select_folder_tip_dds'))
        else:
            self.mode = "png2dds"
            self.product_label.setText("PNG TO DDS")
            self.label.setText(self.tr('select_folder_tip_png'))

        if prev_input_root:
            self.input_root = prev_input_root
            files = []
            ext = '.dds' if self.mode == "dds2png" else '.png'
            for root, _, fs in os.walk(self.input_root):
                for f in fs:
                    if f.lower().endswith(ext):
                        files.append(os.path.join(root, f))
            self.dds_files = files
            self.label.setText(self.tr('found', count=len(self.dds_files), ext=ext.upper()))

        if prev_output_dir:
            self.output_dir = prev_output_dir
            self.label.setText(self.tr('output_path', path=self.output_dir))

        self.progress.setValue(0)

    def update_structure_mode(self):
        self.keep_structure = self.check_keep_structure.isChecked()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.tr('select_folder'))
        if folder:
            self.input_root = folder
            files = []
            if self.mode == "dds2png":
                ext = '.dds'
            else:
                ext = '.png'
            for root, _, fs in os.walk(folder):
                for f in fs:
                    if f.lower().endswith(ext):
                        files.append(os.path.join(root, f))
            self.dds_files = files
            self.label.setText(self.tr('found', count=len(self.dds_files), ext=ext.upper()))

    def select_output(self):
        self.output_dir = QFileDialog.getExistingDirectory(self, self.tr('select_output'))
        if self.output_dir:
            self.label.setText(self.tr('output_path', path=self.output_dir))

    def get_unique_path(self, base_dir, filename):
        path = os.path.join(base_dir, filename)
        while os.path.exists(path):
            base_dir = os.path.join(base_dir, "duplicate")
            if not os.path.exists(base_dir):
                os.makedirs(base_dir)
            path = os.path.join(base_dir, filename)
        return path

    def get_target_path(self, src_path, ext):
        filename = os.path.splitext(os.path.basename(src_path))[0] + ext
        if self.keep_structure and self.input_root:
            rel_path = os.path.relpath(os.path.dirname(src_path), self.input_root)
            target_dir = os.path.join(self.output_dir, rel_path)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            target_path = os.path.join(target_dir, filename)
            while os.path.exists(target_path):
                target_dir = os.path.join(target_dir, "duplicate")
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                target_path = os.path.join(target_dir, filename)
            return target_path
        else:
            return self.get_unique_path(self.output_dir, filename)

    def convert_dds_to_png(self, dds_path):
        try:
            img = Image.open(dds_path)
            png_path = self.get_target_path(dds_path, '.png')
            img.save(png_path)
        except Exception as e:
            print(f"转换失败: {dds_path}，原因: {e}")

    def convert_png_to_dds(self, png_path):
        try:
            img = Image.open(png_path)
            dds_path = self.get_target_path(png_path, '.dds')
            img.save(dds_path)
        except Exception as e:
            print(f"转换失败: {png_path}，原因: {e}")

    def convert_all(self):
        if not self.dds_files:
            self.label.setText(self.tr('select_folder_tip_dds') if self.mode == "dds2png" else self.tr('select_folder_tip_png'))
            return
        if not self.output_dir:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.output_dir = os.path.join(base_dir, "output")
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            self.label.setText(self.tr('default_output', path=self.output_dir))
        self.progress.setMaximum(len(self.dds_files))
        if self.mode == "dds2png":
            func = self.convert_dds_to_png
        else:
            func = self.convert_png_to_dds
        with ThreadPoolExecutor(max_workers=4) as executor:
            for i, _ in enumerate(executor.map(func, self.dds_files)):
                self.progress.setValue(i + 1)
        self.label.setText(self.tr('done'))
        reply = QMessageBox.question(
            self,
            self.tr('done'),
            self.tr('task_done'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.dds_files = []
            self.output_dir = ""
            self.progress.setValue(0)
            self.label.setText(self.tr('select_folder_tip_dds') if self.mode == "dds2png" else self.tr('select_folder_tip_png'))
            self.select_folder()
            self.select_output()

if __name__ == '__main__':
    app = QApplication([])
    win = DDS2PNG()
    win.show()
    app.exec_()