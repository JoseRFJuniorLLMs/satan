import os
import json
import re
# Removido: from openai import OpenAI
# Removido: from dotenv import load_dotenv # satan5.py cuidará disso

# A importação de send_email de send_mail2.py não é mais necessária aqui,
# pois a função de envio será passada como parâmetro para process_responses.
# from send_mail2 import send_email

# Imports do LangChain necessários para interagir com o Gemini
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime  # Importar datetime diretamente

# Não é mais necessário, pois satan5.py carregará as variáveis de ambiente
# load_dotenv(override=True)

# File paths (nomes de arquivo traduzidos para consistência, satan5.py definirá os caminhos)
NEEDS_RESPONSE_REPORT_DEFAULT = "relatorio_precisam_resposta.txt"
RESPONSE_HISTORY_FILE_DEFAULT = "historico_respostas_email.json"


def extract_emails_from_report(report_path=NEEDS_RESPONSE_REPORT_DEFAULT):
    """Extrai e-mails do arquivo de relatório especificado."""
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        email_sections = content.split("-" * 50)
        emails = []
        for section in email_sections:
            if not section.strip():
                continue

            subject_match = re.search(r"Assunto: (.+?)\n", section)
            from_match = re.search(r"De: (.+?)\n", section)
            email_address_match = re.search(r"<(.+?)>", from_match.group(1) if from_match else "")
            preview_match = re.search(r"Prévia: ([\s\S]+?)(?=\n\n-{50}|\n\nSTATUS: ✅ JÁ RESPONDIDO|\n\nMotivo:|$)",
                                      section)
            already_responded = "STATUS: ✅ JÁ RESPONDIDO" in section

            if subject_match and from_match:
                from_text = from_match.group(1).strip()
                email_address = email_address_match.group(1).strip() if email_address_match else from_text

                emails.append({
                    "subject": subject_match.group(1).strip(),
                    "from": from_text,
                    "email_address": email_address,
                    "preview": preview_match.group(1).strip() if preview_match else "Prévia não disponível",
                    "already_responded": already_responded
                })
        return emails
    except FileNotFoundError:
        print(f"Erro: Arquivo de relatório '{report_path}' não encontrado.")
        return []
    except Exception as e:
        print(f"Erro ao extrair e-mails do relatório: {e}")
        import traceback
        traceback.print_exc()
        return []


def save_response_history(new_response_data, history_file_path=RESPONSE_HISTORY_FILE_DEFAULT):
    """Salva um registro de um e-mail ao qual respondemos."""
    history = {"emails_respondidos": []}
    if os.path.exists(history_file_path):
        try:
            with open(history_file_path, "r", encoding="utf-8") as f:
                history = json.load(f)
                if "emails_respondidos" not in history or not isinstance(history["emails_respondidos"], list):
                    history["emails_respondidos"] = []
        except json.JSONDecodeError:
            print(f"Aviso: Arquivo {history_file_path} corrompido/vazio. Criando novo histórico.")
            history = {"emails_respondidos": []}

    history["emails_respondidos"].append({
        "assunto_original": new_response_data["subject"],
        "remetente_original": new_response_data["from"],
        "respondido_em": new_response_data["responded_at"]
    })
    try:
        with open(history_file_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"Histórico de resposta salvo em {history_file_path} para: {new_response_data.get('subject')}")
        return True
    except Exception as e:
        print(f"Erro ao salvar histórico de respostas: {e}")
        return False


