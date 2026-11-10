import os
import sqlite3
import time
import hashlib
import hmac
from pathlib import Path
import streamlit as st

st.set_page_config(page_title='Python Escape Room', page_icon='🐍', layout='wide')
DB = os.environ.get('ESCAPE_DB', str(Path(__file__).with_name('game.db')))
PIN = os.environ.get('TEACHER_PIN', '2468')

LEVELS = [
 dict(title='صندوق المتغيرات', topic='Variables & Types', story='افتح صندوق الطاقة عبر اكتشاف أنواع البيانات وحساب رمز القفل.', code='''player = "Nova"\nlevel = 4\nspeed = 2.5\nactive = True\nsecret = level * 10 + int(speed)\nprint(secret)''', question='ما الرقم الذي يطبعه البرنامج؟', answer='42', hint='int(2.5) تساوي 2، ثم احسب level * 10.', explanation='4 × 10 + 2 = 42. الأنواع: str وint وfloat وbool.'),
 dict(title='بوابة القرارات', topic='if / elif / else', story='البوابة لا تفتح إلا إذا عرفت الرسالة التي سيختارها نظام الحراسة.', code='''energy = 75\nif energy >= 90:\n    print("GOLD")\nelif energy >= 60:\n    print("SILVER")\nelse:\n    print("BRONZE")''', question='ما الكلمة المطبوعة؟ (بالإنجليزية)', answer='SILVER', hint='افحص الشرط الأول، ثم انتقل للشرط الثاني.', explanation='75 أصغر من 90 وأكبر من أو تساوي 60، لذا SILVER.'),
 dict(title='متاهة الحلقات', topic='for loops', story='اجمع شظايا الكريستال لتكوين كلمة مرور المتاهة.', code='''total = 0\nfor n in range(1, 6):\n    total += n * 2\nprint(total)''', question='ما الرقم النهائي؟', answer='30', hint='range(1, 6) يعطي 1 و2 و3 و4 و5.', explanation='2 + 4 + 6 + 8 + 10 = 30.'),
 dict(title='مختبر الدوال', topic='Functions', story='اكتشف نتيجة دالة تعزيز الطاقة لاستعادة مفتاح المختبر.', code='''def boost(power, bonus=5):\n    return power * 2 + bonus\n\nprint(boost(12, 3))''', question='ما الناتج المطبوع؟', answer='27', hint='القيمة 3 تتجاوز القيمة الافتراضية للمعامل bonus.', explanation='12 × 2 + 3 = 27.'),
 dict(title='الزعيم النهائي', topic='Mixed Challenge', story='هذا القفل يجمع الدوال والشروط والحلقات. فك الشيفرة لإنقاذ المملكة!', code='''def attack(power):\n    if power >= 20:\n        return power - 7\n    return power + 3\n\nenergy = 30\nfor _ in range(4):\n    energy = attack(energy)\nprint(energy)''', question='ما الطاقة النهائية؟', answer='15', hint='تتبّع الطاقة بعد كل دورة: أولًا 23 ثم 16.', explanation='30 ← 23 ← 16 ← 19 ← 22. الناتج الصحيح 22.'),
]
# Keep the final answer in sync with the independently traced execution.
LEVELS[-1]['answer'] = '22'

@st.cache_resource
def db_lock():
    import threading
    return threading.Lock()

def connect():
    conn = sqlite3.connect(DB, timeout=20)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('''CREATE TABLE IF NOT EXISTS teams (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, token_hash TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 0, points INTEGER NOT NULL DEFAULT 0, hints INTEGER NOT NULL DEFAULT 0, started REAL NOT NULL, finished REAL)''')
    conn.commit()
    return conn

def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()

def get_team(name, token):
    with connect() as conn:
        return conn.execute('SELECT id,name,level,points,hints,started,finished FROM teams WHERE name=? AND token_hash=?', (name, token_hash(token))).fetchone()

def board():
    with connect() as conn:
        return conn.execute('SELECT name,level,points,hints,started,finished FROM teams ORDER BY points DESC, finished IS NULL, finished ASC, started ASC').fetchall()

st.markdown('''<style>.block-container{max-width:1050px;padding-top:2rem} .stCodeBlock{direction:ltr;text-align:left} h1,h2,h3,p{direction:rtl}</style>''', unsafe_allow_html=True)
st.title('🐍 Python Escape Room')
st.caption('خمس غرف • تحديات Python • منافسة جماعية')
role = st.sidebar.radio('الدخول', ['🎮 الطلاب', '🏆 لوحة المعلمة'])

