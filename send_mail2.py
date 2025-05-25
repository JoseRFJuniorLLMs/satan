import os
# Removido: from dotenv import load_dotenv # satan5.py cuidará disso
import json
from datetime import datetime
# Removido: from openai import OpenAI # Não vamos usar OpenAI
from pydantic import BaseModel, Field
from typing import Optional, Literal, List  # Adicionado List para consistência

# Imports do LangChain necessários para interagir com o Gemini e parsear JSON
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser


# Não é mais necessário, pois satan5.py carregará as variáveis de ambiente
# load_dotenv(override=True)

class EmailAnalysis(BaseModel):
    category: Literal["sponsorship", "business_inquiry", "other"] = Field(..., alias="categoria",
                                                                          description="Categoria do e-mail: 'sponsorship' (patrocínio), 'business_inquiry' (consulta de negócios), ou 'other' (outro).")
    confidence: float = Field(..., alias="confianca", description="Confiança na categorização (entre 0 e 1).")
    reason: str = Field(..., alias="motivo", description="Breve explicação para a categorização.")
    company_name: Optional[str] = Field(None, alias="nome_empresa",
                                        description="Nome da empresa extraído, se aplicável.")
    topic: Optional[str] = Field(None, alias="topico_principal",
                                 description="Tópico ou produto principal mencionado, se aplicável.")


# File paths (nomes traduzidos para consistência com satan5.py)
# Essas constantes serão definidas no satan5.py e os caminhos podem ser passados
# para as funções principais se necessário, ou as funções podem assumir que
# os arquivos de relatório/json têm nomes fixos.
EMAILS_FILE = "emails_para_categorizar.txt"
CATEGORIZED_EMAILS_JSON = "emails_categorizados.json"
OPPORTUNITY_REPORT = "relatorio_de_oportunidades.txt"


# Esta função será removida ou se tornará um placeholder.
# A implementação real estará em satan5.py (satan_send_email_wrapper)
# e será passada como parâmetro para process_responses em email_responder2.py.
def send_email_placeholder(subject, body, recipient_email, gmail_service_instance=None):
    """
    PLACEHOLDER: Esta função será substituída pela implementação em satan5.py.
    """
    print(f"AVISO: Usando send_email_placeholder de send_mail2.py. Deve ser substituída pela função de satan5.py.")
    print(f"   (Simulando envio para: {recipient_email}, Assunto: {subject})")
    return True


# Esta função será removida. A implementação real estará em satan5.py
# e será passada como argumento para sort_emails_and_categorize.
def get_emails_placeholder(gmail_service_instance, hours=72, target_file=EMAILS_FILE):
    """
    PLACEHOLDER: Esta função será substituída pela implementação em satan5.py.
    Ela deveria buscar e-mails e popular o target_file ou retornar uma lista.
    """
    print(f"AVISO: Usando get_emails_placeholder de send_mail2.py. Deve ser substituída pela função de satan5.py.")
    if not os.path.exists(target_file):  # Cria arquivo vazio para read_emails_from_file não falhar
        with open(target_file, "w", encoding="utf-8") as f:
            f.write("")
    return []  # Ou None, dependendo da sua implementação final no satan5.py


