import os
import sys
import requests
from dotenv import load_dotenv

# Import helpers
from helpers.excel_helper import create_excel_if_not_exists, load_existing_companies, add_company_to_excel
from helpers.email_helper import send_email
from helpers.serpapi_helper import search_google_serpapi, get_organic_results_serpapi, SERPAPI_AVAILABLE
from helpers.serper_helper import search_google_serper, get_organic_results_serper

def main():
    load_dotenv() # Carica le variabili dal file .env
    llm_provider = os.environ.get("LLM_PROVIDER", "openai").lower()

    if llm_provider == "openai":
        from scrappers.openai import verify_company, extract_contacts
        llm_client = None  # Per ora non usato, ma potrebbe servire per email
        is_gemini = False
        print("Utilizzo OpenAI come provider LLM.")
    elif llm_provider == "gemini":
        from scrappers.gemini import verify_company, extract_contacts
        llm_client = None  # Per ora non usato, ma potrebbe servire per email
        is_gemini = True
        print("Utilizzo Gemini come provider LLM.")
    elif llm_provider == "ollama":
        from scrappers.ollama import verify_company, extract_contacts
        llm_client = None  # Per ora non usato, ma potrebbe servire per email
        is_gemini = False
        print("Utilizzo Ollama come provider LLM.")
    else:
        print(f"Provider LLM non valido: {llm_provider}. Usa 'openai', 'gemini' o 'ollama'.")
        sys.exit(1)

    # Scegli il provider di ricerca
    search_provider = os.environ.get("SEARCH_PROVIDER", "serpapi").lower()
    if search_provider == "serpapi":
        search_func = search_google_serpapi
        get_organic_func = get_organic_results_serpapi
        api_key_env = "SERPAPI_API_KEY"
        provider_name = "SerpApi"
        print("Utilizzo SerpApi come provider di ricerca.")
    elif search_provider == "serper":
        search_func = search_google_serper
        get_organic_func = get_organic_results_serper
        api_key_env = "SERPER_API_KEY"
        provider_name = "SerperDev"
        print("Utilizzo SerperDev come provider di ricerca.")
    else:
        print(f"Provider di ricerca non valido: {search_provider}. Usa 'serpapi' o 'serper'.")
        sys.exit(1)

    #sector = input("Inserisci il settore di interesse (es. 'green technology', 'logistica'): ")
    sector = [
        "Ferramenta",
        "Cantieri nautici",
        "Officine meccaniche generiche",
        "Utensilerie",
        "Carpenterie metalliche",
        "Fonderie / fusioni",   
        "Stampaggio e deformazione metalli",
        "Trattamenti superficiali (verniciatura, zincatura, sabbiatura, ecc.)",
        "Macchine utensili e strumenti di precisione",
        "Automazione industriale / robotica",
        "Produzione di impianti / installazioni industriali",
        "Elettromeccanica / componentistica elettrica",
        "Settore trasporti correlati (componentistica per auto, ferroviario, aeronautico)",
        "Industria navale specializzata",
        "Oleodinamica / idraulica / pneumatici"
    ]
    limit = None
    print(f"\nLimite:'{limit}'")

    # Stampa il modello AI utilizzato
    if llm_provider == "gemini":
        model_name = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
    elif llm_provider == "openai":
        model_name = os.environ.get('OPENAI_MODEL', 'DuckAi-General')
    elif llm_provider == "ollama":
        model_name = os.environ.get('OLLAMA_MODEL', 'llama3.2')
    else:
        model_name = "Sconosciuto"
    print(f"\nModello AI usato: {model_name}")

    # Verifica o crea il file Excel
    excel_filename = create_excel_if_not_exists()
    
    # Carica le aziende esistenti
    existing_companies = load_existing_companies(excel_filename)
    print(f"Aziende esistenti nel file: {len(existing_companies)}")

    # Elabora i risultati da SerpAPI e salva immediatamente
    total_processed = 0
    for current_sector in sector:
        print(f"\n--- Elaborazione settore: {current_sector} ---")
        processed = process_companies_from_search(current_sector, limit, verify_company, extract_contacts, excel_filename, existing_companies, search_func, get_organic_func, api_key_env, provider_name)
        total_processed += processed

    # Leggi l'email destinatario dal file .env
    recipient_email = os.environ.get("EMAIL_RECIPIENT", "internship@duckpage.com")

    # Carica tutte le aziende dal file Excel per l'email
    all_companies = load_existing_companies(excel_filename)

    # Crea una stringa rappresentativa dei settori
    sector_str = ", ".join(sector)

    try:
        send_email(excel_filename, recipient_email, all_companies, sector_str, is_gemini=is_gemini)
        print(f"File Excel inviato correttamente all'email {recipient_email}")
    except Exception as e:
        print(f"Errore nell'invio dell'email: {e}")