if role == '🏆 لوحة المعلمة':
    pin = st.sidebar.text_input('رمز المعلمة', type='password')
    if not hmac.compare_digest(pin, PIN):
        st.info('أدخلي رمز المعلمة لعرض النتائج.')
        st.stop()
    st.header('🏆 لوحة النتائج')
    if st.button('🔄 تحديث النتائج'):
        st.rerun()
    rows = board()
    st.metric('عدد الفرق', len(rows))
    if rows:
        st.dataframe([{'الفريق':r[0], 'الغرف المفتوحة':min(r[1],5), 'النقاط':r[2], 'التلميحات':r[3], 'الحالة':'🎉 أنهى اللعبة' if r[5] else 'يلعب', 'المدة بالدقائق':round(((r[5] or time.time())-r[4])/60,1)} for r in rows], hide_index=True, use_container_width=True)
        st.download_button('⬇️ تنزيل النتائج CSV', data=('team,levels,points,hints,status\n'+'\n'.join(f'{r[0]},{r[1]},{r[2]},{r[3]},{"finished" if r[5] else "playing"}' for r in rows)).encode('utf-8-sig'), file_name='results.csv', mime='text/csv')
    else:
        st.info('لم يسجّل أي فريق بعد.')
    st.caption('التحديث يدوي: اضغطي زر تحديث النتائج لعرض آخر النتائج.')
    st.stop()

if 'identity' not in st.session_state:
    st.subheader('🚀 انضم إلى المغامرة')
    with st.form('login'):
        name = st.text_input('اسم الفريق (استخدموا نفس الاسم دائمًا)', max_chars=35)
        token = st.text_input('كلمة سر الفريق (4 أحرف على الأقل)', type='password')
        submit = st.form_submit_button('ابدأ / تابع المغامرة', use_container_width=True)
    if submit:
       st.success("الزر اشتغل بنجاح!")
       name = name.strip()
        if not name or len(token)<4:
            st.error('اكتبوا اسم الفريق وكلمة سر من 4 أحرف على الأقل.')
        else:
            with db_lock():
                with connect() as conn:
                    exists = conn.execute('SELECT token_hash FROM teams WHERE name=?',(name,)).fetchone()
                    if exists and not hmac.compare_digest(exists[0],token_hash(token)):
                        st.error('هذا الاسم مستخدم بكلمة سر مختلفة.')
                    else:
                        if not exists:
                            conn.execute('INSERT INTO teams (name,token_hash,started) VALUES (?,?,?)',(name,token_hash(token),time.time()))
                        st.session_state.identity = (name,token)
                        st.rerun()
    st.stop()

name,token = st.session_state.identity
team = get_team(name,token)
if not team:
    st.session_state.pop('identity',None)
    st.rerun()
_,_,level,points,hints,started,finished = team
col1,col2,col3=st.columns(3)
col1.metric('الفريق',name)
col2.metric('النقاط',points)
col3.metric('الغرف المفتوحة',f'{min(level,5)}/5')
st.progress(min(level,5)/5)
if st.sidebar.button('تسجيل خروج'):
    st.session_state.pop('identity',None)
    st.rerun()
if level >= len(LEVELS):
    st.success('🎉 مبروك! نجحتم بالهروب من مملكة الأكواد!')
    st.balloons()
    st.write(f'النقاط النهائية: **{points}** | المدة: **{round(((finished or time.time())-started)/60,1)} دقيقة**')
    st.stop()

item = LEVELS[level]
st.subheader(f'🔐 الغرفة {level+1}: {item["title"]}')
st.caption(item['topic'])
st.write(item['story'])
st.code(item['code'],language='python')
st.markdown('**التحدي:** '+item['question'])
st.info('شغّلوا الكود على جهازكم باستخدام محرّر Python، ثم أدخلوا الناتج. لا تشغّل اللعبة الكود نيابةً عنكم.')
if st.button('💡 تلميح (خصم 5 نقاط من مكافأة هذه الغرفة)', key=f'hint_{level}'):
    st.session_state[f'hint_seen_{level}'] = True
if st.session_state.get(f'hint_seen_{level}'):
    st.warning(item['hint'])
with st.form(f'answer_{level}'):
    response = st.text_input('رمز القفل / الإجابة')
    submitted = st.form_submit_button('🔓 فتح القفل',use_container_width=True)
if submitted:
    if response.strip().casefold() == item['answer'].casefold():
        with db_lock():
            with connect() as conn:
                current = conn.execute('SELECT level FROM teams WHERE id=?',(team[0],)).fetchone()[0]
                if current == level:
                    used_hint = bool(st.session_state.get(f'hint_seen_{level}'))
                    reward = 15 if used_hint else 20
                    conn.execute('UPDATE teams SET level=level+1, points=points+?, hints=hints+?, finished=CASE WHEN level+1=5 THEN ? ELSE finished END WHERE id=?',(reward,int(used_hint),time.time(),team[0]))
        st.success('🎉 إجابة صحيحة! انفتح القفل.')
        st.session_state.pop(f'hint_seen_{level}',None)
        st.rerun()
    else:
        st.error('القفل مغلق! جرّبوا تتبّع تنفيذ الكود مرة ثانية.')
