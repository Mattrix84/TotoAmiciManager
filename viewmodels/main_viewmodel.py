from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime, timedelta, time
from datetime import date as date_type
from utils.auto_save import AutoSave
from utils.report_generator import ReportGenerator
from utils.data_exporter import DataExporter
from utils.custom_exceptions import *
from utils.data_validator import DataValidator
from utils.notification_manager import NotificationManager
from utils.performance_optimizations import PerformanceOptimizer
from utils.database_backup import DatabaseBackup
from models.database_schema import Tournament, Round, RoundState, TournamentState, ProgramState, MatchResult

class MainViewModel(QObject):
    # Segnali
    tournament_created = pyqtSignal(Tournament)
    tournament_updated = pyqtSignal(Tournament)
    tournament_state_changed = pyqtSignal(TournamentState)
    tournament_completed = pyqtSignal()
    participants_updated = pyqtSignal(list)
    remaining_slots_updated = pyqtSignal(int)
    participants_limit_reached = pyqtSignal()
    round_date_set = pyqtSignal(int)  # int è l'ID del round
    round_updated = pyqtSignal(Round)
    round_state_changed = pyqtSignal(int, RoundState)
    matches_updated = pyqtSignal(list)
    predictions_updated = pyqtSignal(list)
    results_updated = pyqtSignal(dict)
    standings_updated = pyqtSignal(list)
    weekly_prize_assigned = pyqtSignal(float, list)
    final_prizes_assigned = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.active_tournament = None
        self.current_round = None
        self.auto_save = AutoSave(self.model)
        self.report_generator = ReportGenerator(self.model)
        self.data_exporter = DataExporter()
        self.validator = DataValidator()
        self.notification_manager = NotificationManager()
        self.performance_optimizer = PerformanceOptimizer()
        self.db_backup = DatabaseBackup("torneo_pronostici.db", "backups")
        self.db_backup.start_scheduled_backup()

    def load_active_tournament(self):
        self.active_tournament = self.model.get_active_tournament()
        if self.active_tournament:
            self.tournament_updated.emit(self.active_tournament)
            participants = self.model.get_participants(self.active_tournament.id)
            self.participants_updated.emit(participants)
            self.update_tournament_state()
        return self.active_tournament

    def create_tournament(self, name, start_date, num_rounds, num_matches_per_round, num_participants, 
                          min_correct_predictions, participant_fee, weekly_prize_percentage, 
                          final_prizes_percentage):
        try:
            self.validator.validate_tournament_creation(
                name, num_rounds, num_matches_per_round, num_participants,
                min_correct_predictions, participant_fee, weekly_prize_percentage, 
                final_prizes_percentage
            )
            tournament = self.model.create_tournament(
                name, datetime.now().year, start_date, num_rounds, num_matches_per_round, num_participants,
                min_correct_predictions, participant_fee, weekly_prize_percentage, final_prizes_percentage
            )
            self.active_tournament = tournament
            self.tournament_created.emit(tournament)
            self.update_tournament_state()
        except ValueError as e:
            self.error_occurred.emit(str(e))
        except ValidationError as e:
            self.error_occurred.emit(str(e))
        except Exception as e:
            self.error_occurred.emit(f"Errore imprevisto: {str(e)}")

    def add_participant(self, name):
        try:
            self.validator.validate_participant_name(name)
            existing_participants = self.model.get_participants(self.active_tournament.id)
            if any(p.name.lower() == name.lower() for p in existing_participants):
                raise ValidationError("Un partecipante con questo nome esiste già.")
        
            participant = self.model.add_participant(self.active_tournament.id, name)
            participants = self.model.get_participants(self.active_tournament.id)
            self.participants_updated.emit(participants)
        
            if len(participants) == self.active_tournament.num_participants:
                self.participants_limit_reached.emit()
        except ValidationError as e:
            self.error_occurred.emit(str(e))
        except Exception as e:
            self.error_occurred.emit(f"Errore nell'aggiunta del partecipante: {str(e)}")

    def edit_participant(self, participant_id, new_name):
        try:
            self.validator.validate_participant_name(new_name)
            self.model.edit_participant(participant_id, new_name)
            participants = self.model.get_participants(self.active_tournament.id)
            self.participants_updated.emit(participants)
        except ValidationError as e:
            self.error_occurred.emit(str(e))
        except Exception as e:
            self.error_occurred.emit(f"Errore durante la modifica del partecipante: {str(e)}")
    
    def start_tournament(self):
        try:
            if not self.active_tournament:
                raise ValueError("Nessun torneo attivo")
        
            self.model.update_tournament_state(self.active_tournament.id, TournamentState.IN_PROGRESS)
            self.active_tournament.state = TournamentState.IN_PROGRESS
            self.tournament_state_changed.emit(TournamentState.IN_PROGRESS)
        
            # Creiamo la prima giornata in una transazione separata
            self.create_first_round()
        
        except Exception as e:
            self.error_occurred.emit(f"Errore nell'avvio del torneo: {str(e)}")
            print(f"Errore dettagliato: {e}")  # Per il debug

    def create_first_round(self):
        try:
            first_round = self.model.create_round(self.active_tournament.id, 1, date_type.today())
            self.current_round = first_round
            self.round_updated.emit(first_round)
        except Exception as e:
            self.error_occurred.emit(f"Errore nella creazione della prima giornata: {str(e)}")
            print(f"Errore dettagliato: {e}")  # Per il debug

    

    def populate_rounds(self):
        for round_number in range(1, self.active_tournament.num_rounds + 1):
            round = self.model.create_round(self.active_tournament.id, round_number, None)
            for _ in range(self.active_tournament.num_matches_per_round):
                self.model.add_match(round.id, "", "")

    def update_tournament_state(self):
        if not self.active_tournament:
            return

        new_state = self.active_tournament.state
        if new_state != self.active_tournament.state:
            self.model.update_tournament_state(self.active_tournament.id, new_state)
            self.tournament_state_changed.emit(new_state)

        if new_state == TournamentState.IN_PROGRESS:
            self.update_current_round()

    def get_current_round(self):
        if self.active_tournament:
            return self.model.get_current_round(self.active_tournament.id)
        return None
    
    def update_current_round(self):
        if not self.current_round or self.current_round.state == RoundState.ROUND_CONCLUDED:
            next_round = self.get_next_round()
            if next_round:
                self.current_round = next_round
                self.round_updated.emit(self.current_round)
                self.update_round_state()

    def get_next_round(self):
        rounds = self.model.get_rounds(self.active_tournament.id)
        for round in rounds:
            if round.state != RoundState.ROUND_CONCLUDED:
                return round
        return None

    def update_round_state(self):
        if not self.current_round:
            return

        new_state = self.current_round.state
        if new_state != self.current_round.state:
            self.model.update_round_state(self.current_round.id, new_state)
            self.round_state_changed.emit(self.current_round.round_number, new_state)

    def set_round_date(self, date_type):
        try:
            self.validator.validate_date(date_type)
            self.model.update_round_date(self.current_round.id, date_type)
            self.current_round.date = date_type
            self.round_updated.emit(self.current_round)
            self.update_round_state()
            # Emettiamo un nuovo segnale per indicare che la data è stata impostata
            self.round_date_set.emit(self.current_round.id)
        except Exception as e:
            self.error_occurred.emit(f"Errore nell'impostazione della data: {str(e)}")
            print(f"Errore dettagliato: {e}")  # Per il debug

    def add_match(self, home_team, away_team):
        try:
            self.validator.validate_match(home_team, away_team, self.model.get_matches(self.current_round.id))
            match = self.model.add_match(self.current_round.id, home_team, away_team)
            matches = self.model.get_matches(self.current_round.id)
            self.matches_updated.emit(matches)
            if len(matches) == self.active_tournament.num_matches_per_round:
                self.update_round_state()
        except ValidationError as e:
            self.error_occurred.emit(str(e))

    def add_prediction(self, participant_id, match_id, prediction):
        try:
            self.validator.validate_prediction(prediction)
            self.model.add_prediction(participant_id, match_id, prediction)
            predictions = self.model.get_predictions(participant_id, self.current_round.id)
            self.predictions_updated.emit(predictions)
            if self.are_all_predictions_entered():
                self.update_round_state()
        except ValidationError as e:
            self.error_occurred.emit(str(e))

    def enter_match_result(self, match_id, result):
        try:
            self.validator.validate_match_result(result)
            self.model.update_match_result(match_id, result)
            self.update_standings()
            if self.are_all_results_entered():
                self.update_round_state()
        except ValidationError as e:
            self.error_occurred.emit(str(e))

    def complete_round(self):
        if self.current_round.state != RoundState.VIEWING_REPORT:
            raise StateError("La giornata non può essere completata in questo momento.")
        
        self.assign_weekly_prize()
        self.model.update_round_state(self.current_round.id, RoundState.ROUND_CONCLUDED)
        self.round_state_changed.emit(self.current_round.round_number, RoundState.ROUND_CONCLUDED)
        
        if self.is_tournament_completed():
            self.complete_tournament()
        else:
            self.update_current_round()

    def assign_weekly_prize(self):
        winners, prize_amount = self.model.get_weekly_prize_winners(self.current_round.id)
        if winners:
            prize_per_winner = prize_amount / len(winners)
            for winner_id in winners:
                self.model.assign_weekly_prize(self.active_tournament.id, self.current_round.id, winner_id, prize_per_winner)
            winner_names = [self.model.get_participant_name(winner_id) for winner_id in winners]
            self.weekly_prize_assigned.emit(prize_amount, winner_names)
        else:
            next_round = self.get_next_round()
            if next_round:
                next_round.weekly_budget += self.current_round.weekly_budget
                self.model.session.commit()

    def update_standings(self):
        standings = self.model.get_tournament_standings(self.active_tournament.id)
        sorted_standings = sorted(standings.items(), key=lambda x: x[1], reverse=True)
        self.standings_updated.emit([(self.model.get_participant_name(p_id), score) for p_id, score in sorted_standings])

    def complete_tournament(self):
        if self.active_tournament.state != TournamentState.IN_PROGRESS:
            raise StateError("Il torneo non può essere completato in questo momento.")
        
        self.assign_final_prizes()
        self.model.update_tournament_state(self.active_tournament.id, TournamentState.CONCLUDED)
        self.tournament_completed.emit()

    def assign_final_prizes(self):
        standings = self.model.get_tournament_standings(self.active_tournament.id)
        sorted_standings = sorted(standings.items(), key=lambda x: x[1], reverse=True)
        total_prize = self.active_tournament.final_budget
        prize_distribution = self.get_prize_distribution()
        
        prizes = []
        for position, (participant_id, _) in enumerate(sorted_standings[:len(prize_distribution)], start=1):
            prize_percentage = prize_distribution[position]
            prize_amount = total_prize * (prize_percentage / 100)
            self.model.assign_final_prizes(self.active_tournament.id, participant_id, position, prize_amount)
            participant_name = self.model.get_participant_name(participant_id)
            prizes.append((position, participant_name, prize_amount))
        
        self.final_prizes_assigned.emit(prizes)

    def get_prize_distribution(self):
        # Questo metodo dovrebbe essere implementato per restituire la distribuzione dei premi finali
        # Per ora, usiamo una distribuzione predefinita
        return {1: 50, 2: 30, 3: 20}

    def get_final_prizes_distribution(self):
        if not self.active_tournament:
            return {}
        return self.active_tournament.final_prizes_distribution

    def update_final_prizes_distribution(self, distribution):
        if not self.active_tournament:
            raise StateError("Nessun torneo attivo")
        self.model.update_final_prizes_distribution(self.active_tournament.id, distribution)
        self.final_prizes_distribution_updated.emit(distribution)

    def calculate_final_prizes_target(self, percentage):
        if not self.active_tournament:
            return 0
        return (self.active_tournament.final_prizes_amount * percentage) / 100
    
    def generate_round_report(self, round_id):
        return self.model.get_round_summary(round_id)

    def generate_tournament_report(self):
        return self.model.get_tournament_summary(self.active_tournament.id)

    def export_standings_to_csv(self, filename):
        standings = self.model.get_tournament_standings(self.active_tournament.id)
        sorted_standings = sorted(standings.items(), key=lambda x: x[1], reverse=True)
        data = [{"Posizione": i+1, "Partecipante": self.model.get_participant_name(p_id), "Punteggio": score} 
                for i, (p_id, score) in enumerate(sorted_standings)]
        self.data_exporter.export_to_csv(data, filename)

    def export_standings_to_pdf(self, filename):
        standings = self.model.get_tournament_standings(self.active_tournament.id)
        sorted_standings = sorted(standings.items(), key=lambda x: x[1], reverse=True)
        data = [{"Posizione": i+1, "Partecipante": self.model.get_participant_name(p_id), "Punteggio": score} 
                for i, (p_id, score) in enumerate(sorted_standings)]
        self.data_exporter.export_to_pdf(data, filename, f"Classifica del Torneo: {self.active_tournament.name}")

    # Metodi di supporto
    def are_all_participants_added(self):
        return len(self.model.get_participants(self.active_tournament.id)) == self.active_tournament.num_participants

    def is_round_date_set(self):
        return self.current_round.date is not None

    def are_all_teams_entered(self):
        matches = self.model.get_matches(self.current_round.id)
        return len(matches) == self.active_tournament.num_matches_per_round and all(m.home_team and m.away_team for m in matches)

    def are_all_predictions_entered(self):
        predictions_count = self.model.session.query(Prediction).join(Match).filter(
            Match.round_id == self.current_round.id
        ).count()
        expected_count = self.active_tournament.num_participants * self.active_tournament.num_matches_per_round
        return predictions_count == expected_count

    def are_all_results_entered(self):
        results_count = self.model.session.query(Match).filter(
            Match.round_id == self.current_round.id,
            Match.result.in_([MatchResult.WIN_HOME, MatchResult.DRAW, MatchResult.WIN_AWAY, 
                              MatchResult.SUSPENDED, MatchResult.POSTPONED, MatchResult.DELAYED, 
                              MatchResult.CANCELLED])
        ).count()
        return results_count == self.active_tournament.num_matches_per_round

    def is_tournament_completed(self):
        completed_rounds = self.model.session.query(Round).filter(
            Round.tournament_id == self.active_tournament.id,
            Round.state == RoundState.ROUND_CONCLUDED
        ).count()
        return completed_rounds == self.active_tournament.num_rounds

    def get_today_or_future_date(self):
        if self.active_tournament and self.active_tournament.start_date:
            return max(date_type.today(), self.active_tournament.start_date)
        return date_type.today()

    def can_enter_results(self):
        if not self.current_round or not self.current_round.date:
            return False
        return datetime.now().date() >= self.current_round.date and datetime.now().time() >= time(12, 0)

    def generate_and_export_participant_performance_report(self, filename):
        df, img_buffer = self.report_generator.generate_participant_performance_report(self.active_tournament.id)
        self.data_exporter.export_participant_performance(df, img_buffer, filename)

    def generate_and_export_most_predicted_teams_report(self, filename):
        series, img_buffer = self.report_generator.generate_most_predicted_teams_report(self.active_tournament.id)
        self.data_exporter.export_most_predicted_teams(series, img_buffer, filename)

    def generate_and_export_weekly_prizes_report(self, filename):
        df, img_buffer = self.report_generator.generate_weekly_prizes_report(self.active_tournament.id)
        self.data_exporter.export_weekly_prizes(df, img_buffer, filename)

    def generate_and_export_final_standings_report(self, filename):
        df, img_buffer = self.report_generator.generate_final_standings_report(self.active_tournament.id)
        self.data_exporter.export_final_standings(df, img_buffer, filename)

    def save_tournament(self):
        try:
            self.model.session.commit()
            self.notification_manager.notify("Salvataggio", "Torneo salvato con successo")
        except Exception as e:
            self.error_occurred.emit(f"Errore durante il salvataggio: {str(e)}")

    def load_tournament(self, tournament_id):
        try:
            tournament = self.model.session.query(Tournament).get(tournament_id)
            if tournament:
                self.active_tournament = tournament
                self.tournament_updated.emit(tournament)
                self.update_tournament_state()
            else:
                raise ValueError("Torneo non trovato")
        except Exception as e:
            self.error_occurred.emit(f"Errore durante il caricamento del torneo: {str(e)}")

    def delete_tournament(self, tournament_id):
        try:
            tournament = self.model.session.query(Tournament).get(tournament_id)
            if tournament:
                self.model.session.delete(tournament)
                self.model.session.commit()
                self.notification_manager.notify("Eliminazione", "Torneo eliminato con successo")
                if self.active_tournament and self.active_tournament.id == tournament_id:
                    self.active_tournament = None
                    self.tournament_updated.emit(None)
            else:
                raise ValueError("Torneo non trovato")
        except Exception as e:
            self.error_occurred.emit(f"Errore durante l'eliminazione del torneo: {str(e)}")

    def get_tournament_list(self):
        return self.model.session.query(Tournament).all()

    def update_prize_distribution(self, distribution):
        try:
            self.validator.validate_prize_distribution(distribution)
            if self.active_tournament:
                # Aggiorna la distribuzione dei premi nel database
                self.active_tournament.final_prizes_distribution = distribution
                self.model.session.commit()
                self.notification_manager.notify("Aggiornamento", "Distribuzione dei premi aggiornata con successo")
            else:
                raise StateError("Nessun torneo attivo")
        except (ValidationError, StateError) as e:
            self.error_occurred.emit(str(e))

    def get_tournament_statistics(self):
        if not self.active_tournament:
            raise StateError("Nessun torneo attivo")
        
        stats = {
            'total_participants': self.active_tournament.num_participants,
            'completed_rounds': self.model.session.query(Round).filter(
                Round.tournament_id == self.active_tournament.id,
                Round.state == RoundState.ROUND_CONCLUDED
            ).count(),
            'total_matches': self.model.session.query(Match).join(Round).filter(
                Round.tournament_id == self.active_tournament.id
            ).count(),
            'total_predictions': self.model.session.query(Prediction).join(Match).join(Round).filter(
                Round.tournament_id == self.active_tournament.id
            ).count(),
        }
        return stats

    def notify_upcoming_round(self):
        if self.current_round and self.current_round.date:
            days_until_round = (self.current_round.date - datetime.now().date()).days
            if days_until_round == 1:
                self.notification_manager.notify("Promemoria", f"La prossima giornata inizierà domani!")
            elif days_until_round == 0:
                self.notification_manager.notify("Promemoria", f"La giornata inizia oggi!")

    def check_and_update_suspended_matches(self):
        if not self.current_round:
            return
        
        suspended_matches = self.model.session.query(Match).filter(
            Match.round_id == self.current_round.id,
            Match.result.in_([MatchResult.SUSPENDED, MatchResult.POSTPONED, MatchResult.DELAYED])
        ).all()

        for match in suspended_matches:
            # Qui potresti implementare una logica per verificare se il risultato è stato aggiornato
            # Per ora, chiediamo all'utente di inserire il nuovo risultato
            new_result = yield f"Inserisci il nuovo risultato per {match.home_team} vs {match.away_team}"
            if new_result in [MatchResult.WIN_HOME, MatchResult.DRAW, MatchResult.WIN_AWAY]:
                match.result = new_result
                self.model.session.commit()
                self.notification_manager.notify("Aggiornamento", f"Risultato aggiornato per {match.home_team} vs {match.away_team}")

    def get_participant_performance(self, participant_id):
        if not self.active_tournament:
            raise StateError("Nessun torneo attivo")
        
        performance = []
        for round in self.active_tournament.rounds:
            score = self.model.calculate_round_scores(round.id).get(participant_id, 0)
            performance.append((round.round_number, score))
        return performance

    def get_most_successful_predictions(self):
        if not self.active_tournament:
            raise StateError("Nessun torneo attivo")
        
        correct_predictions = self.model.session.query(
            Prediction.prediction,
            func.count(Prediction.id).label('count')
        ).join(Match).filter(
            Match.round_id.in_([r.id for r in self.active_tournament.rounds]),
            Prediction.prediction == Match.result,
            Match.result.in_([MatchResult.WIN_HOME, MatchResult.DRAW, MatchResult.WIN_AWAY])
        ).group_by(Prediction.prediction).order_by(desc('count')).all()

        return [(result.value, count) for result, count in correct_predictions]

    def get_participant_streak(self, participant_id):
        if not self.active_tournament:
            raise StateError("Nessun torneo attivo")
        
        rounds = self.model.get_rounds(self.active_tournament.id)
        current_streak = 0
        max_streak = 0
        for round in rounds:
            score = self.model.calculate_round_scores(round.id).get(participant_id, 0)
            if score > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        return max_streak

    def get_head_to_head(self, participant1_id, participant2_id):
        if not self.active_tournament:
            raise StateError("Nessun torneo attivo")
        
        rounds = self.model.get_rounds(self.active_tournament.id)
        head_to_head = []
        for round in rounds:
            scores = self.model.calculate_round_scores(round.id)
            score1 = scores.get(participant1_id, 0)
            score2 = scores.get(participant2_id, 0)
            head_to_head.append((round.round_number, score1, score2))
        return head_to_head