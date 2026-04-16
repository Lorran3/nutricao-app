
import json
from datetime import datetime, date, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================
# CONFIG
# =========================
DATA_FILE = Path("nutri_startup_data.json")

APP_TITLE = "NutriFlow Pro"
APP_SUBTITLE = "Faculdade, atendimento e rotina profissional em um só app"

DEFAULT_FOODS = {
    "Frango grelhado (100g)": {"kcal": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0},
    "Arroz cozido (100g)": {"kcal": 130, "protein": 2.7, "carbs": 28, "fat": 0.3, "fiber": 0.4},
    "Feijão cozido (100g)": {"kcal": 76, "protein": 4.8, "carbs": 13.6, "fat": 0.5, "fiber": 8.5},
    "Ovo inteiro (1 un)": {"kcal": 78, "protein": 6.3, "carbs": 0.6, "fat": 5.3, "fiber": 0},
    "Banana prata (1 un)": {"kcal": 98, "protein": 1.3, "carbs": 26, "fat": 0.1, "fiber": 2.0},
    "Maçã (1 un)": {"kcal": 95, "protein": 0.5, "carbs": 25, "fat": 0.3, "fiber": 4.4},
    "Aveia em flocos (30g)": {"kcal": 114, "protein": 4.0, "carbs": 19.5, "fat": 2.4, "fiber": 3.0},
    "Leite desnatado (200ml)": {"kcal": 70, "protein": 6.6, "carbs": 10, "fat": 0.2, "fiber": 0},
    "Iogurte natural (170g)": {"kcal": 108, "protein": 9.0, "carbs": 12.0, "fat": 3.0, "fiber": 0},
    "Batata-doce cozida (100g)": {"kcal": 86, "protein": 1.6, "carbs": 20.1, "fat": 0.1, "fiber": 3.0},
    "Salmão (100g)": {"kcal": 208, "protein": 20, "carbs": 0, "fat": 13, "fiber": 0},
    "Brócolis cozido (100g)": {"kcal": 35, "protein": 2.4, "carbs": 7.2, "fat": 0.4, "fiber": 3.3},
    "Pão integral (2 fatias)": {"kcal": 138, "protein": 6.0, "carbs": 24.0, "fat": 2.0, "fiber": 4.0},
    "Queijo minas (50g)": {"kcal": 132, "protein": 8.5, "carbs": 1.6, "fat": 10.2, "fiber": 0},
    "Castanha-do-pará (15g)": {"kcal": 99, "protein": 2.1, "carbs": 1.8, "fat": 10.1, "fiber": 1.1},
}

STUDY_MODULES = [
    {
        "categoria": "Base biológica",
        "itens": ["Anatomia", "Fisiologia", "Bioquímica", "Metabolismo energético", "Microbiologia"],
    },
    {
        "categoria": "Ciências dos alimentos",
        "itens": ["Bromatologia", "Técnica dietética", "Tecnologia de alimentos", "Higiene e segurança alimentar"],
    },
    {
        "categoria": "Nutrição aplicada",
        "itens": ["Avaliação nutricional", "Dietoterapia", "Nutrição clínica", "Nutrição esportiva", "Materno-infantil"],
    },
    {
        "categoria": "Saúde coletiva e gestão",
        "itens": ["Políticas públicas", "Epidemiologia", "Unidades de alimentação e nutrição", "Educação alimentar"],
    },
    {
        "categoria": "Profissão",
        "itens": ["Anamnese", "Prontuário", "Conduta", "Prescrição dietética", "Ética", "Comunicação com paciente"],
    },
]

PROFESSIONAL_AREAS = [
    "Nutrição clínica",
    "Alimentação coletiva",
    "Saúde coletiva",
    "Nutrição esportiva",
    "Docência e pesquisa",
    "Consultoria e gestão",
]

ACTIVITY_FACTORS = {
    "Sedentário": 1.2,
    "Levemente ativo": 1.375,
    "Moderadamente ativo": 1.55,
    "Muito ativo": 1.725,
    "Atleta": 1.9,
}


# =========================
# DATA LAYER
# =========================
def parse_dt(value):
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    return value


def default_store():
    return {
        "foods": DEFAULT_FOODS.copy(),
        "diary": [],
        "patients": [],
        "plans": [],
        "study_progress": {},
        "history": [],
    }


