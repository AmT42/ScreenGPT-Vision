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

class ImageThumbnail(QWidget):
    def __init__(self, pixmap, original_pixmap, delete_callback, parent=None):
        super().__init__(parent)
        self.original_pixmap = original_pixmap  # Store the original pixmap
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap)
        self.layout.addWidget(self.image_label)

        self.delete_button = QPushButton('❌')  # Using a simple 'X' as a delete symbol
        self.delete_button.setFixedSize(16, 16)  # Set the size of the button
        self.delete_button.clicked.connect(delete_callback)
        self.layout.addWidget(self.delete_button)
        self.layout.setAlignment(self.delete_button, Qt.AlignTop)

    def on_delete_clicked(self):
        self.setParent(None)
        self.deleteLater()

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
    finished = pyqtSignal()

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
        self.hide()  # Hide the screenshot dialog
        QGuiApplication.processEvents()  # Process any pending events to ensure the dialog is hidden

        # Get the current screen based on the application's window
        current_screen = QGuiApplication.screenAt(self.pos())

        # Now we take the screenshot of the current screen
        screenshot = current_screen.grabWindow(0)
        
        # Translate the selection points to global coordinates
        global_begin = QApplication.desktop().mapToGlobal(self.begin)
        global_end = QApplication.desktop().mapToGlobal(self.end)

        # Make a QRect from the two global points and normalize it
        selection_rect = QRect(global_begin, global_end).normalized()

        # Crop the screenshot to the selection_rect
        cropped = screenshot.copy(selection_rect)
        self.screenshotTaken.emit(cropped)  # Emit the signal with the cropped screenshot
        self.finished.emit()  # Emit the finished signal
        self.show()  # Show the screenshot dialog again if needed

        


