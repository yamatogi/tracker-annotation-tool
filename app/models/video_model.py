# Model Module
#### IMPORT ####
import cv2
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QObject

################
class VideoModel(QObject):
    def __init__(self):
        """オブジェクトのコンストラクタ
        """
        super().__init__()
        self.capture = None
        self.num_total_frames = 0
        self.fps = 0
        self.w = 0
        self.h = 0
        self.current_frame = -1
    
    def load(self, moviepath: str) -> bool:
        """映像ファイルの読み込み

        Args:
            moviepath (str): 映像ファイルのパス

        Returns:
            bool: 映像ファイルの読み込み結果の可否(T/F)
        """
        if self.capture:
            # 既にcaptureが存在する場合は解放
            self.capture.release()

        self.capture = cv2.VideoCapture(moviepath)
        if not self.capture.isOpened():
            # 映像ファイルが読み込めない場合はFalseを返す
            print(f"[ERROR!] Cannot Opened {moviepath}.")
            self.capture = None
            return False
        
        self.num_total_frames = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = int(self.capture.get(cv2.CAP_PROP_FPS))
        self.w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.current_frame = 0

        print(f"Success of Video Loading: {moviepath}")
        print(f"Number of All Frame: {self.num_total_frames}, FPS: {self.fps:.2f}")
        return True

    def set_current_frame(self, set_frame: int):
        """現在フレームのセット

        Args:
            set_frame (int): セットしたいフレーム番号
        """
        if 0 <= set_frame < self.num_total_frames:
            self.current_frame = set_frame
        else:
            print(f"(WARNING) Invalid Frame Number {set_frame}")
    
    def get_frame_image(self) -> QImage | None:
        """self.current_frameのフレーム画像を読み込んでQImage型で返す．

        Returns:
            QImage | None: self.current_frameのフレーム画像データ(読み込めない場合はNone)
        """
        if not self.capture:
            return None
        
        # フレームの読み込み
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        ret, image = self.capture.read()
        if not ret:
            print(f"[ERROR!] Capture Error. (Frame: {self.current_frame})")
            return None
        
        # 読み込んだフレーム画像をQImageにConvert
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888) 

        return q_image.copy()

    def release(self):
        """captureデータの解放と初期値の代入
        """
        if self.capture:
            self.capture.release()
            self.capture = None
            self.num_total_frames = 0
            self.fps = 0
            self.w = 0
            self.h = 0
            self.current_frame = -1            
            print("Release Capture.")
    
    def __del__(self):
        """オブジェクトのデストラクタ
        """
        self.release()

if __name__ == '__main__':
    movie = VideoModel()
    print("Fin.")