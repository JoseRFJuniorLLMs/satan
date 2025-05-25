# -*- coding: utf-8 -*-
# Nome do Arquivo: satan.py
# Data da versão: 2025-05-17 - CONTROLE TOTAL GOOGLE + TTS GOOGLE CLOUD + MODELO ATUALIZADO
# Modificações por Junior (via Gemini): 2025-05-20
#   - Adicionada funcionalidade Win Hoff MP3 e Pomodoro
#   - Adicionada funcionalidade de acesso aos Contatos Google (People API)
#   - Corrigido SyntaxError em CheckGmailTool e outros refinamentos
#   - Revertida voz TTS para original do usuário
#   - Adicionada exibição do timer Pomodoro no terminal
#   - Adicionada ferramenta de Pesquisa Web Direta (simulada)
#   - Adicionada ferramenta de Notícias e Informação (NewsAPI)
# MODIFICAÇÕES ADICIONAIS (2025-05-23 via Gemini):
#   - Lista de SCOPES expandida para permissões mais abrangentes.
#   - CheckGmailTool atualizada para verificação de escopo mais robusta (any()).
# MODIFICAÇÕES ADICIONAIS (2025-05-23 - Noite via Gemini):
#   - CheckGmailTool agora lista emails recentes (lidos ou não lidos) do INBOX.
#   - Adicionada nova ferramenta SearchEmailsTool para buscar e listar todos os emails.

#
# ███████╗██╗   ██╗███████╗ ██████╗ ███╗   ███╗ ██████╗ ██╗   ██╗███████╗
# ██╔════╝██║   ██║██╔════╝██╔════╝ ████╗ ████║██╔════╝ ██║   ██║██╔════╝
# ███████╗██║   ██║███████╗██║  ███╗██╔████╔██║██║  ███╗██║   ██║███████╗
# ╚════██║██║   ██║╚════██║██║   ██║██║╚██╔╝██║██║   ██║██║   ██║╚════██║
# ███████║╚██████╔╝███████║╚██████╔╝██║ ╚═╝ ██║╚██████╔╝╚██████╔╝███████║
# ╚══════╝ ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝
# =====================================================================
# ==       AVISO: RISCO EXTREMO DE SEGURANÇA E PERDA DE DADOS        ==
# ==    USE ESTE CÓDIGO POR SUA CONTA E RISCO ABSOLUTAMENTE TOTAL    ==
# =====================================================================
#

# Jose R F Junior 20/04/2025

# -*- coding: utf-8 -*-
# Nome do Arquivo: satan5.py
# Data da versão: 2025-05-25
# Modificações por Junior (via Gemini): 2025-05-25
#   - CORREÇÃO: NameError para last_checked_time em periodic_email_check.
#   - CORREÇÃO: NameError para RECENT_EMAILS_FILE (e similares) nos módulos de e-mail,
#     passando os caminhos como parâmetros.
#   - CORREÇÃO: Definição de email_agent_scripts_loaded.
#   - INTEGRAÇÃO: Funções de important_email2.py, send_mail2.py, email_responder2.py
#     são chamadas a partir daqui.
#   - REFINAMENTO: Implementações de satan_get_emails_for_scripts,
#     satan_get_sent_emails_for_scripts, e satan_send_email_wrapper.

import os
import os.path
import subprocess
import sys
import tempfile
from dotenv import load_dotenv
import datetime
import traceback
import base64
from email.message import EmailMessage
import re
import threading
import time
# import calendar # Removido se não usado diretamente por satan5.py
import json
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

try:
    import dateutil.parser
    import dateutil.tz
    from dateutil.relativedelta import relativedelta

    dateutil_available = True
except ImportError:
    dateutil_available = False
    print("AVISO: Biblioteca 'python-dateutil' não encontrada. A análise de datas será limitada.")

try:
    import requests

    requests_available = True
except ImportError:
    requests_available = False
    print("AVISO: Biblioteca 'requests' não encontrada. A ferramenta de notícias não funcionará.")

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import BaseTool
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate  # Usado nas funções de email
from langchain_core.output_parsers.json import JsonOutputParser  # Usado nas funções de email

import speech_recognition as sr
from google.cloud import texttospeech

try:
    import playsound

    playsound_installed = True
except ImportError:
    playsound_installed = False
    print("AVISO: 'playsound' não encontrada. Instale com 'pip install playsound==1.2.2'")

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Imports dos MÓDULOS de e-mail ---
# Certifique-se que important_email2.py, send_mail2.py, email_responder2.py
# estão no mesmo diretório ou no PYTHONPATH e foram refatorados como módulos.
email_agent_scripts_loaded = False  # Inicializa a flag
try:
    from important_email2 import find_important_emails_external
    from send_mail2 import sort_emails_and_categorize_external, generate_opportunity_report_external
    from email_responder2 import process_email_responses_external

    email_agent_scripts_loaded = True
    print("Módulos de agente de e-mail carregados com sucesso.")
except ImportError as e_import_email_scripts:
    print(f"AVISO CRÍTICO: Falha ao importar módulos de agente de e-mail: {e_import_email_scripts}")
    print("As funcionalidades avançadas de e-mail podem não funcionar.")


    # Definir stubs para que o programa não quebre completamente se a importação falhar
    def find_important_emails_external(*args, **kwargs):
        print("ERRO: Módulo important_email2 não carregado."); return "Funcionalidade indisponível."


    def sort_emails_and_categorize_external(*args, **kwargs):
        print("ERRO: Módulo send_mail2 (sort) não carregado."); return "Funcionalidade indisponível."


    def generate_opportunity_report_external(*args, **kwargs):
        print("ERRO: Módulo send_mail2 (report) não carregado."); return "Funcionalidade indisponível."


    def process_email_responses_external(*args, **kwargs):
        print("ERRO: Módulo email_responder2 não carregado."); return "Funcionalidade indisponível."

# === CARREGA VARIÁVEIS DE AMBIENTE ===
load_dotenv(override=True)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
USER_NAME = os.getenv("USER_NAME", "Junior")
# Para LangSmith (opcional, mas resolve o aviso)
# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
# os.environ["LANGCHAIN_API_KEY"] = "SUA_LANGSMITH_API_KEY_AQUI" # Adicione ao .env se for usar
# os.environ["LANGCHAIN_PROJECT"] = "SATAN_Agent_Project" # Nome do projeto no LangSmith

# === CONFIGURAÇÕES GERAIS ===
MODEL_NAME = "gemini-2.5-pro-preview-05-06"
TEMPERATURE = 0.3
TTS_VOICE_GOOGLE = "pt-BR-Chirp3-HD-Laomedeia"  # Sua voz preferida
CREDENTIALS_FILENAME = 'credentials.json'
TOKEN_FILENAME = 'token.json'
WINHOFF_MP3_FILE = "winhoff.mp3"

# === ARQUIVOS PARA FUNCIONALIDADES DE E-MAIL (CENTRALIZADOS) ===
EMAILS_FOR_ANALYSIS_FILE = "emails_para_analise_geral.txt"
EMAILS_FOR_IMPORTANCE_FILE = "emails_para_analise_importancia.txt"
RESPONSE_HISTORY_FILE = "historico_respostas_email.json"
NEEDS_RESPONSE_JSON = "emails_precisam_resposta.json"
NEEDS_RESPONSE_REPORT = "relatorio_precisam_resposta.txt"
CATEGORIZED_EMAILS_JSON = "emails_categorizados.json"
OPPORTUNITY_REPORT = "relatorio_de_oportunidades.txt"


# === MODELOS PYDANTIC PARA ANÁLISE DE E-MAIL (CENTRALIZADOS) ===
class EmailImportance(BaseModel):
    importance: Literal["high", "medium", "low"] = Field(..., alias="importancia")
    reason: str = Field(..., alias="motivo")
    needs_response: bool = Field(..., alias="precisa_resposta")
    time_sensitive: bool = Field(..., alias="sensivel_ao_tempo")
    topics: List[str] = Field(..., alias="topicos")


class EmailAnalysis(BaseModel):
    category: Literal["sponsorship", "business_inquiry", "other"] = Field(..., alias="categoria")
    confidence: float = Field(..., alias="confianca")
    reason: str = Field(..., alias="motivo")
    company_name: Optional[str] = Field(None, alias="nome_empresa")
    topic: Optional[str] = Field(None, alias="topico_principal")


