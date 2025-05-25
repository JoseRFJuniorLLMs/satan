import os
import json
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Literal, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser


# load_dotenv removido

class EmailAnalysis(BaseModel):
    category: Literal["sponsorship", "business_inquiry", "other"] = Field(..., alias="categoria")
    confidence: float = Field(..., alias="confianca")
    reason: str = Field(..., alias="motivo")
    company_name: Optional[str] = Field(None, alias="nome_empresa")
    topic: Optional[str] = Field(None, alias="topico_principal")


# Constantes de nome de arquivo removidas, serão passadas como parâmetro

# Função send_email_placeholder removida (a real estará em satan5.py)
# Função get_emails_placeholder removida (a real estará em satan5.py)

def read_emails_from_file_internal(file_path):  # Renomeada
    """Lê e-mails do arquivo especificado (populado por satan5.py) e retorna lista de dicionários."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Arquivo {file_path} não encontrado para leitura. Retornando lista vazia.")
        return []
    emails = [];
    current_email = {};
    current_body_lines = []
    for line in lines:
        line = line.rstrip()
        if line.startswith("Assunto: "):
            if current_email: current_email["body"] = "\n".join(
                l for l in current_body_lines if l.strip()).strip(); emails.append(current_email)
            current_email = {"subject": line[len("Assunto: "):].strip(), "from": "desconhecido"};
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
            if current_body_lines is not None: current_body_lines.append(line)
    if current_email.get("subject"): current_email["body"] = "\n".join(
        l for l in current_body_lines if l.strip()).strip(); emails.append(current_email)
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
    E-mail para analisar: Assunto: {subject}, De: {sender}, Corpo: {{corpo_email_snippet}}
    Categorize em: "sponsorship", "business_inquiry", ou "other".
    Se sponsorship/business_inquiry, extraia nome da empresa e tópico. Para "other", nome_empresa e topico_principal devem ser nulos.
    Responda JSON com: {{format_instructions}}. Não adicione texto antes ou depois do JSON.
    """
    prompt = ChatPromptTemplate.from_template(template=prompt_template_str, partial_variables={
        "format_instructions": parser.get_format_instructions()})
    chain = prompt | llm_client | parser
    try:
        email_body_for_prompt = body[:3800]
        analysis_result = chain.invoke({"corpo_email_snippet": email_body_for_prompt})
        if analysis_result:
            print(f"\nAnalisando com Gemini (Categoria): {subject}")
            print(f"Resultado da análise: {json.dumps(analysis_result, indent=2, ensure_ascii=False)}")
            return EmailAnalysis(**analysis_result)
        return None
    except Exception as e:
        print(f"Erro ao analisar e-mail com Gemini (Categoria): {e}\nE-mail com falha: {subject}");
        import traceback;
        traceback.print_exc();
        return None


