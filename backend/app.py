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
        session = get_session()
        existing_series = session.query(Series).first()
        if not existing_series:
            print("No tournament found. Auto-initializing...")
            result = tournament_mgr.create_tournament_bracket()
            if result:
                print(f"✓ Tournament auto-initialized with {result['round1_series']} Round 1 series")
            else:
                print("⚠ Tournament initialization returned None (check team count)")
        else:
            print("✓ Tournament already exists")
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

# ==================== STATS ENDPOINTS ====================

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