def generate_response(llm_client, email_data, user_name_signature, edit_instructions=None):
    """Gera uma resposta de e-mail usando o cliente LLM fornecido."""
    original_subject = email_data.get('subject', 'Sem Assunto')
    from_sender = email_data.get('from', 'Remetente Desconhecido')
    preview = email_data.get('preview', 'Conteúdo não disponível')

    if edit_instructions:
        prompt_template_str = f"""
        Reescreva a resposta do e-mail com base nestas instruções, em português:

        E-mail Original:
        Assunto: {original_subject}
        De: {from_sender}
        Prévia: {preview[:500]}

        Instruções para reescrever: {{instrucoes_edicao}}

        Sua resposta DEVE manter este formato:
        Assunto: Re: {original_subject}

        [Corpo do e-mail em português]

        Atenciosamente,
        {user_name_signature}
        """
        input_data = {"instrucoes_edicao": edit_instructions}
    else:
        prompt_template_str = f"""
        Crie uma resposta de e-mail concisa e útil em português para a seguinte consulta de Junior:

        Assunto: {original_subject}
        De: {from_sender}
        Prévia: {preview[:1000]}

        Requisitos:
        1. Mantenha a resposta amigável, mas breve e direta ao ponto.
        2. Aborde quaisquer perguntas ou solicitações específicas no e-mail.
        3. Seja profissional e prestativo.
        4. Sempre termine com "Atenciosamente,\\n{user_name_signature}".
        5. Inclua uma linha de assunto apropriada com o prefixo "Re: ".
        6. Não seja excessivamente prolixo - mantenha abaixo de 150 palavras.
        7. Não peça desculpas por atraso, a menos que seja claramente necessário.

        Sua resposta DEVE ser formatada como:
        Assunto: Re: {original_subject}

        [Corpo do e-mail em português]

        Atenciosamente,
        {user_name_signature}
        """
        input_data = {}

    prompt = ChatPromptTemplate.from_template(template=prompt_template_str)
    chain = prompt | llm_client

    try:
        response_message = chain.invoke(input_data)
        return response_message.content
    except Exception as e:
        print(f"Erro ao gerar resposta com Gemini: {e}")
        import traceback
        traceback.print_exc()
        return None