def sort_emails_and_categorize_external(
        llm_client,
        get_emails_function_from_satan,
        gmail_service_instance,
        path_emails_file: str,  # Caminho passado por satan5.py
        path_categorized_json: str  # Caminho passado por satan5.py
):
    """Função principal para categorizar e-mails."""
    print(f"Buscando novos e-mails para categorização (para salvar em '{path_emails_file}')...")
    get_emails_function_from_satan(gmail_service_instance, hours=72, target_file=path_emails_file,
                                   query_extras="in:inbox OR in:spam")

    emails_to_process = read_emails_from_file_internal(path_emails_file)  # Usa a função interna de leitura
    if not emails_to_process:
        msg = f"Nenhum e-mail encontrado em '{path_emails_file}' para processar."
        print(msg);
        return msg

    sponsorship_emails, business_emails, other_emails = [], [], []
    for email_item in emails_to_process:
        if not isinstance(email_item, dict) or not email_item.get('subject') or not email_item.get('body'):
            print(f"Aviso: Item de e-mail malformado, pulando: {email_item}");
            continue
        analysis = analyze_email_category(llm_client, email_item)
        if analysis:
            email_data = {
                "subject": email_item["subject"], "from": email_item["from"],
                "received": email_item.get("received", datetime.now().isoformat()),
                "body": email_item["body"], "analysis": analysis.model_dump(by_alias=True)
            }
            if analysis.categoria == "sponsorship":
                sponsorship_emails.append(email_data)  # Usa alias
            elif analysis.categoria == "business_inquiry":
                business_emails.append(email_data)  # Usa alias
            else:
                other_emails.append(email_data)

    output_data = {"ultima_atualizacao": datetime.now().isoformat(), "emails_patrocinio": sponsorship_emails,
                   "consultas_negocios": business_emails, "outros_emails": other_emails}
    with open(path_categorized_json, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    summary_text = (
        f"\nProcessados {len(emails_to_process)} e-mails para categorização.\nPedidos de patrocínio: {len(sponsorship_emails)}\nConsultas de negócios: {len(business_emails)}\nOutros e-mails: {len(other_emails)}\nResultados detalhados salvos em: {path_categorized_json}")
    print(summary_text);
    return summary_text


def generate_opportunity_report_external(
        llm_client,
        categorized_emails_path: str,  # Caminho passado por satan5.py
        opportunity_report_path: str  # Caminho passado por satan5.py
):
    """Gera um relatório estruturado destacando oportunidades de negócios valiosas."""
    try:
        with open(categorized_emails_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        msg = f"Erro: Arquivo '{categorized_emails_path}' não encontrado. Execute a categorização primeiro."
        print(msg);
        return msg
    except Exception as e:
        msg = f"Erro ao ler '{categorized_emails_path}': {e}"; print(msg); return msg

    business_emails = data.get("consultas_negocios", [])
    sponsorship_emails = data.get("emails_patrocinio", [])
    all_relevant_emails = business_emails + sponsorship_emails
    if not all_relevant_emails:
        msg = "Nenhum e-mail de negócios ou patrocínio para gerar relatório.";
        print(msg);
        return msg

    print("\nAnalisando e-mails para oportunidades com Gemini...")
    email_summaries_for_prompt = []
    for email in all_relevant_emails:
        analysis_data = email.get("analysis", {})
        summary = {
            "categoria": analysis_data.get("categoria"), "de": email.get("from", "N/A"),
            "assunto": email.get("subject", "N/A"), "empresa": analysis_data.get("nome_empresa"),
            "topico": analysis_data.get("topico_principal"),
            "confianca_categorizacao": analysis_data.get("confianca"),
            "trecho_corpo": email.get("body", "")[:300] + "..." if len(email.get("body", "")) > 300 else email.get(
                "body", "")
        }
        email_summaries_for_prompt.append(summary)

    prompt_content = f"""
    Você é um assistente executivo para Junior... (resto do prompt traduzido como antes)...
    E-mails: {json.dumps(email_summaries_for_prompt, indent=2, ensure_ascii=False)}
    ... (resto do prompt traduzido como antes)...
    """
    try:
        response_message = llm_client.invoke(prompt_content)
        report = response_message.content
        print("\n" + "=" * 50 + "\nRELATÓRIO DE OPORTUNIDADES (GEMINI)\n" + "=" * 50 + "\n" + report)
        with open(opportunity_report_path, "w", encoding="utf-8") as f:
            f.write(
                "RELATÓRIO DE OPORTUNIDADES DE NEGÓCIOS E PATROCÍNIO (GERADO PELO GEMINI)\n" + "=" * 50 + "\n\n" + report)
        print(f"\nRelatório salvo em {opportunity_report_path}")
        return f"Relatório de oportunidades gerado. Detalhes em '{opportunity_report_path}'. Prévia: {report[:200]}..."
    except Exception as e:
        msg = f"Erro ao gerar relatório de oportunidades com Gemini: {e}";
        print(msg);
        import traceback;
        traceback.print_exc();
        return msg