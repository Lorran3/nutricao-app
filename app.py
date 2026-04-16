import json
import os
from datetime import datetime, date
from pathlib import Path

import openai
import pandas as pd
import plotly.express as px
import streamlit as st


DATA_FILE = Path("nutrition_data.json")

DEFAULT_ALIMENTOS = {
    "Frango (100g)": 165,
    "Arroz cozido (100g)": 130,
    "Brócolis (100g)": 34,
    "Ovos (1 unidade)": 155,
    "Maçã (média)": 95,
    "Banana (média)": 105,
    "Pão integral (1 fatia)": 80,
    "Leite desnatado (200ml)": 66,
    "Iogurte grego (100g)": 59,
    "Salmão (100g)": 208,
}

OPENAI_MODEL_DEFAULT = "gpt-3.5-turbo"

STUDY_SUBJECTS = [
    "Anatomia e Fisiologia",
    "Bioquímica",
    "Bases da Nutrição",
    "Alimentos e Cultura",
    "Saúde Coletiva e Epidemiologia",
    "Nutrição Clínica",
    "Tecnologia de Alimentos",
    "Nutrição Materno-Infantil",
    "Nutrição Esportiva",
    "Educação em Saúde",
    "Metodologia de Pesquisa",
    "Estágio Supervisionado",
]

STUDY_TIPS = [
    "Organize o semestre por blocos de revisão e prática.",
    "Use mapas mentais para conectar macros, vitaminas e fisiologia.",
    "Leia artigos recentes sobre políticas públicas de alimentação.",
    "Pratique cálculos de necessidade energética e substituição de alimentos.",
    "Acompanhe o diário alimentar do ponto de vista clínico e social.",
]


def get_openai_api_key():
    if "OPENAI_API_KEY" in st.secrets:
        return st.secrets["OPENAI_API_KEY"]
    return os.getenv("OPENAI_API_KEY", "")


def ask_openai(api_key, user_message, history=None, model=OPENAI_MODEL_DEFAULT):
    if not api_key:
        raise ValueError("Nenhuma chave de API OpenAI encontrada.")

    openai.api_key = api_key
    messages = [
        {
            "role": "system",
            "content": (
                "Você é uma assistente de nutrição e estudos universitários. "
                "Ajude a responder dúvidas sobre matérias, rotinas de estudo, alimentação e conceitos práticos."
            ),
        }
    ]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": user_message})

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        max_tokens=600,
        temperature=0.75,
    )
    return response.choices[0].message["content"].strip()


def parse_datetime(value):
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f")
    return value


def load_data():
    if DATA_FILE.exists():
        try:
            raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            raw["historico"] = [
                {**item, "data": parse_datetime(item["data"])}
                for item in raw.get("historico", [])
            ]
            raw["diario"] = [
                {**item, "data": parse_datetime(item["data"])}
                for item in raw.get("diario", [])
            ]
            raw["dietas"] = [
                {**item, "data": parse_datetime(item["data"])}
                for item in raw.get("dietas", [])
            ]
            raw["alimentos_favoritos"] = raw.get(
                "alimentos_favoritos", DEFAULT_ALIMENTOS.copy()
            )
            return raw
        except Exception:
            st.warning("Os dados salvos estão corrompidos. Usando valores padrão.")

    return {
        "alimentos_favoritos": DEFAULT_ALIMENTOS.copy(),
        "historico": [],
        "diario": [],
        "dietas": [],
    }


def save_data():
    store = st.session_state.data_store
    output = {
        "alimentos_favoritos": store["alimentos_favoritos"],
        "historico": [
            {
                **item,
                "data": item["data"].isoformat()
                if isinstance(item["data"], datetime)
                else item["data"],
            }
            for item in store["historico"]
        ],
        "diario": [
            {
                **item,
                "data": item["data"].isoformat()
                if isinstance(item["data"], datetime)
                else item["data"],
            }
            for item in store["diario"]
        ],
        "dietas": [
            {
                **item,
                "data": item["data"].isoformat()
                if isinstance(item["data"], datetime)
                else item["data"],
            }
            for item in store["dietas"]
        ],
    }
    DATA_FILE.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def add_historico(entry):
    st.session_state.data_store["historico"].append(entry)
    save_data()


def add_diario(entry):
    store = st.session_state.data_store
    store["diario"].append(entry)
    store["historico"].append(
        {
            "tipo": "Diário",
            "descricao": entry["descricao"],
            "calorias": entry["calorias"],
            "refeicao": entry["refeicao"],
            "data": entry["data"],
        }
    )
    save_data()


