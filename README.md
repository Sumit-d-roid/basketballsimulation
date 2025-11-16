# 🏀 Basketball Simulation

An advanced basketball game simulation system that extrapolates full 48-minute NBA games from a single quarter of real gameplay. Features a 34-team tournament with best-of-7 series, realistic player stats, play-by-play logs, and ESPN-style stat tracking.

## 🎯 Features

- **Score Extrapolation**: Input just ONE quarter score, get a full realistic 48-minute game
- **32 Teams**: 30 NBA teams + 2 G-League teams
- **Real Players**: 2025-26 NBA rosters with realistic baseline stats
- **Tournament System**: Best-of-7 series in knockout format
- **Advanced Stats**: PER, True Shooting %, Usage Rate, Plus/Minus, and more
- **Play-by-Play Logs**: ESPN-style detailed game logs for every possession
- **Modern Web Interface**: Beautiful React frontend for easy interaction

## 🏗️ Project Structure

```
basketballsimulation/
├── backend/
│   ├── app.py                      # Flask API server
│   ├── models.py                   # SQLAlchemy database models
│   ├── seed_data.py               # Team and player data seeder
│   ├── game_extrapolator.py       # Score extrapolation engine
│   ├── play_by_play_generator.py  # Play-by-play log generator
│   ├── tournament_manager.py      # Tournament bracket manager
│   └── requirements.txt           # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx               # Main React application
│   │   ├── api.ts                # API client
│   │   └── App.css               # Styles
│   ├── public/
│   └── package.json              # Node dependencies
│
└── README.md
```

## 🚀 Quick Start

### Single Command (Recommended)

Serve the frontend from Flask at the same origin and avoid CORS entirely.

```
./run.sh
```

Open http://localhost:5000

The script will:
- Create/activate a Python venv and install backend dependencies
- Seed the database (idempotent)
- Install frontend dependencies and build the UI
- Start Flask on port 5000 serving both API (`/api/*`) and UI (`/`)

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database and seed data:**
   ```bash
   python seed_data.py
   ```

5. **Start the Flask server:**
   ```bash
   python app.py
   ```

   Server will run on `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the React development server:**
   ```bash
   npm start
   ```

   App will open on `http://localhost:3000`

## 📖 How to Use

### 1. Initialize Tournament
- Click "Initialize Tournament" to create the 34-team bracket
- This creates play-in games and sets up the main bracket

### 2. Simulate a Game
- Select home and away teams
- Choose which quarter (1-4) you actually played
- Input the scores from that quarter only
- Optionally link to an active tournament series
- Click "Simulate Full Game"
- System generates:
  - Full 48-minute game with realistic quarter-by-quarter scores
  - Complete box scores for all players
  - Advanced statistics
  - Play-by-play logs

### 3. View Results
- **All Games**: See list of all simulated games
- **Game Details**: View box scores, stats, and play-by-play
- **Tournament Bracket**: Track series progress and winners

## 🔧 API Endpoints

### Teams
- `GET /api/teams` - Get all teams
- `GET /api/teams/<id>` - Get team with roster

### Games
- `POST /api/games/create` - Create and simulate game
- `GET /api/games/<id>` - Get game details
- `GET /api/games/<id>/playbyplay` - Get play-by-play log
- `GET /api/games` - Get all games

### Tournament
- `POST /api/tournament/initialize` - Initialize tournament
- `GET /api/tournament/overview` - Get bracket overview
- `GET /api/tournament/series/<id>` - Get series details
- `GET /api/tournament/active-series` - Get active series

### Stats
- `GET /api/stats/player/<id>` - Get player stats across all games

## 🎮 Game Simulation Details

### Extrapolation Algorithm

The system uses sophisticated algorithms to extrapolate realistic game data:

1. **Base Rate Calculation**: Determines scoring rate from input quarter
2. **Variance Modeling**: Adds realistic quarter-to-quarter variance (±20%)
3. **Momentum Effects**: 4th quarter can have increased scoring (clutch time)
4. **Player Distribution**: Distributes team stats based on player tendencies
5. **Shot Selection**: Models 2PT/3PT ratio based on modern NBA averages

### Statistics Generated

**Basic Stats**:
- Points, Rebounds (Off/Def), Assists, Steals, Blocks
- Field Goals, 3-Pointers, Free Throws (Made/Attempted)
- Turnovers, Fouls, Minutes Played

**Advanced Stats**:
- True Shooting % (TS%)
- Effective Field Goal % (eFG%)
- Plus/Minus (+/-)
- Usage Rate
- Player Efficiency Rating (PER)

### Play-by-Play Generation

Each possession generates realistic events:
- Shot attempts (made/missed, 2PT/3PT)
- Rebounds (offensive/defensive)
- Assists on made baskets (~55% rate)
- Turnovers (~6% of possessions)
- Fouls and free throws
- Time-stamped with quarter and game clock

## 🏆 Tournament Format

32 teams in a standard single-elimination bracket:
1. **Round 1**: 16 series (32 teams)
2. **Round 2**: 8 series (16 teams)
3. **Round 3**: 4 series (8 teams)
4. **Round 4**: 2 series (4 teams - Conference Finals)
5. **Finals**: 1 series (2 teams)

Each series is best-of-7 (first to 4 wins).

## 🗄️ Database Schema

- **Teams**: Team info, conference, division
- **Players**: Roster with career averages
- **Games**: Game results, quarter scores
- **Series**: Tournament matchups and standings
- **PlayerGameStats**: Individual game performances
- **PlayByPlay**: Detailed play-by-play logs

## 🎨 Tech Stack

**Backend**:
- Python 3.8+
- Flask (REST API)
- SQLAlchemy (ORM)
- SQLite (Database)
- NumPy/Pandas (Stats calculations)

**Frontend**:
- React 18
- TypeScript
- Axios (API client)
- CSS3 (Modern styling)

## 🔮 Future Enhancements

- [ ] Real-time game simulation animation
- [ ] Shot charts and heat maps
- [ ] Team and player comparison tools
- [ ] Historical stats tracking across tournaments
- [ ] Export game logs to CSV/PDF
- [ ] Live game input mode
- [ ] Multiplayer tournament support

## 📝 License

MIT License - feel free to use and modify!

## 🤝 Contributing

Contributions welcome! Feel free to submit issues or pull requests.

## 📧 Support

For questions or issues, please open a GitHub issue.

---

**Enjoy simulating basketball games!** 🏀🔥