class ChatApp(QMainWindow):
    
    CHAT_DISPLAY_IMAGE_WIDTH = 200  # Width you want for the chat history images
    CHAT_DISPLAY_IMAGE_HEIGHT = 150  # Height you want for the chat history images

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Chat with GPT')
        self.setGeometry(100, 100, 480, 600)
        self.initUI()
        self.queued_images = []   # This will hold the QPixmap of the screenshot
        self.api_thread = None  # Initialize an attribute to hold the thread
        self.loading_animation_timer = QTimer()  # Timer for loading animation
        self.loading_animation_timer.timeout.connect(self.updateLoadingAnimation)
        self.current_loading_text = ""  # Current text of the loading animation

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
        self.hide()  # Hide the main chat window
        self.screenshot_dialog = ScreenshotDialog()
        self.screenshot_dialog.screenshotTaken.connect(self.queueScreenshot)
        self.screenshot_dialog.finished.connect(self.show)  # Re-show the main chat window after the screenshot dialog is finished
        self.screenshot_dialog.show()

    
    # def queueScreenshot(self, pixmap):
    #     # Store the original pixmap in the queue, not the scaled version
    #     self.queued_images.append(pixmap)

    #     # Scale the pixmap for displaying as a thumbnail in the UI
    #     thumbnail_pixmap = pixmap.scaled(IMAGE_WIDTH, IMAGE_HEIGHT, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    #     thumbnail_widget = ImageThumbnail(thumbnail_pixmap, self.deleteImage)
    #     self.image_preview_layout.addWidget(thumbnail_widget)
    #     thumbnail_widget.show()

    def queueScreenshot(self, pixmap):
    # Store the original pixmap in the queue, not the scaled version
        self.queued_images.append(pixmap)

        # Scale the pixmap for displaying as a thumbnail in the UI
        thumbnail_pixmap = pixmap.scaled(IMAGE_WIDTH, IMAGE_HEIGHT, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        thumbnail_widget = ImageThumbnail(thumbnail_pixmap, pixmap, self.deleteImage)  # Pass the original pixmap here
        self.image_preview_layout.addWidget(thumbnail_widget)
        thumbnail_widget.show()

    # def deleteImage(self):
    #     button = self.sender()
    #     if button:
    #         # Find the parent widget, which is the ImageThumbnail, and delete it
    #         thumbnail_widget = button.parent()
    #         index = self.image_preview_layout.indexOf(thumbnail_widget)
    #         self.image_preview_layout.takeAt(index)
    #         thumbnail_widget.deleteLater()
    #         # Also remove the pixmap from the queued_images list
    #         if thumbnail_widget.image_label.pixmap() in self.queued_images:
    #             self.queued_images.remove(thumbnail_widget.image_label.pixmap())

    def deleteImage(self):
        button = self.sender()
        if button:
            # Find the parent widget, which is the ImageThumbnail, and delete it
            thumbnail_widget = button.parent()
            index = self.image_preview_layout.indexOf(thumbnail_widget)
            
            # Remove the pixmap from the queued_images list
            if thumbnail_widget.original_pixmap in self.queued_images:
                self.queued_images.remove(thumbnail_widget.original_pixmap)

            # Now remove the thumbnail widget from the layout and delete it
            self.image_preview_layout.takeAt(index)
            thumbnail_widget.deleteLater()

    def sendMessage(self):
        message = self.text_input.text().strip()
        if message or self.queued_images:
            # Display the user's message and images in the chat
            self.appendMessage("You:", message, self.queued_images)
            
            # Convert queued images to base64 strings
            base64_images = [pixmap_to_base64(pixmap) for pixmap in self.queued_images]


            # Prepare the data for the POST request
            data = {"text": message, "images": base64_images}

            self.send_button.setEnabled(False)  # Disable the send button
            self.startLoadingAnimation()  # Start the loading animation

             # Instead of creating a local variable, assign the APICaller to the class attribute
            self.api_thread = APICaller('http://localhost:8000/chatGPT', data)
            self.api_thread.response_received.connect(self.handleResponse)
            self.api_thread.finished.connect(self.api_thread.deleteLater)  # Ensure proper cleanup
            self.api_thread.start()

            self.text_input.clear()
            self.clearImagePreviews()
            self.queued_images = []  # Clear the image queue

    def startLoadingAnimation(self):
        self.current_loading_text = "GPT: thinking"
        self.loading_animation_timer.start(500)  # Update the animation every 500ms

    def updateLoadingAnimation(self):
        # Simply update the number of dots for the loading animation
        num_dots = (len(self.current_loading_text) - len("GPT: thinking")) % 3 + 1
        self.current_loading_text = "GPT: thinking" + "." * num_dots
        self.updateChatDisplayWithLoadingText()

    def updateChatDisplayWithLoadingText(self):
        cursor = self.chat_display.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(cursor.End)
        # Move the cursor to the start of the line where "GPT: thinking" starts
        cursor.movePosition(cursor.StartOfLine, cursor.KeepAnchor)
        # Check if the current line contains "GPT: thinking"
        if "GPT: thinking" in cursor.selectedText():
            # If so, remove only the "GPT: thinking..." part
            cursor.removeSelectedText()
            cursor.insertText(self.current_loading_text)
        else:
            # If not, it means this is the first frame of the animation
            # Insert the initial loading text without a newline
            cursor.insertText(self.current_loading_text)
        cursor.endEditBlock()
        self.chat_display.ensureCursorVisible()

    def handleResponse(self, response):
        self.send_button.setEnabled(True)  # Re-enable the send button
        self.loading_animation_timer.stop()  # Stop the loading animation

        # Clear the loading text before displaying the response
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.LineUnderCursor)
        cursor.removeSelectedText()

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
            for pixmap in images:
                # Scale the pixmap for displaying in the chat history
                chat_display_pixmap = pixmap.scaled(self.CHAT_DISPLAY_IMAGE_WIDTH, self.CHAT_DISPLAY_IMAGE_HEIGHT, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                cursor.insertImage(chat_display_pixmap.toImage())
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