# BodyLens

[English](README.md) · [Español](README_ES.md) · [Català](README_CA.md) · [Français](README_FR.md) · [Italiano](README_IT.md) ·
[Deutsch](README_DE.md) · **Português** · [Nederlands](README_NL.md) · [中文](README_ZH.md) ·
[日本語](README_JA.md)

**BodyLens** é uma aplicação web de saúde pessoal, auto-alojada e multiutilizador. Reúne o peso e a composição
corporal de uma balança **Withings** e o que o teu telemóvel e o teu relógio registam (sono, atividade, frequência
cardíaca, VFC, SpO2, VO2 máx., ECG, ciclo, humor…) a partir do **Apple Saúde** ou do **Health Connect do Android**.
Funciona em Docker no teu próprio servidor, os dados chegam sozinhos e cada pessoa vê apenas os seus.

## Funcionalidades

- **Resumo:** peso de tendência, progresso do plano, «hoje de relance» (prontidão, sono, saldo de sono, VFC, passos)
  e conclusões e avisos automáticos.
- **Peso:** tendência suavizada, plano com ritmos-alvo, projeção, semanas, calendário e marcos; histórico de pesos ao
  longo dos anos, tentativas de perda de peso e recuperações.
- **Corpo:** composição (gordura, músculo, água, osso), IMC/FFMI com intervalos por idade e sexo, medidas com fita
  métrica, coração (frequência cardíaca em repouso, VFC, SpO2, VO2 máx., ECG, avisos de frequência cardíaca) e
  bem-estar.
- **Atividade:** passos, calorias e minutos de exercício com anéis e objetivos, treinos e a sua relação com o peso.
- **Sono:** a última noite com fases, saldo de sono de 7 noites, sestas, horário-alvo e análise. Os dados do
  AutoSleep e do Apple Watch são combinados com regras próprias (janela das 17:00 às 17:00, despertares, sestas).
- **Refeições:** uma pontuação diária do que comes, bebes e do exercício que fazes, e o seu efeito estimado no teu
  peso.
- **Íntimo:** ciclo (com previsão), atividade sexual e humor, protegidos por um PIN privado.
- **Ajuda** dentro da app: a ajuda de cada módulo, este README e o registo de alterações, no teu idioma.
- **Relatório em PDF** do período escolhido e **cópias de segurança completas** em JSON e CSV.
- **Interface:** temas claro e escuro, pensada para o telemóvel (instala-se como app a partir do navegador), gestos de
  deslizar, disposição para ecrãs largos até 1600 px.
- **Idiomas:** inglês (predefinido), espanhol, catalão, francês, italiano, alemão, português, neerlandês, chinês e
  japonês. Cada conta escolhe o seu; os e-mails chegam no idioma de quem os recebe.

### Contas

- **Várias contas**, cada uma com os seus dados, com acesso por nome de utilizador e palavra-passe.
- **Registo:** pedidos de acesso a partir da página de entrada, aprovados por um administrador (com avisos por
  e-mail), ou ligações de convite de utilização única.
- **Casais:** duas contas podem ser associadas para partilhar e editar em conjunto os registos de ciclo e
  intimidade.
- **Perfis:** cada conta pode ter vários perfis (com um PIN opcional), geridos em *A tua conta*.
- **Administração:** utilizadores (nome de utilizador, nome, e-mail, palavra-passe, interruptor de ativo, função de
  administrador), pedidos de acesso, convites, e-mail (SMTP), credenciais da aplicação Withings, cópias de segurança
  e fontes de dados.

### Dados que chegam sozinhos

- **Withings:** cada conta liga-se com OAuth; as pesagens, a composição, a atividade, os treinos, o sono, a SpO2, o
  VO2 máx. e o ECG são descarregados a cada poucos minutos, e de imediato quando a Withings avisa de uma nova
  medição.
- **Apple Saúde:** a app de iPhone *Health Auto Export* envia os dados para um endereço pessoal de cada conta.
- **Android:** a app BodyLens para Android (em `android/`) lê o Health Connect e envia a cada hora no mesmo formato.
- **Cópia de segurança diária** da base de dados às 03:30 (as últimas 30 são conservadas).

## Como está construída

```
browser / phone (PWA) ── HTTPS (reverse proxy) ──► BodyLens container
                                                   FastAPI + SQLite + scheduler
Withings (OAuth + webhook) ───────────────────────►│
Health Auto Export (iPhone) / Android app ────────►│  POST /api/ingest/hae/<token>
```

