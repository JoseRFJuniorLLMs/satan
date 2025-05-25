import os
import json
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import re

# Imports do LangChain necessários para interagir com o Gemini e parsear JSON
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser


# Não há mais load_dotenv aqui

class EmailImportance(BaseModel):
    importance: Literal["high", "medium", "low"] = Field(..., alias="importancia")
    reason: str = Field(..., alias="motivo")
    needs_response: bool = Field(..., alias="precisa_resposta")
    time_sensitive: bool = Field(..., alias="sensivel_ao_tempo")
    topics: List[str] = Field(..., alias="topicos")


# REMOVIDAS AS CONSTANTES GLOBAIS DE NOME DE ARQUIVO DESTE MÓDULO
# RESPONSE_HISTORY_FILE = "historico_respostas_email.json"
# NEEDS_RESPONSE_JSON = "emails_precisam_resposta.json"
# NEEDS_RESPONSE_REPORT = "relatorio_precisam_resposta.txt"
# RECENT_EMAILS_FILE será o path_recent_emails_file


def load_response_history(history_file_path):  # Aceita o caminho como parâmetro
    """Carrega o histórico de e-mails aos quais já respondemos."""
    try:
        with open(history_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "emails_respondidos" not in data or not isinstance(data["emails_respondidos"], list):
                return {"emails_respondidos": []}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"emails_respondidos": []}


def save_response_history(new_response_data, history_file_path):  # Aceita o caminho
    """Salva um novo registro no histórico de e-mails respondidos."""
    history = load_response_history(history_file_path)
    history["emails_respondidos"].append(new_response_data)
    try:
        with open(history_file_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"Histórico de resposta salvo em {history_file_path} para: {new_response_data.get('assunto_original')}")
    except Exception as e:
        print(f"Erro ao salvar histórico de respostas: {e}")


def is_previously_responded(email_to_check, sent_emails_list):
    """Verifica se já respondemos a este e-mail olhando os itens enviados."""
    from_match = re.search(r'<(.+?)>', email_to_check.get('from', ''))
    sender_email = from_match.group(1).lower().strip() if from_match else None
    if not sender_email: return False
    subject_to_check = email_to_check.get('subject', '').lower()
    clean_subject_to_check = re.sub(r'^(?:re|fwd|enc|res):\s*', '', subject_to_check, flags=re.IGNORECASE).strip()
    for sent_email_info in sent_emails_list:
        recipients_lower = [r.lower().strip() for r in sent_email_info.get('recipients', []) if isinstance(r, str)]
        if sender_email in recipients_lower:
            sent_subject_lower = sent_email_info.get('subject', '').lower()
            clean_sent_subject = re.sub(r'^(?:re|fwd|enc|res):\s*', '', sent_subject_lower, flags=re.IGNORECASE).strip()
            if clean_subject_to_check and clean_sent_subject and \
                    (clean_subject_to_check == clean_sent_subject or \
                     clean_subject_to_check in clean_sent_subject or \
                     clean_sent_subject in clean_subject_to_check):
                return True
    return False


def read_emails_from_file_internal(file_path):
    """Lê e-mails do arquivo especificado e retorna como uma lista de dicionários."""
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


def analyze_email_importance(llm_client, email_content_dict):
    """Analisa a importância de um único e-mail usando o cliente LLM fornecido."""
    body = email_content_dict.get('body', '').strip()
    subject = email_content_dict.get('subject', 'Sem Assunto')
    sender = email_content_dict.get('from', 'Remetente Desconhecido')
    received_date = email_content_dict.get('received', 'data desconhecida')
    parser = JsonOutputParser(pydantic_object=EmailImportance)
    prompt_template_str = f"""
    Você é um analisador de importância de e-mails para um profissional ocupado chamado Junior.
    Sua tarefa é determinar quais e-mails PRECISAM CRITICAMENTE de uma resposta e quais podem ser ignorados.
    SEJA EXTREMAMENTE SELETIVO - apenas marque e-mails como precisando de resposta se eles forem:
    1. De pessoas reais (não sistemas automatizados ou notificações genéricas).
    2. Personalizados e direcionados a Junior (não marketing em massa ou newsletters genéricas).
    3. Requerem ação específica, entrada ou uma decisão de Junior.
    4. Possuem claro valor comercial, oportunidade substancial, ou são de contatos importantes/estratégicos.
    5. São urgentes ou sensíveis ao tempo.
    Notificações automatizadas (ex: atualizações de redes sociais, logins, alertas de sistema), newsletters em massa,
    e-mails de marketing genéricos DEVEM SEMPRE ser marcados como não precisando de resposta e baixa importância.
    E-mail para analisar:
    Assunto: {subject}
    De: {sender}
    Recebido: {received_date}
    Corpo: {{corpo_email_snippet}}
    Classifique a importância: "high" (alta), "medium" (média), "low" (baixa).
    SEJA RIGOROSO sobre "needs_response" (precisa_resposta) - apenas marque como VERDADEIRO (true) se o e-mail absolutamente exigir atenção e resposta pessoal de Junior.
    Considere o nome do remetente ao avaliar a importância.
    Responda com um objeto JSON que siga este schema. As instruções de formato JSON são: {{format_instructions}}
    Não adicione nenhum texto antes ou depois do objeto JSON.
    """
    prompt = ChatPromptTemplate.from_template(template=prompt_template_str, partial_variables={
        "format_instructions": parser.get_format_instructions()})
    chain = prompt | llm_client | parser
    try:
        email_body_for_prompt = body[:3800]
        analysis_result = chain.invoke({"corpo_email_snippet": email_body_for_prompt})
        if analysis_result:
            print(f"\nAnalisando com Gemini (Importância): {subject}")
            print(f"Resultado da análise: {json.dumps(analysis_result, indent=2, ensure_ascii=False)}")
            return EmailImportance(**analysis_result)
        return None
    except Exception as e:
        print(f"Erro ao analisar e-mail com Gemini (Importância): {e}\nE-mail com falha (assunto): {subject}");
        import traceback;
        traceback.print_exc();
        return None


