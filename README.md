# Disparo DigiSac / Minychat – Envio Automático de Mensagens em Massa

Automação criada para enviar mensagens em massa via **API Oficial DigiSac**, ler contatos de um arquivo CSV/XLSX, disparar mensagens com texto + mídia, registrar cada envio e salvar o resultado em um arquivo `resultado_envio.csv`.

O objetivo é permitir que a InterWeg realize campanhas, avisos e mensagens operacionais de maneira segura, auditável e escalável.

---

##  Funcionalidades

- Leitura de contatos via **CSV** ou **XLSX**  
- Envio de mensagens via **API DigiSac**  
- Envio de texto + mídia (`banner.jpg`)  
- Tratamento de erros automáticos  
- Registro de todos os envios em `resultado_envio.csv`  
- Indicação clara de:
  - Status: `ENVIADO` ou `FALHA`
  - HTTP code retornado
  - Detalhe completo da resposta da API

---

## 📁 Estrutura do Projeto

```text
DISPARO-DIGISAC/
 ├── .env                       # Token, endpoint e serviceId da DigiSac
 ├── banner.jpg                 # Mídia enviada junto com a mensagem
 ├── contato.csv.xlsx           # Lista de números a serem disparados
 ├── digisac_sender_text_v01.py # Script principal de disparo
 ├── resultado_envio.csv        # Log dos envios gerado automaticamente
 └── teste.csv                  # Arquivo auxiliar para testes
```

## 🛠 Requisitos

**Python 3.9+**

**Bibliotecas necessárias:**

- requests  
- pandas  
- python-dotenv