- **Frontend:** uma única página (`src/frontend/app/`), nascida como artefacto do claude.ai, servida com uma pequena
  camada (`src/frontend/compat/claude-shim.js`) que implementa, através da API do servidor, o que a página pedia
  antes ao claude.ai (`db`, `user`, `downloads`…).
- **Backend:** Python 3.12, FastAPI, SQLite (WAL) em `/data`, um único processo com o agendador lá dentro.
- **Traduções:** o catálogo está em inglês (`src/frontend/i18n/catalog.json`) e cada idioma é
  `src/frontend/i18n/locales/<lang>.json`. A página é traduzida no navegador por `src/frontend/i18n/i18n.js`,
  que também formata números e datas; o servidor usa os mesmos ficheiros para os e-mails. A ajuda (`help/en/`), este README e o registo de
  alterações estão escritos em inglês e são traduzidos automaticamente para o idioma de cada conta com a API do Claude
  (a chave define-se em Administração → Tradutor); cada tradução mantém-se até o texto em inglês mudar.
- **Segurança:** palavras-passe com argon2, sessões no servidor (cookie HttpOnly/Secure/SameSite), cabeçalho
  anti-CSRF em cada escrita, limites de frequência, cada conta isolada, tokens OAuth cifrados; segredos apenas em
  variáveis de ambiente ou na base de dados do servidor.

## Estrutura do repositório

```
src/backend/app/        server (package "app"), one subpackage per module:
  core/                 settings, SQLite, security, languages, backups, route dependencies
  accounts/             accounts, sessions, invitations, access requests, admin CLI
  admin/                Administration panel
  couples/              couples
  data/                 documents of each account and backup import
  help/                 the Help module (help, README and changelog, translated automatically)
  sheets/               the data tables and the XLSX workbook the page reads
  sources/              Withings and Apple Health / Android ingestion
  sync/                 synchronisation and scheduler
  mail/                 SMTP email
  web/                  page assembly and static files
src/frontend/
  app/                  the app (app_a: styles and views, app_b: core, app_c: interface)
  compat/               window.claude layer
  accounts/ admin/ common/   sign-in, request, registration, Your account and Administration pages
  i18n/                 translator, English catalog and one file per language
android/                Android app (Health Connect → server)
assets/branding/        icons and logo
tests/<module>/         tests (pytest) and tests/frontend/*.mjs (page and translator in jsdom)
help/en/                user help, one file per module (English; translated automatically in the app)
docker/                 Dockerfile and compose files (NAS, hot reload, development)
docs/DEPLOYMENT.md      deployment on a Synology NAS
tools/                  deployment, development server and translation tools
```

## Desenvolvimento

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e '.[test]'
```
```bash
.venv/bin/python -m pytest -q
```
```bash
(cd src/frontend && npm ci) && PYTHON=$PWD/.venv/bin/python node tests/frontend/smoke.mjs && node tests/frontend/i18n.mjs
```
```bash
tools/dev-data.sh && tools/dev.sh
```
O último comando arranca http://localhost:8000 com recarregamento a quente: a página é servida tal como está a
partir de `src/` (basta recarregar) e o backend reinicia ao guardar. `tools/dev-data.sh` copia os dados do servidor
para `data-dev/` (as alterações feitas em desenvolvimento nunca voltam). Também existe
`docker compose -f docker/compose.dev.yml up --build`.

## Implementação

Cada push para o ramo da versão atual (p. ex. `0.1.0`) executa os testes e publica a imagem
`jaimetur/bodylens:latest` (amd64 e arm64) no Docker Hub; `main` publica `jaimetur/bodylens:main`. No
servidor: `docker/compose.yml` mais um ficheiro `.env`. O NAS monta o código a partir da pasta do stack, por isso
`tools/deploy.sh` implementa um commit em segundos sem esperar por uma nova imagem. Passos completos:
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) (em inglês).

## Colaborar com traduções

Só precisas de inglês: consulta [`src/frontend/i18n/README.md`](src/frontend/i18n/README.md) (em inglês) para
adicionar um idioma ou melhorar um. A ajuda, o README e o registo de alterações são traduzidos automaticamente: só editas os ficheiros em inglês.

## Documentação

- Ajuda de utilização: [`help/`](help/en/README.md) (em inglês; também dentro da app, em *Ajuda*)
- Alterações de cada versão: [`CHANGELOG.md`](CHANGELOG.md)
- Instruções para agentes de código: [`AGENTS.md`](AGENTS.md)

Os dados pessoais nunca entram no repositório: as bases de dados, as cópias JSON e o `.env` estão no `.gitignore`.
