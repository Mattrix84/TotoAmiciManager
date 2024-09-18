from .custom_exceptions import ValidationError
import re
from datetime import date as date_type

class DataValidator:
    @staticmethod
    def validate_tournament_creation(name, num_rounds, num_matches_per_round, num_participants, 
                                     min_correct_predictions, participant_fee, 
                                     weekly_prize_percentage, final_prize_percentage):
        if not name or len(name) > 100:
            raise ValidationError("Il nome del torneo deve essere compreso tra 1 e 100 caratteri.")
        if not (36 <= num_rounds <= 42):
            raise ValidationError("Il numero di giornate deve essere compreso tra 36 e 42.")
        if not (13 <= num_matches_per_round <= 16):
            raise ValidationError("Il numero di partite per giornata deve essere compreso tra 13 e 16.")
        if not (20 <= num_participants <= 200):
            raise ValidationError("Il numero di partecipanti deve essere compreso tra 20 e 200.")
        if not (7 <= min_correct_predictions <= 12):
            raise ValidationError("Il numero minimo di pronostici corretti deve essere compreso tra 7 e 12.")
        if not (1 <= participant_fee <= 100):
            raise ValidationError("La quota di partecipazione deve essere compresa tra 1€ e 100€.")
        if not (5 <= weekly_prize_percentage <= 50):
            raise ValidationError("La percentuale del premio settimanale deve essere compresa tra 5% e 50%.")
        if not (50 <= final_prize_percentage <= 100):
            raise ValidationError("La percentuale del premio finale deve essere compresa tra 50% e 100%.")
    
    @staticmethod
    def validate_participant_name(name):
        if not name or len(name) > 50:
            raise ValidationError("Il nome del partecipante deve essere compreso tra 1 e 50 caratteri.")
        if not re.match(r'^[a-zA-Z0-9\s]+$', name):
            raise ValidationError("Il nome del partecipante può contenere solo lettere, numeri e spazi.")

    @staticmethod
    def validate_date(date_value):
        if not isinstance(date_value, date_type):
            raise ValidationError("Il valore fornito non è una data valida.")
        if date_value < date_type.today():
            raise ValidationError("La data non può essere nel passato.")
    
    @staticmethod
    def validate_match(home_team, away_team, existing_matches):
        if not home_team or not away_team:
            raise ValidationError("I nomi delle squadre non possono essere vuoti.")
        if home_team == away_team:
            raise ValidationError("Le squadre di casa e trasferta non possono essere uguali.")
        if len(home_team) > 50 or len(away_team) > 50:
            raise ValidationError("I nomi delle squadre non possono superare i 50 caratteri.")
        for match in existing_matches:
            if home_team in (match.home_team, match.away_team) or away_team in (match.home_team, match.away_team):
                raise ValidationError("Una squadra non può giocare più di una partita per giornata.")

    @staticmethod
    def validate_prediction(prediction):
        valid_predictions = ["1", "X", "2"]
        if prediction not in valid_predictions:
            raise ValidationError("Il pronostico deve essere '1', 'X' o '2'.")

    @staticmethod
    def validate_match_result(result):
        valid_results = ["1", "X", "2", "Sospesa", "Posticipata", "Rinviata", "Annullata"]
        if result not in valid_results:
            raise ValidationError("Il risultato non è valido.")

    @staticmethod
    def validate_prize_distribution(distribution):
        if not distribution:
            raise ValidationError("La distribuzione dei premi non può essere vuota.")
        if sum(distribution.values()) != 100:
            raise ValidationError("La somma delle percentuali dei premi deve essere 100%.")
        if any(percentage <= 0 for percentage in distribution.values()):
            raise ValidationError("Tutte le percentuali dei premi devono essere positive.")
        if len(distribution) > 10:
            raise ValidationError("Non possono esserci più di 10 posizioni premiate.")

    @staticmethod
    def validate_weekly_budget(weekly_budget, num_participants, participant_fee):
        expected_budget = num_participants * participant_fee
        if abs(weekly_budget - expected_budget) > 0.01:  # Allow for small floating point errors
            raise ValidationError("Il budget settimanale non corrisponde al prodotto tra il numero di partecipanti e la quota di partecipazione.")

    @staticmethod
    def validate_final_budget(final_budget, weekly_budget, num_rounds, final_prize_percentage):
        expected_budget = (weekly_budget * num_rounds) * (final_prize_percentage / 100)
        if abs(final_budget - expected_budget) > 0.01:  # Allow for small floating point errors
            raise ValidationError("Il budget dei premi finali non corrisponde al calcolo previsto.")

    @staticmethod
    def validate_round_number(round_number, total_rounds):
        if not (1 <= round_number <= total_rounds):
            raise ValidationError(f"Il numero di giornata deve essere compreso tra 1 e {total_rounds}.")

    @staticmethod
    def validate_participant_count(current_count, max_count):
        if current_count > max_count:
            raise ValidationError(f"Il numero di partecipanti non può superare il massimo stabilito di {max_count}.")

    @staticmethod
    def validate_predictions_count(predictions_count, expected_count):
        if predictions_count != expected_count:
            raise ValidationError(f"Il numero di pronostici ({predictions_count}) non corrisponde al numero atteso ({expected_count}).")

    @staticmethod
    def validate_results_count(results_count, expected_count):
        if results_count != expected_count:
            raise ValidationError(f"Il numero di risultati ({results_count}) non corrisponde al numero atteso ({expected_count}).")