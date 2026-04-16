
import json
import hashlib
from datetime import datetime, date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# CONFIG
# =========================================================
APP_NAME = "NutriFlow SaaS"
DATA_FILE = Path("nutriflow_saas_data.json")


# =========================================================
# DEFAULT DATA
# =========================================================
DEFAULT_FOODS = {
    "Frango grelhado (100g)": {"kcal": 165, "protein": 31.0, "carbs": 0.0, "fat": 3.6, "fiber": 0.0},
    "Arroz cozido (100g)": {"kcal": 130, "protein": 2.7, "carbs": 28.0, "fat": 0.3, "fiber": 0.4},
    "Feijão cozido (100g)": {"kcal": 76, "protein": 4.8, "carbs": 13.6, "fat": 0.5, "fiber": 8.5},
    "Ovo inteiro (1 un)": {"kcal": 78, "protein": 6.3, "carbs": 0.6, "fat": 5.3, "fiber": 0.0},
    "Banana prata (1 un)": {"kcal": 98, "protein": 1.3, "carbs": 26.0, "fat": 0.1, "fiber": 2.0},
    "Maçã (1 un)": {"kcal": 95, "protein": 0.5, "carbs": 25.0, "fat": 0.3, "fiber": 4.4},
    "Aveia em flocos (30g)": {"kcal": 114, "protein": 4.0, "carbs": 19.5, "fat": 2.4, "fiber": 3.0},
    "Iogurte natural (170g)": {"kcal": 108, "protein": 9.0, "carbs": 12.0, "fat": 3.0, "fiber": 0.0},
    "Leite desnatado (200ml)": {"kcal": 70, "protein": 6.6, "carbs": 10.0, "fat": 0.2, "fiber": 0.0},
    "Salmão (100g)": {"kcal": 208, "protein": 20.0, "carbs": 0.0, "fat": 13.0, "fiber": 0.0},
    "Batata-doce cozida (100g)": {"kcal": 86, "protein": 1.6, "carbs": 20.1, "fat": 0.1, "fiber": 3.0},
    "Brócolis cozido (100g)": {"kcal": 35, "protein": 2.4, "carbs": 7.2, "fat": 0.4, "fiber": 3.3},
    "Pão integral (2 fatias)": {"kcal": 138, "protein": 6.0, "carbs": 24.0, "fat": 2.0, "fiber": 4.0},
    "Queijo minas (50g)": {"kcal": 132, "protein": 8.5, "carbs": 1.6, "fat": 10.2, "fiber": 0.0},
    "Castanha-do-pará (15g)": {"kcal": 99, "protein": 2.1, "carbs": 1.8, "fat": 10.1, "fiber": 1.1},
}

ACTIVITY_FACTORS = {
    "Sedentário": 1.2,
    "Levemente ativo": 1.375,
    "Moderadamente ativo": 1.55,
    "Muito ativo": 1.725,
    "Atleta": 1.9,
}

STUDY_AREAS = {
    "Base biológica": ["Anatomia", "Fisiologia", "Bioquímica", "Metabolismo", "Microbiologia"],
    "Ciências dos alimentos": ["Bromatologia", "Técnica dietética", "Tecnologia de alimentos", "Segurança alimentar"],
    "Nutrição aplicada": ["Avaliação nutricional", "Dietoterapia", "Nutrição clínica", "Nutrição esportiva", "Materno-infantil"],
    "Saúde coletiva e gestão": ["Políticas públicas", "Epidemiologia", "UAN", "Educação alimentar", "Gestão de serviço"],
    "Profissão": ["Anamnese", "Prontuário", "Plano alimentar", "Conduta", "Ética", "Comunicação"],
}


# =========================================================
# STORAGE
# =========================================================
def default_data():
    return {
        "users": {},
        "shared_foods": DEFAULT_FOODS.copy(),
    }


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def parse_dt(value):
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return value


