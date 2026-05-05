import streamlit as st
from datetime import datetime
import pandas as pd
import mysql.connector
import hashlib
import threading
import pygame
import random
import base64

#-----------TO RUN-------------
#py -3.12 -m streamlit run code.py 

#-------------------WATERMARK-----------------------
def get_base64_image(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode()

st.set_page_config(page_title="MINDMATES", layout="wide")

watermark_base64 = get_base64_image("images/watermark.png")

st.markdown(
    f"""
    <style>
    .full-watermark {{
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        opacity: 0.2;
        z-index: 9999;
        pointer-events: none;
        user-select: none;
    }}

    .full-watermark img {{
        width: 420px;
    }}
    </style>

    <div class="full-watermark">
        <img src="data:image/png;base64,{watermark_base64}">
    </div>
    """,
    unsafe_allow_html=True
)

#---------------------FEVICON-------------------------
st.set_page_config(
    page_icon="images/top logo.jpeg")

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="MINDMATES", layout="centered")

# -------------------- DATABASE CONNECTION --------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123Asi@456",
        database="mindmates2"
    )

# -------------------- PASSWORD UTILS --------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s)",
        (username, hash_password(password))
    )
    conn.commit()
    conn.close()

def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username, hash_password(password))
    )
    user = cursor.fetchone()
    conn.close()
    return user

# -------------------- SESSION STATE INIT --------------------
defaults = {
    "logged_in": False,
    "user": {},
    "user_id": None,
    "is_admin": False,
    "shooter_running": False,
    "shooter_thread": None,
    "page": "Home",
    "breathing_step": 0,
    "bubbles_popped": set()
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==================== LOGIN ====================
if not st.session_state.logged_in:
    #--------------------LOGO----------------------------
    col1, col2 = st.columns([2,10])
    with col1:
        st.image("images/logo.png", width=300)
    #-----------------------------------------------------
    st.title("🔐 MINDMATES Login")

    role = st.radio("Login as", ["User", "Admin"])

    if role == "User":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = authenticate_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.session_state.user_id = user["id"]
                st.session_state.is_admin = False
                st.session_state.page = "Home"
                st.success("Login successful")
            else:
                st.error("Invalid username or password")

        st.divider()
        st.subheader("Register")
        new_u = st.text_input("New Username")
        new_p = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            try:
                create_user(new_u, new_p)
                st.success("Account created. Please login.")
            except:
                st.error("Username already exists")

    else:
        admin_pass = st.text_input("Admin Password", type="password")
        if st.button("Login as Admin"):
            if admin_pass == "admin123":
                st.session_state.logged_in = True
                st.session_state.user = {"username": "Admin"}
                st.session_state.user_id = None
                st.session_state.is_admin = True
                st.session_state.page = "Q&A"
                st.success("Admin login successful")
            else:
                st.error("Wrong admin password")

    st.stop()

# ==================== SIDEBAR (SAFE) ====================

st.sidebar.image(
    "images/logo.png", 
    width=150  #Resize by changing width
)

if st.session_state.logged_in and st.session_state.user:
    st.sidebar.success(f"Logged in as {st.session_state.user.get('username','User')}")

    if st.sidebar.button("Logout"):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.stop()

# -------------------- NAVIGATION --------------------
if st.session_state.is_admin:
    st.session_state.page = "Q&A"
else:
    st.session_state.page = st.sidebar.radio(
        "Navigate",
        ["Home", "Q&A", "Mental Health Quiz", "Mood Tracker",
         "Daily Journal", "Stress Relief", "Resources"]
    )

user_id = st.session_state.user_id

# ==================== HOME ====================
if st.session_state.page == "Home":
    st.title("MINDMATES")
    st.write("A Digital Platform For Mental Wellness Support")
    st.image("images/meditating .jpeg", width=400,
             caption="“You don’t have to control your thoughts. You just have to stop letting them control you.” — Dan Millman")
    st.markdown("""
    Welcome to MINDMATES! This website provides tools to support your mental wellness journey:
    - **Q&A**: Ask questions and get answers from admins.
    - **Mental Health Quiz**: Assess your current mental health status.
    - **Mood Tracker**: Log your daily mood and see trends.
    - **Daily Journal**: Reflect on your thoughts and feelings.
    - **Stress Relief Games**: Engage in activities to reduce stress.
    - **Resources**: Access helpful links and information.
    
    Remember, this website is not a substitute for professional help. If you're in crisis, contact a mental health professional or hotline immediately.
    """)

# ==================== Q&A ====================
if st.session_state.page == "Q&A":
    st.header("Q & A")

    if not st.session_state.is_admin:
        with st.form("qa_form"):
            name = st.text_input("Name (optional)")
            category = st.selectbox("Category", ["General","Stress","Anxiety","Depression","Other"])
            question = st.text_area("Your question")
            if st.form_submit_button("Submit") and question.strip():
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO qa_questions (user_id,name,category,question) VALUES (%s,%s,%s,%s)",
                    (user_id, name or "Anonymous", category, question)
                )
                conn.commit()
                conn.close()
                st.success("Question submitted")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM qa_questions ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()

    for r in rows:
        st.markdown(f"**Q#{r['id']} — {r['category']}**")
        st.write(r["question"])
        if r["answer"]:
            st.success(r["answer"])
        elif st.session_state.is_admin:
            ans = st.text_area("Answer", key=r["id"])
            if st.button("Save", key=f"s{r['id']}"):
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("UPDATE qa_questions SET answer=%s WHERE id=%s",(ans,r["id"]))
                conn.commit()
                conn.close()
                st.success("Saved")

