from flask import Flask, request, jsonify, send_from_directory
import os
from flask_cors import CORS
from models import Team, Player, Game, Series, PlayerGameStats, PlayByPlay, get_session
from game_extrapolator import GameExtrapolator
from play_by_play_generator import PlayByPlayGenerator
from tournament_manager import TournamentManager
from datetime import datetime

app = Flask(__name__)
# Allow CORS for all API routes; Codespaces uses unique HTTPS origins per port
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Extra safety: ensure CORS headers are always present (incl. preflight support)
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    # Echo specific Origin when provided (better for some proxies) else fallback to *
    response.headers['Access-Control-Allow-Origin'] = origin if origin else '*'
    response.headers['Vary'] = 'Origin'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
    return response

# Handle preflight explicitly for any /api/* route (some proxies require this)
@app.route('/api/<path:any_path>', methods=['OPTIONS'])
def api_preflight(any_path):
    return ('', 204)

# Initialize services
extrapolator = GameExtrapolator()
pbp_generator = PlayByPlayGenerator()
tournament_mgr = TournamentManager()

# Auto-initialize tournament if not exists
def auto_initialize_tournament():
    """Automatically create tournament bracket on startup if not exists"""
    try:
        from models import Run
        session = get_session()
        
        # Check if there's an active run
        active_run = session.query(Run).filter_by(is_active=True).first()
        
        if not active_run:
            # Create first run
            print("No active run found. Creating initial season...")
            active_run = Run(
                name=f"Season {datetime.now().year}",
                year=datetime.now().year,
                is_active=True,
                is_completed=False
            )
            session.add(active_run)
            session.commit()
            print(f"✓ Created initial run: {active_run.name}")
        
        # Check if tournament exists for active run
        existing_series = session.query(Series).filter_by(run_id=active_run.id).first()
        if not existing_series:
            print(f"No tournament found for {active_run.name}. Auto-initializing...")
            result = tournament_mgr.create_tournament_bracket(run_id=active_run.id)
            if result:
                print(f"✓ Tournament auto-initialized with {result['round1_series']} Round 1 series")
            else:
                print("⚠ Tournament initialization returned None (check team count)")
        else:
            print(f"✓ Tournament already exists for {active_run.name}")
    except Exception as e:
        print(f"⚠ Error auto-initializing tournament: {e}")

# Call auto-initialization
auto_initialize_tournament()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Basketball Simulation API is running'})

# ==================== TEAM ENDPOINTS ====================

