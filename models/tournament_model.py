from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from .database_schema import Base, Tournament, Participant, Round, Match, Prediction, WeeklyPrize, FinalPrize, TournamentState, RoundState, MatchResult
from datetime import datetime, timedelta
from datetime import date as date_type

class TournamentModel:
    def __init__(self):
        self.engine = create_engine('sqlite:///torneo_pronostici.db', echo=True)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.create_tables()

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def create_tournament(self, name, year, start_date, num_rounds, num_matches_per_round, num_participants,
                              min_correct_predictions, participant_fee, weekly_prize_percentage, final_prizes_percentage):
        existing_tournament = self.session.query(Tournament).filter_by(name=name).first()
        if existing_tournament:
            raise ValueError(f"Esiste già un torneo con il nome '{name}'")
        try:    
            weekly_budget = num_participants * participant_fee
            weekly_prize_amount = (weekly_budget * weekly_prize_percentage) / 100
            final_budget = (weekly_budget - weekly_prize_amount) * num_rounds
            final_prizes_amount = (final_budget * final_prizes_percentage) / 100

            tournament = Tournament(
                name=name,
                year=year,
                start_date=start_date,
                num_rounds=num_rounds,
                num_matches_per_round=num_matches_per_round,
                num_participants=num_participants,
                min_correct_predictions=min_correct_predictions,
                participant_fee=participant_fee,
                weekly_prize_percentage=weekly_prize_percentage,
                final_prizes_percentage=final_prizes_percentage,
                weekly_budget=weekly_budget,
                weekly_prize_amount=weekly_prize_amount,
                final_prizes_amount=final_prizes_amount,
                final_budget=final_budget,
                state=TournamentState.ADDING_PARTICIPANTS
            )
            self.session.add(tournament)
            self.session.commit()
            return tournament
        except Exception as e:
            self.session.rollback()
            print(f"Errore durante la creazione del torneo: {e}")  # Per il debug
            raise

    def get_active_tournament(self):
        try:
            return self.session.query(Tournament).filter(Tournament.state != TournamentState.CONCLUDED).first()
        except Exception as e:
            print(f"Errore durante il recupero del torneo attivo: {e}")
            self.session.rollback()
            return None

    def add_participant(self, tournament_id, name):
        participant = Participant(tournament_id=tournament_id, name=name)
        self.session.add(participant)
        self.session.commit()
        return participant

    def edit_participant(self, participant_id, new_name):
        participant = self.session.query(Participant).get(participant_id)
        if participant:
            participant.name = new_name
            self.session.commit()
        else:
            raise ValueError("Partecipante non trovato")
    
    def get_participants(self, tournament_id):
        return self.session.query(Participant).filter_by(tournament_id=tournament_id).all()

    def create_round(self, tournament_id, round_number, round_date=None):
        try:
            tournament = self.session.query(Tournament).get(tournament_id)
            if not tournament:
                raise ValueError(f"Torneo con ID {tournament_id} non trovato")
            
            print(f"Debug: round_date ricevuto: {round_date}, tipo: {type(round_date)}")

            # Se la data non è fornita, usiamo la prossima la data odierna
            if round_date is None:
                round_date = date_type.today()    
            elif isinstance(round_date, str):
                # Se la data è una stringa, convertiamola in ogetto date
                round_date = date_type.fromisoformat(round_date)
            elif not isinstance(round_date, date_type):
                raise ValueError("Il tipo di dato per la data non è valido")
            
            print(f"Debug: round_date finale: {round_date}, tipo: {type(round_date)}")

            round = Round(
                tournament_id=tournament_id,
                round_number=round_number,
                date=round_date,
                weekly_budget=tournament.weekly_budget,
                state=RoundState.SELECTING_DATE
            )
            self.session.add(round)
            tournament.current_round = round_number
            self.session.commit()
            return round
        except Exception as e:
            self.session.rollback()
            print(f"Errore durante la creazione della giornata: {e}")
            raise

    def get_today_or_future_date(self):
        return max(date_type.today(), self.active_tournament.start_date)
    
    def get_rounds(self, tournament_id):
        return self.session.query(Round).filter_by(tournament_id=tournament_id).order_by(Round.round_number).all()
    
    def get_current_round(self, tournament_id):
        tournament = self.session.query(Tournament).get(tournament_id)
        if tournament:
            return self.session.query(Round).filter_by(
                tournament_id=tournament_id,
                round_number=tournament.current_round
            ).first()
        return None

    def add_match(self, round_id, home_team, away_team):
        match = Match(round_id=round_id, home_team=home_team, away_team=away_team)
        self.session.add(match)
        self.session.commit()
        return match

    def get_matches(self, round_id):
        return self.session.query(Match).filter_by(round_id=round_id).all()

    def add_prediction(self, participant_id, match_id, prediction):
        prediction = Prediction(participant_id=participant_id, match_id=match_id, prediction=prediction)
        self.session.add(prediction)
        self.session.commit()
        return prediction

    def get_predictions(self, participant_id, round_id):
        return self.session.query(Prediction).join(Match).filter(
            Prediction.participant_id == participant_id,
            Match.round_id == round_id
        ).all()

    def update_match_result(self, match_id, result):
        match = self.session.query(Match).get(match_id)
        if match:
            match.result = result
            self.session.commit()
            return match
        return None

    def calculate_round_scores(self, round_id):
        scores = {}
        round = self.session.query(Round).get(round_id)
        for participant in round.tournament.participants:
            correct_predictions = self.session.query(Prediction).join(Match).filter(
                Prediction.participant_id == participant.id,
                Match.round_id == round_id,
                Prediction.prediction == Match.result,
                Match.result.in_([MatchResult.WIN_HOME, MatchResult.DRAW, MatchResult.WIN_AWAY])
            ).count()
            scores[participant.id] = correct_predictions
        return scores

    def get_weekly_prize_winners(self, round_id):
        round = self.session.query(Round).get(round_id)
        scores = self.calculate_round_scores(round_id)
        max_score = max(scores.values()) if scores else 0
        
        if max_score >= round.tournament.min_correct_predictions:
            winners = [p_id for p_id, score in scores.items() if score == max_score]
            return winners, round.weekly_budget
        
        return [], 0

    def assign_weekly_prize(self, tournament_id, round_id, winner_id, amount):
        weekly_prize = WeeklyPrize(tournament_id=tournament_id, round_id=round_id, winner_id=winner_id, amount=amount)
        self.session.add(weekly_prize)
        self.session.commit()
        return weekly_prize

    def get_tournament_standings(self, tournament_id):
        tournament = self.session.query(Tournament).get(tournament_id)
        standings = {}
        for participant in tournament.participants:
            total_score = self.session.query(func.count(Prediction.id)).join(Match).filter(
                Prediction.participant_id == participant.id,
                Match.round_id.in_([r.id for r in tournament.rounds]),
                Prediction.prediction == Match.result,
                Match.result.in_([MatchResult.WIN_HOME, MatchResult.DRAW, MatchResult.WIN_AWAY])
            ).scalar()
            standings[participant.id] = total_score
        return standings

    def assign_final_prizes(self, tournament_id, participant_id, position, amount):
        final_prizes = FinalPrize(tournament_id=tournament_id, participant_id=participant_id, position=position, amount=amount)
        self.session.add(final_prizes)
        self.session.commit()
        return final_prizes

    def update_tournament_state(self, tournament_id, new_state):
        tournament = self.session.query(Tournament).get(tournament_id)
        if tournament:
            tournament.state = new_state
            self.session.commit()
            return True
        return False

    def update_round_state(self, round_id, new_state):
        round = self.session.query(Round).get(round_id)
        if round:
            round.state = new_state
            self.session.commit()
            return True
        return False

    def update_round_date(self, round_id, date_type):
        round = self.session.query(Round).get(round_id)
        if round:
            round.date = date_type
            round.state = RoundState.ENTERING_TEAMS
            self.session.commit()
        else:
            raise ValueError("Giornata non trovata")
    
    def get_round_summary(self, round_id):
        round = self.session.query(Round).get(round_id)
        summary = {
            'round_number': round.round_number,
            'date': round.date,
            'matches': [(m.id, m.home_team, m.away_team, m.result) for m in round.matches],
            'predictions': {},
            'scores': self.calculate_round_scores(round_id)
        }
        for participant in round.tournament.participants:
            summary['predictions'][participant.id] = [
                (p.match_id, p.prediction) for p in self.get_predictions(participant.id, round_id)
            ]
        return summary

    def get_tournament_summary(self, tournament_id):
        tournament = self.session.query(Tournament).get(tournament_id)
        summary = {
            'name': tournament.name,
            'year': tournament.year,
            'num_rounds': tournament.num_rounds,
            'num_participants': tournament.num_participants,
            'rounds': [self.get_round_summary(r.id) for r in tournament.rounds],
            'final_standings': sorted(self.get_tournament_standings(tournament_id).items(), key=lambda x: x[1], reverse=True),
            'weekly_prizes': [(wp.round.round_number, wp.winner.name, wp.amount) for wp in tournament.weekly_prizes],
            'final_prizes': [(fp.position, fp.participant.name, fp.amount) for fp in tournament.final_prizes]
        }
        return summary