# -*- coding: utf-8 -*-
# Nome do Arquivo: google_services_test.py
# Descrição: Testa a conectividade e autenticação básica com vários serviços Google API.

import os
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import traceback

# --- CONFIGURAÇÕES (Copie do seu satan5.py ou defina aqui) ---
load_dotenv(override=True)
CREDENTIALS_FILENAME = 'credentials.json'
TOKEN_FILENAME = 'token.json'

# Adapte esta lista de escopos para incluir o MÍNIMO necessário para cada teste.
# Idealmente, use os mesmos SCOPES do seu satan5.py para um teste completo.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',  # Para testar Gmail
    'https://www.googleapis.com/auth/calendar.readonly',  # Para testar Calendar
    'https://www.googleapis.com/auth/drive.metadata.readonly',  # Para testar Drive
    'https://www.googleapis.com/auth/youtube.readonly',  # Para testar YouTube
    'https://www.googleapis.com/auth/contacts.readonly'  # Para testar Contacts
]


def get_test_credentials():
    """Obtém ou atualiza as credenciais do usuário."""
    creds = None
    if os.path.exists(TOKEN_FILENAME):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILENAME, SCOPES)
        except Exception as e:
            print(f"Erro ao carregar token.json: {e}. Tentando re-autenticar.")
            creds = None
            if os.path.exists(TOKEN_FILENAME):
                os.remove(TOKEN_FILENAME)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("Credenciais atualizadas com sucesso (refresh).")
            except Exception as e_refresh:
                print(f"Erro ao atualizar credenciais: {e_refresh}. Re-autenticação necessária.")
                if os.path.exists(TOKEN_FILENAME):
                    os.remove(TOKEN_FILENAME)
                creds = None

        if not creds:  # Primeira vez ou refresh falhou
            if not os.path.exists(CREDENTIALS_FILENAME):
                print(f"ERRO CRÍTICO: Arquivo de credenciais '{CREDENTIALS_FILENAME}' não encontrado.")
                print(
                    "Por favor, baixe o JSON de credenciais do Google Cloud Console e salve-o como 'credentials.json'.")
                return None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILENAME, SCOPES)
                print("Uma janela do navegador será aberta para autorização. Siga as instruções.")
                creds = flow.run_local_server(port=0)
                print("Autorização concedida com sucesso!")
                with open(TOKEN_FILENAME, 'w') as token:
                    token.write(creds.to_json())
                print(f"Credenciais salvas em '{TOKEN_FILENAME}'.")
            except Exception as e_flow:
                print(f"ERRO FATAL durante o fluxo de autorização: {e_flow}")
                traceback.print_exc()
                return None
    return creds


def test_gmail_service(creds):
    service_name = "Gmail API"
    print(f"\n--- Testando {service_name} ---")
    if not creds:
        print(f"FALHA: Credenciais não disponíveis para {service_name}.")
        return False
    if 'https://www.googleapis.com/auth/gmail.readonly' not in creds.scopes and \
            'https://mail.google.com/' not in creds.scopes:
        print(f"FALHA: Escopo necessário para {service_name} (gmail.readonly ou mail.google.com) não concedido.")
        return False
    try:
        service = build('gmail', 'v1', credentials=creds)
        # Tenta listar as labels (uma operação de leitura simples)
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        if labels:
            print(f"SUCESSO: {service_name} - {len(labels)} labels encontradas.")
            return True
        else:
            print(
                f"SUCESSO (parcial): {service_name} conectado, mas nenhuma label encontrada (ou caixa de entrada vazia/sem labels).")
            return True
    except HttpError as error:
        print(f"FALHA: {service_name} - Erro HTTP {error.resp.status}: {error._get_reason()}")
        if error.resp.status == 403:
            print(
                "  Isso pode indicar que a API do Gmail não está habilitada no seu projeto GCP ou que os escopos não foram concedidos corretamente.")
        return False
    except Exception as e:
        print(f"FALHA: {service_name} - Erro inesperado: {e}")
        traceback.print_exc()
        return False