def add_alimento(nome, calorias):
    st.session_state.data_store["alimentos_favoritos"][nome] = calorias
    save_data()


def delete_alimentos(chaves):
    for chave in chaves:
        st.session_state.data_store["alimentos_favoritos"].pop(chave, None)
    save_data()


def add_dieta(dieta):
    st.session_state.data_store["dietas"].append(dieta)
    save_data()


st.set_page_config(
    page_title="Sistema de Auxiliar em Nutrição",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        :root {
            --bg: #edf3fb;
            --surface: #ffffff;
            --surface-2: #f8fbff;
            --border: #d8e4f3;
            --text: #0f172a;
            --muted: #5b6b84;
            --primary: #2563eb;
            --primary-2: #1d4ed8;
            --accent: #14b8a6;
            --success: #16a34a;
            --shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
            --radius-xl: 24px;
            --radius-lg: 18px;
            --radius-md: 14px;
        }

        html, body, [class*="css"] {
            color: var(--text);
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(37,99,235,0.08), transparent 22%),
                linear-gradient(180deg, #f4f8fd 0%, var(--bg) 100%);
            color: var(--text);
        }

        .main .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #111c34 100%);
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        [data-testid="stSidebar"] > div:first-child {
            background: transparent;
        }

        [data-testid="stSidebar"] * {
            color: #e5eefc !important;
        }

        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] .stTextInput label,
        [data-testid="stSidebar"] .stNumberInput label,
        [data-testid="stSidebar"] .stDateInput label,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {
            color: #dbe7fb !important;
        }

        [data-testid="stSidebar"] .stSelectbox > div > div,
        [data-testid="stSidebar"] .stTextInput > div > div,
        [data-testid="stSidebar"] .stNumberInput > div > div {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 14px;
        }

        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] input {
            color: #ffffff !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--text) !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em;
        }

        h1 {
            font-size: 3rem !important;
            line-height: 1.05 !important;
            margin-bottom: 0.4rem !important;
        }

        h2 {
            font-size: 2rem !important;
            margin-top: 0.2rem !important;
            margin-bottom: 0.8rem !important;
        }

        h3 {
            font-size: 1.3rem !important;
        }

        p, li, label, div, span {
            color: var(--text);
        }

        .hero-card {
            background: linear-gradient(135deg, #0f172a 0%, #172554 52%, #1d4ed8 100%);
            border-radius: 28px;
            padding: 2rem 2rem 1.6rem 2rem;
            color: white !important;
            box-shadow: 0 24px 50px rgba(15, 23, 42, 0.18);
            margin-bottom: 1.2rem;
            border: 1px solid rgba(255,255,255,0.06);
        }

        .hero-card h1,
        .hero-card h2,
        .hero-card h3,
        .hero-card p,
        .hero-card span {
            color: white !important;
        }

        .glass-card {
            background: rgba(255,255,255,0.75);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(216,228,243,0.8);
            border-radius: 22px;
            padding: 1.2rem 1.2rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }

        .section-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 1.35rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }

        .metric-chip {
            background: linear-gradient(180deg, #ffffff 0%, #f6faff 100%);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 1rem;
            box-shadow: var(--shadow);
        }

        .stMetric {
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%) !important;
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 1rem !important;
            box-shadow: var(--shadow);
        }

        .stMetric label,
        .stMetric div {
            color: var(--text) !important;
        }

        .stButton > button {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-2) 100%);
            color: white !important;
            border: none !important;
            border-radius: 14px !important;
            padding: 0.82rem 1.15rem !important;
            font-weight: 700 !important;
            box-shadow: 0 12px 24px rgba(37, 99, 235, 0.22);
            transition: 0.18s ease-in-out;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 18px 30px rgba(37, 99, 235, 0.28);
        }

        .stButton > button:focus {
            box-shadow: 0 0 0 0.2rem rgba(37, 99, 235, 0.18) !important;
        }

        .stNumberInput input,
        .stTextInput input,
        .stTextArea textarea,
        .stDateInput input {
            background: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cddbeb !important;
            border-radius: 14px !important;
            padding: 0.65rem 0.8rem !important;
        }

        .stSelectbox div[data-baseweb="select"] > div {
            background: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cddbeb !important;
            border-radius: 14px !important;
        }

        .stMultiSelect div[data-baseweb="select"] > div {
            background: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #cddbeb !important;
            border-radius: 14px !important;
        }

        .stNumberInput input:focus,
        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stDateInput input:focus {
            border: 1px solid var(--primary) !important;
            box-shadow: 0 0 0 0.2rem rgba(37, 99, 235, 0.15) !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.35rem;
            margin-bottom: 1rem;
            background: rgba(255,255,255,0.65);
            border: 1px solid var(--border);
            padding: 0.4rem;
            border-radius: 16px;
        }

        .stTabs [data-baseweb="tab"] {
            height: auto;
            white-space: nowrap;
            background: transparent;
            border-radius: 12px;
            padding: 0.7rem 1rem;
            color: #334155 !important;
            font-weight: 700;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #e0efff 0%, #eef7ff 100%) !important;
            color: #0f172a !important;
            border: 1px solid #bfdbfe !important;
        }

        .stDataFrame, div[data-testid="stTable"] {
            background: white;
            border-radius: 18px;
            border: 1px solid var(--border);
            overflow: hidden;
        }

        [data-testid="stInfo"],
        [data-testid="stSuccess"],
        [data-testid="stWarning"],
        [data-testid="stError"] {
            border-radius: 16px;
            border: none;
            padding: 0.9rem 1rem;
        }

        [data-testid="stInfo"] {
            background: #e8f2ff;
            color: #1d4ed8 !important;
        }

        [data-testid="stSuccess"] {
            background: #ecfdf3;
            color: #166534 !important;
        }

        [data-testid="stWarning"] {
            background: #fff7ed;
            color: #9a3412 !important;
        }

        [data-testid="stError"] {
            background: #fef2f2;
            color: #b91c1c !important;
        }

        .stExpander {
            border: 1px solid var(--border) !important;
            border-radius: 18px !important;
            background: #ffffff !important;
            box-shadow: var(--shadow);
        }

        .stCheckbox label {
            font-weight: 600;
        }

        hr {
            border-color: #dbe8f6;
        }

        .muted {
            color: var(--muted) !important;
        }

        .small-gap {
            margin-top: 0.4rem;
            margin-bottom: 0.6rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if "study_tasks" not in st.session_state:
    st.session_state.study_tasks = {subject: False for subject in STUDY_SUBJECTS}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "data_store" not in st.session_state:
    st.session_state.data_store = load_data()

store = st.session_state.data_store
Hoje = date.today()
today_diario = [item for item in store["diario"] if item["data"].date() == Hoje]
total_calorias_hoje = sum(item["calorias"] for item in today_diario)

with st.sidebar:
    st.markdown("## Navegação")
    st.markdown(
        '<p class="muted">Selecione o módulo desejado para calcular resultados, gerir o diário ou acessar o assistente.</p>',
        unsafe_allow_html=True,
    )
    page = st.selectbox(
        "Menu principal",
        [
            "Home",
            "Calculadoras",
            "Dietas",
            "Diário Alimentar",
            "Análise de Dados",
            "Assistente IA",
            "Estudos",
            "Sobre",
        ],
    )

    st.markdown("---")
    st.markdown("### Resumo rápido")
    st.markdown(f"**Calorias hoje:** {total_calorias_hoje:.0f} kcal")
    st.markdown(f"**Alimentos cadastrados:** {len(store['alimentos_favoritos'])}")
    st.markdown(f"**Dietas salvas:** {len(store['dietas'])}")
    st.markdown(f"**Histórico:** {len(store['historico'])}")


if page == "Home":
    st.markdown(
        """
        <div class="hero-card">
            <h1>Sistema de Auxiliar em Nutrição</h1>
            <p>Um painel moderno para cálculos, dietas, diário alimentar, análise de dados e apoio aos estudos.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cálculos realizados", len(store["historico"]))
    col2.metric("Alimentos cadastrados", len(store["alimentos_favoritos"]))
    col3.metric("Registros no diário", len(store["diario"]))
    col4.metric("Calorias hoje", f"{total_calorias_hoje:.0f} kcal")

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("O que você pode fazer")
    st.write(
        "Use as calculadoras para interpretar índices, crie metas calóricas, monte dietas, registre refeições e acompanhe a evolução dos dados em um só lugar."
    )
    st.write(
        "- **IMC**: avalia a relação entre peso e altura.\n"
        "- **TMB/TDEE**: calcula gasto energético e manutenção.\n"
        "- **Meta Calórica**: ajusta ingestão diária conforme objetivo.\n"
        "- **Macronutrientes**: converte calorias em gramas.\n"
        "- **Banco de Alimentos**: personaliza sua base.\n"
        "- **Dietas**: cria planos de refeições salvos."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("Registros de hoje")
    if today_diario:
        df_diario = pd.DataFrame(today_diario)
        df_diario_display = df_diario[["descricao", "refeicao", "calorias", "data"]].copy()
        df_diario_display["data"] = df_diario_display["data"].dt.strftime("%d/%m/%Y")
        df_diario_display.columns = ["Descrição", "Refeição", "Calorias", "Data"]
        st.dataframe(df_diario_display, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro no diário para hoje. Registre uma refeição na aba Diário Alimentar.")
    st.markdown("</div>", unsafe_allow_html=True)


elif page == "Calculadoras":
    st.markdown(
        """
        <div class="hero-card">
            <h1>Calculadoras de Nutrição</h1>
            <p>Faça cálculos rápidos com interface limpa, contraste forte e resultado visual melhor.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["IMC", "TMB & TDEE", "Meta Calórica", "Macronutrientes", "Banco de Alimentos"]
    )

    with tab1:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.header("Calculadora de IMC")
        col1, col2 = st.columns(2)
        peso = col1.number_input("Peso (kg)", min_value=0.0, step=0.1, key="peso_imc")
        altura = col2.number_input("Altura (m)", min_value=0.0, step=0.01, key="altura_imc")

        if st.button("Calcular IMC", key="btn_imc"):
            if peso > 0 and altura > 0:
                imc = peso / altura**2
                if imc < 18.5:
                    categoria = "Abaixo do peso"
                elif imc < 25:
                    categoria = "Peso normal"
                elif imc < 30:
                    categoria = "Sobrepeso"
                else:
                    categoria = "Obesidade"

                st.success(f"Seu IMC: {imc:.2f} — {categoria}")
                add_historico(
                    {
                        "tipo": "IMC",
                        "descricao": f"IMC = {imc:.2f}",
                        "valor": imc,
                        "categoria": categoria,
                        "data": datetime.now(),
                    }
                )
            else:
                st.error("Informe peso e altura válidos.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.header("Calculadora de TMB e TDEE")
        col1, col2, col3 = st.columns(3)
        peso_tmb = col1.number_input("Peso (kg)", min_value=0.0, step=0.1, key="peso_tmb")
        altura_tmb = col2.number_input("Altura (cm)", min_value=0.0, step=1.0, key="altura_tmb")
        idade = col3.number_input("Idade (anos)", min_value=0, step=1, key="idade_tmb")

        col1, col2 = st.columns(2)
        genero = col1.selectbox("Gênero", ["Masculino", "Feminino"], key="genero_tmb")
        atividade = col2.selectbox(
            "Nível de atividade",
            ["Sedentário", "Levemente ativo", "Moderadamente ativo", "Muito ativo", "Atleta"],
            key="atividade_tmb",
        )

        if st.button("Calcular TMB e TDEE", key="btn_tmb"):
            if peso_tmb > 0 and altura_tmb > 0 and idade > 0:
                if genero == "Masculino":
                    tmb = 10 * peso_tmb + 6.25 * altura_tmb - 5 * idade + 5
                else:
                    tmb = 10 * peso_tmb + 6.25 * altura_tmb - 5 * idade - 161

                fatores = {
                    "Sedentário": 1.2,
                    "Levemente ativo": 1.375,
                    "Moderadamente ativo": 1.55,
                    "Muito ativo": 1.725,
                    "Atleta": 1.9,
                }
                tdee = tmb * fatores[atividade]

                c1, c2 = st.columns(2)
                c1.metric("TMB", f"{tmb:.0f} kcal/dia")
                c2.metric("TDEE", f"{tdee:.0f} kcal/dia")
                st.write(
                    f"Manutenção: **{tdee:.0f} kcal** | Perda: **{tdee * 0.8:.0f} kcal** | Ganho: **{tdee * 1.1:.0f} kcal**"
                )

                add_historico(
                    {
                        "tipo": "TMB/TDEE",
                        "descricao": f"TMB={tmb:.0f}, TDEE={tdee:.0f}",
                        "tmb": tmb,
                        "tdee": tdee,
                        "data": datetime.now(),
                    }
                )
            else:
                st.error("Preencha todos os campos corretamente.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.header("Meta Calórica Recomendada")

        col1, col2, col3 = st.columns(3)
        peso_meta = col1.number_input("Peso (kg)", min_value=0.0, step=0.1, key="peso_meta")
        altura_meta = col2.number_input("Altura (cm)", min_value=0.0, step=1.0, key="altura_meta")
        idade_meta = col3.number_input("Idade (anos)", min_value=0, step=1, key="idade_meta")

        col1, col2 = st.columns(2)
        genero_meta = col1.selectbox("Gênero", ["Masculino", "Feminino"], key="genero_meta")
        atividade_meta = col2.selectbox(
            "Nível de atividade",
            ["Sedentário", "Levemente ativo", "Moderadamente ativo", "Muito ativo", "Atleta"],
            key="atividade_meta",
        )

        objetivo_meta = st.selectbox(
            "Objetivo",
            ["Manutenção", "Déficit leve (-10%)", "Déficit moderado (-15%)", "Ganho leve (+10%)"],
            key="objetivo_meta",
        )

        if st.button("Calcular meta calórica", key="btn_meta_calorica"):
            if peso_meta > 0 and altura_meta > 0 and idade_meta > 0:
                if genero_meta == "Masculino":
                    tmb_meta = 10 * peso_meta + 6.25 * altura_meta - 5 * idade_meta + 5
                else:
                    tmb_meta = 10 * peso_meta + 6.25 * altura_meta - 5 * idade_meta - 161

                fatores = {
                    "Sedentário": 1.2,
                    "Levemente ativo": 1.375,
                    "Moderadamente ativo": 1.55,
                    "Muito ativo": 1.725,
                    "Atleta": 1.9,
                }
                tdee_meta = tmb_meta * fatores[atividade_meta]

                ajustes = {
                    "Manutenção": 1.0,
                    "Déficit leve (-10%)": 0.90,
                    "Déficit moderado (-15%)": 0.85,
                    "Ganho leve (+10%)": 1.10,
                }
                meta_calorica = tdee_meta * ajustes[objetivo_meta]

                c1, c2, c3 = st.columns(3)
                c1.metric("TMB estimada", f"{tmb_meta:.0f} kcal/dia")
                c2.metric("TDEE estimado", f"{tdee_meta:.0f} kcal/dia")
                c3.metric("Meta diária", f"{meta_calorica:.0f} kcal")

                st.success(
                    f"Para seu perfil, sua necessidade energética estimada é de {tdee_meta:.0f} kcal/dia. "
                    f"Com o objetivo selecionado, a recomendação fica em cerca de {meta_calorica:.0f} kcal/dia."
                )

                add_historico(
                    {
                        "tipo": "Meta Calórica",
                        "descricao": f"Meta {objetivo_meta}: {meta_calorica:.0f} kcal",
                        "tmb": tmb_meta,
                        "tdee": tdee_meta,
                        "meta_calorica": meta_calorica,
                        "data": datetime.now(),
                    }
                )
            else:
                st.error("Preencha peso, altura e idade corretamente.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab4:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.header("Calculadora de Macronutrientes")
        calorias_diarias = st.number_input("Calorias diárias", min_value=0, step=50, key="calorias_macros")
        pct_proteina = st.slider("Proteína (%)", 10, 40, 30, key="pct_proteina")
        pct_carbs = st.slider("Carboidratos (%)", 30, 60, 40, key="pct_carbs")
        pct_gordura = st.slider("Gordura (%)", 20, 40, 30, key="pct_gordura")

        if st.button("Calcular Macronutrientes", key="btn_macros"):
            if calorias_diarias > 0 and pct_proteina + pct_carbs + pct_gordura == 100:
                proteina_kcal = calorias_diarias * pct_proteina / 100
                carbs_kcal = calorias_diarias * pct_carbs / 100
                gordura_kcal = calorias_diarias * pct_gordura / 100

                proteina_g = proteina_kcal / 4
                carbs_g = carbs_kcal / 4
                gordura_g = gordura_kcal / 9

                c1, c2, c3 = st.columns(3)
                c1.metric("Proteína", f"{proteina_g:.0f} g")
                c2.metric("Carboidratos", f"{carbs_g:.0f} g")
                c3.metric("Gordura", f"{gordura_g:.0f} g")

                fig = px.pie(
                    names=["Proteína", "Carboidratos", "Gordura"],
                    values=[proteina_kcal, carbs_kcal, gordura_kcal],
                    title="Distribuição de Macronutrientes",
                )
                st.plotly_chart(fig, use_container_width=True)

                add_historico(
                    {
                        "tipo": "Macronutrientes",
                        "descricao": f"{pct_proteina}% P, {pct_carbs}% C, {pct_gordura}% G",
                        "calorias": calorias_diarias,
                        "data": datetime.now(),
                    }
                )
            elif calorias_diarias > 0:
                st.error("A soma dos percentuais deve ser 100%.")
            else:
                st.error("Informe as calorias diárias.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab5:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.header("Banco de Alimentos")

        search = st.text_input("Buscar alimento", key="search_food")
        alimentos = store["alimentos_favoritos"]

        filtrados = (
            {nome: kcal for nome, kcal in alimentos.items() if search.lower() in nome.lower()}
            if search
            else alimentos
        )

        if filtrados:
            df_alimentos = pd.DataFrame(
                list(filtrados.items()), columns=["Alimento", "Calorias"]
            ).sort_values("Calorias", ascending=False)
            st.dataframe(df_alimentos, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum alimento encontrado.")

        with st.expander("Adicionar ou atualizar alimento"):
            col1, col2 = st.columns([3, 1])
            nome_alimento = col1.text_input("Nome do alimento", key="novo_alimento")
            calorias_alimento = col2.number_input(
                "Calorias por porção", min_value=0.0, step=1.0, key="calorias_alimento"
            )
            if st.button("Salvar alimento", key="save_food"):
                if nome_alimento and calorias_alimento > 0:
                    add_alimento(nome_alimento, calorias_alimento)
                    st.success(
                        f"Alimento '{nome_alimento}' cadastrado com {calorias_alimento:.0f} kcal."
                    )
                else:
                    st.error("Informe nome e calorias válidos.")

        if st.button("Excluir alimentos exibidos", key="delete_foods"):
            delete_alimentos(list(filtrados.keys()))
            st.success("Alimentos exibidos excluídos.")
        st.markdown("</div>", unsafe_allow_html=True)


elif page == "Dietas":
    st.markdown(
        """
        <div class="hero-card">
            <h1>Minhas Dietas</h1>
            <p>Monte planos prontos, organize refeições e salve dietas de forma muito mais visual.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    with st.expander("Montar nova dieta", expanded=True):
        nome_dieta = st.text_input("Nome da dieta", key="nome_dieta")
        objetivo_dieta = st.selectbox(
            "Objetivo da dieta",
            ["Manutenção", "Emagrecimento", "Hipertrofia", "Saúde geral"],
            key="objetivo_dieta",
        )
        descricao_dieta = st.text_area(
            "Instruções ou motivação",
            placeholder="Descreva o propósito, dicas ou como seguir essa dieta.",
            key="descricao_dieta",
            height=120,
        )

        alimentos_selecionados = st.multiselect(
            "Escolha os alimentos que farão parte da dieta",
            list(store["alimentos_favoritos"].keys()),
            key="alimentos_dieta",
        )

        porcoes = {}
        if alimentos_selecionados:
            st.write("Defina quantas porções de cada alimento você inclui na dieta:")
            for alimento in alimentos_selecionados:
                porcoes[alimento] = st.number_input(
                    f"{alimento} (porções)",
                    min_value=0.1,
                    step=0.1,
                    value=1.0,
                    key=f"porcao_{alimento}",
                )

        total_calorias_dieta = (
            sum(
                store["alimentos_favoritos"][alimento] * porcoes[alimento]
                for alimento in porcoes
            )
            if porcoes
            else 0.0
        )

        if st.button("Salvar dieta", key="btn_salvar_dieta"):
            if not nome_dieta.strip():
                st.error("Dê um nome à sua dieta.")
            elif not alimentos_selecionados:
                st.error("Selecione pelo menos um alimento.")
            else:
                itens_dieta = [
                    {
                        "alimento": alimento,
                        "porcoes": porcoes[alimento],
                        "calorias": store["alimentos_favoritos"][alimento] * porcoes[alimento],
                    }
                    for alimento in alimentos_selecionados
                ]
                add_dieta(
                    {
                        "nome": nome_dieta.strip(),
                        "objetivo": objetivo_dieta,
                        "descricao": descricao_dieta.strip(),
                        "itens": itens_dieta,
                        "total_calorias": total_calorias_dieta,
                        "data": datetime.now(),
                    }
                )
                st.success("Dieta salva com sucesso.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("Dietas salvas")
    dietas = sorted(store["dietas"], key=lambda x: x["data"], reverse=True)

    if dietas:
        for dieta in dietas:
            with st.expander(
                f"{dieta['nome']} — {dieta['objetivo']} ({dieta['total_calorias']:.0f} kcal)"
            ):
                st.write(f"**Motivação:** {dieta['descricao'] or 'Sem descrição'}")
                st.write(f"**Criada em:** {dieta['data'].strftime('%d/%m/%Y %H:%M')}")
                st.write("**Alimentos da dieta:**")

                df_dieta = pd.DataFrame(dieta["itens"])
                df_dieta["calorias"] = df_dieta["calorias"].map(lambda x: f"{x:.0f}")
                df_dieta.columns = ["Alimento", "Porções", "Calorias"]
                st.dataframe(df_dieta, use_container_width=True, hide_index=True)
    else:
        st.info("Ainda não há dietas salvas. Crie uma dieta para começar.")
    st.markdown("</div>", unsafe_allow_html=True)


elif page == "Diário Alimentar":
    st.markdown(
        """
        <div class="hero-card">
            <h1>Diário Alimentar</h1>
            <p>Registre refeições, acompanhe calorias e mantenha seu histórico organizado.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    data_selecionada = col1.date_input("Data", Hoje)
    refeicao = col2.selectbox(
        "Refeição", ["Café da Manhã", "Almoço", "Lanche", "Jantar"], key="refeicao"
    )
    alimento_selecionado = col3.selectbox(
        "Alimento", list(store["alimentos_favoritos"].keys()), key="alimento_diario"
    )
    quantidade = st.number_input(
        "Quantidade (porções)", min_value=0.1, step=0.1, key="quantidade_diario"
    )

    if st.button("Adicionar ao diário", key="btn_diario"):
        calorias = store["alimentos_favoritos"][alimento_selecionado] * quantidade
        add_diario(
            {
                "descricao": f"{quantidade:.1f}x {alimento_selecionado}",
                "alimento": alimento_selecionado,
                "quantidade": quantidade,
                "calorias": calorias,
                "refeicao": refeicao,
                "data": datetime.combine(data_selecionada, datetime.min.time()),
            }
        )
        st.success(f"Adicionado ao diário: {calorias:.0f} kcal")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("Registros do dia")
    diario_dia = [item for item in store["diario"] if item["data"].date() == data_selecionada]

    if diario_dia:
        df_diario = pd.DataFrame(diario_dia)
        df_diario_display = df_diario[["descricao", "refeicao", "calorias", "data"]].copy()
        df_diario_display["data"] = df_diario_display["data"].dt.strftime("%d/%m/%Y")
        df_diario_display.columns = ["Descrição", "Refeição", "Calorias", "Data"]
        st.dataframe(df_diario_display, use_container_width=True, hide_index=True)
        st.info(f"Total de calorias no dia: {df_diario['calorias'].sum():.0f} kcal")
    else:
        st.info("Nenhum registro para esta data.")
    st.markdown("</div>", unsafe_allow_html=True)


elif page == "Análise de Dados":
    st.markdown(
        """
        <div class="hero-card">
            <h1>Análise de Dados</h1>
            <p>Veja histórico, consumo diário e os alimentos mais calóricos com layout mais limpo.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    historico = store["historico"]
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)

    if historico:
        st.subheader("Histórico completo")
        df_historico = pd.DataFrame(historico)
        df_historico["data"] = pd.to_datetime(df_historico["data"])
        st.dataframe(
            df_historico.sort_values(by="data", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

        diario = [item for item in historico if item.get("tipo") == "Diário"]
        if diario:
            df_diario = pd.DataFrame(diario)
            df_diario["data"] = pd.to_datetime(df_diario["data"])
            resumo = df_diario.groupby(df_diario["data"].dt.date)["calorias"].sum().reset_index()
            resumo.columns = ["Data", "Calorias"]
            st.subheader("Consumo diário de calorias")
            st.line_chart(resumo.set_index("Data"))

        st.subheader("Top 10 alimentos por calorias")
        top_alimentos = pd.DataFrame(
            list(store["alimentos_favoritos"].items()),
            columns=["Alimento", "Calorias"],
        ).sort_values("Calorias", ascending=False).head(10)
        st.bar_chart(top_alimentos.set_index("Alimento"))
    else:
        st.warning("Nenhum registro encontrado. Use as calculadoras e o diário alimentar primeiro.")

    st.markdown("</div>", unsafe_allow_html=True)


elif page == "Assistente IA":
    st.markdown(
        """
        <div class="hero-card">
            <h1>Assistente IA</h1>
            <p>Tire dúvidas sobre nutrição, estudos, rotina alimentar e graduação em um painel mais elegante.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.write(
        "Use uma chave de API OpenAI para conectar o aplicativo a um modelo de linguagem."
    )

    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="Cole sua chave de API aqui",
        key="openai_api_key",
    )

    if not api_key:
        api_key = get_openai_api_key()

    model = st.selectbox(
        "Modelo",
        ["gpt-3.5-turbo", "gpt-4o-mini"],
        index=0,
        key="openai_model",
    )

    question = st.text_area(
        "Pergunta",
        placeholder="Pergunte algo sobre nutrição, estudo, rotina, matérias ou dúvidas do curso.",
        height=150,
        key="openai_question",
    )

    if st.button("Enviar para a IA", key="openai_submit"):
        if not api_key:
            st.error("Informe sua chave de API OpenAI ou configure OPENAI_API_KEY nos secrets.")
        elif not question.strip():
            st.error("Digite uma pergunta para enviar.")
        else:
            with st.spinner("Consultando a IA..."):
                try:
                    answer = ask_openai(
                        api_key,
                        question,
                        history=st.session_state.chat_history,
                        model=model,
                    )
                    st.session_state.chat_history.append({"role": "user", "content": question})
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Erro ao consultar a IA: {e}")

    if st.session_state.chat_history:
        st.subheader("Histórico de conversas")
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"**Você:** {message['content']}")
            else:
                st.markdown(f"**IA:** {message['content']}")

    st.info(
        "ChatGPT Plus no navegador não fornece automaticamente uma chave de API. Para usar no app, é preciso configurar a API separadamente."
    )
    st.markdown("</div>", unsafe_allow_html=True)


elif page == "Estudos":
    st.markdown(
        """
        <div class="hero-card">
            <h1>Estudos para Nutrição</h1>
            <p>Organize matérias, acompanhe revisão e mantenha a rotina de estudo mais clara.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("Matérias importantes para Nutrição")
    col1, col2 = st.columns(2)
    for index, subject in enumerate(STUDY_SUBJECTS):
        coluna = col1 if index % 2 == 0 else col2
        coluna.write(f"- **{subject}**")

    st.subheader("Dicas rápidas de estudo")
    for tip in STUDY_TIPS:
        st.write(f"- {tip}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("Lista de tarefas de revisão")
    completed = 0
    for subject in STUDY_SUBJECTS:
        key = f"study_{subject}"
        st.session_state.study_tasks[subject] = st.checkbox(
            subject,
            value=st.session_state.study_tasks[subject],
            key=key,
        )
        if st.session_state.study_tasks[subject]:
            completed += 1

    st.info(f"Você concluiu {completed} de {len(STUDY_SUBJECTS)} matérias de revisão.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("Plano semanal sugerido")
    st.write(
        "Organize sua semana com blocos de estudo de 45 a 60 minutos, alternando entre teoria, prática e revisão."
    )
    st.write(
        "Foque em: 1) Anatomia e Bioquímica, 2) Nutrição Clínica e Saúde Coletiva, 3) Tecnologia de Alimentos e Educação em Saúde."
    )
    st.write(
        "Use o diário alimentar como fonte de estudo: relacione registros de refeições com conceitos de dietética, macronutrientes e orientação nutricional."
    )
    st.markdown("</div>", unsafe_allow_html=True)


elif page == "Sobre":
    st.markdown(
        f"""
        <div class="hero-card">
            <h1>Sobre o Sistema</h1>
            <p>Aplicativo para apoio ao estudo de nutrição, com cálculo de índices, controle de alimentos, diário alimentar e análise visual.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown(
        f"""
        ## Sistema de Auxiliar em Nutrição

        Aplicativo para apoio ao estudo de nutrição, com cálculo de índices, controle de alimentos e diário alimentar.

        ### Funcionalidades
        - Calculadora de IMC
        - Cálculo de TMB e TDEE
        - Meta Calórica
        - Distribuição de macronutrientes
        - Banco de alimentos com pesquisa e edição
        - Diário alimentar com registro por refeição
        - Análise de dados com gráficos e histórico
        - Área de dietas salvas
        - Assistente IA

        **Última atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """
    )
    st.markdown("</div>", unsafe_allow_html=True)
