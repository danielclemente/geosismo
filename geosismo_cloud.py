import os
import re
import requests
import urllib3
from datetime import datetime
from supabase import create_client, Client

# Desativa os avisos de segurança da Piracicabana para deixar o log limpo
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurações do Supabase
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

if not URL or not KEY:
    print("❌ ERRO CRÍTICO: Chaves do Supabase não encontradas no ambiente do GitHub!")
    exit(1)

supabase: Client = create_client(URL, KEY)
BASE = "https://geosismo.piracicabana.com.br"
session = requests.Session()

def buscar_e_salvar():
    print("🔎 1. Buscando as linhas no site da Piracicabana...")
    try:
        r = session.get(BASE + "/", timeout=15, verify=False)
    except Exception as e:
        print(f"❌ Erro ao acessar o site: {e}")
        return
        
    batch_dados = []
    linhas_encontradas = list(re.finditer(r'<option value="([a-f0-9]{40})"[^>]*>([^<]+)</option>', r.text))
    print(f"🚌 2. Sucesso! {len(linhas_encontradas)} linhas encontradas. Puxando veículos das ruas de Santos...")

    for m in linhas_encontradas:
        hash_val, nome = m.group(1), m.group(2).strip()
        
        try:
            res_linha = session.post(BASE + "/consulta_linha.php", data={"idLinha": hash_val}, timeout=15, verify=False)
            
            # Varre os dados de cada ônibus
            for item in re.finditer(r"\{prefixo:'([^']+)',lat:([\-\d.]+),lng:([\-\d.]+),\s*sentido:(\d+)", res_linha.text):
                
                # Preenche a nova coluna que você criou no banco
                horario_atual = datetime.now().strftime("%H:%M")
                
                batch_dados.append({
                    "linha": nome,
                    "prefixo": item.group(1),
                    "latitude": float(item.group(2)),
                    "longitude": float(item.group(3)),
                    "sentido": "IDA" if item.group(4) == "1" else "VOLTA",
                    "horario": horario_atual, # <--- SUA NOVA COLUNA AQUI
                    "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                })
        except Exception as e:
            print(f"⚠️ Erro ao puxar a linha {nome}: {e}")

    print(f"📊 3. Total de {len(batch_dados)} ônibus capturados. Tentando abrir a porta do Supabase...")

    # Manda para o Supabase
    if batch_dados:
        try:
            supabase.table("posicoes_onibus").insert(batch_dados).execute()
            print(f"✅ SUCESSO ABSOLUTO! {len(batch_dados)} ônibus estacionados no banco de dados!")
        except Exception as e:
            print(f"❌ ERRO AO SALVAR NO SUPABASE: {e}")
    else:
        print("⚠️ Nenhum ônibus rodando no momento.")

if __name__ == "__main__":
    buscar_e_salvar()