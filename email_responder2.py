import os
import json
import re
# Removido: from dotenv import load_dotenv
# Removida a importação de send_email de send_mail2.py
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime


# load_dotenv removido

# Constantes de nome de arquivo removidas, serão passadas como parâmetro

def extract_emails_from_report_internal(report_path):  # Renomeada
    """Extrai e-mails do arquivo de relatório especificado."""
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Erro: Arquivo de relatório '{report_path}' não encontrado.");
        return []
    email_sections = content.split("-" * 50);
    emails = []
    for section in email_sections:
        if not section.strip(): continue
        subject_match = re.search(r"Assunto: (.+?)\n", section)
        from_match = re.search(r"De: (.+?)\n", section)
        email_address_match = re.search(r"<(.+?)>", from_match.group(1) if from_match else "")
        preview_match = re.search(r"Prévia: ([\s\S]+?)(?=\n\n-{50}|\n\nSTATUS: ✅ JÁ RESPONDIDO|\n\nMotivo:|$)", section)
        already_responded = "STATUS: ✅ JÁ RESPONDIDO" in section
        if subject_match and from_match:
            from_text = from_match.group(1).strip()
            email_address = email_address_match.group(1).strip() if email_address_match else from_text
            emails.append({
                "subject": subject_match.group(1).strip(), "from": from_text,
                "email_address": email_address,
                "preview": preview_match.group(1).strip() if preview_match else "Prévia não disponível",
                "already_responded": already_responded
            })
    return emails


def save_response_history_internal(new_response_data, history_file_path):  # Renomeada e aceita path
    """Salva um registro de um e-mail ao qual respondemos."""
    history = {"emails_respondidos": []}
    if os.path.exists(history_file_path):
        try:
            with open(history_file_path, "r", encoding="utf-8") as f:
                history = json.load(f)
            if "emails_respondidos" not in history or not isinstance(history["emails_respondidos"], list):
                history["emails_respondidos"] = []
        except json.JSONDecodeError:
            history = {"emails_respondidos": []}
    history["emails_respondidos"].append(
        {"assunto_original": new_response_data["subject"], "remetente_original": new_response_data["from"],
         "respondido_em": new_response_data["responded_at"]})
    try:
        with open(history_file_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"Histórico de resposta salvo em {history_file_path} para: {new_response_data.get('subject')}")
        return True
    except Exception as e:
        print(f"Erro ao salvar histórico de respostas: {e}"); return False


def generate_response_internal(llm_client, email_data, user_name_signature, edit_instructions=None):  # Renomeada
    """Gera uma resposta de e-mail usando o cliente LLM fornecido."""
    original_subject = email_data.get('subject', 'Sem Assunto')
    from_sender = email_data.get('from', 'Remetente Desconhecido')
    preview = email_data.get('preview', 'Conteúdo não disponível')
    if edit_instructions:
        prompt_template_str = f"""
        Reescreva a resposta do e-mail com base nestas instruções, em português:
        E-mail Original: Assunto: {original_subject}, De: {from_sender}, Prévia: {preview[:500]}
        Instruções para reescrever: {{instrucoes_edicao}}
        Sua resposta DEVE manter este formato: Assunto: Re: {original_subject}\n\n[Corpo do e-mail em português]\n\nAtenciosamente,\n{user_name_signature}"""
        input_data = {"instrucoes_edicao": edit_instructions}
    else:
        prompt_template_str = f"""
        Crie uma resposta de e-mail concisa e útil em português para a seguinte consulta de Junior:
        Assunto: {original_subject}, De: {from_sender}, Prévia: {preview[:1000]}
        Requisitos: 1. Amigável, breve e direto. 2. Aborde perguntas específicas. 3. Profissional. 4. Termine com "Atenciosamente,\\n{user_name_signature}". 5. Assunto "Re: {original_subject}". 6. Menos de 150 palavras. 7. Sem desculpas por atraso desnecessárias.
        Sua resposta DEVE ser formatada como: Assunto: Re: {original_subject}\n\n[Corpo do e-mail em português]\n\nAtenciosamente,\n{user_name_signature}"""
        input_data = {}
    prompt = ChatPromptTemplate.from_template(template=prompt_template_str)
    chain = prompt | llm_client
    try:
        response_message = chain.invoke(input_data)
        return response_message.content
    except Exception as e:
        print(f"Erro ao gerar resposta com Gemini: {e}"); import traceback; traceback.print_exc(); return None


