import os
import re
import requests
from datetime import datetime
from supabase import create_client, Client

# Configurações do Supabase
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(URL, KEY)

BASE = "https://geosismo.piracicabana.com.br"
session = requests.Session()

def buscar_e_salvar():
    # 1. Pega as linhas
    r = session.get(BASE + "/", timeout=15, verify=False)
    batch_dados = []
    
    # 2. Varre cada linha para achar os onibus
    for m in re.finditer(r'<option value="([a-f0-9]{40})"[^>]*>([^<]+)</option>', r.text):
        hash_val, nome = m.group(1), m.group(2).strip()
        
        # Consulta os veículos daquela linha
        res_linha = session.post(BASE + "/consulta_linha.php", data={"idLinha": hash_val}, timeout=15, verify=False)
        
        for item in re.finditer(r"\{prefixo:'([^']+)',lat:([\-\d.]+),lng:([\-\d.]+),\s*sentido:(\d+)", res_linha.text):
            batch_dados.append({
                "linha": nome,
                "prefixo": item.group(1),
                "latitude": float(item.group(2)),
                "longitude": float(item.group(3)),
                "sentido": "IDA" if item.group(4) == "1" else "VOLTA",
                "timestamp": datetime.now().isoformat()
            })

    # 3. Manda para o Supabase (tabela: posicoes_onibus)
    if batch_dados:
        supabase.table("posicoes_onibus").insert(batch_dados).execute()
        print(f"✅ {len(batch_dados)} ônibus de Santos salvos!")

if __name__ == "__main__":
    buscar_e_salvar()
