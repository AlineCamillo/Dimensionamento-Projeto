import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="FullEnergy | Dimensionamento LiFePO4", page_icon="🔋", layout="wide")

V_NOM, V_MAX, V_MIN = 3.2, 3.55, 2.6
SERIE = {12: 4, 24: 8, 36: 12, 48: 16, 60: 20, 72: 24}

CELULAS = [
    ("Great Power", "IFR40135", 20, 60, 60, 0.55),
    ("Gotion", "IFP20100140A", 27, 108, 135, 0.596),
    ("King Power", "IFP36130141AE", 50, 400, 400, 1.23),
    ("CALB", "L148F88A", 88, 88, 176, 1.84),
    ("REPT", "CB56-104Ah", 104, 208, 520, 1.92),
    ("Gotion", "105Ah", 105, 105, 210, 2.0),
    ("CALB", "L173F163", 163, 163, 326, 3.19),
    ("EVE", "LF230", 230, 230, 460, 4.11),
    ("XDLE", "CBA54173204", 230, 230, 690, 4.10),
    ("EVE", "LF280K", 280, 280, 560, 5.49),
]
CELULAS = [
    dict(fabricante=f, modelo=m, ah=ah, cont=cont, pico=pico, peso=peso)
    for f, m, ah, cont, pico, peso in CELULAS
]

CSS = """
<style>
[data-testid="stAppViewContainer"] {background-color:#f4f6f8;}
.block-container {padding-top:1.2rem; padding-bottom:3rem;}

.header-fe {
    background:linear-gradient(135deg,#050505 0%,#181818 60%,#2a2a2a 100%);
    padding:24px 30px;
    border-radius:18px;
    border-bottom:5px solid #FFD400;
    box-shadow:0px 6px 18px rgba(0,0,0,0.22);
    text-align:center;
    margin-bottom:18px;
}
.header-fe h1 {color:white; font-size:38px; margin:0; font-weight:900;}
.header-fe h2 {color:#FFD400; font-size:24px; margin-top:6px; margin-bottom:10px; font-weight:800;}
.header-fe p {color:#d8d8d8; font-size:15px; margin:0;}

.linha-amarela {
    height:3px;
    background:linear-gradient(90deg,#FFD400,#FFB000,#FFD400);
    border-radius:6px;
    margin:5px 0 20px 0;
}

.section-title {
    background:#111;
    color:white;
    padding:12px 18px;
    border-radius:12px;
    border-left:6px solid #FFD400;
    margin-top:26px;
    margin-bottom:18px;
    font-weight:800;
    font-size:20px;
}

div[data-testid="stMetric"], .result-card {
    background:white;
    border-radius:16px;
    padding:18px;
    border-left:5px solid #FFD400;
    box-shadow:0px 3px 10px rgba(0,0,0,0.08);
}
.result-card {min-height:220px;}
.alerta {
    background:#fff7d6;
    padding:16px;
    border-radius:14px;
    border-left:6px solid #FFD400;
    margin:18px 0 20px 0;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown("""
<div class="header-fe">
    <h1>FullEnergy</h1>
    <h2>Dimensionamento de Baterias LiFePO4</h2>
    <p>Pré-dimensionamento técnico com base na aplicação, autonomia, corrente e células disponíveis.</p>
