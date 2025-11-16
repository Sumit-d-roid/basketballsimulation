from models import Team, Series, get_session
import random

class TournamentManager:
    """
    Manages the tournament bracket for 32 teams in a best-of-7 series format.
    """
    
    def __init__(self):
        self.session = get_session()
    
    def create_tournament_bracket(self, run_id=None):
        """
        Create initial tournament bracket for 32 teams.
        Perfect power of 2, standard single-elimination bracket.
        Round 1: 16 series (32 teams)
        Round 2: 8 series (16 teams)
        Round 3: 4 series (8 teams)
        Round 4: 2 series (4 teams - Conference Finals)
        Round 5: 1 series (2 teams - Finals)
        
        Args:
            run_id: Optional run ID to associate series with specific season
        """
        teams = self.session.query(Team).all()
        
        if len(teams) < 32:
            raise ValueError(f"Not enough teams: Expected at least 32, found {len(teams)}")
        
        # Randomly shuffle teams and select first 32
        random.shuffle(teams)
        teams = teams[:32]
        
        # Create Round 1 matchups (16 series)
        round1_series = []
        for i in range(0, 32, 2):
            series = Series(
                tournament_round=1,
                series_number=(i // 2) + 1,
                team1_id=teams[i].id,
                team2_id=teams[i + 1].id,
                run_id=run_id
            )
            self.session.add(series)
            round1_series.append(series)
        
        self.session.commit()
        
        print("Tournament Bracket Created!")
        print("\n=== ROUND 1 (16 SERIES) ===")
        for series in round1_series:
            print(f"Series {series.series_number}: {series.team1.city} {series.team1.name} vs {series.team2.city} {series.team2.name}")
        
        return {
            'round1_series': round1_series,
            'total_teams': len(teams)
        }
    
    def create_next_round(self, current_round):
        """
        After a round completes, create the next round's matchups.
        """
        # Get all completed series from current round
        completed_series = self.session.query(Series).filter_by(
            tournament_round=current_round,
            is_completed=True
        ).all()
        
        if not completed_series:
            print(f"No completed series found in round {current_round}")
            return []
        
        # Get winners
        winners = [s.winner for s in completed_series if s.winner]
        
        if len(winners) < 2:
            print(f"Not enough winners to create next round")
            return []
        
        # Create next round matchups
        random.shuffle(winners)
        next_round = current_round + 1
        next_round_series = []
        
        # Get run_id from first completed series (all in same round should have same run_id)
        first_series = completed_series[0] if completed_series else None
        run_id = first_series.run_id if first_series else None
        
        for i in range(0, len(winners) - 1, 2):
            series = Series(
                tournament_round=next_round,
                series_number=(i // 2) + 1,
                team1_id=winners[i].id,
                team2_id=winners[i + 1].id,
                run_id=run_id
            )
            self.session.add(series)
            next_round_series.append(series)
        
        self.session.commit()
        
        print(f"\n=== ROUND {next_round} MATCHUPS ===")
        for series in next_round_series:
            print(f"Series {series.series_number}: {series.team1.city} {series.team1.name} vs "
                  f"{series.team2.city} {series.team2.name}")
        
        return next_round_series
    
    def update_series_result(self, series_id, winning_team_id):
        """
        Update series when a game is completed.
        Check if series is won (best of 7, first to 4 wins).
        Auto-advance to next round if all series in current round are complete.
        """
        series = self.session.query(Series).filter_by(id=series_id).first()
        
        if not series:
            return None
        
        # Update wins
        if winning_team_id == series.team1_id:
            series.team1_wins += 1
        elif winning_team_id == series.team2_id:
            series.team2_wins += 1
        
        # Check if series is complete (first to 4 wins)
        if series.team1_wins >= 4:
            series.winner_team_id = series.team1_id
            series.is_completed = True
            print(f"\n🏆 {series.team1.city} {series.team1.name} wins series {series.team1_wins}-{series.team2_wins}!")
            self.session.commit()
            self._check_and_advance_round(series.tournament_round)
        elif series.team2_wins >= 4:
            series.winner_team_id = series.team2_id
            series.is_completed = True
            print(f"\n🏆 {series.team2.city} {series.team2.name} wins series {series.team2_wins}-{series.team1_wins}!")
            self.session.commit()
            self._check_and_advance_round(series.tournament_round)
        else:
            self.session.commit()
        
        return series
    
    def _check_and_advance_round(self, current_round):
        """
        Check if all series in current round are complete.
        If so, automatically create next round matchups.
        """
        # Get all series in current round
        round_series = self.session.query(Series).filter_by(tournament_round=current_round).all()
        
        # Check if all are complete
        all_complete = all(s.is_completed for s in round_series)
        
        if all_complete and current_round < 5:  # Max 5 rounds
            print(f"\n✅ Round {current_round} Complete! Advancing to Round {current_round + 1}...")
            next_series = self.create_next_round(current_round)
            if next_series:
                print(f"✨ Created {len(next_series)} series for Round {current_round + 1}")
        elif all_complete and current_round == 5:
            winner = round_series[0].winner
            print(f"\n🏆🏆🏆 TOURNAMENT CHAMPION: {winner.city} {winner.name}! 🏆🏆🏆")

    
    def get_current_series(self):
        """
        Get all active (incomplete) series.
        """
        active_series = self.session.query(Series).filter_by(is_completed=False).all()
        return active_series
    
    def get_series_status(self, series_id):
        """
        Get detailed status of a series.
        """
        series = self.session.query(Series).filter_by(id=series_id).first()
        
        if not series:
            return None
        
        from models import Game
        games = self.session.query(Game).filter_by(series_id=series_id).all()
        
        return {
            'series': series,
            'team1': series.team1,
            'team2': series.team2,
            'team1_wins': series.team1_wins,
            'team2_wins': series.team2_wins,
            'games_played': len(games),
            'is_completed': series.is_completed,
            'winner': series.winner if series.is_completed else None
        }
    
    def get_tournament_overview(self):
        """
        Get overview of entire tournament.
        """
        all_series = self.session.query(Series).order_by(Series.tournament_round, Series.series_number).all()
        
        rounds = {}
        for series in all_series:
            round_num = series.tournament_round
            if round_num not in rounds:
                rounds[round_num] = []
            rounds[round_num].append(series)
        
        return rounds
