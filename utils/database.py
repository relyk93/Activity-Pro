import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'activitypro.db')

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Residents table
    c.execute('''CREATE TABLE IF NOT EXISTS residents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER,
        room TEXT,
        birthday TEXT,
        photo_url TEXT,
        mobility TEXT DEFAULT 'independent',
        cognitive TEXT DEFAULT 'intact',
        dietary TEXT,
        disabilities TEXT,
        special_needs TEXT,
        notes TEXT,
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # Activities table
    c.execute('''CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        instructions TEXT,
        supplies TEXT,
        category TEXT,
        duration_minutes INTEGER DEFAULT 60,
        cost_estimate TEXT DEFAULT 'Free',
        difficulty TEXT DEFAULT 'easy',
        group_type TEXT DEFAULT 'all',
        disability_friendly TEXT,
        min_participants INTEGER DEFAULT 1,
        max_participants INTEGER DEFAULT 20,
        is_special_needs INTEGER DEFAULT 0,
        created_by TEXT DEFAULT 'AI',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # Calendar events
    c.execute('''CREATE TABLE IF NOT EXISTS calendar_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        activity_id INTEGER,
        title TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT,
        location TEXT,
        group_type TEXT DEFAULT 'all',
        notes TEXT,
        staff_note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (activity_id) REFERENCES activities(id)
    )''')

    # Engagement / ratings
    c.execute('''CREATE TABLE IF NOT EXISTS engagements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        resident_id INTEGER,
        engaged INTEGER DEFAULT 0,
        rating INTEGER DEFAULT 0,
        mood_before INTEGER,
        mood_after INTEGER,
        staff_note TEXT,
        recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES calendar_events(id),
        FOREIGN KEY (resident_id) REFERENCES residents(id)
    )''')

    # Facility / settings
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    # Subscription
    c.execute('''CREATE TABLE IF NOT EXISTS subscription (
        id INTEGER PRIMARY KEY,
        tier TEXT DEFAULT 'free',
        facility_name TEXT DEFAULT 'My Facility',
        admin_email TEXT,
        resident_limit INTEGER DEFAULT 15,
        expires_at TEXT
    )''')

    # Seed subscription if not exists
    c.execute("SELECT COUNT(*) FROM subscription")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO subscription (tier, facility_name, resident_limit) VALUES ('pro', 'Sunrise Senior Living', 999)")

    # Seed sample activities
    c.execute("SELECT COUNT(*) FROM activities")
    if c.fetchone()[0] == 0:
        _seed_activities(c)

    # Seed sample residents
    c.execute("SELECT COUNT(*) FROM residents")
    if c.fetchone()[0] == 0:
        _seed_residents(c)

    conn.commit()
    conn.close()

def _seed_activities(c):
    activities = [
        ("Morning Chair Yoga", "Gentle yoga adapted for seniors, performed from a seated position.",
         "1. Begin with deep breathing (3 breaths)\n2. Neck rolls left and right (5 each)\n3. Shoulder rolls forward and back (10 each)\n4. Seated spinal twist each side\n5. Ankle circles and foot flexes\n6. Wrist stretches\n7. Close with gratitude meditation",
         "Chairs without armrests (or pushed aside), soft music playlist, optional yoga blocks",
         "mindful", 45, "Free", "easy", "all",
         "wheelchair,limited_mobility,arthritis", 2, 20, 0),
        ("Memory Lane Photo Sharing", "Residents bring or are shown old photos and share stories.",
         "1. Gather residents in a circle\n2. Display or pass around printed photos (can be staff-collected or residents bring their own)\n3. Ask open-ended prompts: 'What do you remember about this time?'\n4. Encourage others to share similar memories\n5. Record favorite stories with permission",
         "Printed photos (old magazines, family photos), comfortable seating, optional recording device",
         "cognitive", 60, "Free", "easy", "all",
         "dementia,hearing_loss,vision_impairment", 2, 15, 0),
        ("Tabletop Gardening", "Plant herbs or flowers in small pots at a table.",
         "1. Cover tables with newspaper\n2. Provide each resident a small pot, soil, and seeds/seedling\n3. Guide planting step-by-step\n4. Label each pot with resident's name\n5. Display in common area or send to room\n6. Schedule weekly watering check-ins",
         "Small terracotta pots ($1 each), potting soil, herb seeds or seedlings (basil, mint), newspaper, gloves",
         "creative", 60, "$5–10 total", "easy", "all",
         "wheelchair,limited_mobility,dementia", 2, 12, 0),
        ("Balloon Volleyball", "Light-touch volleyball using balloons instead of balls.",
         "1. Arrange chairs in two facing rows or a circle\n2. Inflate 2–3 balloons\n3. Tap balloon back and forth — goal is to keep it in the air\n4. Keep score if desired (team fun, not competitive)\n5. Celebrate every rally!",
         "Balloons (2–3), optional pool noodles as 'paddles', open floor space",
         "physical", 30, "Under $2", "easy", "all",
         "wheelchair,limited_mobility,arthritis", 4, 20, 0),
        ("Guided Meditation — Ocean Breeze", "Calming 20-minute guided audio meditation.",
         "1. Dim lights, play soft ocean ambient sounds\n2. Ask residents to close eyes or find a soft gaze\n3. Read or play: 'Imagine standing on warm sand...'\n4. Guide through body scan: feet, legs, belly, chest, hands, face\n5. Allow 5 minutes of silence\n6. Bring back gently: wiggle fingers, take a deep breath, open eyes",
         "Bluetooth speaker, ocean sounds audio (free on YouTube/Spotify), dimmer or curtains",
         "mindful", 25, "Free", "easy", "all",
         "dementia,anxiety,depression,wheelchair,vision_impairment", 1, 25, 0),
        ("Bingo with a Twist", "Classic bingo with themed cards (nature, animals, food).",
         "1. Print themed bingo cards (free online)\n2. Use large-print cards for vision-impaired residents\n3. Call items aloud AND show picture cards\n4. Small prizes: wrapped candy, stickers, gift cards\n5. Play 3–5 rounds; rotate callers",
         "Printed bingo cards (free), markers or chips, small prizes ($1–5), picture cards",
         "social", 60, "$5–15 for prizes", "easy", "all",
         "hearing_loss,vision_impairment,dementia,wheelchair", 4, 30, 0),
        ("Sensory Bin Exploration", "Tactile activity with rice, beans, or sand in a bin with hidden objects.",
         "1. Fill bin with dry rice, beans, or kinetic sand\n2. Hide small smooth objects (spoons, plastic animals, buttons)\n3. Residents use hands to find objects\n4. Encourage describing textures\n5. For memory residents: name objects as found",
         "Plastic storage bin, dry rice or beans (2 lbs, ~$2), small safe objects to hide",
         "cognitive", 30, "Under $5", "easy", "special_needs",
         "dementia,alzheimers,anxiety,vision_impairment", 1, 8, 1),
        ("Armchair Travel — Italy", "Virtual tour of Italy with music, food tasting, and photos.",
         "1. Set up projector or large screen with Italian scenery images/video\n2. Play Italian music (Volare, O Sole Mio)\n3. Provide small tasting: breadsticks, olives, small pasta bite\n4. Discuss: Has anyone visited Italy? What do they know?\n5. Share printed postcards as keepsakes",
         "Screen/projector, Italian music playlist (free), small food items (~$10), printed postcards",
         "social", 60, "$10–15", "easy", "all",
         "wheelchair,limited_mobility,dementia,hearing_loss", 3, 25, 0),
        ("Hand Massage & Lotion Circle", "Residents gently massage each other's hands with scented lotion.",
         "1. Seat residents in a circle\n2. Provide unscented AND lightly scented lotion options\n3. Demonstrate hand massage: palm circles, finger pulls, wrist rotation\n4. Pairs or self-massage\n5. Play soft background music\n6. Check for latex/fragrance allergies beforehand",
         "Lotion (dollar store or donated), soft music, hand towels",
         "mindful", 30, "Under $5", "easy", "special_needs",
         "dementia,anxiety,limited_mobility,arthritis", 2, 16, 1),
        ("Adaptive Art — Watercolor Wash", "Simple watercolor painting with large brushes and pre-drawn outlines.",
         "1. Pre-draw simple outlines on watercolor paper (flowers, birds, houses)\n2. Set up one color at a time to avoid overwhelm\n3. Large, easy-grip brushes\n4. Encourage freestyle — no wrong answers\n5. Display finished art in hallway with resident's name",
         "Watercolor paint set ($3–5), large brushes, watercolor paper, water cups, smocks",
         "creative", 60, "$5–10", "easy", "all",
         "dementia,limited_mobility,arthritis,vision_impairment", 1, 12, 0),
        ("Trivia Tuesday — Decades Edition", "Fun trivia about the 1940s–1970s that resonates with residents.",
         "1. Divide into small teams of 3–4\n2. Ask 5 rounds of 5 questions each (music, sports, history, TV, pop culture)\n3. Use visual aids: album covers, old ads\n4. Keep score on whiteboard\n5. Award small prizes to all teams",
         "Printed trivia questions (free to make), whiteboard and markers, small prizes",
         "cognitive", 60, "Free–$10", "easy", "all",
         "hearing_loss,vision_impairment", 4, 24, 0),
        ("Morning Stretch & Breathwork", "10-minute daily morning movement ritual to start the day right.",
         "1. Begin seated or standing (both options available)\n2. Inhale arms up — exhale fold forward (seated: reach for toes)\n3. Side stretches left and right\n4. Box breathing: inhale 4 counts, hold 4, exhale 4, hold 4 (repeat 4x)\n5. Positive affirmation to close: 'I am well. I am here. It is a good day.'",
         "Chairs (optional), soft music or silence",
         "physical", 15, "Free", "easy", "all",
         "wheelchair,limited_mobility,arthritis,dementia,anxiety", 1, 30, 0),
    ]
    for a in activities:
        c.execute("""INSERT INTO activities
            (title, description, instructions, supplies, category, duration_minutes, cost_estimate,
             difficulty, group_type, disability_friendly, min_participants, max_participants, is_special_needs)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", a)

def _seed_residents(c):
    residents = [
        ("Margaret Thompson", 82, "101", "1944-03-15", "independent", "intact", "Low sodium", "arthritis", "Loves gardening and music", "Sweet lady, very social"),
        ("Robert 'Bob' Jenkins", 78, "102", "1948-07-22", "walker", "mild_impairment", "Diabetic", "hearing_loss", "Enjoys trivia and sports", "Hard of hearing — speak loudly on left side"),
        ("Dorothy Alvarez", 91, "103", "1935-01-08", "wheelchair", "moderate_impairment", "None", "dementia,limited_mobility", "Used to love painting", "Stage 2 dementia, responds well to music from the 1950s"),
        ("Harold Kim", 75, "104", "1951-09-30", "independent", "intact", "Vegetarian", "vision_impairment", "Chess, reading, history", "Low vision — use large print materials"),
        ("Evelyn Moore", 88, "105", "1938-05-12", "cane", "intact", "Gluten free", "anxiety,arthritis", "Knitting, church choir, baking", "Anxious in crowds — seat near exit"),
        ("Frank Deluca", 80, "106", "1946-11-04", "walker", "mild_impairment", "None", "parkinson", "Baseball, woodworking", "Parkinson's — good days and bad days, tremors affect fine motor"),
        ("Grace Washington", 72, "107", "1954-02-19", "independent", "intact", "None", "", "Dancing, cooking, storytelling", "Very energetic — loves leading activities"),
        ("Walter Nguyen", 85, "108", "1941-08-06", "wheelchair", "moderate_impairment", "Low sodium", "dementia,wheelchair", "Old movies, card games", "Responds to Vietnamese music, family visits Sundays"),
    ]
    for r in residents:
        c.execute("""INSERT INTO residents
            (name, age, room, birthday, mobility, cognitive, dietary, disabilities, special_needs, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?)""", r)

# ---- CRUD helpers ----

def get_residents(active_only=True):
    conn = get_conn()
    q = "SELECT * FROM residents"
    if active_only:
        q += " WHERE active = 1"
    q += " ORDER BY name"
    rows = conn.execute(q).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_resident(resident_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM residents WHERE id=?", (resident_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def save_resident(data, resident_id=None):
    conn = get_conn()
    if resident_id:
        conn.execute("""UPDATE residents SET name=?, age=?, room=?, birthday=?, mobility=?,
            cognitive=?, dietary=?, disabilities=?, special_needs=?, notes=?, updated_at=?
            WHERE id=?""",
            (data['name'], data['age'], data['room'], data['birthday'], data['mobility'],
             data['cognitive'], data['dietary'], data['disabilities'], data['special_needs'],
             data['notes'], datetime.now().isoformat(), resident_id))
    else:
        conn.execute("""INSERT INTO residents (name, age, room, birthday, mobility,
            cognitive, dietary, disabilities, special_needs, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (data['name'], data['age'], data['room'], data['birthday'], data['mobility'],
             data['cognitive'], data['dietary'], data['disabilities'], data['special_needs'],
             data['notes']))
    conn.commit()
    conn.close()

def get_activities(group_type=None, category=None):
    conn = get_conn()
    q = "SELECT * FROM activities WHERE 1=1"
    params = []
    if group_type and group_type != "all":
        q += " AND (group_type=? OR group_type='all')"
        params.append(group_type)
    if category and category != "All":
        q += " AND category=?"
        params.append(category)
    q += " ORDER BY title"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_activity(activity_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM activities WHERE id=?", (activity_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def save_activity(data, activity_id=None):
    conn = get_conn()
    if activity_id:
        conn.execute("""UPDATE activities SET title=?, description=?, instructions=?, supplies=?,
            category=?, duration_minutes=?, cost_estimate=?, difficulty=?, group_type=?,
            disability_friendly=?, is_special_needs=? WHERE id=?""",
            (data['title'], data['description'], data['instructions'], data['supplies'],
             data['category'], data['duration_minutes'], data['cost_estimate'], data['difficulty'],
             data['group_type'], data['disability_friendly'], data['is_special_needs'], activity_id))
    else:
        conn.execute("""INSERT INTO activities (title, description, instructions, supplies,
            category, duration_minutes, cost_estimate, difficulty, group_type, disability_friendly, is_special_needs, created_by)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (data['title'], data['description'], data['instructions'], data['supplies'],
             data['category'], data['duration_minutes'], data['cost_estimate'], data['difficulty'],
             data['group_type'], data['disability_friendly'], data['is_special_needs'], data.get('created_by', 'Manual')))
        activity_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return activity_id

def get_events(date_from=None, date_to=None):
    conn = get_conn()
    q = "SELECT e.*, a.category, a.duration_minutes, a.supplies, a.instructions, a.cost_estimate, a.disability_friendly FROM calendar_events e LEFT JOIN activities a ON e.activity_id = a.id WHERE 1=1"
    params = []
    if date_from:
        q += " AND e.date >= ?"
        params.append(str(date_from))
    if date_to:
        q += " AND e.date <= ?"
        params.append(str(date_to))
    q += " ORDER BY e.date, e.time"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_event(data):
    conn = get_conn()
    conn.execute("""INSERT INTO calendar_events (activity_id, title, date, time, location, group_type, notes)
        VALUES (?,?,?,?,?,?,?)""",
        (data.get('activity_id'), data['title'], data['date'], data.get('time', '10:00'),
         data.get('location', 'Activity Room'), data.get('group_type', 'all'), data.get('notes', '')))
    event_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return event_id

def delete_event(event_id):
    conn = get_conn()
    conn.execute("DELETE FROM calendar_events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()

def save_engagement(data):
    conn = get_conn()
    # Check if already exists
    existing = conn.execute(
        "SELECT id FROM engagements WHERE event_id=? AND resident_id=?",
        (data['event_id'], data['resident_id'])
    ).fetchone()
    if existing:
        conn.execute("""UPDATE engagements SET engaged=?, rating=?, mood_before=?, mood_after=?, staff_note=?, recorded_at=?
            WHERE event_id=? AND resident_id=?""",
            (data['engaged'], data['rating'], data.get('mood_before'), data.get('mood_after'),
             data.get('staff_note', ''), datetime.now().isoformat(),
             data['event_id'], data['resident_id']))
    else:
        conn.execute("""INSERT INTO engagements (event_id, resident_id, engaged, rating, mood_before, mood_after, staff_note)
            VALUES (?,?,?,?,?,?,?)""",
            (data['event_id'], data['resident_id'], data['engaged'], data['rating'],
             data.get('mood_before'), data.get('mood_after'), data.get('staff_note', '')))
    conn.commit()
    conn.close()

def get_engagements(event_id=None, resident_id=None):
    conn = get_conn()
    q = """SELECT eng.*, r.name as resident_name, e.title as event_title, e.date as event_date
           FROM engagements eng
           JOIN residents r ON eng.resident_id = r.id
           JOIN calendar_events e ON eng.event_id = e.id
           WHERE 1=1"""
    params = []
    if event_id:
        q += " AND eng.event_id=?"
        params.append(event_id)
    if resident_id:
        q += " AND eng.resident_id=?"
        params.append(resident_id)
    q += " ORDER BY eng.recorded_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_subscription():
    conn = get_conn()
    row = conn.execute("SELECT * FROM subscription WHERE id=1").fetchone()
    conn.close()
    return dict(row) if row else {"tier": "free", "resident_limit": 15}

def update_subscription(tier, facility_name=None):
    conn = get_conn()
    limits = {"free": 15, "pro": 999, "enterprise": 9999}
    conn.execute("UPDATE subscription SET tier=?, resident_limit=? WHERE id=1",
                 (tier, limits.get(tier, 15)))
    if facility_name:
        conn.execute("UPDATE subscription SET facility_name=? WHERE id=1", (facility_name,))
    conn.commit()
    conn.close()
