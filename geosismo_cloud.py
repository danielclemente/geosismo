import os
import requests
import time
from supabase import create_client, Client

# Configurações do Supabase (Lidas das variáveis de ambiente)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Erro: Variáveis de ambiente SUPABASE_URL ou SUPABASE_KEY não configuradas.")
    exit()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def buscar_e_salvar():
    print(f"[{time.strftime('%H:%M:%S')}] Iniciando rastreio em Santos...")
    
    # URL da API da Piracicabana (ajustada conforme o projeto Geosismo)
    api_url = "https://quantotempofalta.piracicabana.com.br/api/consultar-linhas"
    
    try:
        response = requests.get(api_url, timeout=15)
        linhas = response.json()
        
        batch_dados = []
        for linha in linhas:
            # Aqui simulamos a extração dos dados de cada veículo
            # O script percorre as linhas e identifica os prefixos ativos
            veiculos = linha.get("veiculos", [])
            for v in veiculos:
                batch_dados.append({
                    "linha": linha.get("nome"),
                    "prefixo": v.get("prefixo"),
                    "sentido": v.get("sentido"),
                    "latitude": float(v.get("lat")),
                    "longitude": float(v.get("lng"))
                })
        
        if batch_dados:
            # Inserção em massa no Supabase (mais eficiente)
            supabase.table("posicoes_onibus").insert(batch_dados).execute()
            print(f"✅ {len(batch_dados)} ônibus salvos no banco!")
        else:
            print("⚠️ Nenhum ônibus encontrado no momento.")

    except Exception as e:
        print(f"❌ Falha na coleta: {e}")

if __name__ == "__main__":
    buscar_e_salvar()