import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'activitypro.db')
PHOTOS_DIR = os.path.join(os.path.dirname(__file__), '..', 'photos')

def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100_000)
    return salt.hex() + ':' + key.hex()

def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, key_hex = stored.split(':')
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100_000)
        return key.hex() == key_hex
    except Exception:
        return False

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

    # Staff accounts
    c.execute('''CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'staff',
        full_name TEXT,
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # Activity photos
    c.execute('''CREATE TABLE IF NOT EXISTS activity_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        resident_id INTEGER,
        filename TEXT NOT NULL,
        caption TEXT,
        staff_id INTEGER,
        taken_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES calendar_events(id),
        FOREIGN KEY (resident_id) REFERENCES residents(id),
        FOREIGN KEY (staff_id) REFERENCES staff(id)
    )''')

    # Phase 2: EHR sync columns
    for col in ("ehr_id TEXT", "ehr_provider TEXT"):
        try:
            c.execute(f"ALTER TABLE residents ADD COLUMN {col}")
        except Exception:
            pass

    # Phase 3: Family contact columns
    for col in ("family_name TEXT", "family_email TEXT", "last_update_sent TEXT"):
        try:
            c.execute(f"ALTER TABLE residents ADD COLUMN {col}")
        except Exception:
            pass

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

    # Seed default staff accounts
    c.execute("SELECT COUNT(*) FROM staff")
    if c.fetchone()[0] == 0:
        _seed_staff(c)

    # Ensure photos directory exists
    os.makedirs(PHOTOS_DIR, exist_ok=True)

    # Seed sample activities
    c.execute("SELECT COUNT(*) FROM activities")
    if c.fetchone()[0] == 0:
        _seed_activities(c)

    # Seed sample residents
    c.execute("SELECT COUNT(*) FROM residents")
    if c.fetchone()[0] == 0:
        _seed_residents(c)

    # Seed demo calendar events + engagement history
    c.execute("SELECT COUNT(*) FROM calendar_events")
    if c.fetchone()[0] == 0:
        _seed_demo_events(c)

    conn.commit()
    conn.close()

def _seed_staff(c):
    accounts = [
        ("director", _hash_password("ActivityPro2024!"), "director", "Activity Director"),
        ("staff1",   _hash_password("Staff2024!"),       "staff",    "Floor Staff"),
    ]
    for username, pw_hash, role, full_name in accounts:
        c.execute("INSERT INTO staff (username, password_hash, role, full_name) VALUES (?,?,?,?)",
                  (username, pw_hash, role, full_name))

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

def _seed_demo_events(c):
    """Seed two weeks of calendar events + realistic engagement history for demo."""
    from datetime import date, timedelta
    today = date.today()

    # activity_id map: 1=Chair Yoga, 2=Memory Lane, 3=Gardening, 4=Balloon Volleyball,
    #                  5=Meditation, 6=Bingo, 7=Sensory Bin, 8=Armchair Travel,
    #                  9=Hand Massage, 10=Watercolor, 11=Trivia, 12=Morning Stretch

    schedule = [
        # (days_offset, activity_id, title, time, location)
        (-13, 12, "Morning Stretch & Breathwork", "09:00", "Main Hall"),
        (-13,  6, "Bingo with a Twist",           "14:00", "Activity Room"),
        (-12,  1, "Morning Chair Yoga",            "09:30", "Wellness Room"),
        (-12, 11, "Trivia Tuesday — Decades Edition", "14:00", "Dining Hall"),
        (-11,  2, "Memory Lane Photo Sharing",     "10:00", "Sunroom"),
        (-11,  4, "Balloon Volleyball",             "15:00", "Main Hall"),
        (-10,  5, "Guided Meditation",             "09:00", "Wellness Room"),
        (-10, 10, "Adaptive Art — Watercolor Wash","14:00", "Art Room"),
        (-9,  12, "Morning Stretch & Breathwork",  "09:00", "Main Hall"),
        (-9,   8, "Armchair Travel — Italy",       "14:00", "Activity Room"),
        (-7,   1, "Morning Chair Yoga",            "09:30", "Wellness Room"),
        (-7,   6, "Bingo with a Twist",            "14:00", "Activity Room"),
        (-6,  11, "Trivia Tuesday — Decades Edition","14:00","Dining Hall"),
        (-5,   3, "Tabletop Gardening",            "10:00", "Garden Patio"),
        (-5,   9, "Hand Massage & Lotion Circle",  "15:00", "Sunroom"),
        (-4,  12, "Morning Stretch & Breathwork",  "09:00", "Main Hall"),
        (-4,  10, "Adaptive Art — Watercolor Wash","14:00", "Art Room"),
        (-3,   2, "Memory Lane Photo Sharing",     "10:00", "Sunroom"),
        (-3,   4, "Balloon Volleyball",            "15:00", "Main Hall"),
        (-2,   1, "Morning Chair Yoga",            "09:30", "Wellness Room"),
        (-2,   5, "Guided Meditation",             "14:00", "Wellness Room"),
        (-1,  12, "Morning Stretch & Breathwork",  "09:00", "Main Hall"),
        (-1,   6, "Bingo with a Twist",            "14:00", "Activity Room"),
        # Today
        ( 0,   1, "Morning Chair Yoga",            "09:30", "Wellness Room"),
        ( 0,  11, "Trivia Tuesday — Decades Edition","14:00","Dining Hall"),
        ( 0,   9, "Hand Massage & Lotion Circle",  "16:00", "Sunroom"),
        # Future this week
        ( 1,   3, "Tabletop Gardening",            "10:00", "Garden Patio"),
        ( 1,   8, "Armchair Travel — Italy",       "14:00", "Activity Room"),
        ( 2,  12, "Morning Stretch & Breathwork",  "09:00", "Main Hall"),
        ( 2,  10, "Adaptive Art — Watercolor Wash","14:00", "Art Room"),
        ( 3,   6, "Bingo with a Twist",            "14:00", "Activity Room"),
        ( 3,   4, "Balloon Volleyball",            "15:00", "Main Hall"),
    ]

    event_ids = []
    for days_offset, act_id, title, time_, location in schedule:
        event_date = (today + timedelta(days=days_offset)).isoformat()
        c.execute("""INSERT INTO calendar_events (activity_id, title, date, time, location, group_type)
                     VALUES (?,?,?,?,?,?)""", (act_id, title, event_date, time_, location, "all"))
        event_ids.append((c.lastrowid, days_offset, act_id))

    # Resident IDs 1-8, realistic engagement patterns
    # Margaret(1): high engager, great mood lifts
    # Bob(2): good engager, hearing issues noted
    # Dorothy(3): moderate, dementia affects engagement
    # Harold(4): selective, prefers cognitive
    # Evelyn(5): moderate, anxiety some days
    # Frank(6): variable due to Parkinson's
    # Grace(7): excellent engager, mood always improves
    # Walter(8): low engager recently (at-risk demo)

    import random
    random.seed(42)  # deterministic so data looks the same every time

    engagement_patterns = {
        1: {"base_rate": 0.90, "mood_before": [3,4,4,4,5], "mood_lift": [1,1,2,2,1]},
        2: {"base_rate": 0.75, "mood_before": [3,3,4,4,3], "mood_lift": [1,1,1,2,0]},
        3: {"base_rate": 0.60, "mood_before": [2,3,3,2,3], "mood_lift": [1,2,1,1,2]},
        4: {"base_rate": 0.80, "mood_before": [4,4,5,4,4], "mood_lift": [0,1,0,1,1]},
        5: {"base_rate": 0.65, "mood_before": [3,3,4,3,4], "mood_lift": [1,1,2,1,1]},
        6: {"base_rate": 0.55, "mood_before": [3,2,3,3,2], "mood_lift": [1,1,2,0,1]},
        7: {"base_rate": 0.95, "mood_before": [4,4,5,5,4], "mood_lift": [1,1,1,2,1]},
        8: {"base_rate": 0.30, "mood_before": [2,2,3,2,2], "mood_lift": [1,0,1,1,0]},
    }

    notes_pool = {
        True:  ["Very engaged today", "Smiled throughout", "Led the group at one point",
                 "Great participation", "Asked to do this again", "Uplifting session for them"],
        False: ["Tired today, sat quietly", "Declined to participate", "Left early",
                "Not feeling well", "Low energy", "Distracted, may try again next time"],
    }

    for event_id, days_offset, act_id in event_ids:
        if days_offset >= 0:  # only log past events
            continue
        for resident_id in range(1, 9):
            pat = engagement_patterns[resident_id]
            engaged = random.random() < pat["base_rate"]
            mood_before = random.choice(pat["mood_before"])
            lift = random.choice(pat["mood_lift"]) if engaged else 0
            mood_after = min(5, mood_before + lift)
            note = random.choice(notes_pool[engaged])
            c.execute("""INSERT INTO engagements
                (event_id, resident_id, engaged, rating, mood_before, mood_after, staff_note)
                VALUES (?,?,?,?,?,?,?)""",
                (event_id, resident_id, int(engaged),
                 random.randint(3,5) if engaged else random.randint(1,3),
                 mood_before, mood_after, note))

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

# ---- Staff CRUD ----

def authenticate_staff(username: str, password: str):
    """Returns staff dict on success, None on failure."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM staff WHERE username=? AND active=1", (username,)
    ).fetchone()
    conn.close()
    if row and _verify_password(password, row['password_hash']):
        return dict(row)
    return None

def get_all_staff():
    conn = get_conn()
    rows = conn.execute("SELECT id, username, role, full_name, active, created_at FROM staff ORDER BY role, full_name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_staff(username: str, password: str, role: str, full_name: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO staff (username, password_hash, role, full_name) VALUES (?,?,?,?)",
        (username, _hash_password(password), role, full_name)
    )
    conn.commit()
    conn.close()

def update_staff(staff_id: int, full_name: str, role: str, new_password: str = None):
    conn = get_conn()
    if new_password:
        conn.execute(
            "UPDATE staff SET full_name=?, role=?, password_hash=? WHERE id=?",
            (full_name, role, _hash_password(new_password), staff_id)
        )
    else:
        conn.execute(
            "UPDATE staff SET full_name=?, role=? WHERE id=?",
            (full_name, role, staff_id)
        )
    conn.commit()
    conn.close()

def deactivate_staff(staff_id: int):
    conn = get_conn()
    conn.execute("UPDATE staff SET active=0 WHERE id=?", (staff_id,))
    conn.commit()
    conn.close()

# ---- Photo CRUD ----

def save_photo(event_id: int, resident_id: int, filename: str, caption: str, staff_id: int):
    conn = get_conn()
    conn.execute(
        "INSERT INTO activity_photos (event_id, resident_id, filename, caption, staff_id) VALUES (?,?,?,?,?)",
        (event_id, resident_id, filename, caption, staff_id)
    )
    conn.commit()
    conn.close()

def get_photos(event_id: int = None, resident_id: int = None):
    conn = get_conn()
    q = "SELECT * FROM activity_photos WHERE 1=1"
    params = []
    if event_id:
        q += " AND event_id=?"
        params.append(event_id)
    if resident_id:
        q += " AND resident_id=?"
        params.append(resident_id)
    q += " ORDER BY taken_at DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_photo(photo_id: int):
    conn = get_conn()
    row = conn.execute("SELECT filename FROM activity_photos WHERE id=?", (photo_id,)).fetchone()
    if row:
        path = os.path.join(PHOTOS_DIR, row['filename'])
        if os.path.exists(path):
            os.remove(path)
        conn.execute("DELETE FROM activity_photos WHERE id=?", (photo_id,))
    conn.commit()
    conn.close()

# ---- Resident EHR helpers ----

def update_resident_ehr(resident_id: int, ehr_id: str, ehr_provider: str):
    conn = get_conn()
    conn.execute(
        "UPDATE residents SET ehr_id=?, ehr_provider=? WHERE id=?",
        (ehr_id, ehr_provider, resident_id)
    )
    conn.commit()
    conn.close()

# ---- Phase 3: At-risk & briefing queries ----

def get_at_risk_residents(days_threshold: int = 14) -> list:
    """Residents with no engagement recorded in the last N days."""
    from datetime import date, timedelta
    cutoff = str(date.today() - timedelta(days=days_threshold))
    conn = get_conn()
    rows = conn.execute("""
        SELECT r.* FROM residents r
        WHERE r.active = 1
        AND (
            NOT EXISTS (SELECT 1 FROM engagements e WHERE e.resident_id = r.id)
            OR NOT EXISTS (
                SELECT 1 FROM engagements e
                JOIN calendar_events ev ON e.event_id = ev.id
                WHERE e.resident_id = r.id AND ev.date >= ?
            )
        )
        ORDER BY r.name
    """, (cutoff,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_declining_mood_residents() -> list:
    """Residents whose last 3 recorded mood_after scores are strictly declining."""
    conn = get_conn()
    residents = conn.execute("SELECT * FROM residents WHERE active=1").fetchall()
    declining = []
    for r in residents:
        moods = conn.execute("""
            SELECT mood_after FROM engagements
            WHERE resident_id=? AND mood_after IS NOT NULL
            ORDER BY recorded_at DESC LIMIT 3
        """, (r['id'],)).fetchall()
        vals = [m['mood_after'] for m in moods]
        if len(vals) == 3 and vals[0] < vals[1] < vals[2]:
            declining.append(dict(r))
    conn.close()
    return declining

def get_resident_mood_trend(resident_id: int, limit: int = 6) -> list:
    """Return last N mood_after scores (oldest first) for sparkline display."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT e.mood_after, ev.date FROM engagements e
        JOIN calendar_events ev ON e.event_id = ev.id
        WHERE e.resident_id=? AND e.mood_after IS NOT NULL
        ORDER BY ev.date DESC LIMIT ?
    """, (resident_id, limit)).fetchall()
    conn.close()
    return list(reversed([dict(r) for r in rows]))

def get_last_activity(resident_id: int) -> dict | None:
    """Return the most recent engagement record for a resident."""
    conn = get_conn()
    row = conn.execute("""
        SELECT e.*, ev.title as event_title, ev.date as event_date, ev.category
        FROM engagements e
        JOIN calendar_events ev ON e.event_id = ev.id
        WHERE e.resident_id=?
        ORDER BY ev.date DESC LIMIT 1
    """, (resident_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_event_history_for_resident(resident_id: int, activity_title: str) -> dict | None:
    """Return the last time a resident attended a specific activity."""
    conn = get_conn()
    row = conn.execute("""
        SELECT e.*, ev.date as event_date, ev.title as event_title
        FROM engagements e
        JOIN calendar_events ev ON e.event_id = ev.id
        WHERE e.resident_id=? AND ev.title=?
        ORDER BY ev.date DESC LIMIT 1
    """, (resident_id, activity_title)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_resident_family(resident_id: int, family_name: str, family_email: str):
    conn = get_conn()
    conn.execute(
        "UPDATE residents SET family_name=?, family_email=? WHERE id=?",
        (family_name, family_email, resident_id)
    )
    conn.commit()
    conn.close()

def mark_family_update_sent(resident_id: int):
    conn = get_conn()
    conn.execute(
        "UPDATE residents SET last_update_sent=? WHERE id=?",
        (str(datetime.now().date()), resident_id)
    )
    conn.commit()
    conn.close()
