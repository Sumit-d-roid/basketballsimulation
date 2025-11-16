from flask import Blueprint, jsonify, send_file
from models import Team, Player, Game, Series, Run, get_session
from datetime import datetime
import os

backup_bp = Blueprint('backup', __name__)

@backup_bp.route('/backup/export', methods=['GET'])
def export_database_json():
    """Export database to JSON"""
    session = get_session()
    
    # Export all data
    backup_data = {
        'export_date': datetime.utcnow().isoformat(),
        'version': '1.0',
        'teams': [],
        'players': [],
        'runs': [],
        'series': [],
        'games': []
    }
    
    # Export teams
    teams = session.query(Team).all()
    for t in teams:
        backup_data['teams'].append({
            'id': t.id,
            'name': t.name,
            'city': t.city,
            'abbreviation': t.abbreviation,
            'conference': t.conference,
            'division': t.division,
            'team_type': t.team_type
        })
    
    # Export players
    players = session.query(Player).all()
    for p in players:
        backup_data['players'].append({
            'id': p.id,
            'name': p.name,
            'team_id': p.team_id,
            'position': p.position,
            'jersey_number': p.jersey_number,
            'height': p.height,
            'weight': p.weight,
            'ppg': p.ppg,
            'rpg': p.rpg,
            'apg': p.apg,
            'spg': p.spg,
            'bpg': p.bpg,
            'fg_pct': p.fg_pct,
            'three_pt_pct': p.three_pt_pct,
            'ft_pct': p.ft_pct,
            'mpg': p.mpg
        })
    
    # Export runs
    runs = session.query(Run).all()
    for r in runs:
        backup_data['runs'].append({
            'id': r.id,
            'name': r.name,
            'year': r.year,
            'created_at': r.created_at.isoformat() if r.created_at else None,
            'is_active': r.is_active,
            'is_completed': r.is_completed,
            'champion_team_id': r.champion_team_id
        })
    
    # Export series
    series_list = session.query(Series).all()
    for s in series_list:
        backup_data['series'].append({
            'id': s.id,
            'tournament_round': s.tournament_round,
            'series_number': s.series_number,
            'conference': s.conference,
            'team1_id': s.team1_id,
            'team2_id': s.team2_id,
            'team1_wins': s.team1_wins,
            'team2_wins': s.team2_wins,
            'winner_team_id': s.winner_team_id,
            'is_completed': s.is_completed,
            'run_id': s.run_id
        })
    
    # Export games
    games = session.query(Game).all()
    for g in games:
        backup_data['games'].append({
            'id': g.id,
            'game_date': g.game_date.isoformat() if g.game_date else None,
            'home_team_id': g.home_team_id,
            'away_team_id': g.away_team_id,
            'series_id': g.series_id,
            'game_number_in_series': g.game_number_in_series,
            'run_id': g.run_id,
            'home_team_score': g.home_team_score,
            'away_team_score': g.away_team_score,
            'home_q1': g.home_q1,
            'home_q2': g.home_q2,
            'home_q3': g.home_q3,
            'home_q4': g.home_q4,
            'away_q1': g.away_q1,
            'away_q2': g.away_q2,
            'away_q3': g.away_q3,
            'away_q4': g.away_q4,
            'input_quarter_number': g.input_quarter_number,
            'input_home_score': g.input_home_score,
            'input_away_score': g.input_away_score,
            'is_completed': g.is_completed
        })
    
    # Return as downloadable JSON
    response = jsonify(backup_data)
    response.headers['Content-Disposition'] = f'attachment; filename=basketball_sim_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return response

@backup_bp.route('/backup/download-db', methods=['GET'])
def download_database_file():
    """Download the SQLite database file directly"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'basketball_sim.db')
    
    if not os.path.exists(db_path):
        return jsonify({'error': 'Database file not found'}), 404
    
    return send_file(
        db_path,
        as_attachment=True,
        download_name=f'basketball_sim_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    )
