# Control Module
#### IMPORT ####
import sys
from PyQt6.QtWidgets import QApplication, QFileDialog, QInputDialog, QMessageBox
from PyQt6.QtCore import Qt, QTimer, QObject, QRectF
from PyQt6.QtGui import QPixmap, QColor, QFont, QBrush

# Self-made Module
from app.views.main_window import MainWindow
from app.models.video_model import VideoModel
from app.models.data_model import DataModel
################
class AppController(QObject):
    def __init__(self, view: MainWindow, video_model: VideoModel, data_model: DataModel, max_undo_stack=20):
        """オブジェクトのコンストラクタ

        Args:
            view (MainWindow): メインウィンドウのインスタンス
            video_model (VideoModel): 映像読み込みモデル
            data_model (DataModel): 追跡データの管理モデル
            max_undo_stack (int, optional): undo処理で戻れる最大回数. Default to 20.
        """
        super().__init__()
        # view, video, (tracking)dataの初期化
        self.view = view
        self.video_model = video_model
        self.data_model = data_model

        # Undoスタック
        self.max_undo_stack = max_undo_stack
        self.undo_stack = []

        # 動画再生関連の初期化
        self.frame_step= 1
        self.is_playing_movie = False
        self.play_timer = QTimer()
        self.play_timer.timeout.connect(self._on_next_frame) # タイマーが切れたら次のフレームへ
        
        # 画像アイテムの保存変数
        self.scene_pixmap_item= None
        
        # ハイライトする追跡IDの保持変数
        self.highlited_id = None

        # 初期化処理
        self._connect_signals()
        self._initialize_view()

    def _connect_signals(self):
        """各操作と処理メソッドの連結
        """
        # ファイルメニュー・ツールバー
        self.view.open_video_action.triggered.connect(self._on_open_video)
        self.view.open_track_action.triggered.connect(self._on_open_data)
        self.view.save_action.triggered.connect(self._on_save)
        self.view.save_log_action.triggered.connect(self._on_save_log)
        self.view.exit_action.triggered.connect(self.view.close)

        # 映像再生コントロール
        self.view.play_pause_button.clicked.connect(self._on_play_pause)
        self.view.play_pause_action.triggered.connect(self._on_play_pause)
        self.view.next_frame_button.clicked.connect(self._on_next_frame)
        self.view.next_frame_action.triggered.connect(self._on_next_frame)
        self.view.prev_frame_button.clicked.connect(self._on_prev_frame)
        self.view.prev_frame_action.triggered.connect(self._on_prev_frame)
        self.view.set_step_button.clicked.connect(self._on_set_step_button_clicked)

        # タイムスライダー
        self.view.slider.sliderMoved.connect(self._on_slider_moved) # Sliderドラッグ時更新用
        self.view.slider.sliderReleased.connect(self._on_slider_released) # Sliderリリース時更新用

        # 編集モード
        self.view.edit_mode_button.toggled.connect(self._on_edit_mode_toggled)
        self.view.video_view.box_drawn.connect(self._on_new_box_created)

        # 追跡IDリスト
        self.view.tracking_list.currentItemChanged.connect(self._on_id_selected)
        self.view.tracking_list.itemDoubleClicked.connect(self._on_id_double_clicked)
        self.view.delete_id_button.clicked.connect(self._on_delete_id)
        self.view.delete_id_action.triggered.connect(self._on_delete_id)

        # Undo処理
        self.view.undo_action.triggered.connect(self._on_undo)
    
    def _initialize_view(self):
        """UIの初期状態(無効化)の設定
        """
        self.view.play_pause_button.setEnabled(False)
        self.view.next_frame_button.setEnabled(False)
        self.view.prev_frame_button.setEnabled(False)
        self.view.slider.setEnabled(False)
        self.view.save_action.setEnabled(False)
        self.view.save_log_action.setEnabled(False)
        self.view.edit_mode_button.setEnabled(False) 
        self.view.delete_id_button.setEnabled(False)      
        self.view.undo_action.setEnabled(False) 

    def _enable_controls(self):
        """UIの有効化(保存ボタン以外)の設定
        """
        self.view.play_pause_button.setEnabled(True)
        self.view.next_frame_button.setEnabled(True)
        self.view.prev_frame_button.setEnabled(True)
        self.view.slider.setEnabled(True)
        self.view.edit_mode_button.setEnabled(True)
        self.view.delete_id_button.setEnabled(True)

        self.view.slider.setRange(0, self.video_model.num_total_frames-1)
        self.view.frame_label.setText(f"Frame: 0 / {self.video_model.num_total_frames}")

    def _on_open_video(self):
        """映像ファイルの読み込み
        """
        path, _ = QFileDialog.getOpenFileName(self.view, "Open Movie File", "", "Video Files (*.mp4 *.avi *.mov)")
        if path:
            if self.video_model.load(path):
                self._enable_controls() # UIの有効化
                self._update_views(call_frame=0)
    
    def _on_open_data(self):
        """追跡データの読み込み
        """
        path, _ = QFileDialog.getOpenFileName(self.view, "Open Tracking Data File", "", "Text Files (*.txt *.csv)")
        if path:
            if self.data_model.load(path):
                self.view.save_action.setEnabled(True) # 保存機能の有効化
                self.view.save_log_action.setEnabled(True)
                self._update_views(call_frame= self.video_model.current_frame)
    
    def _on_save(self):
        """修正後の追跡データの保存
        """
        path, _ = QFileDialog.getSaveFileName(self.view, "Save Tracking Data", "", "CSV Files (*.csv)")
        if path:
            self.data_model.save(path, step= self.frame_step)
    
    def _on_save_log(self):
        """作業ログデータの保存
        """
        if not self.data_model.log_data:
            QMessageBox.information(self.view, 'Save Log', "Don't have any Log Data.")
            return
        
        path, _ = QFileDialog.getSaveFileName(self.view, "Save Working Log", "", "CSV Files (*.csv)")
        if path:
            if not self.data_model.save_logdata(path):
                QMessageBox.warning(self.view, "Save error!", "Failed to Save Log.")


    def _on_play_pause(self):
        """映像の再生と停止処理
        """
        if self.is_playing_movie:
            # 映像再生の停止
            self.is_playing_movie = False
            self.play_timer.stop()
            self.view.play_pause_button.setText("▶ 再生")
        else:
            self.is_playing_movie = True
            self.play_timer.start(1000 // self.video_model.fps) # 映像のフレームレートで再生(msec)
            self.view.play_pause_button.setText("⏸ 一時停止")

    def _on_next_frame(self):
        """「Next」ボタンの処理
        """
        current_frame = self.video_model.current_frame
        target_farme = min(current_frame + self.frame_step, self.video_model.num_total_frames -1)
        if target_farme != current_frame:
            self._update_views(call_frame= target_farme)
        else:
            if self.is_playing_movie:
                self._on_play_pause()
    
    def _on_prev_frame(self):
        """「Prev」ボタンの処理
        """
        current_frame = self.video_model.current_frame
        target_farme = max(current_frame - self.frame_step, 0)
        if target_farme != current_frame:
            self._update_views(call_frame= target_farme)
        else:
            if self.is_playing_movie:
                self._on_play_pause()

    def _on_set_step_button_clicked(self):
        """フレームのステップ幅の設定処理

        Raises:
            ValueError: 入力された数値が0以下であった場合に起動
        """
        if self.view.step_lineedit.isReadOnly():
            # ロック解除時
            self.view.step_lineedit.setReadOnly(False)
            self.view.set_step_button.setText("OK")
            self.view.step_lineedit.setFocus()
        else:
            # 設定適用時
            try:
                new_step = int(self.view.step_lineedit.text())
                if new_step <= 0:
                    raise ValueError("Enter one or more integers.")
                
                self.frame_step = new_step
                self.view.step_lineedit.setReadOnly(True)
                self.view.set_step_button.setText("Set")
                print(f"Set the frame step to {self.frame_step}.")
                self._update_views(call_frame= self.video_model.current_frame)
            
            except ValueError as e:
                QMessageBox.warning(self.view, 'Input Error!', f"Invalid Value: {e}")


    def _on_slider_moved(self, position: int):
        """Sliderドラッグ時の処理

        Args:
            position (int): スライダーの位置
        """
        self.view.frame_label.setText(f"Frame: {position} / {self.video_model.num_total_frames}")
        self._update_views(call_frame= position)
    
    def _on_slider_released(self):
        """Sliderドラッグ解放時の処理
        """
        position = self.view.slider.value()
        self._update_views(call_frame= position)
    
    def _on_edit_mode_toggled(self, checked):
        """編集モードボタンの処理

        Args:
            checked (_type_): ボタンの状態
        """
        self.view.video_view.set_edit_mode(checked)
        if checked:
            print("Edit Mode: Valid")
        else:
            print("Edit Mode: Invalid")     
    
    def _on_new_box_created(self, rect_qt: QRectF):
        current_frame = self.video_model.current_frame

        # 1. 新しいIDの入力
        max_tracker_id = self.data_model.get_dataframe_maxid()
        new_id_str, flag = QInputDialog.getText(
            self.view,
            "Add New ID",
            "Please enter the tracker_id to add:",
            text=str(max_tracker_id +1)
        )
        ## 例外処理の確認
        if not flag or not new_id_str:
            return
        try:
            new_id = int(new_id_str)
        except ValueError:
            return

        # 2. 座標変換
        imgsize = (self.video_model.w, self.video_model.h)
        if (imgsize[0] == 0) or (imgsize[1] == 0): return
        qt_box = {'x': rect_qt.x(), 'y': rect_qt.y(), 'w': rect_qt.width(), 'h': rect_qt.height() }
        yolo_box = self._get_convertbox_qt2yolo(qt_box, imgsize[0], imgsize[1])

        # 3. Undo用の処理とBBoxの追加
        self._push_undostack()
        self.data_model.add_bbox(current_frame+1, new_id, yolo_box[0], yolo_box[1], yolo_box[2], yolo_box[3])
        
        # 4. 画面更新
        self._update_views(call_frame=current_frame)
        self.view.edit_mode_button.setChecked(False)

    def _on_id_selected(self, current_item, previous_item):
        """リストでIDを選択した場合の処理
        - 選択したIDのBBoxをハイライト

        Args:
            current_item (_type_): 現在選択中のIDデータ
            previous_item (_type_): 直前に選択したIDデータ
        """
        if current_item:
            print(f"Selected ID {current_item.text()}")
            try:
                self.highlited_id = int(current_item.text().split(': ')[1]) # "ID: 2"のような描画から2を抽出 
            except (ValueError, IndexError):
                self.highlited_id = None
            
        else:
            self.highlited_id = None
        # 再描画
        self._update_views(call_frame= self.video_model.current_frame, is_update_trackinglist=False)

    def _on_id_double_clicked(self, item):
        """リストでIDをダブルクリックした場合の処理
        - 追跡IDの書き換え

        Args:
            item (_type_): 現在選択中のIDデータ
        """
        print(f"Double Clicked ID {item.text()}")
        # 旧IDの確保
        try:
            old_id = int(item.text().split(': ')[1])
        except (ValueError, IndexError):
            return
        current_frame = self.video_model.current_frame

        # 入力ダイアログの表示
        new_id_str, flag = QInputDialog.getText(
            self.view, 
            "Change of Tracking ID", 
            f"Plese enter the new ID with old ID {old_id} (Frame:{current_frame + 1}):",
            text=str(old_id)
        )
        # 変更内容をDataFrameで更新
        if flag and new_id_str:
            try:
                new_id = int(new_id_str)
                self._push_undostack()
                is_subsequent_update = self.view.apply_subsequent_update_id_checkbox.isChecked()
                if self.data_model.update_id(current_frame+1, old_id, new_id, is_subsequent_update):
                    print(f"Successful ID update: {old_id} -> {new_id} (Frame {current_frame + 1})")
                    self.highlited_id = new_id
                    self._update_views(call_frame=current_frame)
                else:
                    self.undo_stack.pop()
                    self._check_undo_stack_state()
                    print(f"Failed ID update: {old_id} (Frame {current_frame})")
            except ValueError:
                print("Invalid input ! Plese enter an integer.")

    def _on_delete_id(self):
        """特定の追跡IDのデータを除去する処理
        """
        if self.highlited_id is None:
            print("Not selected the ID to be deleted.")
            return
        
        target_id = self.highlited_id
        current_frame = self.video_model.current_frame
        is_subsequent_update = self.view.apply_subsequent_update_id_checkbox.isChecked()

        # 確認用メッセージの表示
        confirm_text =f"<b>Delete tracking ID：{target_id}'s data { 'subsequent to' if is_subsequent_update else 'for' } this frame ? <b>"
        reply = QMessageBox.question(
            self.view,
            f"Confirm to Delete ID {target_id} (Frame: {current_frame})",
            f"{confirm_text}\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            # 確認画面でNoが選ばれた場合は何もしない
            return
        
        self._push_undostack()
        if self.data_model.delete_id(current_frame+1, target_id, is_subsequent_update):
            print(f"Successful ID deleted: {target_id} (Frame {current_frame + 1})")
            self.highlited_id = None
            self._update_views(call_frame=current_frame)
        else:
            self.undo_stack.pop()
            self._check_undo_stack_state()
            print(f"Failed to delete ID: {target_id} (Frame {current_frame})")
            QMessageBox.warning(self.view, "Delete Error!", "Failed to delete ID.")  

    def _check_undo_stack_state(self):
        """self.undo_stackが空でない場合にUndoボタンを有効化
        """
        self.view.undo_action.setEnabled(bool(self.undo_stack))
    
    def _push_undostack(self):
        """Undo Stackへのスナップショット(データフレームのコピー)のプッシュ処理
        """
        try:
            df_snapshot = self.data_model.get_dataframe_copy()
            log_snapshot = self.data_model.get_log_copy()
            self.undo_stack.append((df_snapshot, log_snapshot))
            self._check_undo_stack_state()

            # スタックがたまりすぎた場合にLast In を除去
            if len(self.undo_stack) > self.max_undo_stack:
                self.undo_stack.pop(0)

        except Exception as e:
            print(f"Failed to Push to the Undo Stack: {e}")

    def _on_undo(self):
        """Undo 処理
        """
        if not self.undo_stack:
            print("[WARNING] Undo Stack is Empty.")
            return
        
        # undo処理
        (df_last_state, log_last_state) = self.undo_stack.pop()
        self.data_model.restore_dataframe(df_last_state)
        self.data_model.restore_log(log_last_state)
        self._check_undo_stack_state() # undo stackが空かの判定

        # 画面の再描画
        self.highlited_id = None
        self._update_views(call_frame=self.video_model.current_frame)

    def _get_convertbox_yolo2qt(self, yolo_box, img_width: int, img_height: int) -> tuple:
        """YOLOフォーマットのBBoxデータをQtの座標に変換

        Args:
            yolo_box (dict): YOLOフォーマットのbbox辞書データ
            img_width (int): 画像の横幅
            img_height (int): 画像の縦幅

        Returns:
            tuple(int(4)): (x_left, y_top, width, height)
        """
        x_left = int((yolo_box['x'] - (yolo_box['w']/2)) * img_width)
        y_top = int((yolo_box['y'] - (yolo_box['h']/2)) * img_height)
        width = int(yolo_box['w'] * img_width)
        height = int(yolo_box['h'] * img_height)

        return (x_left, y_top, width, height)

    def _get_convertbox_qt2yolo(self, qt_box, img_width: int, img_height: int) -> tuple:
        """Qtの座標のBBoxデータをYOLOフォーマットの座標に変換

        Args:
            qt_box (dict): Qt座標のbbox辞書データ
            img_width (int): 画像の横幅
            img_height (int): 画像の縦幅

        Returns:
            tuple(float(4)): (x, y, width, height)
        """
        x = float((qt_box['x'] + qt_box['w'] / 2) / img_width)
        y = float((qt_box['y'] + qt_box['h'] / 2) / img_height)
        width = float(qt_box['w'] / img_width)
        height = float(qt_box['h'] / img_height)

        return (x, y, width, height)



    def _update_views(self, call_frame: int, is_update_trackinglist=True):
        """動画エリアの更新

        Args:
            call_frame (int): 描画するフレーム番号
            is_update_trackinglist (bool): 追跡IDのリストを更新するかの可否(T/F). Default value is True.
        """
        if not self.video_model or not self.data_model:
            # 各インスタンスが存在しない場合は何もしない
            return
        
        # 1. 映像データからフレーム画像を取得
        self.video_model.set_current_frame(call_frame)
        frame_image = self.video_model.get_frame_image()
        if frame_image is None:
            # フレーム画像が取得できない場合はreturn
            return
        bbox_records = self.data_model.get_bbox_records(call_frame + 1) # YOLOはフレーム番号が1から始まる
    

        # 2. View内容の更新
        # 2-1. Sliderやフレームラベル関連
        num_total_frames = self.video_model.num_total_frames
        current_timestep = (call_frame) // self.frame_step
        total_timestep = num_total_frames // self.frame_step

        self.view.frame_label.setText(f"Frame: {call_frame + 1} / {num_total_frames}")
        self.view.timestep_label.setText(f"Timestep: {current_timestep+1} / {total_timestep}")
        ## スライダーからの更新を一時ストップ(更新ループ防止)
        self.view.slider.blockSignals(True)
        self.view.slider.setValue(call_frame)
        self.view.slider.blockSignals(False)
        # 2-2. 追跡IDリスト 
        if is_update_trackinglist:
            self.view.tracking_list.clear()
            sorted_id_list = list(sorted([int(box['tracker_id']) for box in bbox_records]))
            ids = [f"ID: {id}" for id in sorted_id_list]
            self.view.tracking_list.addItems(ids)
        
        # 2-3. 動画表示エリア
        self.view.video_scene.clear()
        ## 画像の更新処理
        frame_pixmap = QPixmap.fromImage(frame_image)
        if self.scene_pixmap_item is None:
            self.scene_pixmap_item = self.view.video_scene.addPixmap(frame_pixmap)
            self.view.video_scene.setSceneRect(frame_pixmap.rect().toRectF())
            self.view.video_view.fit_in_view() # viewへのfit
        else:
            self.scene_pixmap_item = self.view.video_scene.addPixmap(frame_pixmap)

        ## IDラベル用のフォント・背景設定
        ### フォント
        text_font = QFont()
        text_font.setPointSize(10) # フォントサイズ
        text_font.setBold(True) # 太字
        ### 背景
        bg_brush = QBrush(QColor(0,0,0,170)) # 透明度70%の黒

        ## BBoxの描画
        for box in bbox_records:
            x, y, w, h = self._get_convertbox_yolo2qt(box, self.video_model.w, self.video_model.h)
            # ハイライト状態での色設定
            is_highlited = (box["tracker_id"] == self.highlited_id)
            box_color = Qt.GlobalColor.yellow if is_highlited else Qt.GlobalColor.green
            text_color = Qt.GlobalColor.yellow if is_highlited else Qt.GlobalColor.white 
            
            self.view.video_scene.addRect(x,y,w,h, pen=box_color) # BBox追加
            text = self.view.video_scene.addText(f"ID: {box['tracker_id']}", text_font) # ラベルIDの追加
            text.setDefaultTextColor(text_color)
            text.setPos(x-5, y-20) # 矩形の少し上側にIDラベルを描画


        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_view = MainWindow()
    video_model = VideoModel()
    data_model = DataModel()

    controller = AppController(main_view, video_model, data_model)
    main_view.show()
    sys.exit(app.exec())
    print("Fin.")