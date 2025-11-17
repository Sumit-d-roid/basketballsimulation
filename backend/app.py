from flask import Flask, request, jsonify, send_from_directory
import os
from flask_cors import CORS
from models import Team, Player, Game, Series, PlayerGameStats, PlayByPlay, Run, get_session
from game_extrapolator import GameExtrapolator
from play_by_play_generator import PlayByPlayGenerator
from tournament_manager import TournamentManager
from datetime import datetime

# Import blueprints
from routes.teams import teams_bp
from routes.free_agents import free_agents_bp
from routes.backup import backup_bp

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# CORS headers
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    response.headers['Access-Control-Allow-Origin'] = origin if origin else '*'
    response.headers['Vary'] = 'Origin'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
    return response

@app.route('/api/<path:any_path>', methods=['OPTIONS'])
def api_preflight(any_path):
    return ('', 204)

# Register blueprints
app.register_blueprint(teams_bp, url_prefix='/api')
app.register_blueprint(free_agents_bp, url_prefix='/api')
app.register_blueprint(backup_bp, url_prefix='/api')

# Initialize services
extrapolator = GameExtrapolator()
pbp_generator = PlayByPlayGenerator()
tournament_mgr = TournamentManager()

# Auto-initialize tournament
def auto_initialize_tournament():
    """Automatically create tournament bracket on startup if not exists"""
    try:
        session = get_session()
        active_run = session.query(Run).filter_by(is_active=True).first()
        
        if not active_run:
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

auto_initialize_tournament()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Basketball Simulation API is running'})

# ==================== GAME ENDPOINTS ====================

@app.route('/api/games/preview', methods=['POST'])
def preview_game():
    """Preview extrapolated game scores without creating the game"""
    data = request.json
    
    try:
        home_team_id = data['home_team_id']
        away_team_id = data['away_team_id']
        quarter_number = data['quarter_number']
        home_score = data['home_score']
        away_score = data['away_score']
        
        if quarter_number not in [1, 2, 3, 4]:
            return jsonify({'error': 'Quarter number must be 1-4'}), 400
        
        session = get_session()
        home_team = session.query(Team).filter_by(id=home_team_id).first()
        away_team = session.query(Team).filter_by(id=away_team_id).first()
        
        if not home_team or not away_team:
            return jsonify({'error': 'Invalid team IDs'}), 400
        
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
    """Create and simulate a game from quarter input"""
    data = request.json
    
    try:
        home_team_id = data['home_team_id']
        away_team_id = data['away_team_id']
        quarter_number = data['quarter_number']
        home_score = data['home_score']
        away_score = data['away_score']
        series_id = data.get('series_id')
        
        if quarter_number not in [1, 2, 3, 4]:
            return jsonify({'error': 'Quarter number must be 1-4'}), 400
        
        game = extrapolator.extrapolate_game(
            home_team_id, away_team_id, 
            quarter_number, home_score, away_score
        )
        
        if series_id:
            game.series_id = series_id
            game.game_number_in_series = len([g for g in extrapolator.session.query(Game).filter_by(series_id=series_id).all()]) + 1
            extrapolator.session.commit()
            
            winner_id = game.home_team_id if game.home_team_score > game.away_team_score else game.away_team_id
            tournament_mgr.update_series_result(series_id, winner_id)
        
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
    
    if game.series_id:
        series = session.query(Series).filter_by(id=game.series_id).first()
        if series:
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
            
            series.is_completed = False
            series.winner_team_id = None
    
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

