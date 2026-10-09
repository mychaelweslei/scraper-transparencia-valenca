import os
from urllib.parse import urljoin
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ==================== VARIÁVEIS DE CONFIGURAÇÃO ====================
# Cole aqui a URL da página (seja de 2026 com subitens ou de 2015 com lista direta)
URL_SITE = ''

# Diretório base onde a pasta principal/subpastas serão criadas
CAMINHO_BASE = r''
# ===================================================================


def executar_automacao_inteligente():
  os.makedirs(CAMINHO_BASE, exist_ok=True)

  options = Options()
  # options.add_argument("--headless")  # Descomente se quiser rodar sem abrir a janela do navegador

  print('Iniciando o navegador...')
  driver = webdriver.Chrome(options=options)

  try:
    driver.get(URL_SITE)
    print(f'Acessando: {URL_SITE}')

    # Aguarda o carregamento inicial da página
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, 'body'))
    )

    # 1. Verifica se a página possui blocos de acordeão (<details>)
    detalhes_pregoes = driver.find_elements(By.XPATH, '//details')

    baixados_total = 0

    if detalhes_pregoes:
      print(
          f'Modo Acordeão Detectado: Encontrados {len(detalhes_pregoes)}'
          ' subitens.'
      )

      for index, detalhe in enumerate(detalhes_pregoes, start=1):
        try:
          summary_elem = detalhe.find_element(By.TAG_NAME, 'summary')
          nome_pregao = summary_elem.text.strip()

          if not nome_pregao:
            nome_pregao = f'Pregao_{index}'

          # Força a abertura do elemento details via JavaScript
          driver.execute_script(
              "arguments[0].setAttribute('open', 'true');", detalhe
          )

          nome_pasta_limpo = (
              nome_pregao.replace('/', '-')
              .replace(':', '')
              .replace('º', 'o')
              .strip()
          )
          pasta_destino = os.path.join(CAMINHO_BASE, nome_pasta_limpo)

          links_pdf = detalhe.find_elements(By.TAG_NAME, 'a')
          pdfs_para_baixar = []

          for link in links_pdf:
            href = link.get_attribute('href')
            texto_link = link.text.strip()
            if href and (
                '.pdf' in href.lower() or '.pdf' in texto_link.lower()
            ):
              url_completa = urljoin(URL_SITE, href)
              pdfs_para_baixar.append((url_completa, texto_link))

          if pdfs_para_baixar:
            os.makedirs(pasta_destino, exist_ok=True)
            print(f'\nPasta criada: {pasta_destino}')

            for url_pdf, nome_link in pdfs_para_baixar:
              if not nome_link.lower().endswith('.pdf'):
                nome_arquivo = (
                    nome_link if len(nome_link) > 3 else 'documento_anexo'
                )
                nome_arquivo += '.pdf'
              else:
                nome_arquivo = nome_link

              nome_arquivo_limpo = ''.join(
                  c
                  for c in nome_arquivo
                  if c.isalnum() or c in (' ', '.', '_', '-')
              ).strip()
              if not nome_arquivo_limpo.endswith('.pdf'):
                nome_arquivo_limpo += '.pdf'

              caminho_completo = os.path.join(pasta_destino, nome_arquivo_limpo)

              print(f'   Baixando: {nome_arquivo_limpo}...')
              r_pdf = requests.get(url_pdf)
              if r_pdf.status_code == 200:
                with open(caminho_completo, 'wb') as f:
                  f.write(r_pdf.content)
                baixados_total += 1
              else:
                print(f'   Erro ao baixar (Status {r_pdf.status_code})')
        except Exception as e:
          print(f'Erro ao processar bloco {index}: {e}')

    else:
      print(
          'Modo de Pasta Única Detectado (Sem subitens / estilo 2015)'
          '.'
      )

      # Pega o título principal da página usando o XPath que você enviou: //*[@id="root"]/div[11]/div/div/header/div/h1
      try:
        titulo_elem = driver.find_element(
            By.XPATH, '//*[@id="root"]/div[11]/div/div/header/div/h1'
        )
        nome_pasta_principal = titulo_elem.text.strip()
      except:
        # Fallback caso o ID mude de div[11] para outro número em outra página
        try:
          nome_pasta_principal = driver.find_element(
              By.TAG_NAME, 'h1'
          ).text.strip()
        except:
          nome_pasta_principal = 'Pregoes_Geral'

      if not nome_pasta_principal:
        nome_pasta_principal = 'Pregoes_Geral'

      nome_pasta_limpo = (
          nome_pasta_principal.replace('/', '-')
          .replace(':', '')
          .replace('º', 'o')
          .strip()
      )
      pasta_destino = os.path.join(CAMINHO_BASE, nome_pasta_limpo)

      # Varre todos os links de PDF da página inteira
      todos_links = driver.find_elements(By.TAG_NAME, 'a')
      pdfs_para_baixar = []

      for link in todos_links:
        href = link.get_attribute('href')
        texto_link = link.text.strip()
        if href and ('.pdf' in href.lower() or '.pdf' in texto_link.lower()):
          url_completa = urljoin(URL_SITE, href)
          pdfs_para_baixar.append((url_completa, texto_link))

      if pdfs_para_baixar:
        os.makedirs(pasta_destino, exist_ok=True)
        print(f'\nPasta Única Criada: {pasta_destino}')

        for url_pdf, nome_link in pdfs_para_baixar:
          if not nome_link.lower().endswith('.pdf'):
            nome_arquivo = (
                nome_link if len(nome_link) > 3 else 'documento_anexo'
            )
            nome_arquivo += '.pdf'
          else:
            nome_arquivo = nome_link

          nome_arquivo_limpo = ''.join(
              c for c in nome_arquivo if c.isalnum() or c in (' ', '.', '_', '-')
          ).strip()
          if not nome_arquivo_limpo.endswith('.pdf'):
            nome_arquivo_limpo += '.pdf'

          caminho_completo = os.path.join(pasta_destino, nome_arquivo_limpo)

          print(f'   Baixando: {nome_arquivo_limpo}...')
          r_pdf = requests.get(url_pdf)
          if r_pdf.status_code == 200:
            with open(caminho_completo, 'wb') as f:
              f.write(r_pdf.content)
            baixados_total += 1
          else:
            print(f'   Erro ao baixar (Status {r_pdf.status_code})')

    print(f'\nProcesso concluído! Total de PDFs baixados: {baixados_total}')

  finally:
    driver.quit()


if __name__ == '__main__':
  executar_automacao_inteligente()