# === ESCOPOS GOOGLE API ===
SCOPES = [
    # === GMAIL - ACESSO COMPLETO ===
    'https://mail.google.com/',  # Permissão total para Gmail (leitura, escrita, envio, busca)
    'https://www.googleapis.com/auth/gmail.readonly',  # Leitura de emails
    'https://www.googleapis.com/auth/gmail.send',  # Envio de emails
    'https://www.googleapis.com/auth/gmail.modify',  # Modificação de emails
    'https://www.googleapis.com/auth/gmail.compose',  # Composição de emails
    'https://www.googleapis.com/auth/gmail.labels',  # Gerenciamento de labels
    'https://www.googleapis.com/auth/gmail.settings.basic',  # Configurações básicas
    'https://www.googleapis.com/auth/gmail.settings.sharing',  # Configurações de compartilhamento

    # === CALENDAR - GERENCIAMENTO COMPLETO ===
    'https://www.googleapis.com/auth/calendar',  # Acesso completo ao calendário
    'https://www.googleapis.com/auth/calendar.readonly',  # Leitura do calendário
    'https://www.googleapis.com/auth/calendar.events',  # Gerenciamento de eventos
    'https://www.googleapis.com/auth/calendar.events.readonly',  # Leitura de eventos
    'https://www.googleapis.com/auth/calendar.settings.readonly',  # Configurações do calendário

    # === GOOGLE DRIVE - OPERAÇÕES DE ARQUIVOS ===
    'https://www.googleapis.com/auth/drive',  # Acesso completo ao Drive
    'https://www.googleapis.com/auth/drive.file',  # Acesso a arquivos criados pela app
    'https://www.googleapis.com/auth/drive.readonly',  # Leitura do Drive
    'https://www.googleapis.com/auth/drive.metadata',  # Metadados dos arquivos
    'https://www.googleapis.com/auth/drive.metadata.readonly',  # Leitura de metadados
    'https://www.googleapis.com/auth/drive.photos.readonly',  # Fotos do Drive
    'https://www.googleapis.com/auth/drive.scripts',  # Scripts do Drive
    'https://www.googleapis.com/auth/drive.activity',  # Atividade do Drive
    'https://www.googleapis.com/auth/drive.activity.readonly',  # Leitura de atividade

    # === YOUTUBE - BUSCA E UPLOAD ===
    'https://www.googleapis.com/auth/youtube',  # Acesso completo ao YouTube
    'https://www.googleapis.com/auth/youtube.upload',  # Upload de vídeos
    'https://www.googleapis.com/auth/youtube.readonly',  # Leitura do YouTube
    'https://www.googleapis.com/auth/youtube.force-ssl',  # Acesso via SSL
    'https://www.googleapis.com/auth/youtubepartner',  # YouTube Partner
    'https://www.googleapis.com/auth/youtubepartner-channel-audit',  # Auditoria de canal
    'https://www.googleapis.com/auth/youtube.channel-memberships.creator',  # Memberships

    # === GOOGLE CONTACTS - PEOPLE API ===
    'https://www.googleapis.com/auth/contacts',  # Acesso aos contatos
    'https://www.googleapis.com/auth/contacts.readonly',  # Leitura dos contatos
    'https://www.googleapis.com/auth/contacts.other.readonly',  # Outros contatos
    'https://www.googleapis.com/auth/directory.readonly',  # Diretório

    # === GOOGLE WORKSPACE APPS ===
    'https://www.googleapis.com/auth/spreadsheets',  # Google Sheets completo
    'https://www.googleapis.com/auth/spreadsheets.readonly',  # Leitura de planilhas
    'https://www.googleapis.com/auth/documents',  # Google Docs completo
    'https://www.googleapis.com/auth/documents.readonly',  # Leitura de documentos
    'https://www.googleapis.com/auth/presentations',  # Google Slides completo
    'https://www.googleapis.com/auth/presentations.readonly',  # Leitura de apresentações
    'https://www.googleapis.com/auth/forms',  # Google Forms
    'https://www.googleapis.com/auth/forms.body',  # Corpo dos Forms
    'https://www.googleapis.com/auth/forms.responses.readonly',  # Respostas do Forms

    # === GOOGLE TASKS - GERENCIAMENTO ===
    'https://www.googleapis.com/auth/tasks',  # Acesso completo às tarefas
    'https://www.googleapis.com/auth/tasks.readonly',  # Leitura das tarefas

    # === GOOGLE PHOTOS - BIBLIOTECA E COMPARTILHAMENTO ===
    'https://www.googleapis.com/auth/photoslibrary',  # Acesso completo às fotos
    'https://www.googleapis.com/auth/photoslibrary.readonly',  # Leitura das fotos
    'https://www.googleapis.com/auth/photoslibrary.sharing',  # Compartilhamento de fotos
    'https://www.googleapis.com/auth/photoslibrary.appendonly',  # Adicionar fotos
    'https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata',  # Editar dados criados

    # === GOOGLE MAPS E LOCALIZAÇÃO ===
    'https://www.googleapis.com/auth/maps-platform.places',  # Google Places
    'https://www.googleapis.com/auth/maps-platform.places.details',  # Detalhes de lugares
    'https://www.googleapis.com/auth/maps-platform.places.textsearch',  # Busca de texto
    'https://www.googleapis.com/auth/maps-platform.places.nearbysearch',  # Busca próxima

    # === GOOGLE CLOUD PLATFORM ===
    'https://www.googleapis.com/auth/cloud-platform',  # Google Cloud Platform
    'https://www.googleapis.com/auth/cloud-platform.read-only',  # GCP somente leitura
    'https://www.googleapis.com/auth/compute',  # Google Compute Engine
    'https://www.googleapis.com/auth/compute.readonly',  # Compute somente leitura
    'https://www.googleapis.com/auth/devstorage.full_control',  # Cloud Storage completo
    'https://www.googleapis.com/auth/devstorage.read_only',  # Cloud Storage leitura
    'https://www.googleapis.com/auth/bigquery',  # BigQuery
    'https://www.googleapis.com/auth/bigquery.readonly',  # BigQuery leitura

    # === GOOGLE ANALYTICS ===
    'https://www.googleapis.com/auth/analytics',  # Google Analytics
    'https://www.googleapis.com/auth/analytics.readonly',  # Analytics leitura
    'https://www.googleapis.com/auth/analytics.manage.users',  # Gerenciar usuários
    'https://www.googleapis.com/auth/analytics.edit',  # Editar Analytics

    # === GOOGLE ADS ===
    'https://www.googleapis.com/auth/adwords',  # Google Ads

    # === GOOGLE SEARCH CONSOLE ===
    'https://www.googleapis.com/auth/webmasters',  # Search Console
    'https://www.googleapis.com/auth/webmasters.readonly',  # Search Console leitura

    # === GOOGLE PLAY ===
    'https://www.googleapis.com/auth/androidpublisher',  # Google Play Console

    # === GOOGLE FIREBASE ===
    'https://www.googleapis.com/auth/firebase',  # Firebase
    'https://www.googleapis.com/auth/firebase.readonly',  # Firebase leitura
    'https://www.googleapis.com/auth/firebase.messaging',  # Firebase Messaging

    # === GOOGLE BLOGGER ===
    'https://www.googleapis.com/auth/blogger',  # Blogger
    'https://www.googleapis.com/auth/blogger.readonly',  # Blogger leitura

    # === GOOGLE BOOKS ===
    'https://www.googleapis.com/auth/books',  # Google Books

    # === GOOGLE TRANSLATE ===
    'https://www.googleapis.com/auth/cloud-translation',  # Google Translate

    # === GOOGLE APPS SCRIPT ===
    'https://www.googleapis.com/auth/script.projects',  # Google Apps Script
    'https://www.googleapis.com/auth/script.processes',  # Processos do Script
    'https://www.googleapis.com/auth/script.metrics',  # Métricas do Script
    'https://www.googleapis.com/auth/script.deployments',  # Deployments do Script
    'https://www.googleapis.com/auth/script.deployments.readonly',  # Deployments leitura

    # === GOOGLE ADMIN (SE FOR ADMIN) ===
    'https://www.googleapis.com/auth/admin.directory.user',  # Usuários do domínio
    'https://www.googleapis.com/auth/admin.directory.user.readonly',  # Usuários leitura
    'https://www.googleapis.com/auth/admin.directory.group',  # Grupos do domínio
    'https://www.googleapis.com/auth/admin.directory.group.readonly',  # Grupos leitura
    'https://www.googleapis.com/auth/admin.directory.orgunit',  # Unidades organizacionais
    'https://www.googleapis.com/auth/admin.directory.device.chromeos',  # Dispositivos Chrome
    'https://www.googleapis.com/auth/admin.reports.audit.readonly',  # Relatórios de auditoria
    'https://www.googleapis.com/auth/admin.reports.usage.readonly',  # Relatórios de uso

    # === DADOS DO USUÁRIO E AUTENTICAÇÃO ===
    'https://www.googleapis.com/auth/userinfo.email',  # Email do usuário
    'https://www.googleapis.com/auth/userinfo.profile',  # Perfil do usuário
    'openid',  # OpenID Connect
    'profile',  # Informações básicas do perfil
    'email',  # Endereço de email

    # === GOOGLE CLASSROOM (SE APLICÁVEL) ===
    'https://www.googleapis.com/auth/classroom.courses',  # Cursos do Classroom
    'https://www.googleapis.com/auth/classroom.courses.readonly',  # Cursos leitura
    'https://www.googleapis.com/auth/classroom.rosters',  # Listas de alunos
    'https://www.googleapis.com/auth/classroom.rosters.readonly',  # Listas leitura
    'https://www.googleapis.com/auth/classroom.profile.emails',  # Emails do perfil
    'https://www.googleapis.com/auth/classroom.profile.photos',  # Fotos do perfil

    # === GOOGLE KEEP ===
    'https://www.googleapis.com/auth/keep',  # Google Keep
    'https://www.googleapis.com/auth/keep.readonly',  # Keep leitura

    # === GOOGLE FIT ===
    'https://www.googleapis.com/auth/fitness.activity.read',  # Atividades Fit
    'https://www.googleapis.com/auth/fitness.activity.write',  # Escrever atividades
    'https://www.googleapis.com/auth/fitness.location.read',  # Localização Fit
    'https://www.googleapis.com/auth/fitness.body.read',  # Dados corporais
    'https://www.googleapis.com/auth/fitness.nutrition.read',  # Nutrição
]

