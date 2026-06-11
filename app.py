CSS = """
<style>
[data-testid="stAppViewContainer"]{background-color:#f4f6f8}
.block-container{padding-top:1.2rem;padding-bottom:3rem}

.header-fe{
    background:linear-gradient(135deg,#050505 0%,#181818 60%,#2a2a2a 100%);
    padding:22px 30px;
    border-radius:18px;
    border-bottom:5px solid #FFD400;
    box-shadow:0 6px 18px rgba(0,0,0,.22);
    text-align:left;
    margin-bottom:14px;
    min-height:190px;
    display:flex;
    flex-direction:column;
    justify-content:center;
}
.header-fe h1{color:white;font-size:38px;margin:0;font-weight:900}
.header-fe p{color:#d8d8d8;font-size:16px;margin-top:10px;margin-bottom:0}

.linha-amarela{height:3px;background:linear-gradient(90deg,#FFD400,#FFB000,#FFD400);border-radius:6px;margin:5px 0 20px 0}
.section-title{background:#111;color:white;padding:12px 18px;border-radius:12px;border-left:6px solid #FFD400;margin-top:26px;margin-bottom:18px;font-weight:800;font-size:20px}
div[data-testid="stMetric"],.result-card{background:white;border-radius:16px;padding:18px;border-left:5px solid #FFD400;box-shadow:0 3px 10px rgba(0,0,0,.08)}
.result-card{min-height:220px}
.alerta{background:#fff7d6;padding:16px;border-radius:14px;border-left:6px solid #FFD400;margin:18px 0 20px 0}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

col_logo, col_titulo = st.columns([1, 5])

with col_logo:
    st.image("logo.png", width=190)

with col_titulo:
    st.markdown("""
    <div class="header-fe">
        <h1>Dimensionamento de Baterias LiFePO4</h1>
        <p>Pré-dimensionamento técnico com base na aplicação, retrofit, corrente e células disponíveis.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="linha-amarela"></div>', unsafe_allow_html=True)

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
    itens = "".join(f"<p><b>{label}:</b> {valor}</p>" for label, valor in linhas)
    st.markdown(f'<div class="result-card"><h3>{titulo}</h3>{itens}</div>', unsafe_allow_html=True)


def criar_cards(dados, ncol=3):
    for col, (titulo, linhas) in zip(st.columns(ncol), dados):
        with col:
            card(titulo, linhas)


def exibir_metricas(dados, ncol):
    for col, (titulo, valor) in zip(st.columns(ncol), dados):
        col.metric(titulo, valor)


def serie_por_tensao(v):
    return SERIE.get(int(v), max(1, round(v / V_NOM)))


def tabela_padrao(tipo):
    tabelas = {
        "motor": {"Descrição": "Motor tração", "Tipo": "AC", "Potência": 3000, "Corrente (A)": 0, "Uso (%)": 100, "Eficiência (%)": 90},
        "aux": {"Descrição": "Componente auxiliar", "Tipo": "DC", "Potência": 0, "Corrente (A)": 0, "Uso (%)": 100, "Eficiência (%)": 100},
    }
    return pd.DataFrame([tabelas[tipo]])


def editor(df):
    return st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Tipo": st.column_config.SelectboxColumn("Tipo", options=["AC", "DC"]),
            "Uso (%)": st.column_config.NumberColumn("Uso (%)", min_value=0, max_value=100),
            "Eficiência (%)": st.column_config.NumberColumn("Eficiência (%)", min_value=1, max_value=100),
        },
    )


def input_num(col, label, value, **kwargs):
    with col:
        return st.number_input(label, value=value, **kwargs)


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


def calcular_retrofit(ah_chumbo, dod_chumbo, ef_chumbo, dod_lfp, ef_lfp):
    ah_real_chumbo = ah_chumbo * (dod_chumbo / 100) * (ef_chumbo / 100)
    ah_lfp_necessario = ah_real_chumbo / ((dod_lfp / 100) * (ef_lfp / 100))
    return ah_real_chumbo, ah_lfp_necessario


def calcular_consumo(motores, auxiliares, tensao):
    if motores.empty and auxiliares.empty:
        return 0

    tabela = pd.concat([motores, auxiliares], ignore_index=True)
    return sum(potencia_linha(r, tensao) for _, r in tabela.iterrows())


