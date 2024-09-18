import sys
from PyQt6.QtWidgets import QApplication
from views.main_window import MainWindow
from models.tournament_model import TournamentModel
from viewmodels.main_viewmodel import MainViewModel

def exception_hook(exctype, value, traceback):
    print(f"Un'eccezione non gestita si è verificata: {exctype}, {value}")
    print("Traceback:")
    import traceback as tb
    tb.print_tb(traceback)
    sys.__excepthook__(exctype, value, traceback)
    sys.exit(1)

if __name__ == "__main__":
    sys.excepthook = exception_hook
    app = QApplication(sys.argv)
    model = TournamentModel()
    viewmodel = MainViewModel(model)
    window = MainWindow(viewmodel)
    window.show()
    sys.exit(app.exec())