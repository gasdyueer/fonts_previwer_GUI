#!/usr/bin/env python3
"""
PySide6多字体预览GUI应用

功能描述：
- 列举并显示系统全部字体（包括样式变体）
- 支持字体搜索和过滤
- 实时字体预览效果
- 单/多预览区域切换
- 动态调整字体属性（字号、颜色、粗细等）
- 显示字体详细信息
- 处理大量字体时的性能优化
"""

import sys
import time
from typing import Dict, List, Optional, Tuple

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QTextEdit, QLineEdit, QLabel,
    QSlider, QColorDialog, QComboBox, QCheckBox, QGroupBox,
    QScrollArea, QSplitter, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize
from PySide6.QtGui import (
    QFont, QFontDatabase, QFontMetrics, QColor, QPainter,
    QPixmap, QPalette, QIcon
)
import platform
import os


class FontLoader(QThread):
    """异步字体加载线程，提高应用响应速度"""

    progress = Signal(int)
    font_loaded = Signal(str, QFont)
    finished = Signal(list)

    def __init__(self):
        super().__init__()
        self.fonts: List[Tuple[str, QFont]] = []

    def run(self):
        """加载系统字体"""
        font_db = QFontDatabase()
        families = font_db.families()

        total_operations = len(families)
        completed = 0

        for family in families:
            # 加载字体系列的所有样式
            styles = font_db.styles(family)

            # 优化：过滤掉无用的字体变体，减少内存使用
            useful_styles = self._filter_useable_styles(styles, font_db, family)

            for style in useful_styles:
                # 创建包含样式信息的字体
                font = QFont(family, 12, QFont.Weight.Normal)
                font.setStyleName(style)

                self.fonts.append((f"{family} - {style}", font))
                self.font_loaded.emit(f"{family} - {style}", font)

            completed += 1
            # 进度更新
            progress = int((completed / total_operations) * 100)
            self.progress.emit(progress)

            # 给UI线程时间响应，避免界面冻结
            if completed % 20 == 0:
                QThread.msleep(10)

        self.finished.emit(self.fonts)

    def _filter_useable_styles(self, styles: List[str], font_db, family) -> List[str]:
        """过滤有用的字体样式，减少重复"""
        useful_styles = []

        regular_found = False
        bold_found = False
        italic_found = False
        bold_italic_found = False

        for style in styles:
            lower_style = style.lower()

            if 'regular' in lower_style or (not regular_found and lower_style in ['normal', 'book']):
                useful_styles.append(style)
                regular_found = True
            elif 'bold' in lower_style and 'italic' in lower_style:
                if not bold_italic_found:
                    useful_styles.append(style)
                    bold_italic_found = True
            elif 'bold' in lower_style:
                if not bold_found:
                    useful_styles.append(style)
                    bold_found = True
            elif 'italic' in lower_style:
                if not italic_found:
                    useful_styles.append(style)
                    italic_found = True
            elif len(useful_styles) < 4:  # 最多添加4个样式变体
                useful_styles.append(style)

        return useful_styles[:4]  # 限制每个字体的样式数量


