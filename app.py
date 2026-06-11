import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="FullEnergy | Dimensionamento LiFePO4", page_icon="🔋", layout="wide")

V_NOM, V_MAX, V_MIN = 3.2, 3.55, 2.6
SERIE = {12: 4, 24: 8, 36: 12, 48: 16, 60: 20, 72: 24}
CELULAS_BASE = [
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
CELULAS = [dict(fabricante=f, modelo=m, ah=ah, cont=cont, pico=pico, peso=peso) for f, m, ah, cont, pico, peso in CELULAS_BASE]

CSS = """
<style>
[data-testid="stAppViewContainer"] {background-color:#f4f6f8;}
.block-container {padding-top:1.2rem; padding-bottom:3rem;}
.header-fe {background:linear-gradient(135deg,#050505 0%,#181818 60%,#2a2a2a 100%);padding:24px 30px;border-radius:18px;border-bottom:5px solid #FFD400;box-shadow:0px 6px 18px rgba(0,0,0,.22);text-align:center;margin-bottom:18px;}
.header-fe h1 {color:white;font-size:38px;margin:0;font-weight:900;}
.header-fe h2 {color:#FFD400;font-size:24px;margin-top:6px;margin-bottom:10px;font-weight:800;}
.header-fe p {color:#d8d8d8;font-size:15px;margin:0;}
.linha-amarela {height:3px;background:linear-gradient(90deg,#FFD400,#FFB000,#FFD400);border-radius:6px;margin:5px 0 20px 0;}
.section-title {background:#111;color:white;padding:12px 18px;border-radius:12px;border-left:6px solid #FFD400;margin-top:26px;margin-bottom:18px;font-weight:800;font-size:20px;}
div[data-testid="stMetric"], .result-card {background:white;border-radius:16px;padding:18px;border-left:5px solid #FFD400;box-shadow:0px 3px 10px rgba(0,0,0,.08);}
.result-card {min-height:220px;}
.alerta {background:#fff7d6;padding:16px;border-radius:14px;border-left:6px solid #FFD400;margin:18px 0 20px 0;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
st.markdown("""
<div class="header-fe">
    <h1>FullEnergy</h1>
    <h2>Dimensionamento de Baterias LiFePO4</h2>
    <p>Pré-dimensionamento técnico com base na aplicação, autonomia, corrente, retrofit e células disponíveis.</p>
</div><div class="linha-amarela"></div>
""", unsafe_allow_html=True)


def n(x, default=0.0):
    try:
        return default if pd.isna(x) else float(x)
    except Exception:
        return default


def fmt(v, casas=1, unidade=""):
    return f"{v:,.{casas}f}".replace(",", ".") + unidade


def secao(titulo):
    st.markdown(f'<div class="section-title">{titulo}</div>', unsafe_allow_html=True)


def card(titulo, linhas):
    itens = "".join(f"<p><b>{l}:</b> {v}</p>" for l, v in linhas)
    st.markdown(f'<div class="result-card"><h3>{titulo}</h3>{itens}</div>', unsafe_allow_html=True)


def serie_por_tensao(v):
    return SERIE.get(int(v), max(1, round(v / V_NOM)))


def tabela_padrao(tipo):
    dados = {"Descrição": "Motor tração", "Tipo": "AC", "Potência": 3000, "Corrente (A)": 0, "Uso (%)": 100, "Eficiência (%)": 90}
    if tipo == "aux":
        dados = {"Descrição": "Componente auxiliar", "Tipo": "DC", "Potência": 0, "Corrente (A)": 0, "Uso (%)": 100, "Eficiência (%)": 100}
    return pd.DataFrame([dados])


def editor(df):
    return st.data_editor(
        df, num_rows="dynamic", use_container_width=True,
        column_config={
            "Tipo": st.column_config.SelectboxColumn("Tipo", options=["AC", "DC"]),
            "Uso (%)": st.column_config.NumberColumn("Uso (%)", min_value=0, max_value=100),
            "Eficiência (%)": st.column_config.NumberColumn("Eficiência (%)", min_value=1, max_value=100),
        },
    )


def potencia_linha(row, tensao):
    potencia, corrente = n(row.get("Potência", 0)), n(row.get("Corrente (A)", 0))
    uso, eficiencia = n(row.get("Uso (%)", 100), 100) / 100, n(row.get("Eficiência (%)", 90), 90) / 100
    if potencia <= 0 and corrente <= 0:
        return 0
    potencia_dc = corrente * tensao if corrente > 0 and tensao > 0 else potencia
    if row.get("Tipo", "DC") == "AC" and corrente <= 0 and eficiencia > 0:
        potencia_dc = potencia / eficiencia
    return potencia_dc * uso


def calcular_retrofit(ah_chumbo, dod_chumbo, ef_chumbo, dod_lfp, ef_lfp):
    ah_real_chumbo = ah_chumbo * (dod_chumbo / 100) * (ef_chumbo / 100)
    ah_lfp_necessario = ah_real_chumbo / ((dod_lfp / 100) * (ef_lfp / 100))
    return ah_real_chumbo, ah_lfp_necessario


def calcular_opcoes(tensao, autonomia, fator, motores, auxiliares, ah_minimo_retrofit=0):
    potencia_total = sum(potencia_linha(r, tensao) for _, r in pd.concat([motores, auxiliares]).iterrows())
    i_max = potencia_total / tensao if tensao and potencia_total else 0
    i_media = i_max * fator / 100
    ah_por_consumo = i_media * autonomia
    ah_necessario = max(ah_por_consumo, ah_minimo_retrofit)
    serie = serie_por_tensao(tensao)
    v_nom, v_max, v_min = serie * V_NOM, serie * V_MAX, serie * V_MIN

    opcoes = []
    for c in CELULAS:
        p_ah = max(1, math.ceil(ah_necessario / c["ah"]))
        p_corrente = max(1, math.ceil(i_max / c["cont"])) if i_max else 1
        paralelo = max(p_ah, p_corrente)
        cap, cont_pack, pico_pack = c["ah"] * paralelo, c["cont"] * paralelo, c["pico"] * paralelo
        opcoes.append({
            **c, "serie": serie, "paralelo": paralelo, "total_celulas": serie * paralelo,
            "capacidade_pack": cap, "energia_pack": v_nom * cap / 1000,
            "cont_pack": cont_pack, "pico_pack": pico_pack, "peso_pack": c["peso"] * serie * paralelo,
            "autonomia": cap / i_media if i_media else 0,
            "c_rate_cont": c["cont"] / c["ah"], "c_rate_pico": c["pico"] / c["ah"],
            "c_rate_uso": i_max / cap if cap else 0,
        })

    return dict(
        potencia_total=potencia_total, i_max=i_max, i_media=i_media, ah_por_consumo=ah_por_consumo,
        ah_necessario=ah_necessario, kwh_necessario=(potencia_total * fator / 100 * autonomia / 1000),
        serie=serie, v_nom=v_nom, v_max=v_max, v_min=v_min,
    ), opcoes


secao("1. Dados do projeto")
tipo = st.radio("Este projeto é retrofit?", ["Sim, é retrofit", "Não, é projeto novo"], horizontal=True)
retrofit = tipo == "Sim, é retrofit"

c1, c2, c3, c4 = st.columns(4)
with c1:
    tensao = st.number_input("Tensão da bateria de chumbo atual (V)" if retrofit else "Tensão nominal do sistema (V)", min_value=1, value=48)
with c2:
    autonomia = st.number_input("Autonomia desejada (horas)", min_value=0.1, value=4.0, step=0.5)
with c3:
    st.number_input("Tempo disponível para recarga (horas)", min_value=0.0, value=4.0, step=0.5)
with c4:
    fator = st.number_input("Fator médio real de consumo (%)", min_value=1, max_value=100, value=40, step=5)

ah_minimo_retrofit = 0
retro = {}
if retrofit:
    secao("1.1 Análise retrofit chumbo x LiFePO4")
    r1, r2, r3, r4, r5 = st.columns(5)
    with r1:
        ah_chumbo = st.number_input("Capacidade chumbo atual (Ah)", min_value=1.0, value=220.0, step=5.0)
    with r2:
        dod_chumbo = st.number_input("DoD chumbo (%)", min_value=1.0, max_value=100.0, value=80.0, step=5.0)
    with r3:
        ef_chumbo = st.number_input("Eficiência chumbo (%)", min_value=1.0, max_value=100.0, value=70.0, step=5.0)
    with r4:
        dod_lfp = st.number_input("DoD LiFePO4 (%)", min_value=1.0, max_value=100.0, value=95.0, step=1.0)
    with r5:
        ef_lfp = st.number_input("Eficiência LiFePO4 (%)", min_value=1.0, max_value=100.0, value=95.0, step=1.0)
    ah_real_chumbo, ah_minimo_retrofit = calcular_retrofit(ah_chumbo, dod_chumbo, ef_chumbo, dod_lfp, ef_lfp)
    retro = dict(ah_chumbo=ah_chumbo, ah_real_chumbo=ah_real_chumbo, ah_lfp=ah_minimo_retrofit)

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
    resumo, opcoes = calcular_opcoes(tensao, autonomia, fator, motores, auxiliares, ah_minimo_retrofit)
    if resumo["i_max"] <= 0 and not retrofit:
        st.error("Informe pelo menos uma potência ou corrente nos motores/componentes.")
        st.stop()

    if modo == "Automática":
        validas = [o for o in opcoes if o["cont_pack"] >= resumo["i_max"] and o["capacidade_pack"] >= resumo["ah_necessario"]]
        if not validas:
            st.error("Nenhuma célula atende aos critérios informados.")
            st.stop()
        escolhida = sorted(validas, key=lambda x: (x["paralelo"], x["peso_pack"], x["capacidade_pack"]))[0]
    else:
        nome = modo.split(" - ")[0]
        escolhida = next(o for o in opcoes if f"{o['fabricante']} {o['modelo']}" in nome)

    st.markdown('<div class="alerta"><b>Observação técnica:</b> este é um pré-dimensionamento. Em retrofit, a capacidade mínima usa a equivalência chumbo x LiFePO4; a corrente é validada quando motores/componentes são informados.</div>', unsafe_allow_html=True)

    if retrofit:
        secao("Resultado da análise retrofit")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("🔋 Chumbo nominal", f"{retro['ah_chumbo']:.0f} Ah")
        r2.metric("📉 Ah real entregue chumbo", f"{retro['ah_real_chumbo']:.1f} Ah")
        r3.metric("✅ Ah mínimo LiFePO4", f"{retro['ah_lfp']:.1f} Ah")
        r4.metric("📦 LiFePO4 recomendado", f"{escolhida['capacidade_pack']:.0f} Ah")

    secao("Resultado do dimensionamento")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("⚡ Potência DC máxima", fmt(resumo["potencia_total"], 0, " W"))
    m2.metric("🔌 Corrente máxima", fmt(resumo["i_max"], 1, " A"))
    m3.metric("📉 Corrente média real", fmt(resumo["i_media"], 1, " A"))
    m4.metric("🔋 Capacidade necessária", fmt(resumo["ah_necessario"], 1, " Ah"))
    m5, m6 = st.columns(2)
    m5.metric("📊 Energia necessária", f"{resumo['kwh_necessario']:.2f} kWh")
    m6.metric("⚙️ Fator médio de consumo", f"{fator}%")

    secao("Bateria recomendada")
    r1, r2, r3 = st.columns(3)
    with r1:
        card("Configuração", [("Configuração", f"{resumo['serie']}S{escolhida['paralelo']}P"), ("Quantidade total de células", escolhida["total_celulas"]), ("Tensão nominal", f"{resumo['v_nom']:.1f} V"), ("Tensão máxima FullEnergy", f"{resumo['v_max']:.1f} V"), ("Tensão mínima FullEnergy", f"{resumo['v_min']:.1f} V")])
    with r2:
        card("Célula", [("Fabricante", escolhida["fabricante"]), ("Modelo", escolhida["modelo"]), ("Capacidade da célula", f"{escolhida['ah']:.0f} Ah"), ("Capacidade final do pack", f"{escolhida['capacidade_pack']:.0f} Ah"), ("Energia final", f"{escolhida['energia_pack']:.2f} kWh")])
    with r3:
        card("Características físicas", [("Peso unitário da célula", f"{escolhida['peso']:.2f} kg"), ("Peso estimado das células", f"{escolhida['peso_pack']:.1f} kg")])

    secao("Capacidade de corrente")
    q1, q2, q3 = st.columns(3)
    with q1:
        card("C-rate", [("C-rate contínuo da célula", f"{escolhida['c_rate_cont']:.2f}C"), ("C-rate pico da célula", f"{escolhida['c_rate_pico']:.2f}C"), ("C-rate utilizado pela aplicação", f"{escolhida['c_rate_uso']:.2f}C")])
    with q2:
        card("Célula", [("Corrente contínua da célula", f"{escolhida['cont']:.0f} A"), ("Corrente pico da célula", f"{escolhida['pico']:.0f} A")])
    with q3:
        card("Pack", [("Corrente contínua do pack", f"{escolhida['cont_pack']:.0f} A"), ("Corrente pico do pack", f"{escolhida['pico_pack']:.0f} A")])

    secao("Autonomia")
    a1, a2 = st.columns(2)
    a1.metric("⏱️ Autonomia estimada", f"{escolhida['autonomia']:.2f} h" if resumo["i_media"] else "Informe consumo")
    a2.metric("🔋 Energia disponível", f"{escolhida['energia_pack']:.2f} kWh")

    if controlador_min > 0 and controlador_max > 0:
        ok = resumo["v_min"] >= controlador_min and resumo["v_max"] <= controlador_max
        (st.success if ok else st.warning)("A faixa FullEnergy da bateria está dentro da faixa informada do controlador." if ok else "A faixa FullEnergy da bateria pode não estar compatível com a faixa informada do controlador.")

    secao("Comparativo de células")
    tabela = pd.DataFrame([{
        "Célula": f"{o['fabricante']} {o['modelo']}", "Configuração": f"{resumo['serie']}S{o['paralelo']}P",
        "Ah final": o["capacidade_pack"], "kWh": round(o["energia_pack"], 2),
        "Contínua pack A": o["cont_pack"], "Pico pack A": o["pico_pack"],
        "C-rate utilizado": round(o["c_rate_uso"], 2), "Peso células kg": round(o["peso_pack"], 1),
        "Autonomia h": round(o["autonomia"], 2) if resumo["i_media"] else "-",
    } for o in opcoes])
    st.dataframe(tabela, use_container_width=True)
