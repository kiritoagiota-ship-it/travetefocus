"""Build: o APK vai para a pagina Releases (tag apk-mais-recente, so o mais
novo fica) em vez de "artifact" - o espaco de artifacts da conta enche com os
APKs antigos (ficam 90 dias) e derrubava o build no fim. O log do build
continua como artifact por 3 dias, sem derrubar o build se nao couber."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, '.github', 'workflows', 'build.yml'), [
    ("""  build-apk:
    name: Build Android Debug APK
    runs-on: ubuntu-22.04
    timeout-minutes: 90
""", """  build-apk:
    name: Build Android Debug APK
    runs-on: ubuntu-22.04
    timeout-minutes: 90
    permissions:
      contents: write          # publicar o APK na pagina Releases
"""),
    ("""      - name: Upload APK gerado
        uses: actions/upload-artifact@v4
        with:
          name: travetefocus-debug-apk
          path: bin/*.apk
          if-no-files-found: error

      - name: Upload do log completo de build
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: build-log
          path: build.log
          if-no-files-found: ignore""", """      # ── 12. APK NA PAGINA RELEASES ─────────────────────────────────────────
      # O APK vai para a pagina "Releases" do repositorio (tag apk-mais-recente).
      # Nao ocupa o espaco de artifacts (que enche com os APKs antigos e
      # derrubava o build) e so fica o APK mais novo.
      - name: Publicar APK na pagina Releases
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          APK=$(ls bin/*.apk | head -n 1)
          NOVO="bin/TraveteFocus-1.0.${{ github.run_number }}.apk"
          cp "$APK" "$NOVO"
          gh release delete apk-mais-recente --yes --cleanup-tag || true
          gh release create apk-mais-recente "$NOVO" --target "${{ github.sha }}" --latest --title "TraveteFocus 1.0.${{ github.run_number }}" --notes "APK mais recente do TraveteFocus. Baixe o arquivo .apk abaixo e instale por cima do app."
          echo "::notice::APK publicado em Releases: TraveteFocus 1.0.${{ github.run_number }}"

      - name: Upload do log completo de build
        if: always()
        continue-on-error: true
        uses: actions/upload-artifact@v4
        with:
          name: build-log
          path: build.log
          retention-days: 3
          if-no-files-found: ignore"""),
])
print('ok')