# === OUTRAS PLATAFORMAS (PARA IMPLEMENTAÇÃO FUTURA) ===
# MICROSOFT GRAPH API SCOPES (requer implementação separada):
# - https://graph.microsoft.com/User.Read
# - https://graph.microsoft.com/Mail.ReadWrite
# - https://graph.microsoft.com/Calendars.ReadWrite
# - https://graph.microsoft.com/Files.ReadWrite.All
# - https://graph.microsoft.com/Contacts.ReadWrite
# - https://graph.microsoft.com/Tasks.ReadWrite
# - https://graph.microsoft.com/Notes.ReadWrite.All (OneNote)
# - https://graph.microsoft.com/Sites.ReadWrite.All (SharePoint)
# - https://graph.microsoft.com/Team.ReadBasic.All (Teams)

# LINKEDIN API SCOPES (requer implementação separada):
# - r_liteprofile (perfil básico)
# - r_emailaddress (email)
# - w_member_social (postar)
# - r_organization_social (páginas da empresa)
# - rw_organization_admin (administrar páginas)

# TWITTER API SCOPES (requer implementação separada):
# - tweet.read, tweet.write
# - users.read, follows.read, follows.write
# - space.read, list.read, list.write

# FACEBOOK/META API SCOPES (requer implementação separada):
# - public_profile, email
# - pages_manage_posts, pages_read_engagement
# - instagram_basic, instagram_content_publish

# SLACK API SCOPES (requer implementação separada):
# - channels:read, channels:write
# - chat:write, files:read, files:write
# - users:read, team:read

# DISCORD API SCOPES (requer implementação separada):
# - identify, email, guilds, guilds.join
# - messages.read, bot

# SPOTIFY API SCOPES (requer implementação separada):
# - user-read-private, user-read-email
# - playlist-read-private, playlist-modify-public
# - user-library-read, user-library-modify

# GITHUB API SCOPES (requer implementação separada):
# - repo, user, admin:org
# - workflow, write:packages

# DROPBOX API SCOPES (requer implementação separada):
# - files.metadata.read, files.content.read
# - files.content.write, sharing.read, sharing.write

# NOTION API SCOPES (requer implementação separada):
# - Acesso a páginas, databases, blocos

# TRELLO API SCOPES (requer implementação separada):
# - read, write, account

# ZOOM API SCOPES (requer implementação separada):
# - meeting:read, meeting:write
# - user:read, recording:read

# WHATSAPP BUSINESS API (requer implementação separada):
# - Envio e recebimento de mensagens

# TELEGRAM BOT API (requer implementação separada):
# - Controle total do bot
print(f"Escopos Google API definidos: {len(SCOPES)} escopos.")

# --- Configuração do LLM LangChain ---
if not GOOGLE_API_KEY: sys.exit("Erro Crítico: GOOGLE_API_KEY não definida no .env.")
try:
    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, google_api_key=GOOGLE_API_KEY, temperature=TEMPERATURE,
                                 convert_system_message_to_human=True)
    print(f"LLM LangChain ({MODEL_NAME}) inicializado.")
except Exception as e:
    sys.exit(f"Erro crítico ao inicializar LLM LangChain: {e}")

# --- Inicialização do Cliente Google Cloud TTS ---
google_tts_ready = False
try:
    texttospeech.TextToSpeechClient()
    print("Cliente Google Cloud TTS parece estar pronto.")
    google_tts_ready = True
except Exception as e:
    print(f"Erro ao verificar cliente Google Cloud TTS: {e}\nAVISO: Google Cloud TTS pode não funcionar.")


# --- Função para Autenticação Google OAuth 2.0 ---
def get_google_credentials():
    creds = None
    if os.path.exists(TOKEN_FILENAME):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILENAME, SCOPES)
            if creds:
                token_scopes_set = set(creds.scopes if creds.scopes is not None else [])
                required_scopes_set = set(SCOPES)  # Usa a lista global SCOPES
                if not required_scopes_set.issubset(token_scopes_set):
                    print(
                        f"AVISO: Escopos no token ({token_scopes_set}) não cobrem todos os requeridos ({required_scopes_set}). Forçando re-autenticação.")
                    creds = None
                    if os.path.exists(TOKEN_FILENAME):
                        try:
                            os.remove(TOKEN_FILENAME); print(
                                f"Arquivo '{TOKEN_FILENAME}' removido para re-autenticação.")
                        except Exception as e_rem:
                            print(f"AVISO: Falha ao remover {TOKEN_FILENAME}: {e_rem}")
        except Exception as e:  # Captura exceções mais genéricas ao carregar o token
            print(
                f"Erro ao carregar '{TOKEN_FILENAME}' (pode estar corrompido ou formato inválido): {e}. Tentando re-autenticar.")
            creds = None
            if os.path.exists(TOKEN_FILENAME):
                try:
                    os.remove(TOKEN_FILENAME)
                except Exception as e_rem:
                    print(f"AVISO: Falha ao remover {TOKEN_FILENAME}: {e_rem}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("Credenciais Google atualizadas com sucesso via refresh token.")
                with open(TOKEN_FILENAME, 'w') as token_file:
                    token_file.write(creds.to_json())
            except Exception as e_refresh:
                print(
                    f"Erro ao atualizar credenciais via refresh token: {e_refresh}. Re-autorização completa necessária.")
                if os.path.exists(TOKEN_FILENAME):  # Remove token inválido
                    try:
                        os.remove(TOKEN_FILENAME)
                    except Exception as e_rem:
                        print(f"AVISO: Falha ao remover {TOKEN_FILENAME} após falha no refresh: {e_rem}")
                creds = None
        if not creds:  # Se ainda não tem credenciais (primeira vez ou refresh falhou)
            if not os.path.exists(CREDENTIALS_FILENAME):
                print(f"Erro Crítico: Arquivo de credenciais '{CREDENTIALS_FILENAME}' não encontrado!");
                return None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILENAME, SCOPES)
                print(">>> ATENÇÃO: SEU NAVEGADOR DEVE ABRIR PARA AUTORIZAÇÃO GOOGLE <<<")
                print("Por favor, conceda as permissões solicitadas.")
                creds = flow.run_local_server(port=0)
                print("Autorização Google concedida com sucesso!")
                with open(TOKEN_FILENAME, 'w') as token_file:
                    token_file.write(creds.to_json())
                    print(f"Novas credenciais salvas em '{TOKEN_FILENAME}'.")
            except Exception as e_flow:
                print(f"ERRO FATAL durante o fluxo de autorização Google: {e_flow}");
                traceback.print_exc();
                creds = None
    return creds


# --- Inicialização dos Serviços Google ---
print("\n--- Verificando Credenciais Google OAuth 2.0 ---")
google_creds = get_google_credentials()
google_auth_ready = bool(google_creds and google_creds.valid)
gmail_service = None
# calendar_service = None # Exemplo, descomente e use se necessário
# drive_service = None    # Exemplo

if google_auth_ready:
    print("SUCESSO PÓS-AUTH: Credenciais Google OAuth válidas.")
    try:
        gmail_service = build('gmail', 'v1', credentials=google_creds)
        print("Serviço Gmail API inicializado.")
        # Inicialize outros serviços aqui, se necessário
        # calendar_service = build('calendar', 'v3', credentials=google_creds)
        # drive_service = build('drive', 'v3', credentials=google_creds)
    except Exception as e_build:
        print(f"Erro ao construir serviços Google API: {e_build}")
        google_auth_ready = False  # Se a construção do serviço falhar
else:
    print("ERRO CRÍTICO PÓS-AUTH: Falha na autenticação Google OAuth. Serviços Google podem não funcionar.")
print("-" * 50)