def load_store():
    if not DATA_FILE.exists():
        return default_store()

    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        raw.setdefault("foods", DEFAULT_FOODS.copy())
        raw.setdefault("diary", [])
        raw.setdefault("patients", [])
        raw.setdefault("plans", [])
        raw.setdefault("study_progress", {})
        raw.setdefault("history", [])

        for key in ["diary", "patients", "plans", "history"]:
            processed = []
            for item in raw.get(key, []):
                item = dict(item)
                if "data" in item:
                    item["data"] = parse_dt(item["data"])
                processed.append(item)
            raw[key] = processed

        merged_foods = DEFAULT_FOODS.copy()
        merged_foods.update(raw["foods"])
        raw["foods"] = merged_foods
        return raw
    except Exception:
        return default_store()


def save_store():
    store = st.session_state.store

    def encode(item):
        item = dict(item)
        if "data" in item and isinstance(item["data"], datetime):
            item["data"] = item["data"].isoformat()
        return item

    payload = {
        "foods": store["foods"],
        "diary": [encode(x) for x in store["diary"]],
        "patients": [encode(x) for x in store["patients"]],
        "plans": [encode(x) for x in store["plans"]],
        "study_progress": store["study_progress"],
        "history": [encode(x) for x in store["history"]],
    }
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def add_history(tipo, descricao, extra=None):
    item = {
        "tipo": tipo,
        "descricao": descricao,
        "data": datetime.now(),
    }
    if extra:
        item.update(extra)
    st.session_state.store["history"].append(item)
    save_store()


# =========================
# CALCULATIONS
# =========================
def calc_bmi(weight, height_m):
    if weight <= 0 or height_m <= 0:
        return None
    return weight / (height_m ** 2)


def bmi_category(bmi):
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
    return bmr, bmr * ACTIVITY_FACTORS[activity]


def macro_targets(calories, p_pct, c_pct, f_pct):
    protein_g = (calories * p_pct / 100) / 4
    carbs_g = (calories * c_pct / 100) / 4
    fat_g = (calories * f_pct / 100) / 9
    return protein_g, carbs_g, fat_g


# =========================
# UI HELPERS
# =========================
def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --bg: #eef4fb;
            --surface: #ffffff;
            --surface-soft: #f8fbff;
            --line: #d7e3f1;
            --text: #11203a;
            --muted: #5d718f;
            --primary: #2563eb;
            --primary-2: #1d4ed8;
            --accent: #14b8a6;
            --shadow: 0 10px 28px rgba(17, 32, 58, 0.08);
            --radius: 18px;
        }

        html, body, .stApp {
            color: var(--text);
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(37, 99, 235, 0.08), transparent 24%),
                linear-gradient(180deg, #f5f9ff 0%, var(--bg) 100%);
        }

        .main .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2rem;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #12213f 100%);
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        [data-testid="stSidebar"] * {
            color: #eef4ff !important;
        }

        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] .stTextInput input,
        [data-testid="stSidebar"] .stNumberInput input {
            background: #ffffff !important;
            color: #11203a !important;
            border-radius: 14px !important;
            border: 1px solid rgba(255,255,255,0.14) !important;
        }

        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] span,
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] input {
            color: #11203a !important;
            -webkit-text-fill-color: #11203a !important;
        }

        div[data-baseweb="popover"] * {
            color: #11203a !important;
        }

        ul[role="listbox"], li[role="option"], div[role="option"] {
            background: #ffffff !important;
            color: #11203a !important;
        }

        ul[role="listbox"] li:hover, [role="option"]:hover {
            background: #eff6ff !important;
        }

        h1, h2, h3 {
            color: var(--text) !important;
            letter-spacing: -0.02em;
        }

        h1 {
            font-size: 2.5rem !important;
            font-weight: 800 !important;
        }

        h2 {
            font-size: 1.7rem !important;
            font-weight: 800 !important;
        }

        .hero {
            background: linear-gradient(135deg, #0f172a 0%, #172554 55%, #2563eb 100%);
            border-radius: 26px;
            padding: 1.6rem 1.6rem 1.3rem 1.6rem;
            color: white;
            box-shadow: 0 18px 35px rgba(17, 32, 58, 0.16);
            margin-bottom: 1rem;
        }

        .hero h1, .hero p {
            color: white !important;
            margin: 0;
        }

        .hero p {
            opacity: 0.92;
            margin-top: 0.4rem;
            font-size: 1rem;
        }

        .section-card {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 1.1rem 1.1rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }

        .tip-box {
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 0.95rem;
            margin-bottom: 0.8rem;
        }

        .metric-row {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 0.75rem 0.9rem;
            box-shadow: var(--shadow);
        }

        .stMetric {
            background: linear-gradient(180deg, #ffffff 0%, #f7fbff 100%) !important;
            border: 1px solid var(--line) !important;
            border-radius: 18px !important;
            padding: 0.8rem !important;
            box-shadow: var(--shadow);
        }

        .stButton > button {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-2) 100%);
            color: white !important;
            border: none !important;
            border-radius: 14px !important;
            padding: 0.78rem 1.05rem !important;
            font-weight: 700 !important;
            box-shadow: 0 10px 20px rgba(37, 99, 235, 0.2);
        }

        .stButton > button:hover {
            transform: translateY(-1px);
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
            background: rgba(255,255,255,0.78);
            border: 1px solid var(--line);
            padding: 0.35rem;
            border-radius: 16px;
            gap: 0.35rem;
        }

        .stTabs [data-baseweb="tab"] {
            height: auto;
            padding: 0.7rem 0.9rem;
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
        }

        [data-testid="stInfo"], [data-testid="stSuccess"], [data-testid="stWarning"], [data-testid="stError"] {
            border-radius: 16px;
        }

        .small-muted {
            color: var(--muted) !important;
            font-size: 0.92rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title, subtitle):
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


