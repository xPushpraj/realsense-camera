import sys
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLineEdit
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from camera_thread import CameraThread
from excel_writer import save_to_excel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Human Body Measurement")
        self.setGeometry(100, 100, 800, 600)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter Name")

        self.capture_btn = QPushButton("Capture Measurements")
        self.capture_btn.clicked.connect(self.capture)

        self.result_label = QLabel("Measurements: --")
        self.result_label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.name_input)
        layout.addWidget(self.label)
        layout.addWidget(self.capture_btn)
        layout.addWidget(self.result_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.thread = CameraThread()
        self.thread.frame_updated.connect(self.update_frame)
        self.thread.measurements_ready.connect(self.show_results)
        self.thread.start()

    def update_frame(self, frame):
        img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_BGR888)
        self.label.setPixmap(QPixmap.fromImage(img))

    def capture(self):
        self.thread.capture()

    def show_results(self, measurements):
        name = self.name_input.text().strip()
        if name:
            save_to_excel(name, measurements)
            self.result_label.setText(f"Measurements for {name}: {measurements}")
        else:
            self.result_label.setText("Please enter a name!")

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