# --- FUNÇÕES DE INTERAÇÃO COM GMAIL (IMPLEMENTAÇÕES REAIS) ---
def _get_plain_text_body_from_gmail_payload(payload: dict) -> str:
    """Helper para extrair corpo de texto puro do payload de uma mensagem do Gmail."""
    body_text = ""
    if not payload: return "[Payload do e-mail vazio]"

    mime_type = payload.get('mimeType', '')

    if mime_type == 'text/plain':
        body_data = payload.get('body', {}).get('data')
        if body_data:
            try:
                return base64.urlsafe_b64decode(body_data).decode('utf-8', errors='replace').strip()
            except Exception as e:
                print(f"Erro ao decodificar corpo text/plain: {e}"); return "[Erro ao decodificar corpo]"

    elif mime_type.startswith('multipart/'):
        parts = payload.get('parts', [])
        for part in parts:
            # Prioriza text/plain
            if part.get('mimeType') == 'text/plain':
                part_body_data = part.get('body', {}).get('data')
                if part_body_data:
                    try:
                        return base64.urlsafe_b64decode(part_body_data).decode('utf-8', errors='replace').strip()
                    except Exception as e:
                        print(f"Erro ao decodificar parte text/plain: {e}"); continue
            # Fallback para recursão se for outro multipart
            elif part.get('mimeType', '').startswith('multipart/'):
                nested_body = _get_plain_text_body_from_gmail_payload(part)
                if nested_body != "[Corpo do e-mail não encontrado ou formato não suportado]":
                    return nested_body  # Retorna o primeiro corpo de texto encontrado recursivamente
        # Se não encontrou text/plain direto, tenta html e depois outros multiparts
        for part in parts:
            if part.get('mimeType') == 'text/html':  # Fallback menos ideal para HTML se text/plain não for encontrado
                part_body_data = part.get('body', {}).get('data')
                if part_body_data:
                    print("Aviso: Extraindo de text/html, pode conter tags.")
                    try:  # Simples remoção de tags, pode não ser perfeito
                        html_content = base64.urlsafe_b64decode(part_body_data).decode('utf-8', errors='replace')
                        text_content = re.sub(r'<style.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
                        text_content = re.sub(r'<script.*?</script>', '', text_content, flags=re.DOTALL | re.IGNORECASE)
                        text_content = re.sub(r'<[^>]+>', ' ', text_content)  # Remove tags HTML
                        text_content = re.sub(r'\s+', ' ', text_content).strip()  # Normaliza espaços
                        return text_content
                    except Exception as e:
                        print(f"Erro ao decodificar parte text/html: {e}"); continue

    # Se chegou aqui, não encontrou um corpo de texto plano adequado
    return "[Corpo do e-mail não encontrado ou formato não suportado]"


def satan_get_emails_for_scripts(current_gmail_service, hours=24, query_extras="in:inbox",
                                 target_file="emails_temp.txt", max_results=25):
    """Busca e-mails e os salva em target_file para processamento pelos scripts de análise."""
    print(
        f"[SATAN_GET_EMAILS] Buscando e-mails: últimas {hours}h, extras='{query_extras}', arquivo='{target_file}', max={max_results}")
    if not current_gmail_service:
        msg = "[SATAN_GET_EMAILS] Serviço Gmail não disponível."
        print(msg);
        falar(msg.replace("[SATAN_GET_EMAILS]", "").strip())
        return False

    emails_data_list = []
    try:
        days_ago = (hours + 23) // 24
        query = f'{query_extras} newer_than:{days_ago}d'

        results = current_gmail_service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages_summary = results.get('messages', [])
        print(f"[SATAN_GET_EMAILS] Encontrados {len(messages_summary)} sumários para a query: {query}")

        if not messages_summary:
            print(
                f"Nenhum e-mail encontrado para os critérios. O arquivo {target_file} ficará vazio ou não será atualizado.")
            with open(target_file, "w", encoding="utf-8") as f: f.write("")
            return True  # Sucesso, mas nenhum e-mail

        for msg_summary in messages_summary:
            msg_id = msg_summary['id']
            # Pedir 'full' para ter o payload completo para extração do corpo
            msg = current_gmail_service.users().messages().get(userId='me', id=msg_id, format='full').execute()

            payload = msg.get('payload', {})
            headers = payload.get('headers', [])
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(Sem Assunto)')
            sender_raw = next((h['value'] for h in headers if h['name'].lower() == 'from'), '(Remetente Desconhecido)')
            date_str_header = next((h['value'] for h in headers if h['name'].lower() == 'date'), None)
            internal_date_ms_str = msg.get('internalDate')
            body_text = _get_plain_text_body_from_gmail_payload(payload)

            friendly_date = "Data Desconhecida"
            if dateutil_available:
                parsed_dt = None
                date_to_parse = date_str_header or internal_date_ms_str
                if date_to_parse:
                    try:
                        if isinstance(date_to_parse, str) and date_to_parse.isdigit():
                            parsed_dt = datetime.datetime.fromtimestamp(int(date_to_parse) / 1000,
                                                                        tz=datetime.timezone.utc)
                        elif isinstance(date_to_parse, str):
                            parsed_dt = dateutil.parser.parse(date_to_parse)
                        if parsed_dt:
                            current_tz = dateutil.tz.tzlocal()
                            if parsed_dt.tzinfo:
                                parsed_dt = parsed_dt.astimezone(current_tz)
                            else:
                                parsed_dt = current_tz.localize(parsed_dt)  # Torna aware com o fuso local
                            friendly_date = parsed_dt.isoformat()
                    except Exception as e_date_parse:
                        print(
                            f"Aviso: Não foi possível parsear data '{date_to_parse}' para e-mail '{subject}': {e_date_parse}")
                        friendly_date = str(date_to_parse) if date_to_parse else datetime.datetime.now().isoformat()

            emails_data_list.append({
                "id": msg_id, "subject": subject, "from": sender_raw,
                "received": friendly_date, "body": body_text
            })

        print(f"[SATAN_GET_EMAILS] E-mails formatados: {len(emails_data_list)}. Salvando em {target_file}...")
        with open(target_file, "w", encoding="utf-8") as f:
            for email_dict in emails_data_list:
                f.write(f"Assunto: {email_dict.get('subject', '')}\n")
                f.write(f"De: {email_dict.get('from', '')}\n")
                f.write(f"Recebido: {email_dict.get('received', '')}\n")
                # Adiciona um marcador "Corpo:" mesmo se o corpo estiver vazio para consistência no parsing
                f.write(f"Corpo: {email_dict.get('body', '[Corpo Vazio]')}\n")
                f.write("-" * 50 + "\n")
        return True  # Sucesso
    except HttpError as error:
        err_msg = f"Erro HTTP ao buscar e-mails: {error._get_reason()}"
        print(f"[SATAN_GET_EMAILS] {err_msg}")
        falar(f"Erro ao buscar seus e-mails: {error._get_reason()}")
        return False
    except Exception as e_main:
        print(f"[SATAN_GET_EMAILS] Erro geral em satan_get_emails: {e_main}")
        traceback.print_exc()
        falar("Ocorreu um erro inesperado ao buscar seus e-mails.")
        return False


def satan_get_sent_emails_for_scripts(current_gmail_service, days=7):
    """Busca e-mails enviados e formata para a função is_previously_responded."""
    print(f"[SATAN_GET_SENT_EMAILS] Buscando e-mails enviados dos últimos {days} dias...")
    if not current_gmail_service:
        print("[SATAN_GET_SENT_EMAILS] Serviço Gmail não disponível.")
        return []

    sent_emails_formatted = []
    try:
        query = f'in:sent newer_than:{days}d'
        results = current_gmail_service.users().messages().list(userId='me', q=query,
                                                                maxResults=200).execute()  # Aumentado limite
        messages_summary = results.get('messages', [])
        print(f"[SATAN_GET_SENT_EMAILS] Encontrados {len(messages_summary)} e-mails enviados.")

        for msg_summary in messages_summary:
            msg_id = msg_summary['id']
            msg = current_gmail_service.users().messages().get(userId='me', id=msg_id, format='metadata',
                                                               metadataHeaders=['To', 'Subject', 'Date']).execute()

            headers = msg.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(Sem Assunto)')
            recipients_raw = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
            date_str_header = next((h['value'] for h in headers if h['name'].lower() == 'date'), None)
            internal_date_ms_str = msg.get('internalDate')

            recipients_list = [addr.strip().lower() for addr in
                               re.findall(r'[\w\.-]+@[\w\.-]+', recipients_raw)]  # Regex mais direto para emails

            sent_time_iso = "Data Desconhecida"
            if dateutil_available:
                parsed_dt = None
                date_to_parse = date_str_header or internal_date_ms_str
                if date_to_parse:
                    try:
                        if isinstance(date_to_parse, str) and date_to_parse.isdigit():
                            parsed_dt = datetime.datetime.fromtimestamp(int(date_to_parse) / 1000,
                                                                        tz=datetime.timezone.utc)
                        elif isinstance(date_to_parse, str):
                            parsed_dt = dateutil.parser.parse(date_to_parse)
                        if parsed_dt:
                            current_tz = dateutil.tz.tzlocal()
                            if parsed_dt.tzinfo:
                                parsed_dt = parsed_dt.astimezone(current_tz)
                            else:
                                parsed_dt = current_tz.localize(parsed_dt)
                            sent_time_iso = parsed_dt.isoformat()
                    except Exception as e_date_parse_sent:
                        print(
                            f"Aviso: Não foi possível parsear data '{date_to_parse}' em e-mail enviado '{subject}': {e_date_parse_sent}")
                        sent_time_iso = str(date_to_parse) if date_to_parse else "Data Desconhecida"

            sent_emails_formatted.append({
                "subject": subject, "recipients": recipients_list, "sent_time": sent_time_iso
            })
        return sent_emails_formatted
    except HttpError as error:
        print(f"Erro HTTP ao buscar e-mails enviados: {error._get_reason()}")
        return []
    except Exception as e_main:
        print(f"Erro geral em satan_get_sent_emails: {e_main}")
        traceback.print_exc()
        return []


def satan_send_email_wrapper(current_gmail_service, to_address, subject_line, body_content):
    """Wrapper para enviar e-mail usando o serviço Gmail já autenticado."""
    print(f"[SATAN_SEND_EMAIL] Tentando enviar para: {to_address}, Assunto: {subject_line}")
    if not current_gmail_service:
        msg = "[SATAN_SEND_EMAIL] Serviço Gmail não disponível."
        print(msg);
        falar(msg.replace("[SATAN_SEND_EMAIL]", "").strip())
        return False
    try:
        message = EmailMessage()
        message.set_content(body_content)
        message['To'] = to_address
        message['Subject'] = subject_line

        # Obter o e-mail do usuário para o campo 'From', se possível
        try:
            user_profile = current_gmail_service.users().getProfile(userId='me').execute()
            sender_email = user_profile.get('emailAddress')
            if sender_email: message['From'] = sender_email
        except Exception as e_profile:
            print(f"Aviso: Não foi possível obter o e-mail do remetente para o cabeçalho 'From': {e_profile}")

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_message_result = current_gmail_service.users().messages().send(userId='me',
                                                                            body={'raw': encoded_message}).execute()
        print(f"E-mail enviado para {to_address}. ID da Mensagem: {send_message_result.get('id')}")
        return True
    except HttpError as error:
        err_reason = error._get_reason()
        print(f"Erro HTTP ao enviar e-mail: {err_reason}")
        falar(f"Erro ao tentar enviar o e-mail: {err_reason}")
        return False
    except Exception as e:
        print(f"Erro inesperado ao enviar e-mail: {e}")
        traceback.print_exc()
        falar("Ocorreu um erro inesperado ao tentar enviar o e-mail.")
        return False


# --- Variável Global para Threads de Background ---
# CORREÇÃO: Inicializar last_checked_time globalmente
last_checked_time = 0  # Inicialização da variável global


# --- FERRAMENTAS LANGCHAIN (Suas ferramentas existentes) ---
# (Cole aqui as definições COMPLETAS das suas classes:
# WindowsCommandExecutorTool, GetCalendarEventsTool, CreateCalendarEventTool,
# SendGmailTool (a ferramenta do agente, se diferente da wrapper),
# YouTubeSearchTool, DriveListFilesTool, SearchEmailsTool,
# ReadFullEmailContentTool, ListGoogleContactsTool, DirectWebSearchTool, GetNewsTool)
# E a CheckGmailTool MODIFICADA para usar get_gmail_service()

class WindowsCommandExecutorTool(BaseTool):
    name: str = "windows_command_executor"
    description: str = (
        "Executa um comando FORNECIDO COMO STRING única diretamente no Prompt de Comando do Windows. Use com cautela.")

    def _run(self, command_string: str) -> str:
        print(f"\n LCHAIN TOOL: Executando {self.name}: C:\\> {command_string}")
        if not isinstance(command_string,
                          str) or not command_string.strip(): return "Erro: Input inválido para comando."
        forbidden_commands = ["format", "shutdown", "del ", "rd ", "/s", "/q"]  # Adicione mais se necessário
        command_lower = command_string.lower()
        if any(fc in command_lower for fc in forbidden_commands):
            return f"Return Code: -1\nSTDOUT:\n(None)\nSTDERR:\nErro: Comando contendo termo '{command_lower[:20]}...' foi bloqueado."
        try:
            result = subprocess.run(command_string, shell=True, capture_output=True, text=True, check=False,
                                    encoding='cp850', errors='replace')
            stdout = result.stdout.strip() or '(Vazio)'
            stderr = result.stderr.strip() or '(Vazio)'
            return f"Código de Retorno: {result.returncode}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        except FileNotFoundError:
            return f"Erro: Comando ou programa '{command_string.split()[0]}' não encontrado."
        except Exception as e:
            return f"Erro Inesperado ao executar: {e}"


class GetCalendarEventsTool(BaseTool):
    name: str = "google_calendar_get_events_for_period"
    description: str = (
        "Busca e lista eventos do Google Calendar para um período (ex: 'hoje', 'amanhã', 'esta semana', 'próximo mês', 'junho 2025', '25/05/2025'). Padrão: hoje. Max 50 eventos.")

    def _make_aware(self, dt_obj: datetime.datetime, target_tz) -> datetime.datetime:
        return dt_obj.replace(tzinfo=target_tz) if dt_obj.tzinfo is None else dt_obj.astimezone(target_tz)

    def _get_start_of_day(self, dt_obj: datetime.datetime) -> datetime.datetime:
        return dt_obj.replace(hour=0, minute=0, second=0, microsecond=0)

    def _get_end_of_day(self, dt_obj: datetime.datetime) -> datetime.datetime:
        return dt_obj.replace(hour=23, minute=59, second=59, microsecond=999999)

    def _parse_query_to_daterange(self, query_str: str) -> tuple[str | None, str | None, str]:
        if not dateutil_available: now_utc = datetime.datetime.utcnow(); return (
        self._get_start_of_day(now_utc).isoformat() + 'Z', self._get_end_of_day(now_utc).isoformat() + 'Z',
        "hoje (dateutil indisponível)")
        try:
            local_tz = dateutil.tz.tzlocal()
        except:
            local_tz = datetime.timezone.utc; print("Aviso: Não foi possível determinar fuso local, usando UTC.")
        now_local = datetime.datetime.now(local_tz);
        query_lower = query_str.lower().strip()
        time_min_local, time_max_local = None, None;
        period_desc = query_str or "hoje"
        pt_month_map = {"janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4, "maio": 5, "junho": 6, "julho": 7,
                        "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12}
        if not query_lower or "hoje" in query_lower or (
                "eventos" in query_lower and not any(kw in query_lower for kw in ["amanhã", "semana", "mês", "ano"])):
            period_desc = "hoje";
            time_min_local, time_max_local = self._get_start_of_day(now_local), self._get_end_of_day(now_local)
        elif "amanhã" in query_lower:
            tomorrow_local = now_local + datetime.timedelta(days=1);
            period_desc = "amanhã";
            time_min_local, time_max_local = self._get_start_of_day(tomorrow_local), self._get_end_of_day(
                tomorrow_local)
        elif "esta semana" in query_lower or "semana atual" in query_lower:
            period_desc = "esta semana";
            start_of_week = now_local - datetime.timedelta(days=now_local.weekday());
            end_of_week = start_of_week + datetime.timedelta(days=6);
            time_min_local, time_max_local = self._get_start_of_day(start_of_week), self._get_end_of_day(end_of_week)
        elif "próxima semana" in query_lower:
            period_desc = "próxima semana";
            start_of_current_week = now_local - datetime.timedelta(days=now_local.weekday());
            start_of_next_week = start_of_current_week + datetime.timedelta(weeks=1);
            end_of_next_week = start_of_next_week + datetime.timedelta(days=6);
            time_min_local, time_max_local = self._get_start_of_day(start_of_next_week), self._get_end_of_day(
                end_of_next_week)
        elif "este mês" in query_lower or "mês atual" in query_lower:
            period_desc = "este mês";
            start_of_month = now_local.replace(day=1);
            _, num_days = calendar.monthrange(now_local.year, now_local.month);
            end_of_month = now_local.replace(day=num_days);
            time_min_local, time_max_local = self._get_start_of_day(start_of_month), self._get_end_of_day(end_of_month)
        elif "próximo mês" in query_lower:
            period_desc = "próximo mês";
            first_day_current_month = now_local.replace(day=1);
            first_day_next_month = first_day_current_month + relativedelta(months=1);
            _, num_days_next_month = calendar.monthrange(first_day_next_month.year, first_day_next_month.month);
            end_of_next_month = first_day_next_month.replace(day=num_days_next_month);
            time_min_local, time_max_local = self._get_start_of_day(first_day_next_month), self._get_end_of_day(
                end_of_next_month)
        else:  # Tenta parse mais específico
            year_match = re.search(r'\b(\d{4})\b', query_lower);
            parsed_as_specific_period = False
            for month_name, month_num in pt_month_map.items():
                if month_name in query_lower:
                    year_to_use = now_local.year;
                    if year_match: year_to_use = int(year_match.group(1))
                    start_of_target_month = datetime.datetime(year_to_use, month_num, 1, tzinfo=local_tz);
                    _, num_days_in_month = calendar.monthrange(year_to_use, month_num);
                    end_of_target_month = start_of_target_month.replace(day=num_days_in_month);
                    time_min_local, time_max_local = self._get_start_of_day(
                        start_of_target_month), self._get_end_of_day(end_of_target_month);
                    period_desc = f"{month_name.capitalize()} de {year_to_use}";
                    parsed_as_specific_period = True;
                    break
            if not parsed_as_specific_period and year_match and len(
                    query_lower.split()) == 1 and query_lower == year_match.group(1):  # Ano específico
                year_val = int(year_match.group(1));
                period_desc = f"o ano de {year_val}";
                time_min_local, time_max_local = self._get_start_of_day(
                    datetime.datetime(year_val, 1, 1, tzinfo=local_tz)), self._get_end_of_day(
                    datetime.datetime(year_val, 12, 31, tzinfo=local_tz));
                parsed_as_specific_period = True
            if not parsed_as_specific_period:  # Tenta parsear como data específica
                try:
                    default_date_for_parser = now_local.replace(hour=0, minute=0, second=0, microsecond=0);
                    parsed_dt = dateutil.parser.parse(query_str, default=default_date_for_parser, dayfirst=True);
                    parsed_dt_local = self._make_aware(parsed_dt, local_tz);
                    time_min_local, time_max_local = self._get_start_of_day(parsed_dt_local), self._get_end_of_day(
                        parsed_dt_local);
                    period_desc = f"o dia {time_min_local.strftime('%d/%m/%Y')}"
                except (dateutil.parser.ParserError, ValueError) as e_parse_date:
                    print(
                        f"Não foi possível interpretar '{query_str}' como período/data. Usando 'hoje'. Erro: {e_parse_date}");
                    period_desc = "hoje (falha no parse)";
                    time_min_local, time_max_local = self._get_start_of_day(now_local), self._get_end_of_day(now_local)
        if time_min_local and time_max_local: return time_min_local.isoformat(), time_max_local.isoformat(), period_desc
        print(f"Falha crítica ao determinar período para '{query_str}'. Usando 'hoje'.");
        time_min_local, time_max_local = self._get_start_of_day(now_local), self._get_end_of_day(now_local);
        return time_min_local.isoformat(), time_max_local.isoformat(), "hoje (padrão crítico)"

    def _run(self, query: str = "") -> str:
        creds = get_google_credentials();  # Usa a função global para obter creds
        if not creds: return "Erro: Falha nas credenciais Google para Calendário."
        current_calendar_service = None
        try:
            current_calendar_service = build('calendar', 'v3', credentials=creds)
        except Exception as e_build_cal:
            print(
                f"Erro ao construir serviço Calendar: {e_build_cal}"); return "Erro ao inicializar serviço Google Calendar."
        if not current_calendar_service: return "Erro: Serviço Google Calendar não pôde ser inicializado."

        time_min_str, time_max_str, period_description = self._parse_query_to_daterange(query)
        if not time_min_str or not time_max_str: return f"Não foi possível determinar o período para a consulta: '{query}'."
        print(f"   Buscando eventos para: {period_description} (De: {time_min_str} Até: {time_max_str})")
        try:
            events_result = current_calendar_service.events().list(calendarId='primary', timeMin=time_min_str,
                                                                   timeMax=time_max_str, maxResults=50,
                                                                   singleEvents=True, orderBy='startTime').execute();
            events = events_result.get('items', [])
            if not events: return f"Nenhum evento encontrado para {period_description}."
            output_lines = [f"Eventos para {period_description}:"]
            for event in events:
                start_data = event['start'];
                is_all_day = 'date' in start_data and 'dateTime' not in start_data
                start_str = start_data.get('dateTime', start_data.get('date'));
                summary = event.get('summary', '(Sem Título)')
                try:
                    if not is_all_day and dateutil_available:
                        dt_obj_aware = dateutil.parser.isoparse(start_str);
                        local_tz_for_display = dateutil.tz.tzlocal();
                        dt_obj_local = dt_obj_aware.astimezone(local_tz_for_display)
                        is_multi_day_period = (dateutil.parser.isoparse(time_max_str) - dateutil.parser.isoparse(
                            time_min_str)).days > 0
                        hour_minute = dt_obj_local.strftime(
                            '%d/%m %H:%M') if is_multi_day_period else dt_obj_local.strftime('%H:%M')
                    elif is_all_day and dateutil_available:
                        dt_obj_date = datetime.datetime.strptime(start_str, '%Y-%m-%d').date();
                        hour_minute = f"{dt_obj_date.strftime('%d/%m')} (Dia Inteiro)"
                    else:
                        hour_minute = start_str  # Fallback para string bruta se dateutil não estiver disponível
                except Exception as e_date_fmt:
                    print(
                        f"Erro ao formatar data do evento '{summary}': {e_date_fmt}"); hour_minute = "Horário Indisponível" if not is_all_day else "Dia Inteiro"
                output_lines.append(f"- {hour_minute}: {summary}")
            if len(events) >= 50 and events_result.get('nextPageToken'): output_lines.append(
                "\nAviso: Lista truncada em 50 eventos.")
            return "\n".join(output_lines)
        except HttpError as error:
            return f"Erro Google Calendar (HttpError {error.resp.status}): {error._get_reason()}"
        except Exception as e:
            traceback.print_exc(); return f"Erro ao buscar eventos: {e}"


class CheckGmailTool(BaseTool):
    name: str = "google_gmail_check_emails"
    description: str = ("Verifica e lista os e-mails mais recentes (até 5) na caixa de entrada do Gmail.")
    last_notified_email_id: str | None = None

    def _run(self, query: str = "") -> str | dict:
        print(f"\n LCHAIN TOOL (BACKGROUND/AGENT): Executando {self.name}...")
        current_gmail_service = get_gmail_service()  # Usa a função global para obter o serviço Gmail
        if not current_gmail_service:
            return "Erro: Falha nas credenciais ou serviço Gmail não inicializado para verificar e-mails."
        try:
            results = current_gmail_service.users().messages().list(userId='me', labelIds=['INBOX'],
                                                                    maxResults=5).execute()
            messages_summary_list = results.get('messages', [])
            if not messages_summary_list: return "Nenhum e-mail encontrado na caixa de entrada."

            output_lines_details = []
            first_email_summary_for_speech = {}

            for i, msg_summary in enumerate(messages_summary_list):
                msg_id = msg_summary['id']
                msg = current_gmail_service.users().messages().get(userId='me', id=msg_id, format='metadata',
                                                                   metadataHeaders=['From', 'Subject',
                                                                                    'Date']).execute()
                headers = msg.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '(Sem Assunto)')
                sender_raw = next((h['value'] for h in headers if h['name'].lower() == 'from'),
                                  '(Remetente Desconhecido)')
                date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), None)

                clean_sender_match = re.search(r'([^<]+)<', sender_raw)
                clean_sender = clean_sender_match.group(1).strip() if clean_sender_match else sender_raw.split('@')[
                    0].strip()

                friendly_date = "(Data desc.)"
                if dateutil_available and date_str:
                    try:
                        dt_obj = dateutil.parser.parse(date_str)
                        if dt_obj:  # Verifica se o parse teve sucesso
                            current_tz = dateutil.tz.tzlocal()
                            if dt_obj.tzinfo:
                                dt_obj = dt_obj.astimezone(current_tz)
                            else:
                                dt_obj = current_tz.localize(dt_obj)  # Torna aware com o fuso local
                            friendly_date = dt_obj.strftime('%d/%m %H:%M')
                    except Exception as e_date_parse_check:
                        print(f"Aviso: Falha ao parsear data '{date_str}' em CheckGmail: {e_date_parse_check}")
                        friendly_date = date_str.split(' (')[0] if date_str else "(Data desc.)"  # Fallback
                elif date_str:
                    friendly_date = date_str.split(' (')[0]  # Fallback simples

                output_lines_details.append(
                    f"- De: {clean_sender}, Assunto: {subject} (Recebido: {friendly_date}, ID: {msg_id})")
                if i == 0: first_email_summary_for_speech = {"sender": clean_sender, "subject": subject, "id": msg_id}

            details_string = "E-mails mais recentes na caixa de entrada:\n" + "\n".join(output_lines_details)
            spoken_output = None
            if first_email_summary_for_speech and self.last_notified_email_id != first_email_summary_for_speech.get(
                    "id"):
                self.last_notified_email_id = first_email_summary_for_speech.get("id")
                spoken_output = (
                    f"Novo e-mail na sua caixa de entrada de {first_email_summary_for_speech.get('sender', 'Desconhecido')} "
                    f"sobre {first_email_summary_for_speech.get('subject', 'sem assunto')}.")

            return {"spoken": spoken_output, "details": details_string} if spoken_output else details_string
        except HttpError as error:
            return f"Erro ao acessar Gmail (HttpError {error.resp.status}): {error._get_reason()}"
        except Exception as e:
            traceback.print_exc();
            return f"Erro inesperado ao verificar e-mails: {e}"


