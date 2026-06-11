


        validas = [o for o in opcoes if o["cont_pack"] >= resumo["i_max"] and o["capacidade_pack"] >= resumo["ah_necessario"]]
        return sorted(validas, key=lambda x: (x["paralelo"], x["peso_pack"], x["capacidade_pack"]))[0] if validas else None
    return next(o for o in opcoes if modo.startswith(f"{o['fabricante']} {o['modelo']}"))


def mostrar_retrofit():
    campos = [
        ("Tensão chumbo atual (V)", 48, dict(min_value=1)),
        ("Capacidade chumbo atual (Ah)", 220.0, dict(min_value=1.0, step=5.0)),
        ("DoD chumbo (%)", 80.0, dict(min_value=1.0, max_value=100.0, step=5.0)),
        ("Eficiência chumbo (%)", 70.0, dict(min_value=1.0, max_value=100.0, step=5.0)),
        ("DoD LiFePO4 (%)", 95.0, dict(min_value=1.0, max_value=100.0, step=1.0)),
        ("Eficiência LiFePO4 (%)", 95.0, dict(min_value=1.0, max_value=100.0, step=1.0)),
    ]
    tensao, ah_chumbo, dod_chumbo, ef_chumbo, dod_lfp, ef_lfp = [input_num(c, l, v, **k) for c, (l, v, k) in zip(st.columns(6), campos)]
    ah_real_chumbo, ah_lfp = calcular_retrofit(ah_chumbo, dod_chumbo, ef_chumbo, dod_lfp, ef_lfp)
    return tensao, 0, 0, pd.DataFrame(), pd.DataFrame(), ah_lfp, {"ah_chumbo": ah_chumbo, "ah_real_chumbo": ah_real_chumbo, "ah_lfp": ah_lfp}


def mostrar_projeto_novo():
    cols = st.columns(4)
    tensao = input_num(cols[0], "Tensão nominal do sistema (V)", 48, min_value=1)
    autonomia = input_num(cols[1], "Autonomia desejada (horas)", 4.0, min_value=0.1, step=0.5)
    input_num(cols[2], "Tempo disponível para recarga (horas)", 4.0, min_value=0.0, step=0.5)
    fator = input_num(cols[3], "Fator médio real de consumo (%)", 40, min_value=1, max_value=100, step=5)

secao("2. Motores")
motores = editor(tabela_padrao("motor"))

secao("3. Controlador")
controlador_df = editor_controlador(tabela_controlador())

secao("4. Componentes auxiliares")
auxiliares = editor(tabela_padrao("aux"))

return tensao, autonomia, fator, motores, controlador_df, auxiliares, 0, {}


def mostrar_controlador():
    secao("4. Dados do controlador")
    campos = [
        ("Tensão mínima controlador (V)", 0.0, dict(min_value=0.0, step=1.0)),
        ("Tensão máxima controlador (V)", 0.0, dict(min_value=0.0, step=1.0)),
        ("Corrente contínua controlador (A)", 0.0, dict(min_value=0.0, step=5.0)),
        ("Corrente pico controlador (A)", 0.0, dict(min_value=0.0, step=5.0)),
    ]
    v_min, v_max, i_cont, i_pico = [input_num(c, l, v, **k) for c, (l, v, k) in zip(st.columns(4), campos)]
    return {"v_min": v_min, "v_max": v_max, "i_cont": i_cont, "i_pico": i_pico}