def serialize_dt(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def empty_user_profile(full_name: str):
    return {
        "full_name": full_name,
        "created_at": datetime.now().isoformat(),
        "patients": [],
        "plans": [],
        "diary": [],
        "history": [],
        "tasks": [],
        "study_progress": {},
        "crm_notes": [],
    }


def load_data():
    if not DATA_FILE.exists():
        return default_data()
    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        raw.setdefault("users", {})
        raw.setdefault("shared_foods", DEFAULT_FOODS.copy())
        merged = DEFAULT_FOODS.copy()
        merged.update(raw.get("shared_foods", {}))
        raw["shared_foods"] = merged

        for _, user in raw["users"].items():
            for key in ["patients", "plans", "diary", "history", "tasks", "crm_notes"]:
                user.setdefault(key, [])
            user.setdefault("study_progress", {})
            user.setdefault("profile", empty_user_profile("Usuário"))

            for list_key in ["patients", "plans", "diary", "history", "tasks", "crm_notes"]:
                processed = []
                for item in user[list_key]:
                    item = dict(item)
                    if "data" in item:
                        item["data"] = parse_dt(item["data"])
                    if "created_at" in item:
                        item["created_at"] = parse_dt(item["created_at"])
                    if "updated_at" in item:
                        item["updated_at"] = parse_dt(item["updated_at"])
                    processed.append(item)
                user[list_key] = processed
        return raw
    except Exception:
        return default_data()


def save_data():
    payload = {"users": {}, "shared_foods": st.session_state.app_data["shared_foods"]}

    for username, user in st.session_state.app_data["users"].items():
        saved = {
            "password_hash": user["password_hash"],
            "profile": user["profile"],
            "patients": [],
            "plans": [],
            "diary": [],
            "history": [],
            "tasks": [],
            "study_progress": user.get("study_progress", {}),
            "crm_notes": [],
        }

        for key in ["patients", "plans", "diary", "history", "tasks", "crm_notes"]:
            for item in user.get(key, []):
                clean = {}
                for k, v in item.items():
                    clean[k] = serialize_dt(v)
                saved[key].append(clean)

        payload["users"][username] = saved

    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# =========================================================
# HELPERS
# =========================================================
def current_user():
    username = st.session_state.get("auth_user")
    if not username:
        return None
    return st.session_state.app_data["users"][username]


def add_history(tipo: str, descricao: str, extra=None):
    user = current_user()
    record = {"tipo": tipo, "descricao": descricao, "data": datetime.now()}
    if extra:
        record.update(extra)
    user["history"].append(record)
    save_data()


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
        return "Obesidade grau I"
    if bmi < 40:
        return "Obesidade grau II"
    return "Obesidade grau III"


def calc_bmr(weight, height_cm, age, sex):
    if sex == "Masculino":
        return 10 * weight + 6.25 * height_cm - 5 * age + 5
    return 10 * weight + 6.25 * height_cm - 5 * age - 161


def calc_tdee(weight, height_cm, age, sex, activity):
    bmr = calc_bmr(weight, height_cm, age, sex)
    tdee = bmr * ACTIVITY_FACTORS[activity]
    return bmr, tdee


def macro_from_percent(kcal, protein_pct, carbs_pct, fat_pct):
    p = (kcal * protein_pct / 100) / 4
    c = (kcal * carbs_pct / 100) / 4
    f = (kcal * fat_pct / 100) / 9
    return p, c, f


def patient_report_html(patient: dict) -> str:
    return f"""
    <html>
    <head>
        <meta charset="utf-8" />
        <title>Ficha do Paciente</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 24px; color: #11203a; }}
            h1 {{ margin-bottom: 6px; }}
            h2 {{ margin-top: 24px; border-bottom: 1px solid #dbe5f0; padding-bottom: 6px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
            .box {{ background: #f7fbff; border: 1px solid #dbe5f0; border-radius: 10px; padding: 10px; }}
            .muted {{ color: #5b6b84; }}
        </style>
    </head>
    <body>
        <h1>{patient['name']}</h1>
        <div class="muted">Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>

        <h2>Dados principais</h2>
        <div class="grid">
            <div class="box"><b>Idade:</b> {patient['age']}</div>
            <div class="box"><b>Sexo:</b> {patient['sex']}</div>
            <div class="box"><b>Peso:</b> {patient['weight']} kg</div>
            <div class="box"><b>Altura:</b> {patient['height']} cm</div>
            <div class="box"><b>IMC:</b> {patient['bmi']}</div>
            <div class="box"><b>Classificação:</b> {patient['bmi_class']}</div>
            <div class="box"><b>TMB:</b> {patient['bmr']} kcal</div>
            <div class="box"><b>TDEE:</b> {patient['tdee']} kcal</div>
            <div class="box"><b>Objetivo:</b> {patient['goal']}</div>
            <div class="box"><b>Atividade:</b> {patient['activity']}</div>
        </div>

        <h2>Queixa principal</h2>
        <div class="box">{patient['complaint'] or 'Não informado'}</div>

        <h2>Hábitos e observações</h2>
        <div class="box">{patient['notes'] or 'Não informado'}</div>
    </body>
    </html>
    """


def export_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


# =========================================================
# STYLE
# =========================================================
def inject_css():
    st.markdown(
        """
        <style>
        :root{
            --bg:#eef4fb;
            --bg2:#f7fbff;
            --card:#ffffff;
            --line:#d9e5f2;
            --text:#11203a;
            --muted:#62748f;
            --primary:#2563eb;
            --primary2:#1d4ed8;
            --accent:#14b8a6;
            --success:#16a34a;
            --danger:#dc2626;
            --shadow:0 12px 30px rgba(17,32,58,0.08);
        }

        html, body, .stApp {
            color: var(--text);
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(37,99,235,0.08), transparent 24%),
                linear-gradient(180deg, var(--bg2) 0%, var(--bg) 100%);
        }

        .main .block-container {
            padding-top: 1.3rem;
            padding-bottom: 1.8rem;
            opacity: 1 !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #12213f 100%);
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        [data-testid="stSidebar"] * {
            color: #eef4ff !important;
        }

        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] .stTextInput input,
        [data-testid="stSidebar"] .stNumberInput input {
            background: #ffffff !important;
            color: #11203a !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            border-radius: 14px !important;
        }

        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] span,
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] input {
            color: #11203a !important;
            -webkit-text-fill-color: #11203a !important;
        }

        div[data-baseweb="popover"] * {
            color: #11203a !important;
        }

        ul[role="listbox"],
        li[role="option"],
        div[role="option"] {
            background: #ffffff !important;
            color: #11203a !important;
        }

        ul[role="listbox"] li:hover,
        [role="option"]:hover {
            background: #eff6ff !important;
        }

        h1, h2, h3 {
            color: #071225 !important;
            letter-spacing: -0.02em;
        }

        h1 {
            font-size: 2.5rem !important;
            font-weight: 800 !important;
        }

        h2 {
            font-size: 1.75rem !important;
            font-weight: 800 !important;
        }

        .hero {
            background: linear-gradient(135deg, #0f172a 0%, #1c2f6f 55%, #2563eb 100%);
            border-radius: 28px;
            padding: 1.7rem 1.7rem 1.35rem 1.7rem;
            color: white;
            box-shadow: 0 22px 40px rgba(17,32,58,0.16);
            margin-bottom: 1rem;
        }

        .hero h1, .hero p {
            color: white !important;
            margin: 0;
        }

        .hero p {
            margin-top: 0.45rem;
            font-size: 1rem;
            opacity: 0.95;
        }

        .section-card {
            background: #ffffff !important;
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 1.1rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
            opacity: 1 !important;
        }

        .stMetric {
            background: #ffffff !important;
            color: #11203a !important;
            border: 1px solid #dbeafe !important;
            border-radius: 18px !important;
            padding: 0.8rem !important;
            box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08) !important;
            opacity: 1 !important;
        }

        .stMetric label {
            color: #64748b !important;
            font-weight: 600 !important;
        }

        .stMetric div {
            color: #0f172a !important;
            font-weight: 700 !important;
        }

        .stButton > button {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary2) 100%);
            color: white !important;
            border: none !important;
            border-radius: 14px !important;
            padding: 0.78rem 1rem !important;
            font-weight: 700 !important;
            box-shadow: 0 10px 20px rgba(37,99,235,0.20);
        }

        .stDownloadButton > button {
            background: linear-gradient(135deg, #0f766e 0%, #14b8a6 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 14px !important;
            padding: 0.78rem 1rem !important;
            font-weight: 700 !important;
        }

        .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea {
            background: #ffffff !important;
            color: #11203a !important;
            border-radius: 14px !important;
            border: 1px solid #cedceb !important;
        }

        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div {
            background: #ffffff !important;
            color: #11203a !important;
            border-radius: 14px !important;
            border: 1px solid #cedceb !important;
        }

        .stSelectbox div[data-baseweb="select"] span,
        .stMultiSelect div[data-baseweb="select"] span,
        .stSelectbox div[data-baseweb="select"] input,
        .stMultiSelect div[data-baseweb="select"] input {
            color: #11203a !important;
            -webkit-text-fill-color: #11203a !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            background: rgba(255,255,255,0.8);
            border: 1px solid var(--line);
            padding: 0.35rem;
            border-radius: 16px;
            gap: 0.35rem;
        }

        .stTabs [data-baseweb="tab"] {
            height: auto;
            padding: 0.7rem 0.95rem;
            border-radius: 12px;
            color: #334155 !important;
            font-weight: 700;
        }

        .stTabs [aria-selected="true"] {
            background: #e9f2ff !important;
            color: #11203a !important;
            border: 1px solid #bfd7ff !important;
        }

        div[data-testid="stDataFrame"], div[data-testid="stTable"] {
            border: 1px solid var(--line);
            border-radius: 16px;
            overflow: hidden;
            background: #ffffff !important;
        }

        [data-testid="stInfo"] {
            background: #e0f2fe !important;
            color: #0369a1 !important;
            font-weight: 600 !important;
            border-radius: 16px;
        }

        [data-testid="stSuccess"], [data-testid="stWarning"], [data-testid="stError"] {
            border-radius: 16px;
        }

        .soft {
            color: var(--muted) !important;
        }

        .kpi-strip {
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 0.9rem 1rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_start():
    st.markdown('<div class="section-card">', unsafe_allow_html=True)


def card_end():
    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# AUTH
# =========================================================
def register_user(username: str, password: str, full_name: str):
    users = st.session_state.app_data["users"]
    if username in users:
        return False, "Esse usuário já existe."
    users[username] = {
        "password_hash": hash_password(password),
        "profile": empty_user_profile(full_name),
        "patients": [],
        "plans": [],
        "diary": [],
        "history": [],
        "tasks": [],
        "study_progress": {},
        "crm_notes": [],
    }
    save_data()
    return True, "Conta criada com sucesso."


def login_user(username: str, password: str):
    users = st.session_state.app_data["users"]
    if username not in users:
        return False
    if users[username]["password_hash"] != hash_password(password):
        return False
    st.session_state.auth_user = username
    return True


def logout():
    st.session_state.auth_user = None


def auth_screen():
    hero(APP_NAME, "Visual de SaaS real, gestão de pacientes, dieta, estudos e rotina profissional")

    c1, c2 = st.columns(2)

    with c1:
        card_start()
        st.subheader("Entrar")
        username = st.text_input("Usuário", key="login_user")
        password = st.text_input("Senha", type="password", key="login_pass")
        if st.button("Entrar", use_container_width=True):
            if login_user(username.strip(), password):
                st.success("Login realizado.")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
        card_end()

    with c2:
        card_start()
        st.subheader("Criar conta")
        full_name = st.text_input("Nome completo", key="reg_name")
        new_user = st.text_input("Novo usuário", key="reg_user")
        new_pass = st.text_input("Nova senha", type="password", key="reg_pass")
        if st.button("Criar conta", use_container_width=True):
            if not full_name.strip() or not new_user.strip() or not new_pass.strip():
                st.error("Preencha todos os campos.")
            else:
                ok, msg = register_user(new_user.strip(), new_pass, full_name.strip())
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
        card_end()

    card_start()
    st.subheader("O que esta versão tem")
    st.markdown(
        "- login local por usuário\n"
        "- gestão separada por conta\n"
        "- painel com pacientes, planos, tarefas e histórico\n"
        "- exportação CSV e ficha HTML do paciente\n"
        "- CRM simples de acompanhamento\n"
        "- centro de estudos e rotina profissional\n"
        "- layout otimizado para ficar mais leve"
    )
    card_end()


# =========================================================
# APP
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
    st.markdown('<p class="soft">Painel estilo SaaS para gestão e prática em Nutrição.</p>', unsafe_allow_html=True)

    page = st.selectbox(
        "Menu principal",
        [
            "Dashboard",
            "Pacientes",
            "Planos Alimentares",
            "Diário Alimentar",
            "Calculadoras",
            "CRM e Tarefas",
            "Análises",
            "Faculdade e Estudos",
            "Configurações",
        ],
    )

    st.markdown("---")
    st.markdown("### Resumo")
    st.markdown(f"**Calorias hoje:** {today_kcal:.0f} kcal")
    st.markdown(f"**Proteínas:** {today_protein:.1f} g")
    st.markdown(f"**Pacientes:** {len(user['patients'])}")
    st.markdown(f"**Planos:** {len(user['plans'])}")
    st.markdown(f"**Tarefas:** {len(user['tasks'])}")

    if st.button("Sair", use_container_width=True):
        logout()
        st.rerun()


# =========================================================
# PAGES
# =========================================================
if page == "Dashboard":
    hero("Dashboard", "Sua central de operação para atendimento, faculdade e rotina diária")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pacientes", len(user["patients"]))
    c2.metric("Planos salvos", len(user["plans"]))
    c3.metric("Registros no diário", len(user["diary"]))
    c4.metric("Tarefas", len(user["tasks"]))

    left, right = st.columns([1.15, 0.85])

    with left:
        card_start()
        st.subheader("Visão do dia")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Kcal", f"{today_kcal:.0f}")
        m2.metric("Proteína", f"{today_protein:.1f} g")
        m3.metric("Carboidratos", f"{today_carbs:.1f} g")
        m4.metric("Gorduras", f"{today_fat:.1f} g")

        if today_entries:
            df = pd.DataFrame(
                [
                    {
                        "Data": x["data"].strftime("%d/%m/%Y"),
                        "Refeição": x["meal"],
                        "Alimento": x["food"],
                        "Porções": x["servings"],
                        "Kcal": round(x["kcal"], 1),
                        "Proteína": round(x["protein"], 1),
                    }
                    for x in today_entries
                ]
            )
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Ainda não há registros hoje.")
        card_end()

        card_start()
        st.subheader("Últimos movimentos")
        if user["history"]:
            hist = sorted(user["history"], key=lambda x: x["data"], reverse=True)[:10]
            df_hist = pd.DataFrame(
                [{"Data": x["data"].strftime("%d/%m/%Y %H:%M"), "Tipo": x["tipo"], "Descrição": x["descricao"]} for x in hist]
            )
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum histórico ainda.")
        card_end()

    with right:
        card_start()
        st.subheader("Pendências")
        pending = [x for x in user["tasks"] if not x.get("done")]
        if pending:
            for task in pending[:8]:
                st.markdown(f"- **{task['title']}** — {task['area']}")
        else:
            st.info("Nenhuma pendência em aberto.")
        card_end()

        card_start()
        st.subheader("Mapa rápido da formação")
        for area, topics in STUDY_AREAS.items():
            st.markdown(f"**{area}**")
            st.write(" • " + " • ".join(topics))
        card_end()


elif page == "Pacientes":
    hero("Pacientes", "Cadastro, avaliação inicial e exportação rápida")

    tab1, tab2 = st.tabs(["Novo paciente", "Base de pacientes"])

    with tab1:
        card_start()
        st.subheader("Cadastrar paciente")
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Nome")
        age = c2.number_input("Idade", min_value=0, step=1)
        sex = c3.selectbox("Sexo", ["Masculino", "Feminino"])

        c4, c5, c6 = st.columns(3)
        weight = c4.number_input("Peso (kg)", min_value=0.0, step=0.1)
        height = c5.number_input("Altura (cm)", min_value=0.0, step=1.0)
        activity = c6.selectbox("Atividade", list(ACTIVITY_FACTORS.keys()))

        goal = st.selectbox("Objetivo principal", ["Emagrecimento", "Hipertrofia", "Performance", "Saúde geral", "Melhora clínica"])
        complaint = st.text_area("Queixa principal")
        notes = st.text_area("Hábitos, observações e contexto")

        if st.button("Salvar paciente"):
            if name.strip() and age > 0 and weight > 0 and height > 0:
                bmi = calc_bmi(weight, height / 100)
                bmr, tdee = calc_tdee(weight, height, age, sex, activity)
                patient = {
                    "id": f"PT-{int(datetime.now().timestamp())}",
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
                add_history("Paciente", f"Paciente {patient['name']} cadastrado")
                st.success("Paciente salvo com sucesso.")
            else:
                st.error("Preencha nome, idade, peso e altura.")
        card_end()

    with tab2:
        card_start()
        st.subheader("Pacientes salvos")
        patients = sorted(user["patients"], key=lambda x: x["data"], reverse=True)

        if patients:
            table = pd.DataFrame(
                [
                    {
                        "ID": p["id"],
                        "Nome": p["name"],
                        "Objetivo": p["goal"],
                        "IMC": p["bmi"],
                        "TDEE": p["tdee"],
                        "Data": p["data"].strftime("%d/%m/%Y"),
                    }
                    for p in patients
                ]
            )
            st.dataframe(table, use_container_width=True, hide_index=True)
            st.download_button(
                "Exportar pacientes em CSV",
                data=export_csv_bytes(table),
                file_name="pacientes_nutriflow.csv",
                mime="text/csv",
                use_container_width=True,
            )

            for p in patients:
                with st.expander(f"{p['name']} — {p['goal']}"):
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("IMC", f"{p['bmi']:.2f}")
                    m2.metric("Classificação", p["bmi_class"])
                    m3.metric("TMB", f"{p['bmr']:.0f}")
                    m4.metric("TDEE", f"{p['tdee']:.0f}")
                    st.write(f"**Queixa principal:** {p['complaint'] or 'Não informada'}")
                    st.write(f"**Observações:** {p['notes'] or 'Sem observações'}")

                    html = patient_report_html(p).encode("utf-8")
                    st.download_button(
                        f"Baixar ficha HTML - {p['name']}",
                        data=html,
                        file_name=f"ficha_{p['name'].replace(' ', '_').lower()}.html",
                        mime="text/html",
                        key=f"dl_{p['id']}",
                    )
        else:
            st.info("Nenhum paciente salvo.")
        card_end()


elif page == "Planos Alimentares":
    hero("Planos Alimentares", "Monte modelos rápidos com cálculo automático")

    tab1, tab2 = st.tabs(["Criar plano", "Planos salvos"])

    with tab1:
        card_start()
        st.subheader("Novo plano")
        plan_name = st.text_input("Nome do plano")
        objective = st.selectbox("Objetivo", ["Manutenção", "Emagrecimento", "Hipertrofia", "Reeducação alimentar", "Performance"])
        kcal_target = st.number_input("Meta calórica", min_value=0, step=50)
        meals = st.multiselect("Refeições", ["Café da manhã", "Lanche manhã", "Almoço", "Lanche tarde", "Jantar", "Ceia"])
        selected_foods = st.multiselect("Alimentos", list(foods.keys()))

        portions = {}
        for food in selected_foods:
            portions[food] = st.number_input(f"Porções de {food}", min_value=0.1, step=0.1, value=1.0, key=f"portion_{food}")

        if st.button("Salvar plano"):
            if not plan_name.strip():
                st.error("Dê um nome ao plano.")
            elif not selected_foods:
                st.error("Selecione ao menos um alimento.")
            else:
                items = []
                total_kcal = total_p = total_c = total_f = 0.0
                for food in selected_foods:
                    item = foods[food]
                    q = portions[food]
                    row = {
                        "food": food,
                        "servings": q,
                        "kcal": item["kcal"] * q,
                        "protein": item["protein"] * q,
                        "carbs": item["carbs"] * q,
                        "fat": item["fat"] * q,
                    }
                    items.append(row)
                    total_kcal += row["kcal"]
                    total_p += row["protein"]
                    total_c += row["carbs"]
                    total_f += row["fat"]

                plan = {
                    "id": f"PL-{int(datetime.now().timestamp())}",
                    "name": plan_name.strip(),
                    "objective": objective,
                    "kcal_target": kcal_target,
                    "meals": meals,
                    "items": items,
                    "total_kcal": round(total_kcal, 1),
                    "total_protein": round(total_p, 1),
                    "total_carbs": round(total_c, 1),
                    "total_fat": round(total_f, 1),
                    "data": datetime.now(),
                }
                user["plans"].append(plan)
                save_data()
                add_history("Plano", f"Plano {plan['name']} salvo")
                st.success("Plano salvo com sucesso.")
        card_end()

    with tab2:
        card_start()
        st.subheader("Planos salvos")
        plans = sorted(user["plans"], key=lambda x: x["data"], reverse=True)
        if plans:
            for plan in plans:
                with st.expander(f"{plan['name']} — {plan['objective']}"):
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Kcal total", f"{plan['total_kcal']:.0f}")
                    m2.metric("Proteína", f"{plan['total_protein']:.1f} g")
                    m3.metric("Carboidratos", f"{plan['total_carbs']:.1f} g")
                    m4.metric("Gorduras", f"{plan['total_fat']:.1f} g")
                    rows = pd.DataFrame(
                        [
                            {
                                "Alimento": i["food"],
                                "Porções": i["servings"],
                                "Kcal": i["kcal"],
                                "Proteína": i["protein"],
                                "Carboidratos": i["carbs"],
                                "Gorduras": i["fat"],
                            }
                            for i in plan["items"]
                        ]
                    )
                    st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum plano salvo.")
        card_end()


elif page == "Diário Alimentar":
    hero("Diário Alimentar", "Registre refeições e use isso como base de análise real")

    left, right = st.columns([1.02, 0.98])

    with left:
        card_start()
        st.subheader("Adicionar refeição")
        meal = st.selectbox("Refeição", ["Café da manhã", "Lanche manhã", "Almoço", "Lanche tarde", "Jantar", "Ceia"])
        food = st.selectbox("Alimento", list(foods.keys()))
        servings = st.number_input("Porções", min_value=0.1, step=0.1, value=1.0)
        entry_date = st.date_input("Data", value=date.today())

        if st.button("Adicionar ao diário"):
            item = foods[food]
            entry = {
                "id": f"DG-{int(datetime.now().timestamp())}",
                "meal": meal,
                "food": food,
                "servings": servings,
                "kcal": item["kcal"] * servings,
                "protein": item["protein"] * servings,
                "carbs": item["carbs"] * servings,
                "fat": item["fat"] * servings,
                "fiber": item["fiber"] * servings,
                "data": datetime.combine(entry_date, datetime.min.time()),
            }
            user["diary"].append(entry)
            save_data()
            add_history("Diário", f"{food} adicionado ao diário")
            st.success("Registro salvo.")
        card_end()

        card_start()
        st.subheader("Banco de alimentos")
        search = st.text_input("Buscar alimento")
        filtered = {k: v for k, v in foods.items() if search.lower() in k.lower()} if search else foods
        df_foods = pd.DataFrame(
            [
                {"Alimento": k, "Kcal": v["kcal"], "Proteína": v["protein"], "Carboidratos": v["carbs"], "Gorduras": v["fat"], "Fibra": v["fiber"]}
                for k, v in filtered.items()
            ]
        )
        st.dataframe(df_foods, use_container_width=True, hide_index=True)

        with st.expander("Adicionar novo alimento"):
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
                        "kcal": kcal, "protein": protein, "carbs": carbs, "fat": fat, "fiber": fiber
                    }
                    save_data()
                    st.success("Alimento salvo.")
                else:
                    st.error("Digite o nome do alimento.")
        card_end()

    with right:
        card_start()
        st.subheader("Resumo por data")
        selected_date = st.date_input("Visualizar dia", value=date.today(), key="view_date")
        rows = [x for x in user["diary"] if x["data"].date() == selected_date]

        if rows:
            df = pd.DataFrame(
                [
                    {
                        "Refeição": x["meal"],
                        "Alimento": x["food"],
                        "Porções": x["servings"],
                        "Kcal": round(x["kcal"], 1),
                        "Proteína": round(x["protein"], 1),
                        "Carboidratos": round(x["carbs"], 1),
                        "Gorduras": round(x["fat"], 1),
                    }
                    for x in rows
                ]
            )
            st.dataframe(df, use_container_width=True, hide_index=True)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Kcal", f"{df['Kcal'].sum():.0f}")
            m2.metric("Proteína", f"{df['Proteína'].sum():.1f} g")
            m3.metric("Carboidratos", f"{df['Carboidratos'].sum():.1f} g")
            m4.metric("Gorduras", f"{df['Gorduras'].sum():.1f} g")
        else:
            st.info("Nenhum registro nessa data.")
        card_end()


elif page == "Calculadoras":
    hero("Calculadoras", "Ferramentas rápidas para clínica, estudo e tomada de decisão")

    tab1, tab2, tab3, tab4 = st.tabs(["IMC", "TMB/TDEE", "Meta Calórica", "Macros"])

    with tab1:
        card_start()
        st.subheader("IMC")
        c1, c2 = st.columns(2)
        weight = c1.number_input("Peso (kg)", min_value=0.0, step=0.1)
        height = c2.number_input("Altura (m)", min_value=0.0, step=0.01)
        if st.button("Calcular IMC"):
            bmi = calc_bmi(weight, height)
            if bmi:
                st.success(f"IMC: {bmi:.2f} — {bmi_label(bmi)}")
                add_history("IMC", f"IMC calculado: {bmi:.2f}")
            else:
                st.error("Preencha valores válidos.")
        card_end()

    with tab2:
        card_start()
        st.subheader("TMB e TDEE")
        c1, c2, c3 = st.columns(3)
        w = c1.number_input("Peso (kg)", min_value=0.0, step=0.1, key="tdee_w")
        h = c2.number_input("Altura (cm)", min_value=0.0, step=1.0, key="tdee_h")
        age = c3.number_input("Idade", min_value=0, step=1, key="tdee_age")
        c4, c5 = st.columns(2)
        sex = c4.selectbox("Sexo", ["Masculino", "Feminino"], key="tdee_sex")
        activity = c5.selectbox("Atividade", list(ACTIVITY_FACTORS.keys()), key="tdee_act")
        if st.button("Calcular TMB/TDEE"):
            if w > 0 and h > 0 and age > 0:
                bmr, tdee = calc_tdee(w, h, age, sex, activity)
                m1, m2, m3 = st.columns(3)
                m1.metric("TMB", f"{bmr:.0f}")
                m2.metric("TDEE", f"{tdee:.0f}")
                m3.metric("Déficit leve", f"{tdee*0.9:.0f}")
                add_history("TMB/TDEE", f"TMB {bmr:.0f} | TDEE {tdee:.0f}")
            else:
                st.error("Preencha tudo.")
        card_end()

    with tab3:
        card_start()
        st.subheader("Meta por objetivo")
        c1, c2, c3 = st.columns(3)
        w = c1.number_input("Peso (kg)", min_value=0.0, step=0.1, key="goal_w")
        h = c2.number_input("Altura (cm)", min_value=0.0, step=1.0, key="goal_h")
        age = c3.number_input("Idade", min_value=0, step=1, key="goal_age")
        c4, c5, c6 = st.columns(3)
        sex = c4.selectbox("Sexo", ["Masculino", "Feminino"], key="goal_sex")
        activity = c5.selectbox("Atividade", list(ACTIVITY_FACTORS.keys()), key="goal_act")
        goal = c6.selectbox("Objetivo", ["Manutenção", "Déficit leve", "Déficit moderado", "Ganho leve"])
        if st.button("Calcular meta"):
            if w > 0 and h > 0 and age > 0:
                _, tdee = calc_tdee(w, h, age, sex, activity)
                factor = {"Manutenção": 1.0, "Déficit leve": 0.9, "Déficit moderado": 0.85, "Ganho leve": 1.1}[goal]
                target = tdee * factor
                st.success(f"Meta estimada: {target:.0f} kcal/dia")
                add_history("Meta Calórica", f"{goal}: {target:.0f} kcal")
            else:
                st.error("Preencha tudo.")
        card_end()

    with tab4:
        card_start()
        st.subheader("Macronutrientes")
        kcal = st.number_input("Calorias diárias", min_value=0, step=50)
        c1, c2, c3 = st.columns(3)
        pp = c1.slider("Proteína (%)", 10, 45, 30)
        cp = c2.slider("Carboidratos (%)", 20, 70, 40)
        fp = c3.slider("Gorduras (%)", 15, 45, 30)
        if st.button("Calcular macros"):
            if kcal > 0 and pp + cp + fp == 100:
                p, c, f = macro_from_percent(kcal, pp, cp, fp)
                m1, m2, m3 = st.columns(3)
                m1.metric("Proteína", f"{p:.1f} g")
                m2.metric("Carboidratos", f"{c:.1f} g")
                m3.metric("Gorduras", f"{f:.1f} g")
                fig = px.pie(names=["Proteína", "Carboidratos", "Gorduras"], values=[pp, cp, fp], title="Distribuição (%)")
                st.plotly_chart(fig, use_container_width=True)
                add_history("Macros", f"Distribuição para {kcal} kcal")
            else:
                st.error("Informe calorias e faça a soma dar 100%.")
        card_end()


elif page == "CRM e Tarefas":
    hero("CRM e Tarefas", "Organize follow-up, pendências e relacionamento com seus pacientes")

    left, right = st.columns(2)

    with left:
        card_start()
        st.subheader("Nova tarefa")
        title = st.text_input("Título da tarefa")
        area = st.selectbox("Área", ["Paciente", "Estudo", "Administrativo", "Conteúdo", "Financeiro"])
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
                add_history("Tarefa", f"Tarefa criada: {title.strip()}")
                st.success("Tarefa salva.")
            else:
                st.error("Digite um título.")
        card_end()

        card_start()
        st.subheader("Anotação rápida de relacionamento")
        patient_names = [p["name"] for p in user["patients"]] or ["Sem pacientes cadastrados"]
        linked_patient = st.selectbox("Paciente vinculado", patient_names)
        note = st.text_area("Observação")
        if st.button("Salvar anotação"):
            if patient_names[0] == "Sem pacientes cadastrados":
                st.error("Cadastre um paciente primeiro.")
            elif note.strip():
                user["crm_notes"].append({
                    "patient": linked_patient,
                    "note": note.strip(),
                    "data": datetime.now(),
                })
                save_data()
                add_history("CRM", f"Nota adicionada para {linked_patient}")
                st.success("Anotação salva.")
            else:
                st.error("Escreva uma observação.")
        card_end()

    with right:
        card_start()
        st.subheader("Painel de tarefas")
        if user["tasks"]:
            for idx, task in enumerate(sorted(user["tasks"], key=lambda x: (x.get("done", False), x["due"]))):
                col1, col2 = st.columns([0.75, 0.25])
                done = col1.checkbox(
                    f"{task['title']} — {task['area']} — prazo {task['due']}",
                    value=task.get("done", False),
                    key=f"task_{idx}_{task['title']}",
                )
                user["tasks"][user["tasks"].index(task)]["done"] = done
                if col2.button("Excluir", key=f"del_{idx}"):
                    user["tasks"].remove(task)
                    save_data()
                    st.rerun()
            save_data()
        else:
            st.info("Nenhuma tarefa cadastrada.")
        card_end()

        card_start()
        st.subheader("Últimas anotações")
        if user["crm_notes"]:
            notes = sorted(user["crm_notes"], key=lambda x: x["data"], reverse=True)
            for item in notes[:10]:
                st.markdown(f"**{item['patient']}** — {item['data'].strftime('%d/%m/%Y %H:%M')}")
                st.write(item["note"])
                st.markdown("---")
        else:
            st.info("Nenhuma anotação ainda.")
        card_end()


elif page == "Análises":
    hero("Análises", "Transforme dados em leitura rápida e profissional")

    card_start()
    st.subheader("Histórico de ações")
    if user["history"]:
        hist = pd.DataFrame(
            [
                {"Data": x["data"].strftime("%d/%m/%Y %H:%M"), "Tipo": x["tipo"], "Descrição": x["descricao"]}
                for x in sorted(user["history"], key=lambda x: x["data"], reverse=True)
            ]
        )
        st.dataframe(hist, use_container_width=True, hide_index=True)
        st.download_button(
            "Exportar histórico em CSV",
            data=export_csv_bytes(hist),
            file_name="historico_nutriflow.csv",
            mime="text/csv",
        )
    else:
        st.info("Sem histórico.")
    card_end()

    card_start()
    st.subheader("Calorias por dia")
    if user["diary"]:
        df = pd.DataFrame([{"Data": x["data"].date(), "Calorias": x["kcal"]} for x in user["diary"]])
        resumo = df.groupby("Data", as_index=False).sum()
        fig = px.line(resumo, x="Data", y="Calorias", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Adicione registros no diário para ver análises.")
    card_end()

    card_start()
    st.subheader("Banco de alimentos mais calóricos")
    foods_df = pd.DataFrame(
        [{"Alimento": k, "Calorias": v["kcal"]} for k, v in foods.items()]
    ).sort_values("Calorias", ascending=False).head(12)
    fig = px.bar(foods_df, x="Alimento", y="Calorias")
    st.plotly_chart(fig, use_container_width=True)
    card_end()


elif page == "Faculdade e Estudos":
    hero("Faculdade e Estudos", "Use o app também como base de revisão do curso")

    tab1, tab2 = st.tabs(["Mapa de estudo", "Checklist de domínio"])

    with tab1:
        card_start()
        st.subheader("Mapa da graduação")
        for area, topics in STUDY_AREAS.items():
            st.markdown(f"### {area}")
            for t in topics:
                st.write(f"- {t}")
        st.info("Esse painel ajuda a organizar estudo de base biológica, alimentos, clínica, saúde coletiva e prática profissional.")
        card_end()

    with tab2:
        card_start()
        st.subheader("Checklist")
        for area, topics in STUDY_AREAS.items():
            st.markdown(f"**{area}**")
            for topic in topics:
                key = f"{area}::{topic}"
                checked = user["study_progress"].get(key, False)
                user["study_progress"][key] = st.checkbox(topic, value=checked, key=key)
        if st.button("Salvar progresso"):
            save_data()
            add_history("Estudos", "Progresso de estudos atualizado")
            st.success("Progresso salvo.")
        card_end()


elif page == "Configurações":
    hero("Configurações", "Ajustes do seu espaço e dados do perfil")

    card_start()
    st.subheader("Perfil")
    st.write(f"**Usuário:** {st.session_state.auth_user}")
    st.write(f"**Nome:** {user['profile']['full_name']}")
    st.write(f"**Criado em:** {user['profile']['created_at'][:10]}")
    card_end()

    card_start()
    st.subheader("Resumo técnico")
    st.markdown(
        "- esta versão usa login local com dados salvos em JSON\n"
        "- é uma base estilo SaaS, mas ainda sem banco online e sem multiacesso real em nuvem\n"
        "- já está pronta para evoluir depois para Firebase, Supabase ou banco SQL"
    )
    card_end()
