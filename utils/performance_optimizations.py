from sqlalchemy.orm import joinedload, subqueryload
from sqlalchemy.sql import func
import time
import logging

class PerformanceOptimizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def optimize_participant_query(query):
        return query.options(joinedload('predictions'))

    @staticmethod
    def optimize_match_query(query):
        return query.options(joinedload('predictions'))

    @staticmethod
    def optimize_round_query(query):
        return query.options(subqueryload('matches').subqueryload('predictions'))

    @staticmethod
    def batch_insert(session, objects, batch_size=1000):
        for i in range(0, len(objects), batch_size):
            session.bulk_save_objects(objects[i:i+batch_size])
            session.commit()

    @staticmethod
    def calculate_standings_optimized(session, tournament_id):
        return session.query(
            Prediction.participant_id,
            func.count(Prediction.id).label('correct_predictions')
        ).join(Match).join(Round).filter(
            Round.tournament_id == tournament_id,
            Prediction.prediction == Match.result,
            Match.result.in_(['1', 'X', '2'])
        ).group_by(Prediction.participant_id).all()

    def time_function(self, func, *args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        self.logger.info(f"Funzione {func.__name__} eseguita in {execution_time:.4f} secondi")
        return result

    @staticmethod
    def optimize_memory_usage(session):
        session.expire_all()
        session.get_bind().dispose()

    @staticmethod
    def use_caching_for_frequent_queries(session, model, query_func, cache_key):
        cache = getattr(session, '_query_cache', {})
        if cache_key in cache:
            return cache[cache_key]
        result = query_func(session, model)
        cache[cache_key] = result
        setattr(session, '_query_cache', cache)
        return result

    @staticmethod
    def clear_query_cache(session):
        if hasattr(session, '_query_cache'):
            delattr(session, '_query_cache')

    def profile_query(self, session, query):
        start_time = time.time()
        result = query.all()
        end_time = time.time()
        execution_time = end_time - start_time
        self.logger.info(f"Query eseguita in {execution_time:.4f} secondi")
        self.logger.debug(f"SQL: {query.statement.compile(compile_kwargs={'literal_binds': True})}")
        return result