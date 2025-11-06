# ProgettoPCTO
## descrizione
Codice python che cerca tutti i nomi, email, numeri di telefono di aziende che operano in determinati settori e li salava in un excel che al termine dell'esecuzione sarà inviato via email.
Il progetto necessita l'uso di un Google Search API e degli agenti di intelligenza artificiale (openai o gemini). 

## istruzioni per l'uso

 - creare virtual env:  `python3 -m virtualenv venv`
 - installare le dipendenze:  `venv/bin/pip install -r requirements.txt`
 - recuperare le Api key dei servizi e popolare il file:   `.env`
 - eseguire i comando:   `venv/bin/python3 contacts_scrapper.py`

### Generare API Google

 - https://cloud.google.com
 - Console
 - API e servizi
 - Credenziali
