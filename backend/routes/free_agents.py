from flask import Blueprint, jsonify, request
from models import Team, Player, get_session

free_agents_bp = Blueprint('free_agents', __name__)

@free_agents_bp.route('/free-agents', methods=['GET'])
def get_free_agents():
    """Get all free agents"""
    session = get_session()
    fa_team = session.query(Team).filter_by(team_type='Free Agent').first()
    
    if not fa_team:
        return jsonify([])
    
    players = session.query(Player).filter_by(team_id=fa_team.id).order_by(Player.ppg.desc()).all()
    
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'position': p.position,
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
    } for p in players])

@free_agents_bp.route('/players/<int:player_id>/sign', methods=['POST'])
def sign_player(player_id):
    """Sign a free agent to a team"""
    data = request.get_json()
    team_id = data.get('team_id')
    
    if not team_id:
        return jsonify({'error': 'team_id required'}), 400
    
    session = get_session()
    player = session.query(Player).filter_by(id=player_id).first()
    team = session.query(Team).filter_by(id=team_id).first()
    
    if not player or not team:
        return jsonify({'error': 'Player or team not found'}), 404
    
    # Check if player is a free agent
    fa_team = session.query(Team).filter_by(team_type='Free Agent').first()
    if player.team_id != fa_team.id:
        return jsonify({'error': 'Player is not a free agent'}), 400
    
    # Sign player to team
    old_team_name = player.team.name if player.team else "Free Agency"
    player.team_id = team_id
    session.commit()
    
    return jsonify({
        'message': f'{player.name} signed to {team.city} {team.name}',
        'player': player.name,
        'old_team': old_team_name,
        'new_team': f'{team.city} {team.name}'
    })

@free_agents_bp.route('/players/<int:player_id>/release', methods=['POST'])
def release_player(player_id):
    """Release a player to free agency"""
    session = get_session()
    player = session.query(Player).filter_by(id=player_id).first()
    fa_team = session.query(Team).filter_by(team_type='Free Agent').first()
    
    if not player:
        return jsonify({'error': 'Player not found'}), 404
    
    if not fa_team:
        return jsonify({'error': 'Free agent team not found'}), 404
    
    # Release player
    old_team = player.team
    player.team_id = fa_team.id
    session.commit()
    
    return jsonify({
        'message': f'{player.name} released to free agency',
        'player': player.name,
        'old_team': f'{old_team.city} {old_team.name}' if old_team else 'Unknown'
    })

@free_agents_bp.route('/players/trade', methods=['POST'])
def trade_players():
    """Trade players between two teams"""
    data = request.get_json()
    
    player_ids_team1 = data.get('player_ids_team1', [])
    player_ids_team2 = data.get('player_ids_team2', [])
    
    if not player_ids_team1 or not player_ids_team2:
        return jsonify({'error': 'Both teams must trade at least one player'}), 400
    
    session = get_session()
    
    # Get all players
    players_team1 = session.query(Player).filter(Player.id.in_(player_ids_team1)).all()
    players_team2 = session.query(Player).filter(Player.id.in_(player_ids_team2)).all()
    
    if len(players_team1) != len(player_ids_team1) or len(players_team2) != len(player_ids_team2):
        return jsonify({'error': 'One or more players not found'}), 404
    
    # Verify all team1 players are on the same team
    team1_id = players_team1[0].team_id
    if not all(p.team_id == team1_id for p in players_team1):
        return jsonify({'error': 'All team1 players must be on the same team'}), 400
    
    # Verify all team2 players are on the same team
    team2_id = players_team2[0].team_id
    if not all(p.team_id == team2_id for p in players_team2):
        return jsonify({'error': 'All team2 players must be on the same team'}), 400
    
    # Perform the trade
    for player in players_team1:
        player.team_id = team2_id
    
    for player in players_team2:
        player.team_id = team1_id
    
    session.commit()
    
    team1 = session.query(Team).filter_by(id=team1_id).first()
    team2 = session.query(Team).filter_by(id=team2_id).first()
    
    return jsonify({
        'message': 'Trade completed',
        'team1': f'{team1.city} {team1.name}',
        'team2': f'{team2.city} {team2.name}',
        'team1_receives': [p.name for p in players_team2],
        'team2_receives': [p.name for p in players_team1]
    })