# --- Inicialização das Ferramentas para o Agente LangChain ---
check_gmail_tool_instance = CheckGmailTool()  # Instância para a thread e para o agente

tools = [
    WindowsCommandExecutorTool(),
    GetCalendarEventsTool(),
    # CreateCalendarEventTool(), # Adicione suas outras ferramentas
    # SendGmailTool(), # A ferramenta de agente para enviar e-mail, se diferente da wrapper
    # YouTubeSearchTool(),
    # DriveListFilesTool(),
    check_gmail_tool_instance,
    # SearchEmailsTool(),
    # ReadFullEmailContentTool(),
    # ListGoogleContactsTool(),
    # DirectWebSearchTool(),
    # GetNewsTool()
]
print(f"\nTotal de {len(tools)} ferramentas LangChain carregadas para o agente.")
if not email_agent_scripts_loaded:
    print(
        "AVISO: As funcionalidades avançadas de e-mail podem não estar disponíveis devido a erro de importação dos módulos.")
print("Ferramentas disponíveis para o agente:", [tool.name for tool in tools])
print("-" * 50)

# --- Configuração do Agente LangChain ---
try:
    react_prompt_template = hub.pull("hwchase17/react")
    agent = create_react_agent(llm=llm, tools=tools, prompt=react_prompt_template)
    agent_executor = AgentExecutor(
        agent=agent, tools=tools, verbose=True,
        handle_parsing_errors="Sua resposta anterior não estava no formato ReAct correto. Por favor, certifique-se de que sua resposta comece com 'Thought:' e, se usar uma ferramenta, siga com 'Action:' e 'Action Input:', OU comece com 'Final Answer:' se tiver a resposta final. Não adicione texto antes de 'Thought:' ou 'Final Answer:'.",
        max_iterations=15, max_execution_time=300  # Segundos
    )
    print("\nAgente LangChain (ReAct) e Executor configurados.")