def process_email_responses_external(
        llm_client,
        ouvir_callback,
        falar_callback,
        user_name,
        send_email_function_from_satan,
        gmail_service_instance,
        path_needs_response_report: str,
        path_response_history: str
):
    """Processa e envia respostas para e-mails importantes."""
    emails = extract_emails_from_report_internal(report_path=path_needs_response_report)  # Usa função interna
    if not emails:
        falar_callback("Nenhum e-mail para responder encontrado no relatório.");
        return "Nenhum e-mail para responder."

    new_emails = [email for email in emails if not email['already_responded']]
    falar_callback(f"Encontrei {len(emails)} e-mails marcados para resposta. {len(new_emails)} são novos.")

    for i, email_data in enumerate(emails, 1):
        falar_callback(
            f"Processando e-mail {i} de {len(emails)}. Assunto: {email_data['subject']}. De: {email_data['from']}")
        if email_data['already_responded']:
            falar_callback("Este e-mail já foi respondido. Processar mesmo assim? Diga sim ou não.")
            choice_voice = ouvir_callback(timeout_microfone=7, frase_limite_segundos=5)
            if not (choice_voice and "sim" in choice_voice.lower()):
                falar_callback("Ok, pulando.");
                continue

        falar_callback("Gerando rascunho de resposta...")
        draft_response_text = generate_response_internal(llm_client, email_data, user_name)  # Usa função interna
        if not draft_response_text: falar_callback("Não consegui gerar resposta. Pulando."); continue

        current_draft_text = draft_response_text
        while True:
            response_lines = current_draft_text.strip().split('\n')
            subject_line_extracted = f"Re: {email_data['subject']}"  # Default
            body_parts = []
            body_start_index = 0
            if response_lines and (
                    response_lines[0].lower().startswith("assunto:") or response_lines[0].lower().startswith(
                    "subject:")):
                subject_line_extracted = response_lines[0].split(":", 1)[1].strip()
                body_start_index = 1

            actual_body_start_index = body_start_index
            for k_idx in range(body_start_index, len(response_lines)):
                if response_lines[k_idx].strip() == "" and not body_parts: continue
                body_parts.append(response_lines[k_idx])
            body = '\n'.join(body_parts).strip()

            falar_callback(
                f"Rascunho: Para: {email_data.get('email_address', 'N/A')}. Assunto: {subject_line_extracted}. Corpo: {body[:100]}...")
            print(
                f"\nPara: {email_data.get('email_address')}\nAssunto: {subject_line_extracted}\nCorpo:\n{body}\n" + "-" * 30)

            falar_callback(f"{user_name}, enviar, editar, pular ou cancelar?")
            action_voice = ouvir_callback(timeout_microfone=15, frase_limite_segundos=10)
            choice = ""
            if action_voice:
                lv = action_voice.lower()
                if "enviar" in lv:
                    choice = 'y'
                elif "editar" in lv:
                    choice = 'edit'
                elif "pular" in lv:
                    choice = 'skip'
                elif "cancelar" in lv:
                    choice = 'n'

            if choice == 'y':
                if email_data.get('email_address'):
                    falar_callback(f"Enviando para {email_data['email_address']}.")
                    if send_email_function_from_satan(gmail_service_instance, email_data['email_address'],
                                                      subject_line_extracted, body):
                        falar_callback("E-mail enviado!")
                        save_response_history_internal({"subject": email_data['subject'], "from": email_data['from'],
                                                        "responded_at": datetime.now().isoformat()},
                                                       history_file_path=path_response_history)  # Usa função interna
                    else:
                        falar_callback("Falha ao enviar.")
                else:
                    falar_callback("Erro: Endereço do destinatário não encontrado.")
                break
            elif choice == 'n':
                falar_callback("Cancelado."); break
            elif choice == 'skip':
                falar_callback("Pulado."); break
            elif choice == 'edit':
                falar_callback("Ok. Diga as instruções para reescrever.")
                edit_instructions_voice = ouvir_callback(timeout_microfone=30, frase_limite_segundos=25)
                if edit_instructions_voice:
                    falar_callback("Gerando nova resposta...")
                    new_draft_text = generate_response_internal(llm_client, email_data, user_name,
                                                                edit_instructions_voice)  # Usa função interna
                    if new_draft_text:
                        current_draft_text = new_draft_text
                    else:
                        falar_callback("Não consegui editar. Mantendo rascunho anterior.")
                else:
                    falar_callback("Não entendi as instruções. Mantendo rascunho anterior.")
            else:
                falar_callback("Opção inválida. Diga enviar, editar, pular ou cancelar.")

    msg_final = "Todos os e-mails foram processados."
    falar_callback(msg_final);
    return msg_final

# Removido if __name__ == "__main__":