class TournamentError(Exception):
    """Classe base per le eccezioni personalizzate del torneo."""
    pass

class ValidationError(TournamentError):
    """Eccezione sollevata per errori di validazione dei dati."""
    pass

class StateError(TournamentError):
    """Eccezione sollevata per errori relativi allo stato del torneo o della giornata."""
    pass

class ParticipantError(TournamentError):
    """Eccezione sollevata per errori relativi ai partecipanti."""
    pass

class MatchError(TournamentError):
    """Eccezione sollevata per errori relativi alle partite."""
    pass

class PredictionError(TournamentError):
    """Eccezione sollevata per errori relativi ai pronostici."""
    pass

class ResultError(TournamentError):
    """Eccezione sollevata per errori relativi ai risultati delle partite."""
    pass

class PrizeError(TournamentError):
    """Eccezione sollevata per errori relativi ai premi."""
    pass

class DatabaseError(TournamentError):
    """Eccezione sollevata per errori relativi al database."""
    pass

class ExportError(TournamentError):
    """Eccezione sollevata per errori durante l'esportazione dei dati."""
    pass