@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Get all teams"""
    session = get_session()
    teams = session.query(Team).all()
    
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'city': t.city,
        'abbreviation': t.abbreviation,
        'conference': t.conference,
        'division': t.division,
        'team_type': t.team_type,
        'full_name': f"{t.city} {t.name}"
    } for t in teams])

@app.route('/api/teams/<int:team_id>', methods=['GET'])
def get_team(team_id):
    """Get specific team with roster"""
    session = get_session()
    team = session.query(Team).filter_by(id=team_id).first()
    
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    
    players = [{
        'id': p.id,
        'name': p.name,
        'position': p.position,
        'jersey_number': p.jersey_number,
        'height': p.height,
        'weight': p.weight,
        'ppg': p.ppg,
        'rpg': p.rpg,
        'apg': p.apg,
        'fg_pct': p.fg_pct,
        'three_pt_pct': p.three_pt_pct
    } for p in team.players]
    
    return jsonify({
        'id': team.id,
        'name': team.name,
        'city': team.city,
        'abbreviation': team.abbreviation,
        'conference': team.conference,
        'full_name': f"{team.city} {team.name}",
        'players': players
    })

# ==================== GAME ENDPOINTS ====================

@app.route('/api/games/preview', methods=['POST'])
def preview_game():
    """
    Preview extrapolated game scores without creating the game.
    Body: {
        "home_team_id": 1,
        "away_team_id": 2,
        "quarter_number": 1,
        "home_score": 28,
        "away_score": 25
    }
    """
    data = request.json
    
    try:
        home_team_id = data['home_team_id']
        away_team_id = data['away_team_id']
        quarter_number = data['quarter_number']
        home_score = data['home_score']
        away_score = data['away_score']
        
        # Validate quarter number
        if quarter_number not in [1, 2, 3, 4]:
            return jsonify({'error': 'Quarter number must be 1-4'}), 400
        
        # Get team names
        session = get_session()
        home_team = session.query(Team).filter_by(id=home_team_id).first()
        away_team = session.query(Team).filter_by(id=away_team_id).first()
        
        if not home_team or not away_team:
            return jsonify({'error': 'Invalid team IDs'}), 400
        
        # Calculate base rates and generate quarters preview
        home_base_rate = home_score / 12
        away_base_rate = away_score / 12
        
        quarters_data = extrapolator._generate_all_quarters(
            home_base_rate, away_base_rate, quarter_number,
            home_score, away_score
        )
        
        home_total = sum(quarters_data['home'])
        away_total = sum(quarters_data['away'])
        
        return jsonify({
            'home_team': f"{home_team.city} {home_team.name}",
            'away_team': f"{away_team.city} {away_team.name}",
            'quarters': {
                'home': quarters_data['home'],
                'away': quarters_data['away']
            },
            'final_score': {
                'home': home_total,
                'away': away_total
            },
            'winner': f"{home_team.city} {home_team.name}" if home_total > away_total else f"{away_team.city} {away_team.name}"
        })
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/games/create', methods=['POST'])
def create_game():
    """
    Create and simulate a game from quarter input.
    Body: {
        "home_team_id": 1,
        "away_team_id": 2,
        "quarter_number": 1,
        "home_score": 28,
        "away_score": 25,
        "series_id": null (optional)
    }
    """
    data = request.json
    
    try:
        home_team_id = data['home_team_id']
        away_team_id = data['away_team_id']
        quarter_number = data['quarter_number']
        home_score = data['home_score']
        away_score = data['away_score']
        series_id = data.get('series_id')
        
        # Validate quarter number
        if quarter_number not in [1, 2, 3, 4]:
            return jsonify({'error': 'Quarter number must be 1-4'}), 400
        
        # Create game with extrapolation
        game = extrapolator.extrapolate_game(
            home_team_id, away_team_id, 
            quarter_number, home_score, away_score
        )
        
        # Link to series if provided
        if series_id:
            game.series_id = series_id
            game.game_number_in_series = len([g for g in extrapolator.session.query(Game).filter_by(series_id=series_id).all()]) + 1
            extrapolator.session.commit()
            
            # Update series standings
            winner_id = game.home_team_id if game.home_team_score > game.away_team_score else game.away_team_id
            tournament_mgr.update_series_result(series_id, winner_id)
        
        # Generate play-by-play
        pbp_generator.generate_play_by_play(game)
        
        return jsonify({
            'game_id': game.id,
            'message': 'Game created and simulated successfully',
            'final_score': {
                'home': game.home_team_score,
                'away': game.away_team_score
            }
        })
        
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/games/<int:game_id>', methods=['GET'])
def get_game(game_id):
    """Get complete game details"""
    session = get_session()
    game = session.query(Game).filter_by(id=game_id).first()
    
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    # Get box scores
    home_stats = session.query(PlayerGameStats).filter_by(
        game_id=game_id, team_id=game.home_team_id
    ).all()
    
    away_stats = session.query(PlayerGameStats).filter_by(
        game_id=game_id, team_id=game.away_team_id
    ).all()
    
    def format_player_stats(stats):
        return [{
            'player_name': s.player.name,
            'minutes': s.minutes_played,
            'points': s.points,
            'rebounds': s.rebounds,
            'assists': s.assists,
            'steals': s.steals,
            'blocks': s.blocks,
            'fg': f"{s.fgm}/{s.fga}",
            'three_pt': f"{s.three_pm}/{s.three_pa}",
            'ft': f"{s.ftm}/{s.fta}",
            'turnovers': s.turnovers,
            'fouls': s.fouls,
            'plus_minus': s.plus_minus,
            'ts_pct': s.true_shooting_pct,
            'per': s.per
        } for s in stats]
    
    return jsonify({
        'id': game.id,
        'date': game.game_date.isoformat(),
        'home_team': {
            'id': game.home_team.id,
            'name': f"{game.home_team.city} {game.home_team.name}",
            'score': game.home_team_score,
            'quarter_scores': [game.home_q1, game.home_q2, game.home_q3, game.home_q4]
        },
        'away_team': {
            'id': game.away_team.id,
            'name': f"{game.away_team.city} {game.away_team.name}",
            'score': game.away_team_score,
            'quarter_scores': [game.away_q1, game.away_q2, game.away_q3, game.away_q4]
        },
        'input_data': {
            'quarter': game.input_quarter_number,
            'home_score': game.input_home_score,
            'away_score': game.input_away_score
        },
        'box_score': {
            'home': format_player_stats(home_stats),
            'away': format_player_stats(away_stats)
        }
    })

@app.route('/api/games/<int:game_id>/playbyplay', methods=['GET'])
def get_play_by_play(game_id):
    """Get play-by-play for a game"""
    session = get_session()
    plays = session.query(PlayByPlay).filter_by(game_id=game_id).order_by(
        PlayByPlay.game_time_seconds
    ).all()
    
    if not plays:
        return jsonify({'error': 'No play-by-play data found'}), 404
    
    return jsonify([{
        'id': p.id,
        'quarter': p.quarter,
        'time': p.time_remaining,
        'event_type': p.event_type,
        'description': p.description,
        'home_score': p.home_score,
        'away_score': p.away_score,
        'details': p.details
    } for p in plays])

@app.route('/api/games/<int:game_id>', methods=['DELETE'])
def delete_game(game_id):
    """Delete a game and revert series wins"""
    session = get_session()
    game = session.query(Game).filter_by(id=game_id).first()
    
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    # Revert series wins if game was part of a series
    if game.series_id:
        series = session.query(Series).filter_by(id=game.series_id).first()
        if series:
            # Decrease win count for the team that won this game
            if game.home_team_score > game.away_team_score:
                if series.team1_id == game.home_team_id:
                    series.team1_wins = max(0, series.team1_wins - 1)
                else:
                    series.team2_wins = max(0, series.team2_wins - 1)
            else:
                if series.team1_id == game.away_team_id:
                    series.team1_wins = max(0, series.team1_wins - 1)
                else:
                    series.team2_wins = max(0, series.team2_wins - 1)
            
            # Reset series completion status
            series.is_completed = False
            series.winner_team_id = None
    
    # Delete associated records
    session.query(PlayerGameStats).filter_by(game_id=game_id).delete()
    session.query(PlayByPlay).filter_by(game_id=game_id).delete()
    session.delete(game)
    session.commit()
    
    return jsonify({'message': 'Game deleted successfully'})

@app.route('/api/games', methods=['GET'])
def get_all_games():
    """Get all games"""
    session = get_session()
    games = session.query(Game).order_by(Game.game_date.desc()).all()
    
    return jsonify([{
        'id': g.id,
        'date': g.game_date.isoformat(),
        'home_team': f"{g.home_team.city} {g.home_team.name}",
        'away_team': f"{g.away_team.city} {g.away_team.name}",
        'final_score': f"{g.home_team_score} - {g.away_team_score}",
        'series_id': g.series_id
    } for g in games])

# ==================== TOURNAMENT ENDPOINTS ====================

@app.route('/api/tournament/initialize', methods=['POST'])
def initialize_tournament():
    """Initialize tournament bracket"""
    try:
        result = tournament_mgr.create_tournament_bracket()
        return jsonify({
            'message': 'Tournament initialized',
            'round1_series': len(result['round1_series']),
            'total_teams': result['total_teams']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tournament/overview', methods=['GET'])
def get_tournament_overview():
    """Get complete tournament overview"""
    rounds = tournament_mgr.get_tournament_overview()
    
    result = {}
    for round_num, series_list in rounds.items():
        round_name = {
            1: 'Round 1 (Round of 32)',
            2: 'Round 2 (Sweet 16)',
            3: 'Round 3 (Elite 8)',
            4: 'Conference Finals',
            5: 'Finals'
        }.get(round_num, f'Round {round_num}')
        
        result[round_name] = [{
            'id': s.id,
            'team1': f"{s.team1.city} {s.team1.name}",
            'team2': f"{s.team2.city} {s.team2.name}",
            'score': f"{s.team1_wins} - {s.team2_wins}",
            'is_completed': s.is_completed,
            'winner': f"{s.winner.city} {s.winner.name}" if s.winner else None
        } for s in series_list]
    
    return jsonify(result)

@app.route('/api/tournament/series/<int:series_id>', methods=['GET'])
def get_series(series_id):
    """Get detailed series information"""
    status = tournament_mgr.get_series_status(series_id)
    
    if not status:
        return jsonify({'error': 'Series not found'}), 404
    
    series = status['series']
    return jsonify({
        'id': series.id,
        'round': series.tournament_round,
        'team1': {
            'id': status['team1'].id,
            'name': f"{status['team1'].city} {status['team1'].name}",
            'wins': status['team1_wins']
        },
        'team2': {
            'id': status['team2'].id,
            'name': f"{status['team2'].city} {status['team2'].name}",
            'wins': status['team2_wins']
        },
        'games_played': status['games_played'],
        'is_completed': status['is_completed'],
        'winner': f"{status['winner'].city} {status['winner'].name}" if status['winner'] else None
    })

@app.route('/api/tournament/active-series', methods=['GET'])
def get_active_series():
    """Get all active (incomplete) series"""
    series_list = tournament_mgr.get_current_series()
    
    return jsonify([{
        'id': s.id,
        'round': s.tournament_round,
        'team1': f"{s.team1.city} {s.team1.name}",
        'team2': f"{s.team2.city} {s.team2.name}",
        'score': f"{s.team1_wins} - {s.team2_wins}"
    } for s in series_list])

@app.route('/api/tournament/advance-round/<int:round_number>', methods=['POST'])
def advance_round(round_number):
    """Create next round matchups after current round completes"""
    try:
        next_series = tournament_mgr.create_next_round(round_number)
        return jsonify({
            'message': f'Round {round_number + 1} created',
            'matchups': len(next_series)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tournament/reset', methods=['POST'])
def reset_tournament():
    """Reset the current tournament (delete all series/games, keep teams/players)"""
    try:
        data = request.get_json() or {}
        run_id = data.get('run_id')
        result = tournament_mgr.reset_tournament(run_id=run_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tournament/series/<int:series_id>/games', methods=['GET'])
def get_series_games(series_id):
    """Get all games for a specific series"""
    session = get_session()
    games = session.query(Game).filter_by(series_id=series_id).order_by(Game.game_date).all()
    
    return jsonify([{
        'id': g.id,
        'game_number': g.game_number_in_series,
        'date': g.game_date.isoformat(),
        'home_team': f"{g.home_team.city} {g.home_team.name}",
        'away_team': f"{g.away_team.city} {g.away_team.name}",
        'home_score': g.home_team_score,
        'away_score': g.away_team_score,
        'winner': f"{g.home_team.city} {g.home_team.name}" if g.home_team_score > g.away_team_score else f"{g.away_team.city} {g.away_team.name}",
        'quarters': {
            'home': [g.home_q1, g.home_q2, g.home_q3, g.home_q4],
            'away': [g.away_q1, g.away_q2, g.away_q3, g.away_q4]
        }
    } for g in games])

# ==================== STATS ENDPOINTS ====================

@app.route('/api/stats/leaders', methods=['GET'])
def get_stat_leaders():
    """Get league leaders in various statistical categories"""
    from models import Run
    session = get_session()
    
    # Get optional run_id filter (defaults to active run)
    run_id = request.args.get('run_id', type=int)
    season_filter = request.args.get('season', 'current')  # 'current' or 'all'
    
    # Determine which run(s) to query
    if season_filter == 'all':
        run_filter = None  # Don't filter by run
    elif run_id:
        run_filter = run_id
    else:
        # Default to active run
        active_run = session.query(Run).filter_by(is_active=True).first()
        run_filter = active_run.id if active_run else None
    
    # Get all players with their aggregate stats from games played
    from sqlalchemy import func
    
    # Base query builder
    def build_leader_query(stat_field, label):
        query = session.query(
            Player.id,
            Player.name,
            Team.city,
            Team.name.label('team_name'),
            func.avg(stat_field).label(label),
            func.count(PlayerGameStats.id).label('games_played')
        ).select_from(Player)\
         .join(PlayerGameStats, Player.id == PlayerGameStats.player_id)\
         .join(Team, Player.team_id == Team.id)
        
        # Add run filter if specified
        if run_filter:
            query = query.join(Game, PlayerGameStats.game_id == Game.id)\
                         .filter(Game.run_id == run_filter)
        
        return query.group_by(Player.id, Player.name, Team.city, Team.name)\
                    .having(func.count(PlayerGameStats.id) >= 1)\
                    .order_by(func.avg(stat_field).desc()).limit(10).all()
    
    # Points leaders
    points_leaders = build_leader_query(PlayerGameStats.points, 'ppg')
    
    # Rebounds leaders
    rebounds_leaders = build_leader_query(PlayerGameStats.rebounds, 'rpg')
    
    # Assists leaders
    assists_leaders = build_leader_query(PlayerGameStats.assists, 'apg')
    
    return jsonify({
        'scoring_leaders': [{
            'rank': i + 1,
            'player_id': p.id,
            'name': p.name,
            'team': f"{p.city} {p.team_name}",
            'ppg': round(p.ppg, 1),
            'games': p.games_played
        } for i, p in enumerate(points_leaders)],
        'rebounding_leaders': [{
            'rank': i + 1,
            'player_id': p.id,
            'name': p.name,
            'team': f"{p.city} {p.team_name}",
            'rpg': round(p.rpg, 1),
            'games': p.games_played
        } for i, p in enumerate(rebounds_leaders)],
        'assists_leaders': [{
            'rank': i + 1,
            'player_id': p.id,
            'name': p.name,
            'team': f"{p.city} {p.team_name}",
            'apg': round(p.apg, 1),
            'games': p.games_played
        } for i, p in enumerate(assists_leaders)]
    })

@app.route('/api/stats/player/<int:player_id>', methods=['GET'])
def get_player_stats(player_id):
    """Get all game stats for a player"""
    session = get_session()
    player = session.query(Player).filter_by(id=player_id).first()
    
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    stats = session.query(PlayerGameStats).filter_by(player_id=player_id).all()
    
    return jsonify({
        'player': {
            'id': player.id,
            'name': player.name,
            'team': f"{player.team.city} {player.team.name}",
            'position': player.position
        },
        'career_averages': {
            'ppg': player.ppg,
            'rpg': player.rpg,
            'apg': player.apg,
            'fg_pct': player.fg_pct
        },
        'games': [{
            'game_id': s.game_id,
            'date': s.game.game_date.isoformat(),
            'points': s.points,
            'rebounds': s.rebounds,
            'assists': s.assists,
            'minutes': s.minutes_played,
            'fg': f"{s.fgm}/{s.fga}",
            'plus_minus': s.plus_minus
        } for s in stats]
    })

@app.route('/api/stats/teams', methods=['GET'])
def get_team_stats():
    """Get statistics for all teams in current or specified run"""
    from models import Run
    session = get_session()
    
    # Get optional run_id filter (defaults to active run)
    run_id = request.args.get('run_id', type=int)
    season_filter = request.args.get('season', 'current')
    
    # Determine which run(s) to query
    if season_filter == 'all':
        run_filter = None
    elif run_id:
        run_filter = run_id
    else:
        active_run = session.query(Run).filter_by(is_active=True).first()
        run_filter = active_run.id if active_run else None
    
    teams = session.query(Team).all()
    team_stats = []
    
    from sqlalchemy import func, case
    
    for team in teams:
        # Build query with optional run filter
        home_games_query = session.query(Game).filter(Game.home_team_id == team.id)
        away_games_query = session.query(Game).filter(Game.away_team_id == team.id)
        
        if run_filter:
            home_games_query = home_games_query.filter(Game.run_id == run_filter)
            away_games_query = away_games_query.filter(Game.run_id == run_filter)
        
        home_games = home_games_query.all()
        away_games = away_games_query.all()
        
        wins = sum(1 for g in home_games if g.home_team_score > g.away_team_score)
        wins += sum(1 for g in away_games if g.away_team_score > g.home_team_score)
        
        losses = sum(1 for g in home_games if g.home_team_score < g.away_team_score)
        losses += sum(1 for g in away_games if g.away_team_score < g.home_team_score)
        
        games_played = len(home_games) + len(away_games)
        
        if games_played == 0:
            continue
        
        points_scored = sum(g.home_team_score for g in home_games) + sum(g.away_team_score for g in away_games)
        points_allowed = sum(g.away_team_score for g in home_games) + sum(g.home_team_score for g in away_games)
        
        team_stats.append({
            'team_id': team.id,
            'team': f"{team.city} {team.name}",
            'games_played': games_played,
            'wins': wins,
            'losses': losses,
            'win_pct': round(wins / games_played, 3) if games_played > 0 else 0,
            'ppg': round(points_scored / games_played, 1),
            'opp_ppg': round(points_allowed / games_played, 1),
            'point_diff': round((points_scored - points_allowed) / games_played, 1)
        })
    
    # Sort by wins descending
    team_stats.sort(key=lambda x: (x['wins'], x['point_diff']), reverse=True)
    
    return jsonify(team_stats)

@app.route('/api/stats/head-to-head', methods=['GET'])
def get_head_to_head():
    """Get head-to-head record between two teams across all games"""
    team1_id = request.args.get('team1_id', type=int)
    team2_id = request.args.get('team2_id', type=int)
    
    if not team1_id or not team2_id:
        return jsonify({'error': 'Both team1_id and team2_id required'}), 400
    
    session = get_session()
    team1 = session.query(Team).filter_by(id=team1_id).first()
    team2 = session.query(Team).filter_by(id=team2_id).first()
    
    if not team1 or not team2:
        return jsonify({'error': 'Invalid team IDs'}), 404
    
    # Get all games between these teams
    games = session.query(Game).filter(
        ((Game.home_team_id == team1_id) & (Game.away_team_id == team2_id)) |
        ((Game.home_team_id == team2_id) & (Game.away_team_id == team1_id))
    ).all()
    
    team1_wins = 0
    team2_wins = 0
    game_history = []
    
    for game in games:
        if game.home_team_id == team1_id:
            team1_score = game.home_team_score
            team2_score = game.away_team_score
            if team1_score > team2_score:
                team1_wins += 1
            else:
                team2_wins += 1
        else:
            team1_score = game.away_team_score
            team2_score = game.home_team_score
            if team1_score > team2_score:
                team1_wins += 1
            else:
                team2_wins += 1
        
        game_history.append({
            'game_id': game.id,
            'date': game.game_date.isoformat(),
            'team1_score': team1_score,
            'team2_score': team2_score,
            'winner': f"{team1.city} {team1.name}" if team1_score > team2_score else f"{team2.city} {team2.name}"
        })
    
    return jsonify({
        'team1': f"{team1.city} {team1.name}",
        'team2': f"{team2.city} {team2.name}",
        'team1_wins': team1_wins,
        'team2_wins': team2_wins,
        'total_games': len(games),
        'game_history': game_history
    })

# ==================== RUN MANAGEMENT ENDPOINTS ====================

@app.route('/api/runs', methods=['GET'])
def get_runs():
    """Get all tournament runs/seasons"""
    from models import Run
    session = get_session()
    runs = session.query(Run).order_by(Run.year.desc()).all()
    
    return jsonify([{
        'id': r.id,
        'name': r.name,
        'year': r.year,
        'created_at': r.created_at.isoformat() if r.created_at else None,
        'is_active': r.is_active,
        'is_completed': r.is_completed,
        'champion': f"{r.champion.city} {r.champion.name}" if r.champion else None
    } for r in runs])

@app.route('/api/runs', methods=['POST'])
def create_run():
    """Create a new tournament run/season"""
    from models import Run
    data = request.get_json()
    
    session = get_session()
    
    # Deactivate all existing runs
    session.query(Run).update({'is_active': False})
    
    # Create new run
    new_run = Run(
        name=data.get('name', f"Season {data.get('year', datetime.now().year)}"),
        year=data.get('year', datetime.now().year),
        is_active=True,
        is_completed=False
    )
    session.add(new_run)
    session.commit()
    
    # Initialize tournament for this run
    result = tournament_mgr.create_tournament_bracket(run_id=new_run.id)
    
    return jsonify({
        'id': new_run.id,
        'name': new_run.name,
        'year': new_run.year,
        'tournament_created': result is not None
    })

@app.route('/api/runs/<int:run_id>/activate', methods=['PUT'])
def activate_run(run_id):
    """Switch to a different run/season"""
    from models import Run
    session = get_session()
    
    # Deactivate all runs
    session.query(Run).update({'is_active': False})
    
    # Activate selected run
    run = session.query(Run).filter_by(id=run_id).first()
    if not run:
        return jsonify({'error': 'Run not found'}), 404
    
    run.is_active = True
    session.commit()
    
    return jsonify({
        'id': run.id,
        'name': run.name,
        'is_active': True
    })

@app.route('/api/runs/active', methods=['GET'])
def get_active_run():
    """Get currently active run"""
    from models import Run
    session = get_session()
    run = session.query(Run).filter_by(is_active=True).first()
    
    if not run:
        return jsonify({'error': 'No active run'}), 404
    
    return jsonify({
        'id': run.id,
        'name': run.name,
        'year': run.year,
        'is_completed': run.is_completed,
        'champion': f"{run.champion.city} {run.champion.name}" if run.champion else None
    })

"""
Static frontend serving must be defined before app.run
so routes are registered prior to server start.
"""
# ==================== STATIC FRONTEND (BUILD) ====================
# Serve the React build for same-origin usage when available
FRONTEND_BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build'))

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    # If a real file exists (css/js/assets), serve it; else return index.html for SPA routing
    target = os.path.join(FRONTEND_BUILD_DIR, path)
    if path and os.path.exists(target) and os.path.isfile(target):
        return send_from_directory(FRONTEND_BUILD_DIR, path)
    index_path = os.path.join(FRONTEND_BUILD_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_BUILD_DIR, 'index.html')
    return jsonify({'error': 'Frontend not built. Run npm run build in frontend/'}), 404

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '1') in ('1', 'true', 'True')
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', '5000'))
    app.run(debug=debug, host=host, port=port)
