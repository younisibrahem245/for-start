import os
import time
import sqlite3
import hashlib
import hmac
import threading
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Python Escape Room", page_icon="🐍", layout="wide")
DB = os.environ.get("ESCAPE_DB", str(Path(__file__).with_name("game.db")))
PIN = os.environ.get("TEACHER_PIN", "2468")  # Change using Streamlit secrets/environment before class.

LEVELS = [
    dict(title="صندوق المتغيرات", topic="Variables & Types", story="افتح صندوق الطاقة عبر حساب رمز القفل.", code='player = "Nova"\nlevel = 4\nspeed = 2.5\nactive = True\nsecret = level * 10 + int(speed)\nprint(secret)', question="ما الرقم الذي يطبعه البرنامج؟", answer="42", hint="int(2.5) تساوي 2.", explanation="4 × 10 + 2 = 42"),
    dict(title="بوابة القرارات", topic="if / elif / else", story="اكتشف الرسالة التي سيختارها نظام الحراسة.", code='energy = 75\nif energy >= 90:\n    print("GOLD")\nelif energy >= 60:\n    print("SILVER")\nelse:\n    print("BRONZE")', question="ما الكلمة المطبوعة؟", answer="SILVER", hint="افحص الشرط الأول ثم الثاني.", explanation="75 أقل من 90 وأكبر من أو تساوي 60."),
    dict(title="متاهة الحلقات", topic="for loops", story="اجمع شظايا الكريستال.", code='total = 0\nfor n in range(1, 6):\n    total += n * 2\nprint(total)', question="ما الرقم النهائي؟", answer="30", hint="range(1, 6) يعطي 1 إلى 5.", explanation="2 + 4 + 6 + 8 + 10 = 30."),
    dict(title="مختبر الدوال", topic="Functions", story="اكتشف نتيجة دالة تعزيز الطاقة.", code='def boost(power, bonus=5):\n    return power * 2 + bonus\n\nprint(boost(12, 3))', question="ما الناتج المطبوع؟", answer="27", hint="القيمة 3 تحل محل القيمة الافتراضية.", explanation="12 × 2 + 3 = 27."),
    dict(title="الزعيم النهائي", topic="Mixed Challenge", story="فك الشيفرة لإنقاذ المملكة!", code='def attack(power):\n    if power >= 20:\n        return power - 7\n    return power + 3\n\nenergy = 30\nfor _ in range(4):\n    energy = attack(energy)\nprint(energy)', question="ما الطاقة النهائية؟", answer="22", hint="تتبّع الطاقة: 30 ثم 23 ثم 16.", explanation="30 ← 23 ← 16 ← 19 ← 22."),
]

@st.cache_resource
def db_lock():
    return threading.RLock()


def connect():
    conn = sqlite3.connect(DB, timeout=30)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("""CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        token_hash TEXT NOT NULL,
        level INTEGER NOT NULL DEFAULT 0,
        points INTEGER NOT NULL DEFAULT 0,
        hints INTEGER NOT NULL DEFAULT 0,
        started REAL NOT NULL,
        finished REAL
    )""")
    conn.commit()
    return conn


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def login_team(name, token):
    with db_lock():
        with connect() as conn:
            found = conn.execute("SELECT token_hash FROM teams WHERE name=?", (name,)).fetchone()
            if found and not hmac.compare_digest(found[0], hash_token(token)):
                return False, "اسم الفريق مستخدم بكلمة سر مختلفة."
            if not found:
                conn.execute(
                    "INSERT INTO teams (name,token_hash,started) VALUES (?,?,?)",
                    (name, hash_token(token), time.time()),
                )
    return True, "تم تسجيل الفريق بنجاح!"


def get_team(name, token):
    with connect() as conn:
        return conn.execute(
            "SELECT id,name,level,points,hints,started,finished FROM teams WHERE name=? AND token_hash=?",
            (name, hash_token(token)),
        ).fetchone()


def board():
    with connect() as conn:
        return conn.execute(
            "SELECT name,level,points,hints,started,finished FROM teams ORDER BY points DESC, finished IS NULL, finished ASC, started ASC"
        ).fetchall()


st.markdown(
    "<style>.block-container{max-width:1050px}</style>",
    unsafe_allow_html=True
)

st.title("🐍 Python Escape Room")
st.caption("خمس غرف • تحديات Python • منافسة جماعية")

role = st.sidebar.radio(
    "الدخول",
    ["🎮 الطلاب", "🏆 لوحة المعلمة"]
)

if role == "🏆 لوحة المعلمة":
    pin = st.sidebar.text_input(
        "رمز المعلمة",
        type="password"
    )
    if not hmac.compare_digest(pin, PIN):
        st.info("أدخلي رمز المعلمة لعرض النتائج.")
        st.stop()
    st.header("🏆 لوحة النتائج")
    if st.button("🔄 تحديث النتائج"):
        st.rerun()
    try:
        rows = board()
    except sqlite3.Error as exc:
        st.error(f"مشكلة في قاعدة البيانات: {exc}")
        st.stop()
    st.metric("عدد الفرق", len(rows))
