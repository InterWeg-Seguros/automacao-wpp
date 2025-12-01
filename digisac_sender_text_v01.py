#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io, os, re, csv, json, base64, time, argparse
from pathlib import Path
from typing import Optional
import requests

# ============== ENV ==========================
def load_env_file(path: str = ".env"):
    if not os.path.exists(path):
        return
    for line in open(path, "r", encoding="utf-8"):
        m = re.match(r'\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$', line)
        if not m:
            continue
        k, v = m.group(1), m.group(2)
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        os.environ.setdefault(k, v)

# ============== UTILS ========================
def normalize_phone(raw: str) -> str:
    s = (str(raw) or "").strip()
    s = "".join(ch for ch in s if ch.isdigit())
    s = s.lstrip("0")
    if len(s) >= 10 and not s.startswith("55"):
        s = "55" + s
    return s

def read_image_bytes(src: str) -> bytes:
    if src.startswith(("http://", "https://")):
        r = requests.get(src, timeout=20)
        r.raise_for_status()
        return r.content
    p = Path(src)
    if not p.exists():
        raise FileNotFoundError(f"Imagem não encontrada: {src}")
    return p.read_bytes()

def ensure_jpeg_bytes(img_bytes: bytes) -> bytes:
    """
    Converte qualquer coisa abrível pela Pillow para JPEG (RGB) com qualidade 85.
    Se já for JPEG, retorna como está.
    """
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(img_bytes))
        # Se já é JPEG puro, devolve original
        if (getattr(im, "format", "") or "").upper() == "JPEG":
            return img_bytes
        # Converte para RGB e salva como JPEG
        out = io.BytesIO()
        im.convert("RGB").save(out, format="JPEG", quality=85, optimize=True)
        return out.getvalue()
    except Exception:
        # Se não conseguir abrir, envia original mesmo (pode falhar na API)
        return img_bytes

def to_base64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")

# ============== CSV IO =======================
FIELDNAMES = ["linha","telefone","status","http","detalhe"]

def load_contacts_csv(path: str):
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(2048); f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
        except Exception:
            class _D: delimiter = ","
            dialect = _D()
        reader = csv.reader(f, dialect)
        header = [ (h or "").strip().lower().replace("\ufeff","") for h in next(reader, []) ]
        try:
            idx_tel = next(i for i,h in enumerate(header) if h in ("telefone","celular","celular.1","fone","phone","number"))
        except StopIteration:
            raise ValueError(f"Header não tem coluna de telefone: {header}")
        idx_nome = None
        for i,h in enumerate(header):
            if h in ("nome","name"):
                idx_nome = i; break
        for line in reader:
            if not any(line):
                continue
            telefone = normalize_phone(line[idx_tel] if idx_tel < len(line) else "")
            nome = (line[idx_nome].strip() if (idx_nome is not None and idx_nome < len(line)) else "")
            if telefone:
                rows.append({"nome": nome, "telefone": telefone})
    return rows

def append_row(csv_path, linha, telefone, status, http, detalhe_dict):
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists or os.path.getsize(csv_path) == 0:
            w.writeheader()
        w.writerow({
            "linha": linha,
            "telefone": telefone,
            "status": status,
            "http": http,
            "detalhe": json.dumps(detalhe_dict, ensure_ascii=False, separators=(",",":"))
        })

# ============== SENDER =======================
def send_image_with_caption_base64(api_base_v1: str, token: str, number: str,
                                   service_id: str, text: str,
                                   img_src: str, filename: Optional[str] = None):
    """
    Envia para POST {API_BASE_V1}/messages com:
    {
      "text": "...",
      "number": "...",
      "serviceId": "...",
      "file": {"base64": "...", "mimetype": "image/jpeg", "name": "..."}
    }
    """
    raw = read_image_bytes(img_src)
    jpg = ensure_jpeg_bytes(raw)
    # limite DigiSac: 63 MB
    if len(jpg) > 63*1024*1024:
        raise ValueError(f"Arquivo > 63MB ({len(jpg)} bytes)")

    b64 = to_base64(jpg)
    name = filename or (Path(img_src).name if not img_src.startswith("http") else "image.jpg")

    payload = {
        "text": (text or "").strip(),
        "number": number,
        "serviceId": service_id,
        "file": {
            "base64": b64,
            "mimetype": "image/jpeg",
            "name": name if name.lower().endswith(".jpg") or name.lower().endswith(".jpeg") else f"{Path(name).stem}.jpg"
        }
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{api_base_v1.rstrip('/')}/messages"
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        body = r.text[:800] if r is not None else ""
        raise requests.HTTPError(f"{e} | body={body}") from None
    return r.json()

# ============== MAIN =========================
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="teste.csv", help="CSV com colunas (nome, telefone/number)")
    ap.add_argument("--limit", type=int, default=0, help="Limite de contatos (0=todos)")
    args = ap.parse_args()

    load_env_file()

    API_V1 = (os.getenv("DIGISAC_API_URL") or "").rstrip("/")   # ex: https://interweg.digisac.chat/api/v1
    TOKEN  = os.getenv("DIGISAC_TOKEN") or ""
    SRVID  = os.getenv("DIGISAC_SERVICE") or ""
    IMAGE  = os.getenv("IMAGE_SRC") or "banner.jpg"
    TEXT   = (os.getenv("MESSAGE_TEMPLATE") or os.getenv("MESSAGE_TEXT") or "").strip()
    DELAY  = float(os.getenv("DELAY_SECONDS") or 0)

    if not API_V1 or not TOKEN or not SRVID:
        raise SystemExit("Defina DIGISAC_API_URL, DIGISAC_TOKEN e DIGISAC_SERVICE no .env")

    print("API_V1:", API_V1)
    print("TOKEN..:", (TOKEN[:4]+"..."+TOKEN[-4:]) if len(TOKEN)>=8 else "***")
    print("SERVICE:", SRVID)

    # imagem local obrigatória ou URL pública
    if not (IMAGE.startswith("http://") or IMAGE.startswith("https://")):
        if not os.path.exists(IMAGE):
            raise SystemExit(f"Imagem não encontrada: {IMAGE}")

    contacts = load_contacts_csv(args.file)
    if args.limit and args.limit > 0:
        contacts = contacts[:args.limit]
    print(f"Carregados {len(contacts)} contatos de {args.file}")

    for i, c in enumerate(contacts, start=1):
        tel = c["telefone"]
        try:
            resp = send_image_with_caption_base64(API_V1, TOKEN, tel, SRVID, TEXT, IMAGE)
            append_row("resultado_envio.csv", i, tel, "ENVIADO", 200, {"resp": resp})
            print(f"[OK] {tel}")
        except Exception as e:
            code = getattr(getattr(e, "response", None), "status_code", 0) or 0
            append_row("resultado_envio.csv", i, tel, "FALHA", code, {"erro": str(e)})
            print(f"[ERRO] {tel}: {e}")
        if DELAY > 0 and i < len(contacts):
            time.sleep(DELAY)




