import math
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="FullEnergy | Dimensionamento LiFePO4",
    page_icon="🔋",
    layout="wide"
)

# =========================
# BANCO DE CÉLULAS
# =========================

CELULAS = [
    {"fabricante": "Great Power", "modelo": "IFR40135", "ah": 20, "v": 3.2, "descarga_continua_a": 60, "descarga_pico_a": 60, "carga_continua_a": 20, "peso_kg": 0.55},
    {"fabricante": "Gotion", "modelo": "IFP20100140A", "ah": 27, "v": 3.2, "descarga_continua_a": 108, "descarga_pico_a": 135, "carga_continua_a": 54, "peso_kg": 0.596},
    {"fabricante": "King Power", "modelo": "IFP36130141AE", "ah": 50, "v": 3.2, "descarga_continua_a": 400, "descarga_pico_a": 400, "carga_continua_a": 150, "peso_kg": 1.23},
    {"fabricante": "CALB", "modelo": "L148F88A", "ah": 88, "v": 3.2, "descarga_continua_a": 88, "descarga_pico_a": 176, "carga_continua_a": 88, "peso_kg": 1.84},
    {"fabricante": "REPT", "modelo": "CB56-104Ah", "ah": 104, "v": 3.2, "descarga_continua_a": 208, "descarga_pico_a": 520, "carga_continua_a": 104, "peso_kg": 1.92},
    {"fabricante": "Gotion", "modelo": "105Ah", "ah": 105, "v": 3.2, "descarga_continua_a": 105, "descarga_pico_a": 210, "carga_continua_a": 52.5, "peso_kg": 2.0},
    {"fabricante": "CALB", "modelo": "L173F163", "ah": 163, "v": 3.2, "descarga_continua_a": 163, "descarga_pico_a": 326, "carga_continua_a": 163, "peso_kg": 3.19},
    {"fabricante": "EVE", "modelo": "LF230", "ah": 230, "v": 3.2, "descarga_continua_a": 230, "descarga_pico_a": 460, "carga_continua_a": 230, "peso_kg": 4.11},
    {"fabricante": "XDLE", "modelo": "CBA54173204", "ah": 230, "v": 3.2, "descarga_continua_a": 230, "descarga_pico_a": 690, "carga_continua_a": 230, "peso_kg": 4.10},
    {"fabricante": "EVE", "modelo": "LF280K", "ah": 280, "v": 3.2, "descarga_continua_a": 280, "descarga_pico_a": 560, "carga_continua_a": 280, "peso_kg": 5.49},
]

# =========================
# ESTILO
# =========================

st.markdown("""
<style>
.block-container {padding-top: 1.5rem;}
.header {
    background: linear-gradient(90deg, #111111, #2a2a2a);
    padding: 28px;
    border-radius: 18px;
    border-bottom: 5px solid #FFD400;
}
.header h1 {color: white; margin-bottom: 5px;}
.header p {color: #d8d8d8; font-size: 17px;}
.card {
    background-color: white;
    padding: 22px;
    border-radius: 15px;
    border: 1px solid #e6e6e6;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.04);
}
.alerta {
    background-color: #fff7d6;
    padding: 14px;
    border-radius: 12px;
    border-left: 6px solid #FFD400;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <h1>🔋 FullEnergy | Dimensionamento de Bateria LiFePO4</h1>
    <p>Ferramenta técnica para pré-dimensionamento de baterias de lítio com base na aplicação, autonomia, corrente e células disponíveis.</p>
</div>
""", unsafe_allow_html=True)

st.write("")

# =========================
# FUNÇÕES
# =========================

def serie_por_tensao(tensao):
    mapa = {12: 4, 24: 8, 36: 12, 48: 16, 60: 20, 72: 24, 80: 25, 96: 30}
    return mapa.get(int(tensao), max(1, round(tensao / 3.2)))

def calcula_potencia_linha(row, tensao):
    potencia = float(row.get("Potência", 0) or 0)
    corrente = float(row.get("Corrente (A)", 0) or 0)
    uso = float(row.get("Uso (%)", 100) or 100) / 100
    eficiencia = float(row.get("Eficiência (%)", 90) or 90) / 100
    tipo = row.get("Tipo", "DC")

    if corrente > 0 and tensao > 0:
        potencia_dc = corrente * tensao
    else:
        if tipo == "AC":
            potencia_dc = potencia / eficiencia if eficiencia > 0 else potencia
        else:
            potencia_dc = potencia

    return potencia_dc * uso