# ==================== QUIZ ====================
if st.session_state.page == "Mental Health Quiz":
    st.header("Mental Health Quiz")
    st.write("This quiz is based on the PHQ-9 scale. Answer the following questions to get an assessment of your mental health status.")
    questions = [
        "Little interest or pleasure in doing things",
        "Feeling down or hopeless",
        "Trouble sleeping",
        "Low energy",
        "Poor appetite",
        "Feeling bad about yourself",
        "Trouble concentrating",
        "Restlessness",
        "Thoughts of self-harm"
    ]
    opts = ["Not at all","Several days","More than half","Nearly every day"]
    score_map = [0,1,2,3]
    total = 0
    for q in questions:
        a = st.radio(q, opts)
        total += score_map[opts.index(a)]
    if st.button("Submit Quiz"):
        st.subheader("Your Assessment Results")
        st.success(f"**Total Score:** {total}/27")

        if total <= 4:
            severity = "Minimal Depression"
            analysis = "Your symptoms suggest minimal depression. This is a normal level of stress or sadness that most people experience from time to time. Continue maintaining healthy habits like exercise, sleep, and social connections."
        elif total <= 9:
            severity = "Mild Depression"
            analysis = "Your symptoms indicate mild depression. You may feel persistently sad or have lost interest in activities. Consider talking to a trusted friend, practicing mindfulness, or seeking professional advice if symptoms persist."
        elif total <= 14:
            severity = "Moderate Depression"
            analysis = "Your symptoms suggest moderate depression. This can significantly impact daily life. It's important to seek support from a mental health professional. Consider therapy, medication, or lifestyle changes."
        elif total <= 19:
            severity = "Moderately Severe Depression"
            analysis = "Your symptoms indicate moderately severe depression. This level requires professional intervention. Please consult a healthcare provider for a proper diagnosis and treatment plan, which may include therapy and medication."
        else:
            severity = "Severe Depression"
            analysis = "Your symptoms suggest severe depression. This is a serious condition that requires immediate professional help. Contact a mental health crisis hotline or emergency services if you're in danger. Seek comprehensive treatment including therapy and possibly medication."
        
        st.write(f"**Severity Level:** {severity}")
        st.write(f"**Detailed Analysis:** {analysis}")
        
        if total >= 10:
            st.warning("If you're experiencing thoughts of self-harm or suicide, please seek immediate help. Call emergency services or a crisis hotline.")
        
        st.info("This quiz is not a diagnostic tool. Please consult a qualified mental health professional for a proper assessment.")


# ==================== MOOD TRACKER ====================
if st.session_state.page == "Mood Tracker":
    st.header("Mood Tracker")
    st.write("Track your daily mood to see patterns over time.")
    mood = st.slider("How are you feeling today? (1 = Very Low, 10 = Excellent)", 1, 10, 5)
    date = st.date_input("Date", datetime.now().date())
    notes = st.text_area("Notes")
    if st.button("Save Mood"):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO mood_entries (user_id,mood_date,mood,notes) VALUES (%s,%s,%s,%s)",
            (user_id, datetime.now().date(), mood, notes)
        )
        conn.commit()
        conn.close()
        st.success("Mood saved")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM mood_entries ORDER BY mood_date ASC")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        df = pd.DataFrame(rows)
        df['mood_date'] = pd.to_datetime(df['mood_date'])
        st.line_chart(df.set_index('mood_date')['mood'])
        st.dataframe(df[['mood_date', 'mood', 'notes']])


