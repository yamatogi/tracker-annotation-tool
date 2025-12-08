# View Module
#### IMPORT ####
import sys
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QPen, QColor
################
class VideoView(QGraphicsView):
    # 矩形描画が完了したときに発火するシグナル (描画された矩形座標を渡す)
    box_drawn = pyqtSignal(QRectF)

    def __init__(self, scene: QGraphicsScene, parent=None):
        super().__init__(scene, parent)
        self.setDragMode(QGraphicsView.DragMode.NoDrag) # デフォルトはドラッグしない
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

        # BBox追加用のメンバー
        self.small_boxsize_threshold = 5 # 極端に小さい矩形を無視する閾値
        self._is_edit_mode = False # 編集モードのフラグ
        self._is_drawing = False # 描画中のフラグ
        self._start_pos = None # 描画中の開始位置(Scene座標)
        self._temp_rect_item = None # 描画中の仮表示用アイテム
    
    def set_edit_mode(self, edit_flag:bool):
        """編集モードのOn/Offを受け取り，そのフラグに合わせてマウスカーソルを切り替える

        Args:
            edit_flag (bool): 編集ボタンのOn(True)とOff(False)の値
        """
        self._is_edit_mode = edit_flag
        if edit_flag:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        """マウスクリックが行われた際の処理

        Args:
            event (QMouseEvent): マウス操作に関するイベントデータ
        """
        if self._is_edit_mode and (event.button() == Qt.MouseButton.LeftButton):
            # 追加BBoxの描画処理の場合
            self._is_drawing = True
            self._start_pos = self.mapToScene(event.pos())

            # 仮のBBox描画
            self._temp_rect_item = QGraphicsRectItem()
            pen = QPen(Qt.GlobalColor.red)
            pen.setStyle(Qt.PenStyle.DashLine)
            self._temp_rect_item.setPen(pen)
            self.scene().addItem(self._temp_rect_item)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """マウスを移動させているときの処理

        Args:
            event (QMouseEvent): マウス操作に関するイベントデータ
        """
        if self._is_drawing and self._temp_rect_item:
            # 追加BBoxの描画処理の場合
            current_pos = self.mapToScene(event.pos())
            # 開始点と現在のマウス位置で矩形を描画
            rect = QRectF(self._start_pos, current_pos).normalized()
            self._temp_rect_item.setRect(rect)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """マウスのクリックを離した際の処理

        Args:
            event (QMouseEvent): マウス操作に関するイベントデータ
        """
        if self._is_drawing and (event.button() == Qt.MouseButton.LeftButton):
            self._is_drawing = False
            if self._temp_rect_item:
                # 最終的な矩形の取得と仮データの除去
                final_rect = self._temp_rect_item.rect()
                self.scene().removeItem(self._temp_rect_item)
                self._temp_rect_item = None

                # 極端に小さい矩形は無視
                if (final_rect.width() > self.small_boxsize_threshold) and (final_rect.height() > self.small_boxsize_threshold):
                    self.box_drawn.emit(final_rect) # コントローラーに矩形追加を通知
            
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event) #親クラスのイベントも参照
        self.fit_in_view()

    def fit_in_view(self):
        rect = self.scene().sceneRect()
        if not rect.isEmpty():
            self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

if __name__ == '__main__':
    VideoView= VideoView()
    print("Fin.")