def calcular_opcoes(tensao, autonomia, fator, motores, auxiliares, ah_minimo_retrofit=0):
    potencia_total = calcular_consumo(motores, auxiliares, tensao)
    i_max = potencia_total / tensao if tensao and potencia_total else 0
    i_media = i_max * fator / 100 if fator else 0
    ah_por_consumo = i_media * autonomia if autonomia else 0
    ah_necessario = max(ah_por_consumo, ah_minimo_retrofit)

    serie = serie_por_tensao(tensao)
    v_nom, v_max, v_min = serie * V_NOM, serie * V_MAX, serie * V_MIN
    opcoes = []

    for c in CELULAS:
        p_ah = max(1, math.ceil(ah_necessario / c["ah"]))
        p_corrente = max(1, math.ceil(i_max / c["cont"])) if i_max else 1
        paralelo = max(p_ah, p_corrente)
        cap = c["ah"] * paralelo

        opcoes.append({
            **c,
            "serie": serie,
            "paralelo": paralelo,
            "total_celulas": serie * paralelo,
            "capacidade_pack": cap,
            "energia_pack": v_nom * cap / 1000,
            "cont_pack": c["cont"] * paralelo,
            "pico_pack": c["pico"] * paralelo,
            "peso_pack": c["peso"] * serie * paralelo,
            "autonomia": cap / i_media if i_media else 0,
            "c_rate_cont": c["cont"] / c["ah"],
            "c_rate_pico": c["pico"] / c["ah"],
            "c_rate_uso": i_max / cap if cap else 0,
        })

    resumo = {
        "potencia_total": potencia_total,
        "i_max": i_max,
        "i_media": i_media,
        "ah_por_consumo": ah_por_consumo,
        "ah_necessario": ah_necessario,
        "kwh_necessario": potencia_total * (fator / 100) * autonomia / 1000 if fator and autonomia else 0,
        "serie": serie,
        "v_nom": v_nom,
        "v_max": v_max,
        "v_min": v_min,
    }

    return resumo, opcoes


def escolher_celula(modo, opcoes, resumo):
    if modo == "Automática":
        validas = [
            o for o in opcoes
            if o["cont_pack"] >= resumo["i_max"]
            and o["capacidade_pack"] >= resumo["ah_necessario"]
        ]

        if not validas:
            return None

        return sorted(
            validas,
            key=lambda x: (x["paralelo"], x["peso_pack"], x["capacidade_pack"])
        )[0]

    nome = modo.split(" - ")[0]
    return next(o for o in opcoes if f"{o['fabricante']} {o['modelo']}" in nome)


def mostrar_retrofit():
    cols = st.columns(6)

    campos = [
        ("Tensão chumbo atual (V)", 48, dict(min_value=1)),
        ("Capacidade chumbo atual (Ah)", 220.0, dict(min_value=1.0, step=5.0)),
        ("DoD chumbo (%)", 80.0, dict(min_value=1.0, max_value=100.0, step=5.0)),
        ("Eficiência chumbo (%)", 70.0, dict(min_value=1.0, max_value=100.0, step=5.0)),
        ("DoD LiFePO4 (%)", 95.0, dict(min_value=1.0, max_value=100.0, step=1.0)),
        ("Eficiência LiFePO4 (%)", 95.0, dict(min_value=1.0, max_value=100.0, step=1.0)),
    ]

    tensao, ah_chumbo, dod_chumbo, ef_chumbo, dod_lfp, ef_lfp = [
        input_num(col, label, value, **kwargs)
        for col, (label, value, kwargs) in zip(cols, campos)
    ]

    ah_real_chumbo, ah_lfp = calcular_retrofit(
        ah_chumbo,
        dod_chumbo,
        ef_chumbo,
        dod_lfp,
        ef_lfp
    )

    retro = {
        "ah_chumbo": ah_chumbo,
        "ah_real_chumbo": ah_real_chumbo,
        "ah_lfp": ah_lfp,
    }

    return tensao, 0, 0, pd.DataFrame(), pd.DataFrame(), ah_lfp, retro


def mostrar_projeto_novo():
    cols = st.columns(4)

    tensao = input_num(cols[0], "Tensão nominal do sistema (V)", 48, min_value=1)
    autonomia = input_num(cols[1], "Autonomia desejada (horas)", 4.0, min_value=0.1, step=0.5)
    input_num(cols[2], "Tempo disponível para recarga (horas)", 4.0, min_value=0.0, step=0.5)
    fator = input_num(cols[3], "Fator médio real de consumo (%)", 40, min_value=1, max_value=100, step=5)

    secao("2. Motores")
    motores = editor(tabela_padrao("motor"))

    secao("3. Componentes auxiliares")
    auxiliares = editor(tabela_padrao("aux"))

    return tensao, autonomia, fator, motores, auxiliares, 0, {}


def tabela_comparativo(opcoes, resumo):
    return pd.DataFrame([{
        "Célula": f"{o['fabricante']} {o['modelo']}",
        "Configuração": f"{resumo['serie']}S{o['paralelo']}P",
        "Ah final": o["capacidade_pack"],
        "kWh": round(o["energia_pack"], 2),
        "Contínua pack A": o["cont_pack"],
        "Pico pack A": o["pico_pack"],
        "C-rate utilizado": round(o["c_rate_uso"], 2),
        "Peso células kg": round(o["peso_pack"], 1),
        "Autonomia h": round(o["autonomia"], 2) if resumo["i_media"] else "-",
    } for o in opcoes])


secao("1. Dados do projeto")

tipo = st.radio(
    "Este projeto é retrofit?",
    ["Sim, é retrofit", "Não, é projeto novo"],
    horizontal=True
)

retrofit = tipo == "Sim, é retrofit"

