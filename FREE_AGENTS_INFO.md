# Free Agents & Trade System

## What's New 🎯

Added a **Free Agent Pool** with **80 quality players** including:
- Current NBA free agents (Carmelo Anthony, Blake Griffin, etc.)
- International EuroLeague stars
- G-League prospects
- NBA legends (Dwyane Wade, Dirk Nowitzki, Vince Carter, etc.)
- Solid role players and specialists

## Database Stats 📊

- **33 Total Teams** (32 NBA + 1 Free Agents)
- **400 Total Players** (320 on NBA rosters + 80 free agents)
- Each NBA team has 10 players
- Free agent pool sorted by PPG (best players listed first)

## New API Endpoints 🔌

### 1. View Free Agents
```
GET /api/free-agents
```
Returns all available free agents sorted by PPG (best players first)

### 2. Sign Free Agent to Team
```
POST /api/players/<player_id>/sign
Body: { "team_id": 1 }
```
Sign a free agent to any NBA team

### 3. Release Player to Free Agency
```
POST /api/players/<player_id>/release
```
Release any player from their current team to free agency

### 4. Trade Players Between Teams
```
POST /api/players/trade
Body: {
  "player_ids_team1": [1, 2],
  "player_ids_team2": [3, 4]
}
```
Trade players between two teams (must trade at least 1 player from each side)

## Example Free Agents Available

**Legends:**
- Dwyane Wade (22.0 PPG, 4.7 RPG, 5.4 APG)
- Dirk Nowitzki (20.7 PPG, 7.5 RPG)
- Tracy McGrady (19.6 PPG, 5.6 RPG, 4.4 APG)
- Vince Carter (16.7 PPG, 4.3 RPG)
- Paul Pierce (19.7 PPG, 5.6 RPG)

**Current Players:**
- Carmelo Anthony (13.4 PPG)
- Blake Griffin (12.0 PPG, 5.5 RPG)
- John Wall (15.5 PPG, 6.9 APG)
- DeMarcus Cousins (16.3 PPG, 8.2 RPG)

**International Stars:**
- Vasilije Micic (13.7 PPG, 5.4 APG)
- Nikola Mirotic (14.8 PPG, 6.2 RPG)
- Mike James (14.3 PPG, 4.8 APG)

## Future Features You Can Build 🚀

With this free agent system in place, you can now add:

1. **Trade Deadline**: Set rules for when trades can happen
2. **Salary Cap**: Add contract/salary system
3. **Draft System**: Create a draft with prospects
4. **Roster Limits**: Enforce min/max roster sizes
5. **Contract Length**: Multi-year contracts with expiration
6. **Team Chemistry**: Roster changes affect performance
7. **Injuries**: Move players to IR, sign replacements

## How to Use

Right now, you can:
1. View all free agents via the API
2. Manually sign/release/trade players via API calls
3. Build UI in the frontend to manage rosters

The system automatically creates the Free Agents team if it doesn't exist, so everything is ready to go!
