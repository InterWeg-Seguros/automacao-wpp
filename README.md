#  Automação de Disparo WhatsApp – DigiSac API

Automação criada para realizar **envio em massa de mensagens no WhatsApp** através da **API Oficial DigiSac**, utilizando Python.  
O projeto lê uma planilha de contatos, envia mensagens individuais e gera um relatório completo com o status de cada envio.

Ideal para campanhas, notificações, comunicações operacionais e processos internos da InterWeg.

---

##  Estrutura do Projeto

DISPARO-DIGISAC/
├── .env # Credenciais e endpoints da DigiSac
├── banner.jpg # Imagem opcional para envio
├── contato.csv.xlsx # Arquivo de entrada com telefones
├── digisac_sender_text_v01.py # Script principal
├── resultado_envio.csv # Log final de todos os envios
├── teste.csv # Arquivo auxiliar


---

## 🛠 Requisitos

- **Python 3.9+**

###  Bibliotecas utilizadas

- `requests`
- `pandas`
- `python-dotenv`

Instale tudo com:

```bash
pip install requests pandas python-dotenv
