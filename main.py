# Main Module
#### IMPORT ####
import sys
from PyQt6.QtWidgets import QApplication

# Self-made Module
from app.views.main_window import MainWindow
from app.controller.app_controller import AppController
from app.models.video_model import VideoModel
from app.models.data_model import DataModel
################

def main():
    app = QApplication(sys.argv)
    # 各インスタンスの呼び出し
    main_view = MainWindow()
    video_model = VideoModel()
    data_model = DataModel()
    contoroller = AppController(main_view, video_model, data_model)

    # アプリの実行
    main_view.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
    print("Fin.")