def padrao_tabela_motor():
    return pd.DataFrame([
        {"Descrição": "Motor tração", "Tipo": "AC", "Potência": 3000, "Corrente (A)": 0, "Uso (%)": 100, "Eficiência (%)": 90}
    ])

def padrao_tabela_aux():
    return pd.DataFrame([
        {"Descrição": "Iluminação / módulo / bomba", "Tipo": "DC", "Potência": 0, "Corrente (A)": 0, "Uso (%)": 100, "Eficiência (%)": 100}
    ])

def sugerir_bms(corrente):
    opcoes = [30, 60, 100, 150, 200, 300, 400, 500, 600]
    for o in opcoes:
        if corrente <= o:
            return o
    return math.ceil(corrente / 100) * 100

def sugerir_carregador(capacidade_ah, tempo_h):
    if tempo_h <= 0:
        return None
    corrente = capacidade_ah / tempo_h
    opcoes = [10, 15, 25, 30, 50, 80, 100, 120, 150, 200]
    for o in opcoes:
        if corrente <= o:
            return o
    return math.ceil(corrente / 10) * 10

# =========================
# ENTRADAS
# =========================

st.subheader("1. Tipo de projeto")

tipo = st.radio(
    "Este projeto é retrofit?",
    ["Sim, é retrofit", "Não, é projeto novo"],
    horizontal=True
)

col1, col2, col3 = st.columns(3)

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

st.write("")

with st.expander("Faixa de operação do controlador (opcional)"):
    c1, c2 = st.columns(2)
    with c1:
        controlador_min = st.number_input("Tensão mínima do controlador (V)", min_value=0.0, value=0.0)
    with c2:
        controlador_max = st.number_input("Tensão máxima do controlador (V)", min_value=0.0, value=0.0)

st.write("")

st.subheader("2. Motores")

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

st.subheader("3. Componentes auxiliares")

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

st.write("")

modo_celula = st.selectbox(
    "Seleção de célula",
    ["Automática"] + [f"{c['fabricante']} {c['modelo']} - {c['ah']}Ah" for c in CELULAS]
)

# =========================
# CÁLCULO
# =========================

