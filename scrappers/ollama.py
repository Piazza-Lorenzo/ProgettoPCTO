# Import delle librerie necessarie
import os
import re
import json
from ollama import Client

# Configurazione Ollama
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")

# Inizializza il client Ollama
if OLLAMA_BASE_URL == "http://localhost:11434" and not OLLAMA_API_KEY:
    client = Client()
else:
    headers = {}
    if OLLAMA_API_KEY:
        headers['Authorization'] = f'Bearer {OLLAMA_API_KEY}'
    client = Client(host=OLLAMA_BASE_URL, headers=headers)

def verify_company(name, url, snippet):
    """
    Verifica se un risultato di ricerca corrisponde a un'azienda vera usando Ollama.

    Args:
        name (str): Nome del risultato
        url (str): URL del sito
        snippet (str): Descrizione del risultato

    Returns:
        bool: True se è un'azienda, False altrimenti
    """
    try:
        prompt = f"""Sei un assistente esperto che identifica se un risultato di ricerca corrisponde a un'azienda vera e propria.

Analizza il titolo, l'URL e la descrizione del risultato.
Rispondi SOLO con 'SI' se è un'azienda vera, 'NO' in tutti gli altri casi.

Analizza questo risultato:

Titolo: {name}
URL: {url}
Descrizione: {snippet}

È un'azienda vera?"""
        messages = [{'role': 'user', 'content': prompt}]
        result = client.chat(model=OLLAMA_MODEL, messages=messages, stream=False)
        is_company = result['message']['content'].strip().upper()
        return "SI" in is_company
    except Exception as e:
        print(f"  ⚠ Verifica LLM fallita: {str(e)[:80]}")
        return False

def extract_contacts(html_content):
    """
    Estrae email e telefono da contenuto HTML usando Ollama.

    Args:
        html_content (str): Contenuto HTML della pagina web

    Returns:
        dict: Dizionario con 'email' e 'phone', None se non trovati
    """
    if not html_content:
        return {'email': None, 'phone': None}

    try:
        prompt = f"""Sei un assistente esperto che estrae informazioni di contatto da pagine web HTML aziendali. Analizza l'HTML fornito, pulisci il testo rimuovendo script, stili, navigazione, footer, header e contenuti non rilevanti, poi trova l'email aziendale principale e il primo numero di telefono aziendale italiano che incontri nel testo pulito. Rispondi ESCLUSIVAMENTE con un oggetto JSON valido nel formato esatto: {{"email": "email@example.com", "phone": "+39 123 456789"}}. Se non trovi l'email, metti null. Se non trovi il telefono, metti null. Non aggiungere alcun testo, commento o spiegazione prima o dopo il JSON.

Estrai email e numero di telefono (aiutandoti con i prefissi come .como.it e +39) da questo HTML di pagina web aziendale: {html_content}"""
        messages = [{'role': 'user', 'content': prompt}]
        result = client.chat(model=OLLAMA_MODEL, messages=messages, stream=False)
        result_data = result['message']['content'].strip()

        # Cerca un pattern JSON nella risposta
        json_match = re.search(r'\{[^}]*"email"\s*:\s*[^}]*"phone"\s*:\s*[^}]*\}', result_data)
        if not json_match:
            # Prova pattern più semplice
            json_match = re.search(r'\{[^}]*\}', result_data)

        if json_match:
            result_data = json_match.group(0)

        try:
            extracted = json.loads(result_data)
            email = extracted.get('email')
            phone = extracted.get('phone')
            return {
                'email': email if email and email not in ["null", "None"] else None,
                'phone': phone if phone and phone not in ["null", "None"] else None
            }
        except json.JSONDecodeError:
            return {'email': None, 'phone': None}
    except Exception as e:
        print(f"  ✗ Errore estrazione contatti: {str(e)[:100]}")
        return {'email': None, 'phone': None}