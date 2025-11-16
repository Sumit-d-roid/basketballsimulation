import random
import numpy as np
from models import Game, Player, PlayerGameStats, get_session

class GameExtrapolator:
    """
    Takes a single quarter score input and extrapolates it to a full 48-minute game
    with realistic statistical variance.
    """
    
    def __init__(self):
        self.session = get_session()
    
    def extrapolate_game(self, home_team_id, away_team_id, quarter_number, 
                        home_quarter_score, away_quarter_score):
        """
        Main method to extrapolate a full game from one quarter of data.
        
        Args:
            home_team_id: ID of home team
            away_team_id: ID of away team
            quarter_number: Which quarter was played (1-4)
            home_quarter_score: Score of home team in that quarter
            away_quarter_score: Score of away team in that quarter
        
        Returns:
            Game object with full extrapolated data
        """
        
        # Create the game record
        game = Game(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            input_quarter_number=quarter_number,
            input_home_score=home_quarter_score,
            input_away_score=away_quarter_score
        )
        
        # Calculate base scoring rate from the input quarter
        home_base_rate = home_quarter_score / 12  # Points per minute
        away_base_rate = away_quarter_score / 12
        
        # Generate all 4 quarters with realistic variance
        quarters_data = self._generate_all_quarters(
            home_base_rate, away_base_rate, quarter_number,
            home_quarter_score, away_quarter_score
        )
        
        # Assign quarter scores
        game.home_q1 = quarters_data['home'][0]
        game.home_q2 = quarters_data['home'][1]
        game.home_q3 = quarters_data['home'][2]
        game.home_q4 = quarters_data['home'][3]
        game.away_q1 = quarters_data['away'][0]
        game.away_q2 = quarters_data['away'][1]
        game.away_q3 = quarters_data['away'][2]
        game.away_q4 = quarters_data['away'][3]
        
        # Calculate final scores
        game.home_team_score = sum(quarters_data['home'])
        game.away_team_score = sum(quarters_data['away'])
        game.is_completed = True
        
        self.session.add(game)
        self.session.commit()
        
        # Generate player stats for this game
        self._generate_player_stats(game)
        
        return game
    
    def _generate_all_quarters(self, home_base_rate, away_base_rate, 
                               actual_quarter, actual_home_score, actual_away_score):
        """
        Generate scores for all 4 quarters with realistic NBA variance.
        Handles blowouts realistically - prevents 21-4 from becoming 84-16.
        Uses regression to mean and momentum swings.
        """
        quarters = {
            'home': [0, 0, 0, 0],
            'away': [0, 0, 0, 0]
        }
        
        # Set the actual quarter that was played
        quarters['home'][actual_quarter - 1] = actual_home_score
        quarters['away'][actual_quarter - 1] = actual_away_score
        
        # Real NBA average: ~110 points per game = ~27.5 per quarter
        nba_avg_rate = 27.5 / 12  # 2.29 points per minute
        
        # Detect if this was a blowout quarter
        quarter_diff = abs(actual_home_score - actual_away_score)
        is_blowout = quarter_diff > 10  # More than 10 point difference
        
        # For blowouts, regress MORE toward league average (prevent 84-16 games)
        # For normal games, use actual performance more heavily
        if is_blowout:
            # Blowout: 40% input rate, 60% league average (strong regression)
            home_adjusted_rate = (home_base_rate * 0.4) + (nba_avg_rate * 0.6)
            away_adjusted_rate = (away_base_rate * 0.4) + (nba_avg_rate * 0.6)
        else:
            # Normal: 70% input rate, 30% league average
            home_adjusted_rate = (home_base_rate * 0.7) + (nba_avg_rate * 0.3)
            away_adjusted_rate = (away_base_rate * 0.7) + (nba_avg_rate * 0.3)
        
        # Generate other quarters with realistic NBA variance
        for q in range(4):
            if q == actual_quarter - 1:
                continue  # Skip the actual played quarter
            
            # NBA variance: typically ±15% per quarter
            home_variance = random.uniform(0.85, 1.15)
            away_variance = random.uniform(0.85, 1.15)
            
            # Quarter-specific adjustments (real NBA patterns)
            if q == 0:  # 1st quarter: slightly lower scoring (feeling out)
                home_variance *= random.uniform(0.92, 1.05)
                away_variance *= random.uniform(0.92, 1.05)
            elif q == 1:  # 2nd quarter: normal pace
                home_variance *= random.uniform(0.95, 1.10)
                away_variance *= random.uniform(0.95, 1.10)
            elif q == 2:  # 3rd quarter: often highest scoring
                home_variance *= random.uniform(1.00, 1.15)
                away_variance *= random.uniform(1.00, 1.15)
            elif q == 3:  # 4th quarter: clutch time, can vary widely
                home_variance *= random.uniform(0.90, 1.20)
                away_variance *= random.uniform(0.90, 1.20)
            
            # Calculate quarter scores (12 minutes per quarter)
            home_q_score = int(home_adjusted_rate * 12 * home_variance)
            away_q_score = int(away_adjusted_rate * 12 * away_variance)
            
            # Realistic NBA quarter scoring range: 18-35 points typically
            home_q_score = max(18, min(35, home_q_score))
            away_q_score = max(18, min(35, away_q_score))
            
            quarters['home'][q] = home_q_score
            quarters['away'][q] = away_q_score
        
        # CRITICAL: Ensure the team that won the input quarter ALWAYS wins the game
        home_total = sum(quarters['home'])
        away_total = sum(quarters['away'])
        
        # Determine who should win based on input quarter
        home_should_win = actual_home_score > actual_away_score
        
        # If wrong team is winning, adjust the final score
        if home_should_win and home_total <= away_total:
            # Home should win but isn't - add points to home's last quarter
            deficit = (away_total - home_total) + random.randint(3, 8)
            quarters['home'][3] += deficit
        elif not home_should_win and away_total <= home_total:
            # Away should win but isn't - add points to away's last quarter
            deficit = (home_total - away_total) + random.randint(3, 8)
            quarters['away'][3] += deficit
        
        return quarters
    
    def _generate_player_stats(self, game):
        """
        Generate realistic player statistics for all players in the game.
        """
        from models import Team
        
        # Get both teams
        home_team = self.session.query(Team).filter_by(id=game.home_team_id).first()
        away_team = self.session.query(Team).filter_by(id=game.away_team_id).first()
        
        # Generate stats for home team
        self._generate_team_player_stats(game, home_team, game.home_team_score, 
                                         game.away_team_score, is_home=True)
        
        # Generate stats for away team
        self._generate_team_player_stats(game, away_team, game.away_team_score,
                                         game.home_team_score, is_home=False)
        
        self.session.commit()
    
    def _generate_team_player_stats(self, game, team, team_score, opponent_score, is_home):
        """
        Generate individual player stats for a team that sum up to team totals.
        """
        players = team.players
        
        # Sort players by PPG (stars play more and score more)
        players_sorted = sorted(players, key=lambda p: p.ppg, reverse=True)
        
        # Select 8-10 players who played (realistic rotation)
        num_players = random.randint(8, 10)
        playing_players = players_sorted[:num_players]
        
        # Distribute team points among players based on their PPG
        total_ppg = sum(p.ppg for p in playing_players)
        
        team_stats = {
            'points': team_score,
            'rebounds': random.randint(38, 52),
            'assists': int(team_score * random.uniform(0.18, 0.25)),  # ~20-25% of points
            'steals': random.randint(5, 12),
            'blocks': random.randint(3, 8),
            'turnovers': random.randint(10, 18),
            'fga': int(team_score * random.uniform(1.8, 2.2)),  # Field goal attempts
            'three_pa': random.randint(25, 45)  # 3-point attempts
        }
        
        for player in playing_players:
            # Calculate player's share based on their average
            share = player.ppg / total_ppg if total_ppg > 0 else 1.0 / num_players
            
            # Add some randomness (player could have hot/cold night)
            share *= random.uniform(0.7, 1.3)
            
            # Generate player stats
            points = int(team_stats['points'] * share)
            minutes = min(48, player.mpg * random.uniform(0.85, 1.15))
            
            # Shooting stats
            three_pm = int(points * random.uniform(0.15, 0.35) / 3)  # Some points from 3s
            three_pa = int(three_pm / max(0.3, player.three_pt_pct))
            
            remaining_points = points - (three_pm * 3)
            ftm = int(remaining_points * random.uniform(0.15, 0.25))
            fta = int(ftm / max(0.7, player.ft_pct))
            
            remaining_points -= ftm
            fgm_2pt = remaining_points // 2
            fgm = fgm_2pt + three_pm
            fga = int(fgm / max(0.38, player.fg_pct))
            
            # Other stats based on position and player tendencies
            rebounds = int(player.rpg * random.uniform(0.7, 1.3))
            assists = int(player.apg * random.uniform(0.7, 1.3))
            steals = int(player.spg * random.uniform(0.5, 1.5))
            blocks = int(player.bpg * random.uniform(0.5, 1.5))
            turnovers = max(0, int(assists * random.uniform(0.3, 0.6)))
            fouls = random.randint(0, 5)
            
            # Calculate advanced stats
            ts_pct = points / (2 * (fga + 0.44 * fta)) if (fga + 0.44 * fta) > 0 else 0
            efg_pct = (fgm + 0.5 * three_pm) / fga if fga > 0 else 0
            
            # Plus/minus (simplified: based on team performance and minutes)
            score_diff = team_score - opponent_score
            plus_minus = int((score_diff * (minutes / 48)) * random.uniform(0.8, 1.2))
            
            # Usage rate (simplified)
            usage_rate = ((fga + 0.44 * fta + turnovers) * 48 / minutes) if minutes > 0 else 0
            
            # PER (simplified calculation)
            per = (points + rebounds + assists + steals + blocks - 
                   (fga - fgm) - (fta - ftm) - turnovers) / minutes if minutes > 0 else 0
            per = max(0, per * 10)  # Scale to typical PER range
            
            # Create player game stats
            player_stats = PlayerGameStats(
                game_id=game.id,
                player_id=player.id,
                team_id=team.id,
                minutes_played=round(minutes, 1),
                points=points,
                rebounds=rebounds,
                offensive_rebounds=rebounds // 3,
                defensive_rebounds=(rebounds * 2) // 3,
                assists=assists,
                steals=steals,
                blocks=blocks,
                turnovers=turnovers,
                fouls=fouls,
                fgm=fgm,
                fga=fga,
                three_pm=three_pm,
                three_pa=three_pa,
                ftm=ftm,
                fta=fta,
                plus_minus=plus_minus,
                usage_rate=round(usage_rate, 3),
                true_shooting_pct=round(ts_pct, 3),
                effective_fg_pct=round(efg_pct, 3),
                per=round(per, 1)
            )
            
            self.session.add(player_stats)