def today_diary(store):
    today = date.today()
    return [x for x in store["diary"] if x["data"].date() == today]


def diary_dataframe(entries):
    rows = []
    for item in entries:
        rows.append({
            "Data": item["data"].strftime("%d/%m/%Y"),
            "Refeição": item["meal"],
            "Alimento": item["food"],
            "Porções": item["servings"],
            "Calorias": round(item["kcal"], 1),
            "Proteínas": round(item["protein"], 1),
            "Carboidratos": round(item["carbs"], 1),
            "Gorduras": round(item["fat"], 1),
        })
    return pd.DataFrame(rows)


# =========================
# APP INIT
# =========================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

if "store" not in st.session_state:
    st.session_state.store = load_store()

store = st.session_state.store
today_entries = today_diary(store)
today_kcal = sum(x["kcal"] for x in today_entries)
today_p = sum(x["protein"] for x in today_entries)
today_c = sum(x["carbs"] for x in today_entries)
today_f = sum(x["fat"] for x in today_entries)

with st.sidebar:
    st.markdown("## NutriFlow Pro")
    st.markdown('<p class="small-muted">Painel para faculdade, atendimento e prática profissional.</p>', unsafe_allow_html=True)

    page = st.selectbox(
        "Menu principal",
        [
            "Dashboard",
            "Calculadoras",
            "Diário Alimentar",
            "Planejador de Dieta",
            "Pacientes",
            "Análises",
            "Faculdade e Estudos",
            "Rotina Profissional",
            "Sobre o App",
        ],
    )

    st.markdown("---")
    st.markdown("### Resumo de hoje")
    st.markdown(f"**Calorias:** {today_kcal:.0f} kcal")
    st.markdown(f"**Proteína:** {today_p:.1f} g")
    st.markdown(f"**Carboidratos:** {today_c:.1f} g")
    st.markdown(f"**Gorduras:** {today_f:.1f} g")
    st.markdown(f"**Pacientes salvos:** {len(store['patients'])}")
    st.markdown(f"**Planos salvos:** {len(store['plans'])}")


# =========================
# PAGES
# =========================
if page == "Dashboard":
    hero(APP_TITLE, APP_SUBTITLE)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registros no diário", len(store["diary"]))
    c2.metric("Alimentos cadastrados", len(store["foods"]))
    c3.metric("Pacientes", len(store["patients"]))
    c4.metric("Planos alimentares", len(store["plans"]))

    col_a, col_b = st.columns([1.15, 0.85])

    with col_a:
        card_start()
        st.subheader("Visão geral do dia")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Calorias", f"{today_kcal:.0f}")
        c2.metric("Proteína", f"{today_p:.1f} g")
        c3.metric("Carboidratos", f"{today_c:.1f} g")
        c4.metric("Gorduras", f"{today_f:.1f} g")

        if today_entries:
            df = diary_dataframe(today_entries)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Ainda não há registros hoje. Use a página Diário Alimentar.")
        card_end()

        card_start()
        st.subheader("Atalhos inteligentes")
        st.write("Use o app como central de estudos e prática. Os módulos mais úteis para o dia a dia são:")
        st.markdown(
            "- **Calculadoras** para IMC, TMB, TDEE e metas de macronutrientes\n"
            "- **Planejador de Dieta** para montar refeições e salvar modelos\n"
            "- **Pacientes** para registrar anamnese rápida e objetivo\n"
            "- **Faculdade e Estudos** para revisar os grandes eixos da formação\n"
            "- **Rotina Profissional** para organizar avaliação, atendimento e condutas"
        )
        card_end()

    with col_b:
        card_start()
        st.subheader("Estrutura da formação")
        for bloco in STUDY_MODULES:
            st.markdown(f"**{bloco['categoria']}**")
            st.write(" • " + " • ".join(bloco["itens"]))
        card_end()

        card_start()
        st.subheader("Áreas de atuação")
        for area in PROFESSIONAL_AREAS:
            st.markdown(f"- {area}")
        card_end()


