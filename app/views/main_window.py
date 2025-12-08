# View Module
#### IMPORT ####
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QGraphicsScene,
    QSlider, QLineEdit, QToolBar, QCheckBox
)
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtCore import Qt, QSize

# Self-made Module
from app.views.video_views import VideoView
################

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        """オブジェクトのコンストラクタ

        Args:
            parent (_type_, optional): 他に表示するウィンドウ. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Movie Annotation Tool (MAT)")
        self.setGeometry(100, 100, 1280, 720)

        # 主要UIの初期化
        self._create_actions()
        self._create_menubar()
        self._create_toolbar()
        self._create_central_widget()
    
    def _create_actions(self):
        """動作処理の初期化
        """
        # 基本機能(IO・exit)
        self.open_video_action = QAction(QIcon.fromTheme("folder-open"), "Open Movie File", self)
        self.open_track_action = QAction(QIcon.fromTheme("document-open-csv"), "Open Tracking File", self)
        self.save_action = QAction(QIcon.fromTheme("document-save"), "Save", self)
        self.save_action.setShortcut("Ctrl+S")
        self.undo_action = QAction(QIcon.fromTheme("edit-undo"), "Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.exit_action = QAction(QIcon.fromTheme("application-exit"), "Exit", self)

        # 動画再生機能
        ## 再生・停止機能(スペースキー)
        self.play_pause_action = QAction('Play/Pause', self)
        self.play_pause_action.setShortcut(Qt.Key.Key_Space)
        ## 次フレームへ(Dキー・→キー)
        self.next_frame_action = QAction("Next Frame", self)
        self.next_frame_action.setShortcuts([Qt.Key.Key_D, Qt.Key.Key_Right])
        ## 前のフレームへ (Aキー, ←キー)
        self.prev_frame_action = QAction("Previous Frame", self)
        self.prev_frame_action.setShortcuts([Qt.Key.Key_A, Qt.Key.Key_Left])

        # 追跡ID関連
        self.delete_id_action = QAction("Delete Selected ID", self)
        self.delete_id_action.setShortcut(QKeySequence.StandardKey.Delete)

        # ログ保存機能
        self.save_log_action = QAction(QIcon.fromTheme("document-save-as"), "Save Log", self)
        self.save_log_action.setToolTip("Save the working log as a CSV file.")
        
        self.addActions([
            self.play_pause_action,
            self.next_frame_action,
            self.prev_frame_action,
            self.delete_id_action,
            self.undo_action
        ])


    def _create_menubar(self):
        """Menu Barの作成
        """
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        file_menu.addAction(self.open_video_action)
        file_menu.addAction(self.open_track_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_log_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

    def _create_toolbar(self):
        """Tool Barの作成
        """
        self.toolbar = QToolBar("Main Tool Bar")
        self.toolbar.setIconSize(QSize(24,24))
        self.addToolBar(self.toolbar)

        self.toolbar.addAction(self.undo_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.open_video_action)
        self.toolbar.addAction(self.open_track_action)
        self.toolbar.addAction(self.save_action)
        self.toolbar.addAction(self.save_log_action)
        self.toolbar.addSeparator()

        # 編集モードの切り替えボタン
        self.edit_mode_button = QPushButton("✏️ edit")
        self.edit_mode_button.setCheckable(True) # Bool(On/Off)
        self.edit_mode_button.setShortcut(Qt.Key.Key_W)
        self.edit_mode_button.setToolTip("Switch BBox editing mode (W key)")
        self.toolbar.addWidget(self.edit_mode_button)


        # 追跡ID更新時の処理切り替え
        self.toolbar.addSeparator()
        self.apply_subsequent_update_id_checkbox =QCheckBox("Update in subsequent frames")
        self.apply_subsequent_update_id_checkbox.setToolTip("When modifying an ID, \nsubsequent frames will also be updated in bulk.")
        self.toolbar.addWidget(self.apply_subsequent_update_id_checkbox)

    def _create_central_widget(self):
        """メインウィンドウ内のコンテンツを作成
        """
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # メインレイアウト (左右分割)
        main_layout = QHBoxLayout(main_widget)

        # 1. 動画関連UI(画面左側)
        left_layout = QVBoxLayout()
        
        # 1-1. 動画表示エリア
        # QGraphicsView は、画像(フレーム)の上にBBoxなどの図形を
        # 効率的に描画・操作するのに最適です。
        self.video_scene = QGraphicsScene()
        self.video_view = VideoView(self.video_scene)
        self.video_view.setStyleSheet("background-color: #333;") # 背景色
        left_layout.addWidget(self.video_view, stretch=1) # widgetの大きさ調整

        # 1-2. 再生スライダー (シークバー)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        left_layout.addWidget(self.slider)

        # 1-3. コントロールボタンとフレーム表示
        controls_layout = QHBoxLayout()
        ## 操作ボタン
        self.prev_frame_button = QPushButton("<< Prev")
        self.play_pause_button = QPushButton("▶ 再生")
        self.next_frame_button = QPushButton("Next >>")
        controls_layout.addWidget(self.prev_frame_button)
        controls_layout.addWidget(self.play_pause_button)
        controls_layout.addWidget(self.next_frame_button)
        controls_layout.addStretch()
        ## フレーム表示エリア
        frame_display_layout = QVBoxLayout()
        self.frame_label = QLabel("Frame: - / -")
        self.frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timestep_label = QLabel("Timestep: - / -")
        self.timestep_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_display_layout.addWidget(self.frame_label)
        frame_display_layout.addWidget(self.timestep_label)
        controls_layout.addLayout(frame_display_layout)
        controls_layout.addStretch()
        ## Timestepの設定エリア
        set_step_layout = QHBoxLayout()
        set_step_layout.addWidget(QLabel("Step:"))
        self.step_lineedit = QLineEdit("1") # デフォルトはstr(1)
        self.step_lineedit.setFixedWidth(50) # 入力フォームの幅
        self.step_lineedit.setReadOnly(True) # デフォルトはReadOnly
        self.set_step_button = QPushButton("Set")
        self.set_step_button.setToolTip("Change the Step Size.")
        set_step_layout.addWidget(self.step_lineedit)
        set_step_layout.addWidget(self.set_step_button)
        controls_layout.addLayout(set_step_layout)

        left_layout.addLayout(controls_layout)
        
        # 2. 追跡IDリスト(画面右側)
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Tracking ID"))
        self.tracking_list = QListWidget() # クリックされたIDをコントローラーに通知
        right_layout.addWidget(self.tracking_list, stretch=1)

        ## 追跡ID削除ボタン
        self.delete_id_button = QPushButton(QIcon.fromTheme("edit-delete"), "Delete Selected ID")
        self.delete_id_button.setToolTip("Delete the selected ID from the list (Del key)")
        right_layout.addWidget(self.delete_id_button)

        # メインレイアウトの配置(left:right =3:1)
        main_layout.addLayout(left_layout, stretch=3)
        main_layout.addLayout(right_layout, stretch=1)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    print("Fin.")