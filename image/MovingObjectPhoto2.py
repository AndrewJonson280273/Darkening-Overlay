from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QFileDialog
from PyQt5.QtGui import QPixmap, QPainter, QImage, QPen, QBrush, QCursor, QMouseEvent
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent
from PIL import Image
import sys


class CanvasLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(640, 480)
        self.pixmap = QPixmap(640, 480)
        self.setPixmap(self.pixmap)

        self.layers = []
        self.active_layer_index = None
        self.dragging = False
        self.mouse_position = QPoint()

        self.highlight_color = Qt.green  # Цвет рамки при наведении
        self.selection_color = Qt.red  # Цвет рамки при выделении

        # Устанавливаем фильтр событий для CanvasLabel
        self.installEventFilter(self)

    def eventFilter(self, watched, event):
        if watched == self and event.type() == QEvent.MouseMove:
            pos = event.pos()
            if self.rect().contains(pos):
                return False  # Пропускаем событие дальше
            else:
                self.leaveEvent(event)  # Вызываем leaveEvent вручную
                return True  # Отменяем дальнейшее распространение события
        return super(CanvasLabel, self).eventFilter(watched, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Определяем, находится ли курсор над одним из слоев
            for index, layer in reversed(list(enumerate(self.layers))):
                if layer.image is not None:
                    rect = QRect(layer.offset, layer.image.size())
                    if rect.contains(event.pos()):
                        self.active_layer_index = index
                        break
            else:
                self.active_layer_index = None

            if self.active_layer_index is not None:
                self.dragging = True
                self.mouse_position = event.pos()

            self.update_canvas()  # Обновляем холст сразу после выбора слоя

    def mouseMoveEvent(self, event):
        if self.dragging:
            offset = event.pos() - self.mouse_position
            self.move_active_layer(offset)
            self.mouse_position = event.pos()
            self.update_canvas()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def enterEvent(self, event):
        # Подсветка рамки при наведении курсора
        self.highlight_color = Qt.green
        self.update_canvas()

    def leaveEvent(self, event):
        # Удаляем подсветку рамки при уходе курсора
        self.highlight_color = Qt.NoPen
        self.update_canvas()

    def move_active_layer(self, offset):
        if self.active_layer_index is not None:
            layer = self.layers[self.active_layer_index]
            layer.offset += offset

    def update_canvas(self):
        self.pixmap.fill(Qt.transparent)
        painter = QPainter(self.pixmap)

        for i, layer in enumerate(self.layers):
            if layer.image is not None:
                if i == 0:
                    painter.drawPixmap(layer.offset, layer.image)
                else:
                    painter.setCompositionMode(QPainter.CompositionMode_Darken)
                    painter.drawPixmap(layer.offset, layer.image)

                # Рисуем рамку вокруг активного слоя
                if i == self.active_layer_index:
                    pen = QPen(self.selection_color)
                    pen.setWidth(1)
                    painter.setPen(pen)
                    painter.drawRect(layer.offset.x(), layer.offset.y(), layer.image.width(), layer.image.height())
                elif self.highlight_color != Qt.NoPen:
                    pen = QPen(self.highlight_color)
                    pen.setWidth(1)
                    painter.setPen(pen)
                    painter.drawRect(layer.offset.x(), layer.offset.y(), layer.image.width(), layer.image.height())

        painter.end()  # Завершаем работу с QPainter
        self.setPixmap(self.pixmap)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle("Image Editor")

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()

        self.canvas_label = CanvasLabel(self)

        open_button = QPushButton("Открыть изображение", self)
        open_button.clicked.connect(self.open_image)

        add_layer_button = QPushButton("Добавить слой", self)
        add_layer_button.clicked.connect(self.add_layer)

        remove_layer_button = QPushButton("Удалить активный слой", self)
        remove_layer_button.clicked.connect(self.remove_active_layer)

        save_button = QPushButton("Сохранить", self)
        save_button.clicked.connect(self.save_image)

        hbox.addWidget(open_button)
        hbox.addWidget(add_layer_button)
        hbox.addWidget(remove_layer_button)
        hbox.addWidget(save_button)

        vbox.addLayout(hbox)
        vbox.addWidget(self.canvas_label)

        self.setLayout(vbox)

        self.show()

    def open_image(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Images (*.png *.jpg *.bmp)", options=options)
        if filename:
            layer = Layer(filename)
            self.canvas_label.layers.append(layer)
            self.canvas_label.update_canvas()

    def add_layer(self):
        layer = Layer(None)
        self.canvas_label.layers.append(layer)
        self.canvas_label.update_canvas()

    def remove_active_layer(self):
        if self.canvas_label.active_layer_index is not None:
            del self.canvas_label.layers[self.canvas_label.active_layer_index]
            self.canvas_label.active_layer_index = None
            self.canvas_label.update_canvas()

    def save_image(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Сохранить изображение", "", "Images (*.png *.jpg *.bmp)", options=options)
        if file_name:
            self.canvas_label.pixmap.save(file_name)


class Layer:
    def __init__(self, image_path=None):
        self.image = None
        self.offset = QPoint(0, 0)
        if image_path:
            self.load_image(image_path)

    def load_image(self, path):
        try:
            self.image = QPixmap(path)
        except Exception as e:
            print(f"Ошибка загрузки изображения: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())