elif page == "Calculadoras":
    hero("Calculadoras", "Ferramentas rápidas para avaliação nutricional e tomada de decisão")

    tab1, tab2, tab3, tab4 = st.tabs(["IMC", "TMB e TDEE", "Meta Calórica", "Macronutrientes"])

    with tab1:
        card_start()
        st.subheader("Calculadora de IMC")
        col1, col2 = st.columns(2)
        weight = col1.number_input("Peso (kg)", min_value=0.0, step=0.1)
        height = col2.number_input("Altura (m)", min_value=0.0, step=0.01)

        if st.button("Calcular IMC", key="bmi_btn"):
            bmi = calc_bmi(weight, height)
            if bmi:
                cat = bmi_category(bmi)
                st.success(f"IMC: {bmi:.2f} — {cat}")
                add_history("IMC", f"IMC {bmi:.2f}", {"valor": bmi, "categoria": cat})
            else:
                st.error("Informe peso e altura válidos.")
        card_end()

    with tab2:
        card_start()
        st.subheader("TMB e TDEE")
        c1, c2, c3 = st.columns(3)
        w = c1.number_input("Peso (kg)", min_value=0.0, step=0.1, key="tdee_w")
        h = c2.number_input("Altura (cm)", min_value=0.0, step=1.0, key="tdee_h")
        age = c3.number_input("Idade", min_value=0, step=1, key="tdee_age")
        c4, c5 = st.columns(2)
        sex = c4.selectbox("Sexo", ["Masculino", "Feminino"])
        activity = c5.selectbox("Nível de atividade", list(ACTIVITY_FACTORS.keys()))

        if st.button("Calcular TMB e TDEE", key="tdee_btn"):
            if w > 0 and h > 0 and age > 0:
                bmr, tdee = calc_tdee(w, h, age, sex, activity)
                m1, m2, m3 = st.columns(3)
                m1.metric("TMB", f"{bmr:.0f} kcal")
                m2.metric("TDEE", f"{tdee:.0f} kcal")
                m3.metric("Déficit leve", f"{tdee*0.9:.0f} kcal")
                st.info(f"Manutenção: {tdee:.0f} kcal | Ganho leve: {tdee*1.1:.0f} kcal")
                add_history("TMB/TDEE", f"TMB {bmr:.0f} e TDEE {tdee:.0f}", {"tmb": bmr, "tdee": tdee})
            else:
                st.error("Preencha todos os campos.")
        card_end()

    with tab3:
        card_start()
        st.subheader("Meta calórica por objetivo")
        c1, c2, c3 = st.columns(3)
        w = c1.number_input("Peso (kg)", min_value=0.0, step=0.1, key="goal_w")
        h = c2.number_input("Altura (cm)", min_value=0.0, step=1.0, key="goal_h")
        age = c3.number_input("Idade", min_value=0, step=1, key="goal_age")
        c4, c5, c6 = st.columns(3)
        sex = c4.selectbox("Sexo", ["Masculino", "Feminino"], key="goal_sex")
        activity = c5.selectbox("Atividade", list(ACTIVITY_FACTORS.keys()), key="goal_act")
        goal = c6.selectbox("Objetivo", ["Manutenção", "Déficit leve", "Déficit moderado", "Ganho leve"])

        if st.button("Calcular meta", key="goal_btn"):
            if w > 0 and h > 0 and age > 0:
                bmr, tdee = calc_tdee(w, h, age, sex, activity)
                factor = {
                    "Manutenção": 1.00,
                    "Déficit leve": 0.90,
                    "Déficit moderado": 0.85,
                    "Ganho leve": 1.10,
                }[goal]
                target = tdee * factor
                c1, c2, c3 = st.columns(3)
                c1.metric("TMB", f"{bmr:.0f} kcal")
                c2.metric("TDEE", f"{tdee:.0f} kcal")
                c3.metric("Meta", f"{target:.0f} kcal")
                add_history("Meta Calórica", f"{goal}: {target:.0f} kcal", {"meta": target})
            else:
                st.error("Preencha todos os campos.")
        card_end()

    with tab4:
        card_start()
        st.subheader("Distribuição de macronutrientes")
        kcal = st.number_input("Calorias diárias", min_value=0, step=50)
        c1, c2, c3 = st.columns(3)
        p_pct = c1.slider("Proteína (%)", 10, 45, 30)
        c_pct = c2.slider("Carboidratos (%)", 20, 70, 40)
        f_pct = c3.slider("Gorduras (%)", 15, 45, 30)

        if st.button("Calcular macros", key="macro_btn"):
            if kcal > 0 and p_pct + c_pct + f_pct == 100:
                pg, cg, fg = macro_targets(kcal, p_pct, c_pct, f_pct)
                m1, m2, m3 = st.columns(3)
                m1.metric("Proteína", f"{pg:.1f} g")
                m2.metric("Carboidratos", f"{cg:.1f} g")
                m3.metric("Gorduras", f"{fg:.1f} g")

                fig = px.pie(
                    names=["Proteína", "Carboidratos", "Gorduras"],
                    values=[p_pct, c_pct, f_pct],
                    title="Distribuição de macronutrientes (%)",
                )
                st.plotly_chart(fig, use_container_width=True)
                add_history("Macros", f"Macros para {kcal} kcal", {"kcal": kcal})
            elif kcal <= 0:
                st.error("Informe as calorias.")
            else:
                st.error("A soma dos percentuais deve ser 100.")
        card_end()


