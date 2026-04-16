
import json
import os
import hashlib
from datetime import datetime, date
from pathlib import Path
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# IA opcional
# =========================================================
try:
    from openai import OpenAI
    OPENAI_OK = True
except Exception:
    OpenAI = None
    OPENAI_OK = False


# =========================================================
# Config
# =========================================================
APP_NAME = "Painel Nutrição"
DATA_FILE = Path("painel_nutricao_mega_data.json")

ACTIVITY_FACTORS = {
    "Sedentário": 1.2,
    "Levemente ativo": 1.375,
    "Moderadamente ativo": 1.55,
    "Muito ativo": 1.725,
    "Atleta": 1.9,
}

DEFAULT_FOODS = {
    "Frango grelhado (100g)": {"kcal": 165, "protein": 31.0, "carbs": 0.0, "fat": 3.6, "fiber": 0.0},
    "Arroz cozido (100g)": {"kcal": 130, "protein": 2.7, "carbs": 28.0, "fat": 0.3, "fiber": 0.4},
    "Feijão cozido (100g)": {"kcal": 76, "protein": 4.8, "carbs": 13.6, "fat": 0.5, "fiber": 8.5},
    "Ovo inteiro (1 un)": {"kcal": 78, "protein": 6.3, "carbs": 0.6, "fat": 5.3, "fiber": 0.0},
    "Aveia em flocos (30g)": {"kcal": 114, "protein": 4.0, "carbs": 19.5, "fat": 2.4, "fiber": 3.0},
    "Banana prata (1 un)": {"kcal": 98, "protein": 1.3, "carbs": 26.0, "fat": 0.1, "fiber": 2.0},
    "Maçã (1 un)": {"kcal": 95, "protein": 0.5, "carbs": 25.0, "fat": 0.3, "fiber": 4.4},
    "Batata-doce cozida (100g)": {"kcal": 86, "protein": 1.6, "carbs": 20.1, "fat": 0.1, "fiber": 3.0},
    "Salmão (100g)": {"kcal": 208, "protein": 20.0, "carbs": 0.0, "fat": 13.0, "fiber": 0.0},
    "Iogurte natural (170g)": {"kcal": 108, "protein": 9.0, "carbs": 12.0, "fat": 3.0, "fiber": 0.0},
    "Leite desnatado (200ml)": {"kcal": 70, "protein": 6.6, "carbs": 10.0, "fat": 0.2, "fiber": 0.0},
    "Pão integral (2 fatias)": {"kcal": 138, "protein": 6.0, "carbs": 24.0, "fat": 2.0, "fiber": 4.0},
    "Brócolis cozido (100g)": {"kcal": 35, "protein": 2.4, "carbs": 7.2, "fat": 0.4, "fiber": 3.3},
    "Queijo minas (50g)": {"kcal": 132, "protein": 8.5, "carbs": 1.6, "fat": 10.2, "fiber": 0.0},
    "Castanha-do-pará (15g)": {"kcal": 99, "protein": 2.1, "carbs": 1.8, "fat": 10.1, "fiber": 1.1},
}

STUDY_BLOCKS = {
    "Base": ["Anatomia", "Fisiologia", "Bioquímica", "Metabolismo", "Microbiologia"],
    "Alimentos": ["Bromatologia", "Técnica dietética", "Tecnologia de alimentos", "Segurança alimentar"],
    "Clínica": ["Avaliação nutricional", "Dietoterapia", "Nutrição clínica", "Nutrição esportiva", "Materno-infantil"],
    "Coletiva": ["Políticas públicas", "Epidemiologia", "UAN", "Educação alimentar"],
    "Profissão": ["Anamnese", "Prontuário", "Plano alimentar", "Conduta", "Ética", "Comunicação"],
}


# =========================================================
# Helpers
# =========================================================
def now_ts():
    return int(datetime.now().timestamp())


def slugify(value: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in value.strip().lower()).strip("_") or "arquivo"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def parse_dt(value):
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return value
    return value


