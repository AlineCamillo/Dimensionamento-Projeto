import streamlit as st

st.set_page_config(
    page_title="Dimensionamento FullEnergy",
    page_icon="🔋",
    layout="wide"
)

st.markdown("""
<style>
.main {
    background-color: #f7f7f5;
}
.block-container {
    padding-top: 2rem;
}
.header {
    background: linear-gradient(90deg, #111111, #2b2b2b);
    padding: 28px;
    border-radius: 18px;
    border-bottom: 5px solid #FFD400;
}
.header h1 {
    color: white;
    margin-bottom: 5px;
}
.header p {
    color: #d8d8d8;
    font-size: 17px;
}
.card {
    background-color: white;
    padding: 24px;
    border-radius: 16px;
    border: 1px solid #e6e6e6;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
}
.resultado {
    background-color: #fff8d6;
    padding: 20px;
    border-radius: 14px;
    border-left: 6px solid #FFD400;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <h1>🔋 FULLENERGY | Dimensionamento de Bateria LiFePO4</h1>
    <p>Painel técnico para levantamento inicial de dados e pré-dimensionamento de baterias de lítio.</p>
</div>
""", unsafe_allow_html=True)

st.write("")

st.subheader("1. Tipo de projeto")

tipo_projeto = st.radio(
    "Este projeto é um retrofit?",
    ["Sim, é retrofit", "Não, é projeto novo"],
    horizontal=True
)

st.write("")

if tipo_projeto == "Sim, é retrofit":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Dados da bateria de chumbo atual")

    col1, col2 = st.columns(2)

    with col1:
        tensao_chumbo = st.number_input("Tensão da bateria de chumbo atual (V)", min_value=0, value=48)

    with col2:
        capacidade_chumbo = st.number_input("Capacidade da bateria de chumbo atual (Ah)", min_value=0, value=105)

    observacoes = st.text_area("Observações sobre a aplicação", placeholder="Ex: carrinho de golfe, plataforma, lavadora de piso, empilhadeira...")

    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    if st.button("Gerar pré-análise"):
        st.markdown('<div class="resultado">', unsafe_allow_html=True)
        st.subheader("Pré-análise do retrofit")
        st.write(f"**Tensão atual:** {tensao_chumbo} V")
        st.write(f"**Capacidade atual:** {capacidade_chumbo} Ah")
        st.write("Para retrofit, a primeira referência será manter a tensão nominal do sistema e avaliar a autonomia desejada.")
        st.markdown("</div>", unsafe_allow_html=True)

else:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Dados da máquina / sistema")

    col1, col2 = st.columns(2)

    with col1:
        potencia_maquina = st.number_input("Potência da máquina (W)", min_value=0, value=1000)
        tensao_sistema = st.number_input("Tensão do sistema (V)", min_value=0, value=48)
        corrente_consumo = st.number_input("Corrente de consumo conhecida (A) - se houver", min_value=0.0, value=0.0)

    with col2:
        controlador_min = st.number_input("Faixa mínima de operação do controlador (V)", min_value=0.0, value=40.0)
        controlador_max = st.number_input("Faixa máxima de operação do controlador (V)", min_value=0.0, value=60.0)
        quantidade_motores = st.number_input("Quantidade de motores", min_value=1, value=1)

    componentes = st.text_area(
        "Consumo de componentes particulares",
        placeholder="Ex: bomba hidráulica, inversor, iluminação, módulo eletrônico, ventilador, etc."
    )

    observacoes = st.text_area("Observações gerais da aplicação")

    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    if st.button("Gerar pré-análise"):
        corrente_estimativa = potencia_maquina / tensao_sistema if tensao_sistema > 0 else 0

        st.markdown('<div class="resultado">', unsafe_allow_html=True)
        st.subheader("Pré-análise do projeto novo")

        st.write(f"**Potência informada:** {potencia_maquina} W")
        st.write(f"**Tensão do sistema:** {tensao_sistema} V")
        st.write(f"**Faixa do controlador:** {controlador_min} V até {controlador_max} V")
        st.write(f"**Quantidade de motores:** {quantidade_motores}")

        if corrente_consumo > 0:
            st.write(f"**Corrente informada:** {corrente_consumo:.2f} A")
        else:
            st.write(f"**Corrente estimada:** {corrente_estimativa:.2f} A")

        st.write("Esta é uma análise inicial. Para dimensionamento final, ainda será necessário considerar autonomia desejada, regime de uso, picos de corrente e espaço físico disponível.")
        st.markdown("</div>", unsafe_allow_html=True)
