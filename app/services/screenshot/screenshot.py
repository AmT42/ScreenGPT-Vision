import pyautogui
from PIL import Image
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPixmap, QPen




def capture_screen(x_start, y_start, width, height):
    # Capture a region of the screen
    screenshot = pyautogui.screenshot(region = (x_start, y_start, width, height))
    return screenshot

class ScreenshotGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Screenshot Tool')
        self.setGeometry(100, 100, 800, 600)
        self.begin = None
        self.end = None
        self.is_pressed = False

        # Set the window transparency
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowOpacity(0.3)  # Set the opacity
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        btn = QPushButton('Take Screenshot', self)
        btn.clicked.connect(self.takeScreenshot)

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        self.is_pressed = True
        self.update()

    def mouseMoveEvent(self, event):
        if self.is_pressed:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self.is_pressed = False
        self.takeScreenshot()

    def keyPressEvent(self, event):
        # Check if the 'Escape' key is pressed
        if event.key() == Qt.Key_Escape:
            self.close()  # Close the application


    def takeScreenshot(self):
        if self.begin is None or self.end is None:
            return
        self.hide()  # Hide the window before taking screenshot

        # Delay added to ensure the window is hidden before the screenshot is taken
        QApplication.processEvents()  # Corrected to QApplication

        x1 = min(self.begin.x(), self.end.x())
        y1 = min(self.begin.y(), self.end.y())
        x2 = max(self.begin.x(), self.end.x())
        y2 = max(self.begin.y(), self.end.y())

        # Create the screenshot directly with PyAutoGUI
        screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
        screenshot.save('screenshot.png')
        print("Screenshot taken and saved as screenshot.png")

        self.close() 

    def paintEvent(self, event):
        if self.begin is None or self.end is None:
            return
        qp = QPainter(self)
        qp.setPen(QPen(Qt.red, 3, Qt.DashLine))
        qp.setBrush(Qt.transparent)
        rect = QRect(self.begin, self.end)
        qp.drawRect(rect)

def main():
    app = QApplication(sys.argv)
    ex = ScreenshotGui()
    ex.showFullScreen()  # Make the window full screen
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()