elif page == "Diário Alimentar":
    hero("Diário Alimentar", "Registre refeições, acompanhe macros e monte histórico real do dia a dia")

    col1, col2 = st.columns([1.05, 0.95])

    with col1:
        card_start()
        st.subheader("Novo registro")
        foods = store["foods"]
        meal = st.selectbox("Refeição", ["Café da manhã", "Lanche manhã", "Almoço", "Lanche tarde", "Jantar", "Ceia"])
        food = st.selectbox("Alimento", list(foods.keys()))
        servings = st.number_input("Porções", min_value=0.1, step=0.1, value=1.0)
        entry_date = st.date_input("Data", value=date.today())

        if st.button("Adicionar ao diário"):
            item = foods[food]
            record = {
                "data": datetime.combine(entry_date, datetime.min.time()),
                "meal": meal,
                "food": food,
                "servings": servings,
                "kcal": item["kcal"] * servings,
                "protein": item["protein"] * servings,
                "carbs": item["carbs"] * servings,
                "fat": item["fat"] * servings,
                "fiber": item["fiber"] * servings,
            }
            store["diary"].append(record)
            save_store()
            add_history("Diário", f"{food} adicionado ao diário")
            st.success("Registro adicionado com sucesso.")
        card_end()

        card_start()
        st.subheader("Banco de alimentos")
        search = st.text_input("Buscar alimento")
        foods_filtered = {
            k: v for k, v in foods.items()
            if search.lower() in k.lower()
        } if search else foods

        rows = []
        for name, vals in foods_filtered.items():
            rows.append({
                "Alimento": name,
                "Kcal": vals["kcal"],
                "Proteína": vals["protein"],
                "Carboidratos": vals["carbs"],
                "Gorduras": vals["fat"],
                "Fibra": vals["fiber"],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        with st.expander("Adicionar novo alimento"):
            name = st.text_input("Nome", key="food_name")
            c1, c2, c3 = st.columns(3)
            kcal = c1.number_input("Kcal", min_value=0.0, step=1.0, key="food_kcal")
            protein = c2.number_input("Proteína", min_value=0.0, step=0.1, key="food_p")
            carbs = c3.number_input("Carboidratos", min_value=0.0, step=0.1, key="food_c")
            c4, c5 = st.columns(2)
            fat = c4.number_input("Gorduras", min_value=0.0, step=0.1, key="food_f")
            fiber = c5.number_input("Fibra", min_value=0.0, step=0.1, key="food_fb")

            if st.button("Salvar alimento"):
                if name.strip():
                    store["foods"][name.strip()] = {
                        "kcal": kcal,
                        "protein": protein,
                        "carbs": carbs,
                        "fat": fat,
                        "fiber": fiber,
                    }
                    save_store()
                    st.success("Alimento salvo.")
                else:
                    st.error("Digite o nome do alimento.")
        card_end()

    with col2:
        card_start()
        st.subheader("Resumo do dia selecionado")
        selected_day = st.date_input("Visualizar data", value=date.today(), key="view_day")
        entries = [x for x in store["diary"] if x["data"].date() == selected_day]
        if entries:
            df = diary_dataframe(entries)
            st.dataframe(df, use_container_width=True, hide_index=True)

            total_kcal = sum(x["kcal"] for x in entries)
            total_p = sum(x["protein"] for x in entries)
            total_c = sum(x["carbs"] for x in entries)
            total_f = sum(x["fat"] for x in entries)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Kcal", f"{total_kcal:.0f}")
            m2.metric("P", f"{total_p:.1f} g")
            m3.metric("C", f"{total_c:.1f} g")
            m4.metric("G", f"{total_f:.1f} g")
        else:
            st.info("Nenhum registro nesta data.")
        card_end()


elif page == "Planejador de Dieta":
    hero("Planejador de Dieta", "Monte planos alimentares rápidos para estudo, rotina ou atendimento")

    tab1, tab2 = st.tabs(["Montar plano", "Planos salvos"])

    with tab1:
        card_start()
        st.subheader("Novo plano alimentar")
        plan_name = st.text_input("Nome do plano")
        objective = st.selectbox("Objetivo", ["Manutenção", "Emagrecimento", "Hipertrofia", "Reeducação alimentar", "Performance"])
        kcal_target = st.number_input("Meta calórica do plano", min_value=0, step=50)
        meals = st.multiselect("Refeições incluídas", ["Café da manhã", "Lanche manhã", "Almoço", "Lanche tarde", "Jantar", "Ceia"])

        selected_foods = st.multiselect("Alimentos do plano", list(store["foods"].keys()))
        portions = {}
        for f in selected_foods:
            portions[f] = st.number_input(f"Porções de {f}", min_value=0.1, step=0.1, value=1.0, key=f"portion_{f}")

        if st.button("Salvar plano alimentar"):
            if not plan_name.strip():
                st.error("Dê um nome ao plano.")
            elif not selected_foods:
                st.error("Selecione ao menos um alimento.")
            else:
                items = []
                total_kcal = total_p = total_c = total_f = 0
                for f in selected_foods:
                    vals = store["foods"][f]
                    mult = portions[f]
                    entry = {
                        "food": f,
                        "servings": mult,
                        "kcal": vals["kcal"] * mult,
                        "protein": vals["protein"] * mult,
                        "carbs": vals["carbs"] * mult,
                        "fat": vals["fat"] * mult,
                    }
                    total_kcal += entry["kcal"]
                    total_p += entry["protein"]
                    total_c += entry["carbs"]
                    total_f += entry["fat"]
                    items.append(entry)

                plan = {
                    "data": datetime.now(),
                    "name": plan_name.strip(),
                    "objective": objective,
                    "kcal_target": kcal_target,
                    "meals": meals,
                    "items": items,
                    "total_kcal": total_kcal,
                    "total_protein": total_p,
                    "total_carbs": total_c,
                    "total_fat": total_f,
                }
                store["plans"].append(plan)
                save_store()
                add_history("Plano", f"Plano {plan_name} salvo")
                st.success("Plano salvo com sucesso.")

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Kcal total", f"{total_kcal:.0f}")
                m2.metric("Proteína", f"{total_p:.1f} g")
                m3.metric("Carboidratos", f"{total_c:.1f} g")
                m4.metric("Gorduras", f"{total_f:.1f} g")
        card_end()

    with tab2:
        card_start()
        st.subheader("Planos salvos")
        plans = sorted(store["plans"], key=lambda x: x["data"], reverse=True)
        if plans:
            for plan in plans:
                with st.expander(f"{plan['name']} — {plan['objective']} ({plan['total_kcal']:.0f} kcal)"):
                    st.write(f"**Meta informada:** {plan['kcal_target']:.0f} kcal")
                    st.write(f"**Refeições:** {', '.join(plan['meals']) if plan['meals'] else 'Não definido'}")
                    rows = []
                    for item in plan["items"]:
                        rows.append({
                            "Alimento": item["food"],
                            "Porções": item["servings"],
                            "Kcal": round(item["kcal"], 1),
                            "Proteína": round(item["protein"], 1),
                            "Carboidratos": round(item["carbs"], 1),
                            "Gorduras": round(item["fat"], 1),
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum plano salvo ainda.")
        card_end()


elif page == "Pacientes":
    hero("Pacientes", "Ficha rápida para anamnese, objetivo e avaliação inicial")

    tab1, tab2 = st.tabs(["Novo paciente", "Pacientes salvos"])

    with tab1:
        card_start()
        st.subheader("Cadastro rápido")
        c1, c2 = st.columns(2)
        name = c1.text_input("Nome do paciente")
        age = c2.number_input("Idade", min_value=0, step=1)
        c3, c4 = st.columns(2)
        sex = c3.selectbox("Sexo", ["Masculino", "Feminino"], key="patient_sex")
        objective = c4.selectbox("Objetivo principal", ["Emagrecimento", "Hipertrofia", "Performance", "Saúde geral", "Melhora clínica"])
        c5, c6 = st.columns(2)
        weight = c5.number_input("Peso (kg)", min_value=0.0, step=0.1, key="patient_w")
        height = c6.number_input("Altura (cm)", min_value=0.0, step=1.0, key="patient_h")
        activity = st.selectbox("Atividade física", list(ACTIVITY_FACTORS.keys()), key="patient_activity")
        notes = st.text_area("Queixa principal / observações")
        habits = st.text_area("Rotina, sono, fome, adesão, preferências alimentares")

        if st.button("Salvar paciente"):
            if name.strip() and age > 0 and weight > 0 and height > 0:
                bmi = calc_bmi(weight, height / 100)
                bmr, tdee = calc_tdee(weight, height, age, sex, activity)
                patient = {
                    "data": datetime.now(),
                    "name": name.strip(),
                    "age": age,
                    "sex": sex,
                    "objective": objective,
                    "weight": weight,
                    "height": height,
                    "activity": activity,
                    "bmi": round(bmi, 2),
                    "bmi_category": bmi_category(bmi),
                    "tmb": round(bmr, 1),
                    "tdee": round(tdee, 1),
                    "notes": notes,
                    "habits": habits,
                }
                store["patients"].append(patient)
                save_store()
                add_history("Paciente", f"Paciente {name} salvo")
                st.success("Paciente salvo com avaliação inicial calculada.")
            else:
                st.error("Preencha nome, idade, peso e altura.")
        card_end()

    with tab2:
        card_start()
        st.subheader("Pacientes salvos")
        patients = sorted(store["patients"], key=lambda x: x["data"], reverse=True)
        if patients:
            for patient in patients:
                with st.expander(f"{patient['name']} — {patient['objective']}"):
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("IMC", f"{patient['bmi']:.2f}")
                    m2.metric("Classificação", patient["bmi_category"])
                    m3.metric("TMB", f"{patient['tmb']:.0f}")
                    m4.metric("TDEE", f"{patient['tdee']:.0f}")
                    st.write(f"**Idade:** {patient['age']} | **Sexo:** {patient['sex']} | **Atividade:** {patient['activity']}")
                    st.write(f"**Observações:** {patient['notes'] or 'Sem observações'}")
                    st.write(f"**Hábitos:** {patient['habits'] or 'Sem registro'}")
        else:
            st.info("Nenhum paciente salvo.")
        card_end()


elif page == "Análises":
    hero("Análises", "Transforme diário e histórico em visão clara para estudo e acompanhamento")

    card_start()
    st.subheader("Histórico geral")
    if store["history"]:
        hist = pd.DataFrame([
            {
                "Data": item["data"].strftime("%d/%m/%Y %H:%M"),
                "Tipo": item["tipo"],
                "Descrição": item["descricao"],
            }
            for item in sorted(store["history"], key=lambda x: x["data"], reverse=True)
        ])
        st.dataframe(hist, use_container_width=True, hide_index=True)
    else:
        st.info("Sem histórico por enquanto.")
    card_end()

    card_start()
    st.subheader("Consumo calórico por dia")
    if store["diary"]:
        rows = []
        for item in store["diary"]:
            rows.append({"Data": item["data"].date(), "Calorias": item["kcal"]})
        df = pd.DataFrame(rows).groupby("Data", as_index=False).sum()
        fig = px.line(df, x="Data", y="Calorias", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Adicione refeições ao diário para gerar análises.")
    card_end()

    card_start()
    st.subheader("Top alimentos do banco")
    rows = []
    for name, vals in store["foods"].items():
        rows.append({"Alimento": name, "Calorias": vals["kcal"]})
    df_foods = pd.DataFrame(rows).sort_values("Calorias", ascending=False).head(12)
    if not df_foods.empty:
        fig = px.bar(df_foods, x="Alimento", y="Calorias")
        st.plotly_chart(fig, use_container_width=True)
    card_end()


elif page == "Faculdade e Estudos":
    hero("Faculdade e Estudos", "Um centro de revisão pensado para o curso de Nutrição")

    tab1, tab2, tab3 = st.tabs(["Mapa da graduação", "Checklist", "Rotina de estudo"])

    with tab1:
        card_start()
        st.subheader("Grandes pilares da formação")
        for bloco in STUDY_MODULES:
            st.markdown(f"### {bloco['categoria']}")
            for item in bloco["itens"]:
                st.write(f"- {item}")
        st.info(
            "Este módulo cobre a base biológica, alimentos, avaliação nutricional, dietoterapia, saúde coletiva, gestão e prática profissional."
        )
        card_end()

    with tab2:
        card_start()
        st.subheader("Checklist de domínio")
        for bloco in STUDY_MODULES:
            st.markdown(f"**{bloco['categoria']}**")
            for item in bloco["itens"]:
                key = f"study::{bloco['categoria']}::{item}"
                checked = st.session_state.store["study_progress"].get(key, False)
                new_value = st.checkbox(item, value=checked, key=key)
                st.session_state.store["study_progress"][key] = new_value
        if st.button("Salvar progresso"):
            save_store()
            st.success("Progresso salvo.")
        card_end()

    with tab3:
        card_start()
        st.subheader("Plano semanal sugerido")
        st.markdown(
            "- **Segunda:** Anatomia, fisiologia e bioquímica\n"
            "- **Terça:** Técnica dietética, bromatologia e tecnologia de alimentos\n"
            "- **Quarta:** Avaliação nutricional e dietoterapia\n"
            "- **Quinta:** Nutrição clínica e esportiva\n"
            "- **Sexta:** Saúde coletiva, epidemiologia e políticas públicas\n"
            "- **Sábado:** Estudos de caso, prontuário e prescrição\n"
            "- **Domingo:** Revisão leve e leitura científica"
        )

        st.subheader("Como usar o app para estudar")
        st.markdown(
            "- Monte casos simulados na aba **Pacientes**\n"
            "- Use **Calculadoras** para revisar fórmulas e interpretação\n"
            "- Use o **Planejador de Dieta** para treinar composição de cardápio\n"
            "- Use **Análises** para interpretar dados e padrões"
        )
        card_end()


elif page == "Rotina Profissional":
    hero("Rotina Profissional", "Ferramentas e lembretes para consulta, evolução e prática diária")

    col1, col2 = st.columns(2)

    with col1:
        card_start()
        st.subheader("Checklist de atendimento")
        st.markdown(
            "- Identificação do paciente\n"
            "- Queixa principal\n"
            "- Histórico clínico\n"
            "- Histórico alimentar\n"
            "- Rotina, sono, estresse e atividade física\n"
            "- Avaliação antropométrica\n"
            "- Objetivo terapêutico\n"
            "- Conduta inicial\n"
            "- Meta de adesão\n"
            "- Retorno agendado"
        )
        card_end()

        card_start()
        st.subheader("Ferramentas essenciais")
        st.markdown(
            "- Avaliação antropométrica básica\n"
            "- Cálculo energético\n"
            "- Distribuição de macronutrientes\n"
            "- Planejamento alimentar\n"
            "- Educação alimentar\n"
            "- Registro de evolução"
        )
        card_end()

    with col2:
        card_start()
        st.subheader("Áreas para crescer na profissão")
        st.markdown(
            "- Nutrição clínica\n"
            "- Esportiva\n"
            "- Saúde coletiva\n"
            "- Alimentação coletiva\n"
            "- Consultoria\n"
            "- Docência e pesquisa"
        )

        st.subheader("Competências que mais ajudam no mercado")
        st.markdown(
            "- Comunicação clara com paciente\n"
            "- Organização de prontuário e rotina\n"
            "- Interpretação de dados\n"
            "- Educação alimentar\n"
            "- Acompanhamento com metas simples\n"
            "- Presença digital e posicionamento"
        )
        card_end()

        card_start()
        st.subheader("Rotina prática do dia")
        agenda = [
            ("08:00", "Revisar agenda e retornos"),
            ("09:00", "Atendimento e anamnese"),
            ("11:00", "Montagem de plano alimentar"),
            ("14:00", "Acompanhamento de adesão"),
            ("16:00", "Estudo de caso / atualização"),
            ("18:00", "Organização de registros"),
        ]
        st.table(pd.DataFrame(agenda, columns=["Horário", "Atividade"]))
        card_end()


elif page == "Sobre o App":
    hero("Sobre o App", "Projeto startup em Streamlit para Nutrição")

    card_start()
    st.subheader("O que este app reúne")
    st.markdown(
        "- Dashboard com visão do dia\n"
        "- Calculadoras de avaliação nutricional\n"
        "- Diário alimentar com macros\n"
        "- Banco de alimentos editável\n"
        "- Planejador de dieta\n"
        "- Cadastro rápido de pacientes\n"
        "- Análises de histórico\n"
        "- Centro de estudos para faculdade\n"
        "- Módulo de rotina profissional"
    )
    st.write(f"**Última execução:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    card_end()
