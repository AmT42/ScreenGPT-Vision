import sys
import requests
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QObject, QByteArray, QBuffer, QThread
from PyQt5.QtGui import QPixmap, QPainter, QPen, QIcon, QGuiApplication, QImage
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QTextEdit, QDialog, QVBoxLayout,
                             QLabel, QWidget, QHBoxLayout, QLineEdit, QScrollArea)
import base64

def pixmap_to_base64(pixmap):
    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QBuffer.WriteOnly)
    pixmap.save(buffer, "JPEG")
    base64_data = base64.b64encode(byte_array.data()).decode("utf-8")
    return f"data:image/jpeg;base64, {base64_data}"

class WorkerSignals(QObject):
    finished = pyqtSignal(object) # The parameter will be the response from the server

# Constants for image sizes and spacing
IMAGE_WIDTH = 160
IMAGE_HEIGHT = 120
IMAGE_SPACING = 10  # Space between images

class APICaller(QThread):
    response_received = pyqtSignal(object)
     
    def __init__(self, url, data):
        super().__init__()
        self.url = url
        self.data = data

    def run(self):
        response = requests.post(self.url, json = self.data)
        self.response_received.emit(response)

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


    def queueScreenshot(self, pixmap):
        # Scale the screenshot to a standard size
        normalized_pixmap = pixmap.scaled(IMAGE_WIDTH, IMAGE_HEIGHT, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.queued_images.append(normalized_pixmap)

        # Create a label for the thumbnail, set a fixed size to avoid different sizes being displayed
        label = QLabel()
        label.setPixmap(normalized_pixmap)
        label.setFixedSize(IMAGE_WIDTH + IMAGE_SPACING, IMAGE_HEIGHT)  # Include spacing in fixed size
        label.setStyleSheet(f"margin-right: {IMAGE_SPACING}px;")  # Add spacing between thumbnails
        self.image_preview_layout.addWidget(label)

    def sendMessage(self):
        message = self.text_input.text().strip()
        if message or self.queued_images:
            # Display the user's message and images in the chat
            self.appendMessage("You:", message, self.queued_images)
            
            # Convert queued images to base64 strings
            base64_images = [pixmap_to_base64(img) for img in self.queued_images]

            # Prepare the data for the POST request
            data = {"text": message, "images": base64_images}
            
            # Create and start a thread to send the request without freezing the UI
            api_caller = APICaller('http://localhost:8000/chatGPT', data)
            api_caller.response_received.connect(self.handleResponse)
            api_caller.start()

            self.text_input.clear()
            self.clearImagePreviews()
            self.queued_images = []  # Clear the image queue

    def handleResponse(self, response):
        if response.status_code == 200:
            # Append response to chat display
            self.appendMessage("GPT:", response.json()["response"])
        else:
            # Handle error
            self.appendMessage("Error:", "Failed to get response from the server.")

    def clearImagePreviews(self):
        # Clear the preview area
        for i in reversed(range(self.image_preview_layout.count())): 
            widget_to_remove = self.image_preview_layout.itemAt(i).widget()
            if widget_to_remove is not None:  # Check if it is a widget before removing
                self.image_preview_layout.removeWidget(widget_to_remove)
                widget_to_remove.setParent(None)


    
    def appendMessage(self, prefix, message, images=None):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.End)
        self.chat_display.setTextCursor(cursor)
        
        # Insert text message if available
        if message:
            self.chat_display.insertPlainText(prefix + " " + message + "\n")
        
        # Insert images if available
        if images:
            for img in images:
                cursor.insertImage(img.toImage())
                cursor.insertText(" ")  # Add space after each image

            self.chat_display.insertPlainText("\n")  # Add a newline after the last image

        self.chat_display.ensureCursorVisible()


def main():
    app = QApplication(sys.argv)
    chat_app = ChatApp()
    chat_app.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()