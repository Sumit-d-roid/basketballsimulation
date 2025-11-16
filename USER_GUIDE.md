# 🎮 How to Use Your Basketball Tournament Simulator

## 🏁 Getting Started

### 1. Start the App
```bash
cd basketballsimulation
./run.sh
```

Open **http://localhost:3000** in your browser.

### 2. Access from Your Phone

Want to input scores right after your pickup game? Access from your phone!

**Same WiFi Method:**
1. Find your computer's IP address:
   ```bash
   # On Mac/Linux
   ifconfig | grep "inet " | grep -v 127.0.0.1
   
   # On Windows
   ipconfig
   ```
2. On your phone's browser, go to: `http://YOUR-COMPUTER-IP:3000`
3. Bookmark it for easy access!

## 🏀 How to Play

### The Flow

```
Real Life Game → Input Scores → System Extrapolates → Tournament Advances
     ↓               ↓                  ↓                    ↓
  Play 12 min   Enter final Q1     Generates 48 min      Best-of-7
  pickup game    (e.g., 28-25)     with variance         series
```

### Step-by-Step

#### 1. **View the Tournament Bracket**
- Open the app and you'll see the 32-team playoff bracket
- East Conference (left) and West Conference (right)
- 5 rounds: Round of 32 → Round of 16 → Quarter-Finals → Semi-Finals → Finals

#### 2. **Select a Game to Play**
- Click on any matchup in Round 1
- You'll see the two teams and their rosters
- Example: "Brooklyn Nets vs Indiana Pacers"

#### 3. **Play Your Real Pickup Game**
- Go outside and play basketball for **one quarter** (12 minutes)
- Keep score! This is important
- At the end, you'll have something like: **Team A: 28, Team B: 25**

#### 4. **Input the Quarter Scores**
- Back in the app, enter your actual scores:
  - Home Team (Q1): `28`
  - Away Team (Q1): `25`
- Click "Create Game" or "Submit"

#### 5. **Watch the Magic**
The system will:
- Take your 28-25 quarter score
- Calculate the scoring rates (2.33 PPM vs 2.08 PPM)
- Apply realistic NBA variance (each quarter varies ±15%)
- Regress to league mean (prevents unrealistic blowouts)
- Generate all 4 quarters

**Example Output:**
```
Quarter 1: 28-25 (your input)
Quarter 2: 24-27 (extrapolated with variance)
Quarter 3: 30-23 (extrapolated with variance)
Quarter 4: 26-29 (extrapolated with variance)
Final Score: 108-104
```

#### 6. **View Game Details**
- See the full 4-quarter breakdown
- Play-by-play log (coming soon in UI)
- Player statistics
- Game classification (Nail-Biter, Blowout, Comeback, etc.)

#### 7. **Continue the Series**
- This was Game 1 of a best-of-7 series
- Series score updates: "Nets lead 1-0"
- Keep playing real quarters and inputting scores
- First to 4 wins advances!

#### 8. **Crown a Champion**
- Complete all 5 rounds
- Final winner gets crowned NBA Champion
- View championship stats and history

## 🎯 Game Types Explained

The system classifies each game:

- **🔥 Nail-Biter**: Final margin ≤ 5 points (e.g., 108-104)
- **💥 Blowout**: Final margin ≥ 20 points (e.g., 125-98)
- **🚀 High Scoring**: Both teams score 115+ (e.g., 122-118)
- **🛡️ Defensive Battle**: Both teams score <95 (e.g., 88-85)
- **🎢 Comeback**: Trailing team wins (based on Q1 score)
- **⚡ Overtime**: 5+ point swings between quarters

## 📊 Features You Can Use

### Free Agent System
- **80 Free Agents** available (legends + current FAs)
- **Sign Players**: Add FAs to your team roster
- **Release Players**: Send players to free agency
- **Trade Players**: Swap players between teams

### Stats & History
- **Input Performance**: View your quarter score history
  - Average scores
  - Highest/lowest games
  - Win rates
- **Game History**: Browse all past games
  - Filter by team, date, game type
  - See series context

