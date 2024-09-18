from PyQt6.QtCore import QTimer

class AutoSave:
    def __init__(self, model, interval=300000):  # Default: salva ogni 5 minuti
        self.model = model
        self.timer = QTimer()
        self.timer.timeout.connect(self.save)
        self.timer.start(interval)

    def save(self):
        try:
            self.model.session.commit()
            print("Salvataggio automatico completato")
        except Exception as e:
            print(f"Errore durante il salvataggio automatico: {str(e)}")