def serialize_dt(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def calc_bmi(weight, height_m):
    if weight <= 0 or height_m <= 0:
        return None
    return weight / (height_m ** 2)


def bmi_label(bmi):
    if bmi is None:
        return ""
    if bmi < 18.5:
        return "Abaixo do peso"
    if bmi < 25:
        return "Eutrofia"
    if bmi < 30:
        return "Sobrepeso"
    if bmi < 35:
        return "Obesidade I"
    if bmi < 40:
        return "Obesidade II"
    return "Obesidade III"


def calc_bmr(weight, height_cm, age, sex):
    if sex == "Masculino":
        return 10 * weight + 6.25 * height_cm - 5 * age + 5
    return 10 * weight + 6.25 * height_cm - 5 * age - 161


def calc_tdee(weight, height_cm, age, sex, activity):
    bmr = calc_bmr(weight, height_cm, age, sex)
    return bmr, bmr * ACTIVITY_FACTORS[activity]


def calc_macros(kcal, protein_pct, carbs_pct, fat_pct):
    p = (kcal * protein_pct / 100) / 4
    c = (kcal * carbs_pct / 100) / 4
    f = (kcal * fat_pct / 100) / 9
    return p, c, f


def export_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def render_patient_report_html(patient: dict, plan: dict | None = None) -> bytes:
    plan_html = ""
    if plan:
        rows = []
        for item in plan["items"]:
            rows.append(
                f"<tr><td>{escape(item['food'])}</td><td>{item['servings']}</td><td>{item['kcal']:.0f}</td>"
                f"<td>{item['protein']:.1f}</td><td>{item['carbs']:.1f}</td><td>{item['fat']:.1f}</td></tr>"
            )
        plan_html = f"""
        <h2>Plano alimentar</h2>
        <div class="box"><b>{escape(plan['name'])}</b> — {escape(plan['objective'])}</div>
        <table>
            <thead>
                <tr><th>Alimento</th><th>Porções</th><th>Kcal</th><th>P</th><th>C</th><th>G</th></tr>
            </thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
        """

    html = f"""
    <html>
    <head>
        <meta charset="utf-8" />
        <title>Ficha do paciente</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #0f172a;
                color: #f8fafc;
                padding: 24px;
            }}
            h1, h2 {{
                margin-bottom: 8px;
            }}
            .muted {{
                color: #cbd5e1;
                margin-bottom: 24px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 12px;
                margin-bottom: 20px;
            }}
            .card {{
                background: #172033;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 12px;
            }}
            .box {{
                background: #172033;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 14px;
                margin-bottom: 16px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            th, td {{
                border: 1px solid #334155;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background: #1e293b;
            }}
        </style>
    </head>
    <body>
        <h1>{escape(patient['name'])}</h1>
        <div class="muted">Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>

        <div class="grid">
            <div class="card"><b>Idade:</b> {patient['age']}</div>
            <div class="card"><b>Sexo:</b> {escape(patient['sex'])}</div>
            <div class="card"><b>Peso:</b> {patient['weight']} kg</div>
            <div class="card"><b>Altura:</b> {patient['height']} cm</div>
            <div class="card"><b>IMC:</b> {patient['bmi']}</div>
            <div class="card"><b>Classificação:</b> {escape(patient['bmi_class'])}</div>
            <div class="card"><b>TMB:</b> {patient['bmr']} kcal</div>
            <div class="card"><b>TDEE:</b> {patient['tdee']} kcal</div>
        </div>

        <h2>Objetivo</h2>
        <div class="box">{escape(patient['goal'])}</div>

        <h2>Queixa principal</h2>
        <div class="box">{escape(patient['complaint'] or '-')}</div>

        <h2>Observações</h2>
        <div class="box">{escape(patient['notes'] or '-')}</div>

        {plan_html}
    </body>
    </html>
    """
    return html.encode("utf-8")


def empty_user(full_name: str):
    return {
        "password_hash": "",
        "profile": {
            "full_name": full_name,
            "created_at": datetime.now().isoformat(),
        },
        "patients": [],
        "plans": [],
        "diary": [],
        "history": [],
        "tasks": [],
        "notes": [],
        "study_progress": {},
    }


def default_data():
    return {
        "users": {},
        "shared_foods": DEFAULT_FOODS.copy(),
    }


def load_data():
    if not DATA_FILE.exists():
        return default_data()

    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        raw.setdefault("users", {})
        raw.setdefault("shared_foods", DEFAULT_FOODS.copy())

        foods = DEFAULT_FOODS.copy()
        foods.update(raw["shared_foods"])
        raw["shared_foods"] = foods

        for _, user in raw["users"].items():
            user.setdefault("password_hash", "")
            user.setdefault("profile", {"full_name": "Usuário", "created_at": datetime.now().isoformat()})
            for key in ["patients", "plans", "diary", "history", "tasks", "notes"]:
                user.setdefault(key, [])
                converted = []
                for item in user[key]:
                    item = dict(item)
                    for dt_key in ["data", "created_at", "updated_at"]:
                        if dt_key in item:
                            item[dt_key] = parse_dt(item[dt_key])
                    converted.append(item)
                user[key] = converted
            user.setdefault("study_progress", {})
        return raw
    except Exception:
        return default_data()


def save_data():
    payload = {
        "users": {},
        "shared_foods": st.session_state.app_data["shared_foods"],
    }

    for username, user in st.session_state.app_data["users"].items():
        saved = {
            "password_hash": user["password_hash"],
            "profile": user["profile"],
            "patients": [],
            "plans": [],
            "diary": [],
            "history": [],
            "tasks": [],
            "notes": [],
            "study_progress": user.get("study_progress", {}),
        }

        for key in ["patients", "plans", "diary", "history", "tasks", "notes"]:
            for item in user.get(key, []):
                saved[key].append({k: serialize_dt(v) for k, v in item.items()})

        payload["users"][username] = saved

    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def current_user():
    username = st.session_state.get("auth_user")
    if not username:
        return None
    return st.session_state.app_data["users"][username]


def add_history(kind: str, text: str):
    user = current_user()
    user["history"].append({
        "tipo": kind,
        "descricao": text,
        "data": datetime.now(),
    })
    save_data()


def register_user(username: str, password: str, full_name: str):
    users = st.session_state.app_data["users"]
    if username in users:
        return False, "Esse usuário já existe."
    users[username] = empty_user(full_name)
    users[username]["password_hash"] = hash_password(password)
    save_data()
    return True, "Conta criada."


def login_user(username: str, password: str):
    users = st.session_state.app_data["users"]
    if username not in users:
        return False
    if users[username]["password_hash"] != hash_password(password):
        return False
    st.session_state.auth_user = username
    return True


def logout_user():
    st.session_state.auth_user = None


def run_ai(prompt: str, patient: dict | None = None):
    if not OPENAI_OK:
        raise RuntimeError("Biblioteca openai não instalada.")

    api_key = None
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        pass
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Defina OPENAI_API_KEY nos secrets ou no ambiente.")

    client = OpenAI(api_key=api_key)

    context_parts = [
        "Você ajuda em um sistema de nutrição.",
        "Responda em português do Brasil.",
        "Use tom direto, simples, humano e natural.",
        "Não escreva como propaganda.",
        "Evite frases robóticas.",
    ]
    if patient:
        context_parts.append(
            f"Paciente: {patient['name']}, {patient['age']} anos, {patient['sex']}, "
            f"{patient['weight']} kg, {patient['height']} cm, IMC {patient['bmi']}, "
            f"{patient['goal']}, atividade {patient['activity']}, TDEE {patient['tdee']} kcal, "
            f"queixa: {patient['complaint']}, observações: {patient['notes']}."
        )

    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions="\n".join(context_parts),
        input=prompt,
    )
    return response.output_text


