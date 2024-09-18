from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QDoubleSpinBox,
                             QLineEdit, QListWidget, QMessageBox, QDateEdit, QScrollArea, QFileDialog, QPushButton,
                             QSpinBox, QGroupBox, QStackedWidget, QComboBox, QTableWidget, QGridLayout, QFrame, QWidget, 
                             QTableWidgetItem, QInputDialog, QToolBar, QStatusBar, QSystemTrayIcon, QMenu, QApplication)
from PyQt6.QtGui import QIcon, QAction, QPageLayout
from PyQt6.QtCore import Qt, QDate
from utils.theme_manager import ThemeManager
from models.tournament_model import TournamentState, RoundState

class MainWindow(QMainWindow):
    def __init__(self, viewmodel):
        super().__init__()
        self.viewmodel = viewmodel
        self.init_ui()
        self.connect_signals()
        ThemeManager.set_football_theme(QApplication.instance())
        ThemeManager.set_custom_football_style(self)
        self.update_button_states()

    def init_ui(self):
        self.setWindowTitle("Gestore Torneo Pronostici")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        self.setup_sidebar()
        self.setup_main_area()
        self.setup_toolbar()
        self.setup_statusbar()
        self.setup_system_tray()
        
        self.load_active_tournament()

    def setup_sidebar(self):
        sidebar = QVBoxLayout()
        
        self.new_tournament_btn = QPushButton("Nuovo Torneo")
        self.add_participants_btn = QPushButton("Aggiungi Partecipanti")
        self.manage_round_btn = QPushButton("Gestisci Giornata")
        self.enter_predictions_btn = QPushButton("Inserisci Pronostici")
        self.enter_results_btn = QPushButton("Inserisci Risultati")
        self.view_standings_btn = QPushButton("Visualizza Classifica")
        self.view_statistics_btn = QPushButton("Statistiche Torneo")
        
        sidebar.addWidget(self.new_tournament_btn)
        sidebar.addWidget(self.add_participants_btn)
        sidebar.addWidget(self.manage_round_btn)
        sidebar.addWidget(self.enter_predictions_btn)
        sidebar.addWidget(self.enter_results_btn)
        sidebar.addWidget(self.view_standings_btn)
        sidebar.addWidget(self.view_statistics_btn)

        # Aggiungiamo una linea di separazione
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        sidebar.addWidget(line)

        self.tournament_name_label = QLabel("Nome Torneo: ")
        self.tournament_state_label = QLabel("Stato Torneo: ")
        self.round_number_label = QLabel("Numero Giornata: ")
        self.round_state_label = QLabel("Stato Giornata: ")
    
        sidebar.addWidget(self.tournament_name_label)
        sidebar.addWidget(self.tournament_state_label)
        sidebar.addWidget(self.round_number_label)
        sidebar.addWidget(self.round_state_label)
        
        sidebar.addStretch(1)
        self.main_layout.addLayout(sidebar, 1)

    def setup_main_area(self):
        self.main_area = QStackedWidget()
        self.main_layout.addWidget(self.main_area, 3)

        self.create_tournament_page = self.create_tournament_page()
        self.add_participants_page = self.create_add_participants_page()
        self.manage_round_page = self.create_manage_round_page()
        self.enter_predictions_page = self.create_enter_predictions_page()
        self.enter_results_page = self.create_enter_results_page()
        self.view_standings_page = self.create_view_standings_page()
        self.view_statistics_page = self.create_view_statistics_page()

        self.main_area.addWidget(self.create_tournament_page)
        self.main_area.addWidget(self.add_participants_page)
        self.main_area.addWidget(self.manage_round_page)
        self.main_area.addWidget(self.enter_predictions_page)
        self.main_area.addWidget(self.enter_results_page)
        self.main_area.addWidget(self.view_standings_page)
        self.main_area.addWidget(self.view_statistics_page)

    def setup_toolbar(self):
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        save_action = QAction(QIcon("icons/save.png"), "Salva", self)
        save_action.triggered.connect(self.viewmodel.save_tournament)
        toolbar.addAction(save_action)

        export_action = QAction(QIcon("icons/export.png"), "Esporta Classifica", self)
        export_action.triggered.connect(self.export_standings)
        toolbar.addAction(export_action)

    def setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

    def setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icons/app_icon.png"))
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Mostra")
        quit_action = tray_menu.addAction("Esci")
        
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.close)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def connect_signals(self):
        # Segali relativi al torneo
        self.viewmodel.tournament_created.connect(self.on_tournament_created)
        self.viewmodel.tournament_updated.connect(self.on_tournament_updated)
        self.viewmodel.tournament_state_changed.connect(self.on_tournament_state_changed)
        
        # Segnali relativi ai partecipanti
        self.viewmodel.participants_updated.connect(self.update_participants_list)
        self.viewmodel.remaining_slots_updated.connect(self.update_remaining_slots)
        self.viewmodel.participants_limit_reached.connect(self.on_participants_limit_reached)
        
        # Segnali relativi alla gestione delle giornate
        self.viewmodel.round_date_set.connect(self.disable_date_input)
        self.viewmodel.round_updated.connect(self.on_round_updated)
        self.viewmodel.round_state_changed.connect(self.on_round_state_changed)

        # Segnali relativi alla gestione delle partite
        self.viewmodel.matches_updated.connect(self.update_matches_list)
        
        # Segnali relativi ai pronostici e ai risultati
        self.viewmodel.predictions_updated.connect(self.update_predictions_table)
        self.viewmodel.results_updated.connect(self.update_results_table)

        # Segnali relativi alle statistiche
        self.viewmodel.standings_updated.connect(self.update_standings)
        self.viewmodel.weekly_prize_assigned.connect(self.show_weekly_prize_winners)
        self.viewmodel.final_prizes_assigned.connect(self.show_final_prizes)

        # Segnali relativi agli errori
        self.viewmodel.error_occurred.connect(self.show_error)
        
        # Connessione dei pulsanti
        self.new_tournament_btn.clicked.connect(self.show_create_tournament_page)
        self.add_participants_btn.clicked.connect(self.show_add_participants_page)
        self.set_date_btn.clicked.connect(self.set_round_date)
        self.manage_round_btn.clicked.connect(self.show_manage_round_page)
        self.enter_predictions_btn.clicked.connect(self.show_enter_predictions_page)
        self.enter_results_btn.clicked.connect(self.show_enter_results_page)
        self.view_standings_btn.clicked.connect(self.show_view_standings_page)
        self.view_statistics_btn.clicked.connect(self.show_view_statistics_page)

    def update_button_states(self):
        if not self.viewmodel.active_tournament:
            self.new_tournament_btn.setEnabled(True)
            self.add_participants_btn.setEnabled(False)
            self.manage_round_btn.setEnabled(False)
            self.enter_predictions_btn.setEnabled(False)
            self.enter_results_btn.setEnabled(False)
            self.view_standings_btn.setEnabled(False)
            self.view_statistics_btn.setEnabled(False)
        else:
            tournament_state = self.viewmodel.active_tournament.state
            round_state = self.viewmodel.current_round.state if self.viewmodel.current_round else None

            self.new_tournament_btn.setEnabled(tournament_state == TournamentState.CONCLUDED)
            self.add_participants_btn.setEnabled(tournament_state == TournamentState.ADDING_PARTICIPANTS)
            self.manage_round_btn.setEnabled(tournament_state == TournamentState.IN_PROGRESS and 
                                             round_state in [RoundState.CREATING_FIRST_ROUND, RoundState.CREATING_NEXT_ROUND, RoundState.SELECTING_DATE])
            self.enter_predictions_btn.setEnabled(round_state == RoundState.ENTERING_PREDICTIONS)
            self.enter_results_btn.setEnabled(round_state == RoundState.ENTERING_RESULTS)
            self.view_standings_btn.setEnabled(tournament_state in [TournamentState.IN_PROGRESS, TournamentState.CONCLUDED])
            self.view_statistics_btn.setEnabled(tournament_state in [TournamentState.IN_PROGRESS, TournamentState.CONCLUDED])
    
    def create_tournament_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.tournament_name_input = QLineEdit()
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())
        self.start_date_input.setMinimumDate(QDate.currentDate())
        self.num_rounds_input = QSpinBox()
        self.num_rounds_input.setRange(36, 42)
        self.num_rounds_input.setValue(38)
        self.num_matches_input = QSpinBox()
        self.num_matches_input.setRange(13, 16)
        self.num_matches_input.setValue(14)
        self.num_participants_input = QSpinBox()
        self.num_participants_input.setRange(20, 200)
        self.num_participants_input.setValue(100)
        self.min_correct_predictions_input = QSpinBox()
        self.min_correct_predictions_input.setRange(7, 12)
        self.min_correct_predictions_input.setValue(9)
        self.participant_fee_input = QSpinBox()
        self.participant_fee_input.setRange(1, 100)
        self.participant_fee_input.setValue(10)
        self.participant_fee_input.setPrefix("€ ")
        self.weekly_prize_percentage_input = QSpinBox()
        self.weekly_prize_percentage_input.setRange(5, 50)
        self.weekly_prize_percentage_input.setValue(20)
        self.weekly_prize_percentage_input.setSuffix("%")
        self.weekly_budget_label = QLabel("Budget Settimanale: 0Euro", self)
        self.weekly_prize_amount_label = QLabel("Premio Settimanale: 0Euro", self)                                        
        self.final_prizes_percentage_input = QSpinBox()
        self.final_prizes_percentage_input.setRange(50, 100)
        self.final_prizes_percentage_input.setValue(80)
        self.final_prizes_percentage_input.setSuffix("%")
        self.final_prizes_budget_label = QLabel("Budget Premi Finali: 0Euro", self)
        self.final_prizes_amount_label = QLabel("Ammontare Totale Premi Finali: 0Euro", self)

        layout.addWidget(QLabel("Nome Torneo:"))
        layout.addWidget(self.tournament_name_input)
        layout.addWidget(QLabel("Data di Inizio Torneo:"))
        layout.addWidget(self.start_date_input)
        layout.addWidget(QLabel("Numero Giornate:"))
        layout.addWidget(self.num_rounds_input)
        layout.addWidget(QLabel("Numero Partite per Giornata:"))
        layout.addWidget(self.num_matches_input)
        layout.addWidget(QLabel("Numero Partecipanti:"))
        layout.addWidget(self.num_participants_input)
        layout.addWidget(QLabel("Numero minimo pronostici esatti per premio settimanale:"))
        layout.addWidget(self.min_correct_predictions_input)
        layout.addWidget(QLabel("Quota Partecipante:"))
        layout.addWidget(self.participant_fee_input)
        layout.addWidget(self.weekly_budget_label)
        layout.addWidget(QLabel("Percentuale Premio Settimanale:"))
        layout.addWidget(self.weekly_prize_percentage_input)
        layout.addWidget(self.weekly_prize_amount_label)
        layout.addWidget(QLabel("Percentuale Premi Finali:"))
        layout.addWidget(self.final_prizes_percentage_input)
        layout.addWidget(self.final_prizes_budget_label)
        layout.addWidget(self.final_prizes_amount_label)

        create_btn = QPushButton("Crea Torneo")
        create_btn.clicked.connect(self.create_tournament)
        layout.addWidget(create_btn)
        self.tournament_name_input.returnPressed.connect(self.create_tournament)

        self.num_rounds_input.valueChanged.connect(self.update_prize_calculation)
        self.num_participants_input.valueChanged.connect(self.update_prize_calculation)
        self.participant_fee_input.valueChanged.connect(self.update_prize_calculation)
        self.weekly_prize_percentage_input.valueChanged.connect(self.update_prize_calculation)
        self.final_prizes_percentage_input.valueChanged.connect(self.update_prize_calculation)
        
        self.update_prize_calculation()
        return page

    def update_prize_calculation(self):
        participant_fee = self.participant_fee_input.value()
        num_participants = self.num_participants_input.value()
        weekly_prize_percentage = self.weekly_prize_percentage_input.value()
        final_prizes_percentage = self.final_prizes_percentage_input.value()
        num_rounds = self.num_rounds_input.value()

        weekly_budget = participant_fee * num_participants
        self.weekly_budget_label.setText(f"Budget Settimanale: {weekly_budget}Euro")
        
        weekly_prize_amount = (weekly_budget * weekly_prize_percentage) / 100
        self.weekly_prize_amount_label.setText(f"Premio Settimanale: {weekly_prize_amount}Euro")

        final_prizes_budget = (weekly_budget - weekly_prize_amount) * num_rounds
        self.final_prizes_budget_label.setText(f"Budget Premi Finali: {final_prizes_budget}Euro")

        final_prizes_amount = (final_prizes_budget * final_prizes_percentage) / 100
        self.final_prizes_amount_label.setText(f"Ammontare Totale per i Premi Finali: {final_prizes_amount}Euro")

    def create_add_participants_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)  # Definiamo il layout principale qui
        
        # Input per il nome del partecipante
        self.participant_name_input = QLineEdit()
        self.participant_name_input.setPlaceholderText("Nome Partecipante")
        self.participant_name_input.returnPressed.connect(self.add_participant)

        add_btn = QPushButton("Aggiungi Partecipante")
        add_btn.clicked.connect(self.add_participant)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.participant_name_input)
        input_layout.addWidget(add_btn)

        layout.addLayout(input_layout)

        self.remaining_slots_label = QLabel()
        layout.addWidget(self.remaining_slots_label)

        # Griglia scrollable per i partecipanti
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.participants_grid = QGridLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        return page

    def create_final_prizes_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.final_prizes_table = QTableWidget()
        self.final_prizes_table.setColumnCount(3)
        self.final_prizes_table.setHorizontalHeaderLabels(["Posizione", "Percentuale", "Importo (€)"])

        layout.addWidget(self.final_prizes_table)

        save_btn = QPushButton("Salva Distribuzione")
        save_btn.clicked.connect(self.save_final_prizes_distribution)
        layout.addWidget(save_btn)

        return page

    def update_final_prizes_table(self):
        distribution = self.viewmodel.get_final_prizes_distribution()
        self.final_prizes_table.setRowCount(self.viewmodel.active_tournament.num_participants)

        for row in range(self.viewmodel.active_tournament.num_participants):
            position = row + 1
            self.final_prizes_table.setItem(row, 0, QTableWidgetItem(str(position)))

            percentage_spinner = QDoubleSpinBox()
            percentage_spinner.setRange(0, 50)
            percentage_spinner.setSingleStep(0.5)
            percentage_spinner.setValue(distribution.get(str(position), 0))
            percentage_spinner.valueChanged.connect(lambda value, r=row: self.update_prize_amount(r, value))
            self.final_prizes_table.setCellWidget(row, 1, percentage_spinner)

            amount_label = QLabel()
            self.final_prizes_table.setCellWidget(row, 2, amount_label)

            self.update_prize_amount(row, percentage_spinner.value())
    
    def update_prize_amount(self, row, percentage):
        amount = self.viewmodel.calculate_final_prizes_target(percentage)
        self.final_prizes_table.cellWidget(row, 2).setText(f"{amount:.2f}€")

    def save_final_prizes_distribution(self):
        distribution = {}
        for row in range(self.final_prizes_table.rowCount()):
            position = int(self.final_prizes_table.item(row, 0).text())
            percentage = self.final_prizes_table.cellWidget(row, 1).value()
            if percentage > 0:
                distribution[str(position)] = percentage
    
        self.viewmodel.update_final_prizes_distribution(distribution)
    
    def create_manage_round_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.round_date_input = QDateEdit()
        self.round_date_input.setCalendarPopup(True)
        self.round_date_input.setDate(self.viewmodel.get_today_or_future_date())
        self.round_date_input.setMinimumDate(self.viewmodel.get_today_or_future_date())
        
        self.set_date_btn = QPushButton("Imposta Data")
        self.set_date_btn.clicked.connect(self.set_round_date)

        self.matches_list = QListWidget()

        self.home_team_input = QLineEdit()
        self.away_team_input = QLineEdit()
        add_match_btn = QPushButton("Aggiungi Partita")
        add_match_btn.clicked.connect(self.add_match)
        self.away_team_input.returnPressed.connect(self.add_match)

        layout.addWidget(QLabel("Data Giornata:"))
        layout.addWidget(self.round_date_input)
        layout.addWidget(self.set_date_btn)
        layout.addWidget(QLabel("Partite:"))
        layout.addWidget(self.matches_list)
        layout.addWidget(QLabel("Squadra Casa:"))
        layout.addWidget(self.home_team_input)
        layout.addWidget(QLabel("Squadra Trasferta:"))
        layout.addWidget(self.away_team_input)
        layout.addWidget(add_match_btn)
        
        if self.round_date_input.isEnabled():
            self.set_date_btn.setFocus()
        else:
            self.away_team_input.setFocus()
        return page

    def create_enter_predictions_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.participant_combo = QComboBox()
        self.predictions_table = QTableWidget()
        self.predictions_table.setColumnCount(4)
        self.predictions_table.setHorizontalHeaderLabels(["Partita", "Casa", "Trasferta", "Pronostico"])

        save_btn = QPushButton("Salva Pronostici")
        save_btn.clicked.connect(self.save_predictions)

        layout.addWidget(QLabel("Seleziona Partecipante:"))
        layout.addWidget(self.participant_combo)
        layout.addWidget(self.predictions_table)
        layout.addWidget(save_btn)

        return page

    def create_enter_results_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Partita", "Casa", "Trasferta", "Risultato"])

        save_btn = QPushButton("Salva Risultati")
        save_btn.clicked.connect(self.save_results)

        layout.addWidget(self.results_table)
        layout.addWidget(save_btn)

        return page

    def create_view_standings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.standings_table = QTableWidget()
        self.standings_table.setColumnCount(3)
        self.standings_table.setHorizontalHeaderLabels(["Posizione", "Partecipante", "Punteggio"])

        layout.addWidget(self.standings_table)

        return page

    def create_view_statistics_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.statistics_label = QLabel()
        layout.addWidget(self.statistics_label)

        return page

    def show_create_tournament_page(self):
        self.main_area.setCurrentWidget(self.create_tournament_page)

    def show_add_participants_page(self):
        self.main_area.setCurrentWidget(self.add_participants_page)
        if self.viewmodel.active_tournament:
            participants = self.viewmodel.model.get_participants(self.viewmodel.active_tournament.id)
            self.update_participants_list(participants)

    def show_manage_round_page(self):
        self.main_area.setCurrentWidget(self.manage_round_page)

    def show_enter_predictions_page(self):
        self.main_area.setCurrentWidget(self.enter_predictions_page)

    def show_enter_results_page(self):
        self.main_area.setCurrentWidget(self.enter_results_page)

    def show_view_standings_page(self):
        self.main_area.setCurrentWidget(self.view_standings_page)

    def show_view_statistics_page(self):
        self.main_area.setCurrentWidget(self.view_statistics_page)

    def create_tournament(self):
        try:
            name = self.tournament_name_input.text()
            start_date = self.start_date_input.date().toPyDate()
            num_rounds = self.num_rounds_input.value()
            num_matches = self.num_matches_input.value()
            num_participants = self.num_participants_input.value()
            min_correct = self.min_correct_predictions_input.value()
            participant_fee = self.participant_fee_input.value()
            weekly_prize_percentage = self.weekly_prize_percentage_input.value()
            final_prizes_percentage = self.final_prizes_percentage_input.value()

            self.viewmodel.create_tournament(name, start_date, num_rounds, num_matches, num_participants, 
                                            min_correct, participant_fee, weekly_prize_percentage, 
                                            final_prizes_percentage)
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Si è verificato un errore durante la creazione del torneo: {str(e)}")
            print(f"Errore dettagliato: {e}")  # Per il debug

    def add_participant(self):
        name = self.participant_name_input.text()
        if name:
            self.viewmodel.add_participant(name)
            self.participant_name_input.clear()
            self.participant_name_input.setFocus()

    def set_round_date(self):
        selected_date = self.round_date_input.date().toPyDate()
        self.viewmodel.set_round_date(selected_date)
    
    def disable_date_input(self, round_id):
        if self.viewmodel.current_round and self.viewmodel.current_round.id == round_id:
            self.round_date_input.setEnabled(False)
            self.set_date_btn.setEnabled(False)

    def add_match(self):
        home_team = self.home_team_input.text()
        away_team = self.away_team_input.text()
        if home_team and away_team:
            self.viewmodel.add_match(home_team, away_team)
            self.home_team_input.clear()
            self.away_team_input.clear()

    def save_predictions(self):
        participant_id = self.participant_combo.currentData()
        for row in range(self.predictions_table.rowCount()):
            match_id = self.predictions_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            prediction = self.predictions_table.cellWidget(row, 3).currentText()
            self.viewmodel.add_prediction(participant_id, match_id, prediction)

    def save_results(self):
        for row in range(self.results_table.rowCount()):
            match_id = self.results_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            result = self.results_table.cellWidget(row, 3).currentText()
            self.viewmodel.enter_match_result(match_id, result)

    def on_tournament_created(self, tournament):
        QMessageBox.information(self, "Successo", f"Il torneo '{tournament.name}' è stato creato con successo!")
        self.update_tournament_info(tournament)
        self.show_appropriate_page(tournament.state)

    def on_tournament_updated(self, tournament):
        self.setWindowTitle(f"Gestore Torneo Pronostici - {tournament.name}")

    def on_tournament_state_changed(self, state):
        print(f"Cambio di stato del torneo: {state}")  # Per il debug
        self.tournament_state_label.setText(f"Stato Torneo: {state.name}")
        self.show_appropriate_page(state)

    def update_participants_list(self, participants):
        # Rimuovi tutti i widget esistenti dalla griglia
        while self.participants_grid.count():
            item = self.participants_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Calcola il numero di colonne in base alla larghezza della finestra
        grid_width = self.participants_grid.parent().width()
        num_columns = max(1, grid_width // 200)  # Assumiamo che ogni elemento sia largo circa 200px

        for index, participant in enumerate(participants):
            row = index // num_columns
            col = index % num_columns

            # Crea un widget per ogni partecipante
            participant_widget = QWidget()
            participant_layout = QHBoxLayout(participant_widget)

            label = QLabel(f"{index + 1}. {participant.name}")
            edit_button = QPushButton()
            edit_button.setIcon(QIcon("path/images/edit_icon.png"))  # Sostituisci con il percorso della tua icona
            edit_button.clicked.connect(lambda checked, p=participant: self.edit_participant(p))

            participant_layout.addWidget(label)
            participant_layout.addWidget(edit_button)

            self.participants_grid.addWidget(participant_widget, row, col)

        self.update_remaining_slots(len(participants))

    def edit_participant(self, participant):
        new_name, ok = QInputDialog.getText(self, "Modifica Partecipante", "Nuovo nome:", text=participant.name)
        if ok and new_name:
            try:
                self.viewmodel.edit_participant(participant.id, new_name)
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Impossibile modificare il partecipante: {str(e)}")

    def update_remaining_slots(self, current_participants):
        remaining = self.viewmodel.active_tournament.num_participants - current_participants
        self.remaining_slots_label.setText(f"Posti rimanenti: {remaining}")
        if remaining == 0:
            self.proceed_to_next_phase()

    def on_participants_limit_reached(self):
        try:
            QMessageBox.information(self, "Limite raggiunto", "Il numero massimo di partecipanti è stato raggiunto.")
            self.viewmodel.start_tournament()
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Si è verificato un errore durante l'avvio del torneo: {str(e)}")
            print(f"Errore dettagliato: {e}")  # Per il debug
    
    def proceed_to_next_phase(self):
        QMessageBox.information(self, "Partecipanti Completi", "Il numero richiesto di partecipanti è stato raggiunto. Passaggio alla fase successiva.")
        self.viewmodel.start_tournament()

    def on_round_updated(self, round):
        self.round_number_label.setText(f"Numero Giornata: {round.round_number}")
        self.round_state_label.setText(f"Stato Giornata: {round.state.name}")
        if round.date:
           self.round_date_input.setDate(round.date)
        else:
            # Impostiamo una data predefinita, ad esempio la prossima domenica
            next_sunday = self.viewmodel.get_next_sunday()
            self.round_date_input.setDate(next_sunday)

    def on_round_state_changed(self, round_number, state):
        self.round_state_label.setText(f"Stato Giornata: {state.name}")
        self.update_button_states()
        self.show_appropriate_round_page(state)

    def update_matches_list(self, matches):
        self.matches_list.clear()
        for match in matches:
            self.matches_list.addItem(f"{match.home_team} vs {match.away_team}")

    def update_predictions_table(self, predictions):
        self.predictions_table.setRowCount(len(predictions))
        for row, prediction in enumerate(predictions):
            self.predictions_table.setItem(row, 0, QTableWidgetItem(f"{prediction.match.home_team} vs {prediction.match.away_team}"))
            self.predictions_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, prediction.match.id)
            self.predictions_table.setItem(row, 1, QTableWidgetItem(prediction.match.home_team))
            self.predictions_table.setItem(row, 2, QTableWidgetItem(prediction.match.away_team))
            combo = QComboBox()
            combo.addItems(["1", "X", "2"])
            combo.setCurrentText(prediction.prediction)
            self.predictions_table.setCellWidget(row, 3, combo)

    def update_results_table(self, matches):
        self.results_table.setRowCount(len(matches))
        for row, match in enumerate(matches):
            self.results_table.setItem(row, 0, QTableWidgetItem(f"{match.home_team} vs {match.away_team}"))
            self.results_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, match.id)
            self.results_table.setItem(row, 1, QTableWidgetItem(match.home_team))
            self.results_table.setItem(row, 2, QTableWidgetItem(match.away_team))
            combo = QComboBox()
            combo.addItems(["1", "X", "2", "Sospesa", "Posticipata", "Rinviata", "Annullata"])
            if match.result:
                combo.setCurrentText(match.result.value)
            self.results_table.setCellWidget(row, 3, combo)

    def update_standings(self, standings):
        self.standings_table.setRowCount(len(standings))
        for row, (participant, score) in enumerate(standings):
            self.standings_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.standings_table.setItem(row, 1, QTableWidgetItem(participant))
            self.standings_table.setItem(row, 2, QTableWidgetItem(str(score)))

    def show_weekly_prize_winners(self, amount, winners):
        winners_str = ", ".join(winners)
        QMessageBox.information(self, "Premio Settimanale", f"Il premio di {amount}€ è stato assegnato a: {winners_str}")

    def show_final_prizes(self, prizes):
        message = "Premi finali assegnati:\n\n"
        for position, name, amount in prizes:
            message += f"{position}° posto: {name} - {amount:.2f}€\n"
        QMessageBox.information(self, "Premi Finali", message)

    def load_active_tournament(self):
        active_tournament = self.viewmodel.load_active_tournament()
        if active_tournament:
            self.update_tournament_info(active_tournament)
            participants = self.viewmodel.model.get_participants(active_tournament.id)
            self.update_participants_list(participants)
            self.show_appropriate_page(active_tournament.state)
        else:
            self.show_create_tournament_page()

    def show_appropriate_page(self, tournament_state):
        if tournament_state == TournamentState.ADDING_PARTICIPANTS:
            self.show_add_participants_page()
        elif tournament_state == TournamentState.IN_PROGRESS:
            current_round = self.viewmodel.get_current_round()
            if current_round:
                self.show_appropriate_round_page(current_round.state)
            else:
                self.show_manage_round_page()  # Fallback se non c'è una giornata corrente
        elif tournament_state == TournamentState.CONCLUDED:
            self.show_view_standings_page()
        else:
            self.show_create_tournament_page()

    def show_appropriate_round_page(self, round_state):
        if round_state == RoundState.SELECTING_DATE:
            self.show_manage_round_page()
        elif round_state == RoundState.ENTERING_TEAMS:
            self.show_manage_round_page()
        elif round_state == RoundState.ENTERING_PREDICTIONS:
            self.show_enter_predictions_page()
        elif round_state == RoundState.ENTERING_RESULTS:
            self.show_enter_results_page()
        elif round_state in [RoundState.VIEWING_REPORT, RoundState.ROUND_CONCLUDED]:
            self.show_view_standings_page()
        else:
            self.show_manage_round_page()

    def update_tournament_info(self, tournament):
        self.tournament_name_label.setText(f"Nome Torneo: {tournament.name}")
        self.tournament_state_label.setText(f"Stato Torneo: {tournament.state.name}")
        current_round = self.viewmodel.get_current_round()
        if current_round:
            self.round_number_label.setText(f"Numero Giornata: {current_round.round_number}")
            self.round_state_label.setText(f"Stato Giornata: {current_round.state.name}")
        else:
            self.round_number_label.setText("Numero Giornata: -")
            self.round_state_label.setText("Stato Giornata: -")
    
    def show_error(self, message):
        QMessageBox.critical(self, "Errore", message)

    def export_standings(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Esporta Classifica", "", "CSV Files (*.csv);;PDF Files (*.pdf)")
        if filename:
            if filename.endswith('.csv'):
                self.viewmodel.export_standings_to_csv(filename)
            elif filename.endswith('.pdf'):
                self.viewmodel.export_standings_to_pdf(filename)
            QMessageBox.information(self, "Esportazione Completata", f"La classifica è stata esportata in {filename}")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Conferma Uscita',
                                     "Sei sicuro di voler chiudere l'applicazione?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.viewmodel.save_tournament()
            event.accept()
        else:
            event.ignore()

    def update_statistics(self):
        stats = self.viewmodel.get_tournament_statistics()
        stats_text = f"""
        Statistiche del Torneo:
        Partecipanti Totali: {stats['total_participants']}
        Giornate Completate: {stats['completed_rounds']}
        Partite Totali: {stats['total_matches']}
        Pronostici Totali: {stats['total_predictions']}
        """
        self.statistics_label.setText(stats_text)

    def show_participant_performance(self):
        participant, ok = QInputDialog.getItem(self, "Seleziona Partecipante", 
                                               "Partecipante:", 
                                               [p.name for p in self.viewmodel.active_tournament.participants], 
                                               0, False)
        if ok and participant:
            performance = self.viewmodel.get_participant_performance(participant)
            performance_text = "Prestazioni per giornata:\n"
            for round_num, score in performance:
                performance_text += f"Giornata {round_num}: {score} punti\n"
            QMessageBox.information(self, f"Prestazioni di {participant}", performance_text)

    def show_most_successful_predictions(self):
        predictions = self.viewmodel.get_most_successful_predictions()
        predictions_text = "Pronostici più azzeccati:\n"
        for result, count in predictions:
            predictions_text += f"{result}: {count} volte\n"
        QMessageBox.information(self, "Pronostici di Successo", predictions_text)

    def show_participant_streak(self):
        participant, ok = QInputDialog.getItem(self, "Seleziona Partecipante", 
                                               "Partecipante:", 
                                               [p.name for p in self.viewmodel.active_tournament.participants], 
                                               0, False)
        if ok and participant:
            streak = self.viewmodel.get_participant_streak(participant)
            QMessageBox.information(self, f"Streak di {participant}", 
                                    f"La serie positiva più lunga di {participant} è stata di {streak} giornate consecutive.")

    def show_head_to_head(self):
        participants = [p.name for p in self.viewmodel.active_tournament.participants]
        participant1, ok1 = QInputDialog.getItem(self, "Seleziona Primo Partecipante", 
                                                 "Partecipante 1:", participants, 0, False)
        if ok1:
            participants.remove(participant1)
            participant2, ok2 = QInputDialog.getItem(self, "Seleziona Secondo Partecipante", 
                                                     "Partecipante 2:", participants, 0, False)
            if ok2:
                head_to_head = self.viewmodel.get_head_to_head(participant1, participant2)
                h2h_text = f"Confronto tra {participant1} e {participant2}:\n"
                for round_num, score1, score2 in head_to_head:
                    h2h_text += f"Giornata {round_num}: {participant1} {score1} - {score2} {participant2}\n"
                QMessageBox.information(self, "Confronto Diretto", h2h_text)

    def notify_upcoming_round(self):
        self.viewmodel.notify_upcoming_round()

    def check_suspended_matches(self):
        for match, new_result in self.viewmodel.check_and_update_suspended_matches():
            result, ok = QInputDialog.getItem(self, f"Aggiorna Risultato",
                                              f"Nuovo risultato per {match.home_team} vs {match.away_team}:",
                                              ["1", "X", "2", "Sospesa", "Posticipata", "Rinviata", "Annullata"],
                                              0, False)
            if ok:
                new_result(result)