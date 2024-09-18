import shutil
import os
from datetime import datetime
import schedule
import time
import threading
import logging
from .custom_exceptions import DatabaseError

class DatabaseBackup:
    def __init__(self, db_path, backup_dir):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.scheduler = schedule.Scheduler()
        self.scheduler_thread = None
        self.logger = logging.getLogger(__name__)

        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def backup(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"tournament_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"Backup creato: {backup_path}")

            # Rimuovi i backup più vecchi se ce ne sono più di 5
            self.cleanup_old_backups()
        except Exception as e:
            self.logger.error(f"Errore durante il backup: {str(e)}")
            raise DatabaseError(f"Impossibile creare il backup: {str(e)}")

    def cleanup_old_backups(self):
        backups = sorted([f for f in os.listdir(self.backup_dir) if f.startswith("tournament_backup_")], reverse=True)
        for old_backup in backups[5:]:  # Mantieni solo i 5 backup più recenti
            os.remove(os.path.join(self.backup_dir, old_backup))
            self.logger.info(f"Backup vecchio rimosso: {old_backup}")

    def start_scheduled_backup(self, interval_hours=24):
        self.scheduler.every(interval_hours).hours.do(self.backup)
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()
        self.logger.info(f"Backup programmato ogni {interval_hours} ore")

    def run_scheduler(self):
        while True:
            self.scheduler.run_pending()
            time.sleep(1)

    def stop_scheduled_backup(self):
        if self.scheduler_thread:
            self.scheduler.clear()
            self.scheduler_thread.join()
            self.logger.info("Backup programmato fermato")

    def restore_from_backup(self, backup_file):
        try:
            backup_path = os.path.join(self.backup_dir, backup_file)
            if not os.path.exists(backup_path):
                raise DatabaseError(f"Il file di backup {backup_file} non esiste")
            
            shutil.copy2(backup_path, self.db_path)
            self.logger.info(f"Database ripristinato dal backup: {backup_file}")
        except Exception as e:
            self.logger.error(f"Errore durante il ripristino del backup: {str(e)}")
            raise DatabaseError(f"Impossibile ripristinare dal backup: {str(e)}")

    def list_backups(self):
        return sorted([f for f in os.listdir(self.backup_dir) if f.startswith("tournament_backup_")], reverse=True)