</div>
<div class="linha-amarela"></div>
""", unsafe_allow_html=True)


def n(x, default=0.0):
    try:
        return default if pd.isna(x) else float(x)
    except Exception:
        return default


def secao(titulo):
    st.markdown(f'<div class="section-title">{titulo}</div>', unsafe_allow_html=True)


def card(titulo, linhas):
    html = f'<div class="result-card"><h3>{titulo}</h3>'
    for label, valor in linhas:
        html += f"<p><b>{label}:</b> {valor}</p>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def serie_por_tensao(v):
    return SERIE.get(int(v), max(1, round(v / V_NOM)))


def tabela_padrao(tipo):
    if tipo == "motor":
        return pd.DataFrame([{"Descrição": "Motor tração", "Tipo": "AC", "Potência": 3000, "Corrente (A)": 0, "Uso (%)": 100, "Eficiência (%)": 90}])
    return pd.DataFrame([{"Descrição": "Componente auxiliar", "Tipo": "DC", "Potência": 0, "Corrente (A)": 0, "Uso (%)": 100, "Eficiência (%)": 100}])


def potencia_linha(row, tensao):
    potencia = n(row.get("Potência", 0))
    corrente = n(row.get("Corrente (A)", 0))
    uso = n(row.get("Uso (%)", 100), 100) / 100
    eficiencia = n(row.get("Eficiência (%)", 90), 90) / 100
    tipo = row.get("Tipo", "DC")

    if potencia <= 0 and corrente <= 0:
        return 0

    if corrente > 0 and tensao > 0:
        potencia_dc = corrente * tensao
    else:
        potencia_dc = potencia / eficiencia if tipo == "AC" and eficiencia > 0 else potencia

    return potencia_dc * uso


def editor(df):
    return st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Tipo": st.column_config.SelectboxColumn("Tipo", options=["AC", "DC"]),
            "Uso (%)": st.column_config.NumberColumn("Uso (%)", min_value=0, max_value=100),
            "Eficiência (%)": st.column_config.NumberColumn("Eficiência (%)", min_value=1, max_value=100),
        }
    )


def calcular_opcoes(tensao, autonomia, fator, motores, auxiliares):
    potencia_total = sum(potencia_linha(r, tensao) for _, r in motores.iterrows())
    potencia_total += sum(potencia_linha(r, tensao) for _, r in auxiliares.iterrows())

    i_max = potencia_total / tensao if tensao else 0
    i_media = i_max * fator / 100
    ah_necessario = i_media * autonomia
    kwh_necessario = potencia_total * (fator / 100) * autonomia / 1000

    serie = serie_por_tensao(tensao)
    v_nom, v_max, v_min = serie * V_NOM, serie * V_MAX, serie * V_MIN

    opcoes = []
    for c in CELULAS:
        p_ah = max(1, math.ceil(ah_necessario / c["ah"])) if c["ah"] else 1
        p_corrente = max(1, math.ceil(i_max / c["cont"])) if c["cont"] else 1
        paralelo = max(p_ah, p_corrente)

        cap = c["ah"] * paralelo
        cont_pack = c["cont"] * paralelo
        pico_pack = c["pico"] * paralelo

        opcoes.append({
            **c,
            "serie": serie,
            "paralelo": paralelo,
            "total_celulas": serie * paralelo,
            "capacidade_pack": cap,
            "energia_pack": v_nom * cap / 1000,
            "cont_pack": cont_pack,
            "pico_pack": pico_pack,
            "peso_pack": c["peso"] * serie * paralelo,
            "autonomia": cap / i_media if i_media else 0,
            "c_rate_cont": c["cont"] / c["ah"] if c["ah"] else 0,
            "c_rate_pico": c["pico"] / c["ah"] if c["ah"] else 0,
            "c_rate_uso": i_max / cap if cap else 0,
        })

    resumo = dict(
        potencia_total=potencia_total,
        i_max=i_max,
        i_media=i_media,
        ah_necessario=ah_necessario,
        kwh_necessario=kwh_necessario,
        serie=serie,
        v_nom=v_nom,
        v_max=v_max,
        v_min=v_min,
    )
    return resumo, opcoes


secao("1. Dados do projeto")

tipo = st.radio("Este projeto é retrofit?", ["Sim, é retrofit", "Não, é projeto novo"], horizontal=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    if tipo == "Sim, é retrofit":
        tensao = st.number_input("Tensão da bateria de chumbo atual (V)", min_value=1, value=48)
        st.number_input("Capacidade da bateria de chumbo atual (Ah)", min_value=0, value=105)
    else:
        tensao = st.number_input("Tensão nominal do sistema (V)", min_value=1, value=48)
with c2:
    autonomia = st.number_input("Autonomia desejada (horas)", min_value=0.1, value=4.0, step=0.5)
with c3:
    st.number_input("Tempo disponível para recarga (horas)", min_value=0.0, value=4.0, step=0.5)
with c4:
    fator = st.number_input("Fator médio real de consumo (%)", min_value=1, max_value=100, value=40, step=5)

with st.expander("Faixa de operação do controlador (opcional)"):
    cx1, cx2 = st.columns(2)
    with cx1:
        controlador_min = st.number_input("Tensão mínima do controlador (V)", min_value=0.0, value=0.0)
    with cx2:
        controlador_max = st.number_input("Tensão máxima do controlador (V)", min_value=0.0, value=0.0)

secao("2. Motores")
motores = editor(tabela_padrao("motor"))

secao("3. Componentes auxiliares")
auxiliares = editor(tabela_padrao("aux"))

secao("4. Seleção da célula")
modo = st.selectbox("Seleção de célula", ["Automática"] + [f"{c['fabricante']} {c['modelo']} - {c['ah']}Ah" for c in CELULAS])

if st.button("Dimensionar bateria", type="primary"):
    resumo, opcoes = calcular_opcoes(tensao, autonomia, fator, motores, auxiliares)

    if resumo["i_max"] <= 0:
        st.error("Informe pelo menos uma potência ou corrente nos motores/componentes.")
        st.stop()

    if modo == "Automática":
        validas = [o for o in opcoes if o["cont_pack"] >= resumo["i_max"] and o["capacidade_pack"] >= resumo["ah_necessario"]]
        if not validas:
            st.error("Nenhuma célula atende aos critérios de corrente e autonomia informados.")
            st.stop()
        escolhida = sorted(validas, key=lambda x: (x["paralelo"], x["peso_pack"], x["capacidade_pack"]))[0]
    else:
        nome = modo.split(" - ")[0]
        escolhida = next(o for o in opcoes if f"{o['fabricante']} {o['modelo']}" in nome)

    st.markdown('<div class="alerta"><b>Observação técnica:</b> este é um pré-dimensionamento. A autonomia utiliza o fator médio real de consumo. Os limites de corrente são baseados nos dados cadastrados das células.</div>', unsafe_allow_html=True)

    secao("Resultado do dimensionamento")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("⚡ Potência DC máxima", f"{resumo['potencia_total']:,.0f} W".replace(",", "."))
    m2.metric("🔌 Corrente máxima", f"{resumo['i_max']:.1f} A")
    m3.metric("📉 Corrente média real", f"{resumo['i_media']:.1f} A")
    m4.metric("🔋 Capacidade necessária", f"{resumo['ah_necessario']:.1f} Ah")

    m5, m6 = st.columns(2)
    m5.metric("📊 Energia necessária", f"{resumo['kwh_necessario']:.2f} kWh")
    m6.metric("⚙️ Fator médio de consumo", f"{fator}%")

    secao("Bateria recomendada")
    r1, r2, r3 = st.columns(3)
    with r1:
        card("Configuração", [
            ("Configuração", f"{resumo['serie']}S{escolhida['paralelo']}P"),
            ("Quantidade total de células", escolhida["total_celulas"]),
            ("Tensão nominal", f"{resumo['v_nom']:.1f} V"),
            ("Tensão máxima FullEnergy", f"{resumo['v_max']:.1f} V"),
            ("Tensão mínima FullEnergy", f"{resumo['v_min']:.1f} V"),
        ])
    with r2:
        card("Célula", [
            ("Fabricante", escolhida["fabricante"]),
            ("Modelo", escolhida["modelo"]),
            ("Capacidade da célula", f"{escolhida['ah']:.0f} Ah"),
            ("Capacidade final do pack", f"{escolhida['capacidade_pack']:.0f} Ah"),
            ("Energia final", f"{escolhida['energia_pack']:.2f} kWh"),
        ])
    with r3:
        card("Características físicas", [
            ("Peso unitário da célula", f"{escolhida['peso']:.2f} kg"),
            ("Peso estimado das células", f"{escolhida['peso_pack']:.1f} kg"),
        ])

    secao("Capacidade de corrente")
    q1, q2, q3 = st.columns(3)
    with q1:
        card("C-rate", [
            ("C-rate contínuo da célula", f"{escolhida['c_rate_cont']:.2f}C"),
            ("C-rate pico da célula", f"{escolhida['c_rate_pico']:.2f}C"),
            ("C-rate utilizado pela aplicação", f"{escolhida['c_rate_uso']:.2f}C"),
        ])
    with q2:
        card("Célula", [
            ("Corrente contínua da célula", f"{escolhida['cont']:.0f} A"),
            ("Corrente pico da célula", f"{escolhida['pico']:.0f} A"),
        ])
    with q3:
        card("Pack", [
            ("Corrente contínua do pack", f"{escolhida['cont_pack']:.0f} A"),
            ("Corrente pico do pack", f"{escolhida['pico_pack']:.0f} A"),
        ])

    secao("Autonomia")
    a1, a2 = st.columns(2)
    a1.metric("⏱️ Autonomia estimada", f"{escolhida['autonomia']:.2f} h")
    a2.metric("🔋 Energia disponível", f"{escolhida['energia_pack']:.2f} kWh")

    if controlador_min > 0 and controlador_max > 0:
        if resumo["v_min"] >= controlador_min and resumo["v_max"] <= controlador_max:
            st.success("A faixa FullEnergy da bateria está dentro da faixa informada do controlador.")
        else:
            st.warning("A faixa FullEnergy da bateria pode não estar compatível com a faixa informada do controlador.")

    secao("Comparativo de células")
    tabela = pd.DataFrame([{
        "Célula": f"{o['fabricante']} {o['modelo']}",
        "Configuração": f"{resumo['serie']}S{o['paralelo']}P",
        "Ah final": o["capacidade_pack"],
        "kWh": round(o["energia_pack"], 2),
        "Contínua pack A": o["cont_pack"],
        "Pico pack A": o["pico_pack"],
        "C-rate utilizado": round(o["c_rate_uso"], 2),
        "Peso células kg": round(o["peso_pack"], 1),
        "Autonomia h": round(o["autonomia"], 2),
    } for o in opcoes])

    st.dataframe(tabela, use_container_width=True)