if st.button("Dimensionar bateria", type="primary"):

    potencia_motores = sum(calcula_potencia_linha(row, tensao_sistema) for _, row in motores.iterrows())
    potencia_aux = sum(calcula_potencia_linha(row, tensao_sistema) for _, row in auxiliares.iterrows())

    potencia_total = potencia_motores + potencia_aux
    corrente_media = potencia_total / tensao_sistema if tensao_sistema > 0 else 0

    ah_necessario = corrente_media * autonomia_h
    energia_necessaria_kwh = (potencia_total * autonomia_h) / 1000

    serie = serie_por_tensao(tensao_sistema)
    tensao_nominal_pack = serie * 3.2
    tensao_max_pack = serie * 3.65
    tensao_min_pack = serie * 2.5

    resultados = []

    for cel in CELULAS:
        paralelo_por_ah = math.ceil(ah_necessario / cel["ah"]) if cel["ah"] > 0 else 1
        paralelo_por_corrente = math.ceil(corrente_media / cel["descarga_continua_a"]) if cel["descarga_continua_a"] > 0 else 1
        paralelo = max(1, paralelo_por_ah, paralelo_por_corrente)

        capacidade_pack = cel["ah"] * paralelo
        energia_pack_kwh = tensao_nominal_pack * capacidade_pack / 1000
        corrente_cont_pack = cel["descarga_continua_a"] * paralelo
        corrente_pico_pack = cel["descarga_pico_a"] * paralelo
        peso_pack = cel["peso_kg"] * serie * paralelo
        autonomia_estimada = capacidade_pack / corrente_media if corrente_media > 0 else 0

        resultados.append({
            "celula": cel,
            "paralelo": paralelo,
            "capacidade_pack": capacidade_pack,
            "energia_pack_kwh": energia_pack_kwh,
            "corrente_cont_pack": corrente_cont_pack,
            "corrente_pico_pack": corrente_pico_pack,
            "peso_pack": peso_pack,
            "autonomia_estimada": autonomia_estimada
        })

    if modo_celula == "Automática":
        resultados_validos = [r for r in resultados if r["corrente_cont_pack"] >= corrente_media and r["capacidade_pack"] >= ah_necessario]
        escolhido = sorted(resultados_validos, key=lambda x: (x["paralelo"], x["peso_pack"], x["capacidade_pack"]))[0]
    else:
        modelo_escolhido = modo_celula.split(" - ")[0]
        escolhido = next(r for r in resultados if f"{r['celula']['fabricante']} {r['celula']['modelo']}" in modelo_escolhido)

    cel = escolhido["celula"]
    paralelo = escolhido["paralelo"]

    bms_sugerido = sugerir_bms(corrente_media * 1.25)
    carregador = sugerir_carregador(escolhido["capacidade_pack"], tempo_recarga_h)

    st.write("")
    st.markdown('<div class="alerta">', unsafe_allow_html=True)
    st.write("**Observação técnica:** este é um pré-dimensionamento. Caso algum dado da aplicação não tenha sido informado, o sistema utiliza estimativas com base em tensão, potência, corrente e eficiência.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    st.subheader("Resultado do dimensionamento")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Potência DC estimada", f"{potencia_total:,.0f} W".replace(",", "."))
    r2.metric("Corrente média estimada", f"{corrente_media:.1f} A")
    r3.metric("Capacidade necessária", f"{ah_necessario:.1f} Ah")
    r4.metric("Energia necessária", f"{energia_necessaria_kwh:.2f} kWh")

    st.write("")

    st.subheader("Bateria recomendada")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.write(f"**Configuração:** {serie}S{paralelo}P")
        st.write(f"**Tensão nominal:** {tensao_nominal_pack:.1f} V")
        st.write(f"**Faixa estimada do pack:** {tensao_min_pack:.1f} V a {tensao_max_pack:.1f} V")

    with c2:
        st.write(f"**Célula:** {cel['fabricante']} {cel['modelo']}")
        st.write(f"**Capacidade final:** {escolhido['capacidade_pack']:.0f} Ah")
        st.write(f"**Energia final:** {escolhido['energia_pack_kwh']:.2f} kWh")

    with c3:
        st.write(f"**Corrente contínua do pack:** {escolhido['corrente_cont_pack']:.0f} A")
        st.write(f"**Corrente pico do pack:** {escolhido['corrente_pico_pack']:.0f} A")
        st.write(f"**Peso estimado das células:** {escolhido['peso_pack']:.1f} kg")

    st.write("")
    st.subheader("Autonomia e recarga")

    a1, a2, a3 = st.columns(3)
    a1.metric("Autonomia estimada", f"{escolhido['autonomia_estimada']:.2f} h")
    a2.metric("BMS sugerido", f"{bms_sugerido} A")
    if carregador:
        a3.metric("Carregador sugerido", f"{int(tensao_sistema)}V {carregador}A")
    else:
        a3.metric("Carregador sugerido", "Definir manualmente")

    if controlador_min > 0 and controlador_max > 0:
        st.write("")
        if tensao_min_pack >= controlador_min and tensao_max_pack <= controlador_max:
            st.success("A faixa estimada da bateria está dentro da faixa informada do controlador.")
        else:
            st.warning("A faixa estimada da bateria pode não estar compatível com a faixa informada do controlador.")

    st.write("")
    st.subheader("Comparativo de células")

    tabela = []
    for r in resultados:
        tabela.append({
            "Célula": f"{r['celula']['fabricante']} {r['celula']['modelo']}",
            "Configuração": f"{serie}S{r['paralelo']}P",
            "Ah final": r["capacidade_pack"],
            "kWh": round(r["energia_pack_kwh"], 2),
            "Corrente contínua A": r["corrente_cont_pack"],
            "Peso células kg": round(r["peso_pack"], 1),
            "Autonomia h": round(r["autonomia_estimada"], 2)
        })

    st.dataframe(pd.DataFrame(tabela), use_container_width=True)