# ==================== JOURNAL ====================
if st.session_state.page == "Daily Journal":
    st.header("Daily Journal")
    st.write("Write your thoughts and reflections. Your entries are private and stored locally.")
    with st.form("journal_form"):
        entry = st.text_area("What is on your mind today?", height=200)
        entry_date = st.date_input("Date", datetime.now().date())
        submitted_journal = st.form_submit_button("Save Entry")
        if submitted_journal:
            if not entry.strip():
                st.error("Please write something before saving.")
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO journal_entries (user_id,entry_date, entry)
                    VALUES (%s,%s, %s)
                """, (user_id,entry_date, entry.strip()))
                conn.commit()
                conn.close()
                st.success("Journal entry saved!")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM journal_entries ORDER BY entry_date DESC")
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        st.markdown(f"**{row['entry_date']}**")
        st.write(row['entry'])

# ==================== STRESS RELIEF ====================
if st.session_state.page == "Stress Relief":
    st.header("Stress Relief Games")
    st.write("Relax with these simple, interactive games.")
    if "breathing_started" not in st.session_state:
        st.session_state.breathing_started = False
    if "breathing_step" not in st.session_state:
        st.session_state.breathing_step = 0

    if not st.session_state.breathing_started:
        if st.button("Start Breathing Exercise"):
            st.session_state.breathing_started = True
            st.session_state.breathing_step = 0
            st.rerun()
    else:
        steps = [
            "Breathe in slowly through your nose for 4 seconds...",
            "Hold your breath for 4 seconds...",
            "Exhale slowly through your mouth for 4 seconds...",
            "Hold for 4 seconds...",
            "Repeat the cycle. Focus on your breath."
        ]
        
        if st.session_state.breathing_step < len(steps):
            st.write(steps[st.session_state.breathing_step])
            if st.button("Next"):
                st.session_state.breathing_step += 1
                st.rerun()
        else:
            st.success("Great job! You've completed a breathing cycle. Feel calmer?")
            if st.button("Restart Breathing"):
                st.session_state.breathing_started = False
                st.session_state.breathing_step = 0
                st.rerun()

    st.markdown("---")


    st.subheader("Bubble Pop Game")
    st.write("Click the bubbles to pop them and release stress! Pop as many as you can.")

    if "bubbles" not in st.session_state:
        st.session_state.bubbles = [True] * 9  # 9 bubbles in a 3x3 grid
    if "pop_count" not in st.session_state:
        st.session_state.pop_count = 0

    cols = st.columns(3)
    for i in range(3):
        with cols[i]:
            for j in range(3):
                idx = i * 3 + j
                if st.session_state.bubbles[idx]:
                    if st.button(f"💥", key=f"bubble_{idx}"):
                        st.session_state.bubbles[idx] = False
                        st.session_state.pop_count += 1
                        st.rerun()
                else:
                    st.write("🎉")  # Popped bubble

    st.write(f"**Bubbles Popped:** {st.session_state.pop_count}/9")
    if st.session_state.pop_count == 9:
        st.success("All bubbles popped! Great job relieving stress!")
        if st.button("Reset Bubbles"):
            st.session_state.bubbles = [True] * 9
            st.session_state.pop_count = 0
            st.rerun()

    st.markdown("---")


    st.subheader("Calm Clicker")
    st.write("Click the button to build your calm energy. Watch the progress bar fill up!")

    if "calm_clicks" not in st.session_state:
        st.session_state.calm_clicks = 0

    if st.button("🌟 Build Calm 🌟"):
        st.session_state.calm_clicks += 1

    progress = min(st.session_state.calm_clicks / 10, 1.0)  # 10 clicks to full
    st.progress(progress)
    st.write(f"**Calm Level:** {st.session_state.calm_clicks}/10")

    if st.session_state.calm_clicks >= 10:
        st.success("You're feeling super calm! 🧘‍♀️")
        if st.button("Reset Calm"):
            st.session_state.calm_clicks = 0

    st.markdown("---")
    
    st.subheader("🎮 Shooter Game")
    st.write("Controls: A = Left | D = Right | SPACE = Shoot | R = Restart")
    st.write("Click the button below to start the game in a separate Pygame window.")

    def shooter_game():
        pygame.init()
        width, height = 600, 400
        win = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Shooter Game")

        # Player & game variables
        player_x = width // 2
        player_y = height - 50
        player_speed = 2
        bullets = []
        bullet_speed = 3
        enemy_speed = 2
        enemies = [[random.randint(0, width - 30), random.randint(-150, -50)] for _ in range(5)]
        score = 0
        lives = 15 
        font = pygame.font.SysFont(None, 30)
        clock = pygame.time.Clock()
        running = True

        def reset_game():
            nonlocal player_x, bullets, enemies, score, lives
            player_x = width // 2
            bullets.clear()
            enemies[:] = [[random.randint(0, width - 30), random.randint(-150, -50)] for _ in range(5)]
            score = 0
            lives = 15 

        while running:
            clock.tick(60)
            win.fill((30, 30, 30))

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            keys = pygame.key.get_pressed()
            if keys[pygame.K_a]:
                player_x -= player_speed
            if keys[pygame.K_d]:
                player_x += player_speed
            if keys[pygame.K_SPACE]:
                if not bullets or bullets[-1][1] < player_y - 20:
                    bullets.append([player_x + 15, player_y])
            if keys[pygame.K_r]:
                reset_game()

            player_x = max(0, min(player_x, width - 30))

            # Draw player
            pygame.draw.rect(win, (0, 255, 0), (player_x, player_y, 30, 30))

            # Bullets
            for b in bullets[:]:
                b[1] -= bullet_speed
                pygame.draw.rect(win, (255, 255, 0), (b[0], b[1], 5, 10))
                if b[1] < 0:
                    bullets.remove(b)

            # Enemies
            for e in enemies[:]:
                e[1] += enemy_speed
                pygame.draw.rect(win, (255, 0, 0), (e[0], e[1], 30, 30))

                # Collision with bullets
                for b in bullets[:]:
                    if e[0] < b[0] < e[0] + 30 and e[1] < b[1] < e[1] + 30:
                        enemies.remove(e)
                        bullets.remove(b)
                        enemies.append([random.randint(0, width - 30), random.randint(-150, -50)])
                        score += 1
                        break

                # Enemy reaches bottom → lose 1 life
                if e[1] > height:
                    lives -= 1
                    enemies.remove(e)
                    enemies.append([random.randint(0, width - 30), random.randint(-150, -50)])
                    if lives <= 0:
                        running = False

            # Display **score only**
            score_text = font.render(f"Score: {score}", True, (255, 255, 255))
            win.blit(score_text, (10, 10))

            pygame.display.update()

        # Game Over screen
        win.fill((0, 0, 0))
        game_over_text = font.render(f"GAME OVER! Score: {score}", True, (255, 0, 0))
        restart_text = font.render("Press R to Restart or Close Window to Exit", True, (255, 255, 255))
        win.blit(game_over_text, (width // 2 - 100, height // 2 - 20))
        win.blit(restart_text, (width // 2 - 180, height // 2 + 20))
        pygame.display.update()

        # Wait for restart or exit
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                shooter_game()  # Restart
                waiting = False
            clock.tick(10)

    # Button to start the game
    if st.button("Start Shooter Game"):
        threading.Thread(target=shooter_game, daemon=True).start()
        st.success("Shooter game started! Focus on the Pygame window to play.")

    st.subheader("Color Relaxation")

    color_sounds = {
        "Blue": "sounds/ocean.wav",
        "Green": "sounds/forest.wav",
        "Purple": "sounds/splash.wav",
        "Pink": "sounds/relaxing.wav",
        "Yellow": "sounds/sunny.wav"
    }

    color_images = {
        "Blue": "images/blue.jpg",
        "Green": "images/green.jpg",
        "Purple": "images/purple.jpg",
        "Pink": "images/pink.png",
        "Yellow": "images/yellow.png"
    }

    messages = {
        "Blue": "Blue is like the ocean—deep, calming, and endless. Take a deep breath and let it wash over you.",
        "Green": "Green represents nature and growth. Imagine yourself in a peaceful forest, surrounded by tranquility.",
        "Purple": "Purple evokes creativity and serenity. Let your mind wander to a dreamy, stress-free place.",
        "Pink": "Pink is soft and gentle. Feel the warmth and comfort it brings, like a cozy blanket.",
        "Yellow": "Yellow is bright and uplifting. Let it energize you with positive, sunny vibes."
    }

    selected_color = st.selectbox(
    "Pick a calming color:",
    list(color_sounds.keys()),
    index=None,
    placeholder="Choose a color..."
    )

    if selected_color:
        st.write(f"**{selected_color}:** {messages[selected_color]}")
        st.image(color_images[selected_color], width=400)

        # This plays immediately when selection changes
        st.audio(color_sounds[selected_color], format="audio/wav")

# ==================== RESOURCES ====================
if st.session_state.page == "Resources":
    st.header("Helpful Resources")
    st.subheader("Hotlines")
    st.markdown("""
    - **Tele MANAS**: 14416 or 1-800-89-14416 or 1800-599-0019
    - **International Association for Suicide Prevention**: [Find local resources](https://www.iasp.info/resources/Crisis_Centres/)
    """)
    st.subheader("Websites")
    st.markdown("""
    - [Tele MANAS](https://www.pib.gov.in/PressNoteDetails.aspx?NoteId=153277&ModuleId=3&reg=3&lang=2)
    - [NAMI](https://www.nami.org/)
    - [Psychology Today](https://www.psychologytoday.com/)
    - [Headspace](https://www.headspace.com/)
    - [Calm](https://www.calm.com/)
    """)
    st.subheader("Books")
    st.markdown("""
    - "The Happiness Trap" by Russ Harris
    - "Feeling Good: The New Mood Therapy" by David D. Burns
    - "Man's Search for Meaning" by Viktor E. Frankl
    """)
    st.info("If you're in immediate danger, call emergency services (112).")
