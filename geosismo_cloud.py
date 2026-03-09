import os
import re
import requests
import urllib3
from datetime import datetime
from supabase import create_client, Client

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

if not URL or not KEY:
    print("❌ ERRO CRÍTICO: Chaves do Supabase não encontradas!")
    exit(1)

supabase: Client = create_client(URL, KEY)
BASE = "https://geosismo.piracicabana.com.br"
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

# Hashes fixos — não precisa mais buscar no site
LINHAS = {
    "CIRCULAR 004": "8699fb761982986b735bf58256a428cb28517b0c",
    "CIRCULAR 005": "ee2153ff64273d537abd8a267c9603177447affe",
    "CIRCULAR 007": "dbc9c6f4651ed3172a5a665bb97c6dceab9a31dd",
    "CIRCULAR 008": "61c867d5220e7f5097eb533067d66ba9d0355309",
    "CIRCULAR 010": "aef59cf3ad8decf0d82e366b6a5553f0431f694d",
    "CIRCULAR 013": "ceac37ac08a6bf547f61f9f9d2ee9ae312a14690",
    "CIRCULAR 017": "ccc3df43d6b7c0f2a4f14c587389a5e35da052ba",
    "CIRCULAR 019": "40161ecf9f429ee52e24540253a8d0f902673c30",
    "CIRCULAR 020": "f613360d64cfad09249eec2e1f082ef777687e16",
    "CIRCULAR 023": "3811183ccab2326e0748fd029481b0ab27d3d781",
    "CIRCULAR 025": "b48d0a5b187718cfeedb5f4340dcef98673b0625",
    "CIRCULAR 029": "804508b9af513c031197a11ea6e8abea34f2eb90",
    "CIRCULAR 030": "537bc12835c88ba787979f75f09e4864f615a71d",
    "CIRCULAR 037": "0f3493490ccb83ae2d5f49659934cf1e08c3a36d",
    "CIRCULAR 040": "722d378ae2af683f1156580267beea1d4f5fe583",
    "CIRCULAR 042": "a87f6fa4ed425fb2e6890c030b464eca1c8661e0",
    "CIRCULAR 052": "a82d12ff7356e27b364bbe7364de482a41d4a343",
    "CIRCULAR 053": "e982617d81a08c491bb03cc7ca5f8768b9594c47",
    "CIRCULAR 054": "948c22fd74b33d0d877c9d2f68a693bf3b25c0ac",
    "CIRCULAR 061": "87a468da8aea78033481ba3dde8eb47673cee8dc",
    "CIRCULAR 073": "2d8111afa83ffc8356821c21a835edb2749217ba",
    "CIRCULAR 077": "f2458b3691c4693efca5f5a9ecd9ab1b69fc86d7",
    "CIRCULAR 080": "4159bafd449ce1fa5eff7892412b225a3813678a",
    "CIRCULAR 100": "8afbd81ebf3d6e5d50a86a5c07687b94e6216fd2",
    "CIRCULAR 101": "b5494e71e4adeb802e75b406fab5b5b72b233215",
    "CIRCULAR 102": "ae29d7a90b59190be57fe32b4d0ad880df273aa5",
    "CIRCULAR 108": "b27492413f7909cb889c291ef79fe0f849fddc44",
    "CIRCULAR 118": "da589c4e446667b701c73117636674194e832ffd",
    "CIRCULAR 139": "3eae61cc20517b4592741ecbe117e46a14f5dbad",
    "CIRCULAR 152": "cf3802cced93abe176f6399ee930041956aba674",
    "CIRCULAR 153": "7055e7acaca6831b8764bc2f67e519e440fafde1",
    "CIRCULAR 154": "b978da5a5135b75fde4862eb993962cadf88867c",
    "CIRCULAR 155": "d70af4a7b8b8d701f2566c6f1d5fe38749d1e3bf",
    "CIRCULAR 156": "c321f828ed6aa319a016179c17173a28363dd4f2",
    "CIRCULAR 158": "a3822cdaf31a59d5f7d48b5a934372287f9733f4",
    "CIRCULAR 181": "f0e90fa15d406dfd4f6f12cd2361682ac164b44c",
    "CIRCULAR 184": "ac6f69b26c6dfe196dc6f215bafec5cbab5d7830",
    "CIRCULAR 191": "f590b2da8e435ea91b1399b0f1513866f03d53aa",
    "CIRCULAR 193": "5d1e29813a025933830be60eaddcf6796e1174a9",
    "CIRCULAR 194": "9b6164d5f4ac2f0fc2cc647c99ea47cfbdcd30c2",
    "CIRCULAR 198": "8f9122da3aa5c4632601d28aac6f763b53d20f39",
    "RE 200":        "c783e913593ba8caadabe7cd77b8b27cd1a850f1",
    "LINHA DO SAMBA":"ee3d871e02801cb156e62e9ff75e0985b8392d61",
}

def buscar_e_salvar():
    print(f"🚌 {len(LINHAS)} linhas configuradas. Consultando GPS...")
    batch_dados = []

    for nome, hash_val in LINHAS.items():
        try:
            res = session.post(
                BASE + "/consulta_linha.php",
                data={"idLinha": hash_val},
                timeout=20,
                verify=False
            )
            for item in re.finditer(r"\{prefixo:'([^']+)',lat:([\-\d.]+),lng:([\-\d.]+),\s*sentido:(\d+)", res.text):
                batch_dados.append({
                    "linha": nome,
                    "prefixo": item.group(1),
                    "latitude": float(item.group(2)),
                    "longitude": float(item.group(3)),
                    "sentido": "IDA" if item.group(4) == "1" else "VOLTA",
                    "horario": datetime.now().strftime("%H:%M"),
                    "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                })
        except Exception as e:
            print(f"⚠️ Erro em {nome}: {e}")

    print(f"📊 {len(batch_dados)} ônibus capturados.")

    if batch_dados:
        try:
            supabase.table("posicoes_onibus").insert(batch_dados).execute()
            print(f"✅ {len(batch_dados)} registros salvos no Supabase!")
        except Exception as e:
            print(f"❌ ERRO AO SALVAR: {e}")
    else:
        print("⚠️ Nenhum ônibus encontrado.")

if __name__ == "__main__":
    buscar_e_salvar()
