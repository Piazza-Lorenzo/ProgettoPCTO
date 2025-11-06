# Verifica disponibilità SerpApi
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False

def search_google_serpapi(query, api_key, num=10, start=0):
    """
    Esegue una ricerca Google utilizzando SerpApi.

    Args:
        query (str): La query di ricerca
        api_key (str): La chiave API di SerpApi
        num (int): Numero di risultati per pagina (default 10)
        start (int): Offset per la paginazione (default 0)

    Returns:
        dict: Risultati della ricerca o None se errore
    """
    if not SERPAPI_AVAILABLE:
        print("ERRORE: SerpApi non è disponibile. Installalo con: pip install google-search-results")
        return None

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": num,
        "start": start
    }

    try:
        search = GoogleSearch(params)
        return search.get_dict()
    except Exception as e:
        print(f"Errore nella richiesta SerpApi: {e}")
        return None

def get_organic_results_serpapi(results):
    """
    Estrae i risultati organici dalla risposta di SerpApi.

    Args:
        results (dict): Risultati dalla API SerpApi

    Returns:
        list: Lista dei risultati organici
    """
    return results.get("organic_results", [])