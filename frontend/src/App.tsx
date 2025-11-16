import React, { useState, useEffect } from 'react';
import './App.css';
import * as api from './api';

interface Series {
  id: number;
  round: number;
  team1: string;
  team2: string;
  score: string;
  is_completed?: boolean;
  winner?: string;
}

function App() {
  const [currentView, setCurrentView] = useState('create-game');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Game creation form
  const [quarterNumber, setQuarterNumber] = useState('1');
  const [homeScore, setHomeScore] = useState('');
  const [awayScore, setAwayScore] = useState('');
  const [selectedSeries, setSelectedSeries] = useState('');
  
  // Results
  const [activeSeries, setActiveSeries] = useState<Series[]>([]);
  const [tournamentData, setTournamentData] = useState<any>(null);
  const [games, setGames] = useState<any[]>([]);
  const [selectedGame, setSelectedGame] = useState<any>(null);
  const [playByPlay, setPlayByPlay] = useState<any[]>([]);

  useEffect(() => {
    // Load active series on mount
    loadActiveSeries();
  }, []);

  const loadActiveSeries = async () => {
    try {
      const response = await api.getActiveSeries();
      setActiveSeries(response.data);
    } catch (err: any) {
      console.error('Failed to load active series:', err.message);
    }
  };

  const loadTournament = async () => {
    try {
      setLoading(true);
      const response = await api.getTournamentOverview();
      setTournamentData(response.data);
      setLoading(false);
    } catch (err: any) {
      setError('Failed to load tournament: ' + err.message);
      setLoading(false);
    }
  };

  const loadGames = async () => {
    try {
      setLoading(true);
      const response = await api.getGames();
      setGames(response.data);
      setLoading(false);
    } catch (err: any) {
      setError('Failed to load games: ' + err.message);
      setLoading(false);
    }
  };

  const handleCreateGame = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      // Get series details to extract team IDs
      if (!selectedSeries) {
        setError('Please select a series first');
        setLoading(false);
        return;
      }

      const seriesResponse = await api.getSeries(parseInt(selectedSeries));
      const seriesData = seriesResponse.data;

      const response = await api.createGame({
        home_team_id: seriesData.team1.id,
        away_team_id: seriesData.team2.id,
        quarter_number: parseInt(quarterNumber),
        home_score: parseInt(homeScore),
        away_score: parseInt(awayScore),
        series_id: parseInt(selectedSeries)
      });

      setSuccess('Game created and simulated successfully!');
      
      // Load the full game details
      const gameDetails = await api.getGame(response.data.game_id);
      setSelectedGame(gameDetails.data);
      
      // Reload active series to update scores
      await loadActiveSeries();
      
      setLoading(false);
      
      // Reset form
      setHomeScore('');
      setAwayScore('');
    } catch (err: any) {
      setError('Failed to create game: ' + (err.response?.data?.error || err.message));
      setLoading(false);
    }
  };

  const handleInitTournament = async () => {
    try {
      setLoading(true);
      await api.initializeTournament();
      setSuccess('Tournament initialized! Check the Tournament view.');
      await loadActiveSeries();
      setLoading(false);
    } catch (err: any) {
      setError('Failed to initialize tournament: ' + (err.response?.data?.error || err.message));
      setLoading(false);
    }
  };

  const handleViewGame = async (gameId: number) => {
    try {
      setLoading(true);
      const response = await api.getGame(gameId);
      setSelectedGame(response.data);
      
      // Load play-by-play
      const pbpResponse = await api.getPlayByPlay(gameId);
      setPlayByPlay(pbpResponse.data);
      
      setCurrentView('game-details');
      setLoading(false);
    } catch (err: any) {
      setError('Failed to load game: ' + err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentView === 'tournament') {
      loadTournament();
    } else if (currentView === 'games') {
      loadGames();
    } else if (currentView === 'create-game') {
      loadActiveSeries();
    }
  }, [currentView]);

  return (
    <div className="app">
      <div className="header">
        <h1>🏀 Basketball Simulation</h1>
        <p>32-Team Tournament • Best of 7 Series • Real NBA Rosters</p>
        
        <div className="nav">
          <button 
            className={currentView === 'create-game' ? 'active' : ''}
            onClick={() => setCurrentView('create-game')}
          >
            Create Game
          </button>
          <button 
            className={currentView === 'games' ? 'active' : ''}
            onClick={() => setCurrentView('games')}
          >
            All Games
          </button>
          <button 
            className={currentView === 'tournament' ? 'active' : ''}
            onClick={() => setCurrentView('tournament')}
          >
            Tournament Bracket
          </button>
        </div>
      </div>

      {error && <div className="card error">{error}</div>}
      {success && <div className="card success">{success}</div>}

      {currentView === 'create-game' && (
        <div className="card">
          <h2>Enter Game Score</h2>
          <p style={{ color: '#718096', marginBottom: '20px' }}>
            Select an active series below and input the score from ONE quarter you played. The system will extrapolate a full 48-minute game!
          </p>

          {activeSeries.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <p style={{ color: '#718096', marginBottom: '20px' }}>No active series found. Tournament may not be initialized.</p>
              <button 
                onClick={handleInitTournament} 
                className="btn-primary"
              >
                Initialize Tournament
              </button>
            </div>
          ) : (
            <>
              <div style={{ marginBottom: '30px' }}>
                <h3 style={{ marginBottom: '15px' }}>Active Series (Round {activeSeries[0]?.round || 1})</h3>
                <div style={{ display: 'grid', gap: '10px', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' }}>
                  {activeSeries.map(series => (
                    <div 
                      key={series.id}
                      onClick={() => {
                        setSelectedSeries(series.id.toString());
                      }}
                      style={{
                        padding: '15px',
                        border: selectedSeries === series.id.toString() ? '2px solid #3182ce' : '1px solid #e2e8f0',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        backgroundColor: selectedSeries === series.id.toString() ? '#ebf8ff' : 'white'
                      }}
                    >
                      <div style={{ fontWeight: '600', fontSize: '14px' }}>{series.team1}</div>
                      <div style={{ textAlign: 'center', padding: '8px 0', color: '#718096' }}>vs</div>
                      <div style={{ fontWeight: '600', fontSize: '14px' }}>{series.team2}</div>
                      <div style={{ textAlign: 'center', marginTop: '8px', color: '#3182ce', fontSize: '16px', fontWeight: '700' }}>
                        {series.score}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {selectedSeries && (
                <form onSubmit={handleCreateGame}>
                  <div style={{ backgroundColor: '#f7fafc', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
                    <h3 style={{ marginBottom: '15px' }}>Selected Series</h3>
                    <p style={{ fontSize: '18px', fontWeight: '600' }}>
                      {activeSeries.find(s => s.id.toString() === selectedSeries)?.team1} vs {activeSeries.find(s => s.id.toString() === selectedSeries)?.team2}
                    </p>
                  </div>

            <div className="form-group">
              <label>Which Quarter Did You Play?</label>
              <select value={quarterNumber} onChange={(e) => setQuarterNumber(e.target.value)} required>
                <option value="1">1st Quarter</option>
                <option value="2">2nd Quarter</option>
                <option value="3">3rd Quarter</option>
                <option value="4">4th Quarter</option>
              </select>
            </div>

            <div className="form-group">
              <label>Score in that Quarter</label>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '10px', alignItems: 'center' }}>
                <div>
                  <label style={{ fontSize: '0.9rem', color: '#718096' }}>
                    {activeSeries.find(s => s.id.toString() === selectedSeries)?.team1.split(' ').pop()} (Home)
                  </label>
                  <input 
                    type="number" 
                    value={homeScore} 
                    onChange={(e) => setHomeScore(e.target.value)}
                    placeholder="28"
                    required
                    min="0"
                    style={{ width: '100%' }}
                  />
                </div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#718096' }}>-</div>
                <div>
                  <label style={{ fontSize: '0.9rem', color: '#718096' }}>
                    {activeSeries.find(s => s.id.toString() === selectedSeries)?.team2.split(' ').pop()} (Away)
                  </label>
                  <input 
                    type="number" 
                    value={awayScore} 
                    onChange={(e) => setAwayScore(e.target.value)}
                    placeholder="25"
                    required
                    min="0"
                    style={{ width: '100%' }}
                  />
                </div>
              </div>
            </div>

            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Simulating Full Game...' : 'Simulate Full 48-Minute Game'}
            </button>
          </form>
              )}
            </>
          )}

          {selectedGame && (
            <div className="game-result">
              <h3>Game Result</h3>
              <div className="score-display">
                <div className="team-score">
                  <div>{selectedGame.home_team.name}</div>
                  <div className="score">{selectedGame.home_team.score}</div>
                  <div style={{ fontSize: '0.9rem', color: '#718096' }}>
                    Q: {selectedGame.home_team.quarter_scores.join('-')}
                  </div>
                </div>
                <div className="vs">VS</div>
                <div className="team-score">
                  <div>{selectedGame.away_team.name}</div>
                  <div className="score">{selectedGame.away_team.score}</div>
                  <div style={{ fontSize: '0.9rem', color: '#718096' }}>
                    Q: {selectedGame.away_team.quarter_scores.join('-')}
                  </div>
                </div>
              </div>
              
              <button 
                onClick={() => handleViewGame(selectedGame.id)} 
                className="btn-primary"
                style={{ marginTop: '20px' }}
              >
                View Full Box Score & Play-by-Play
              </button>
            </div>
          )}
        </div>
      )}

      {currentView === 'games' && (
        <div className="card">
          <h2>All Games</h2>
          {loading ? (
            <div className="loading">Loading games...</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Matchup</th>
                  <th>Final Score</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {games.map(game => (
                  <tr key={game.id}>
                    <td>{new Date(game.date).toLocaleDateString()}</td>
                    <td>{game.home_team} vs {game.away_team}</td>
                    <td>{game.final_score}</td>
                    <td>
                      <button 
                        onClick={() => handleViewGame(game.id)}
                        style={{ padding: '8px 16px', cursor: 'pointer' }}
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {currentView === 'game-details' && selectedGame && (
        <div>
          <div className="card">
            <button onClick={() => setCurrentView('games')} style={{ marginBottom: '20px' }}>
              ← Back to Games
            </button>
            
            <h2>Game Details</h2>
            <div className="score-display">
              <div className="team-score">
                <div>{selectedGame.home_team.name}</div>
                <div className="score">{selectedGame.home_team.score}</div>
                <div style={{ fontSize: '0.9rem', color: '#718096' }}>
                  Quarters: {selectedGame.home_team.quarter_scores.join('-')}
                </div>
              </div>
              <div className="vs">VS</div>
              <div className="team-score">
                <div>{selectedGame.away_team.name}</div>
                <div className="score">{selectedGame.away_team.score}</div>
                <div style={{ fontSize: '0.9rem', color: '#718096' }}>
                  Quarters: {selectedGame.away_team.quarter_scores.join('-')}
                </div>
              </div>
            </div>

            <div style={{ background: '#f7fafc', padding: '15px', borderRadius: '8px', marginTop: '20px' }}>
              <strong>Input Data:</strong> Quarter {selectedGame.input_data.quarter} - 
              {selectedGame.home_team.name}: {selectedGame.input_data.home_score}, 
              {selectedGame.away_team.name}: {selectedGame.input_data.away_score}
            </div>
          </div>

          <div className="card">
            <h3>{selectedGame.home_team.name} Box Score</h3>
            <table>
              <thead>
                <tr>
                  <th>Player</th>
                  <th>MIN</th>
                  <th>PTS</th>
                  <th>REB</th>
                  <th>AST</th>
                  <th>STL</th>
                  <th>BLK</th>
                  <th>FG</th>
                  <th>3PT</th>
                  <th>FT</th>
                  <th>+/-</th>
                </tr>
              </thead>
              <tbody>
                {selectedGame.box_score.home.map((player: any, idx: number) => (
                  <tr key={idx}>
                    <td><strong>{player.player_name}</strong></td>
                    <td>{player.minutes}</td>
                    <td>{player.points}</td>
                    <td>{player.rebounds}</td>
                    <td>{player.assists}</td>
                    <td>{player.steals}</td>
                    <td>{player.blocks}</td>
                    <td>{player.fg}</td>
                    <td>{player.three_pt}</td>
                    <td>{player.ft}</td>
                    <td>{player.plus_minus}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="card">
            <h3>{selectedGame.away_team.name} Box Score</h3>
            <table>
              <thead>
                <tr>
                  <th>Player</th>
                  <th>MIN</th>
                  <th>PTS</th>
                  <th>REB</th>
                  <th>AST</th>
                  <th>STL</th>
                  <th>BLK</th>
                  <th>FG</th>
                  <th>3PT</th>
                  <th>FT</th>
                  <th>+/-</th>
                </tr>
              </thead>
              <tbody>
                {selectedGame.box_score.away.map((player: any, idx: number) => (
                  <tr key={idx}>
                    <td><strong>{player.player_name}</strong></td>
                    <td>{player.minutes}</td>
                    <td>{player.points}</td>
                    <td>{player.rebounds}</td>
                    <td>{player.assists}</td>
                    <td>{player.steals}</td>
                    <td>{player.blocks}</td>
                    <td>{player.fg}</td>
                    <td>{player.three_pt}</td>
                    <td>{player.ft}</td>
                    <td>{player.plus_minus}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {playByPlay.length > 0 && (
            <div className="card">
              <h3>Play-by-Play</h3>
              <div className="play-by-play">
                {playByPlay.map((play: any) => (
                  <div key={play.id} className="play-item">
                    <span className="play-time">Q{play.quarter} {play.time}</span>
                    <span style={{ flex: 1 }}>{play.description}</span>
                    <span className="play-score">{play.home_score}-{play.away_score}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {currentView === 'tournament' && (
        <div className="card">
          <h2>Tournament Bracket</h2>
          {loading ? (
            <div className="loading">Loading tournament...</div>
          ) : tournamentData ? (
            <div className="tournament-bracket">
              {Object.entries(tournamentData).map(([roundName, seriesList]: [string, any]) => (
                <div key={roundName} className="round-card">
                  <h3>{roundName}</h3>
                  {seriesList.map((series: any) => (
                    <div 
                      key={series.id} 
                      className={`series-item ${series.is_completed ? 'completed' : 'active'}`}
                    >
                      <div><strong>{series.team1}</strong></div>
                      <div style={{ margin: '5px 0', color: '#718096' }}>vs</div>
                      <div><strong>{series.team2}</strong></div>
                      <div style={{ marginTop: '10px', fontSize: '1.2rem', fontWeight: 'bold', color: '#667eea' }}>
                        {series.score}
                      </div>
                      {series.winner && (
                        <div style={{ marginTop: '10px', color: '#48bb78', fontWeight: 'bold' }}>
                          Winner: {series.winner}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          ) : (
            <p>No tournament data available. Initialize the tournament first.</p>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