### Backups
- **Export Database**: Download JSON backup of everything
- **Download DB File**: Get the SQLite database file
- **Restore**: Copy old database file back to restore

## 💡 Tips & Tricks

### For Best Results

1. **Play Full Effort**: The system works best with real competitive scores
2. **Track Your Stats**: Keep a notebook of your quarter scores
3. **Balanced Scoring**: If one team is dominating (30-10), system adjusts to prevent 120-40 games
4. **Series Strategy**: Try to play the same matchup consistently for realistic series

### Understanding Extrapolation

**How it handles different scenarios:**

| Your Q1 Score | What Happens | Final Game Example |
|---------------|-------------|-------------------|
| 28-25 (close) | 70% your rate + 30% league avg | 108-104 (realistic) |
| 35-15 (blowout) | 40% your rate + 60% league avg | 115-92 (adjusted) |
| 15-13 (defensive) | Applies variance but stays low | 68-62 (defensive game) |

**Why adjustment?**
- A 30-10 quarter → 120-40 game is unrealistic
- System knows even NBA blowouts rarely exceed 130-85
- Your real game still determines the winner and general pace

### Mobile-Friendly Tips

1. **Add to Home Screen** (iOS/Android)
   - Safari/Chrome → Share → Add to Home Screen
   - Opens like a native app!

2. **Quick Input After Games**
   - Bookmark the "Create Game" page
   - Input scores immediately while fresh

3. **Check Bracket Between Quarters**
   - See tournament progress during water breaks

## 🐛 Troubleshooting

### App Won't Load
```bash
# Check if servers are running
ps aux | grep -E "python.*app.py|npm.*start"

# Restart
./run.sh
```

### Database Issues
```bash
# Reset database (WARNING: Deletes all data!)
cd backend
rm basketball_sim.db
python seed_data.py
python add_free_agents.py
```

### Port Already in Use
```bash
# Kill existing processes
lsof -ti:5000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
```

### Can't Connect from Phone
1. Make sure both devices on same WiFi
2. Check firewall allows connections
3. Try: `http://COMPUTER-IP:3000` (use actual IP)

## 🎮 Example Session

### Real-World Example

**You and your friends decide to simulate the 2025 playoffs:**

1. **Game 1: Nets vs Pacers**
   - Play 12 minutes, Nets win 26-23
   - Input scores → System generates: Nets 105, Pacers 98
   - Series: Nets lead 1-0

2. **Game 2: Same matchup**
   - Play another quarter, Pacers win 30-24
   - Input scores → System generates: Pacers 112, Nets 101
   - Series: Tied 1-1

3. **Game 3: Continue...**
   - Keep playing until one team wins 4 games
   - Winner advances to Round 2!

4. **Repeat for all 16 Round 1 series**
   - Play 16 real quarters (or more if series go to 7 games)
   - Takes about 3-4 hours of real basketball
   - Results in 16 winners advancing

5. **Continue through 5 rounds**
   - Each round, pick a matchup to play
   - Or play all of them!
   - Crown your champion

### Weekly Tournament Format

**Cool idea:** Run a weekly tournament with friends

- **Week 1**: Round 1 (play 4-5 series)
- **Week 2**: Round 2 + Quarter-finals
- **Week 3**: Semi-finals + Finals
- **Week 4**: Start new season with traded rosters!

## 🚀 Advanced Usage

### Season Management
- Each tournament = one "season" or "run"
- View past seasons in the app
- Compare champions across seasons

### Roster Building
- Start with default NBA rosters
- Trade players between teams
- Sign free agents (legends available!)
- Build your super team

### Data Analysis
- Export database to analyze stats
- Track scoring trends over time
- Compare your quarter inputs to final results
- Find patterns in variance

## 📱 Ready to Play?

1. ✅ Servers running: `./run.sh`
2. ✅ Browser open: http://localhost:3000
3. ✅ Tournament bracket visible
4. ✅ Go play basketball! 🏀

**Have fun and may the best team win!** 🏆
