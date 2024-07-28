import streamlit as st
import pandas as pd
from openai import OpenAI
from collections import Counter
import re

# Função para calcular o NPS
def calcular_nps(respostas):
    """Calcula o NPS com base na lista de respostas."""
    detratores = len([r for r in respostas if r <= 6])
    promotores = len([r for r in respostas if r >= 9])
    neutros    = len([r for r in respostas if r in [7,8]])
    total = len(respostas)
    nps = ((promotores - detratores) / total) * 100
    return nps, promotores, detratores, neutros, total

# Função para analisar o sentimento usando a API da OpenAI
def analisar_sentimento(texto, api_key):
    """Analisa o sentimento de um texto usando a API da OpenAI."""
    client = OpenAI(api_key = api_key)
    resposta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Você é um especilista em análise de sentimento e em NPS - Net Promoter Score."},
            {"role": "user", "content": f"Analise o sentimento do seguinte comentário e categorize-o somente como Positivo, Neutro, ou Negativo. :\n\nComentário: {texto}"},
            {"role": "assistant", "content": ""}
        ]
    )
#    resposta.choices[0].message['content']
    sentimentos = ["Positivo","Negativo","Neutro"]
    padrao = r'\b(?:' + '|'.join(sentimentos) + r')\b'
    resposta_limpa = ''.join(re.findall(padrao, resposta.choices[0].message.content))
    return resposta_limpa

# Interface com Streamlit
st.title("Análise de NPS com OpenAI")

# Carregar arquivo
arquivo_carregado = st.file_uploader(
    "Carregue o arquivo CSV ou Excel com as respostas do NPS:",
    type=["csv", "xlsx"],
)

# Opção para análise de sentimento
analise_sentimento = st.checkbox("Realizar análise de sentimento nos comentários?")

# Campo para inserir a chave da API, apenas se a análise de sentimento estiver marcada
if analise_sentimento:
    api_key = st.text_input("Insira sua chave de API da OpenAI:", type="password")

# Botão para emitir o relatório
if st.button("Emitir Relatório"):
    if arquivo_carregado is not None:
        try:
            # Ler dados do arquivo
            if arquivo_carregado.type == "text/csv":
                df = pd.read_csv(arquivo_carregado)
            else:
                df = pd.read_excel(arquivo_carregado)

            # Calcular o NPS
            nps, promotores, detratores, neutros, total = calcular_nps(df["resposta"])

            # Mostrar resultados do NPS
            st.header("Resultados do NPS")
            col1, col2 = st.columns(2)
            col1.metric("Total Respostas:", f"{total}")
            col2.metric("NPS: ", f"{nps:.2f}")
            col3, col4, col5 = st.columns(3)
            col3.metric("Promotores:", f"{promotores/total*100:.2f}%", f"{promotores} respostas")
            col4.metric("Detratores:", f"{detratores/total*100:.2f}%", f"{detratores} respostas")
            col5.metric("Neutros:", f"{neutros/total*100:.2f}%", f"{neutros} respostas")

            # Análise de sentimento (se habilitada)
            if analise_sentimento and api_key:
                st.header("Análise dos comentários")
                # Aplicar análise de sentimento a cada comentário
                with st.spinner("Analisando comentários..."):  # Mostrar indicador de progresso
                    df["sentimento"] = df["comentario"].apply(
                        lambda texto: analisar_sentimento(texto, api_key) if texto else None
                    )
                st.write(df)
                # Contar o número de sentimentos positivos, negativos e neutros
                sentiment_counts = Counter(df['sentimento'])
                # Gerar a tabela de estatísticas
                stats_df = pd.DataFrame.from_dict(sentiment_counts, orient='index', columns=['Count']).reset_index()
                stats_df.rename(columns={'index': 'Sentiment'}, inplace=True)

                # Função para resumir os principais pontos positivos e negativos
                def summarize_points(sentiment):
                    points = df[df['sentimento'] == sentiment]['comentario'].tolist()
                    client2 = OpenAI(api_key = api_key)
                    response = client2.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Você é um especialista em resumir textos."},
                            {"role": "user", "content": f"Encontre os principais pontos {sentiment}s do seguinte texto:\n\n{points}\nResumo:"}
                        ]
                    )
                    summary = response.choices[0].message.content.strip()
                    return summary

                # Obter resumos dos principais pontos positivos e negativos
                with st.spinner("Resumindo a análise dos comentários..."):  # Mostrar indicador de progresso
                    positive_points = summarize_points('Positivo')
                    negative_points = summarize_points('Negativo')

                # Mostrar os principais pontos positivos e negativos
                st.write("\nPrincipais pontos positivos:")
                st.write(positive_points)

                st.write("\nPrincipais pontos negativos:")
                st.write(negative_points)
                # Salvar a tabela de estatísticas em um arquivo CSV
                stats_file_path = 'nps_sentiment_statistics.csv'
                stats_df.to_csv(stats_file_path, index=False)
                # Salvar o DataFrame atualizado em um novo arquivo CSV
                updated_file_path = 'nps_respostas_com_sentimento.csv'
                df.to_csv(updated_file_path, index=False)
            else:
                st.warning("Análise de sentimento desabilitada ou chave de API não fornecida.")

            # Opção para baixar o relatório (implementação pendente)
            # st.download_button("Baixar Relatório (Markdown)", data="relatorio.md")

        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
    else:
        st.warning("Carregue um arquivo para continuar.")




