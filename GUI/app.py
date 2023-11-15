import sys
import requests
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QObject, QByteArray, QBuffer, QThread, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QPen, QIcon, QGuiApplication, QImage, QKeySequence
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QTextEdit, QDialog, QVBoxLayout,
                             QLabel, QWidget, QHBoxLayout, QLineEdit, QScrollArea, QShortcut)
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

    # def showEvent(self, event):
    #     super().showEvent(event)
    #     self.activateWindow()  # Make sure the window is active
    #     self.raise_()   


    def paintEvent(self, event):
        if self.is_selecting:
            qp = QPainter(self)
            qp.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            qp.setBrush(Qt.transparent)
            
            # Translate the coordinates relative to the virtual desktop
            global_begin = QApplication.desktop().mapToGlobal(self.begin)
            global_end = QApplication.desktop().mapToGlobal(self.end)

            # Since the dialog is full screen, map back from global to local
            local_begin = self.mapFromGlobal(global_begin)
            local_end = self.mapFromGlobal(global_end)
            
            rect = QRect(local_begin, local_end).normalized()
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
        self.end = event.pos()
        self.is_selecting = False
        self.takeScreenshot()
        self.close()  # Exit the screenshot mode

    def takeScreenshot(self):
        # ... existing code to hide the dialog and process events ...
        self.hide()
        QGuiApplication.processEvents()

        # Get the current screen based on the application's window
        current_screen = QGuiApplication.screenAt(self.pos())

        # Now we take the screenshot of the current screen
        screenshot = current_screen.grabWindow(0)
        # Take a screenshot of the entire virtual desktop
        # full_screenshot = QGuiApplication.primaryScreen().grabWindow(QApplication.desktop().winId())

        # Translate the selection points to global coordinates
        global_begin = QApplication.desktop().mapToGlobal(self.begin)
        global_end = QApplication.desktop().mapToGlobal(self.end)

        # Make a QRect from the two global points and normalize it
        selection_rect = QRect(global_begin, global_end).normalized()

        # Crop the full_screenshot to the selection_rect
        cropped = screenshot.copy(selection_rect)
        self.screenshotTaken.emit(cropped)
        self.show()  # Show the dialog again if needed
        


class ChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Chat with GPT')
        self.setGeometry(100, 100, 480, 600)
        self.initUI()
        self.queued_images = []   # This will hold the QPixmap of the screenshot
        self.api_thread = None  # Initialize an attribute to hold the thread

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

        # Set the shortcut to the screenshot
        shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        shortcut.activated.connect(self.openScreenshotDialog)

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
            
             # Instead of creating a local variable, assign the APICaller to the class attribute
            self.api_thread = APICaller('http://localhost:8000/chatGPT', data)
            self.api_thread.response_received.connect(self.handleResponse)
            self.api_thread.finished.connect(self.api_thread.deleteLater)  # Ensure proper cleanup
            self.api_thread.start()

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
        self.api_thread = None 

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