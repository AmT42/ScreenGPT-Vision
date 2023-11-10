import sys
import requests
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QPainter, QPen, QIcon, QGuiApplication, QImage
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QTextEdit, QDialog, QVBoxLayout,
                             QLabel, QWidget, QHBoxLayout, QLineEdit, QScrollArea)


class WorkerSignals(QObject):
    finished = pyqtSignal(object) # The parameter will be the response from the server


# class ScreenshotWorker(QRunnable):
#     def __init__(self, image_path, text):
#         super(ScreenshotWorker, self).__init__()
#         self.image_path = image_path
#         self.text = text
#         self.signlats = WorkerSignals()

#     def run(self):
#         # Here you would send the image and text to your server
#         # I'm using 'httpbin.org/post' as a placeholder URL for demonstration
#         url = 'http://httpbin.org/post'
#         files = {'screenshot': open(self.image_path, 'rb')}
#         data = {'text': self.text}
#         # response = requests.post(url, files=files, data=data)
#         # self.signals.finished.emit(response.json())  # Emit the response

class ScreenshotDialog(QDialog):

    screenshotTaken = pyqtSignal(QPixmap)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowState(self.windowState() | Qt.WindowFullScreen)
        self.begin = QPoint()
        self.end = QPoint()
        self.is_selecting = False

    def paintEvent(self, event):
        if self.is_selecting:
            qp = QPainter(self)
            qp.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            qp.setBrush(Qt.transparent)
            rect = QRect(self.begin, self.end)
            qp.drawRect(rect)

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = self.begin
        self.is_selecting = True
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.is_selecting = False
        self.takeScreenshot()

    def takeScreenshot(self):
        self.hide()  # Hide the overlay before taking the screenshot
        screenshot = QGuiApplication.primaryScreen().grabWindow(0)
        rect = QRect(self.begin, self.end).normalized()
        cropped = screenshot.copy(rect)
        self.screenshotTaken.emit(cropped)  # Emit the screenshot QPixmap
        self.close()   # Close the dialog after taking the screenshot


class ChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Chat with GPT')
        self.setGeometry(100, 100, 480, 600)
        self.initUI()
        self.screenshot_pixmap = None  # This will hold the QPixmap of the screenshot

    def initUI(self):
        # Chat display area
        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)

        # Screenshot preview area
        self.screenshot_label = QLabel(self)
        self.screenshot_label.setAlignment(Qt.AlignCenter)
        self.screenshot_label.setFixedSize(60, 60)  # Smaller fixed size
        self.screenshot_label.setStyleSheet("background-color: rgba(0, 0, 0, 0);") 

        # Text input for messages
        self.text_input = QLineEdit(self)
        self.text_input.setPlaceholderText('Type your message here...')
        
        # Send button
        self.send_button = QPushButton('Send', self)
        self.send_button.clicked.connect(self.sendMessage)

        # Screenshot button
        self.screenshot_button = QPushButton('Screenshot', self)
        self.screenshot_button.clicked.connect(self.openScreenshotDialog)

        # Layout setup
        layout = QVBoxLayout()
        chat_area = QWidget()
        chat_area.setLayout(layout)
        layout.addWidget(self.chat_display)
        layout.addWidget(self.screenshot_label)  # Add the screenshot preview area to the layout
        layout.addWidget(self.text_input)
        
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.send_button)
        controls_layout.addWidget(self.screenshot_button)

        controls_widget = QWidget()
        controls_widget.setLayout(controls_layout)

        layout.addWidget(controls_widget)

        self.setCentralWidget(chat_area)

    def openScreenshotDialog(self):
        self.screenshot_dialog = ScreenshotDialog()
        self.screenshot_dialog.screenshotTaken.connect(self.displayScreenshotPreview)
        self.screenshot_dialog.show()

    def displayScreenshotPreview(self, pixmap):
        # Normalize the screenshot size to the smaller fixed size
        normalized_pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.screenshot_pixmap = normalized_pixmap
        self.screenshot_label.setPixmap(normalized_pixmap)

    def sendMessage(self):
        message = self.text_input.text().strip()
        if message or self.screenshot_pixmap:
            self.appendMessage("You:", message, self.screenshot_pixmap)
            self.text_input.clear()
            self.screenshot_label.clear()  # Clear the preview
            self.screenshot_label.setFixedSize(60, 60)  # Reset the size if it was changed
            self.screenshot_pixmap = None  # Reset the screenshot pixmap

    def appendMessage(self, prefix, message, pixmap=None):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.End)
        self.chat_display.setTextCursor(cursor)
        if message:
            self.chat_display.insertPlainText(prefix + " " + message + "\n")
        if pixmap:
            # Ensure we add a newline before and after the image if there is also text
            if message:
                cursor.insertBlock()
            cursor.insertImage(pixmap.toImage())
            if message:
                cursor.insertBlock()
        self.chat_display.ensureCursorVisible()


def main():
    app = QApplication(sys.argv)
    chat_app = ChatApp()
    chat_app.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()