def test_calendar_service(creds):
    service_name = "Google Calendar API"
    print(f"\n--- Testando {service_name} ---")
    if not creds:
        print(f"FALHA: Credenciais não disponíveis para {service_name}.")
        return False
    if 'https://www.googleapis.com/auth/calendar.readonly' not in creds.scopes and \
            'https://www.googleapis.com/auth/calendar' not in creds.scopes:
        print(f"FALHA: Escopo necessário para {service_name} (calendar.readonly ou calendar) não concedido.")
        return False
    try:
        service = build('calendar', 'v3', credentials=creds)
        # Tenta listar os calendários do usuário
        calendar_list = service.calendarList().list().execute()
        items = calendar_list.get('items', [])
        if items:
            print(f"SUCESSO: {service_name} - {len(items)} calendários encontrados. (Ex: {items[0].get('summary')})")
            return True
        else:
            print(f"SUCESSO (parcial): {service_name} conectado, mas nenhuma lista de calendário encontrada.")
            return True
    except HttpError as error:
        print(f"FALHA: {service_name} - Erro HTTP {error.resp.status}: {error._get_reason()}")
        if error.resp.status == 403:
            print("  Isso pode indicar que a API do Google Calendar não está habilitada no seu projeto GCP.")
        return False
    except Exception as e:
        print(f"FALHA: {service_name} - Erro inesperado: {e}")
        traceback.print_exc()
        return False


