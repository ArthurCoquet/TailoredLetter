# LettreMotivation

> Génération assistée de lettres de motivation à partir d'une offre d'emploi, d'un référentiel d'expériences professionnelles et d'un pipeline Retrieval-Augmented Generation (RAG).

## Présentation

**LettreMotivation** est un projet Python qui automatise l'analyse d'une offre d'emploi afin d'identifier les expériences professionnelles les plus pertinentes d'un candidat avant de préparer un plan de lettre de motivation.

Le projet combine :

* Analyse sémantique d'offres d'emploi via un LLM.
* Recherche vectorielle d'expériences professionnelles.
* Reranking des expériences retrouvées.
* Préparation d'un plan de rédaction de lettre de motivation.

L'objectif est de réduire le temps nécessaire à la personnalisation d'une candidature tout en maximisant l'adéquation entre le profil du candidat et les attentes du recruteur.

---

# Fonctionnement global

```text
Offre d'emploi (URL)
          │
          ▼
    offer_parser.py
          │
          ▼
 Analyse structurée
     via LLM
          │
          ▼
  build_queries.py
          │
          ▼
 Génération des besoins
          │
          ▼
  vector_search.py
          │
          ▼
 Recherche vectorielle
     dans Qdrant
          │
          ▼
retrieval_post_processing.py
          │
          ▼
      rerank.py
          │
          ▼
Classement des expériences
          │
          ▼
   writing_plan.py
          │
          ▼
 Plan de lettre
```

---

# Architecture du projet

```text
LettreMotivation/
│
├── Prompts/
│   ├── offer_analysis_for_lm.txt
│   ├── offer_analysis_structured.txt
│   └── reranking.txt
│
├── Src/
│   ├── Schemas/
│   │   ├── experiences.py
│   │   ├── job_analysis.py
│   │   ├── rerank_format.py
│   │   └── search_query.py
│   │
│   ├── build_queries.py
│   ├── llm_inference.py
│   ├── main.py
│   ├── offer_parser.py
│   ├── rerank.py
│   ├── retrieval_post_processing.py
│   ├── vector_db.py
│   ├── vector_search.py
│   └── writing_plan.py
│
├── config.yaml
├── requirements.txt
└── README.md
```

---

# Technologies utilisées

## LLM

Modèle actuellement configuré :

```text
nvidia/nemotron-3-super-120b-a12b
```

API :

```text
NVIDIA Integrate API
```

Client :

```python
OpenAI(base_url="https://integrate.api.nvidia.com/v1")
```

---

## Recherche vectorielle

Base de données :

```text
Qdrant
```

Embeddings :

```text
intfloat/multilingual-e5-large
```

Avantages :

* multilingue ;
* très bonnes performances en retrieval ;
* compatible français.

---

## Bibliothèques principales

* OpenAI SDK
* Pydantic
* Qdrant
* LangChain HuggingFace
* HuggingFace Hub
* PyTorch
* BeautifulSoup
* Requests
* PyYAML

---

# Pipeline détaillé

## 1. Extraction de l'offre

Module :

```text
offer_parser.py
```

Responsabilités :

* téléchargement de l'offre ;
* nettoyage du HTML ;
* extraction du contenu textuel ;
* sauvegarde en JSON.

Exemple :

```python
saveOffer(
    url,
    offer_title,
    proxies,
    headers
)
```

---

## 2. Analyse de l'offre

Module :

```text
llm_inference.py
```

Prompt :

```text
Prompts/offer_analysis_for_lm.txt
```

Le LLM identifie :

* les compétences attendues ;
* les besoins du recruteur ;
* les signaux implicites ;
* les priorités ;
* les domaines d'impact.

La sortie est validée via des schémas Pydantic.

---

## 3. Génération des requêtes

Module :

```text
build_queries.py
```

Chaque besoin devient une requête de recherche vectorielle.

Exemple :

```json
{
  "query": "gestion paie administration personnel",
  "priority": 1
}
```

---

## 4. Recherche vectorielle

