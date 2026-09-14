import requests
from bs4 import BeautifulSoup
import json
import logging 
from dataclasses import dataclass, asdict

@dataclass
class JobOffer:
    """
    Représente une offre d'emploi nettoyée provenant d'une source quelconque (Indeed, LinkedIn, WelcomeToTheJungle, etc.).
    Sera donné tel quel au llm pour qu'il puisse extraire uniquement le contenu de l'offre et supprimer le texte non pertinent.

    attributes : 
        - title : intitulé du poste
        - url : lien vers l'offre originale
        - content : Description complète de l'offre
    """
    title: str
    url: str
    content: str

logger = logging.getLogger(__name__) # Crée un logger spécifique à ce fichier et qui porte le nom de ce fichier 
logging.basicConfig( # configure le système de logs 
    level=logging.INFO, # definit la granularité que l'on affiche 
    format="%(asctime)s - %(levelname)s - %(message)s" # affiche dans le log la date, la granularité et le message
)

def _fetchPage(
        proxies: dict[str, str], 
        headers: dict[str, str], 
        url: str
) -> str:
    """
    Télécharge le contenu HTML d'une page Web.
    Lève une exception si la requête échoue (erreur http ou problème réseau).

    Args : 
        proxies : dictionnaire des proxies http / https
        headers : headers http (user-agent, accept, referer, etc.)
        url : url de la page à récupérer
    
    Returns :
        HTML de la page sous forme de string.

    Raises : 
        requests.RequestException: en cas d'erreur réseau ou HTTP.  
    """
    try:
        response = requests.get( # envoie une requête HTTP pour récupérer la page
            url=url,
            proxies=proxies,
            headers=headers,
            timeout=30,
        )

        response.raise_for_status() # Lève une erreur si la requête échoue

        return response.text

    except requests.RequestException as e:
        logger.error("Erreur lors du téléchargement de %s : %s", url, e)
        raise

def _extractJobOffer(html_page: str) -> str:
    """
    Extrait le texte utile d'une page HTML d'offre d'emploi.

    Nettoie la page en supprimant les éléments non pertinents
    (script, style, noscript, svg), puis récupère le contenu
    textuel du body.

    Args:
        html_page: HTML complet de la page à analyser.

    Returns:
        Texte brut du contenu principal de la page.

    Raises:
        ValueError: si aucun <body> n'est trouvé dans le HTML.
    """
    soup = BeautifulSoup(html_page, "html.parser") # parse le HTML brut 
    for tag in soup(["script", "style", "noscript", "svg"]): # supprime les éléments non pertinents pour l'extraction de texte 
        tag.decompose()
    
    body = soup.body # récupère le body de la page 

    if body is None: # vérifie que le body existe, car si None, la méthode get_text renvoie une erreur 
        raise ValueError("Aucun body trouvé dans le HTML")

    return body.get_text(separator="\n", strip=True) # extrait le texte brut du body

def saveOffer(
    url: str,
    offer_title: str,
    proxies: dict[str, str],
    headers: dict[str, str]
) -> JobOffer:
    """
    Récupère une offre d'emploi depuis une URL, l'extrait,
    puis la sauvegarde dans un fichier JSON.

    Args:
        url: URL de l'offre d'emploi
        offer_title: titre du poste (utilisé pour nommer le fichier)
        proxies: configuration proxy HTTP/HTTPS
        headers: headers HTTP (User-Agent, etc.)

    Returns:
        JobOffer: objet structuré représentant l'offre
    """

    html_page = _fetchPage(proxies, headers, url) # Téléchargement de la page HTML

    offer = _extractJobOffer(html_page) # Extraction du contenu utile


    job_offer = JobOffer(    # Création de l'objet métier
        title=offer_title,
        url=url,
        content=offer,
    )

    with open(rf"Offers\{offer_title}.json", "w", encoding="utf-8") as f: # Sauvegarde JSON (conversion dataclass → dict)
        json.dump(asdict(job_offer), f, indent=4, ensure_ascii=False)

    logger.info("Offre %s écrite dans Offers\\%s.json", url, offer_title)

    return job_offer

def saveOfferNoScrapping(
    offer_as_str: str,
    url: str,
    offer_title: str
) -> tuple[JobOffer, str]:
    """
    Récupère une offre d'emploi depuis un string, l'extrait,
    puis la sauvegarde dans un fichier JSON.

    Cette fonction diffère de saveOffer dans la provenance du contenu : ici elle est fournie par l'utilisateur sous forme de texte. 
    Cette fonction existe car il arrive que les requêtes automatisées soient bloquées par le site d'offres, rendant inutilisable la 
    fonction saveOffer.

    Args:
        offer_as_str: contenu texte qui correspond à l'offre d'emploi de la page
        url: URL de l'offre d'emploi
        offer_title: titre du poste (utilisé pour nommer le fichier)

    Returns:
        JobOffer: objet structuré représentant l'offre
        filepath : chemin d'accès de l'offre structurée
    """

    job_offer = JobOffer(    # Création de l'objet métier
        title=offer_title,
        url=url,
        content=offer_as_str,
    )

    filepath = rf"Offers\{offer_title}.json"
    
    with open(filepath, "w", encoding="utf-8") as f: # Sauvegarde JSON (conversion dataclass → dict)
        json.dump(asdict(job_offer), f, indent=4, ensure_ascii=False)

    logger.info("Offre %s écrite dans Offers\\%s.json", url, offer_title)

    return job_offer, filepath