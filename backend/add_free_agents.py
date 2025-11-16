from models import Team, Player, get_session
import random

def add_free_agents():
    """Add a free agent pool with quality NBA players (retired legends, international stars, etc.)"""
    session = get_session()
    
    # Check if Free Agents team exists
    fa_team = session.query(Team).filter_by(team_type='Free Agent').first()
    
    if not fa_team:
        # Create Free Agents team
        fa_team = Team(
            name="Free Agents",
            city="NBA",
            abbreviation="FA",
            conference=None,
            division=None,
            team_type="Free Agent"
        )
        session.add(fa_team)
        session.commit()
        print("✓ Created Free Agents team")
    else:
        print("✓ Free Agents team already exists")
    
    # Check if we already have free agents
    existing_fa = session.query(Player).filter_by(team_id=fa_team.id).count()
    if existing_fa > 0:
        print(f"✓ Already have {existing_fa} free agents")
        choice = input("Add more free agents? (y/n): ").lower()
        if choice != 'y':
            return
    
    # Quality Free Agent Pool (mix of current free agents, international stars, legends)
    free_agents = [
        # Current NBA Free Agents / Recently Unsigned
        {"name": "Carmelo Anthony", "pos": "SF", "ppg": 13.4, "rpg": 4.2, "apg": 1.0},
        {"name": "Blake Griffin", "pos": "PF", "ppg": 12.0, "rpg": 5.5, "apg": 1.9},
        {"name": "Dwight Howard", "pos": "C", "ppg": 7.4, "rpg": 7.8, "apg": 0.4},
        {"name": "Isaiah Thomas", "pos": "PG", "ppg": 12.2, "rpg": 1.6, "apg": 3.7},
        {"name": "DeMarcus Cousins", "pos": "C", "ppg": 16.3, "rpg": 8.2, "apg": 2.5},
        {"name": "John Wall", "pos": "PG", "ppg": 15.5, "rpg": 3.5, "apg": 6.9},
        {"name": "Dennis Schroder", "pos": "PG", "ppg": 13.9, "rpg": 2.6, "apg": 4.5},
        {"name": "Goran Dragic", "pos": "PG", "ppg": 13.2, "rpg": 3.1, "apg": 4.1},
        {"name": "Tristan Thompson", "pos": "C", "ppg": 7.8, "rpg": 6.5, "apg": 0.9},
        {"name": "Serge Ibaka", "pos": "C", "ppg": 11.1, "rpg": 6.8, "apg": 1.0},
        
        # Borderline NBA / Strong Rotation Players
        {"name": "JaVale McGee", "pos": "C", "ppg": 8.0, "rpg": 5.2, "apg": 0.8},
        {"name": "Hassan Whiteside", "pos": "C", "ppg": 8.2, "rpg": 7.7, "apg": 0.5},
        {"name": "Jeff Green", "pos": "PF", "ppg": 7.8, "rpg": 2.6, "apg": 1.0},
        {"name": "Markieff Morris", "pos": "PF", "ppg": 7.6, "rpg": 4.4, "apg": 1.4},
        {"name": "Wesley Matthews", "pos": "SG", "ppg": 8.4, "rpg": 2.5, "apg": 1.4},
        {"name": "Avery Bradley", "pos": "SG", "ppg": 8.6, "rpg": 2.3, "apg": 1.3},
        {"name": "Rajon Rondo", "pos": "PG", "ppg": 5.8, "rpg": 3.7, "apg": 5.3},
        {"name": "Eric Bledsoe", "pos": "PG", "ppg": 12.1, "rpg": 3.4, "apg": 3.9},
        {"name": "Kent Bazemore", "pos": "SG", "ppg": 8.8, "rpg": 3.2, "apg": 1.6},
        {"name": "Rodney Hood", "pos": "SG", "ppg": 10.2, "rpg": 2.2, "apg": 1.5},
        
        # International Stars (EuroLeague / FIBA standouts)
        {"name": "Luca Vildoza", "pos": "PG", "ppg": 11.5, "rpg": 2.8, "apg": 4.2},
        {"name": "Vasilije Micic", "pos": "PG", "ppg": 13.7, "rpg": 2.9, "apg": 5.4},
        {"name": "Tornike Shengelia", "pos": "PF", "ppg": 12.8, "rpg": 5.6, "apg": 2.1},
        {"name": "Jan Vesely", "pos": "PF", "ppg": 10.4, "rpg": 5.8, "apg": 1.3},
        {"name": "Mike James", "pos": "PG", "ppg": 14.3, "rpg": 2.1, "apg": 4.8},
        {"name": "Shane Larkin", "pos": "PG", "ppg": 13.9, "rpg": 2.4, "apg": 5.1},
        {"name": "Sergio Rodriguez", "pos": "PG", "ppg": 9.8, "rpg": 2.2, "apg": 6.2},
        {"name": "Nikola Mirotic", "pos": "PF", "ppg": 14.8, "rpg": 6.2, "apg": 1.5},
        {"name": "Kostas Sloukas", "pos": "PG", "ppg": 12.1, "rpg": 2.6, "apg": 5.8},
        {"name": "Nando De Colo", "pos": "SG", "ppg": 13.4, "rpg": 3.1, "rpg": 4.9},
        
        # Young Prospects / G-League Stars
        {"name": "Mac McClung", "pos": "PG", "ppg": 15.8, "rpg": 3.2, "apg": 5.1},
        {"name": "Craig Sword", "pos": "SG", "ppg": 17.2, "rpg": 4.8, "apg": 3.4},
        {"name": "Justin Jackson", "pos": "SF", "ppg": 16.1, "rpg": 5.2, "apg": 2.8},
        {"name": "Mychal Mulder", "pos": "SG", "ppg": 14.3, "rpg": 3.7, "apg": 2.1},
        {"name": "Quinndary Weatherspoon", "pos": "SG", "ppg": 13.8, "rpg": 4.1, "apg": 3.2},
        {"name": "Zylan Cheatham", "pos": "PF", "ppg": 12.7, "rpg": 7.3, "apg": 2.4},
        {"name": "Tyler Cook", "pos": "PF", "ppg": 15.4, "rpg": 6.9, "apg": 1.8},
        {"name": "Deonte Burton", "pos": "SF", "ppg": 14.9, "rpg": 5.1, "apg": 2.3},
        {"name": "Brandon Goodwin", "pos": "PG", "ppg": 13.6, "rpg": 3.4, "apg": 6.2},
        {"name": "Jaylen Adams", "pos": "PG", "ppg": 12.8, "rpg": 2.9, "apg": 5.7},
        
        # Retired Legends (for fun dynasty mode)
        {"name": "Dwyane Wade", "pos": "SG", "ppg": 22.0, "rpg": 4.7, "apg": 5.4},
        {"name": "Dirk Nowitzki", "pos": "PF", "ppg": 20.7, "rpg": 7.5, "apg": 2.4},
        {"name": "Tony Parker", "pos": "PG", "ppg": 15.5, "rpg": 2.7, "apg": 5.6},
        {"name": "Manu Ginobili", "pos": "SG", "ppg": 13.3, "rpg": 3.5, "apg": 3.8},
        {"name": "Vince Carter", "pos": "SF", "ppg": 16.7, "rpg": 4.3, "apg": 3.1},
        {"name": "Paul Pierce", "pos": "SF", "ppg": 19.7, "rpg": 5.6, "apg": 3.5},
        {"name": "Pau Gasol", "pos": "C", "ppg": 17.0, "rpg": 9.2, "apg": 3.2},
        {"name": "Amar'e Stoudemire", "pos": "PF", "ppg": 18.9, "rpg": 7.8, "apg": 1.2},
        {"name": "Yao Ming", "pos": "C", "ppg": 19.0, "rpg": 9.2, "apg": 1.6},
        {"name": "Tracy McGrady", "pos": "SG", "ppg": 19.6, "rpg": 5.6, "apg": 4.4},
        
        # More Recent Retirees
        {"name": "Andre Iguodala", "pos": "SF", "ppg": 11.3, "rpg": 4.9, "apg": 4.2},
        {"name": "Joe Johnson", "pos": "SG", "ppg": 16.0, "rpg": 4.0, "apg": 3.9},
        {"name": "Jamal Crawford", "pos": "SG", "ppg": 14.6, "rpg": 2.2, "apg": 3.4},
        {"name": "Monta Ellis", "pos": "SG", "ppg": 17.8, "rpg": 3.5, "apg": 4.6},
        {"name": "David West", "pos": "PF", "ppg": 13.6, "rpg": 6.4, "apg": 2.3},
        {"name": "Zach Randolph", "pos": "PF", "ppg": 16.6, "rpg": 9.1, "apg": 1.8},
        {"name": "Richard Jefferson", "pos": "SF", "ppg": 12.6, "rpg": 4.0, "apg": 2.0},
        {"name": "Deron Williams", "pos": "PG", "ppg": 16.0, "rpg": 3.1, "apg": 8.1},
        {"name": "Josh Smith", "pos": "PF", "ppg": 14.5, "rpg": 7.4, "apg": 3.1},
        {"name": "Al Jefferson", "pos": "C", "ppg": 15.7, "rpg": 8.4, "apg": 1.6},
        
        # Solid Role Players / Specialists
        {"name": "Marco Belinelli", "pos": "SG", "ppg": 9.8, "rpg": 2.3, "apg": 1.8},
        {"name": "Ersan Ilyasova", "pos": "PF", "ppg": 10.9, "rpg": 5.9, "apg": 1.2},
        {"name": "Garrett Temple", "pos": "SG", "ppg": 7.4, "rpg": 2.6, "apg": 2.1},
        {"name": "Ryan Anderson", "pos": "PF", "ppg": 11.0, "rpg": 4.8, "apg": 0.9},
        {"name": "Meyers Leonard", "pos": "C", "ppg": 5.9, "rpg": 3.9, "apg": 0.8},
        {"name": "Michael Beasley", "pos": "PF", "ppg": 12.4, "rpg": 4.7, "apg": 1.3},
        {"name": "Lance Stephenson", "pos": "SG", "ppg": 8.6, "rpg": 4.2, "apg": 2.9},
        {"name": "JR Smith", "pos": "SG", "ppg": 12.4, "rpg": 3.2, "apg": 2.1},
        {"name": "Nick Young", "pos": "SG", "ppg": 11.4, "rpg": 2.3, "apg": 1.0},
        {"name": "Michael Carter-Williams", "pos": "PG", "ppg": 11.2, "rpg": 4.9, "apg": 5.0},
        
        # Additional Depth
        {"name": "Shabazz Napier", "pos": "PG", "ppg": 9.4, "rpg": 2.5, "apg": 3.6},
        {"name": "Stanley Johnson", "pos": "SF", "ppg": 6.9, "rpg": 3.2, "apg": 1.5},
        {"name": "Frank Kaminsky", "pos": "C", "ppg": 8.6, "rpg": 4.3, "apg": 1.4},
        {"name": "Cristiano Felicio", "pos": "C", "ppg": 4.8, "rpg": 4.5, "apg": 0.6},
        {"name": "Troy Williams", "pos": "SF", "ppg": 7.2, "rpg": 3.8, "apg": 1.1},
        {"name": "Tyler Ulis", "pos": "PG", "ppg": 7.7, "rpg": 1.9, "apg": 4.0},
        {"name": "DeAndre Liggins", "pos": "SG", "ppg": 4.4, "rpg": 2.5, "apg": 1.6},
        {"name": "Jameer Nelson", "pos": "PG", "ppg": 10.3, "rpg": 2.4, "apg": 5.0},
        {"name": "Ty Lawson", "pos": "PG", "ppg": 12.7, "rpg": 2.5, "apg": 6.0},
        {"name": "Brandon Bass", "pos": "PF", "ppg": 8.8, "rpg": 4.7, "apg": 0.7},
    ]
    
    # Add all free agents
    jersey_num = 1
    for fa_data in free_agents:
        # Height/weight based on position
        if fa_data["pos"] in ["PG", "SG"]:
            height = f"{random.randint(6, 6)}'{random.randint(2, 7)}\""
            weight = random.randint(180, 210)
        elif fa_data["pos"] == "SF":
            height = f"{random.randint(6, 6)}'{random.randint(6, 11)}\""
            weight = random.randint(210, 230)
        elif fa_data["pos"] == "PF":
            height = f"{random.randint(6, 6)}'{random.randint(8, 11)}\""
            weight = random.randint(225, 250)
        else:  # C
            height = f"{random.randint(6, 7)}'{random.randint(10, 11)}\""
            weight = random.randint(240, 280)
        
        player = Player(
            name=fa_data["name"],
            team_id=fa_team.id,
            position=fa_data["pos"],
            jersey_number=jersey_num,
            height=height,
            weight=weight,
            ppg=fa_data.get("ppg", 10.0),
            rpg=fa_data.get("rpg", 4.0),
            apg=fa_data.get("apg", 2.0),
            spg=round(random.uniform(0.5, 1.5), 1),
            bpg=round(random.uniform(0.2, 1.0), 1),
            fg_pct=round(random.uniform(0.38, 0.48), 3),
            three_pt_pct=round(random.uniform(0.30, 0.38), 3),
            ft_pct=round(random.uniform(0.70, 0.85), 3),
            mpg=round(random.uniform(18, 28), 1)
        )
        session.add(player)
        jersey_num += 1
    
    session.commit()
    print(f"✓ Added {len(free_agents)} free agents to the pool!")
    print(f"✓ Total free agents: {session.query(Player).filter_by(team_id=fa_team.id).count()}")
    session.close()

if __name__ == "__main__":
    add_free_agents()
