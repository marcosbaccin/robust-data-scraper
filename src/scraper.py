import time
import os
import re
import pandas as pd
import pandera as pa
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from schema import KabumSchema
from selenium.webdriver.common.action_chains import ActionChains
from sqlalchemy import create_engine, text

class KabumScraper:
    def __init__(self, termo_busca="placas-de-video-vga"):
        self.base_url = "https://www.kabum.com.br/hardware"
        self.termo_busca = termo_busca
        self.driver = None

    def setup_driver(self):
        options = Options()
        # Opções para Docker/Headless
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Modo Stealth
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        selenium_host = os.getenv("SELENIUM_HOST")
        
        if selenium_host:
            print(f"🌍 Tentando conectar ao Remote WebDriver em: {selenium_host}")
            
            # --- BLOCO DE RETRY (RESILIÊNCIA) ---
            max_retries = 10
            for attempt in range(max_retries):
                try:
                    self.driver = webdriver.Remote(
                        command_executor=selenium_host,
                        options=options
                    )
                    print("✅ Conexão com Selenium Grid estabelecida!")
                    return
                except Exception as e:
                    print(f"⏳ Tentativa {attempt+1}/{max_retries} falhou. O Selenium ainda está acordando... ({e})")
                    time.sleep(3)
            
            raise Exception("❌ Falha crítica: Não foi possível conectar ao Selenium após várias tentativas.")
            
        else:
            # Modo Local
            options.add_argument("--start-maximized")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            self.driver = webdriver.Chrome(options=options)

    def _clean_price(self, price_str: str) -> float:
        """Método auxiliar (privado) para limpar a string de preço."""
        if not price_str:
            return 0.0
        try:
            # Remove tudo que não é dígito ou vírgula
            clean = re.sub(r'[^\d,]', '', price_str)
            # Troca vírgula por ponto para o Python entender
            return float(clean.replace(',', '.'))
        except ValueError:
            return 0.0

    def get_products(self):
        full_url = f"{self.base_url}/{self.termo_busca}"
        print(f"🚀 Iniciando coleta em: {full_url}")
        
        self.driver.get(full_url)
        
        try:
            # ESTRATÉGIA 1: Espera baseada em CONTEÚDO, não em estrutura.
            # Se aparecer "R$" na tela, significa que os preços carregaram.
            print("⏳ Aguardando carregamento dos preços...")
            WebDriverWait(self.driver, 20).until(
                EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "R$")
            )
            
            # Scroll para garantir que o Lazy Load dispare
            self.driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠️ Erro de Timeout. O site carregou?")
            return []

        products_data = []
        
        # ESTRATÉGIA 2: Busca por TAG HTML (Semântica)
        # Ignoramos classes e IDs. Buscamos qualquer <article> na página.
        # Geralmente cards de produto são <article>
        cards = self.driver.find_elements(By.TAG_NAME, "article")
        
        print(f"📦 Encontrados {len(cards)} cards (Tentativa via tag <article>).")

        # Fallback: Se não achar article, tenta buscar divs que contenham preço
        if len(cards) == 0:
            print("⚠️ Tag <article> não encontrada. Tentando estratégia de fallback...")
            cards = self.driver.find_elements(By.XPATH, "//div[contains(., 'R$') and contains(@class, 'Card')]")

        for i, card in enumerate(cards):
            if i > 15: break 
            
            try:
                # --- MELHORIA NA EXTRAÇÃO DO NOME ---
                nome = "Nome Indisponível"
                
                # Tentativa 1: O 'alt' da imagem costuma ser o nome limpo e completo
                try:
                    img_elem = card.find_element(By.TAG_NAME, "img")
                    nome_alt = img_elem.get_attribute("title") # Às vezes é 'alt', às vezes 'title' na Kabum
                    if not nome_alt:
                        nome_alt = img_elem.get_attribute("alt")
                    
                    if nome_alt and len(nome_alt) > 5:
                        nome = nome_alt
                except:
                    pass

                # Tentativa 2: Se falhar, busca classes que contenham 'name' ou 'title'
                if nome == "Nome Indisponível":
                    try:
                        nome = card.find_element(By.CSS_SELECTOR, "span[class*='name'], h2").text
                    except:
                        pass
                
                # Preço e Link continuam iguais...
                texto_card = card.text
                match = re.search(r'R\$\s?[\d\.,]+', texto_card)
                
                if match:
                    preco_raw = match.group(0)
                else:
                    continue 

                # Link
                try:
                    link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                except:
                    link = self.driver.current_url

                products_data.append({
                    "nome_produto": nome,
                    "preco_pix": self._clean_price(preco_raw),
                    "link": link,
                    "data_coleta": pd.Timestamp.now()
                })
                
            except Exception as e:
                continue

        return products_data
    
    def save_to_db(self, df):
        """Salva o DataFrame no PostgreSQL."""
        db_url = os.getenv("DB_CONNECTION_STRING")
        
        if not db_url:
            print("⚠️ Nenhuma string de conexão encontrada. Pulando salvamento no banco.")
            return

        try:
            print("💾 Conectando ao Banco de Dados...")
            engine = create_engine(db_url)
            
            # Salva no banco. 
            # 'if_exists="append"' adiciona os dados novos sem apagar os velhos.
            # 'index=False' não salva o índice numérico do Pandas (0, 1, 2...).
            df.to_sql('precos_placas_video', con=engine, if_exists='append', index=False)
            
            print(f"✅ {len(df)} registros salvos na tabela 'precos_placas_video'!")
            
        except Exception as e:
            print(f"❌ Erro ao salvar no banco: {e}")

    def run(self):
        try:
            self.setup_driver()
            raw_data = self.get_products()
        finally:
            if self.driver:
                self.driver.quit()

        if not raw_data:
            print("❌ Nenhum dado coletado.")
            return None

        df = pd.DataFrame(raw_data)

        print("🔍 Validando dados...")
        try:
            validated_df = KabumSchema.validate(df, lazy=True)
            print("✅ Sucesso! Dados validados.")
            
            self.save_to_db(validated_df)
            
            return validated_df
        except pa.errors.SchemaErrors as err:
            print("❌ Dados fora do padrão contratado:")
            print(err.failure_cases)
            return df

if __name__ == "__main__":
    scraper = KabumScraper()
    scraper.run()