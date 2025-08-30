[🇨🇳 中文](README.md) | [🇺🇸 English](README_en.md)

---

# Multi-Font Previewer - PySide6 GUI Application

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.4+-green.svg)](https://pypi.org/project/PySide6/)

A powerful multi-font preview GUI application built with PySide6, supporting system font browsing, search, real-time preview, and multiple preview mode switching.

## ✨ Features

### 🎯 Core Features
- **System Font Listing**: Automatically detect and load all system fonts and style variants
- **Font Search & Filtering**: Support real-time search and filtering by font name
- **Multiple Preview Modes**: Provide single preview, multi-preview, and selected fonts preview modes
- **Real-time Effect Adjustments**: Dynamically adjust font size, color, and weight with live preview
- **Font Information Display**: Show font family, style, file location and other detailed information
- **Performance Optimization**: Asynchronous font loading, preview caching, multi-threading for smooth experience

### 🔧 Interface Features
- **Modern UI Design**: Use Fusion style with beautiful color scheme and user-friendly experience
- **Responsive Layout**: Adaptive window sizing, supports large display
- **User-friendly Interaction**: Support font multi-selection, quick operations, rich visual feedback
- **Real-time Updates**: Parameter adjustments reflect on preview immediately, no reboot needed

## 📋 System Requirements

- **Python**: 3.11 or higher version
- **Operating System**: Windows 10+, macOS 10.14+, Linux
- **Dependencies**: PySide6
- **Storage Space**: At least 50MB available space

## 🚀 Quick Start

### 1. Clone the Project
```bash
git clone https://github.com/gasdyueer/fonts_previwer_GUI.git
cd fonts_previwer_GUI
```

### 2. Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -e .
```

### 4. Run the Application
```bash
python main.py
```

## 📖 User Guide

### 🖥️ Interface Layout
The application uses three-column layout design:

1. **Left Control Panel**: Font search, font list, property control, preview settings
2. **Middle Preview Area**: Real-time font effect preview
3. **Right Information Panel**: Font detailed information display

### 📝 Operation Steps

#### Font Preview
1. After launching, the system will automatically load all fonts (first run may be slower)
2. Select fonts to preview from the font list on the left
3. Support single or multi-selection (hold Ctrl for multi-selection)

#### Three Preview Modes

**Single Preview Mode (Default)**
- Only show the currently selected font's preview effect
- Suitable for focused viewing of individual font details

**Multi-Preview Mode**
- Show selected font and its adjacent fonts' preview
- Convenient for font comparison and selection

**Selected Fonts Mode**
- Show all selected fonts' preview effects
- Maximum display of first 20 selected fonts
- Suitable for batch preview of multiple selected fonts

#### Property Adjustment
- **Size Adjustment**: Use slider to adjust font size (8-72px)
- **Color Selection**: Click color button to open color palette
- **Weight Adjustment**: Use slider to adjust font weight (Thin to Black)

#### Preview Text
- Input custom text in the preview text box at the top
- Support Chinese, English, numbers and other characters
- Real-time reflection in all preview effects

## 🔧 Development Notes

### Project Structure
```
fonts_previwer_GUI/
├── main.py          # Main application file
├── pyproject.toml   # Project configuration and dependencies
├── .python-version  # Python version requirements
├── .gitignore       # Git ignore file
└── README.md        # Project documentation
```

### Core Classes Description

#### 1. FontLoader (Asynchronous Font Loader)
```python
class FontLoader(QThread)
```
- Asynchronous thread loading system fonts
- Real-time update loading progress
- Filter duplicate font styles, optimize memory usage

#### 2. FontPreviewWidget (Font Preview Widget)
```python
class FontPreviewWidget(QFrame)
```
- Custom widget implementing font preview
- Support text auto-wrap
- Preview effect caching for performance optimization

#### 3. MainWindow (Main Window)
```python
class MainWindow(QMainWindow)
```
- GUI main window and interface management
- Handle user operations and events
- Coordinate interactions between components

### Performance Optimization Features

1. **Asynchronous Loading**: Font loading uses dedicated threads to avoid UI freezing
2. **Caching Mechanism**: Preview effect caching, reduce repeated drawing overhead
3. **Delayed Updates**: Use QTimer for debouncing, avoid frequent refreshes
4. **Memory Optimization**: Font style filtering, remove redundant variants
5. **Thread Safety**: UI thread separated from loading thread, improve responsiveness

## 🎨 Custom Styles

The application uses Qt style sheets for appearance customization:
- Modern blue theme color scheme
- Rounded buttons and borders
- Hover state animation effects
- High contrast visual design

## 🐛 Troubleshooting

### Common Issues Resolution

**1. Slow Font Loading**
- This is normal, system fonts take time on first load
- Subsequent launches will use cache, speed will improve significantly

**2. Some Fonts Not Displaying**
- Some special fonts (like icon fonts) may not show preview
- This is because they don't contain standard character sets

**3. Interface Display Abnormal**
- Ensure Chinese fonts are installed on the system
- Check if graphics card driver supports OpenGL acceleration

**4. Cannot Start Application**
- Check if Python version is 3.11+
- Ensure PySide6 is correctly installed
- Run command to check: `python -c "import PySide6; print('PySide6 OK')"`

## 📄 License

This project has not specified an open source license yet. Please contact the developer for commercial use.

## 🤝 Contribution Guidelines

Welcome to submit Issues and Pull Requests to improve the project!

### Development Environment Setup
```bash
# Install development dependencies
pip install black flake8 pytest

# Run code formatting
black main.py

# Run code checking
flake8 main.py
```

## 📞 Contact Us

If you have questions or suggestions, please contact us through:
- Submit GitHub Issue
- Send email to developer mailbox

---

**Project Version**: v1.0.0 | **Last Updated**: 2024