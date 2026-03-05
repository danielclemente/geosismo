import time
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuração
DOWNLOAD_FOLDER = r"C:\Users\daniel.csilva76\Documents\SICWEB"
CHAVE = "C76FAD09E"

# Criar pasta
Path(DOWNLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

# Configurar Chrome
chrome_options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": DOWNLOAD_FOLDER,
    "download.prompt_for_download": False,
    "plugins.always_open_pdf_externally": True,
    "profile.default_content_settings.popups": 0,
}
chrome_options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 15)

try:
    # LOGIN
    print("🔐 Login...")
    driver.get("https://egov.santos.sp.gov.br/sicweb/")
    time.sleep(2)
    
    # Clicar "Meus Pedidos"
    wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Meus Pedidos"))).click()
    time.sleep(2)
    
    # Inserir chave
    driver.execute_script("""
        let modal = document.querySelector('.modal.show');
        if(modal) {
            let inputs = modal.querySelectorAll('input[type="text"]');
            for(let input of inputs) {
                if(!input.id.includes('CPF')) {
                    input.value = arguments[0];
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    break;
                }
            }
        }
    """, CHAVE)
    time.sleep(1)
    
    # Clicar Consultar
    driver.execute_script("""
        let modal = document.querySelector('.modal.show');
        if(modal) {
            let buttons = modal.querySelectorAll('button');
            for(let btn of buttons) {
                if(btn.textContent.includes('Consultar')) {
                    btn.click();
                    break;
                }
            }
        }
    """)
    
    print("⏳ Aguardando lista...")
    time.sleep(4)
    
    # EXTRAIR PROTOCOLOS
    html = driver.page_source
    protocolos = list(set(re.findall(r'\b(\d{3,5}/20\d{2})\b', html)))
    
    print(f"\n✅ {len(protocolos)} protocolos encontrados")
    print("="*60)
    
    # PROCESSAR CADA PROTOCOLO
    for idx, protocolo in enumerate(protocolos, 1):
        print(f"\n[{idx}/{len(protocolos)}] {protocolo}")
        
        try:
            # Clicar no botão Visualizar
            clicked = driver.execute_script(f"""
                let protocol = "{protocolo}";
                let all = document.querySelectorAll('*');
                
                for(let elem of all) {{
                    if(elem.textContent.includes(protocol)) {{
                        let parent = elem;
                        for(let i = 0; i < 5; i++) {{
                            if(!parent) break;
                            let btns = parent.querySelectorAll('button');
                            for(let btn of btns) {{
                                if(btn.textContent.toLowerCase().includes('visualizar')) {{
                                    if(parent.textContent.includes(protocol)) {{
                                        btn.scrollIntoView({{block: 'center'}});
                                        btn.click();
                                        return true;
                                    }}
                                }}
                            }}
                            parent = parent.parentElement;
                        }}
                    }}
                }}
                return false;scr
            """)
            
            if not clicked:
                print("  ⚠️ Botão não encontrado, pulando...")
                continue
            
            time.sleep(3)
            
            # Aguardar página carregar
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            
            # Clicar em Imprimir
            print("  📄 Clicando em Imprimir...")
            pdf_clicked = driver.execute_script("""
                let buttons = document.querySelectorAll('button, a');
                for(let elem of buttons) {
                    let text = elem.textContent.toLowerCase();
                    if(text.includes('imprimir') || text.includes('pdf')) {
                        elem.click();
                        return true;
                    }
                }
                return false;
            """)
            
            if pdf_clicked:
                time.sleep(4)  # Aguardar download
                
                # Renomear XReport.pdf
                xreport = Path(DOWNLOAD_FOLDER) / "XReport.pdf"
                if xreport.exists():
                    novo_nome = Path(DOWNLOAD_FOLDER) / f"{protocolo.replace('/', '_')}.pdf"
                    try:
                        xreport.rename(novo_nome)
                        print(f"  ✅ Salvo: {novo_nome.name}")
                    except:
                        print(f"  ⚠️ Erro ao renomear")
                else:
                    print(f"  ⚠️ PDF não encontrado")
            else:
                print(f"  ⚠️ Botão Imprimir não encontrado")
            
            # Fechar abas extras
            main_window = driver.window_handles[0]
            for window in driver.window_handles[1:]:
                driver.switch_to.window(window)
                driver.close()
            driver.switch_to.window(main_window)
            
            # Voltar para lista
            driver.back()
            time.sleep(2)
            
        except Exception as e:
            print(f"  ❌ Erro: {e}")
            try:
                driver.back()
                time.sleep(2)
            except:
                pass
    
    print("\n" + "="*60)
    print("🎉 CONCLUÍDO!")
    print(f"📁 Arquivos em: {DOWNLOAD_FOLDER}")
    print("="*60)

except Exception as e:
    print(f"\n💥 Erro fatal: {e}")

finally:
    input("\nPressione ENTER para fechar...")
    driver.quit()