# Função principal que será importada e chamada por satan5.py
def process_email_responses_external(
        llm_client,
        ouvir_callback,
        falar_callback,
        user_name,
        send_email_function_from_satan,  # Função de envio de satan5.py
        gmail_service_instance,  # Instância do serviço Gmail de satan5.py
        path_needs_response_report=NEEDS_RESPONSE_REPORT_DEFAULT,  # Caminhos podem vir de satan5.py
        path_response_history=RESPONSE_HISTORY_FILE_DEFAULT
):
    """Processa e envia respostas para e-mails importantes, usando dependências externas."""

    emails = extract_emails_from_report(report_path=path_needs_response_report)

    if not emails:
        falar_callback("Nenhum e-mail para responder encontrado no relatório.")
        print("Nenhum e-mail para responder encontrado no relatório.")
        return "Nenhum e-mail para responder."

    new_emails = [email for email in emails if not email['already_responded']]
    falar_callback(f"Encontrei {len(emails)} e-mails marcados para resposta. {len(new_emails)} são novos.")
    print(
        f"Encontrados {len(emails)} e-mails que requerem resposta ({len(new_emails)} novos, {len(emails) - len(new_emails)} já respondidos).\n")

    for i, email_data in enumerate(emails, 1):
        falar_callback(
            f"Processando e-mail {i} de {len(emails)}. Assunto: {email_data['subject']}. De: {email_data['from']}")
        print("=" * 50)
        # ... (resto da lógica de print do e-mail)

        if email_data['already_responded']:
            falar_callback("Este e-mail já foi respondido anteriormente.")
            print(f"STATUS: ✅ JÁ RESPONDIDO")
            falar_callback("Deseja processá-lo mesmo assim? Diga sim ou não.")
            choice_voice = ouvir_callback(timeout_microfone=7, frase_limite_segundos=5)
            if choice_voice and "sim" not in choice_voice.lower():
                falar_callback("Ok, pulando para o próximo e-mail.")
                print("Pulando para o próximo e-mail...")
                continue
            elif not choice_voice:
                falar_callback("Não entendi. Pulando para o próximo.")
                print("Pulando devido a timeout/sem resposta...")
                continue

        falar_callback("Gerando um rascunho de resposta...")
        draft_response_text = generate_response(llm_client, email_data, user_name)

        if not draft_response_text:
            falar_callback("Não consegui gerar uma resposta. Pulando.")
            print("Falha ao gerar resposta. Pulando.")
            continue

        current_draft_text = draft_response_text
        while True:
            response_lines = current_draft_text.strip().split('\n')
            subject_line_extracted = ""
            body_start_index = 0
            if response_lines and (
                    response_lines[0].lower().startswith("assunto:") or response_lines[0].lower().startswith(
                    "subject:")):
                subject_line_extracted = response_lines[0].split(":", 1)[1].strip()
                body_start_index = 1
            else:
                subject_line_extracted = f"Re: {email_data['subject']}"

            actual_body_start_index = body_start_index
            for k_idx in range(body_start_index, len(response_lines)):
                if response_lines[k_idx].strip():
                    actual_body_start_index = k_idx
                    break
            body = '\n'.join(response_lines[actual_body_start_index:]).strip()

            falar_callback("Aqui está o rascunho:")
            falar_callback(f"Para: {email_data.get('email_address', 'Endereço não encontrado')}")
            falar_callback(f"Assunto: {subject_line_extracted}")
            falar_callback(f"Corpo: {body[:150]}...")

            print(
                f"\nPara: {email_data.get('email_address')}\nAssunto: {subject_line_extracted}\nCorpo:\n{body}\n" + "-" * 30)
            falar_callback(f"{user_name}, deseja enviar, editar, pular ou cancelar?")
            action_voice = ouvir_callback(timeout_microfone=15, frase_limite_segundos=10)
            choice = ""
            if action_voice:
                action_voice_lower = action_voice.lower()
                if "enviar" in action_voice_lower:
                    choice = 'y'
                elif "editar" in action_voice_lower:
                    choice = 'edit'
                elif "pular" in action_voice_lower or "ignorar" in action_voice_lower:
                    choice = 'skip'
                elif "cancelar" in action_voice_lower or "não" in action_voice_lower:
                    choice = 'n'

            if choice == 'y':
                if email_data.get('email_address'):
                    falar_callback(f"Enviando e-mail para {email_data['email_address']}.")
                    # Usa a send_email_function_from_satan, que deve usar o gmail_service_instance
                    result = send_email_function_from_satan(
                        gmail_service_instance,  # Passa o serviço do Gmail
                        email_data['email_address'],
                        subject_line_extracted,
                        body
                    )
                    if result:
                        falar_callback("E-mail enviado!")
                        save_response_history({
                            "subject": email_data['subject'], "from": email_data['from'],
                            "responded_at": datetime.now().isoformat()
                        }, history_file_path=path_response_history)
                    else:
                        falar_callback("Falha ao enviar o e-mail.")
                else:
                    falar_callback("Erro: Nenhum endereço de e-mail para o destinatário.")
                break
            elif choice == 'n':
                falar_callback("Resposta cancelada."); break
            elif choice == 'skip':
                falar_callback("E-mail pulado."); break
            elif choice == 'edit':
                falar_callback("Ok. Diga as instruções para reescrever.")
                edit_instructions_voice = ouvir_callback(timeout_microfone=30, frase_limite_segundos=25)
                if edit_instructions_voice:
                    falar_callback("Entendido. Gerando nova resposta...")
                    new_draft_text = generate_response(llm_client, email_data, user_name, edit_instructions_voice)
                    if new_draft_text:
                        current_draft_text = new_draft_text
                    else:
                        falar_callback("Não consegui editar. Mantendo rascunho anterior.")
                else:
                    falar_callback("Não entendi as instruções. Mantendo rascunho anterior.")
            else:
                falar_callback("Opção inválida. Diga enviar, editar, pular ou cancelar.")
        print()

    msg_final = "Todos os e-mails foram processados."
    falar_callback(msg_final)
    return msg_final

# Removido o if __name__ == "__main__":
# Este script agora é um módulo a ser importado e suas funções chamadas por satan5.py