except Exception as e:
    print(f"Erro crítico na configuração do Agente LangChain: {e}");
    traceback.print_exc();
    sys.exit(1)


# --- Funções de Voz ---
def ouvir_comando(timeout_microfone=7, frase_limite_segundos=15):  # Aumentados
    r = sr.Recognizer();
    audio = None
    try:
        with sr.Microphone() as source:
            print("\nAjustando ruído ambiente (0.5s)...");
            try:
                r.adjust_for_ambient_noise(source, duration=0.5)
            except Exception as e_noise:
                print(f"Aviso: Falha ajuste ruído: {e_noise}")
            print(f"Fale seu comando ou pergunta ({frase_limite_segundos}s max):")
            try:
                audio = r.listen(source, timeout=timeout_microfone, phrase_time_limit=frase_limite_segundos)
            except sr.WaitTimeoutError:
                print("Tempo de escuta do microfone esgotado."); return None
            except Exception as e_listen:
                print(f"Erro durante escuta: {e_listen}"); return None
    except sr.RequestError as e_mic_req:
        print(f"Erro no serviço de reconhecimento: {e_mic_req}"); return None
    except OSError as e_os_mic:
        if e_os_mic.errno == -9999 or "No Default Input Device Available" in str(e_os_mic):
            print(f"ERRO MICROFONE: Nenhum dispositivo de entrada padrão. Detalhes: {e_os_mic}")
        else:
            print(f"Erro OS com Microfone: {e_os_mic}"); traceback.print_exc()
        return None
    except Exception as e_mic:
        print(f"Erro geral com Microfone: {e_mic}"); traceback.print_exc(); return None

    if not audio: return None
    print("Reconhecendo fala...");
    texto_comando = None
    try:
        texto_comando = r.recognize_google(audio, language='pt-BR');
        print(f"Você disse: '{texto_comando}'")
    except sr.UnknownValueError:
        print("Não entendi o que você disse.")
    except sr.RequestError as e_rec_req:
        print(f"Erro Serviço Reconhecimento Google: {e_rec_req}")
    except Exception as e_rec:
        print(f"Erro Desconhecido no Reconhecimento: {e_rec}")
    return texto_comando