def test_drive_service(creds):
    service_name = "Google Drive API"
    print(f"\n--- Testando {service_name} ---")
    if not creds:
        print(f"FALHA: Credenciais não disponíveis para {service_name}.")
        return False
    if 'https://www.googleapis.com/auth/drive.metadata.readonly' not in creds.scopes and \
            'https://www.googleapis.com/auth/drive.readonly' not in creds.scopes and \
            'https://www.googleapis.com/auth/drive.file' not in creds.scopes and \
            'https://www.googleapis.com/auth/drive' not in creds.scopes:
        print(f"FALHA: Escopo de leitura necessário para {service_name} não concedido.")
        return False
    try:
        service = build('drive', 'v3', credentials=creds)
        # Tenta listar os primeiros 5 arquivos da raiz
        results = service.files().list(
            pageSize=5, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        if items:
            print(f"SUCESSO: {service_name} - {len(items)} arquivos/pastas encontrados na raiz.")
            # for item in items:
            #    print(f"  - {item['name']} ({item['id']})")
            return True
        else:
            print(
                f"SUCESSO (parcial): {service_name} conectado, mas nenhum arquivo/pasta encontrado na raiz (ou raiz vazia).")
            return True
    except HttpError as error:
        print(f"FALHA: {service_name} - Erro HTTP {error.resp.status}: {error._get_reason()}")
        if error.resp.status == 403:
            print("  Isso pode indicar que a API do Google Drive não está habilitada no seu projeto GCP.")
        return False
    except Exception as e:
        print(f"FALHA: {service_name} - Erro inesperado: {e}")
        traceback.print_exc()
        return False


def test_youtube_service(creds):
    service_name = "YouTube Data API v3"
    print(f"\n--- Testando {service_name} ---")
    if not creds:
        print(f"FALHA: Credenciais não disponíveis para {service_name}.")
        return False
    if 'https://www.googleapis.com/auth/youtube.readonly' not in creds.scopes and \
            'https://www.googleapis.com/auth/youtube' not in creds.scopes:  # Escopo mais amplo também serve
        print(f"FALHA: Escopo de leitura para {service_name} (youtube.readonly ou youtube) não concedido.")
        return False
    try:
        service = build('youtube', 'v3',
                        credentials=creds)  # Usa credenciais se tiver, senão GOOGLE_API_KEY (não ideal para este teste)
        # Tenta uma busca simples
        search_response = service.search().list(
            q='Google',
            part='snippet',
            maxResults=1
        ).execute()
        if search_response.get("items"):
            print(f"SUCESSO: {service_name} - Busca por 'Google' retornou resultados.")
            return True
        else:
            print(f"SUCESSO (parcial): {service_name} conectado, mas busca por 'Google' não retornou itens.")
            return True
    except HttpError as error:
        print(f"FALHA: {service_name} - Erro HTTP {error.resp.status}: {error._get_reason()}")
        if error.resp.status == 403:
            print("  Isso pode indicar que a API do YouTube Data v3 não está habilitada ou cotas excedidas.")
        return False
    except Exception as e:
        print(f"FALHA: {service_name} - Erro inesperado: {e}")
        traceback.print_exc()
        return False


def test_contacts_service(creds):
    service_name = "Google People API (Contacts)"
    print(f"\n--- Testando {service_name} ---")
    if not creds:
        print(f"FALHA: Credenciais não disponíveis para {service_name}.")
        return False
    if 'https://www.googleapis.com/auth/contacts.readonly' not in creds.scopes and \
            'https://www.googleapis.com/auth/contacts' not in creds.scopes:
        print(f"FALHA: Escopo de leitura para {service_name} (contacts.readonly ou contacts) não concedido.")
        return False
    try:
        service = build('people', 'v1', credentials=creds)
        # Tenta listar os primeiros 5 contatos
        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=5,
            personFields='names,emailAddresses'
        ).execute()
        connections = results.get('connections', [])
        if connections:
            print(f"SUCESSO: {service_name} - {len(connections)} contatos encontrados.")
            # for person in connections:
            #    names = person.get('names', [])
            #    if names:
            #        print(f"  - {names[0].get('displayName')}")
            return True
        else:
            print(f"SUCESSO (parcial): {service_name} conectado, mas nenhum contato encontrado (ou lista vazia).")
            return True
    except HttpError as error:
        print(f"FALHA: {service_name} - Erro HTTP {error.resp.status}: {error._get_reason()}")
        if error.resp.status == 403:
            print("  Isso pode indicar que a People API não está habilitada no seu projeto GCP.")
        return False
    except Exception as e:
        print(f"FALHA: {service_name} - Erro inesperado: {e}")
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Iniciando teste de serviços Google...")

    master_creds = get_test_credentials()

    if not master_creds:
        print("\nNão foi possível obter as credenciais Google. Testes não podem prosseguir.")
        sys.exit(1)

    print("\nCredenciais obtidas. Iniciando testes individuais dos serviços...")

    results = {}
    results["Gmail"] = test_gmail_service(master_creds)
    results["Calendar"] = test_calendar_service(master_creds)
    results["Drive"] = test_drive_service(master_creds)
    results["YouTube"] = test_youtube_service(master_creds)
    results["Contacts"] = test_contacts_service(master_creds)

    print("\n--- Resumo dos Testes ---")
    all_ok = True
    for service, status in results.items():
        status_text = "OK" if status else "FALHOU"
        print(f"- {service}: {status_text}")
        if not status:
            all_ok = False

    if all_ok:
        print("\nTODOS os serviços testados parecem estar funcionando corretamente com as credenciais fornecidas!")
    else:
        print("\nATENÇÃO: Um ou mais serviços Google falharam no teste. Verifique os logs acima para detalhes.")
        print("Possíveis causas comuns de falha incluem:")
        print("  - API não habilitada no Google Cloud Platform para o seu projeto.")
        print("  - Escopos OAuth incorretos ou não concedidos durante a autorização.")
        print("  - Problemas com o arquivo 'credentials.json' ou 'token.json'.")
        print("  - Cotas da API excedidas (menos provável para testes básicos).")
        print("  - Problemas de rede.")
    print("-------------------------")