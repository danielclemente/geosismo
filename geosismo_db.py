"""
GEOSISMO — Dashboard Cloud + Modo Noturno
Uso:
    python geosismo_db.py --mapa  → Busca dados na nuvem e gera o HTML
"""

import sys
from datetime import datetime
from pathlib import Path

# Biblioteca do Supabase
try:
    from supabase import create_client, Client
except ImportError:
    print("❌ A biblioteca 'supabase' não está instalada.")
    print("   Rode no terminal: pip install supabase")
    sys.exit(1)

# ── 1. CONFIGURAÇÃO DA NUVEM ──────────────────────────────
URL = "https://ysjvujylzgtzysfsboub.supabase.co"
KEY = "sb_publishable_7OxVthi18jZYYMErbMG7fw_FdC7snK7"
supabase: Client = create_client(URL, KEY)


# ── 2. GERAÇÃO DO MAPA (Direto do Supabase) ───────────────
def gerar_mapa_nuvem():
    print("🛰️  Conectando ao Supabase para buscar a frota de Santos...")
    
    try:
        # Pega as 100 posições mais recentes que o GitHub salvou
        resposta = supabase.table("posicoes_onibus").select("*").order("timestamp", desc=True).limit(100).execute()
        onibus = resposta.data
    except Exception as e:
        print(f"❌ Erro ao acessar o Supabase: {e}")
        return

    # Se a tabela estiver vazia
    if not onibus:
        print("⚠️  Nenhum ônibus encontrado no banco de dados no momento.")
        # Podemos continuar para gerar o mapa vazio e testar o fundo preto

    markers = ""
    for bus in onibus:
        # Verifica e converte lat/lng para garantir que não dê erro no mapa
        try:
            lat = float(bus['latitude'])
            lng = float(bus['longitude'])
        except (ValueError, TypeError):
            continue # Pula se não tiver coordenada válida

        cor = "#2E8B57" if bus['sentido'] == "IDA" else "#4682B4"
        
        # O try/except aqui garante que não quebre se faltar o 'horario' no banco
        horario = bus.get('horario', 'N/A')
        popup = f"{bus['linha']} | Prefixo: {bus['prefixo']} | {bus['sentido']} | {horario}"
        
        markers += f"""
        L.circleMarker([{lat}, {lng}], {{
            radius: 8, color: '{cor}', fillColor: '{cor}',
            fillOpacity: 0.9, weight: 2
        }}).addTo(map).bindPopup('{popup}');
"""

    total = len(onibus)
    gerado = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>VigiaBus Santos — Mapa ao Vivo</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  body {{ margin: 0; background: #1a1a1a; font-family: Arial; color: white; }}
  #map {{ height: 100vh; }}
  #info {{
    position: absolute; top: 10px; right: 10px; z-index: 999;
    background: rgba(0,0,0,0.85); padding: 12px; border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.5); font-size: 13px; border: 1px solid #444;
  }}
  .ida {{ color: #2E8B57; font-weight: bold; }}
  .volta {{ color: #4682B4; font-weight: bold; }}
</style>
</head>
<body>
<div id="info">
  🚌 <b>Ônibus rastreados: {total}</b><br>
  🕐 Dados do Supabase: {gerado}<br><br>
  <span class="ida">● IDA</span> &nbsp;
  <span class="volta">● VOLTA</span>
</div>
<div id="map"></div>
<script>
var map = L.map('map').setView([-23.953, -46.333], 13);

// MODO NOTURNO (Dark Mode)
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
    attribution: '© OpenStreetMap © CARTO'
}}).addTo(map);

{markers}
</script>
</body>
</html>"""

    Path("mapa_onibus.html").write_text(html, encoding="utf-8")
    print(f"✅ Mapa gerado com sucesso: mapa_onibus.html ({total} ônibus rastreados)")
    print("👉 Abra o arquivo no Chrome para visualizar!")


# ── MAIN ──────────────────────────────────────────────────
def main():
    args = sys.argv[1:]

    # Agora o script principal foca apenas em gerar o mapa da nuvem
    if "--mapa" in args or not args:
        gerar_mapa_nuvem()

if __name__ == "__main__":
    main()