def falar(texto_para_falar):  # Renomeado para evitar conflito com variável 'texto'
    global playsound_installed, google_tts_ready, TTS_VOICE_GOOGLE
    if not texto_para_falar: print("[TTS] Nada para falar."); return
    if not google_tts_ready: print(f"\n(Simulando saída falada - Google TTS não pronto): {texto_para_falar}"); return

    print(f"\n🔊 Falando (Google Cloud TTS - Voz: {TTS_VOICE_GOOGLE}): {texto_para_falar}")
    temp_filename = None
    try:
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=texto_para_falar)
        voice_params = texttospeech.VoiceSelectionParams(language_code="pt-BR", name=TTS_VOICE_GOOGLE)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = client.synthesize_speech(
            request={'input': synthesis_input, 'voice': voice_params, 'audio_config': audio_config})

        # Usar tempfile.mkstemp para mais controle e garantir que o arquivo seja fechado antes do playsound
        fd, temp_filename = tempfile.mkstemp(suffix=".mp3")
        with os.fdopen(fd, "wb") as tmp_file:
            tmp_file.write(response.audio_content)

        if playsound_installed:
            playsound.playsound(temp_filename)
        else:
            print("AVISO: playsound não instalado. Tentando abrir MP3 com o sistema.")
            if sys.platform == "win32":
                os.startfile(temp_filename)
            elif sys.platform == "darwin":
                subprocess.call(["open", temp_filename])
            else:
                subprocess.call(["xdg-open", temp_filename])
            time.sleep(3)  # Dar mais tempo para player externo
    except Exception as e:
        print(f"Erro durante Google Cloud TTS ou reprodução do áudio: {e}");
        traceback.print_exc()
    finally:
        if temp_filename and os.path.exists(temp_filename):
            time.sleep(1)  # Pequeno delay
            try:
                os.remove(temp_filename)
            except PermissionError:
                print(f"AVISO: Não foi possível remover {temp_filename} (em uso).")
            except Exception as e_del:
                print(f"Aviso: Erro ao remover {temp_filename}: {e_del}")


# --- Funções Win Hoff e Pomodoro (SUAS IMPLEMENTAÇÕES COMPLETAS AQUI) ---
def play_winhoff_sound():
    global playsound_installed, WINHOFF_MP3_FILE
    if not os.path.exists(WINHOFF_MP3_FILE): msg = f"AVISO: Arquivo '{WINHOFF_MP3_FILE}' não encontrado."; print(
        msg); falar(msg.replace("AVISO: ", "Atenção, ")); return
    if not playsound_installed: msg = f"AVISO: 'playsound' não instalada."; print(msg); falar(
        msg.replace("AVISO: ", "Atenção, ")); return
    try:
        print(f"▶️ Tocando {WINHOFF_MP3_FILE}..."); playsound.playsound(WINHOFF_MP3_FILE)
    except Exception as e:
        print(f"Erro ao tocar {WINHOFF_MP3_FILE}: {e}"); falar("Erro ao tocar o som do exercício.")


def winhoff_periodic_task(interval_seconds, stop_event):
    print(f"[Thread Win Hoff] Iniciada. Tocando a cada {interval_seconds / 3600:.1f} horas.")
    while not stop_event.wait(interval_seconds):  # Espera pelo intervalo ou pelo evento de parada
        if stop_event.is_set(): break
        print(f"[Thread Win Hoff] Intervalo concluído. Tocando som.")
        play_winhoff_sound()
    print("[Thread Win Hoff] Encerrada.")


def pomodoro_task(pomodoro_duration_seconds, stop_event):
    print(f"[Thread Pomodoro] Iniciada. Duração: {pomodoro_duration_seconds / 60:.0f} min.")
    while not stop_event.is_set():
        print(f"\n[Thread Pomodoro] Novo ciclo de {pomodoro_duration_seconds / 60:.0f} minutos.")
        falar(f"Iniciando Pomodoro de {pomodoro_duration_seconds / 60:.0f} minutos.")
        tempo_restante = pomodoro_duration_seconds
        while tempo_restante > 0 and not stop_event.is_set():
            minutos, segundos = divmod(tempo_restante, 60)
            sys.stdout.write(f"\rTempo Pomodoro: {minutos:02d}:{segundos:02d}   ");
            sys.stdout.flush()
            if stop_event.wait(1): break  # Verifica a cada segundo
            tempo_restante -= 1
        if stop_event.is_set():
            sys.stdout.write("\r[Thread Pomodoro] Interrompido.                 \n");
            sys.stdout.flush()
            falar("Pomodoro interrompido.");
            break
        if tempo_restante == 0:
            sys.stdout.write("\r[Thread Pomodoro] Ciclo Concluído!              \n");
            sys.stdout.flush()
            print(f"[Thread Pomodoro] Tocando {WINHOFF_MP3_FILE}.")
            falar("Pomodoro concluído. Hora do exercício.");
            play_winhoff_sound();
            falar("Exercício finalizado.")
        if stop_event.wait(2): break  # Pequena pausa antes de reiniciar o ciclo
    sys.stdout.write("\r[Thread Pomodoro] Encerrada.                   \n");
    sys.stdout.flush()
    print("[Thread Pomodoro] Encerrada.")


# --- Função de Verificação Periódica de E-mails ---
# CORREÇÃO: last_checked_time foi movida para o escopo global antes desta função
def periodic_email_check(interval_seconds, stop_event):
    global last_checked_time, google_auth_ready, USER_NAME, check_gmail_tool_instance, gmail_service
    print(f"[Thread E-mail] Iniciada. Verificando e-mails a cada {interval_seconds} segundos.")
    while not stop_event.is_set():
        if not google_auth_ready or not gmail_service:
            print("[Thread E-mail] Autenticação Google ou serviço Gmail não pronto. Aguardando...")
            if stop_event.wait(60): break  # Espera 60s e verifica se deve parar
            continue

        current_time = time.time()
        if (current_time - last_checked_time) >= interval_seconds or last_checked_time == 0:
            print(
                f"\n[Thread E-mail] Verificando e-mails (última verificação há {current_time - last_checked_time:.0f}s)...")
            try:
                check_result = check_gmail_tool_instance._run()  # Usa a instância global da ferramenta
                last_checked_time = time.time()  # Atualiza o tempo da última verificação
                if isinstance(check_result, dict) and check_result.get("spoken"):
                    spoken_message = check_result["spoken"]
                    full_spoken_message = f"{USER_NAME}, {spoken_message[0].lower() + spoken_message[1:]}" if USER_NAME and spoken_message else spoken_message
                    if full_spoken_message: falar(full_spoken_message)
                elif isinstance(check_result, str) and "Erro:" in check_result:
                    print(f"[Thread E-mail] Erro retornado pela ferramenta de verificação: {check_result}")
            except Exception as e:
                print(f"[Thread E-mail] Erro crítico na verificação periódica de e-mails: {e}");
                traceback.print_exc()
                last_checked_time = time.time()  # Atualiza mesmo em erro para não ficar em loop de erro rápido

        # Calcula quanto tempo esperar até a próxima verificação, limitado a 60s para permitir que stop_event seja checado
        time_elapsed_since_last_check = time.time() - last_checked_time
        time_to_next_check = max(0, interval_seconds - time_elapsed_since_last_check)
        wait_duration = min(time_to_next_check, 60.0)  # Garante que wait() não seja 0 se o tempo já passou

        if stop_event.wait(wait_duration if wait_duration > 0 else 1.0):  # Espera no mínimo 1s
            break
    print("[Thread E-mail] Encerrada.")


# --- Iniciar Threads de Background ---
all_threads = []
stop_background_threads = threading.Event()

print("\n--- Iniciando Threads de Background ---")
email_check_interval = 300
if google_auth_ready and gmail_service:
    print(f"Thread de verificação de e-mails será iniciada (intervalo: {email_check_interval}s).")
    email_thread = threading.Thread(target=periodic_email_check, args=(email_check_interval, stop_background_threads),
                                    daemon=True, name="EmailCheckThread")
    all_threads.append(email_thread);
    email_thread.start()