def validar_controlador(controlador, resumo):
    alertas = [
        (controlador["v_min"] > 0 and resumo["v_min"] < controlador["v_min"], st.warning, f"⚠️ Tensão mínima do pack ({resumo['v_min']:.1f}V) abaixo da mínima do controlador ({controlador['v_min']:.1f}V)."),
        (controlador["v_max"] > 0 and resumo["v_max"] > controlador["v_max"], st.warning, f"⚠️ Tensão máxima do pack ({resumo['v_max']:.1f}V) acima da máxima do controlador ({controlador['v_max']:.1f}V)."),
        (controlador["i_cont"] > 0 and resumo["i_max"] > controlador["i_cont"], st.warning, f"⚠️ Corrente requerida ({resumo['i_max']:.1f}A) acima da corrente contínua do controlador ({controlador['i_cont']:.1f}A)."),
        (controlador["i_pico"] > 0 and resumo["i_max"] > controlador["i_pico"], st.error, f"❌ Corrente requerida ({resumo['i_max']:.1f}A) acima da corrente pico do controlador ({controlador['i_pico']:.1f}A)."),
    ]
    for condicao, funcao, mensagem in alertas:
        if condicao:
            funcao(mensagem)


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
tipo = st.radio("Este projeto é retrofit?", ["Sim, é retrofit", "Não, é projeto novo"], horizontal=True)
retrofit = tipo == "Sim, é retrofit"

if retrofit:
    tensao, autonomia, fator, motores, auxiliares, ah_minimo_retrofit, retro = mostrar_retrofit()
else:
   tensao, autonomia, fator, motores, controlador_df, auxiliares, ah_minimo_retrofit, retro = mostrar_projeto_novo()

controlador = mostrar_controlador()

secao("5. Seleção da célula")
modo = st.selectbox("Seleção de célula", ["Automática"] + [f"{c['fabricante']} {c['modelo']} - {c['ah']}Ah" for c in CELULAS])

if st.button("Dimensionar bateria", type="primary"):
    resumo, opcoes = calcular_opcoes(tensao, autonomia, fator, motores, auxiliares, ah_minimo_retrofit)

    if resumo["i_max"] <= 0 and not retrofit:
        st.error("Informe pelo menos uma potência ou corrente nos motores/componentes.")
        st.stop()

    validar_controlador(controlador, resumo)
    escolhida = escolher_celula(modo, opcoes, resumo)

    if escolhida is None:
        st.error("Nenhuma célula atende aos critérios informados.")
        st.stop()

    st.markdown(
        '<div class="alerta"><b>Observação técnica:</b> este é um pré-dimensionamento. '
        'Em retrofit, a capacidade mínima usa a equivalência chumbo x LiFePO4. '
        'Em projeto novo, o cálculo considera potência, corrente, autonomia, controlador e fator médio real de consumo.</div>',
        unsafe_allow_html=True,
    )

    if retrofit:
        secao("Resultado da análise retrofit")
        exibir_metricas([
            ("🔋 Chumbo nominal", f"{retro['ah_chumbo']:.0f} Ah"),
            ("📉 Ah real entregue chumbo", f"{retro['ah_real_chumbo']:.1f} Ah"),
            ("✅ Ah mínimo LiFePO4", f"{retro['ah_lfp']:.1f} Ah"),
            ("📦 LiFePO4 recomendado", f"{escolhida['capacidade_pack']:.0f} Ah"),
        ])
    else:
        secao("Resultado do dimensionamento")
        exibir_metricas([
            ("⚡ Potência DC máxima", fmt(resumo["potencia_total"], 0, " W")),
            ("🔌 Corrente máxima", fmt(resumo["i_max"], 1, " A")),
            ("📉 Corrente média real", fmt(resumo["i_media"], 1, " A")),
            ("🔋 Capacidade necessária", fmt(resumo["ah_necessario"], 1, " Ah")),
        ])
        exibir_metricas([
            ("📊 Energia necessária", f"{resumo['kwh_necessario']:.2f} kWh"),
            ("⚙️ Fator médio de consumo", f"{fator}%"),
        ])

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
    ])

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
        ])

        secao("Autonomia")
        exibir_metricas([
            ("⏱️ Autonomia estimada", f"{escolhida['autonomia']:.2f} h"),
            ("🔋 Energia disponível", f"{escolhida['energia_pack']:.2f} kWh"),
        ])

    secao("Comparativo de células")
    st.dataframe(tabela_comparativo(opcoes, resumo), use_container_width=True)
