# TraveteFocus

App Android para quem trabalha **por peça** (travete, costura): lança a
produção do dia, acompanha a meta da semana e as faixas de pagamento, guarda o
histórico e transforma o trabalho num pequeno RPG — com XP, níveis, sequência
de dias e o **Yoru**, o espadachim que comemora cada conquista.

Visual HUD futurista (inspirado em *Sword Art Online*), animado e pensado para
rodar liso (60 quadros por segundo) num celular comum.

| Menu | Registro | Memórias |
|:---:|:---:|:---:|
| ![Menu](docs/capturas/menu.png) | ![Registro](docs/capturas/registro.png) | ![Memórias](docs/capturas/memorias.png) |
| **Progresso** | **Ganhos** | **Calculadora** |
| ![Progresso](docs/capturas/progresso.png) | ![Ganhos](docs/capturas/ganhos.png) | ![Calculadora](docs/capturas/calculadora.png) |

## O que o app faz

- **Registro diário** — lança cada lote (peça + quantidade, com ícone pelo tipo
  de roupa), ou cola a mensagem do WhatsApp e o app separa os lotes sozinho.
  Mostra quanto já saiu hoje e a meta do dia.
- **Memórias** — cada turno salvo (dia, peças, XP), o recorde em destaque,
  gráfico dos últimos dias e filtro por mês; exporta e manda pelo WhatsApp.
- **Progresso** — nível, XP, título, sequência de dias trabalhados e recordes.
- **Ganhos** — o período (semanal) aberto, a projeção em R$ e as **faixas de
  pagamento** da semana (ex.: R$ 0,25 → 0,27 a partir de 2.500 peças → 0,30 a
  partir de 3.000), quanto falta para a próxima e quanto por dia (o sábado entra
  como **previsão** de meio período, ajustável).
- **Calculadora** — contas rápidas com histórico.
- **Avisos na barra do celular** — lembrete para lançar (11h), meta do dia
  (16h), faixa ao alcance e resumo da semana (sábado). O botão **AVISOS** do
  menu mostra o que pode estar bloqueando e tem um **teste**.
- **Senha (PIN)** — guardada só como impressão digital (PBKDF2 com sal) no
  celular; errar 3 vezes bloqueia por um tempo crescente.

## Instalar

1. Baixe o `.apk` em **[Releases](../../releases)** (cada envio para `main`
   gera um APK novo automaticamente, em ~30 minutos).
2. Antes de atualizar, **exporte um backup** (Memórias → EXPORTAR).
3. Instale **por cima** do app antigo. **Nunca desinstale**: os dados ficam só
   no celular e iriam junto.

> **Privacidade:** nenhum dado sai do celular — produção, turnos, ganhos e a
> senha ficam no armazenamento do app. O repositório contém só o código.
> Troque a senha padrão no primeiro uso (botão **SENHA** do menu).

## Como o projeto é organizado

| Arquivo / pasta | O que é |
|---|---|
| `main.py` | Início do app: dados, telas, menu e avisos |
| `interface.kv` | O layout de todas as telas (Kivy) |
| `telas/` | Uma tela por arquivo: registro, memórias, progresso, ganhos, calculadora, abertura (senha) |
| `menu_hud.py` | O menu HUD (cabeçalho com o capacete NerveGear, painel, cartões) e o fundo animado das telas |
| `efeitos.py`, `animacoes_ui.py` | Botões, cartões, gráficos, barras, ícones de pixel e as animações da interface |
| `helpers.py` | Avisos (popups), teclado do app, trocas de tela |
| `metas.py` | As contas: semana, faixas de pagamento, meta do dia |
| `lembretes.py` + `java/` + `res_notif/` | Avisos na barra (AlarmManager + recebedor Java) |
| `kirito.py`, `cenas.py`, `yoru_*`, `bankai/` | O Yoru: desenho em pixel art, poses e as cenas animadas |
| `chefe*.py`, `chefe/`, `espadachim.py`, `infinito.py` | A abertura (a luta contra o chefe) e efeitos de espada |
| `notificacoes.py`, `som.py`, `tatil.py` | LEVEL UP, sons e vibração |
| `importar_zap.py`, `exportar.py`, `seguranca.py` | WhatsApp, exportação e a senha |
| `sons/`, `*.ttf`, `*.png` | Sons, fontes e ícones (créditos em `sons/CREDITOS.txt` e `OFL-*.txt`) |
| `dev/` | Ferramentas de desenvolvimento e testes (não vão para o APK) — veja `dev/LEIA-ME.txt` |
| `docs/` | Capturas de tela deste README (não vão para o APK) |
| `.github/` | O build do APK no GitHub Actions |

## Desenvolvimento

- **Kivy 2.3** (Python), empacotado com **buildozer / python-for-android**.
- O APK é gerado pelo GitHub Actions (`.github/workflows/build.yml`), assinado
  com a chave guardada nos *Secrets* do repositório. A versão vem do arquivo
  `VERSAO`.
- Testes no PC (Git Bash, dentro desta pasta): `bash dev/bateria_curta.sh`
  roda os cenários principais no tamanho do celular (toques de verdade,
  trocas de tela, avisos, fluidez quadro a quadro) e os testes das contas.
