from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain_huggingface import HuggingFaceEmbeddings
from uuid import uuid5, NAMESPACE_URL
from torch import cuda
import logging
from dataclasses import asdict
from Schemas.experiences import Experiences, Experience

logger = logging.getLogger(__name__)

class VectorStoreIndexer:

    def __init__(
            self, 
            embedding_model: str = "intfloat/multilingual-e5-large",
            batch_size: int = 128
    ):
        """
        Initialise le moteur d'indexation vectorielle.

        Charge le modèle d'embedding, détermine la dimension des vecteurs
        générés et initialise la connexion à Qdrant.
        
        Args:
            embedding_model: modèle HuggingFace utilisé pour générer les embeddings des documents.
        """

        device = "cuda" if cuda.is_available() else "cpu"
        logger.info(
            "VectorStoreIndexer initialisé (model=%s, device=%s)",
            embedding_model,
            device
        )

        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True}
        )

        self.embedding_size = len(
            self.embeddings.embed_query("test")
        )

        self.batch_size = batch_size

        self.client = QdrantClient(host="localhost", port=6333)
    
    def _generate_doc_id(self, doc: Experience) -> str:
        """
        Génère un identifiant déterministe pour un document.

        L'identifiant est construit à partir du contenu du document afin de garantir qu'un même document conserve toujours le même ID lors des réindexations.

        Args:
            doc: document à identifier.

        Returns:
            Identifiant unique du document.
        """
        unique_string = (
            f"{doc.experience}|"
            f"{doc.section}|"
            f"{doc.chunk}"
        )
        return str(uuid5(NAMESPACE_URL, unique_string))
    
    def _create_collection(self, collection_name: str) -> None:
        """
        Crée une collection Qdrant si elle n'existe pas déjà.

        La collection est configurée avec une distance cosinus et une dimension compatible avec le modèle d'embedding utilisé.

        Args:
            collection_name: nom de la collection à créer.
        """

        if not self.client.collection_exists(collection_name=collection_name):
            try:
                self.client.create_collection(
                    collection_name=collection_name, 
                    vectors_config=VectorParams(
                        size=self.embedding_size,  
                        distance=Distance.COSINE
                    )
                )
                logger.info(
                    "Création de la collection '%s'",
                    collection_name
                )
            except Exception:
                logger.exception(
                    "Erreur lors de la création de la collection '%s'",
                    collection_name
                )
                raise
        else:
            logger.info(
                "Collection '%s' déjà existante",
                collection_name
            )

    async def _embed_docs(self, docs: Experiences) -> list[list[float]]:
        """
        Génère les embeddings des documents à indexer.

        Chaque chunk est préfixé par 'passage:' afin de respecter le format recommandé par les modèles de la famille E5 pour les documents.

        Args:
            docs: ensemble des documents à vectoriser.

        Returns:
            Liste des vecteurs correspondant aux documents.
        """
        texts = ["passage: " + doc.chunk for doc in docs.experiences]
        try:
            # Génération des embeddings par batch pour éviter de charger l'ensemble des documents en mémoire GPU simultanément.
            embeddings: list[list[float]] = []
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i+self.batch_size]
                embeddings.extend(
                    await self.embeddings.aembed_documents(batch)
                )
            return embeddings
        except Exception:
            logger.exception("Erreur lors de la génération des embeddings")
            raise
    
    def _upsert_points(self, docs: Experiences, embeddings: list[list[float]], collection_name: str) -> None:
        """
        Insère ou met à jour les documents dans la collection Qdrant.

        Chaque document est stocké avec :
            - son embedding
            - un identifiant déterministe
            - ses métadonnées (payload)

        Args:
            docs: documents à indexer.
            embeddings: vecteurs associés aux documents.
            collection_name: collection cible.
        """

        if len(docs.experiences) != len(embeddings):
            raise ValueError(
                f"Nombre de documents ({len(docs.experiences)}) "
                f"différent du nombre d'embeddings ({len(embeddings)})"
            )

        points = [
            PointStruct(
                id=self._generate_doc_id(doc),
                vector=embedding,
                payload=asdict(doc),
            )
            for doc, embedding in zip(docs.experiences, embeddings)
        ]

        try:
            operation_info = self.client.upsert(
                collection_name=collection_name,
                points=points,
                wait=True,
            )
            logger.info(
                "%d documents indexés dans '%s'",
                len(points),
                collection_name,
            )
            logger.debug("%s", operation_info)

        except Exception:
            logger.exception(
                "Erreur lors de l'indexation dans '%s'",
                collection_name,
            )
            raise
    
    async def index_documents(self, collection_name: str, docs: Experiences) -> None:
        """
        Pipeline complet d'indexation.

        Les étapes exécutées sont :
            1. Création de la collection si nécessaire
            2. Génération des embeddings
            3. Insertion ou mise à jour des documents dans Qdrant

        Args:
            collection_name: collection cible.
            docs: documents à indexer.
        """

        if not docs.experiences:
            logger.warning("Aucun document à indexer.")
            return

        self._create_collection(collection_name=collection_name)

        embeddings = await self._embed_docs(docs)
        
        self._upsert_points(
            docs=docs, 
            embeddings=embeddings, 
            collection_name=collection_name
        )

        logger.info(
            "Indexation terminée pour '%s'",
            collection_name
        )
