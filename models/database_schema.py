from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class ProgramState(enum.Enum):
    NO_TOURNAMENT = 0
    TOURNAMENT_OPEN = 1
    TOURNAMENT_CONCLUDED = 2

class TournamentState(enum.Enum):
    SETTING_INITIAL_PARAMETERS = 0
    ADDING_PARTICIPANTS = 1
    IN_PROGRESS = 2
    CONCLUDED = 3

class RoundState(enum.Enum):
    CREATING_FIRST_ROUND = 0
    SELECTING_DATE = 1
    ENTERING_TEAMS = 2
    ENTERING_PREDICTIONS = 3
    ENTERING_RESULTS = 4
    VIEWING_REPORT = 5
    ROUND_CONCLUDED = 6
    CREATING_NEXT_ROUND = 7
    CREATING_LAST_ROUND = 8
    VIEWING_FINAL_REPORT = 9
    TOURNAMENT_COMPLETED = 10

class MatchResult(enum.Enum):
    WIN_HOME = "1"
    DRAW = "X"
    WIN_AWAY = "2"
    SUSPENDED = "Sospesa"
    POSTPONED = "Posticipata"
    DELAYED = "Rinviata"
    CANCELLED = "Annullata"

class Tournament(Base):
    __tablename__ = 'tournaments'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    num_rounds = Column(Integer, nullable=False)
    num_matches_per_round = Column(Integer, nullable=False)
    num_participants = Column(Integer, nullable=False)
    min_correct_predictions = Column(Integer, nullable=False)
    participant_fee = Column(Float, nullable=False)
    weekly_prize_percentage = Column(Float, nullable=False)
    final_prizes_percentage = Column(Float, nullable=False)
    weekly_budget = Column(Float, nullable=False)
    final_budget = Column(Float, nullable=False)
    weekly_prize_amount = Column(Float, nullable=False)
    final_prizes_amount = Column(Float, nullable=False)
    state = Column(Enum(TournamentState), default=TournamentState.SETTING_INITIAL_PARAMETERS)
    current_round = Column(Integer, default=0)

    participants = relationship("Participant", back_populates="tournament")
    rounds = relationship("Round", back_populates="tournament")
    weekly_prizes = relationship("WeeklyPrize", back_populates="tournament")
    final_prizes = relationship("FinalPrize", back_populates="tournament")

class Participant(Base):
    __tablename__ = 'participants'

    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id'))
    name = Column(String, nullable=False)

    tournament = relationship("Tournament", back_populates="participants")
    predictions = relationship("Prediction", back_populates="participant")

class Round(Base):
    __tablename__ = 'rounds'

    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id'))
    round_number = Column(Integer, nullable=False)
    date = Column(Date, nullable=True)
    state = Column(Enum(RoundState), default=RoundState.CREATING_FIRST_ROUND)
    weekly_budget = Column(Float, nullable=False)

    tournament = relationship("Tournament", back_populates="rounds")
    matches = relationship("Match", back_populates="round")

class Match(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey('rounds.id'))
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    result = Column(Enum(MatchResult), nullable=True)
    is_final = Column(Boolean, default=False)

    round = relationship("Round", back_populates="matches")
    predictions = relationship("Prediction", back_populates="match")

class Prediction(Base):
    __tablename__ = 'predictions'

    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, ForeignKey('participants.id'))
    match_id = Column(Integer, ForeignKey('matches.id'))
    prediction = Column(Enum(MatchResult), nullable=False)

    participant = relationship("Participant", back_populates="predictions")
    match = relationship("Match", back_populates="predictions")

class WeeklyPrize(Base):
    __tablename__ = 'weekly_prizes'

    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id'))
    round_id = Column(Integer, ForeignKey('rounds.id'))
    winner_id = Column(Integer, ForeignKey('participants.id'))
    amount = Column(Float, nullable=False)

    tournament = relationship("Tournament", back_populates="weekly_prizes")
    round = relationship("Round")
    winner = relationship("Participant")

class FinalPrize(Base):
    __tablename__ = 'final_prizes'

    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id'))
    participant_id = Column(Integer, ForeignKey('participants.id'))
    position = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)

    tournament = relationship("Tournament", back_populates="final_prizes")
    participant = relationship("Participant")