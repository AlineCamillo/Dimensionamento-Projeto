import streamlit as st

st.set_page_config(page_title="Teste", page_icon="🚀")

st.title("🚀 TESTE DE ATUALIZAÇÃO")

st.success("Se você está vendo esta mensagem, o GitHub e o Streamlit atualizaram corretamente.")

nome = st.text_input("Digite seu nome:")

if nome:
    st.write(f"Olá, {nome}!")

if st.button("Clique aqui"):
    st.balloons()
    st.success("Funcionou!")