Module :

```text
vector_search.py
```

Étapes :

1. génération des embeddings ;
2. recherche dans Qdrant ;
3. récupération des chunks pertinents ;
4. regroupement par expérience.

Le modèle E5 utilise :

```text
query:
```

pour les requêtes et :

```text
passage:
```

pour les documents.

---

## 5. Reranking

Module :

```text
rerank.py
```

Prompt :

```text
Prompts/reranking.txt
```

Le LLM attribue un score de pertinence à chaque expérience retrouvée.

Exemple :

```json
{
  "Gestion administrative RH": {
    "score": 92
  },
  "Support recrutement": {
    "score": 78
  }
}
```

---

## 6. Construction du plan

Module :

```text
writing_plan.py
```

Responsabilités :

* sélection des expériences les plus pertinentes ;
* vérification d'un seuil minimal ;
* préparation des données destinées à la génération finale.

Cette étape est actuellement préparatoire.

La génération complète de la lettre n'est pas encore implémentée.

---

# Installation

## Cloner le dépôt

```bash
git clone <repo>
cd LettreMotivation
```

---

## Créer un environnement virtuel

### Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

---

## Installer les dépendances

```bash
pip install -r requirements.txt
```

---

# Configuration

## Variables d'environnement

Créer un fichier :

```text
.env
```

Contenu :

```env
NVIDIA_API_KEY=xxxxxxxx
HF_TOKEN=xxxxxxxx
```

---

## Configuration applicative

Fichier :

```yaml
config.yaml
```

Exemple :

```yaml
llm_inference:
  base_url: https://integrate.api.nvidia.com/v1
  llm_model_name: nvidia/nemotron-3-super-120b-a12b
```

---

# Qdrant

Démarrage rapide via Docker :

```bash
docker run -p 6333:6333 qdrant/qdrant
```

Interface :

```text
http://localhost:6333/dashboard
```

---

# Indexation des expériences

Module :

```text
vector_db.py
```

Fonctionnalités :

* création de collection ;
* génération d'embeddings ;
* insertion ;
* mise à jour.

Chaque chunk est stocké avec :

* son embedding ;
* un identifiant déterministe ;
* ses métadonnées.

---

# Schémas Pydantic

Le projet repose fortement sur la validation de données :

```text
Schemas/
```

Contient :

* job_analysis.py
* experiences.py
* rerank_format.py
* search_query.py

Cette approche garantit :

* robustesse ;
* validation automatique ;
* compatibilité avec les Structured Outputs.

---

# État actuel du projet

## Fonctionnel

* Extraction d'offres.
* Analyse LLM.
* Génération de requêtes.
* Recherche vectorielle.
* Reranking.
* Sélection des expériences.

## En cours

* Génération complète de la lettre.
* Refactorisation du pipeline principal.
* Centralisation de l'instanciation du LLM.

---

# Améliorations prévues

## Architecture

* Injection de dépendances.
* Service unique pour le LLM.
* Pipeline orchestré par étapes.

## IA

* Génération finale de lettre.
* Révision stylistique.
* Adaptation du ton à l'entreprise.

## Recherche

* Hybrid Search (BM25 + Vector Search).
* Cross-encoder reranking.
* Gestion avancée des expériences.

---

# Exemple d'utilisation cible

```bash
python Src/main.py
```

Pipeline :

```text
Offre
 ↓
Analyse
 ↓
Queries
 ↓
Retrieval
 ↓
Rerank
 ↓
Plan
 ↓
Lettre de motivation
```

---

# Limitations connues

* Dépendance à NVIDIA API.
* Dépendance à Qdrant local.
* Génération finale non implémentée.
* Quelques instanciations redondantes du LLM restent à refactoriser.
* Certains chemins de prompts nécessitent encore une harmonisation.

---

# Auteur

Projet développé dans le cadre d'un système intelligent d'assistance à la candidature visant à transformer automatiquement un historique professionnel en argumentaire ciblé pour une offre d'emploi donnée.
