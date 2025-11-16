import React from 'react';
import './BracketTree.css';

interface BracketSeries {
  id: number;
  team1: string;
  team2: string;
  score: string;
  is_completed: boolean;
  winner?: string;
}

interface BracketTreeProps {
  tournamentData: {
    [roundName: string]: BracketSeries[];
  };
}

export const BracketTree: React.FC<BracketTreeProps> = ({ tournamentData }) => {
  if (!tournamentData) {
    return <div>Loading bracket...</div>;
  }

  // Define round order and labels
  const rounds = [
    { key: 'Round 1 (Round of 32)', label: 'Round of 32', maxSeries: 16 },
    { key: 'Round 2 (Sweet 16)', label: 'Sweet 16', maxSeries: 8 },
    { key: 'Round 3 (Elite 8)', label: 'Elite 8', maxSeries: 4 },
    { key: 'Conference Finals', label: 'Conference Finals', maxSeries: 2 },
    { key: 'Finals', label: 'Finals', maxSeries: 1 }
  ];

  return (
    <div className="bracket-tree-container">
      <div className="bracket-tree">
        {rounds.map((round, roundIdx) => {
          const seriesList = tournamentData[round.key] || [];
          
          return (
            <div key={roundIdx} className="bracket-round">
              <div className="round-header">{round.label}</div>
              <div className="round-series">
                {seriesList.map((series, seriesIdx) => (
                  <div 
                    key={series.id} 
                    className={`bracket-matchup ${series.is_completed ? 'completed' : 'active'}`}
                  >
                    <div className={`team ${series.winner === series.team1 ? 'winner' : ''}`}>
                      <span className="team-name">{series.team1}</span>
                      <span className="team-wins">{series.score.split(' - ')[0]}</span>
                    </div>
                    <div className={`team ${series.winner === series.team2 ? 'winner' : ''}`}>
                      <span className="team-name">{series.team2}</span>
                      <span className="team-wins">{series.score.split(' - ')[1]}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
      
      {tournamentData['Finals']?.[0]?.winner && (
        <div className="champion-banner">
          🏆 {tournamentData['Finals'][0].winner} - Tournament Champion! 🏆
        </div>
      )}
    </div>
  );
};