# =========================================================
# UI
# =========================================================
def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --bg: #0a0f1a;
            --bg2: #0f172a;
            --card: #121a2b;
            --card2: #182236;
            --line: #2a3a57;
            --text: #f8fafc;
            --muted: #cbd5e1;
            --primary: #3b82f6;
            --primary2: #2563eb;
            --ok: #16a34a;
            --shadow: 0 16px 36px rgba(0,0,0,0.28);
        }

        html, body, .stApp, p, span, div, label, li {
            color: var(--text) !important;
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(59,130,246,0.10), transparent 24%),
                linear-gradient(180deg, var(--bg2) 0%, var(--bg) 100%);
        }

        .main .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #020617 0%, #0f172a 100%);
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        [data-testid="stSidebar"] * {
            color: #f8fafc !important;
        }

        h1, h2, h3 {
            color: #ffffff !important;
            letter-spacing: -0.02em;
        }

        h1 {
            font-size: 2.5rem !important;
            font-weight: 800 !important;
        }

        h2 {
            font-size: 1.6rem !important;
            font-weight: 800 !important;
        }

        .hero {
            background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 100%);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 26px;
            padding: 1.55rem 1.55rem 1.25rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }

        .hero h1, .hero p {
            margin: 0;
            color: #fff !important;
        }

        .hero p {
            margin-top: 0.35rem;
            color: #dbeafe !important;
        }

        .section-card {
            background: var(--card) !important;
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 1.05rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }

        .stMetric {
            background: var(--card2) !important;
            border: 1px solid #334155 !important;
            border-radius: 18px !important;
            padding: 0.8rem !important;
        }

        .stMetric label {
            color: #cbd5e1 !important;
            font-weight: 600 !important;
        }

        .stMetric div {
            color: #ffffff !important;
            font-weight: 700 !important;
        }

        .stButton > button, .stDownloadButton > button {
            color: #fff !important;
            border: none !important;
            border-radius: 14px !important;
            font-weight: 700 !important;
        }

        .stButton > button {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary2) 100%) !important;
        }

        .stDownloadButton > button {
            background: linear-gradient(135deg, #0f766e 0%, #14b8a6 100%) !important;
        }

        .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea {
            background: #0f172a !important;
            color: #f8fafc !important;
            border: 1px solid #475569 !important;
            border-radius: 14px !important;
            -webkit-text-fill-color: #f8fafc !important;
        }

        .stTextInput label, .stNumberInput label, .stDateInput label, .stTextArea label,
        .stSelectbox label, .stMultiSelect label {
            color: #e2e8f0 !important;
            font-weight: 600 !important;
        }

        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div {
            background: #0f172a !important;
            color: #f8fafc !important;
            border: 1px solid #475569 !important;
            border-radius: 14px !important;
        }

        .stSelectbox div[data-baseweb="select"] span,
        .stMultiSelect div[data-baseweb="select"] span,
        .stSelectbox div[data-baseweb="select"] input,
        .stMultiSelect div[data-baseweb="select"] input,
        .stSelectbox div[data-baseweb="select"] div,
        .stMultiSelect div[data-baseweb="select"] div {
            color: #f8fafc !important;
            -webkit-text-fill-color: #f8fafc !important;
        }

        .stSelectbox svg, .stMultiSelect svg {
            fill: #f8fafc !important;
        }

        div[data-baseweb="popover"], div[data-baseweb="popover"] * {
            background: #0f172a !important;
            color: #f8fafc !important;
            -webkit-text-fill-color: #f8fafc !important;
        }

        ul[role="listbox"], div[role="listbox"] {
            background: #0f172a !important;
            border: 1px solid #475569 !important;
            border-radius: 14px !important;
            box-shadow: 0 18px 40px rgba(0,0,0,0.45) !important;
        }

        li[role="option"], div[role="option"], [role="option"] {
            background: #0f172a !important;
            color: #f8fafc !important;
        }

        li[role="option"]:hover, div[role="option"]:hover, [role="option"]:hover {
            background: #1e293b !important;
        }

        li[aria-selected="true"], div[aria-selected="true"] {
            background: #2563eb !important;
            color: #fff !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            background: #111827;
            border: 1px solid var(--line);
            padding: 0.35rem;
            border-radius: 16px;
            gap: 0.35rem;
        }

        .stTabs [data-baseweb="tab"] {
            color: #e2e8f0 !important;
            border-radius: 12px;
            font-weight: 700;
            height: auto;
            padding: 0.7rem 0.95rem;
        }

        .stTabs [aria-selected="true"] {
            background: #2563eb !important;
            color: #ffffff !important;
            border: 1px solid #3b82f6 !important;
        }

        div[data-testid="stDataFrame"], div[data-testid="stTable"] {
            border: 1px solid var(--line);
            border-radius: 16px;
            overflow: hidden;
            background: var(--card) !important;
        }

        [data-testid="stInfo"] {
            background: #082f49 !important;
            color: #bae6fd !important;
            border-radius: 16px;
        }

        [data-testid="stSuccess"] {
            background: #052e16 !important;
            color: #bbf7d0 !important;
            border-radius: 16px;
        }

        [data-testid="stWarning"] {
            background: #451a03 !important;
            color: #fed7aa !important;
            border-radius: 16px;
        }

        [data-testid="stError"] {
            background: #450a0a !important;
            color: #fecaca !important;
            border-radius: 16px;
        }

        .soft {
            color: var(--muted) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title, subtitle):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def card_start():
    st.markdown('<div class="section-card">', unsafe_allow_html=True)


def card_end():
    st.markdown('</div>', unsafe_allow_html=True)


def auth_screen():
    hero(APP_NAME, "Sistema completo para rotina nutricional")
    c1, c2 = st.columns(2)

    with c1:
        card_start()
        st.subheader("Entrar")
        username = st.text_input("Usuário", key="login_user")
        password = st.text_input("Senha", key="login_pass", type="password")
        if st.button("Entrar", use_container_width=True):
            if login_user(username.strip(), password):
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
        card_end()

    with c2:
        card_start()
        st.subheader("Criar conta")
        full_name = st.text_input("Nome", key="reg_name")
        username = st.text_input("Usuário", key="reg_user")
        password = st.text_input("Senha", key="reg_pass", type="password")
        if st.button("Criar conta", use_container_width=True):
            if not full_name.strip() or not username.strip() or not password.strip():
                st.error("Preencha tudo.")
            else:
                ok, msg = register_user(username.strip(), password, full_name.strip())
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
        card_end()


# =========================================================
# App init
# =========================================================
st.set_page_config(page_title=APP_NAME, page_icon="🥗", layout="wide", initial_sidebar_state="expanded")
inject_css()

if "app_data" not in st.session_state:
    st.session_state.app_data = load_data()
if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if not st.session_state.auth_user:
    auth_screen()
    st.stop()

user = current_user()
foods = st.session_state.app_data["shared_foods"]

today_entries = [x for x in user["diary"] if x["data"].date() == date.today()]
today_kcal = sum(x["kcal"] for x in today_entries)
today_protein = sum(x["protein"] for x in today_entries)
today_carbs = sum(x["carbs"] for x in today_entries)
today_fat = sum(x["fat"] for x in today_entries)

with st.sidebar:
    st.markdown(f"## {APP_NAME}")
    st.markdown(f"**{user['profile']['full_name']}**")
    st.markdown('<p class="soft">Área interna</p>', unsafe_allow_html=True)

    page = st.selectbox(
        "Menu",
        ["Resumo", "Pacientes", "Planos", "Diário", "Cálculos", "IA", "Tarefas", "Análises", "Estudos", "Configurações"]
    )

    st.markdown("---")
    st.markdown(f"**Kcal hoje:** {today_kcal:.0f}")
    st.markdown(f"**Pacientes:** {len(user['patients'])}")
    st.markdown(f"**Planos:** {len(user['plans'])}")
    st.markdown(f"**Tarefas:** {len(user['tasks'])}")

    if st.button("Sair", use_container_width=True):
        logout_user()
        st.rerun()


# =========================================================
# Pages
# =========================================================
if page == "Resumo":
    hero("Resumo", "Visão rápida do dia")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kcal", f"{today_kcal:.0f}")
    c2.metric("Proteína", f"{today_protein:.1f} g")
    c3.metric("Carboidratos", f"{today_carbs:.1f} g")
    c4.metric("Gorduras", f"{today_fat:.1f} g")

    left, right = st.columns([1.1, 0.9])

    with left:
        card_start()
        st.subheader("Hoje")
        if today_entries:
            df = pd.DataFrame(
                [{
                    "Refeição": x["meal"],
                    "Alimento": x["food"],
                    "Porções": x["servings"],
                    "Kcal": round(x["kcal"], 1),
                    "Proteína": round(x["protein"], 1),
                } for x in today_entries]
            )
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro hoje.")
        card_end()

        card_start()
        st.subheader("Últimos movimentos")
        if user["history"]:
            hist = pd.DataFrame(
                [{
                    "Data": x["data"].strftime("%d/%m/%Y %H:%M"),
                    "Tipo": x["tipo"],
                    "Descrição": x["descricao"],
                } for x in sorted(user["history"], key=lambda x: x["data"], reverse=True)[:10]]
            )
            st.dataframe(hist, use_container_width=True, hide_index=True)
        else:
            st.info("Nada por enquanto.")
        card_end()

    with right:
        card_start()
        st.subheader("Pendências")
        pending = [x for x in user["tasks"] if not x.get("done")]
        if pending:
            for task in pending[:8]:
                st.markdown(f"- {task['title']}")
        else:
            st.info("Sem pendências.")
        card_end()


elif page == "Pacientes":
    hero("Pacientes", "Cadastro, ficha e exportação")
    tab1, tab2 = st.tabs(["Novo", "Lista"])

    with tab1:
        card_start()
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Nome")
        age = c2.number_input("Idade", min_value=0, step=1)
        sex = c3.selectbox("Sexo", ["Masculino", "Feminino"])
        c4, c5, c6 = st.columns(3)
        weight = c4.number_input("Peso (kg)", min_value=0.0, step=0.1)
        height = c5.number_input("Altura (cm)", min_value=0.0, step=1.0)
        activity = c6.selectbox("Atividade", list(ACTIVITY_FACTORS.keys()))
        goal = st.selectbox("Objetivo", ["Emagrecimento", "Hipertrofia", "Performance", "Saúde geral", "Melhora clínica"])
        complaint = st.text_area("Queixa principal")
        notes = st.text_area("Observações")

        if st.button("Salvar paciente"):
            if name.strip() and age > 0 and weight > 0 and height > 0:
                bmi = calc_bmi(weight, height / 100)
                bmr, tdee = calc_tdee(weight, height, age, sex, activity)
                patient = {
                    "id": f"PT-{now_ts()}",
                    "name": name.strip(),
                    "age": int(age),
                    "sex": sex,
                    "weight": weight,
                    "height": height,
                    "activity": activity,
                    "goal": goal,
                    "complaint": complaint,
                    "notes": notes,
                    "bmi": round(bmi, 2),
                    "bmi_class": bmi_label(bmi),
                    "bmr": round(bmr, 1),
                    "tdee": round(tdee, 1),
                    "data": datetime.now(),
                }
                user["patients"].append(patient)
                save_data()
                add_history("Paciente", f"{patient['name']} cadastrado")
                st.success("Paciente salvo.")
            else:
                st.error("Preencha nome, idade, peso e altura.")
        card_end()

    with tab2:
        card_start()
        patients = sorted(user["patients"], key=lambda x: x["data"], reverse=True)

        if patients:
            df = pd.DataFrame(
                [{
                    "ID": p["id"],
                    "Nome": p["name"],
                    "Objetivo": p["goal"],
                    "IMC": p["bmi"],
                    "TDEE": p["tdee"],
                    "Data": p["data"].strftime("%d/%m/%Y"),
                } for p in patients]
            )
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("Exportar CSV", data=export_csv_bytes(df), file_name="pacientes.csv", mime="text/csv")

            plans_by_patient = {}
            for p in patients:
                plans_by_patient[p["id"]] = [pl for pl in user["plans"] if pl.get("patient_id") == p["id"]]

            for p in patients:
                with st.expander(p["name"]):
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("IMC", f"{p['bmi']:.2f}")
                    m2.metric("Classificação", p["bmi_class"])
                    m3.metric("TMB", f"{p['bmr']:.0f}")
                    m4.metric("TDEE", f"{p['tdee']:.0f}")

                    st.write(f"**Queixa:** {p['complaint'] or '-'}")
                    st.write(f"**Observações:** {p['notes'] or '-'}")

                    linked_plans = plans_by_patient[p["id"]]
                    selected_plan = None
                    if linked_plans:
                        selected_name = st.selectbox(
                            "Plano para incluir na ficha",
                            ["Nenhum"] + [pl["name"] for pl in linked_plans],
                            key=f"plan_select_{p['id']}"
                        )
                        if selected_name != "Nenhum":
                            selected_plan = next(pl for pl in linked_plans if pl["name"] == selected_name)

                    report_html = render_patient_report_html(p, selected_plan)
                    st.download_button(
                        "Baixar ficha HTML",
                        data=report_html,
                        file_name=f"ficha_{slugify(p['name'])}.html",
                        mime="text/html",
                        key=f"dl_{p['id']}",
                    )
        else:
            st.info("Nenhum paciente salvo.")
        card_end()


elif page == "Planos":
    hero("Planos", "Montagem simples")
    tab1, tab2 = st.tabs(["Novo", "Salvos"])

    with tab1:
        card_start()
        plan_name = st.text_input("Nome do plano")
        objective = st.selectbox("Objetivo", ["Manutenção", "Emagrecimento", "Hipertrofia", "Reeducação alimentar", "Performance"])
        patient_options = ["Sem vínculo"] + [f"{p['name']} ({p['id']})" for p in user["patients"]]
        patient_selected = st.selectbox("Paciente", patient_options)
        selected_foods = st.multiselect("Alimentos", list(foods.keys()))

        portions = {}
        for food in selected_foods:
            portions[food] = st.number_input(f"Porções de {food}", min_value=0.1, step=0.1, value=1.0, key=f"portion_{food}")

        if st.button("Salvar plano"):
            if not plan_name.strip():
                st.error("Dê um nome.")
            elif not selected_foods:
                st.error("Selecione os alimentos.")
            else:
                items = []
                total_kcal = total_p = total_c = total_f = 0.0
                for food in selected_foods:
                    base = foods[food]
                    q = portions[food]
                    row = {
                        "food": food,
                        "servings": q,
                        "kcal": base["kcal"] * q,
                        "protein": base["protein"] * q,
                        "carbs": base["carbs"] * q,
                        "fat": base["fat"] * q,
                    }
                    items.append(row)
                    total_kcal += row["kcal"]
                    total_p += row["protein"]
                    total_c += row["carbs"]
                    total_f += row["fat"]

                patient_id = None
                if patient_selected != "Sem vínculo":
                    patient_id = patient_selected.split("(")[-1].replace(")", "")

                plan = {
                    "id": f"PL-{now_ts()}",
                    "patient_id": patient_id,
                    "name": plan_name.strip(),
                    "objective": objective,
                    "items": items,
                    "total_kcal": round(total_kcal, 1),
                    "total_protein": round(total_p, 1),
                    "total_carbs": round(total_c, 1),
                    "total_fat": round(total_f, 1),
                    "data": datetime.now(),
                }
                user["plans"].append(plan)
                save_data()
                add_history("Plano", f"{plan['name']} salvo")
                st.success("Plano salvo.")
        card_end()

    with tab2:
        card_start()
        plans = sorted(user["plans"], key=lambda x: x["data"], reverse=True)
        if plans:
            for plan in plans:
                with st.expander(plan["name"]):
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Kcal", f"{plan['total_kcal']:.0f}")
                    m2.metric("Proteína", f"{plan['total_protein']:.1f} g")
                    m3.metric("Carboidratos", f"{plan['total_carbs']:.1f} g")
                    m4.metric("Gorduras", f"{plan['total_fat']:.1f} g")

                    df = pd.DataFrame(
                        [{
                            "Alimento": i["food"],
                            "Porções": i["servings"],
                            "Kcal": i["kcal"],
                            "Proteína": i["protein"],
                            "Carboidratos": i["carbs"],
                            "Gorduras": i["fat"],
                        } for i in plan["items"]]
                    )
                    st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum plano salvo.")
        card_end()


elif page == "Diário":
    hero("Diário", "Registros do dia")
    left, right = st.columns([1.0, 1.0])

    with left:
        card_start()
        meal = st.selectbox("Refeição", ["Café da manhã", "Lanche manhã", "Almoço", "Lanche tarde", "Jantar", "Ceia"])
        food = st.selectbox("Alimento", list(foods.keys()))
        servings = st.number_input("Porções", min_value=0.1, step=0.1, value=1.0)
        entry_date = st.date_input("Data", value=date.today())

        if st.button("Adicionar ao diário"):
            base = foods[food]
            entry = {
                "id": f"DG-{now_ts()}",
                "meal": meal,
                "food": food,
                "servings": servings,
                "kcal": base["kcal"] * servings,
                "protein": base["protein"] * servings,
                "carbs": base["carbs"] * servings,
                "fat": base["fat"] * servings,
                "fiber": base["fiber"] * servings,
                "data": datetime.combine(entry_date, datetime.min.time()),
            }
            user["diary"].append(entry)
            save_data()
            add_history("Diário", f"{food} adicionado")
            st.success("Registro salvo.")
        card_end()

        card_start()
        st.subheader("Banco de alimentos")
        search = st.text_input("Buscar")
        filtered = {k: v for k, v in foods.items() if search.lower() in k.lower()} if search else foods

        df_foods = pd.DataFrame(
            [{
                "Alimento": k,
                "Kcal": v["kcal"],
                "Proteína": v["protein"],
                "Carboidratos": v["carbs"],
                "Gorduras": v["fat"],
                "Fibra": v["fiber"],
            } for k, v in filtered.items()]
        )
        st.dataframe(df_foods, use_container_width=True, hide_index=True)

        with st.expander("Adicionar alimento"):
            fname = st.text_input("Nome do alimento")
            c1, c2, c3 = st.columns(3)
            kcal = c1.number_input("Kcal", min_value=0.0, step=1.0)
            protein = c2.number_input("Proteína", min_value=0.0, step=0.1)
            carbs = c3.number_input("Carboidratos", min_value=0.0, step=0.1)
            c4, c5 = st.columns(2)
            fat = c4.number_input("Gorduras", min_value=0.0, step=0.1)
            fiber = c5.number_input("Fibra", min_value=0.0, step=0.1)

            if st.button("Salvar alimento"):
                if fname.strip():
                    st.session_state.app_data["shared_foods"][fname.strip()] = {
                        "kcal": kcal,
                        "protein": protein,
                        "carbs": carbs,
                        "fat": fat,
                        "fiber": fiber,
                    }
                    save_data()
                    st.success("Alimento salvo.")
                else:
                    st.error("Digite o nome.")
        card_end()

    with right:
        card_start()
        view_date = st.date_input("Ver data", value=date.today(), key="view_date")
        rows = [x for x in user["diary"] if x["data"].date() == view_date]

        if rows:
            df = pd.DataFrame(
                [{
                    "Refeição": x["meal"],
                    "Alimento": x["food"],
                    "Porções": x["servings"],
                    "Kcal": round(x["kcal"], 1),
                    "Proteína": round(x["protein"], 1),
                    "Carboidratos": round(x["carbs"], 1),
                    "Gorduras": round(x["fat"], 1),
                } for x in rows]
            )
            st.dataframe(df, use_container_width=True, hide_index=True)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Kcal", f"{df['Kcal'].sum():.0f}")
            m2.metric("Proteína", f"{df['Proteína'].sum():.1f} g")
            m3.metric("Carboidratos", f"{df['Carboidratos'].sum():.1f} g")
            m4.metric("Gorduras", f"{df['Gorduras'].sum():.1f} g")
        else:
            st.info("Sem registros nessa data.")
        card_end()


elif page == "Cálculos":
    hero("Cálculos", "Ferramentas básicas")
    tab1, tab2, tab3, tab4 = st.tabs(["IMC", "TMB/TDEE", "Meta", "Macros"])

    with tab1:
        card_start()
        c1, c2 = st.columns(2)
        weight = c1.number_input("Peso (kg)", min_value=0.0, step=0.1)
        height = c2.number_input("Altura (m)", min_value=0.0, step=0.01)
        if st.button("Calcular IMC"):
            bmi = calc_bmi(weight, height)
            if bmi:
                st.success(f"IMC: {bmi:.2f} — {bmi_label(bmi)}")
            else:
                st.error("Preencha valores válidos.")
        card_end()

    with tab2:
        card_start()
        c1, c2, c3 = st.columns(3)
        w = c1.number_input("Peso (kg)", min_value=0.0, step=0.1, key="t_w")
        h = c2.number_input("Altura (cm)", min_value=0.0, step=1.0, key="t_h")
        age = c3.number_input("Idade", min_value=0, step=1, key="t_age")
        c4, c5 = st.columns(2)
        sex = c4.selectbox("Sexo", ["Masculino", "Feminino"], key="t_sex")
        activity = c5.selectbox("Atividade", list(ACTIVITY_FACTORS.keys()), key="t_act")
        if st.button("Calcular TMB/TDEE"):
            if w > 0 and h > 0 and age > 0:
                bmr, tdee = calc_tdee(w, h, age, sex, activity)
                m1, m2, m3 = st.columns(3)
                m1.metric("TMB", f"{bmr:.0f}")
                m2.metric("TDEE", f"{tdee:.0f}")
                m3.metric("Déficit leve", f"{tdee*0.9:.0f}")
            else:
                st.error("Preencha tudo.")
        card_end()

    with tab3:
        card_start()
        c1, c2, c3 = st.columns(3)
        w = c1.number_input("Peso (kg)", min_value=0.0, step=0.1, key="g_w")
        h = c2.number_input("Altura (cm)", min_value=0.0, step=1.0, key="g_h")
        age = c3.number_input("Idade", min_value=0, step=1, key="g_age")
        c4, c5, c6 = st.columns(3)
        sex = c4.selectbox("Sexo", ["Masculino", "Feminino"], key="g_sex")
        activity = c5.selectbox("Atividade", list(ACTIVITY_FACTORS.keys()), key="g_act")
        goal = c6.selectbox("Objetivo", ["Manutenção", "Déficit leve", "Déficit moderado", "Ganho leve"])
        if st.button("Calcular meta"):
            if w > 0 and h > 0 and age > 0:
                _, tdee = calc_tdee(w, h, age, sex, activity)
                factor = {"Manutenção": 1.0, "Déficit leve": 0.9, "Déficit moderado": 0.85, "Ganho leve": 1.1}[goal]
                target = tdee * factor
                st.success(f"Meta: {target:.0f} kcal/dia")
            else:
                st.error("Preencha tudo.")
        card_end()

    with tab4:
        card_start()
        kcal = st.number_input("Calorias diárias", min_value=0, step=50)
        c1, c2, c3 = st.columns(3)
        pp = c1.slider("Proteína (%)", 10, 45, 30)
        cp = c2.slider("Carboidratos (%)", 20, 70, 40)
        fp = c3.slider("Gorduras (%)", 15, 45, 30)
        if st.button("Calcular macros"):
            if kcal > 0 and pp + cp + fp == 100:
                p, c, f = calc_macros(kcal, pp, cp, fp)
                m1, m2, m3 = st.columns(3)
                m1.metric("Proteína", f"{p:.1f} g")
                m2.metric("Carboidratos", f"{c:.1f} g")
                m3.metric("Gorduras", f"{f:.1f} g")
            else:
                st.error("A soma precisa dar 100.")
        card_end()


elif page == "IA":
    hero("IA", "Rascunho rápido")
    card_start()
    st.subheader("Gerar texto")

    patient_options = ["Sem paciente"] + [f"{p['name']} ({p['id']})" for p in user["patients"]]
    chosen = st.selectbox("Paciente", patient_options)
    selected_patient = None
    if chosen != "Sem paciente":
        pid = chosen.split("(")[-1].replace(")", "")
        selected_patient = next((p for p in user["patients"] if p["id"] == pid), None)

    prompt_type = st.selectbox(
        "Tipo",
        ["Plano alimentar inicial", "Orientações para consulta", "Mensagem simples para paciente", "Resumo do caso"]
    )
    extra = st.text_area("Pedido", placeholder="Ex.: montar um rascunho com café da manhã, almoço, jantar e lanches simples.")

    default_prompt = {
        "Plano alimentar inicial": "Monte um rascunho inicial de plano alimentar com refeições simples.",
        "Orientações para consulta": "Escreva orientações curtas para a próxima consulta.",
        "Mensagem simples para paciente": "Escreva uma mensagem curta e natural para enviar ao paciente.",
        "Resumo do caso": "Resuma o caso em linguagem simples para prontuário.",
    }[prompt_type]

    final_prompt = f"{default_prompt}\n{extra}".strip()

    if st.button("Gerar com IA"):
        if not OPENAI_OK:
            st.warning("IA indisponível: biblioteca openai não instalada.")
        else:
            with st.spinner("Gerando..."):
                try:
                    output = run_ai(final_prompt, selected_patient)
                    st.session_state["ai_output"] = output
                    add_history("IA", f"Geração: {prompt_type}")
                except Exception as e:
                    st.error(str(e))

    output = st.session_state.get("ai_output", "")
    if output:
        st.text_area("Resultado", value=output, height=320)
        st.download_button("Baixar texto", data=output.encode("utf-8"), file_name="rascunho_ia.txt", mime="text/plain")

    st.caption("Se quiser usar IA, configure OPENAI_API_KEY.")
    card_end()


elif page == "Tarefas":
    hero("Tarefas", "Lista simples")
    left, right = st.columns(2)

    with left:
        card_start()
        title = st.text_input("Título")
        area = st.selectbox("Área", ["Paciente", "Estudo", "Administração", "Financeiro", "Outro"])
        due = st.date_input("Prazo", value=date.today())

        if st.button("Salvar tarefa"):
            if title.strip():
                user["tasks"].append({
                    "title": title.strip(),
                    "area": area,
                    "due": due.isoformat(),
                    "done": False,
                    "data": datetime.now(),
                })
                save_data()
                add_history("Tarefa", f"{title.strip()} criada")
                st.success("Tarefa salva.")
            else:
                st.error("Digite o título.")
        card_end()

    with right:
        card_start()
        if user["tasks"]:
            tasks_sorted = sorted(user["tasks"], key=lambda x: (x.get("done", False), x["due"]))
            for i, task in enumerate(tasks_sorted):
                cols = st.columns([0.75, 0.25])
                done = cols[0].checkbox(
                    f"{task['title']} — {task['area']} — {task['due']}",
                    value=task.get("done", False),
                    key=f"task_{i}",
                )
                user["tasks"][user["tasks"].index(task)]["done"] = done
                if cols[1].button("Excluir", key=f"del_{i}"):
                    user["tasks"].remove(task)
                    save_data()
                    st.rerun()
            save_data()
        else:
            st.info("Nenhuma tarefa.")
        card_end()


elif page == "Análises":
    hero("Análises", "Leitura rápida")

    card_start()
    if user["history"]:
        hist = pd.DataFrame(
            [{
                "Data": x["data"].strftime("%d/%m/%Y %H:%M"),
                "Tipo": x["tipo"],
                "Descrição": x["descricao"],
            } for x in sorted(user["history"], key=lambda x: x["data"], reverse=True)]
        )
        st.dataframe(hist, use_container_width=True, hide_index=True)
        st.download_button("Exportar histórico", data=export_csv_bytes(hist), file_name="historico.csv", mime="text/csv")
    else:
        st.info("Sem histórico.")
    card_end()

    card_start()
    if user["diary"]:
        df = pd.DataFrame([{"Data": x["data"].date(), "Calorias": x["kcal"]} for x in user["diary"]])
        resumo = df.groupby("Data", as_index=False).sum()
        fig = px.line(resumo, x="Data", y="Calorias", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados no diário.")
    card_end()


elif page == "Estudos":
    hero("Estudos", "Checklist")
    card_start()
    for area, topics in STUDY_BLOCKS.items():
        st.markdown(f"**{area}**")
        for topic in topics:
            key = f"{area}::{topic}"
            checked = user["study_progress"].get(key, False)
            user["study_progress"][key] = st.checkbox(topic, value=checked, key=key)

    if st.button("Salvar progresso"):
        save_data()
        add_history("Estudos", "Checklist atualizado")
        st.success("Salvo.")
    card_end()


elif page == "Configurações":
    hero("Configurações", "Conta e observações")
    card_start()
    st.write(f"**Usuário:** {st.session_state.auth_user}")
    st.write(f"**Nome:** {user['profile']['full_name']}")
    st.write(f"**Criado em:** {user['profile']['created_at'][:10]}")
    st.caption("Essa versão continua local. Para deixar online de verdade, o próximo passo é banco e autenticação em nuvem.")
    card_end()
