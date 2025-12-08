# Model Module
#### IMPORT ####
import pandas as pd
from PyQt6.QtCore import QObject
from datetime import datetime
################
class DataModel(QObject):
    def __init__(self):
        """オブジェクトのコンストラクタ
        """
        super().__init__()
        self.df_track = pd.DataFrame()
        self.columns = ['frame', 'tracker_id', 'x', 'y', 'w', 'h']
        self.log_data = []
        self.log_columns = ['datetime', 'action', 'scope', 'frame', 'old_id', 'new_id']
    
    def _add_log(self, action:str, scope:str, frame:int, old_id:int, new_id=None):
        """ログデータへの追加

        Args:
            action (str): 作業種類
            scope (str): 処理範囲
            frame (int): 指定フレーム
            old_id (int): 作業対象のID番号
            new_id (int, optional): ID変更時の変更先のID番号. Defaults to None.
        """
        timestamp = datetime.now().isoformat()
        log_entry = {
            'datetime': timestamp,
            'action': action,
            'scope':scope,
            'frame':frame,
            'old_id':old_id,
            'new_id':new_id
        }
        self.log_data.append(log_entry)
        print(f"(Log: {log_entry}")

    def add_bbox(self, frame: int, tracker_id: int, x: float, y: float, w: float, h:float):
        """データフレームに矩形データ(YOLOフォーマット)を追加

        Args:
            frame (int): フレーム番号
            tracker_id (int): 追跡番号
            x (float): yolo_x
            y (float): yolo_y
            w (float): yolo_width
            h (float): yolo_height
        """
        df = self.df_track.copy()
        new_row = {'frame':frame, 'tracker_id':tracker_id, 'x':x, 'y':y, 'w':w, 'h':h}
        self._add_log('ADD_BOX', 'SINGLE_FRAME', frame, None, tracker_id)

        df_add =  pd.DataFrame([new_row])
        df_update = pd.concat([df, df_add], ignore_index=True)

        self.df_track = df_update.copy()
        print(f"Add BBox: ID {tracker_id} (Frame {frame})")


    def save_logdata(self, export_csvpath: str) -> bool:
        """ログデータの保存

        Args:
            export_csvpath (str): ログデータの出力先のパス

        Returns:
            bool: ログデータの保存成功可否
        """
        if not self.log_data:
            print("[WARNING] Don't have any Log Data.")
            return False
        
        try:
            df_log = pd.DataFrame(self.log_data, columns=self.log_columns)
            df_log.to_csv(export_csvpath, index=False)
            print(f"Success of Log Data Saved: {export_csvpath}")
            return True
        
        except Exception as e:
            print(f"Filed to save log data: {e}")
            return False
        
    def get_log_copy(self) -> list:
        """ログデータのコピーを取得

        Returns:
            list: slef.log_dataのコピー
        """
        return self.log_data.copy()
    
    def restore_log(self, log_list: list):
        """self.log_dataの書き換え(Undo処理で実施)

        Args:
            log_list (list): self.log_dataに置き換えるログリストデータ
        """
        self.log_data = log_list.copy()

    def load(self, datapath: str) -> bool:
        """追跡データの読み込み

        Args:
            datapath (str): YOLOフォーマットの追跡データ(CSV)パス

        Returns:
            bool: 追跡データファイルの読み込み結果の可否(T/F)
        """
        try:
            buffer_track = pd.read_csv(datapath)
            self.df_track = buffer_track[self.columns].astype({'frame': int, 'tracker_id': int, 'x': float, 'y': float, 'w': float, 'h': float})
            self.df_track.sort_values(by='frame', inplace=True)
            print(f"Success of Data Loading: {datapath} ({len(self.df_track)} rows)")
            return True

        except FileNotFoundError:
            print(f"[ERROR!] File Not Found. (File:{datapath})")
            return False
        except Exception as e:
            print(f"[ERROR!] Loading Error: {e}")
            self.df_track = pd.DataFrame()
            return False
    
    def get_bbox_records(self, call_frame: int) -> list[dict]:
        """指定フレームにおけるBBoxを辞書型リストで取得(カラムはデフォルトのもので実装)

        Args:
            call_frame (int): 指定フレーム番号

        Returns:
            list[dict]: 指定フレームにおけるBBoxの辞書型リスト
        """
        export_records = []
        if self.df_track.empty:
            # データフレームが空の場合は空のリストを返す．
            return export_records
        
        try:
            bbox_data = self.df_track[self.df_track['frame'] == call_frame]
            for record in bbox_data.to_dict(orient="records"):
                export_records.append({
                    'tracker_id': int(record['tracker_id']),
                    'x': float(record['x']),
                    'y': float(record['y']),
                    'w': float(record['w']),
                    'h': float(record['h']),
                })

        except KeyError:
            pass

        except Exception as e:
            print(f"[ERROR!] Get BBox Records Error: {e}")

        return export_records
    
    def save(self, exportpath: str, step=1) -> bool:
        """修正後の追跡データの保存

        Args:
            exportpath (str): 追跡データ(CSV)の保存先パス
            step (int, optional): 保存する際のフレーム間隔(開始は1フレーム目から)

        Returns:
            bool: 追跡データ保存の成功可否(T/F)
        """
        if self.df_track.empty:
            # データフレームが空の場合はFalseを返す．
            print(f"(WARNING) Don't have any Tracking Data.")
            return False 
        
        try:
            df_save = self.df_track[(self.df_track['frame'] % step) == 1].copy()
            df_save[self.columns].to_csv(exportpath, index=False)
            print(f"Success of Save Data: {exportpath}")
            return True
        except Exception as e:
            print(f"[ERROR!] Data Saving Error: {e}")
            return False

    def update_id(self, frame: int, old_id: int, new_id: int, is_subsequent_update=False) -> bool:
        """追跡IDを変更する処理

        Args:
            frame (int): フレーム
            old_id (int): 旧追跡ID番号
            new_id (int): 更新するID番号
            is_subsequent_update (bool, optional): 後続フレームの追跡IDも更新するかの可否(T/F). Defaults to False.

        Returns:
            bool: 更新処理の成功可否(T/F)
        """
        if self.df_track.empty: return False
        log_scope = 'FUTURE_FRAMES' if is_subsequent_update else 'SINGLE_FRAME'
        
        try:
            if is_subsequent_update:
                target_indeces = self.df_track[(self.df_track['frame'] >= frame) & (self.df_track['tracker_id'] == old_id)].index
            else:
                target_indeces = self.df_track[(self.df_track['frame'] == frame) & (self.df_track['tracker_id'] == old_id)].index
            
            if target_indeces.empty:
                print(f"[Update Error!] Not Found ID {old_id} without Frame {frame}.")
                return False
            
            self.df_track.loc[target_indeces, 'tracker_id'] = new_id
            self._add_log('UPDATE_ID', log_scope, frame, old_id, new_id)
            return True
        
        except Exception as e:
            print(f"DataModel.update_id error: {e}")
            return False

    def delete_id(self, frame: int, track_id: int, is_subsequent_update=False) -> bool:
        """指定したIDのデータを削除

        Args:
            frame (int): 操作を行うフレーム番号
            track_id (int): 削除対象の追跡番号
            is_subsequent_update (bool, optional): 後続フレームの追跡IDも更新するかの可否(T/F). Defaults to False.

        Returns:
            bool: 更新処理の成功可否(T/F)
        """
        if self.df_track.empty: return False
        log_scope = 'FUTURE_FRAMES' if is_subsequent_update else 'SINGLE_FRAME'
        
        try:
            if is_subsequent_update:
                target_indeces = self.df_track[(self.df_track['frame'] >= frame) & (self.df_track['tracker_id'] == track_id)].index
            else:
                target_indeces = self.df_track[(self.df_track['frame'] == frame) & (self.df_track['tracker_id'] == track_id)].index

            if target_indeces.empty:
                print(f"[Update Error!] Not Found ID {track_id} without Frame {frame}.")
                return False

            self.df_track.drop(index=target_indeces, inplace=True)
            self._add_log('DELETE_ID', log_scope, frame, track_id, None)
            print(f"Delete ID: {track_id} (Frame: {frame}, {len(target_indeces)} rows)")
            return True

        except Exception as e:
            print(f"DataModel.update_id error: {e}")
            return False

    def get_dataframe_copy(self) -> pd.DataFrame:
        """データフレームのコピーを取得

        Returns:
            pd.DataFrame: slef.df_tarckのコピー
        """
        return self.df_track.copy()
    
    def get_dataframe_maxid(self) -> int:
        """データフレーム内の最大追跡IDを取得

        Returns:
            int: 追跡IDの最大値
        """
        return int(self.df_track['tracker_id'].max())

    def restore_dataframe(self, df: pd.DataFrame):
        """self.df_trackの書き換え(Undo処理で実施)

        Args:
            df (pd.DataFrame): self.df_trackに置き換えるデータフレーム
        """
        self.df_track = df.copy()
        print(f"Undo the Tracking DataFrame.")


if __name__ == '__main__':
    track_data = DataModel()
    if track_data.load("data/track/remove_tent_tracker.csv"):
        track_data.update_id(10, 1, 1234)
    else:
        print("Loading Error!")
    print("Fin.")