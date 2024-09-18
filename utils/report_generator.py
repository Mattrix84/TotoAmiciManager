import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import seaborn as sns
from .custom_exceptions import ValidationError

class ReportGenerator:
    def __init__(self, model):
        self.model = model

    def generate_participant_performance_report(self, tournament_id):
        participants = self.model.get_participants(tournament_id)
        rounds = self.model.get_rounds(tournament_id)
        
        data = []
        for participant in participants:
            participant_data = {'Partecipante': participant.name}
            for round in rounds:
                score = self.model.calculate_round_scores(round.id).get(participant.id, 0)
                participant_data[f'Giornata {round.round_number}'] = score
            data.append(participant_data)
        
        df = pd.DataFrame(data)
        df.set_index('Partecipante', inplace=True)
        
        plt.figure(figsize=(12, 6))
        sns.heatmap(df, annot=True, cmap="YlGnBu", fmt="d")
        plt.title('Prestazioni dei Partecipanti per Giornata')
        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        
        return df, img_buffer

    def generate_most_predicted_teams_report(self, tournament_id):
        predictions = self.model.session.query(Prediction).join(Match).join(Round).filter(Round.tournament_id == tournament_id).all()
        
        home_teams = [p.match.home_team for p in predictions]
        away_teams = [p.match.away_team for p in predictions]
        all_teams = home_teams + away_teams
        
        team_counts = pd.Series(all_teams).value_counts()
        
        plt.figure(figsize=(10, 6))
        sns.barplot(x=team_counts.index, y=team_counts.values)
        plt.title('Squadre più Pronosticate')
        plt.xlabel('Squadra')
        plt.ylabel('Numero di Pronostici')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        
        return team_counts, img_buffer

    def generate_weekly_prizes_report(self, tournament_id):
        weekly_prizes = self.model.session.query(WeeklyPrize).filter_by(tournament_id=tournament_id).all()
        
        data = [{'Giornata': wp.round.round_number, 'Vincitore': wp.winner.name, 'Premio': wp.amount} for wp in weekly_prizes]
        df = pd.DataFrame(data)
        
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=df, x='Giornata', y='Premio')
        plt.title('Premi Settimanali Assegnati')
        plt.xlabel('Giornata')
        plt.ylabel('Premio (€)')
        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        
        return df, img_buffer

    def generate_final_standings_report(self, tournament_id):
        standings = self.model.get_tournament_standings(tournament_id)
        
        data = [{'Posizione': i+1, 'Partecipante': self.model.session.query(Participant).get(p_id).name, 'Punteggio': score} 
                for i, (p_id, score) in enumerate(sorted(standings.items(), key=lambda x: x[1], reverse=True))]
        df = pd.DataFrame(data)
        
        plt.figure(figsize=(10, 6))
        sns.barplot(data=df, x='Partecipante', y='Punteggio')
        plt.title('Classifica Finale del Torneo')
        plt.xlabel('Partecipante')
        plt.ylabel('Punteggio Totale')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        
        return df, img_buffer

    def generate_prediction_accuracy_report(self, tournament_id):
        predictions = self.model.session.query(Prediction).join(Match).join(Round).filter(Round.tournament_id == tournament_id).all()
        
        correct_predictions = sum(1 for p in predictions if p.prediction == p.match.result and p.match.result in ['1', 'X', '2'])
        total_predictions = len(predictions)
        
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        results = {'1': 0, 'X': 0, '2': 0}
        for p in predictions:
            if p.prediction in results:
                results[p.prediction] += 1
        
        plt.figure(figsize=(10, 6))
        plt.pie(results.values(), labels=results.keys(), autopct='%1.1f%%')
        plt.title(f'Distribuzione dei Pronostici (Accuratezza: {accuracy:.2%})')
        plt.axis('equal')
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        
        return accuracy, results, img_buffer

    def generate_team_performance_report(self, tournament_id):
        matches = self.model.session.query(Match).join(Round).filter(Round.tournament_id == tournament_id).all()
        
        team_performance = {}
        for match in matches:
            if match.result in ['1', 'X', '2']:
                if match.home_team not in team_performance:
                    team_performance[match.home_team] = {'wins': 0, 'draws': 0, 'losses': 0}
                if match.away_team not in team_performance:
                    team_performance[match.away_team] = {'wins': 0, 'draws': 0, 'losses': 0}
                
                if match.result == '1':
                    team_performance[match.home_team]['wins'] += 1
                    team_performance[match.away_team]['losses'] += 1
                elif match.result == 'X':
                    team_performance[match.home_team]['draws'] += 1
                    team_performance[match.away_team]['draws'] += 1
                else:  # '2'
                    team_performance[match.home_team]['losses'] += 1
                    team_performance[match.away_team]['wins'] += 1
        
        df = pd.DataFrame(team_performance).T
        df['total'] = df['wins'] + df['draws'] + df['losses']
        df['win_rate'] = df['wins'] / df['total']
        df = df.sort_values('win_rate', ascending=False)
        
        plt.figure(figsize=(12, 6))
        sns.barplot(data=df, x=df.index, y='win_rate')
        plt.title('Percentuale di Vittorie per Squadra')
        plt.xlabel('Squadra')
        plt.ylabel('Percentuale di Vittorie')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        
        return df, img_buffer

    def generate_tournament_summary_report(self, tournament_id):
        tournament = self.model.session.query(Tournament).get(tournament_id)
        if not tournament:
            raise ValidationError("Torneo non trovato")
        
        summary = {
            'Nome Torneo': tournament.name,
            'Anno': tournament.year,
            'Numero di Giornate': tournament.num_rounds,
            'Numero di Partecipanti': tournament.num_participants,
            'Quota di Partecipazione': f"€{tournament.participant_fee:.2f}",
            'Premio Settimanale': f"€{tournament.weekly_budget:.2f}",
            'Premio Finale Totale': f"€{tournament.final_budget:.2f}",
        }
        
        standings = self.model.get_tournament_standings(tournament_id)
        winner = max(standings, key=standings.get)
        winner_name = self.model.session.query(Participant).get(winner).name
        summary['Vincitore del Torneo'] = f"{winner_name} (Punteggio: {standings[winner]})"
        
        total_predictions = self.model.session.query(Prediction).join(Match).join(Round).filter(Round.tournament_id == tournament_id).count()
        correct_predictions = self.model.session.query(Prediction).join(Match).join(Round).filter(
            Round.tournament_id == tournament_id,
            Prediction.prediction == Match.result,
            Match.result.in_(['1', 'X', '2'])
        ).count()
        
        summary['Totale Pronostici'] = total_predictions
        summary['Pronostici Corretti'] = correct_predictions
        summary['Accuratezza Pronostici'] = f"{(correct_predictions / total_predictions * 100):.2f}%" if total_predictions > 0 else "N/A"
        
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, '\n'.join(f"{k}: {v}" for k, v in summary.items()),
                 horizontalalignment='center', verticalalignment='center', fontsize=12)
        plt.axis('off')
        plt.tight_layout()
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        
        return summary, img_buffer