from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    abbreviation = Column(String(10), nullable=False)
    conference = Column(String(20))  # East, West, or Expansion/G-League
    division = Column(String(50))
    team_type = Column(String(20))  # NBA, Expansion, G-League
    
    players = relationship("Player", back_populates="team")
    home_games = relationship("Game", foreign_keys="Game.home_team_id", back_populates="home_team")
    away_games = relationship("Game", foreign_keys="Game.away_team_id", back_populates="away_team")

class Player(Base):
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'))
    position = Column(String(10))
    jersey_number = Column(Integer)
    height = Column(String(10))
    weight = Column(Integer)
    
    # Career averages (baseline stats)
    ppg = Column(Float, default=0.0)  # Points per game
    rpg = Column(Float, default=0.0)  # Rebounds per game
    apg = Column(Float, default=0.0)  # Assists per game
    spg = Column(Float, default=0.0)  # Steals per game
    bpg = Column(Float, default=0.0)  # Blocks per game
    fg_pct = Column(Float, default=0.0)  # Field goal percentage
    three_pt_pct = Column(Float, default=0.0)  # 3-point percentage
    ft_pct = Column(Float, default=0.0)  # Free throw percentage
    mpg = Column(Float, default=0.0)  # Minutes per game
    
    team = relationship("Team", back_populates="players")
    game_stats = relationship("PlayerGameStats", back_populates="player")

class Game(Base):
    __tablename__ = 'games'
    
    id = Column(Integer, primary_key=True)
    game_date = Column(DateTime, default=datetime.utcnow)
    home_team_id = Column(Integer, ForeignKey('teams.id'))
    away_team_id = Column(Integer, ForeignKey('teams.id'))
    series_id = Column(Integer, ForeignKey('series.id'), nullable=True)
    game_number_in_series = Column(Integer, nullable=True)  # 1-7 for playoff series
    
    # Final scores
    home_team_score = Column(Integer)
    away_team_score = Column(Integer)
    
    # Quarter scores
    home_q1 = Column(Integer, default=0)
    home_q2 = Column(Integer, default=0)
    home_q3 = Column(Integer, default=0)
    home_q4 = Column(Integer, default=0)
    away_q1 = Column(Integer, default=0)
    away_q2 = Column(Integer, default=0)
    away_q3 = Column(Integer, default=0)
    away_q4 = Column(Integer, default=0)
    
    # Input data (the actual quarter you played)
    input_quarter_number = Column(Integer)  # Which quarter was actually played (1-4)
    input_home_score = Column(Integer)  # Actual score from played quarter
    input_away_score = Column(Integer)  # Actual score from played quarter
    
    is_completed = Column(Boolean, default=False)
    
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_games")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_games")
    series = relationship("Series", back_populates="games")
    player_stats = relationship("PlayerGameStats", back_populates="game")
    play_by_play = relationship("PlayByPlay", back_populates="game", order_by="PlayByPlay.game_time_seconds")

class Series(Base):
    __tablename__ = 'series'
    
    id = Column(Integer, primary_key=True)
    tournament_round = Column(Integer)  # 1, 2, 3, 4 (Finals)
    series_number = Column(Integer)  # Which series in this round
    team1_id = Column(Integer, ForeignKey('teams.id'))
    team2_id = Column(Integer, ForeignKey('teams.id'))
    team1_wins = Column(Integer, default=0)
    team2_wins = Column(Integer, default=0)
    winner_team_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    is_completed = Column(Boolean, default=False)
    
    team1 = relationship("Team", foreign_keys=[team1_id])
    team2 = relationship("Team", foreign_keys=[team2_id])
    winner = relationship("Team", foreign_keys=[winner_team_id])
    games = relationship("Game", back_populates="series")

class PlayerGameStats(Base):
    __tablename__ = 'player_game_stats'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    player_id = Column(Integer, ForeignKey('players.id'))
    team_id = Column(Integer, ForeignKey('teams.id'))
    
    # Basic stats
    minutes_played = Column(Float, default=0.0)
    points = Column(Integer, default=0)
    rebounds = Column(Integer, default=0)
    offensive_rebounds = Column(Integer, default=0)
    defensive_rebounds = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    steals = Column(Integer, default=0)
    blocks = Column(Integer, default=0)
    turnovers = Column(Integer, default=0)
    fouls = Column(Integer, default=0)
    
    # Shooting stats
    fgm = Column(Integer, default=0)  # Field goals made
    fga = Column(Integer, default=0)  # Field goals attempted
    three_pm = Column(Integer, default=0)  # 3-pointers made
    three_pa = Column(Integer, default=0)  # 3-pointers attempted
    ftm = Column(Integer, default=0)  # Free throws made
    fta = Column(Integer, default=0)  # Free throws attempted
    
    # Advanced stats
    plus_minus = Column(Integer, default=0)
    usage_rate = Column(Float, default=0.0)
    true_shooting_pct = Column(Float, default=0.0)
    effective_fg_pct = Column(Float, default=0.0)
    per = Column(Float, default=0.0)  # Player Efficiency Rating
    
    game = relationship("Game", back_populates="player_stats")
    player = relationship("Player", back_populates="game_stats")

class PlayByPlay(Base):
    __tablename__ = 'play_by_play'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    quarter = Column(Integer)
    game_time_seconds = Column(Integer)  # Seconds elapsed in game (0-2880 for 48 min)
    time_remaining = Column(String(10))  # MM:SS format
    
    event_type = Column(String(50))  # shot, free_throw, rebound, assist, steal, block, turnover, foul, substitution
    description = Column(Text)
    
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=True)
    assist_player_id = Column(Integer, ForeignKey('players.id'), nullable=True)
    
    # Score after this play
    home_score = Column(Integer, default=0)
    away_score = Column(Integer, default=0)
    
    # Additional details (stored as JSON)
    details = Column(JSON)  # shot_type, shot_distance, shot_made, etc.
    
    game = relationship("Game", back_populates="play_by_play")

# Database initialization
def init_db(db_path='basketball_sim.db'):
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def get_session(db_path='basketball_sim.db'):
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    return Session()