def find_important_emails_external(
        llm_client,
        get_emails_function_from_satan,
        get_sent_emails_function_from_satan,
        gmail_service_instance,
        # Caminhos dos arquivos agora são passados como argumentos
        path_recent_emails_file: str,
        path_needs_response_json: str,
        path_needs_response_report: str,
        path_response_history: str
):
    """Identifica e-mails importantes, utilizando funções e caminhos de arquivo fornecidos."""
    print(f"Iniciando busca de e-mails importantes (últimas 24 horas) para salvar em '{path_recent_emails_file}'...")
    get_emails_function_from_satan(gmail_service_instance, hours=24, target_file=path_recent_emails_file,
                                   query_extras="in:inbox")
    emails_to_process = read_emails_from_file_internal(path_recent_emails_file)  # Usa a função interna

    print(f"Verificando e-mails enviados nos últimos 7 dias...")
    sent_emails = get_sent_emails_function_from_satan(gmail_service_instance, days=7)

    if not emails_to_process:
        msg = f"Nenhum e-mail encontrado em '{path_recent_emails_file}' para processar."
        print(msg);
        return msg

    needs_response_emails = []
    for email_item in emails_to_process:
        if not isinstance(email_item, dict) or not email_item.get('subject') or not email_item.get('body'):
            print(f"Aviso: Item de e-mail malformado, pulando: {email_item}");
            continue
        already_responded = is_previously_responded(email_item, sent_emails)
        analysis = analyze_email_importance(llm_client, email_item)
        if analysis and analysis.precisa_resposta:  # Acessa o alias 'precisa_resposta'
            email_data = {
                "subject": email_item["subject"], "from": email_item["from"],
                "received": email_item.get("received", datetime.now().isoformat()),
                "body": email_item["body"][:1000] + ("..." if len(email_item["body"]) > 1000 else ""),
                "analysis": analysis.model_dump(by_alias=True), "already_responded": already_responded
            }
            needs_response_emails.append(email_data)

    output_data = {"ultima_atualizacao": datetime.now().isoformat(),
                   "emails_que_precisam_resposta": needs_response_emails}
    with open(path_needs_response_json, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\nProcessados {len(emails_to_process)} e-mails.")
    already_responded_count = sum(1 for e in needs_response_emails if e["already_responded"])
    newly_needs_response_count = len(needs_response_emails) - already_responded_count
    print(
        f"E-mails que requerem resposta: {len(needs_response_emails)} (Novos: {newly_needs_response_count}, Já respondidos: {already_responded_count})")
    print(f"Resultados detalhados salvos em: {path_needs_response_json}")

    report_content = f"==================================================\nE-MAILS QUE REQUEREM RESPOSTA (ANÁLISE PELO GEMINI)\nGerado em: {datetime.now().isoformat()}\n==================================================\n\n"
    if needs_response_emails:
        sorted_emails = sorted(needs_response_emails, key=lambda x: (
        x["already_responded"], not x['analysis']['sensivel_ao_tempo'],
        0 if x['analysis']['importancia'] == 'high' else 1 if x['analysis']['importancia'] == 'medium' else 2))
        for email_item in sorted_emails:
            report_content += f"Assunto: {email_item['subject']}\nDe: {email_item['from']}\nRecebido: {email_item['received']}\nImportância: {email_item['analysis']['importancia'].upper()}\nSensível ao Tempo: {'SIM' if email_item['analysis']['sensivel_ao_tempo'] else 'NÃO'}\nTópicos: {', '.join(email_item['analysis']['topicos'])}\nMotivo: {email_item['analysis']['motivo']}\n"
            if email_item["already_responded"]: report_content += f"STATUS: ✅ JÁ RESPONDIDO\n"
            report_content += f"Prévia: {email_item['body'][:300]}...\n\n" + "-" * 50 + "\n\n"
    else:
        report_content += "Nenhum e-mail que requer resposta imediata foi encontrado.\n\n"
    with open(path_needs_response_report, "w", encoding="utf-8") as f:
        f.write(report_content)

    if needs_response_emails:
        print("\nRESUMO DOS E-MAILS QUE REQUEREM RESPOSTA (ANÁLISE PELO GEMINI):\n" + "=" * 50)
        for email_item in sorted_emails:
            print(
                f"\nAssunto: {email_item['subject']}\nDe: {email_item['from']}\nImportância: {email_item['analysis']['importancia'].upper()}")
            if email_item["already_responded"]: print(f"STATUS: ✅ JÁ RESPONDIDO")
            print("-" * 30)
    else:
        print("\nNenhum e-mail que requer resposta imediata foi encontrado.")
    print(f"\nRelatório completo disponível em {path_needs_response_report}")
    return f"Análise de importância concluída. {len(needs_response_emails)} e-mails marcados para resposta, {newly_needs_response_count} são novos. Detalhes em {path_needs_response_report}."