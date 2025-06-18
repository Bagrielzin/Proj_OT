import streamlit as st
import pulp as plp
import pandas as pd

st.title("Programação Linear com até 4 Variáveis")

# Escolha do número de variáveis
num_vars = st.selectbox("Número de variáveis", [2, 3, 4])
f_obj = st.radio("Tipo de função objetivo", ["max", "min"])

# Criação das variáveis
vars_lp = [plp.LpVariable(f'x{i+1}', lowBound=0, cat='Continuous') for i in range(num_vars)]
prob = plp.LpProblem("Problema_PL", plp.LpMaximize if f_obj == "max" else plp.LpMinimize)

# Coeficientes da função objetivo
st.subheader("Função Objetivo")
cols = st.columns(num_vars)
obj_coefs = [cols[i].number_input(f"Coeficiente de x{i+1}", key=f"obj_{i}", value=1.0) for i in range(num_vars)]
prob += plp.lpDot(obj_coefs, vars_lp)

# Restrições
st.subheader("Restrições")
num_rest = st.number_input("Número de restrições", min_value=1, max_value=10, step=1)
if "restricoes_atuais" not in st.session_state:
    st.session_state.restricoes_atuais = [
        {"coefs": [1.0]*num_vars, "operador": "<=", "valor": 1.0}
        for _ in range(int(num_rest))
    ]

# Atualizar restrições se número for alterado
if len(st.session_state.restricoes_atuais) != int(num_rest):
    st.session_state.restricoes_atuais = [
        {"coefs": [1.0]*num_vars, "operador": "<=", "valor": 1.0}
        for _ in range(int(num_rest))
    ]

# Exibir e montar restrições
restricoes = []
for r in range(int(num_rest)):
    st.markdown(f"**Restrição {r+1}**")
    restr_cols = st.columns(num_vars + 2)
    coefs = [restr_cols[i].number_input(
        f"x{i+1}_r{r}", key=f"r{r}_x{i}", value=st.session_state.restricoes_atuais[r]["coefs"][i]
    ) for i in range(num_vars)]
    operador = restr_cols[num_vars].selectbox("Operador", ["<=", ">=", "=="], key=f"op{r}", index=["<=", ">=", "=="].index(st.session_state.restricoes_atuais[r]["operador"]))
    valor = restr_cols[num_vars + 1].number_input("Valor", key=f"val{r}", value=st.session_state.restricoes_atuais[r]["valor"])
    restricoes.append((coefs, operador, valor))
    st.session_state.restricoes_atuais[r] = {"coefs": coefs, "operador": operador, "valor": valor}

for i, (coefs, operador, valor) in enumerate(restricoes):
    expr = plp.lpDot(coefs, vars_lp)
    if operador == "<=":
        prob += expr <= valor, f"R{i}"
    elif operador == ">=":
        prob += expr >= valor, f"R{i}"
    else:
        prob += expr == valor, f"R{i}"

# Resolver
if st.button("Resolver"):
    resultado = prob.solve()
    status = plp.LpStatus[prob.status]
    st.subheader("Resultado")
    st.write(f"Status da solução: **{status}**")

    if status == "Optimal":
        for var in vars_lp:
            st.write(f"{var.name} = {var.varValue}")
        st.write(f"Valor ótimo da função objetivo: **{plp.value(prob.objective)}**")

        st.subheader("Análise de Sensibilidade das Restrições")
        dados = []
        for nome, c in prob.constraints.items():
            dados.append({
                "Restrição": nome,
                "Preço sombra": c.pi,
                "Folga": c.slack
            })
        st.dataframe(pd.DataFrame(dados))

    elif status == "Infeasible":
        st.error("O problema é inviável: não existe nenhuma solução que satisfaça todas as restrições.")
    elif status == "Unbounded":
        st.error("O problema é ilimitado: a função objetivo pode crescer indefinidamente.")
    else:
        st.warning("Não foi possível resolver o problema.")

# Modificar restrições e resolver manualmente com botão
with st.expander("🔧 Modificar Restrições"):
    st.write("Modifique os valores das restrições abaixo. Clique em 'Nova Solução' para resolver novamente.")

    novas_restricoes = []
    for r in range(int(num_rest)):
        st.markdown(f"**Nova Restrição {r+1}**")
        restr_cols = st.columns(num_vars + 2)
        coefs = [restr_cols[i].number_input(f"mod_r{r}_x{i}", key=f"mod_r{r}_x{i}", value=st.session_state.restricoes_atuais[r]["coefs"][i]) for i in range(num_vars)]
        operador = restr_cols[num_vars].selectbox("Operador", ["<=", ">=", "=="], key=f"mod_op{r}", index=["<=", ">=", "=="].index(st.session_state.restricoes_atuais[r]["operador"]))
        valor = restr_cols[num_vars + 1].number_input("Valor", key=f"mod_val{r}", value=st.session_state.restricoes_atuais[r]["valor"])
        novas_restricoes.append((coefs, operador, valor))

    if st.button("Nova Solução"):
        prob.constraints.clear()
        for i, (coefs, operador, valor) in enumerate(novas_restricoes):
            expr = plp.lpDot(coefs, vars_lp)
            if operador == "<=":
                prob += expr <= valor, f"ModR{i}"
            elif operador == ">=":
                prob += expr >= valor, f"ModR{i}"
            else:
                prob += expr == valor, f"ModR{i}"

        novo_resultado = prob.solve()
        novo_status = plp.LpStatus[prob.status]
        st.subheader("Resultado com Novas Restrições")
        st.write(f"Status da nova solução: **{novo_status}**")

        if novo_status == "Optimal":
            for var in vars_lp:
                st.write(f"{var.name} = {var.varValue}")
            st.write(f"Novo valor ótimo da função objetivo: **{plp.value(prob.objective)}**")

            dados = []
            for nome, c in prob.constraints.items():
                dados.append({
                    "Restrição": nome,
                    "Preço sombra": c.pi,
                    "Folga": c.slack
                })
            st.dataframe(pd.DataFrame(dados))

        elif novo_status == "Infeasible":
            st.error("As novas restrições tornaram o problema inviável.")
        elif novo_status == "Unbounded":
            st.error("O problema modificado é ilimitado.")
        else:
            st.warning("Não foi possível resolver o problema com as novas restrições.")