def process_companies_from_search(sector, limit, verify_func, extract_func, excel_filename, existing_companies, search_func, get_organic_func, api_key_env, provider_name):
    """
    Elabora aziende dalla ricerca Google, verifica duplicati e salva immediatamente in Excel.

    Args:
        sector (str): Il settore di ricerca
        limit (int, optional): Limite sul numero di elementi da processare
        verify_func (function): Funzione per verificare se è un'azienda
        extract_func (function): Funzione per estrarre contatti da HTML
        excel_filename (str): Nome del file Excel
        existing_companies (list): Lista di aziende già esistenti
        search_func (function): Funzione per eseguire la ricerca
        get_organic_func (function): Funzione per estrarre risultati organici
        api_key_env (str): Nome della variabile d'ambiente per la chiave API
        provider_name (str): Nome del provider per i messaggi

    Returns:
        int: Numero totale di aziende processate
    """
    # Verifica che la chiave API sia configurata
    api_key = os.environ.get(api_key_env)
    if not api_key:
        print(f"ERRORE: {api_key_env} non configurata nelle variabili d'ambiente")
        if provider_name == "SerpApi":
            print("Ottieni una chiave gratuita su: https://serpapi.com/")
        else:
            print("Ottieni una chiave gratuita su: https://serper.dev/")
        return 0

    all_companies = []

    print("=" * 70)
    print(f"RICERCA AZIENDE NEL SETTORE: {sector}")
    print(f"Utilizzo: Google Search API ({provider_name})")
    print("=" * 70)
    print()

    # Ricerca con Google Search
    print(f"Ricerca Google per: '{sector}'...\n")

    try:
        processed_count = 0
        start = 0
        page = 1
        max_per_page = 10  # Massimo risultati per pagina (limite SerpApi)

        print(f"  Applicazione filtri intelligenti...\n")
        print("=" * 70)
        print("PROCESSAMENTO E FILTRAGGIO RISULTATI")
        print("=" * 70)
        print()

        while True:
            # Esegui la ricerca
            results = search_func(sector, api_key, max_per_page, start)

            if not results:
                print(f"✗ Errore nella ricerca per la pagina {page}")
                break

            # Estrai i risultati organici
            organic_results = get_organic_func(results)

            if not organic_results:
                print(f"✗ Nessun risultato trovato nella pagina {page}")
                break

            print(f"✓ Trovati {len(organic_results)} risultati da Google Search (pagina {page})")

            # Processa ogni risultato
            for idx, result in enumerate(organic_results, 1):
                global_idx = start + idx
                try:
                    name = result.get("title", "N/D")
                    website = result.get("link", None)
                    snippet = result.get("snippet", "N/D")

                    processed_count += 1

                    print(f"[{global_idx}] {name}")
                    print(f"  Descrizione: {snippet[:100]}...")

                    # Verifica sito web
                    if not website:
                        print(f"  ✗ Nessun URL - risultato scartato")
                        print()
                        continue

                    # Verifica se già presente nell'Excel
                    existing_urls = [comp['url'] for comp in existing_companies]
                    if website in existing_urls:
                        print(f"  ✓ Azienda già presente in Excel - saltata")
                        print()
                        continue

                    # Usa LLM per verificare se è un'azienda vera
                    print(f"  → Verifica se è un'azienda vera...")
                    if not verify_func(name, website, snippet):
                        print(f"  ✗ Non è un'azienda vera - scartato")
                        print()
                        continue
                    else:
                        print(f"  ✓ Verificato come azienda vera")

                    print(f"  ✓ URL: {website}")

                    # Inizializza variabili
                    phone = None
                    email = None

                    # Scarica contenuto HTML dall'URL del sito web
                    try:
                        print(f"  → Scarico contenuto dal sito web: {website}")

                        # Aggiungi user-agent per evitare blocchi
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }

                        # Scarica il contenuto della pagina
                        response = requests.get(website, headers=headers, timeout=10)
                        response.raise_for_status()
                        html_content = response.text

                        print(f"  ✓ Contenuto scaricato ({len(html_content)} caratteri)")

                        # Usa LLM per estrarre email e telefono dal contenuto HTML
                        extracted = extract_func(html_content)

                        # Estrai email
                        email = extracted.get('email')
                        if email:
                            print(f"  ✓ Email: {email}")
                        else:
                            print(f"  • Email non trovata nel sito")

                        # Estrai telefono
                        phone = extracted.get('phone')
                        if phone:
                            print(f"  ✓ Telefono: {phone}")
                        else:
                            print(f"  • Telefono non trovato nel sito")

                    except requests.RequestException as e:
                        print(f"  ✗ Errore scaricamento sito: {str(e)[:100]}")
                    except Exception as e:
                        print(f"  ✗ Errore estrazione contatti: {str(e)[:100]}")

                    # Crea l'oggetto azienda
                    company = {
                        'name': name,
                        'url': website,
                        'email': email,
                        'phone': phone
                    }

                    # Aggiungi l'azienda al file Excel immediatamente
                    add_company_to_excel(excel_filename, company, sector)
                    
                    # Aggiungi anche alla lista esistente per evitare duplicati futuri
                    existing_companies.append(company)
                    
                    print(f"  ✓ Azienda aggiunta\n")

                except Exception as e:
                    print(f"✗ Errore nell'elaborazione del risultato {global_idx}: {e}\n")
                    continue

            start += max_per_page
            page += 1

    except Exception as e:
        print(f"\n✗ ERRORE nella ricerca {provider_name}: {e}")
        print("\nPossibili cause:")
        print("  1. Chiave API non valida o scaduta")
        print("  2. Limite di chiamate API raggiunto")
        print("  3. Problema di connessione")
        if provider_name == "SerpApi":
            print("\nVerifica su: https://serpapi.com/dashboard")
        else:
            print("\nVerifica su: https://serper.dev/dashboard")
        return 0

    print("\n" + "=" * 70)
    print(f"COMPLETATO - Totale aziende processate: {processed_count}")
    print("=" * 70)
    print()

    return processed_count


if __name__ == "__main__":
    main()
