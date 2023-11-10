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
        self.queued_images = []   # This will hold the QPixmap of the screenshot

    def initUI(self):
        # Main layout container
        main_layout = QVBoxLayout()
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        main_layout.addWidget(self.chat_display)

        # Horizontal layout for image previews
        self.image_preview_layout = QHBoxLayout()
        
        # Scroll area for image previews
        self.image_preview_scroll_area = QScrollArea()
        self.image_preview_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.image_preview_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.image_preview_scroll_area.setWidgetResizable(True)
        
        # Container widget for the images
        self.image_preview_widget = QWidget()
        self.image_preview_widget.setLayout(self.image_preview_layout)
        self.image_preview_scroll_area.setWidget(self.image_preview_widget)
        
        # Fixed height for the scroll area to make it look like an input area, but expandable width
        self.image_preview_scroll_area.setFixedHeight(120)
        main_layout.addWidget(self.image_preview_scroll_area)

        # Text input for messages
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText('Type your message here...')
        main_layout.addWidget(self.text_input)

        # Send button
        self.send_button = QPushButton('Send')
        self.send_button.clicked.connect(self.sendMessage)
        
        # Screenshot button
        self.screenshot_button = QPushButton('Screenshot')
        self.screenshot_button.clicked.connect(self.openScreenshotDialog)
        
        # Layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.send_button)
        button_layout.addWidget(self.screenshot_button)
        main_layout.addLayout(button_layout)

        # Central widget setup
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)


    def openScreenshotDialog(self):
        self.screenshot_dialog = ScreenshotDialog()
        self.screenshot_dialog.screenshotTaken.connect(self.queueScreenshot)
        self.screenshot_dialog.show()

    # def displayScreenshotPreview(self, pixmap):
    #     # Normalize the screenshot size to the smaller fixed size
    #     normalized_pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    #     self.screenshot_pixmap = normalized_pixmap
    #     self.screenshot_label.setPixmap(normalized_pixmap)

    def queueScreenshot(self, pixmap):
        # Normalize the screenshot size and add it to the queue
        normalized_pixmap = pixmap.scaled(160, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.queued_images.append(normalized_pixmap)

        # Create a label to show the thumbnail and add it to the image_preview_layout
        label = QLabel()
        label.setPixmap(normalized_pixmap)
        label.setFixedSize(160, 120)
        self.image_preview_layout.addWidget(label) 

    def sendMessage(self):
        message = self.text_input.text().strip()
        if message or self.queued_images:
            self.appendMessage("You:", message, self.queued_images)
            self.text_input.clear()
            # Clear the preview area
            for i in reversed(range(self.image_preview_layout.count())): 
                widget_to_remove = self.image_preview_layout.itemAt(i).widget()
                if widget_to_remove is not None:  # Check if it is a widget before removing
                    self.image_preview_layout.removeWidget(widget_to_remove)
                    widget_to_remove.setParent(None)
            self.queued_images.clear() 

    def appendMessage(self, prefix, message, images=None):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.End)
        self.chat_display.setTextCursor(cursor)
        if message:
            self.chat_display.insertPlainText(prefix + " " + message + "\n")
        if images:
            for image in images:
                cursor.insertBlock()
                cursor.insertImage(image.toImage())
            cursor.insertBlock()
        self.chat_display.ensureCursorVisible()


def main():
    app = QApplication(sys.argv)
    chat_app = ChatApp()
    chat_app.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()