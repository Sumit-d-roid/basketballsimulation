import random
from models import PlayByPlay, PlayerGameStats, get_session
from datetime import datetime

class PlayByPlayGenerator:
    """
    Generates realistic play-by-play logs for a completed game based on 
    player stats and quarter scores.
    """
    
    def __init__(self):
        self.session = get_session()
        self.event_types = [
            'made_shot', 'missed_shot', 'free_throw', 'rebound', 
            'assist', 'steal', 'block', 'turnover', 'foul', 'substitution'
        ]
    
    def generate_play_by_play(self, game):
        """
        Generate complete play-by-play log for a game.
        """
        # Get player stats for this game
        home_stats = self.session.query(PlayerGameStats).filter_by(
            game_id=game.id, team_id=game.home_team_id
        ).all()
        
        away_stats = self.session.query(PlayerGameStats).filter_by(
            game_id=game.id, team_id=game.away_team_id
        ).all()
        
        # Generate plays for each quarter
        plays = []
        running_home_score = 0
        running_away_score = 0
        
        quarter_scores = [
            (game.home_q1, game.away_q1),
            (game.home_q2, game.away_q2),
            (game.home_q3, game.away_q3),
            (game.home_q4, game.away_q4)
        ]
        
        for quarter in range(1, 5):
            home_quarter_score = quarter_scores[quarter - 1][0]
            away_quarter_score = quarter_scores[quarter - 1][1]
            
            quarter_plays = self._generate_quarter_plays(
                game, quarter, home_stats, away_stats,
                home_quarter_score, away_quarter_score,
                running_home_score, running_away_score
            )
            
            plays.extend(quarter_plays)
            
            # Update running scores
            running_home_score += home_quarter_score
            running_away_score += away_quarter_score
        
        # Save all plays to database
        for play in plays:
            self.session.add(play)
        
        self.session.commit()
        return plays
    
    def _generate_quarter_plays(self, game, quarter, home_stats, away_stats,
                                home_score, away_score, start_home_score, start_away_score):
        """
        Generate plays for a single quarter.
        """
        plays = []
        current_home_score = start_home_score
        current_away_score = start_away_score
        
        # Quarter is 12 minutes (720 seconds)
        quarter_start_seconds = (quarter - 1) * 720
        time_elapsed = 0
        
        # Estimate number of possessions (typically 90-110 per game, ~22-28 per quarter)
        total_quarter_points = home_score + away_score
        possessions = random.randint(22, 28)
        
        # Determine possession distribution
        home_possessions = int(possessions * (home_score / (home_score + away_score + 1)))
        away_possessions = possessions - home_possessions
        
        # Create possession list
        possession_list = ['home'] * home_possessions + ['away'] * away_possessions
        random.shuffle(possession_list)
        
        for possession_team in possession_list:
            # Average possession is 24-30 seconds
            possession_time = random.randint(14, 30)
            time_elapsed += possession_time
            
            if time_elapsed > 720:
                time_elapsed = 720
            
            game_time = quarter_start_seconds + time_elapsed
            time_remaining = self._format_time_remaining(720 - time_elapsed)
            
            if possession_team == 'home':
                is_home = True
                team_stats = home_stats
                team_id = game.home_team_id
                points_needed = home_score - (current_home_score - start_home_score)
            else:
                is_home = False
                team_stats = away_stats
                team_id = game.away_team_id
                points_needed = away_score - (current_away_score - start_away_score)
            
            # Generate possession plays
            possession_plays = self._generate_possession(
                game, quarter, game_time, time_remaining,
                team_id, team_stats, is_home,
                current_home_score, current_away_score,
                points_needed > 0
            )
            
            # Update scores based on possession outcome
            for play in possession_plays:
                if is_home and play.event_type in ['made_shot', 'free_throw']:
                    if play.details and play.details.get('shot_made'):
                        current_home_score += play.details.get('points', 0)
                elif not is_home and play.event_type in ['made_shot', 'free_throw']:
                    if play.details and play.details.get('shot_made'):
                        current_away_score += play.details.get('points', 0)
                
                play.home_score = current_home_score
                play.away_score = current_away_score
            
            plays.extend(possession_plays)
        
        return plays
    
    def _generate_possession(self, game, quarter, game_time, time_remaining,
                            team_id, team_stats, is_home, home_score, away_score, 
                            needs_points):
        """
        Generate plays for a single possession.
        """
        plays = []
        
        # Select a random player from the team to be primary ball handler
        if not team_stats:
            return plays
        
        # Weight selection by minutes played
        weights = [stat.minutes_played for stat in team_stats]
        player_stat = random.choices(team_stats, weights=weights)[0]
        
        # Determine possession outcome
        outcome = random.choices(
            ['made_shot', 'missed_shot', 'turnover'],
            weights=[0.48, 0.46, 0.06]  # Realistic league averages
        )[0]
        
        if outcome == 'turnover':
            # Turnover play
            play = PlayByPlay(
                game_id=game.id,
                quarter=quarter,
                game_time_seconds=game_time,
                time_remaining=time_remaining,
                event_type='turnover',
                description=f"{player_stat.player.name} turnover (bad pass)",
                team_id=team_id,
                player_id=player_stat.player_id,
                home_score=home_score,
                away_score=away_score,
                details={'turnover_type': 'bad pass'}
            )
            plays.append(play)
            
        elif outcome == 'missed_shot':
            # Missed shot
            shot_type = random.choice(['2PT', '3PT'])
            points = 3 if shot_type == '3PT' else 2
            
            play = PlayByPlay(
                game_id=game.id,
                quarter=quarter,
                game_time_seconds=game_time,
                time_remaining=time_remaining,
                event_type='missed_shot',
                description=f"{player_stat.player.name} misses {shot_type} shot",
                team_id=team_id,
                player_id=player_stat.player_id,
                home_score=home_score,
                away_score=away_score,
                details={'shot_type': shot_type, 'shot_made': False, 'points': 0}
            )
            plays.append(play)
            
            # Rebound (50% offensive, 50% defensive)
            rebound_is_offensive = random.random() < 0.30  # 30% offensive rebound rate
            if rebound_is_offensive:
                rebounder = random.choice(team_stats)
            else:
                # Defensive rebound goes to opponent (we'll simplify here)
                rebounder = random.choice(team_stats)
            
            play = PlayByPlay(
                game_id=game.id,
                quarter=quarter,
                game_time_seconds=game_time + 1,
                time_remaining=time_remaining,
                event_type='rebound',
                description=f"{rebounder.player.name} rebound ({'offensive' if rebound_is_offensive else 'defensive'})",
                team_id=team_id if rebound_is_offensive else game.away_team_id if is_home else game.home_team_id,
                player_id=rebounder.player_id,
                home_score=home_score,
                away_score=away_score,
                details={'rebound_type': 'offensive' if rebound_is_offensive else 'defensive'}
            )
            plays.append(play)
            
        else:  # made_shot
            # Made shot
            shot_type = random.choice(['2PT', '2PT', '3PT'])  # 2:1 ratio
            points = 3 if shot_type == '3PT' else 2
            
            # Determine if assisted
            is_assisted = random.random() < 0.55  # ~55% of made shots are assisted
            assister = None
            if is_assisted:
                potential_assisters = [s for s in team_stats if s.player_id != player_stat.player_id]
                if potential_assisters:
                    assister = random.choice(potential_assisters)
            
            description = f"{player_stat.player.name} makes {shot_type} shot"
            if assister:
                description += f" (assist: {assister.player.name})"
            
            play = PlayByPlay(
                game_id=game.id,
                quarter=quarter,
                game_time_seconds=game_time,
                time_remaining=time_remaining,
                event_type='made_shot',
                description=description,
                team_id=team_id,
                player_id=player_stat.player_id,
                assist_player_id=assister.player_id if assister else None,
                home_score=home_score,
                away_score=away_score,
                details={'shot_type': shot_type, 'shot_made': True, 'points': points}
            )
            plays.append(play)
            
            # Occasionally add fouls/free throws
            if random.random() < 0.15:  # 15% chance of foul on made shot
                play = PlayByPlay(
                    game_id=game.id,
                    quarter=quarter,
                    game_time_seconds=game_time + 1,
                    time_remaining=time_remaining,
                    event_type='foul',
                    description=f"Shooting foul",
                    team_id=game.away_team_id if is_home else game.home_team_id,
                    home_score=home_score,
                    away_score=away_score,
                    details={'foul_type': 'shooting'}
                )
                plays.append(play)
        
        return plays
    
    def _format_time_remaining(self, seconds):
        """Format seconds as MM:SS"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
