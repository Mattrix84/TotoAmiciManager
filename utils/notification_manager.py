from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QSystemTrayIcon
from PyQt6.QtGui import QIcon
import logging

class NotificationManager(QObject):
    notification = pyqtSignal(str, str)  # (titolo, messaggio)

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.tray_icon = None

    def setup_tray_icon(self, parent):
        self.tray_icon = QSystemTrayIcon(QIcon("icons/app_icon.png"), parent)
        self.tray_icon.show()

    def notify(self, title, message, icon=QSystemTrayIcon.MessageIcon.Information):
        self.logger.info(f"Notifica: {title} - {message}")
        self.notification.emit(title, message)
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, icon)

    def notify_round_start(self, round_number):
        self.notify("Inizio Giornata", f"La giornata {round_number} sta per iniziare.")

    def notify_round_end(self, round_number):
        self.notify("Fine Giornata", f"La giornata {round_number} è terminata.")

    def notify_prize_assignment(self, prize_type, winner):
        self.notify("Premio Assegnato", f"{prize_type} assegnato a {winner}.")

    def notify_tournament_start(self):
        self.notify("Inizio Torneo", "Il torneo è iniziato.")

    def notify_tournament_end(self):
        self.notify("Fine Torneo", "Il torneo è terminato.")

    def notify_no_winners(self, prize_type):
        self.notify("Nessun Vincitore", f"Nessun vincitore per il {prize_type} questa settimana.")

    def notify_predictions_due(self, hours_left):
        self.notify("Pronostici in Scadenza", f"Mancano {hours_left} ore alla chiusura dei pronostici.")

    def notify_results_entry_open(self):
        self.notify("Inserimento Risultati", "È ora possibile inserire i risultati delle partite.")

    def notify_error(self, error_message):
        self.notify("Errore", error_message, QSystemTrayIcon.MessageIcon.Warning)

    def notify_backup_created(self, backup_path):
        self.notify("Backup Creato", f"Un nuovo backup è stato creato in {backup_path}")

    def notify_export_completed(self, export_type, file_path):
        self.notify("Esportazione Completata", f"L'esportazione di {export_type} è stata completata. File salvato in {file_path}")