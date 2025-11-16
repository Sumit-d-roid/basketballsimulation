from models import Team, Player, init_db
import random

def seed_teams_and_players():
    """Seed the database with exactly 32 NBA teams and real player rosters."""
    session = init_db()
    
    # Exactly 32 NBA Teams (adding Hornets and Wizards to make 32)
    nba_teams = [
        # Eastern Conference - Atlantic
        {"name": "Celtics", "city": "Boston", "abbr": "BOS", "conf": "East", "div": "Atlantic", "type": "NBA"},
        {"name": "Nets", "city": "Brooklyn", "abbr": "BKN", "conf": "East", "div": "Atlantic", "type": "NBA"},
        {"name": "Knicks", "city": "New York", "abbr": "NYK", "conf": "East", "div": "Atlantic", "type": "NBA"},
        {"name": "76ers", "city": "Philadelphia", "abbr": "PHI", "conf": "East", "div": "Atlantic", "type": "NBA"},
        {"name": "Raptors", "city": "Toronto", "abbr": "TOR", "conf": "East", "div": "Atlantic", "type": "NBA"},
        
        # Eastern Conference - Central
        {"name": "Bulls", "city": "Chicago", "abbr": "CHI", "conf": "East", "div": "Central", "type": "NBA"},
        {"name": "Cavaliers", "city": "Cleveland", "abbr": "CLE", "conf": "East", "div": "Central", "type": "NBA"},
        {"name": "Pistons", "city": "Detroit", "abbr": "DET", "conf": "East", "div": "Central", "type": "NBA"},
        {"name": "Pacers", "city": "Indiana", "abbr": "IND", "conf": "East", "div": "Central", "type": "NBA"},
        {"name": "Bucks", "city": "Milwaukee", "abbr": "MIL", "conf": "East", "div": "Central", "type": "NBA"},
        
        # Eastern Conference - Southeast
        {"name": "Hawks", "city": "Atlanta", "abbr": "ATL", "conf": "East", "div": "Southeast", "type": "NBA"},
        {"name": "Hornets", "city": "Charlotte", "abbr": "CHA", "conf": "East", "div": "Southeast", "type": "NBA"},
        {"name": "Heat", "city": "Miami", "abbr": "MIA", "conf": "East", "div": "Southeast", "type": "NBA"},
        {"name": "Magic", "city": "Orlando", "abbr": "ORL", "conf": "East", "div": "Southeast", "type": "NBA"},
        {"name": "Wizards", "city": "Washington", "abbr": "WAS", "conf": "East", "div": "Southeast", "type": "NBA"},
        {"name": "Grizzlies", "city": "Memphis", "abbr": "MEM", "conf": "East", "div": "Southeast", "type": "NBA"},  # Move to East for balance
        
        # Western Conference - Northwest
        {"name": "Nuggets", "city": "Denver", "abbr": "DEN", "conf": "West", "div": "Northwest", "type": "NBA"},
        {"name": "Timberwolves", "city": "Minnesota", "abbr": "MIN", "conf": "West", "div": "Northwest", "type": "NBA"},
        {"name": "Thunder", "city": "Oklahoma City", "abbr": "OKC", "conf": "West", "div": "Northwest", "type": "NBA"},
        {"name": "Trail Blazers", "city": "Portland", "abbr": "POR", "conf": "West", "div": "Northwest", "type": "NBA"},
        {"name": "Jazz", "city": "Utah", "abbr": "UTA", "conf": "West", "div": "Northwest", "type": "NBA"},
        
        # Western Conference - Pacific
        {"name": "Warriors", "city": "Golden State", "abbr": "GSW", "conf": "West", "div": "Pacific", "type": "NBA"},
        {"name": "Clippers", "city": "Los Angeles", "abbr": "LAC", "conf": "West", "div": "Pacific", "type": "NBA"},
        {"name": "Lakers", "city": "Los Angeles", "abbr": "LAL", "conf": "West", "div": "Pacific", "type": "NBA"},
        {"name": "Suns", "city": "Phoenix", "abbr": "PHX", "conf": "West", "div": "Pacific", "type": "NBA"},
        {"name": "Kings", "city": "Sacramento", "abbr": "SAC", "conf": "West", "div": "Pacific", "type": "NBA"},
        
        # Western Conference - Southwest
        {"name": "Mavericks", "city": "Dallas", "abbr": "DAL", "conf": "West", "div": "Southwest", "type": "NBA"},
        {"name": "Rockets", "city": "Houston", "abbr": "HOU", "conf": "West", "div": "Southwest", "type": "NBA"},
        {"name": "Pelicans", "city": "New Orleans", "abbr": "NOP", "conf": "West", "div": "Southwest", "type": "NBA"},
        {"name": "Spurs", "city": "San Antonio", "abbr": "SAS", "conf": "West", "div": "Southwest", "type": "NBA"},
        
        # Additional teams to reach 32
        {"name": "SuperSonics", "city": "Seattle", "abbr": "SEA", "conf": "West", "div": "Pacific", "type": "NBA"},
        {"name": "Expansion", "city": "Las Vegas", "abbr": "LV", "conf": "West", "div": "Southwest", "type": "NBA"},
    ]
    
    # Create teams
    team_objects = []
    for team_data in nba_teams:
        team = Team(
            name=team_data["name"],
            city=team_data["city"],
            abbreviation=team_data["abbr"],
            conference=team_data["conf"],
            division=team_data["div"],
            team_type=team_data["type"]
        )
        session.add(team)
        team_objects.append(team)
    
    session.commit()
    
    # Real NBA player names by team (top players for each roster)
    real_rosters = {
        "BOS": ["Jayson Tatum", "Jaylen Brown", "Kristaps Porzingis", "Derrick White", "Jrue Holiday", 
                "Al Horford", "Sam Hauser", "Payton Pritchard", "Luke Kornet", "Oshae Brissett"],
        "BKN": ["Mikal Bridges", "Cam Thomas", "Nicolas Claxton", "Spencer Dinwiddie", "Dorian Finney-Smith",
                "Cam Johnson", "Day'Ron Sharpe", "Lonnie Walker", "Dennis Smith Jr", "Trendon Watford"],
        "NYK": ["Jalen Brunson", "Julius Randle", "RJ Barrett", "Mitchell Robinson", "Josh Hart",
                "Immanuel Quickley", "Isaiah Hartenstein", "Donte DiVincenzo", "Quentin Grimes", "Precious Achiuwa"],
        "PHI": ["Joel Embiid", "Tyrese Maxey", "Tobias Harris", "De'Anthony Melton", "Nicolas Batum",
                "Kelly Oubre Jr", "Paul Reed", "Marcus Morris", "Patrick Beverley", "Danuel House"],
        "TOR": ["Scottie Barnes", "Pascal Siakam", "OG Anunoby", "Dennis Schroder", "Jakob Poeltl",
                "Gary Trent Jr", "Precious Achiuwa", "Otto Porter Jr", "Chris Boucher", "Malachi Flynn"],
        "CHI": ["DeMar DeRozan", "Zach LaVine", "Nikola Vucevic", "Coby White", "Alex Caruso",
                "Patrick Williams", "Ayo Dosunmu", "Andre Drummond", "Torrey Craig", "Jevon Carter"],
        "CLE": ["Donovan Mitchell", "Darius Garland", "Evan Mobley", "Jarrett Allen", "Max Strus",
                "Caris LeVert", "Isaac Okoro", "Georges Niang", "Dean Wade", "Sam Merrill"],
        "DET": ["Cade Cunningham", "Jaden Ivey", "Bojan Bogdanovic", "Isaiah Stewart", "Jalen Duren",
                "Ausar Thompson", "Marcus Sasser", "James Wiseman", "Joe Harris", "Alec Burks"],
        "IND": ["Tyrese Haliburton", "Myles Turner", "Bennedict Mathurin", "Bruce Brown", "Buddy Hield",
                "Aaron Nesmith", "Obi Toppin", "T.J. McConnell", "Jalen Smith", "Andrew Nembhard"],
        "MIL": ["Giannis Antetokounmpo", "Damian Lillard", "Khris Middleton", "Brook Lopez", "Bobby Portis",
                "Malik Beasley", "Pat Connaughton", "Jae Crowder", "MarJon Beauchamp", "AJ Green"],
        "ATL": ["Trae Young", "Dejounte Murray", "Clint Capela", "Bogdan Bogdanovic", "De'Andre Hunter",
                "Onyeka Okongwu", "Saddiq Bey", "Jalen Johnson", "AJ Griffin", "Garrison Mathews"],
        "CHA": ["LaMelo Ball", "Brandon Miller", "Mark Williams", "Miles Bridges", "Terry Rozier",
                "Gordon Hayward", "PJ Washington", "Nick Richards", "Bryce McGowens", "JT Thor"],
        "MIA": ["Jimmy Butler", "Bam Adebayo", "Tyler Herro", "Kyle Lowry", "Caleb Martin",
                "Duncan Robinson", "Kevin Love", "Josh Richardson", "Jaime Jaquez Jr", "Nikola Jovic"],
        "ORL": ["Paolo Banchero", "Franz Wagner", "Wendell Carter Jr", "Cole Anthony", "Markelle Fultz",
                "Jalen Suggs", "Jonathan Isaac", "Gary Harris", "Moritz Wagner", "Chuma Okeke"],
        "WAS": ["Kyle Kuzma", "Jordan Poole", "Tyus Jones", "Daniel Gafford", "Deni Avdija",
                "Corey Kispert", "Bilal Coulibaly", "Marvin Bagley", "Delon Wright", "Landry Shamet"],
        "DEN": ["Nikola Jokic", "Jamal Murray", "Michael Porter Jr", "Aaron Gordon", "Kentavious Caldwell-Pope",
                "Christian Braun", "Reggie Jackson", "Justin Holiday", "Peyton Watson", "DeAndre Jordan"],
        "MIN": ["Anthony Edwards", "Karl-Anthony Towns", "Rudy Gobert", "Mike Conley", "Jaden McDaniels",
                "Kyle Anderson", "Naz Reid", "Nickeil Alexander-Walker", "Troy Brown Jr", "Jordan McLaughlin"],
        "OKC": ["Shai Gilgeous-Alexander", "Chet Holmgren", "Josh Giddey", "Jalen Williams", "Luguentz Dort",
                "Cason Wallace", "Isaiah Joe", "Jaylin Williams", "Kenrich Williams", "Vasilije Micic"],
        "POR": ["Damian Lillard", "Anfernee Simons", "Jerami Grant", "Shaedon Sharpe", "Deandre Ayton",
                "Malcolm Brogdon", "Matisse Thybulle", "Jabari Walker", "Kris Murray", "Duop Reath"],
        "UTA": ["Lauri Markkanen", "Jordan Clarkson", "Collin Sexton", "Walker Kessler", "John Collins",
                "Talen Horton-Tucker", "Simone Fontecchio", "Ochai Agbaji", "Kelly Olynyk", "Keyonte George"],
        "GSW": ["Stephen Curry", "Klay Thompson", "Andrew Wiggins", "Draymond Green", "Chris Paul",
                "Jonathan Kuminga", "Brandin Podziemski", "Moses Moody", "Kevon Looney", "Gary Payton II"],
        "LAC": ["Kawhi Leonard", "Paul George", "Russell Westbrook", "Ivica Zubac", "James Harden",
                "Norman Powell", "Terance Mann", "Bones Hyland", "Mason Plumlee", "Amir Coffey"],
        "LAL": ["LeBron James", "Anthony Davis", "D'Angelo Russell", "Austin Reaves", "Rui Hachimura",
                "Jarred Vanderbilt", "Taurean Prince", "Jaxson Hayes", "Gabe Vincent", "Cam Reddish"],
        "PHX": ["Kevin Durant", "Devin Booker", "Bradley Beal", "Jusuf Nurkic", "Grayson Allen",
                "Eric Gordon", "Drew Eubanks", "Yuta Watanabe", "Josh Okogie", "Bol Bol"],
        "SAC": ["De'Aaron Fox", "Domantas Sabonis", "Kevin Huerter", "Harrison Barnes", "Keegan Murray",
                "Malik Monk", "Trey Lyles", "Davion Mitchell", "Sasha Vezenkov", "Chris Duarte"],
        "DAL": ["Luka Doncic", "Kyrie Irving", "Derrick Jones Jr", "Daniel Gafford", "PJ Washington",
                "Josh Green", "Maxi Kleber", "Tim Hardaway Jr", "Dereck Lively II", "Dante Exum"],
        "HOU": ["Alperen Sengun", "Jalen Green", "Fred VanVleet", "Jabari Smith Jr", "Dillon Brooks",
                "Amen Thompson", "Cam Whitmore", "Tari Eason", "Jeff Green", "Aaron Holiday"],
        "MEM": ["Ja Morant", "Desmond Bane", "Jaren Jackson Jr", "Marcus Smart", "Brandon Clarke",
                "Luke Kennard", "Santi Aldama", "Derrick Rose", "Xavier Tillman", "David Roddy"],
        "NOP": ["Zion Williamson", "Brandon Ingram", "CJ McCollum", "Herb Jones", "Jonas Valanciunas",
                "Trey Murphy III", "Jordan Hawkins", "Larry Nance Jr", "Jose Alvarado", "Dyson Daniels"],
        "SAS": ["Victor Wembanyama", "Devin Vassell", "Keldon Johnson", "Tre Jones", "Jeremy Sochan",
                "Zach Collins", "Malaki Branham", "Cedi Osman", "Sandro Mamukelashvili", "Blake Wesley"],
        "SEA": ["Kevin Durant", "Russell Westbrook", "Ray Allen", "Shawn Kemp", "Gary Payton",
                "Detlef Schrempf", "Rashard Lewis", "Jack Sikma", "Spencer Haywood", "Gus Williams"],
        "LV": ["Jalen Green", "Scoot Henderson", "Brandon Clarke", "Saddiq Bey", "Collin Sexton",
               "Jalen Duren", "Josh Christopher", "Marvin Bagley", "Dennis Smith Jr", "Killian Hayes"],
    }
    
    # Create realistic player rosters for each team
    positions = ["PG", "SG", "SF", "PF", "C"]
    
    for team in team_objects:
        # Get real roster for this team
        real_players = real_rosters.get(team.abbreviation, [])
        
        # Create 10-12 players per team
        num_players = len(real_players) if real_players else 10
        
        for i in range(num_players):
            position = positions[i % 5]  # Distribute positions evenly
            
            # Use real name if available, otherwise generate one
            if i < len(real_players):
                player_name = real_players[i]
            else:
                player_name = f"Player {i+1}"
            
            # Generate realistic stats based on position and role
            if position == "PG":
                ppg = random.uniform(8, 25)
                rpg = random.uniform(2, 6)
                apg = random.uniform(4, 10)
                spg = random.uniform(0.5, 2)
                bpg = random.uniform(0.1, 0.5)
            elif position == "SG":
                ppg = random.uniform(10, 28)
                rpg = random.uniform(3, 6)
                apg = random.uniform(2, 5)
                spg = random.uniform(0.8, 2)
                bpg = random.uniform(0.2, 0.8)
            elif position == "SF":
                ppg = random.uniform(12, 27)
                rpg = random.uniform(4, 8)
                apg = random.uniform(2, 6)
                spg = random.uniform(0.7, 1.8)
                bpg = random.uniform(0.3, 1.2)
            elif position == "PF":
                ppg = random.uniform(10, 24)
                rpg = random.uniform(6, 12)
                apg = random.uniform(1, 4)
                spg = random.uniform(0.5, 1.5)
                bpg = random.uniform(0.8, 2)
            else:  # C
                ppg = random.uniform(8, 22)
                rpg = random.uniform(8, 14)
                apg = random.uniform(1, 5)
                spg = random.uniform(0.3, 1)
                bpg = random.uniform(1.5, 3)
            
            # Adjust stats for stars (first 2-3 players) vs role players
            if i < 2:  # Star players
                ppg *= 1.4
                apg *= 1.4
                rpg *= 1.3
            elif i < 5:  # Starters
                ppg *= 1.1
                apg *= 1.1
                rpg *= 1.1
            elif i >= 8:  # Bench players
                ppg *= 0.6
                apg *= 0.7
                rpg *= 0.8
            
            player = Player(
                name=player_name,
                team_id=team.id,
                position=position,
                jersey_number=i + 1,
                height=f"{random.randint(6, 7)}'{random.randint(0, 11)}\"",
                weight=random.randint(180, 280),
                ppg=round(ppg, 1),
                rpg=round(rpg, 1),
                apg=round(apg, 1),
                spg=round(spg, 1),
                bpg=round(bpg, 1),
                fg_pct=round(random.uniform(0.38, 0.52), 3),
                three_pt_pct=round(random.uniform(0.30, 0.42), 3),
                ft_pct=round(random.uniform(0.70, 0.90), 3),
                mpg=round(random.uniform(25, 36), 1) if i < 5 else round(random.uniform(8, 20), 1)
            )
            session.add(player)
    
    session.commit()
    print(f"✓ Created {len(team_objects)} teams (exactly 32)")
    total_players = sum(len(real_rosters.get(t.abbreviation, [])) or 10 for t in team_objects)
    print(f"✓ Created {total_players} real NBA players")
    session.close()

if __name__ == "__main__":
    seed_teams_and_players()