def read_emails_from_file(file_path=EMAILS_FILE):
    """Lê e-mails do arquivo especificado (populado por satan5.py) e retorna como uma lista de dicionários."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Arquivo {file_path} não encontrado para leitura. Retornando lista vazia.")
        return []

    emails = []
    current_email = {}
    current_body_lines = []
    for line in lines:
        line = line.rstrip()
        if line.startswith("Assunto: "):
            if current_email:
                current_email["body"] = "\n".join(l for l in current_body_lines if l.strip()).strip()
                emails.append(current_email)
            current_email = {"subject": line[len("Assunto: "):].strip(), "from": "desconhecido"}
            current_body_lines = []
        elif line.startswith("De: "):
            current_email["from"] = line[len("De: "):].strip()
        elif line.startswith("Recebido: "):
            current_email["received"] = line[len("Recebido: "):].strip()
        elif line.startswith("Corpo: "):
            current_body_lines = [line[len("Corpo: "):].strip()]
        elif line.startswith("-" * 50):
            continue
        else:
            if current_body_lines is not None:
                current_body_lines.append(line)
    if current_email.get("subject"):
        current_email["body"] = "\n".join(l for l in current_body_lines if l.strip()).strip()
        emails.append(current_email)
    return emails


def analyze_email_category(llm_client, email_content_dict):
    """Analisa um único e-mail usando o cliente LLM fornecido para categorização."""
    body = email_content_dict.get('body', '').strip()
    subject = email_content_dict.get('subject', 'Sem Assunto')
    sender = email_content_dict.get('from', 'Remetente Desconhecido')

    parser = JsonOutputParser(pydantic_object=EmailAnalysis)

    prompt_template_str = f"""
    Você é um categorizador de e-mails para um profissional chamado Junior. Sua tarefa é categorizar os e-mails recebidos
    e identificar informações importantes.

    E-mail para analisar:
    Assunto: {subject}
    De: {sender}
    Corpo:
    {{corpo_email_snippet}}

    Categorize este e-mail em um dos seguintes:
    1. "sponsorship" - Empresas querendo patrocinar conteúdo ou serviços para Junior.
    2. "business_inquiry" - E-mails relacionados a negócios, ofertas de parceria, oportunidades de marketing para Junior.
    3. "other" - Todo o resto (notificações, spam, pessoais não urgentes, etc.).

    Se for um patrocínio ("sponsorship") ou uma consulta de negócios ("business_inquiry"), extraia o nome da empresa e o tópico/produto principal.
    Para e-mails da categoria "other", os campos "nome_empresa" e "topico_principal" devem ser nulos ou omitidos.
    Responda com um objeto JSON que siga este schema. As instruções de formato JSON são:
    {{format_instructions}}
    Não adicione nenhum texto antes ou depois do objeto JSON.
    """
    prompt = ChatPromptTemplate.from_template(
        template=prompt_template_str,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    chain = prompt | llm_client | parser

    try:
        email_body_for_prompt = body[:3800]
        analysis_result = chain.invoke({"corpo_email_snippet": email_body_for_prompt})
        if analysis_result:
            print(f"\nAnalisando com Gemini (Categoria): {subject}")
            print(f"Resultado da análise: {json.dumps(analysis_result, indent=2, ensure_ascii=False)}")
            return EmailAnalysis(**analysis_result)
        else:
            print(f"Resposta vazia do Gemini para o e-mail (Categoria): {subject}")
            return None
    except Exception as e:
        print(f"Erro ao analisar e-mail com Gemini (Categoria): {e}")
        print(f"E-mail com falha (assunto): {subject}")
        import traceback
        traceback.print_exc()
        return None


# Função principal que será importada pelo satan5.py
def sort_emails_and_categorize_external(
        llm_client,
        get_emails_function_from_satan,
        gmail_service_instance,
        path_emails_file=EMAILS_FILE,  # Caminhos podem ser passados de satan5.py
        path_categorized_json=CATEGORIZED_EMAILS_JSON
):
    """Função principal para categorizar e-mails, usando funções externas para acesso ao Gmail."""
    print("Buscando novos e-mails para categorização (via função de satan5.py)...")
    # get_emails_function_from_satan deve popular o path_emails_file
    get_emails_function_from_satan(gmail_service_instance, hours=72, target_file=path_emails_file,
                                   query_extras="in:inbox OR in:spam")  # Exemplo de query_extras

    emails_to_process = read_emails_from_file(path_emails_file)
    if not emails_to_process:
        msg = f"Nenhum e-mail encontrado em '{path_emails_file}' para processar."
        print(msg)
        return msg

    sponsorship_emails = []
    business_emails = []
    other_emails = []

    for email_item in emails_to_process:
        if not isinstance(email_item, dict) or not email_item.get('subject') or not email_item.get('body'):
            print(f"Aviso: Item de e-mail malformado em send_mail2.py, pulando: {email_item}")
            continue
        analysis = analyze_email_category(llm_client, email_item)
        if analysis:
            email_data = {
                "subject": email_item["subject"],
                "from": email_item["from"],
                "received": email_item.get("received", datetime.now().isoformat()),
                "body": email_item["body"],
                "analysis": analysis.model_dump(by_alias=True)
            }
            if analysis.category == "sponsorship":
                sponsorship_emails.append(email_data)
            elif analysis.category == "business_inquiry":
                business_emails.append(email_data)
            else:
                other_emails.append(email_data)

    output_data = {
        "ultima_atualizacao": datetime.now().isoformat(),
        "emails_patrocinio": sponsorship_emails,
        "consultas_negocios": business_emails,
        "outros_emails": other_emails
    }
    with open(path_categorized_json, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    summary_text = (
        f"\nProcessados {len(emails_to_process)} e-mails para categorização.\n"
        f"Pedidos de patrocínio: {len(sponsorship_emails)}\n"
        f"Consultas de negócios: {len(business_emails)}\n"
        f"Outros e-mails: {len(other_emails)}\n"
        f"Resultados detalhados salvos em: {path_categorized_json}"
    )
    print(summary_text)
    return summary_text


# Função principal que será importada pelo satan5.py
def generate_opportunity_report_external(llm_client, categorized_emails_path=CATEGORIZED_EMAILS_JSON,
                                         opportunity_report_path=OPPORTUNITY_REPORT):
    """Gera um relatório estruturado destacando oportunidades de negócios valiosas."""
    try:
        with open(categorized_emails_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        msg = f"Erro: Arquivo de e-mails categorizados '{categorized_emails_path}' não encontrado. Execute a categorização primeiro."
        print(msg)
        return msg
    except Exception as e:
        msg = f"Erro ao ler arquivo de e-mails categorizados: {e}"
        print(msg)
        return msg

    business_emails = data.get("consultas_negocios", [])
    sponsorship_emails = data.get("emails_patrocinio", [])
    all_relevant_emails = business_emails + sponsorship_emails

    if not all_relevant_emails:
        msg = "Nenhum e-mail de negócios ou patrocínio encontrado para gerar relatório de oportunidades."
        print(msg)
        return msg

    print("\nAnalisando e-mails de negócios e patrocínio para oportunidades de qualidade com Gemini...")

    email_summaries_for_prompt = []
    for email in all_relevant_emails:
        analysis_data = email.get("analysis", {})  # Lidar com caso de 'analysis' ausente
        summary = {
            "categoria": analysis_data.get("categoria"),
            "de": email.get("from", "N/A"),
            "assunto": email.get("subject", "N/A"),
            "empresa": analysis_data.get("nome_empresa"),
            "topico": analysis_data.get("topico_principal"),
            "confianca_categorizacao": analysis_data.get("confianca"),
            "trecho_corpo": email.get("body", "")[:300] + "..." if len(email.get("body", "")) > 300 else email.get(
                "body", "")
        }
        email_summaries_for_prompt.append(summary)

    prompt_content = f"""
    Você é um assistente executivo para Junior, encarregado de filtrar e-mails de negócios e patrocínio para identificar as oportunidades de maior qualidade.

    Por favor, analise estes {len(all_relevant_emails)} e-mails (sumarizados abaixo em formato JSON) e crie um relatório estruturado em português que:

    1. Categorize cada um como "Alto Valor" ou "Marketing em Massa/Genérico".
    2. Para os de "Alto Valor", forneça uma breve justificativa e classifique-os em ordem de prioridade para Junior.
    3. Para os de "Marketing em Massa/Genérico", apenas liste-os brevemente.

    Aqui estão os sumários dos e-mails para analisar:
    {json.dumps(email_summaries_for_prompt, indent=2, ensure_ascii=False)}

    Considere os seguintes critérios para avaliar as oportunidades:
    1. Personalização: O e-mail é especificamente endereçado a Junior ou menciona seu trabalho específico?
    2. Autenticidade: Parece um contato genuíno ou um e-mail em massa?
    3. Relevância: O tópico ou oferta se alinha com os interesses ou trabalho de Junior?
    4. Reputação: A empresa ou pessoa é conhecida ou parece estabelecida?
    5. Especificidade: A solicitação ou oportunidade é clara e detalhada?

    Formate seu relatório com seções claras (ex: "Oportunidades de Alto Valor", "Marketing em Massa/Genérico").
    Priorize oportunidades que pareçam únicas, personalizadas e valiosas para Junior.
    """
    try:
        response_message = llm_client.invoke(prompt_content)
        report = response_message.content

        print("\n" + "=" * 50)
        print("RELATÓRIO DE OPORTUNIDADES DE NEGÓCIOS E PATROCÍNIO (GERADO PELO GEMINI)")
        print("=" * 50 + "\n")
        print(report)

        with open(opportunity_report_path, "w", encoding="utf-8") as f:
            f.write("RELATÓRIO DE OPORTUNIDADES DE NEGÓCIOS E PATROCÍNIO (GERADO PELO GEMINI)\n")
            f.write("=" * 50 + "\n\n")
            f.write(report)

        print(f"\nRelatório salvo em {opportunity_report_path}")
        return f"Relatório de oportunidades gerado e salvo em '{opportunity_report_path}'.\nPrimeira parte do relatório: {report[:200]}..."
    except Exception as e:
        msg = f"Erro ao gerar relatório de oportunidades com Gemini: {e}"
        print(msg)
        import traceback
        traceback.print_exc()
        return msg

# Removido o if __name__ == "__main__":
# Este script agora é um módulo a ser importado e suas funções chamadas por satan5.py