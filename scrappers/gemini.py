# Import delle librerie necessarie
import os
import re
import json
import google.generativeai as genai

# Inizializza il client Gemini
try:
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", 'gemini-2.5-flash'))
except Exception as e:
    print(f"Errore nell'inizializzazione di Gemini: {e}")
    model = None

def verify_company(name, url, snippet):
    """
    Verifica se un risultato di ricerca corrisponde a un'azienda vera usando Gemini.

    Args:
        name (str): Nome del risultato
        url (str): URL del sito
        snippet (str): Descrizione del risultato

    Returns:
        bool: True se è un'azienda, False altrimenti
    """
    if model is None:
        return False

    try:
        verification = model.generate_content(
            f"""Sei un assistente esperto che identifica se un risultato di ricerca corrisponde a un'azienda vera e propria.

Analizza il titolo, l'URL e la descrizione del risultato.
Rispondi SOLO con 'SI' se è un'azienda vera, 'NO' in tutti gli altri casi.

Analizza questo risultato:

Titolo: {name}
URL: {url}
Descrizione: {snippet}

È un'azienda vera?"""
        )

        is_company = verification.text.strip().upper()
        return "SI" in is_company
    except Exception as e:
        print(f"  ⚠ Verifica LLM fallita: {str(e)[:80]}")
        return False

def extract_contacts(html_content):
    """
    Estrae email e telefono da contenuto HTML usando Gemini.

    Args:
        html_content (str): Contenuto HTML della pagina web

    Returns:
        dict: Dizionario con 'email' e 'phone', None se non trovati
    """
    if model is None or not html_content:
        return {'email': None, 'phone': None}

    try:
        completion = model.generate_content(
            f"""Sei un assistente esperto che estrae informazioni di contatto da pagine web HTML aziendali. Analizza l'HTML fornito, pulisci il testo rimuovendo script, stili, navigazione, footer, header e contenuti non rilevanti, poi trova l'email aziendale principale e il primo numero di telefono aziendale italiano che incontri nel testo pulito. Rispondi ESCLUSIVAMENTE con un oggetto JSON valido nel formato esatto: {{"email": "email@example.com", "phone": "+39 123 456789"}}. Se non trovi l'email, metti null. Se non trovi il telefono, metti null. Non aggiungere alcun testo, commento o spiegazione prima o dopo il JSON.

Estrai email e numero di telefono (aiutandoti con i prefissi come .como.it e +39) da questo HTML di pagina web aziendale: {html_content}"""
        )

        result_data = completion.text.strip()

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