else:
    print(
        "AVISO: Thread de verificação de e-mails NÃO iniciada (falha na autenticação Google ou serviço Gmail indisponível).")

can_start_audio_threads = playsound_installed and os.path.exists(WINHOFF_MP3_FILE)
if not playsound_installed: print(
    f"AVISO: 'playsound' não instalado. Threads de áudio ({WINHOFF_MP3_FILE}) não iniciadas.")
if not os.path.exists(WINHOFF_MP3_FILE) and playsound_installed: print(
    f"AVISO: Arquivo '{WINHOFF_MP3_FILE}' não encontrado. Threads de áudio não iniciadas.")

if can_start_audio_threads:
    winhoff_interval_2_hours = 2 * 60 * 60
    print(f"Thread Win Hoff Periódico ({WINHOFF_MP3_FILE} a cada 2 horas) será iniciada.")
    winhoff_periodic_thread = threading.Thread(target=winhoff_periodic_task,
                                               args=(winhoff_interval_2_hours, stop_background_threads), daemon=True,
                                               name="WinHoffPeriodicThread")
    all_threads.append(winhoff_periodic_thread);
    winhoff_periodic_thread.start()

    pomodoro_duration = 30 * 60
    print(f"Thread Pomodoro ({WINHOFF_MP3_FILE} a cada {pomodoro_duration / 60:.0f} minutos) será iniciada.")
    pomodoro_thread = threading.Thread(target=pomodoro_task, args=(pomodoro_duration, stop_background_threads),
                                       daemon=True, name="PomodoroThread")
    all_threads.append(pomodoro_thread);
    pomodoro_thread.start()
else:
    print(f"AVISO: Threads de áudio para '{WINHOFF_MP3_FILE}' não foram iniciadas.")
print("-" * 50)

# --- Loop Principal Interativo ---
print(f"\nSATAN v{datetime.date.today().strftime('%Y.%m.%d')} - Assistente por Voz com Gemini & Email Agents")
print("=================================================================")
falar(f"Olá {USER_NAME}! Sistema SATAN com gerenciamento de e-mail pronto. Diga 'sair' para terminar.")

try:
    while True:
        task_text = ouvir_comando()
        if task_text:
            task_lower = task_text.lower().strip()
            if task_lower == 'sair':
                falar(f"Encerrando as operações, {USER_NAME}. Até logo!");
                stop_background_threads.set();
                break

            # --- NOVAS FUNCIONALIDADES DE E-MAIL ---
            if "analisar emails importantes" in task_lower or \
                    "verificar e-mails importantes" in task_lower or \
                    "quais emails precisam de resposta" in task_lower:
                falar("Ok, vou verificar e analisar seus e-mails importantes.")
                if gmail_service and email_agent_scripts_loaded:
                    try:
                        # Passa as funções wrapper do satan5.py e a instância gmail_service
                        resultado = find_important_emails_external(
                            llm,
                            satan_get_emails_for_scripts,
                            satan_get_sent_emails_for_scripts,
                            gmail_service,
                            EMAILS_FOR_IMPORTANCE_FILE,  # Passa o nome do arquivo
                            NEEDS_RESPONSE_JSON,
                            NEEDS_RESPONSE_REPORT
                        )
                        falar(resultado)
                    except Exception as e:
                        msg_erro = f"Desculpe {USER_NAME}, ocorreu um erro ao analisar os e-mails importantes: {str(e)[:100]}"
                        print(f"Erro em find_important_emails_external: {e}");
                        traceback.print_exc();
                        falar(msg_erro)
                else:
                    falar(
                        f"Desculpe {USER_NAME}, não posso analisar e-mails sem acesso ao Gmail ou se os módulos de e-mail não carregaram.")

            elif "categorizar oportunidades nos emails" in task_lower or \
                    "procurar negócios nos emails" in task_lower or \
                    "categorizar meus emails" in task_lower:
                falar("Entendido. Vou categorizar seus e-mails e procurar por oportunidades de negócios.")
                if gmail_service and email_agent_scripts_loaded:
                    try:
                        # sort_emails_and_categorize_external espera:
                        # (llm_client, get_emails_function_from_satan, gmail_service_instance, path_emails_file, path_categorized_json)
                        summary_categorizacao = sort_emails_and_categorize_external(
                            llm,
                            satan_get_emails_for_scripts,
                            gmail_service,
                            EMAILS_FOR_ANALYSIS_FILE,  # Arquivo que satan_get_emails... vai popular
                            CATEGORIZED_EMAILS_JSON  # Arquivo onde o JSON categorizado será salvo
                        )
                        falar(summary_categorizacao)  # Fala o resumo da categorização

                        # Em seguida, gera o relatório de oportunidades com base no JSON categorizado
                        falar("Agora, gerando o relatório de oportunidades...")
                        resultado_report = generate_opportunity_report_external(
                            llm,
                            CATEGORIZED_EMAILS_JSON,  # Caminho para o JSON já criado
                            OPPORTUNITY_REPORT  # Caminho para salvar o relatório TXT
                        )
                        falar(resultado_report)
                    except Exception as e:
                        msg_erro = f"Desculpe {USER_NAME}, ocorreu um erro ao categorizar e-mails ou gerar o relatório: {str(e)[:100]}"
                        print(f"Erro em sort_emails/generate_report: {e}");
                        traceback.print_exc();
                        falar(msg_erro)
                else:
                    falar(
                        f"Desculpe {USER_NAME}, não posso categorizar e-mails sem acesso ao Gmail ou se os módulos de e-mail não carregaram.")

            elif "responder emails pendentes" in task_lower or \
                    "ajudar a responder emails" in task_lower:
                falar(
                    f"Ok {USER_NAME}, vamos processar os e-mails que precisam de resposta. Vou precisar da sua ajuda para confirmar ou editar.")
                if gmail_service and email_agent_scripts_loaded:
                    try:
                        # process_email_responses_external espera:
                        # (llm_client, ouvir_callback, falar_callback, user_name,
                        #  send_email_function_from_satan, gmail_service_instance,
                        #  path_needs_response_report, path_response_history)
                        resultado = process_email_responses_external(
                            llm,
                            ouvir_comando,
                            falar,
                            USER_NAME,
                            satan_send_email_wrapper,  # Nossa função de envio que usa gmail_service
                            gmail_service,
                            NEEDS_RESPONSE_REPORT,  # Caminho do relatório de entrada
                            RESPONSE_HISTORY_FILE  # Caminho para salvar histórico
                        )
                        falar(resultado)
                    except Exception as e:
                        msg_erro = f"Desculpe {USER_NAME}, ocorreu um erro ao processar as respostas dos e-mails: {str(e)[:100]}"
                        print(f"Erro em process_email_responses_external: {e}");
                        traceback.print_exc();
                        falar(msg_erro)
                else:
                    falar(
                        f"Desculpe {USER_NAME}, não posso processar respostas de e-mails sem acesso ao Gmail ou se os módulos de e-mail não carregaram.")

            # --- Comandos Existentes do Agente LangChain ---
            else:
                # Verifica se o comando requer serviços Google e se a autenticação está pronta
                google_service_keywords = ["agenda", "evento", "calendário", "gmail", "email", "e-mail", "drive",
                                           "arquivo", "youtube", "vídeo", "contato", "contatos"]
                requires_google_services = any(keyword in task_lower for keyword in google_service_keywords)

                if requires_google_services and not google_auth_ready:
                    falar(
                        f"Desculpe {USER_NAME}, não posso realizar essa tarefa porque a autenticação com os serviços Google falhou. Verifique o console para erros.");
                    continue

                try:
                    input_for_agent = f"O nome do usuário é {USER_NAME}. Hoje é {datetime.datetime.now().strftime('%d de %B de %Y, %H:%M')}. A solicitação do usuário é: {task_text}"
                    print(f"\n>>> Enviando tarefa ( '{input_for_agent}' ) para o agente LangChain...")
                    response = agent_executor.invoke({"input": input_for_agent})
                    agent_output_text = response.get("output", "Não obtive uma resposta final do agente.")
                    print("\n--- Resposta Final do Agente LangChain ---");
                    print(agent_output_text);
                    print("------------------------------")
                    falar(agent_output_text)
                except Exception as e_agent:
                    error_message = f"Ocorreu um erro crítico durante a execução do agente LangChain: {e_agent}"
                    print(f"\n!!! {error_message} !!!");
                    traceback.print_exc()
                    falar(f"Desculpe {USER_NAME}, ocorreu um erro interno severo ao processar seu pedido via agente.")
        else:
            pass  # Nenhuma entrada de voz
except KeyboardInterrupt:
    print("\nInterrupção pelo teclado. Encerrando...");
    falar(f"Encerrando as operações, {USER_NAME}.")
    stop_background_threads.set()
finally:
    print("\nLimpando e aguardando threads de background finalizarem...")
    if not stop_background_threads.is_set(): stop_background_threads.set()
    for t in all_threads:
        if t.is_alive():
            print(f"Aguardando thread {t.name} finalizar...");
            t.join(timeout=3)  # Timeout menor para finalizar mais rápido
            if t.is_alive(): print(f"AVISO: Thread {t.name} não finalizou a tempo.")
    print("\nScript SATAN terminado.")