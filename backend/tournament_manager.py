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
        Create initial tournament bracket for 32 teams with East/West conferences.
        Structure:
        Round 1: 16 series (32 teams) - 8 East, 8 West
        Round 2: 8 series (16 teams) - 4 East, 4 West  
        Round 3: 4 series (8 teams) - 2 East, 2 West (Conference Semifinals)
        Round 4: 2 series (4 teams) - East Finals, West Finals
        Round 5: 1 series (2 teams) - NBA Finals
        
        Args:
            run_id: Optional run ID to associate series with specific season
        """
        teams = self.session.query(Team).all()
        
        if len(teams) < 32:
            raise ValueError(f"Not enough teams: Expected at least 32, found {len(teams)}")
        
        # Separate teams by conference
        east_teams = [t for t in teams if t.conference == 'East']
        west_teams = [t for t in teams if t.conference == 'West']
        
        # Ensure we have 16 teams per conference
        if len(east_teams) < 16:
            print(f"Warning: Only {len(east_teams)} East teams, need 16")
            # Fill with any remaining teams
            other_teams = [t for t in teams if t.conference not in ['East', 'West']]
            east_teams.extend(other_teams[:16 - len(east_teams)])
        if len(west_teams) < 16:
            print(f"Warning: Only {len(west_teams)} West teams, need 16")
            other_teams = [t for t in teams if t.conference not in ['East', 'West']]
            west_teams.extend(other_teams[:16 - len(west_teams)])
        
        # Take exactly 16 from each
        random.shuffle(east_teams)
        random.shuffle(west_teams)
        east_teams = east_teams[:16]
        west_teams = west_teams[:16]
        
        # Create Round 1 matchups (8 East + 8 West = 16 series)
        round1_series = []
        
        # East Conference Round 1 (Series 1-8)
        for i in range(0, 16, 2):
            series = Series(
                tournament_round=1,
                series_number=(i // 2) + 1,
                team1_id=east_teams[i].id,
                team2_id=east_teams[i + 1].id,
                run_id=run_id,
                conference='East'
            )
            self.session.add(series)
            round1_series.append(series)
        
        # West Conference Round 1 (Series 9-16)
        for i in range(0, 16, 2):
            series = Series(
                tournament_round=1,
                series_number=(i // 2) + 9,
                team1_id=west_teams[i].id,
                team2_id=west_teams[i + 1].id,
                run_id=run_id,
                conference='West'
            )
            self.session.add(series)
            round1_series.append(series)
        
        self.session.commit()
        
        print("Tournament Bracket Created with East/West Conferences!")
        print("\n=== EASTERN CONFERENCE - ROUND 1 ===")
        for series in round1_series[:8]:
            print(f"Series {series.series_number}: {series.team1.city} {series.team1.name} vs {series.team2.city} {series.team2.name}")
        print("\n=== WESTERN CONFERENCE - ROUND 1 ===")
        for series in round1_series[8:]:
            print(f"Series {series.series_number}: {series.team1.city} {series.team1.name} vs {series.team2.city} {series.team2.name}")
        
        return {
            'round1_series': len(round1_series),
            'total_teams': 32
        }
    
    def create_next_round(self, current_round):
        """
        After a round completes, create the next round's matchups.
        Maintains conference separation until Finals.
        """
        # Get all completed series from current round
        completed_series = self.session.query(Series).filter_by(
            tournament_round=current_round,
            is_completed=True
        ).all()
        
        if not completed_series:
            print(f"No completed series found in round {current_round}")
            return []
        
        # Get run_id from first completed series
        first_series = completed_series[0] if completed_series else None
        run_id = first_series.run_id if first_series else None
        
        next_round = current_round + 1
        next_round_series = []
        
        # If we're going into Round 5 (Finals), it's East champion vs West champion
        if next_round == 5:
            # Separate by conference
            east_series = [s for s in completed_series if s.conference == 'East']
            west_series = [s for s in completed_series if s.conference == 'West']
            
            if len(east_series) == 1 and len(west_series) == 1:
                finals = Series(
                    tournament_round=5,
                    series_number=1,
                    conference=None,  # NBA Finals has no conference
                    team1_id=east_series[0].winner.id,
                    team2_id=west_series[0].winner.id,
                    run_id=run_id
                )
                self.session.add(finals)
                next_round_series.append(finals)
                print(f"\n🏆 === NBA FINALS === 🏆")
                print(f"{east_series[0].winner.city} {east_series[0].winner.name} (East) vs {west_series[0].winner.city} {west_series[0].winner.name} (West)")
        else:
            # For rounds 1-4, keep conferences separate
            east_series = [s for s in completed_series if s.conference == 'East']
            west_series = [s for s in completed_series if s.conference == 'West']
            
            # Create East matchups
            east_winners = [s.winner for s in east_series if s.winner]
            random.shuffle(east_winners)
            for i in range(0, len(east_winners) - 1, 2):
                series = Series(
                    tournament_round=next_round,
                    series_number=(i // 2) + 1,
                    conference='East',
                    team1_id=east_winners[i].id,
                    team2_id=east_winners[i + 1].id,
                    run_id=run_id
                )
                self.session.add(series)
                next_round_series.append(series)
            
            # Create West matchups
            west_winners = [s.winner for s in west_series if s.winner]
            random.shuffle(west_winners)
            start_series_num = (len(east_winners) // 2) + 1
            for i in range(0, len(west_winners) - 1, 2):
                series = Series(
                    tournament_round=next_round,
                    series_number=(i // 2) + start_series_num,
                    conference='West',
                    team1_id=west_winners[i].id,
                    team2_id=west_winners[i + 1].id,
                    run_id=run_id
                )
                self.session.add(series)
                next_round_series.append(series)
            
            round_name = {
                2: "ROUND 2 (Conference Quarterfinals)",
                3: "ROUND 3 (Conference Semifinals)",
                4: "CONFERENCE FINALS"
            }.get(next_round, f"ROUND {next_round}")
            
            print(f"\n=== {round_name} ===")
            print(f"Eastern Conference:")
            for series in next_round_series[:len(east_winners)//2]:
                print(f"  Series {series.series_number}: {series.team1.city} {series.team1.name} vs {series.team2.city} {series.team2.name}")
            print(f"Western Conference:")
            for series in next_round_series[len(east_winners)//2:]:
                print(f"  Series {series.series_number}: {series.team1.city} {series.team1.name} vs {series.team2.city} {series.team2.name}")
        
        self.session.commit()
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
            
            # Mark the run as completed and set champion
            from models import Run
            if round_series[0].run_id:
                run = self.session.query(Run).filter_by(id=round_series[0].run_id).first()
                if run:
                    run.is_completed = True
                    run.champion_team_id = winner.id
                    self.session.commit()
                    print(f"✅ Season '{run.name}' marked as completed!")
    
    def reset_tournament(self, run_id=None):
        """
        Reset tournament by deleting all series and games for a specific run.
        Keeps teams and players intact.
        """
        from models import Game, PlayerGameStats, PlayByPlay
        
        # Build query based on run_id
        if run_id:
            series_to_delete = self.session.query(Series).filter_by(run_id=run_id).all()
        else:
            # If no run_id, reset current active run
            from models import Run
            active_run = self.session.query(Run).filter_by(is_active=True).first()
            if active_run:
                series_to_delete = self.session.query(Series).filter_by(run_id=active_run.id).all()
                run_id = active_run.id
            else:
                series_to_delete = self.session.query(Series).all()
        
        # Delete all related data
        for series in series_to_delete:
            # Get all games in this series
            games = self.session.query(Game).filter_by(series_id=series.id).all()
            for game in games:
                # Delete player stats and play-by-play
                self.session.query(PlayerGameStats).filter_by(game_id=game.id).delete()
                self.session.query(PlayByPlay).filter_by(game_id=game.id).delete()
                self.session.delete(game)
            self.session.delete(series)
        
        # Also delete any games not associated with a series in this run
        if run_id:
            orphan_games = self.session.query(Game).filter_by(run_id=run_id, series_id=None).all()
            for game in orphan_games:
                self.session.query(PlayerGameStats).filter_by(game_id=game.id).delete()
                self.session.query(PlayByPlay).filter_by(game_id=game.id).delete()
                self.session.delete(game)
        
        self.session.commit()
        print(f"✅ Tournament reset complete! All series and games deleted.")
        
        return {'message': 'Tournament reset successfully', 'run_id': run_id}
    
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
