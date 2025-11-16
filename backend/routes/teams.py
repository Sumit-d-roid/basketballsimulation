from flask import Blueprint, jsonify
from models import Team, Player, get_session

teams_bp = Blueprint('teams', __name__)

@teams_bp.route('/teams', methods=['GET'])
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

@teams_bp.route('/teams/<int:team_id>', methods=['GET'])
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
