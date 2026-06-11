import math
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="FullEnergy | Dimensionamento LiFePO4",
    page_icon="🔋",
    layout="wide"
)

V_CEL_NOMINAL = 3.2
V_CEL_MAX = 3.55
V_CEL_MIN = 2.6

SERIE_PADRAO = {12: 4, 24: 8, 36: 12, 48: 16, 60: 20, 72: 24}

CELULAS = [
    {"fabricante": "Great Power", "modelo": "IFR40135", "ah": 20, "descarga_continua_a": 60, "descarga_pico_a": 60, "peso_kg": 0.55},
    {"fabricante": "Gotion", "modelo": "IFP20100140A", "ah": 27, "descarga_continua_a": 108, "descarga_pico_a": 135, "peso_kg": 0.596},
    {"fabricante": "King Power", "modelo": "IFP36130141AE", "ah": 50, "descarga_continua_a": 400, "descarga_pico_a": 400, "peso_kg": 1.23},
    {"fabricante": "CALB", "modelo": "L148F88A", "ah": 88, "descarga_continua_a": 88, "descarga_pico_a": 176, "peso_kg": 1.84},
    {"fabricante": "REPT", "modelo": "CB56-104Ah", "ah": 104, "descarga_continua_a": 208, "descarga_pico_a": 520, "peso_kg": 1.92},
    {"fabricante": "Gotion", "modelo": "105Ah", "ah": 105, "descarga_continua_a": 105, "descarga_pico_a": 210, "peso_kg": 2.0},
    {"fabricante": "CALB", "modelo": "L173F163", "ah": 163, "descarga_continua_a": 163, "descarga_pico_a": 326, "peso_kg": 3.19},
    {"fabricante": "EVE", "modelo": "LF230", "ah": 230, "descarga_continua_a": 230, "descarga_pico_a": 460, "peso_kg": 4.11},
    {"fabricante": "XDLE", "modelo": "CBA54173204", "ah": 230, "descarga_continua_a": 230, "descarga_pico_a": 690, "peso_kg": 4.10},
    {"fabricante": "EVE", "modelo": "LF280K", "ah": 280, "descarga_continua_a": 280, "descarga_pico_a": 560, "peso_kg": 5.49},
]

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {background-color: #f4f6f8;}
.block-container {padding-top: 1.2rem; padding-bottom: 3rem;}

.header-fe {
    background: linear-gradient(135deg, #050505 0%, #181818 60%, #2a2a2a 100%);
    padding: 26px 30px;
    border-radius: 18px;
    border-bottom: 6px solid #FFD400;
    box-shadow: 0px 6px 18px rgba(0,0,0,0.22);
    text-align: center;
    margin-bottom: 24px;
}
.header-fe h1 {color: #ffffff; font-size: 30px; margin: 8px 0 0 0; font-weight: 800;}
.header-fe p {color: #d8d8d8; font-size: 16px; margin-top: 6px;}

.linha-amarela {
    height: 5px;
    background: linear-gradient(90deg,#FFD400,#FFB000,#FFD400);
    border-radius: 6px;
    margin: 10px 0 28px 0;
}

.section-title {
    background: #111111;
    color: white;
    padding: 12px 18px;
    border-radius: 12px;
    border-left: 6px solid #FFD400;
    margin-top: 26px;
    margin-bottom: 18px;
    font-weight: 800;
    font-size: 20px;
}

div[data-testid="stMetric"] {
    background-color: #ffffff;
    border-radius: 16px;
    padding: 18px;
    border-left: 5px solid #FFD400;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.08);
}

.result-card {
    background-color: #ffffff;
    padding: 22px;
    border-radius: 16px;
    border-left: 5px solid #FFD400;
    box-shadow: 0px 3px 12px rgba(0,0,0,0.08);
    min-height: 230px;
}

.alerta {
    background-color: #fff7d6;
    padding: 16px;
    border-radius: 14px;
    border-left: 6px solid #FFD400;
    margin-top: 18px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-fe">', unsafe_allow_html=True)
st.image("Prancheta 5.png", width=260)
st.markdown("""
<h1>Dimensionamento de Baterias LiFePO4</h1>
<p>Pré-dimensionamento técnico com base na aplicação, autonomia, corrente e células disponíveis.</p>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div class="linha-amarela"></div>', unsafe_allow_html=True)

def valor_numero(valor, padrao=0.0):
    try:
        if pd.isna(valor):
            return padrao
        return float(valor)
    except:
        return padrao

def serie_por_tensao(tensao):
    return SERIE_PADRAO.get(int(tensao), max(1, round(tensao / V_CEL_NOMINAL)))

def calcula_potencia_linha(row, tensao):
    potencia = valor_numero(row.get("Potência", 0))
    corrente = valor_numero(row.get("Corrente (A)", 0))
    uso = valor_numero(row.get("Uso (%)", 100), 100) / 100
    eficiencia = valor_numero(row.get("Eficiência (%)", 90), 90) / 100
    tipo = row.get("Tipo", "DC")

    if potencia <= 0 and corrente <= 0:
        return 0

    if corrente > 0 and tensao > 0:
        potencia_dc = corrente * tensao
    else:
        potencia_dc = potencia / eficiencia if tipo == "AC" and eficiencia > 0 else potencia

    return potencia_dc * uso

def padrao_tabela_motor():
    return pd.DataFrame([
        {"Descrição": "Motor tração", "Tipo": "AC", "Potência": 3000, "Corrente (A)": 0, "Uso (%)": 100, "Eficiência (%)": 90}
    ])

def padrao_tabela_aux():
    return pd.DataFrame([
        {"Descrição": "Componente auxiliar", "Tipo": "DC", "Potência": 0, "Corrente (A)": 0, "Uso (%)": 100, "Eficiência (%)": 100}
    ])

st.markdown('<div class="section-title">1. Dados do projeto</div>', unsafe_allow_html=True)

tipo = st.radio("Este projeto é retrofit?", ["Sim, é retrofit", "Não, é projeto novo"], horizontal=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if tipo == "Sim, é retrofit":
        tensao_sistema = st.number_input("Tensão da bateria de chumbo atual (V)", min_value=1, value=48)
        ah_chumbo = st.number_input("Capacidade da bateria de chumbo atual (Ah)", min_value=0, value=105)
    else:
        tensao_sistema = st.number_input("Tensão nominal do sistema (V)", min_value=1, value=48)

with col2:
    autonomia_h = st.number_input("Autonomia desejada (horas)", min_value=0.1, value=4.0, step=0.5)

with col3:
    tempo_recarga_h = st.number_input("Tempo disponível para recarga (horas)", min_value=0.0, value=4.0, step=0.5)

with col4:
    fator_consumo_medio = st.number_input("Fator médio real de consumo (%)", min_value=1, max_value=100, value=40, step=5)

with st.expander("Faixa de operação do controlador (opcional)"):
    c1, c2 = st.columns(2)
    with c1:
        controlador_min = st.number_input("Tensão mínima do controlador (V)", min_value=0.0, value=0.0)
    with c2:
        controlador_max = st.number_input("Tensão máxima do controlador (V)", min_value=0.0, value=0.0)

st.markdown('<div class="section-title">2. Motores</div>', unsafe_allow_html=True)

motores = st.data_editor(
    padrao_tabela_motor(),
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Tipo": st.column_config.SelectboxColumn("Tipo", options=["AC", "DC"]),
        "Uso (%)": st.column_config.NumberColumn("Uso (%)", min_value=0, max_value=100),
        "Eficiência (%)": st.column_config.NumberColumn("Eficiência (%)", min_value=1, max_value=100),
    }
)

st.markdown('<div class="section-title">3. Componentes auxiliares</div>', unsafe_allow_html=True)

auxiliares = st.data_editor(
    padrao_tabela_aux(),
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Tipo": st.column_config.SelectboxColumn("Tipo", options=["AC", "DC"]),
        "Uso (%)": st.column_config.NumberColumn("Uso (%)", min_value=0, max_value=100),
        "Eficiência (%)": st.column_config.NumberColumn("Eficiência (%)", min_value=1, max_value=100),
    }
)

st.markdown('<div class="section-title">4. Seleção da célula</div>', unsafe_allow_html=True)

modo_celula = st.selectbox(
    "Seleção de célula",
    ["Automática"] + [f"{c['fabricante']} {c['modelo']} - {c['ah']}Ah" for c in CELULAS]
)

if st.button("Dimensionar bateria", type="primary"):

    potencia_motores = sum(calcula_potencia_linha(row, tensao_sistema) for _, row in motores.iterrows())
    potencia_aux = sum(calcula_potencia_linha(row, tensao_sistema) for _, row in auxiliares.iterrows())

    potencia_total_pico = potencia_motores + potencia_aux
    corrente_maxima_aplicacao = potencia_total_pico / tensao_sistema if tensao_sistema > 0 else 0

    fator = fator_consumo_medio / 100
    potencia_media_real = potencia_total_pico * fator
    corrente_media_real = corrente_maxima_aplicacao * fator

    if corrente_maxima_aplicacao <= 0:
        st.error("Informe pelo menos uma potência ou corrente nos motores/componentes para calcular o dimensionamento.")
        st.stop()

    ah_necessario = corrente_media_real * autonomia_h
    energia_necessaria_kwh = (potencia_media_real * autonomia_h) / 1000

    serie = serie_por_tensao(tensao_sistema)

    tensao_nominal_pack = serie * V_CEL_NOMINAL
    tensao_max_pack = serie * V_CEL_MAX
    tensao_min_pack = serie * V_CEL_MIN

    resultados = []

    for cel in CELULAS:
        ah_celula = valor_numero(cel.get("ah", 0))
        descarga_cont = valor_numero(cel.get("descarga_continua_a", 0))
        descarga_pico = valor_numero(cel.get("descarga_pico_a", 0))
        peso_celula = valor_numero(cel.get("peso_kg", 0))

        paralelo_por_ah = max(1, math.ceil(ah_necessario / ah_celula)) if ah_celula > 0 else 1
        paralelo_por_corrente = max(1, math.ceil(corrente_maxima_aplicacao / descarga_cont)) if descarga_cont > 0 else 1

        paralelo = max(1, paralelo_por_ah, paralelo_por_corrente)

        capacidade_pack = ah_celula * paralelo
        energia_pack_kwh = tensao_nominal_pack * capacidade_pack / 1000
        corrente_cont_pack = descarga_cont * paralelo
        corrente_pico_pack = descarga_pico * paralelo
        peso_pack = peso_celula * serie * paralelo
        autonomia_estimada = capacidade_pack / corrente_media_real if corrente_media_real > 0 else 0

        c_rate_cont_celula = descarga_cont / ah_celula if ah_celula > 0 else 0
        c_rate_pico_celula = descarga_pico / ah_celula if ah_celula > 0 else 0
        c_rate_utilizado_pack = corrente_maxima_aplicacao / capacidade_pack if capacidade_pack > 0 else 0

        resultados.append({
            "celula": cel,
            "paralelo": paralelo,
            "capacidade_pack": capacidade_pack,
            "energia_pack_kwh": energia_pack_kwh,
            "corrente_cont_pack": corrente_cont_pack,
            "corrente_pico_pack": corrente_pico_pack,
            "peso_pack": peso_pack,
            "autonomia_estimada": autonomia_estimada,
            "c_rate_cont_celula": c_rate_cont_celula,
            "c_rate_pico_celula": c_rate_pico_celula,
            "c_rate_utilizado_pack": c_rate_utilizado_pack
        })

    if modo_celula == "Automática":
        resultados_validos = [
            r for r in resultados
            if r["corrente_cont_pack"] >= corrente_maxima_aplicacao
            and r["capacidade_pack"] >= ah_necessario
        ]

        if not resultados_validos:
            st.error("Nenhuma célula atende aos critérios de corrente e autonomia informados.")
            st.stop()

        escolhido = sorted(resultados_validos, key=lambda x: (x["paralelo"], x["peso_pack"], x["capacidade_pack"]))[0]
    else:
        modelo_escolhido = modo_celula.split(" - ")[0]
        escolhido = next(
            r for r in resultados
            if f"{r['celula']['fabricante']} {r['celula']['modelo']}" in modelo_escolhido
        )

    cel = escolhido["celula"]
    paralelo = escolhido["paralelo"]
    total_celulas = serie * paralelo

    st.markdown('<div class="alerta">', unsafe_allow_html=True)
    st.write("**Observação técnica:** este é um pré-dimensionamento. A autonomia utiliza o fator médio real de consumo. Os limites de corrente são baseados nos dados cadastrados das células.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Resultado do dimensionamento</div>', unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("⚡ Potência DC máxima", f"{potencia_total_pico:,.0f} W".replace(",", "."))
    r2.metric("🔌 Corrente máxima", f"{corrente_maxima_aplicacao:.1f} A")
    r3.metric("📉 Corrente média real", f"{corrente_media_real:.1f} A")
    r4.metric("🔋 Capacidade necessária", f"{ah_necessario:.1f} Ah")

    r5, r6 = st.columns(2)
    r5.metric("📊 Energia necessária", f"{energia_necessaria_kwh:.2f} kWh")
    r6.metric("⚙️ Fator médio de consumo", f"{fator_consumo_medio}%")

    st.markdown('<div class="section-title">Bateria recomendada</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown("### Configuração")
        st.write(f"**Configuração:** {serie}S{paralelo}P")
        st.write(f"**Quantidade total de células:** {total_celulas}")
        st.write(f"**Tensão nominal:** {tensao_nominal_pack:.1f} V")
        st.write(f"**Tensão máxima FullEnergy:** {tensao_max_pack:.1f} V")
        st.write(f"**Tensão mínima FullEnergy:** {tensao_min_pack:.1f} V")
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown("### Célula")
        st.write(f"**Fabricante:** {cel['fabricante']}")
        st.write(f"**Modelo:** {cel['modelo']}")
        st.write(f"**Capacidade da célula:** {cel['ah']:.0f} Ah")
        st.write(f"**Capacidade final do pack:** {escolhido['capacidade_pack']:.0f} Ah")
        st.write(f"**Energia final:** {escolhido['energia_pack_kwh']:.2f} kWh")
        st.markdown('</div>', unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown("### Características físicas")
        st.write(f"**Peso unitário da célula:** {cel['peso_kg']:.2f} kg")
        st.write(f"**Peso estimado das células:** {escolhido['peso_pack']:.1f} kg")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Capacidade de corrente</div>', unsafe_allow_html=True)

    cc1, cc2, cc3 = st.columns(3)

    with cc1:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown("### C-rate")
        st.write(f"**C-rate contínuo da célula:** {escolhido['c_rate_cont_celula']:.2f}C")
        st.write(f"**C-rate pico da célula:** {escolhido['c_rate_pico_celula']:.2f}C")
        st.write(f"**C-rate utilizado pela aplicação:** {escolhido['c_rate_utilizado_pack']:.2f}C")
        st.markdown('</div>', unsafe_allow_html=True)

    with cc2:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown("### Célula")
        st.write(f"**Corrente contínua da célula:** {cel['descarga_continua_a']:.0f} A")
        st.write(f"**Corrente pico da célula:** {cel['descarga_pico_a']:.0f} A")
        st.markdown('</div>', unsafe_allow_html=True)

    with cc3:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown("### Pack")
        st.write(f"**Corrente contínua do pack:** {escolhido['corrente_cont_pack']:.0f} A")
        st.write(f"**Corrente pico do pack:** {escolhido['corrente_pico_pack']:.0f} A")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Autonomia</div>', unsafe_allow_html=True)

    a1, a2 = st.columns(2)
    a1.metric("⏱️ Autonomia estimada", f"{escolhido['autonomia_estimada']:.2f} h")
    a2.metric("🔋 Energia disponível", f"{escolhido['energia_pack_kwh']:.2f} kWh")

    if controlador_min > 0 and controlador_max > 0:
        if tensao_min_pack >= controlador_min and tensao_max_pack <= controlador_max:
            st.success("A faixa FullEnergy da bateria está dentro da faixa informada do controlador.")
        else:
            st.warning("A faixa FullEnergy da bateria pode não estar compatível com a faixa informada do controlador.")

    st.markdown('<div class="section-title">Comparativo de células</div>', unsafe_allow_html=True)

    tabela = []
    for r in resultados:
        tabela.append({
            "Célula": f"{r['celula']['fabricante']} {r['celula']['modelo']}",
            "Configuração": f"{serie}S{r['paralelo']}P",
            "Ah final": r["capacidade_pack"],
            "kWh": round(r["energia_pack_kwh"], 2),
            "Contínua pack A": r["corrente_cont_pack"],
            "Pico pack A": r["corrente_pico_pack"],
            "C-rate utilizado": round(r["c_rate_utilizado_pack"], 2),
            "Peso células kg": round(r["peso_pack"], 1),
            "Autonomia h": round(r["autonomia_estimada"], 2)
        })

    st.dataframe(pd.DataFrame(tabela), use_container_width=True)