if retrofit:
    tensao, autonomia, fator, motores, auxiliares, ah_minimo_retrofit, retro = mostrar_retrofit()
else:
    tensao, autonomia, fator, motores, auxiliares, ah_minimo_retrofit, retro = mostrar_projeto_novo()

secao("4. Seleção da célula")

modo = st.selectbox(
    "Seleção de célula",
    ["Automática"] + [
        f"{c['fabricante']} {c['modelo']} - {c['ah']}Ah"
        for c in CELULAS
    ],
)

if st.button("Dimensionar bateria", type="primary"):
    resumo, opcoes = calcular_opcoes(
        tensao,
        autonomia,
        fator,
        motores,
        auxiliares,
        ah_minimo_retrofit
    )

    if resumo["i_max"] <= 0 and not retrofit:
        st.error("Informe pelo menos uma potência ou corrente nos motores/componentes.")
        st.stop()

    escolhida = escolher_celula(modo, opcoes, resumo)

    if escolhida is None:
        st.error("Nenhuma célula atende aos critérios informados.")
        st.stop()

    st.markdown(
        '<div class="alerta"><b>Observação técnica:</b> este é um pré-dimensionamento. '
        'Em retrofit, a capacidade mínima usa a equivalência chumbo x LiFePO4. '
        'Em projeto novo, o cálculo considera potência, corrente, autonomia e fator médio real de consumo.</div>',
        unsafe_allow_html=True,
    )

    if retrofit:
        secao("Resultado da análise retrofit")
        exibir_metricas([
            ("🔋 Chumbo nominal", f"{retro['ah_chumbo']:.0f} Ah"),
            ("📉 Ah real entregue chumbo", f"{retro['ah_real_chumbo']:.1f} Ah"),
            ("✅ Ah mínimo LiFePO4", f"{retro['ah_lfp']:.1f} Ah"),
            ("📦 LiFePO4 recomendado", f"{escolhida['capacidade_pack']:.0f} Ah"),
        ], 4)

    if not retrofit:
        secao("Resultado do dimensionamento")
        exibir_metricas([
            ("⚡ Potência DC máxima", fmt(resumo["potencia_total"], 0, " W")),
            ("🔌 Corrente máxima", fmt(resumo["i_max"], 1, " A")),
            ("📉 Corrente média real", fmt(resumo["i_media"], 1, " A")),
            ("🔋 Capacidade necessária", fmt(resumo["ah_necessario"], 1, " Ah")),
        ], 4)

        exibir_metricas([
            ("📊 Energia necessária", f"{resumo['kwh_necessario']:.2f} kWh"),
            ("⚙️ Fator médio de consumo", f"{fator}%"),
        ], 2)

    secao("Bateria recomendada")
    criar_cards([
        ("Configuração", [
            ("Configuração", f"{resumo['serie']}S{escolhida['paralelo']}P"),
            ("Quantidade total de células", escolhida["total_celulas"]),
            ("Tensão nominal", f"{resumo['v_nom']:.1f} V"),
            ("Tensão máxima FullEnergy", f"{resumo['v_max']:.1f} V"),
            ("Tensão mínima FullEnergy", f"{resumo['v_min']:.1f} V"),
        ]),
        ("Célula", [
            ("Fabricante", escolhida["fabricante"]),
            ("Modelo", escolhida["modelo"]),
            ("Capacidade da célula", f"{escolhida['ah']:.0f} Ah"),
            ("Capacidade final do pack", f"{escolhida['capacidade_pack']:.0f} Ah"),
            ("Energia final", f"{escolhida['energia_pack']:.2f} kWh"),
        ]),
        ("Características físicas", [
            ("Peso unitário da célula", f"{escolhida['peso']:.2f} kg"),
            ("Peso estimado das células", f"{escolhida['peso_pack']:.1f} kg"),
        ]),
    ], 3)

    if not retrofit:
        secao("Capacidade de corrente")
        criar_cards([
            ("C-rate", [
                ("C-rate contínuo da célula", f"{escolhida['c_rate_cont']:.2f}C"),
                ("C-rate pico da célula", f"{escolhida['c_rate_pico']:.2f}C"),
                ("C-rate utilizado pela aplicação", f"{escolhida['c_rate_uso']:.2f}C"),
            ]),
            ("Célula", [
                ("Corrente contínua da célula", f"{escolhida['cont']:.0f} A"),
                ("Corrente pico da célula", f"{escolhida['pico']:.0f} A"),
            ]),
            ("Pack", [
                ("Corrente contínua do pack", f"{escolhida['cont_pack']:.0f} A"),
                ("Corrente pico do pack", f"{escolhida['pico_pack']:.0f} A"),
            ]),
        ], 3)

        secao("Autonomia")
        exibir_metricas([
            ("⏱️ Autonomia estimada", f"{escolhida['autonomia']:.2f} h"),
            ("🔋 Energia disponível", f"{escolhida['energia_pack']:.2f} kWh"),
        ], 2)

    secao("Comparativo de células")
    st.dataframe(tabela_comparativo(opcoes, resumo), use_container_width=True)