class FontPreviewWidget(QFrame):
    """字体预览组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setMinimumHeight(60)
        self.font_family = ""
        self.font_style = ""
        self.text = "字体预览样本 ABC abc 123"
        self.font_size = 24
        self.font_color = QColor(0, 0, 0)
        self.font_weight = QFont.Weight.Normal
        self.cache_pixmap = None

    def set_font_info(self, family: str, style: str, text: str):
        """设置字体信息和预览文本"""
        self.font_family = family
        self.font_style = style
        self.text = text
        self.cache_pixmap = None
        self.update()

    def set_font_properties(self, size: int, color: QColor, weight: int):
        """设置字体属性"""
        self.font_size = size
        self.font_color = color
        self.font_weight = weight
        self.cache_pixmap = None
        self.update()

    def paintEvent(self, event):
        """绘制字体预览"""
        if self.cache_pixmap is None:
            self._update_cache()

        painter = QPainter(self)
        if self.cache_pixmap:
            painter.drawPixmap(0, 0, self.cache_pixmap)

    def _update_cache(self):
        """更新预览缓存"""
        try:
            font = QFont(self.font_family, self.font_size, self.font_weight)
            font.setStyleName(self.font_style)

            rect = self.rect()
            pixmap = QPixmap(rect.size())
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.setFont(font)
            painter.setPen(self.font_color)

            # 适应文本到组件大小
            metrics = QFontMetrics(font)
            width = rect.width() - 20

            # 分行处理文本
            lines = []
            if metrics.horizontalAdvance(self.text) > width:
                # 简单文本分行逻辑
                words = self.text.replace('\n', ' \n ').split()
                current_line = ""
                for word in words:
                    if word == '\n':
                        if current_line.strip():
                            lines.append(current_line.strip())
                        lines.append("")  # 空行处理换行符
                        current_line = ""
                        continue

                    test_line = current_line + (" " if current_line else "") + word
                    if metrics.horizontalAdvance(test_line) > width:
                        if current_line:
                            lines.append(current_line)
                        if metrics.horizontalAdvance(word) > width:
                            # 长单词截断处理
                            lines.append(word)
                            current_line = ""
                        else:
                            current_line = word
                    else:
                        current_line = test_line

                if current_line.strip():
                    lines.append(current_line.strip())
            else:
                # 简单文本直接处理换行
                lines = self.text.split('\n')

            # 计算实际文本高度
            total_height = 0
            line_heights = []
            for line in lines:
                line_height = metrics.lineSpacing()
                line_heights.append(line_height)
                total_height += line_height

            # 确定绘制起始Y坐标，确保所有文本可见
            if total_height > rect.height() - 20:
                # 如果文本过高，从组件顶部边缘开始绘制
                y = metrics.ascent()
                available_height = rect.height() - 10
            else:
                # 如果文本不高，从组件顶部一点位置开始绘制
                y = 10 + metrics.ascent()

            # 绘制每一行文本和字体名称
            for i, line in enumerate(lines):
                if y - metrics.ascent() + line_heights[i] > rect.height():
                    break  # 防止绘制超出组件底部

                # 绘制预览文本
                painter.drawText(10, y, line)

                # 在右侧绘制字体名称
                font_name = f"{self.font_family} - {self.font_style}"
                # 使用较小的字体显示字体名称
                small_font = QFont(self.font_family, max(self.font_size - 4, 8), self.font_weight)
                painter.setFont(small_font)
                small_metrics = QFontMetrics(small_font)

                # 计算字体名称的右对齐位置
                name_width = small_metrics.horizontalAdvance(font_name)
                name_x = rect.width() - name_width - 10  # 右侧10px边距

                # 确保字体名称不与预览文本重叠的最小距离
                preview_text_end = 10 + metrics.horizontalAdvance(line)
                if name_x > preview_text_end + 20:  # 至少20px间距
                    painter.drawText(name_x, y - (metrics.ascent() - small_metrics.ascent()), font_name)
                else:
                    # 如果空间不够，使用省略号形式
                    available_width = max(0, name_x - preview_text_end - 20)
                    if available_width > 30:  # 最小30px显示部分名称
                        # 使用省略号缩短字体名称
                        shortened_name = font_name
                        while small_metrics.horizontalAdvance(shortened_name + "...") > available_width and len(shortened_name) > 3:
                            shortened_name = shortened_name[:-1]
                        if len(shortened_name) < len(font_name):
                            painter.drawText(preview_text_end + 20, y - (metrics.ascent() - small_metrics.ascent()), shortened_name + "...")
                        else:
                            painter.drawText(preview_text_end + 20, y - (metrics.ascent() - small_metrics.ascent()), font_name)

                # 恢复原始字体
                painter.setFont(font)
                y += line_heights[i]

            painter.end()
            self.cache_pixmap = pixmap

        except Exception as e:
            print(f"字体预览错误: {e}")
            self.cache_pixmap = None


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("多字体预览器 - PySide6")
        self.setMinimumSize(1200, 800)

        # 初始化数据
        self.fonts: List[Tuple[str, QFont]] = []
        self.filtered_fonts: List[Tuple[str, QFont]] = []
        self.selected_fonts: List[Tuple[str, QFont]] = []  # 选中的字体
        self.current_font_index = 0
        self.preview_mode = "single"  # "single", "multi", 或 "selected"

        # 性能优化：更新延迟和缓存
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._perform_preview_update)
        self.preview_cache = {}  # 预览组件缓存

        # 初始化UI
        self._setup_ui()
        self._connect_signals()

        # 启动字体加载
        self._start_font_loading()

    def _setup_ui(self):
        """设置UI界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 左侧控制面板
        self._create_control_panel()
        main_layout.addWidget(self.control_panel, 0)

        # 中间预览区域
        self._create_preview_area()
        main_layout.addWidget(self.preview_area, 1)

    def _create_control_panel(self):
        """创建控制面板"""
        self.control_panel = QWidget()
        self.control_panel.setFixedWidth(300)
        layout = QVBoxLayout(self.control_panel)

        # 搜索框
        search_group = QGroupBox("字体搜索")
        search_layout = QVBoxLayout(search_group)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索字体...")
        search_layout.addWidget(self.search_input)
        layout.addWidget(search_group)

        # 字体列表
        font_list_group = QGroupBox("字体列表")
        font_list_layout = QVBoxLayout(font_list_group)
        self.font_list = QListWidget()
        self.font_list.setMinimumHeight(200)
        self.font_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)  # 启用多选模式
        font_list_layout.addWidget(self.font_list)
        layout.addWidget(font_list_group)

        # 属性控制
        self._create_properties_panel(layout)

        # 预览模式
        preview_group = QGroupBox("预览设置")
        preview_layout = QVBoxLayout(preview_group)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["单预览", "多预览", "选中字体"])
        preview_layout.addWidget(QLabel("预览模式:"))
        preview_layout.addWidget(self.mode_combo)

        # 清除选中按钮
        self.clear_selection_button = QPushButton("清除所有选择")
        self.clear_selection_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        preview_layout.addWidget(self.clear_selection_button)

        layout.addWidget(preview_group)

        # 字体信息
        self._create_info_panel(layout)

        # 占用剩余空间
        layout.addStretch()

    def _create_properties_panel(self, parent_layout):
        """创建属性控制面板"""
        properties_group = QGroupBox("字体属性")
        properties_layout = QVBoxLayout(properties_group)

        # 字号
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("字号:"))
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(8, 72)
        self.size_slider.setValue(24)
        self.size_label = QLabel(f"{self.size_slider.value()}px")
        self.size_label.setFixedWidth(50)
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(self.size_label)
        properties_layout.addLayout(size_layout)

        # 颜色选择
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("颜色:"))
        self.color_button = QPushButton()
        self.color_button.setFixedSize(40, 20)
        self.current_color = QColor(0, 0, 0)
        self._update_color_button()
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()
        properties_layout.addLayout(color_layout)

        # 粗细
        weight_layout = QHBoxLayout()
        weight_layout.addWidget(QLabel("粗细:"))
        self.weight_slider = QSlider(Qt.Orientation.Horizontal)
        self.weight_slider.setRange(0, 99)
        self.weight_slider.setValue(50)  # Normal
        self.weight_label = QLabel("Normal")
        self.weight_label.setFixedWidth(60)
        weight_layout.addWidget(self.weight_slider)
        weight_layout.addWidget(self.weight_label)
        properties_layout.addLayout(weight_layout)

        parent_layout.addWidget(properties_group)

    def _create_info_panel(self, parent_layout):
        """创建字体信息面板"""
        self.info_group = QGroupBox("字体信息")
        info_layout = QVBoxLayout(self.info_group)

        self.font_family_label = QLabel("字体: -")
        self.font_style_label = QLabel("样式: -")
        self.font_file_label = QLabel("文件: -")

        info_layout.addWidget(self.font_family_label)
        info_layout.addWidget(self.font_style_label)
        info_layout.addWidget(self.font_file_label)

        parent_layout.addWidget(self.info_group)

    def _create_preview_area(self):
        """创建预览区域"""
        self.preview_area = QWidget()
        layout = QVBoxLayout(self.preview_area)

        # 预览文本输入框 - 放在顶部
        preview_text_group = QGroupBox("预览文本")
        preview_text_layout = QVBoxLayout(preview_text_group)
        self.preview_text = QTextEdit()
        self.preview_text.setText("字体预览样例 Typography"),
        self.preview_text.setMaximumHeight(100)
        preview_text_layout.addWidget(self.preview_text)
        layout.addWidget(preview_text_group)

        # 滚动预览区域
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)

        self.preview_container = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_container)

        self.preview_scroll.setWidget(self.preview_container)
        layout.addWidget(self.preview_scroll, 1)  # 占用剩余空间

    def _connect_signals(self):
        """连接信号"""
        self.search_input.textChanged.connect(self._filter_fonts)
        self.font_list.itemSelectionChanged.connect(self._on_font_selection_changed)
        self.size_slider.valueChanged.connect(self._update_font_size)
        self.weight_slider.valueChanged.connect(self._update_font_weight)
        self.color_button.clicked.connect(self._select_color)
        self.mode_combo.currentTextChanged.connect(self._change_preview_mode)
        self.preview_text.textChanged.connect(self._update_preview_text)
        self.clear_selection_button.clicked.connect(self._clear_all_selections)

    def _start_font_loading(self):
        """启动字体加载"""
        self.font_loader = FontLoader()
        self.font_loader.progress.connect(self._on_load_progress)
        self.font_loader.finished.connect(self._on_load_finished)
        self.font_loader.start()

    def _on_load_progress(self, progress):
        """字体加载进度"""
        self.statusBar().showMessage(f"加载字体中... {progress}%")

    def _on_load_finished(self, fonts):
        """字体加载完成"""
        self.fonts = fonts
        self.filtered_fonts = fonts.copy()

        self.font_list.clear()
        for name, font in self.filtered_fonts:
            item = QListWidgetItem(name)
            self.font_list.addItem(item)

        self.statusBar().showMessage(f"已加载 {len(self.fonts)} 个字体")

        # 选中第一个字体
        if self.font_list.count() > 0:
            self.font_list.setCurrentRow(0)

    def _filter_fonts(self, text):
        """过滤字体列表"""
        text = text.lower()
        self.filtered_fonts = [
            (name, font) for name, font in self.fonts
            if text in name.lower()
        ]

        self.font_list.clear()
        for name, font in self.filtered_fonts:
            item = QListWidgetItem(name)
            self.font_list.addItem(item)

        if self.font_list.count() > 0:
            self.font_list.setCurrentRow(0)

    def _on_font_selection_changed(self):
        """字体选择改变"""
        # 如果是选中字体模式，实时更新选中的字体和预览
        if self.preview_mode == "selected":
            self._update_selected_fonts()

        # 对于单预览模式，处理单选
        elif self.preview_mode == "single":
            if not self.font_list.currentItem():
                return

            index = self.font_list.currentRow()
            if 0 <= index < len(self.filtered_fonts):
                name, font = self.filtered_fonts[index]
                self._update_font_preview(name, font)

        # 对于多预览模式，更新多字体列表
        elif self.preview_mode == "multi":
            self._debounced_update_previews()

    def _update_font_preview(self, name: str, font: QFont):
        """更新字体预览"""
        text = self.preview_text.toPlainText()

        if self.preview_mode == "single":
            # 单预览模式
            try:
                family, style = name.split(" - ", 1)
            except ValueError:
                family = name
                style = ""
            self._update_single_preview(family, style, text, font)

            # 更新信息面板
            self.font_family_label.setText(f"字体: {family}")
            self.font_style_label.setText(f"样式: {style}")

        elif self.preview_mode == "multi":
            # 多预览模式
            try:
                family, style = name.split(" - ", 1)
            except ValueError:
                family = name
                style = ""
            self._update_multi_preview(family, style, text, font)

        elif self.preview_mode == "selected":
            # 选中字体模式 - 直接更新所有选中字体的预览
            self._update_selected_fonts_preview(text)

    def _update_selected_fonts_preview(self, text: str):
        """更新所有选中字体的预览"""
        # 清除现有预览
        for i in reversed(range(self.preview_layout.count())):
            widget = self.preview_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # 创建选中字体的预览
        for name, font in self.selected_fonts[:20]:  # 限制显示前20个选中字体
            try:
                family, style = name.split(" - ", 1)
            except ValueError:
                family = name
                style = ""

            preview_widget = FontPreviewWidget()
            preview_widget.set_font_info(family, style, text)
            preview_widget.set_font_properties(
                self.size_slider.value(),
                self.current_color,
                self._slider_value_to_weight(self.weight_slider.value())
            )

            self.preview_layout.addWidget(preview_widget)

        # 更新信息面板显示选中字体的数量
        self.font_family_label.setText(f"选中字体: {len(self.selected_fonts)} 个")
        if self.selected_fonts:
            try:
                family, style = self.selected_fonts[0][0].split(" - ", 1)
            except ValueError:
                family = self.selected_fonts[0][0]
                style = ""
            self.font_style_label.setText(f"当前: {family} - {style}")
        else:
            self.font_style_label.setText("样式: 未选择")

    def _update_single_preview(self, family: str, style: str, text: str, font: QFont):
        """更新单预览"""
        # 清除现有预览
        for i in reversed(range(self.preview_layout.count())):
            widget = self.preview_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # 创建新预览组件
        preview_widget = FontPreviewWidget()
        preview_widget.set_font_info(family, style, text)
        preview_widget.set_font_properties(
            self.size_slider.value(),
            self.current_color,
            self._slider_value_to_weight(self.weight_slider.value())
        )

        self.preview_layout.addWidget(preview_widget)

    def _update_multi_preview(self, family: str, style: str, text: str, font: QFont):
        """更新多预览"""
        # 清除现有预览
        for i in reversed(range(self.preview_layout.count())):
            widget = self.preview_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # 创建多个预览组件（显示相邻字体）
        current_index = self._find_font_index_in_original(family, style)
        start_index = max(0, current_index - 5)
        end_index = min(len(self.fonts), current_index + 6)

        for i in range(start_index, end_index):
            if i >= len(self.fonts):
                break

            fname, ffont = self.fonts[i]
            try:
                f_family, f_style = fname.split(" - ", 1)
            except ValueError:
                f_family = fname
                f_style = ""

            preview_widget = FontPreviewWidget()
            preview_widget.set_font_info(f_family, f_style, text)
            preview_widget.set_font_properties(
                self.size_slider.value(),
                self.current_color,
                self._slider_value_to_weight(self.weight_slider.value())
            )

            # 当前字体高亮
            if i == current_index:
                palette = preview_widget.palette()
                palette.setColor(QPalette.ColorRole.Window, QColor(173, 216, 230))  # 浅蓝色
                preview_widget.setPalette(palette)

            self.preview_layout.addWidget(preview_widget)

    def _find_font_index_in_original(self, family: str, style: str) -> int:
        """在原始字体列表中找到索引"""
        search_name = f"{family} - {style}"
        for i, (name, _) in enumerate(self.fonts):
            if name == search_name:
                return i
        return 0

    def _update_font_size(self, value):
        """更新字体大小"""
        self.size_label.setText(f"{value}px")
        self._debounced_update_previews()

    def _update_font_weight(self, value):
        """更新字体粗细"""
        weight_names = {
            range(0, 12): "Thin", range(12, 25): "Extra Light", range(25, 38): "Light",
            range(38, 50): "Normal", range(50, 62): "Medium", range(62, 75): "Semi Bold",
            range(75, 88): "Bold", range(88, 100): "Extra Bold"
        }

        for weight_range, name in weight_names.items():
            if value in weight_range:
                self.weight_label.setText(name)
                break
        else:
            self.weight_label.setText("Normal")

        self._debounced_update_previews()

    def _slider_value_to_weight(self, value: int) -> int:
        """将滑块值转换为字体粗细"""
        weights = [QFont.Weight.Thin, QFont.Weight.ExtraLight, QFont.Weight.Light, QFont.Weight.Normal,
                  QFont.Weight.Medium, QFont.Weight.DemiBold, QFont.Weight.Bold, QFont.Weight.ExtraBold, QFont.Weight.Black]
        index = int(value / 11.11)  # 将0-99映射到0-7
        return weights[min(index, len(weights)-1)]

    def _select_color(self):
        """选择字体颜色"""
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self._update_color_button()
            self._debounced_update_previews()

    def _update_color_button(self):
        """更新颜色按钮显示"""
        pic = QPixmap(36, 16)
        pic.fill(self.current_color)
        self.color_button.setIcon(QIcon(pic))

    def _change_preview_mode(self, mode):
        """改变预览模式"""
        if mode == "单预览":
            self.preview_mode = "single"
        elif mode == "多预览":
            self.preview_mode = "multi"
        else:  # "选中字体"
            self.preview_mode = "selected"
            self._update_selected_fonts()
        self._debounced_update_previews()

    def _update_preview_text(self):
        """更新预览文本"""
        self._debounced_update_previews()

    def _perform_preview_update(self):
        """执行预览更新（延迟更新机制）"""
        self._refresh_previews()

    def _refresh_previews(self):
        """刷新所有预览"""
        if hasattr(self, 'filtered_fonts') and self.font_list.currentItem():
            index = self.font_list.currentRow()
            if 0 <= index < len(self.filtered_fonts):
                name, font = self.filtered_fonts[index]
                self._update_font_preview(name, font)

    def _update_selected_fonts(self):
        """更新选中的字体列表"""
        self.selected_fonts = []
        for index in range(len(self.filtered_fonts)):
            item = self.font_list.item(index)
            if item and item.isSelected():
                if index < len(self.filtered_fonts):
                    self.selected_fonts.append(self.filtered_fonts[index])
        self._debounced_update_previews()

    def _update_multi_preview_selected_name(self, name, text, font):
        """更新多预览模式（以指定名称为中心）"""
        try:
            family, style = name.split(" - ", 1)
        except ValueError:
            family = name
            style = ""

        self._update_multi_preview(family, style, text, font)

    def _clear_all_selections(self):
        """清除所有选中的字体"""
        # 清除字体列表中的选中状态
        for index in range(self.font_list.count()):
            item = self.font_list.item(index)
            if item:
                item.setSelected(False)

        # 清除内部选中的字体列表
        self.selected_fonts.clear()

        # 更新预览，只有在选中字体模式下才清空预览
        if self.preview_mode == "selected":
            # 清除现有预览
            for i in reversed(range(self.preview_layout.count())):
                widget = self.preview_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

            # 更新信息面板
            self.font_family_label.setText("字体: 未选择")
            self.font_style_label.setText("样式: 未选择")

    def _debounced_update_previews(self, delay_ms=150):
        """延迟更新预览，避免频繁刷新"""
        self.update_timer.start(delay_ms)


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("多字体预览器")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("字体工具")

    # 设置样式
    app.setStyle("Fusion")  # 使用现代样式

    # 设置应用程序样式表
    app.setStyleSheet("""
        /* 主窗口样式 */
        QMainWindow {
            background-color: #f8f9fa;
        }

        /* 组盒样式 */
        QGroupBox {
            font-weight: bold;
            border: 2px solid #3498db;
            border-radius: 8px;
            margin-top: 1ex;
            background-color: #ffffff;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
            color: #2c3e50;
            font-size: 14px;
        }

        /* 按钮样式 */
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #2980b9;
        }

        QPushButton:pressed {
            background-color: #21618c;
        }

        /* 滑块样式 */
        QSlider::groove:horizontal {
            height: 8px;
            background: #ddd;
            border-radius: 4px;
        }

        QSlider::handle:horizontal {
            background: #3498db;
            border: none;
            width: 18px;
            margin: -5px 0;
            border-radius: 9px;
        }

        QSlider::handle:horizontal:hover {
            background: #2980b9;
        }

        /* 文本编辑框样式 */
        QTextEdit, QLineEdit {
            border: 2px solid #bdc3c7;
            border-radius: 4px;
            padding: 8px;
            background-color: white;
        }

        QTextEdit:focus, QLineEdit:focus {
            border-color: #3498db;
        }

        /* 列表样式 */
        QListWidget {
            border: 2px solid #bdc3c7;
            border-radius: 4px;
            background-color: white;
            selection-background-color: #3498db;
            selection-color: white;
        }

        QListWidget::item:hover {
            background-color: #ecf0f1;
        }

        /* 滚动条样式 */
        QScrollBar:vertical {
            background: #ffffff;
            width: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:vertical {
            background: #bdc3c7;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background: #95a5a6;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }

        /* 标签样式 */
        QLabel {
            color: #2c3e50;
        }
    """)

    # 创建主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()