@app.route('/api/games/<int:game_id>', methods=['DELETE'])
def delete_game(game_id):
    """Delete a game and all associated data"""
    session = get_session()
    
    try:
        game = session.query(Game).get(game_id)
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        # Delete associated play-by-play data
        session.query(PlayByPlay).filter_by(game_id=game_id).delete()
        
        # Delete associated player stats
        session.query(PlayerGameStats).filter_by(game_id=game_id).delete()
        
        # Delete associated runs data
        session.query(Run).filter_by(game_id=game_id).delete()
        
        # Delete the game
        session.delete(game)
        session.commit()
        
        return jsonify({'message': 'Game deleted successfully'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': f'Failed to delete game: {str(e)}'}), 500

@app.route('/api/games/history', methods=['GET'])
def get_game_history():
    """Get recent games with detailed info (game feed)"""
    session = get_session()
    
    run_id = request.args.get('run_id', type=int)
    limit = request.args.get('limit', type=int, default=20)
    team_id = request.args.get('team_id', type=int)
    
    query = session.query(Game).filter(Game.is_completed == True)
    
    if run_id:
        query = query.filter(Game.run_id == run_id)
    
    if team_id:
        query = query.filter(
            (Game.home_team_id == team_id) | (Game.away_team_id == team_id)
        )
    
    games = query.order_by(Game.game_date.desc()).limit(limit).all()
    
    result = []
    for g in games:
        home_won = g.home_team_score > g.away_team_score
        margin = abs(g.home_team_score - g.away_team_score)
        
        if margin <= 3:
            game_type = "Nail-biter"
        elif margin <= 10:
            game_type = "Close game"
        elif margin >= 20:
            game_type = "Blowout"
        else:
            game_type = "Competitive"
        
        result.append({
            'id': g.id,
            'date': g.game_date.isoformat(),
            'home_team': {
                'id': g.home_team.id,
                'name': f"{g.home_team.city} {g.home_team.name}",
                'abbr': g.home_team.abbreviation,
                'score': g.home_team_score,
                'won': home_won
            },
            'away_team': {
                'id': g.away_team.id,
                'name': f"{g.away_team.city} {g.away_team.name}",
                'abbr': g.away_team.abbreviation,
                'score': g.away_team_score,
                'won': not home_won
            },
            'margin': margin,
            'game_type': game_type,
            'series_info': {
                'id': g.series_id,
                'game_number': g.game_number_in_series,
                'round': g.series.tournament_round if g.series else None
            } if g.series_id else None,
            'input_quarter': {
                'number': g.input_quarter_number,
                'home_score': g.input_home_score,
                'away_score': g.input_away_score
            },
            'quarters': {
                'home': [g.home_q1, g.home_q2, g.home_q3, g.home_q4],
                'away': [g.away_q1, g.away_q2, g.away_q3, g.away_q4]
            }
        })
    
    return jsonify(result)

# ==================== TOURNAMENT ENDPOINTS ====================

@app.route('/api/tournament/initialize', methods=['POST'])
def initialize_tournament():
    """Initialize tournament bracket"""
    try:
        result = tournament_mgr.create_tournament_bracket()
        return jsonify({
            'message': 'Tournament initialized',
            'round1_series': len(result['round1_series']) if result else 0,
            'total_teams': result['total_teams'] if result else 0
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
        'team1': f"{s.team1.city} {s.team1.name}" if s.team1 else "TBD",
        'team2': f"{s.team2.city} {s.team2.name}" if s.team2 else "TBD",
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
    """Reset the current tournament"""
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
    from sqlalchemy import func
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

@app.route('/api/stats/input-performance', methods=['GET'])
def get_input_performance():
    """Get aggregated stats from user's quarter inputs"""
    session = get_session()
    run_id = request.args.get('run_id', type=int)
    
    games_query = session.query(Game).filter(Game.is_completed == True)
    if run_id:
        games_query = games_query.filter(Game.run_id == run_id)
    
    games = games_query.all()
    
    if not games:
        return jsonify({
            'total_games': 0,
            'avg_total_score': 0,
            'avg_home_score': 0,
            'avg_away_score': 0,
            'avg_point_diff': 0,
            'highest_scoring_game': None,
            'lowest_scoring_game': None,
            'closest_game': None,
            'biggest_blowout': None,
            'quarters_played': {},
            'recent_inputs': []
        })
    
    total_home = sum(g.input_home_score for g in games)
    total_away = sum(g.input_away_score for g in games)
    total_combined = total_home + total_away
    
    point_diffs = [abs(g.input_home_score - g.input_away_score) for g in games]
    
    quarter_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for g in games:
        quarter_counts[g.input_quarter_number] = quarter_counts.get(g.input_quarter_number, 0) + 1
    
    highest_game = max(games, key=lambda g: g.input_home_score + g.input_away_score)
    lowest_game = min(games, key=lambda g: g.input_home_score + g.input_away_score)
    closest_game = min(games, key=lambda g: abs(g.input_home_score - g.input_away_score))
    biggest_blowout = max(games, key=lambda g: abs(g.input_home_score - g.input_away_score))
    
    return jsonify({
        'total_games': len(games),
        'avg_total_score': round(total_combined / len(games), 1),
        'avg_home_score': round(total_home / len(games), 1),
        'avg_away_score': round(total_away / len(games), 1),
        'avg_point_diff': round(sum(point_diffs) / len(games), 1),
        'highest_scoring_game': {
            'game_id': highest_game.id,
            'home_team': f"{highest_game.home_team.city} {highest_game.home_team.name}",
            'away_team': f"{highest_game.away_team.city} {highest_game.away_team.name}",
            'score': f"{highest_game.input_home_score}-{highest_game.input_away_score}",
            'total': highest_game.input_home_score + highest_game.input_away_score
        },
        'lowest_scoring_game': {
            'game_id': lowest_game.id,
            'home_team': f"{lowest_game.home_team.city} {lowest_game.home_team.name}",
            'away_team': f"{lowest_game.away_team.city} {lowest_game.away_team.name}",
            'score': f"{lowest_game.input_home_score}-{lowest_game.input_away_score}",
            'total': lowest_game.input_home_score + lowest_game.input_away_score
        },
        'closest_game': {
            'game_id': closest_game.id,
            'home_team': f"{closest_game.home_team.city} {closest_game.home_team.name}",
            'away_team': f"{closest_game.away_team.city} {closest_game.away_team.name}",
            'score': f"{closest_game.input_home_score}-{closest_game.input_away_score}",
            'diff': abs(closest_game.input_home_score - closest_game.input_away_score)
        },
        'biggest_blowout': {
            'game_id': biggest_blowout.id,
            'home_team': f"{biggest_blowout.home_team.city} {biggest_blowout.home_team.name}",
            'away_team': f"{biggest_blowout.away_team.city} {biggest_blowout.away_team.name}",
            'score': f"{biggest_blowout.input_home_score}-{biggest_blowout.input_away_score}",
            'diff': abs(biggest_blowout.input_home_score - biggest_blowout.input_away_score)
        },
        'quarters_played': quarter_counts,
        'win_rate_by_score': {
            '20+': round(len([g for g in games if max(g.input_home_score, g.input_away_score) >= 20]) / len(games) * 100, 1),
            '25+': round(len([g for g in games if max(g.input_home_score, g.input_away_score) >= 25]) / len(games) * 100, 1),
            '30+': round(len([g for g in games if max(g.input_home_score, g.input_away_score) >= 30]) / len(games) * 100, 1)
        },
        'recent_inputs': [{
            'game_id': g.id,
            'date': g.game_date.isoformat(),
            'quarter': g.input_quarter_number,
            'home_score': g.input_home_score,
            'away_score': g.input_away_score,
            'total': g.input_home_score + g.input_away_score
        } for g in sorted(games, key=lambda x: x.game_date, reverse=True)[:10]]
    })

# ==================== RUN MANAGEMENT ENDPOINTS ====================

@app.route('/api/runs', methods=['GET'])
def get_runs():
    """Get all tournament runs/seasons"""
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
    data = request.get_json()
    
    session = get_session()
    session.query(Run).update({'is_active': False})
    
    new_run = Run(
        name=data.get('name', f"Season {data.get('year', datetime.now().year)}"),
        year=data.get('year', datetime.now().year),
        is_active=True,
        is_completed=False
    )
    session.add(new_run)
    session.commit()
    
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
    session = get_session()
    session.query(Run).update({'is_active': False})
    
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

# ==================== STATIC FRONTEND ====================

# Use absolute path from /app root
FRONTEND_BUILD_DIR = '/app/frontend/build'

# Serve static files (CSS, JS, etc.)
@app.route('/static/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(FRONTEND_BUILD_DIR, 'static', 'css'), filename)

@app.route('/static/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(FRONTEND_BUILD_DIR, 'static', 'js'), filename)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    # API routes should not be caught here
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    
    target = os.path.join(FRONTEND_BUILD_DIR, path)
    if path and os.path.exists(target) and os.path.isfile(target):
        return send_from_directory(FRONTEND_BUILD_DIR, path)
    
    # Always serve index.html for frontend routes
    index_path = os.path.join(FRONTEND_BUILD_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_BUILD_DIR, 'index.html')
    
    return jsonify({'error': 'Frontend not built. Run npm run build in frontend/'}), 404

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '1') in ('1', 'true', 'True')
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', '5000'))
    app.run(debug=debug, host=host, port=port)
