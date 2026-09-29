R = r'C:\Users\kirit\travetefocus\app'
import os


def troca(p, a, b):
    c = open(os.path.join(R, p), encoding='utf-8').read()
    assert c.count(a) == 1, (p, a[:70], c.count(a))
    open(os.path.join(R, p), 'w', encoding='utf-8').write(c.replace(a, b))


# ── build: a chave vai para um arquivo proprio (o Gradle segue com a dele) e
#    o APK e re-assinado depois, sem travar o build se a chave nao abrir ──
troca('.github/workflows/build.yml', '''      - name: Restaurar keystore de assinatura
        env:
          KS_B64: ${{ secrets.KEYSTORE_BASE64 }}
        run: |
          mkdir -p ~/.android
          if [ -z "$KS_B64" ]; then
            echo "::error::Falta o secret KEYSTORE_BASE64 (Settings > Secrets and variables > Actions). Sem ele cada APK sai com uma chave diferente e o celular nao atualiza (App nao instalado)."
            exit 1
          fi
          echo "$KS_B64" | base64 -d > ~/.android/debug.keystore''', '''      - name: Restaurar keystore de assinatura
        env:
          KS_B64: ${{ secrets.KEYSTORE_BASE64 }}
        run: |
          # A chave vai para um arquivo proprio: o Gradle assina com a chave
          # de debug dele e, no fim, o APK e assinado de novo com esta.
          mkdir -p ~/.android
          if [ -z "$KS_B64" ]; then
            echo "::warning::Falta o secret KEYSTORE_BASE64: o APK sai com chave temporaria (para instalar vai precisar apagar o app)."
            exit 0
          fi
          echo "$KS_B64" | base64 -d > ~/.android/travete.keystore
          echo "[KEYSTORE] $(wc -c < ~/.android/travete.keystore) bytes restaurados"
          exit 0''')
c = open(os.path.join(R, '.github/workflows/build.yml'), encoding='utf-8').read()
# tira as linhas antigas que mexiam no debug.keystore do Gradle
a = c.index('          echo "[KEYSTORE] $(wc -c < ~/.android/travete.keystore) bytes restaurados"\n          exit 0')
b = c.index('      # ── 7. VARIÁVEIS ANDROID')
fim_bloco = '          echo "[KEYSTORE] $(wc -c < ~/.android/travete.keystore) bytes restaurados"\n          exit 0\n\n'
c = c[:a] + fim_bloco + c[b:]
open(os.path.join(R, '.github/workflows/build.yml'), 'w', encoding='utf-8').write(c)

troca('.github/workflows/build.yml', '''          sed -i "s/^version = .*/version = 1.0.${{ github.run_number }}/" buildozer.spec
          grep -n "^version" buildozer.spec''', '''          sed -i "s/^version = .*/version = 1.0.${{ github.run_number }}/" buildozer.spec
          grep -n "^version" buildozer.spec
          # o app mostra a versao no rodape do menu
          echo '{"versao": "1.0.${{ github.run_number }}"}' > versao.json''')
troca('.github/workflows/build.yml', '''      - name: Assinar o APK sempre com a mesma chave
        run: |
          APK=$(ls bin/*.apk | head -n 1)
          BT=$(ls -d $ANDROID_HOME/build-tools/*/ | sort -V | tail -n 1)
          "${BT}apksigner" sign --ks ~/.android/debug.keystore --ks-pass pass:android --key-pass pass:android "$APK"
          "${BT}apksigner" verify --print-certs "$APK" | grep -i "SHA-256"''', '''      - name: Assinar o APK sempre com a mesma chave
        run: |
          APK=$(ls bin/*.apk | head -n 1)
          BT=$(ls -d $ANDROID_HOME/build-tools/*/ | sort -V | tail -n 1)
          ESPERADA="94ef9ec68ebd71c6ce1cc15936c440985a0fbd5900f04694009bb3bbd50709eb"
          if [ -s ~/.android/travete.keystore ] && \\
             "${BT}apksigner" sign --ks ~/.android/travete.keystore --ks-pass pass:android --key-pass pass:android "$APK"; then
            DIG=$("${BT}apksigner" verify --print-certs "$APK" | grep -i "SHA-256 digest" | head -n 1 | awk '{print $NF}')
            echo "Impressao digital do APK: $DIG"
            if [ "$DIG" = "$ESPERADA" ]; then
              echo "::notice::APK assinado com a chave fixa do TraveteFocus: atualiza por cima."
            else
              echo "::warning::APK assinado com uma chave diferente da esperada ($DIG)."
            fi
          else
            echo "::warning::A chave do secret KEYSTORE_BASE64 nao abriu (senha android): o APK saiu com chave temporaria. Troque o secret pelo conteudo de keystore_novo_base64.txt."
          fi''')

# ── app: versao no rodape do menu ──
troca('main.py', '''    periodos_ganhos = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)''', '''    periodos_ganhos = ListProperty([])
    versao          = StringProperty("dev")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:                                   # escrito pelo build do GitHub
            import json
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'versao.json'),
                      encoding='utf-8') as f:
                self.versao = str(json.load(f).get('versao', 'dev'))
        except Exception:
            pass''')
troca('interface.kv', '''                text:      "[ SISTEMA OPERACIONAL DE CONFECÇÃO ]"''',
      '''                text:      "[ SISTEMA OPERACIONAL DE CONFECÇÃO  ·  v" + app.versao + " ]"''')
print('ok')
