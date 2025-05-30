# S.A.T.A.N.
![Satan](./satan.png) 
![Satan](./fluxo.png) 
# (Ou uma nova imagem que reflita as capacidades de e-mail)

- Script de Automação Total e Assistência Neural com Gerenciamento Inteligente de E-mails

**AVISO IMPORTANTE: Este projeto concede amplas permissões e capacidades de execução, incluindo acesso total ao Gmail. Use com extrema cautela e por sua conta e risco.**

## 🚩 Descrição

**S.A.T.A.N.** (Script de Automação Total e Assistência Neural) é um assistente pessoal avançado controlado por voz, construído em Python. Ele utiliza o poder da Inteligência Artificial através do modelo Gemini do Google (via LangChain) e se integra profundamente com uma vasta gama de serviços Google (especialmente Gmail) e outras APIs para fornecer automação e assistência em diversas tarefas, incluindo gerenciamento inteligente da sua caixa de entrada de e-mails.

Este projeto foi aprimorado para incorporar um sistema de "Agentes de IA para E-mails", visando o "inbox zero" através da filtragem, categorização e auxílio na resposta de e-mails.

## ✨ Funcionalidades Principais

* **Controle por Voz Total:**
    * Reconhecimento de fala em português (via `speech_recognition` e Google Speech API).
    * Síntese de voz natural em português (via Google Cloud Text-to-Speech, voz configurável como `pt-BR-Chirp3-HD-Laomedeia`).
* **Agente Inteligente com LangChain & Gemini:**
    * Utiliza o modelo `gemini-2.5-pro-preview-05-06` (configurável) para compreensão e tomada de decisões.
    * Arquitetura de agente ReAct para orquestração de ferramentas.
* **Gerenciamento Inteligente de E-mails (Novas Funcionalidades):**
    * **Detector de E-mails Importantes:** Analisa sua caixa de entrada usando IA (Gemini) para identificar e-mails que realmente necessitam de atenção, ignorando notificações e marketing em massa. Verifica se já foram respondidos.
    * **Categorizador de E-mails e Oportunidades:** Usa IA para categorizar e-mails em "patrocínio", "consulta de negócios" ou "outros". Gera relatórios destacando oportunidades de alto valor.
    * **Gerador de Respostas de E-mail:** Cria rascunhos de respostas em português para os e-mails importantes, permitindo que o usuário revise, edite (com instruções por voz) e aprove o envio por voz.
* **Integração Profunda com Serviços Google (OAuth 2.0):**
    * **Gmail:** Acesso completo para leitura, busca, envio, e as novas funcionalidades de análise e resposta inteligente.
    * **Google Calendar:** Criar e listar eventos.
    * **Google Drive:** Listar arquivos.
    * **Google Contacts (People API):** Listar contatos.
    * **YouTube:** Pesquisar vídeos.
* **Ferramentas Adicionais:**
    * Executor de Comandos Windows (com restrições de segurança).
    * Notícias (NewsAPI).
    * Pesquisa Web Direta (simulada, para ser expandida pelo Gemini).
    * Timer Pomodoro e áudio para exercício Win Hoff (requer arquivo `winhoff.mp3`).
* **Tarefas em Background:** Verificação periódica de novos e-mails (com notificação por voz), Pomodoro, Win Hoff.
* **Configurável e Robusto:** Autenticação OAuth, chaves de API e configurações via `.env`.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.x
* **Inteligência Artificial & LangChain:**
    * `langchain`, `langchain-google-genai`, `langchain-core`
    * Modelos Pydantic para estruturação de dados da IA.
* **APIs Google:** (Conforme listado em `SCOPES` no script)
    * `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`
    * `google-cloud-texttospeech`
* **Voz e Áudio:** `SpeechRecognition`, `playsound==1.2.2`
* **Outras:** `python-dotenv`, `python-dateutil`, `requests`

## ⚙️ Configuração e Instalação

### Pré-requisitos
* Python 3.8+
* Microfone e sistema de som.
* Projeto no Google Cloud Platform com as APIs necessárias habilitadas.

### Passos Detalhados
(Manter os passos de 1 a 7 do seu README original, pois eles continuam válidos para a configuração do ambiente, dependências e credenciais).
* Certifique-se de que seu arquivo `credentials.json` possui os escopos corretos, especialmente `https://mail.google.com/` para as funcionalidades completas do Gmail.
* Adicione `OPENAI_API_KEY="SUA_CHAVE_OPENAI_SE_PRECISO_PARA_OUTRAS_COISAS"` ao seu `.env` se alguma parte do seu código ainda a utilizar, embora as novas funcionalidades de e-mail usem Gemini. Para este projeto focado em Gemini, ela pode não ser mais necessária se todas as chamadas de IA foram migradas. **(Nota: Os scripts de e-mail foram migrados para Gemini, então a chave OpenAI não é mais necessária para eles).**

## 🚀 Executando o Script

1.  Ative seu ambiente virtual.
2.  Navegue até a pasta do projeto.
3.  Execute: `python satan5.py`
4.  Autorize o acesso à sua conta Google na primeira execução ou se os escopos mudarem.

## 🎙️ Comandos de Voz para E-mail (Exemplos)

* "Satan, analisar emails importantes"
* "Satan, verificar e-mails importantes"
* "Satan, quais emails precisam de resposta?"
* "Satan, categorizar oportunidades nos emails"
* "Satan, procurar negócios nos emails"
* "Satan, responder emails pendentes"
* "Satan, me ajude a responder os emails"

## 📁 Arquivos Gerados pelas Funções de E-mail

* `emails_para_analise_geral.txt`: E-mails brutos para categorização.
* `emails_para_analise_importancia.txt`: E-mails brutos para análise de importância.
* `historico_respostas_email.json`: Log de e-mails que foram respondidos.
* `emails_precisam_resposta.json`: Saída JSON dos e-mails importantes.
* `relatorio_precisam_resposta.txt`: Relatório legível dos e-mails importantes.
* `emails_categorizados.json`: Saída JSON dos e-mails categorizados.
* `relatorio_de_oportunidades.txt`: Relatório legível das oportunidades de negócio.

## ⚠️ Considerações de Segurança MUITO IMPORTANTES

(Manter a seção de segurança do seu README original, pois ela continua extremamente relevante, especialmente com o acesso total ao Gmail).

## 👤 Autor / Modificações

* Script original: `satan.py` por Jose R F Junior
* Integração dos Módulos de Email e adaptação para Gemini: Junior (com assistência de IA Gemini).
* Funcionalidades base de análise de e-mail inspiradas no projeto "Inbox Zero AI Agent System" de AllAboutAI-YT.

---
Este README atualizado deve refletir melhor as novas capacidades do seu projeto S.A.T.A.N!