import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def generate_email_html(llm_client, companies, sector, is_gemini=False):
    """
    Genera il contenuto HTML dell'email usando il modello LLM specificato.

    Args:
        llm_client: Il client LLM (OpenAI o Gemini) - se None, usa fallback
        companies: Lista delle aziende
        sector: Il settore
        is_gemini: True se è Gemini, False se OpenAI

    Returns:
        str: Contenuto HTML dell'email
    """
    if llm_client is not None:
        try:
            if is_gemini:
                prompt = f"""
                Crea un messaggio email in formato HTML che semplicemente dà conferma della creazione del file.
                Non usare codice CSS inline.
                il messaggio di base deve essere "Ciao! il file con la lista è stato creato! la lista è composta da {len(companies)} aziende che operano nel settore {sector}"
                
                RESTITUISCI SOLO CODICE HTML
                """
                response = llm_client.generate_content(prompt)
                html_content = response.text.strip()
            else:
                completion = llm_client.chat.completions.create(
                    model=os.environ.get("OPENAI_MODEL", "DuckAi-General"),
                    messages=[
                        {"role": "system", "content": "Sei un assistente che genera email HTML professionali e concise. Non includere CSS inline."},
                        {"role": "user", "content": f"Genera una breve email HTML che conferma la creazione del file Excel con {len(companies)} aziende trovate nel settore '{sector}'. Menziona che il file è allegato. Mantieni il messaggio breve e professionale."},
                    ]
                )
                html_content = completion.choices[0].message.content
        except Exception as e:
            print(f"Errore nella generazione del contenuto HTML: {e}")
            html_content = generate_fallback_html(companies, sector)
    else:
        html_content = generate_fallback_html(companies, sector)

    return html_content

def generate_fallback_html(companies, sector):
    """Genera HTML di fallback quando LLM non è disponibile."""
    return f"""
    <html>
    <body>
        <h2>Lista Aziende - {sector}</h2>
        <p>Ciao,</p>
        <p>Il file Excel con la lista delle aziende è stato creato con successo!</p>
        <p><strong>Totale aziende trovate: {len(companies)}</strong></p>
        <p>Trovi i dettagli completi nel file Excel allegato.</p>
        <p>Cordiali saluti</p>
    </body>
    </html>
    """

def send_email(file_path, recipient_email, companies, sector, llm_client=None, is_gemini=False):
    """
    Invia un'email con il file Excel allegato.

    Args:
        file_path: Percorso del file Excel
        recipient_email: Email del destinatario
        companies: Lista delle aziende
        sector: Il settore
        llm_client: Il client LLM (opzionale)
        is_gemini: True se è Gemini, False se OpenAI
    """
    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASSWORD")
    smtp_server = os.environ.get("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("EMAIL_SMTP_PORT", "587"))

    if not sender_email or not sender_password:
        print("ERRORE: EMAIL_USER e EMAIL_PASSWORD devono essere configurati nelle variabili d'ambiente")
        return

    message = MIMEMultipart('mixed')
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = f"Lista Aziende - {sector}"

    html_content = generate_email_html(llm_client, companies, sector, is_gemini)
    html_part = MIMEText(html_content, 'html')
    message.attach(html_part)

    # Allega il file Excel
    try:
        with open(file_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {os.path.basename(file_path)}',
        )
        message.attach(part)
    except Exception as e:
        print(f"Errore nell'allegare il file: {e}")
        return

    # Invia l'email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())
        server.quit()
        print(f"✓ Email inviata con successo a {recipient_email}")
    except Exception as e:
        print(f"✗ Errore nell'invio dell'email: {e}")