import os
import requests
import json

def search_google_serper(query, api_key, num=10, start=0):
    """
    Esegue una ricerca Google utilizzando SerperDev API.

    Args:
        query (str): La query di ricerca
        api_key (str): La chiave API di SerperDev
        num (int): Numero di risultati per pagina (default 10)
        start (int): Offset per la paginazione (default 0)

    Returns:
        dict: Risultati della ricerca o None se errore
    """
    url = "https://google.serper.dev/search"

    payload = json.dumps({
        "q": query,
        "gl": "it",
        "hl": "it",
        "num": num,
        "start": start
    })

    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore nella richiesta SerperDev: {e}")
        return None

def get_organic_results_serper(results):
    """
    Estrae i risultati organici dalla risposta di SerperDev.

    Args:
        results (dict): Risultati dalla API SerperDev

    Returns:
        list: Lista dei risultati organici
    """
    return results.get("organic", [])