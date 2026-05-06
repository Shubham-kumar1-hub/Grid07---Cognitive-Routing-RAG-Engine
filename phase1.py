# phase1.py
# Author: Dev
# Description: Vector based persona matching using FAISS and HuggingFace embeddings.
# This is Phase 1 of the Grid07 AI assignment -> the "router" that decides which
# bot should respond to a given post based on cosine similarity.

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss


# -------------------------------------------------
# Bot Persona Definitions
# -------------------------------------------------

BOT_PERSONAS = {
    "Bot_A_TechMaximalist": (
        "I believe AI and crypto will solve all human problems. I am highly optimistic "
        "about technology, Elon Musk, and space exploration. I dismiss regulatory concerns."
    ),
    "Bot_B_Doomer": (
        "I believe late-stage capitalism and tech monopolies are destroying society. "
        "I am highly critical of AI, social media, and billionaires. I value privacy and nature."
    ),
    "Bot_C_FinanceBro": (
        "I strictly care about markets, interest rates, trading algorithms, and making money. "
        "I speak in finance jargon and view everything through the lens of ROI."
    ),
}

class PersonaRouter:
    def __init__(self):
        # Loading a lightweight embedding model
        print("[INFO] Loading HuggingFace embedding model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        self.bot_ids = list(BOT_PERSONAS.keys())
        self.persona_texts = list(BOT_PERSONAS.values())

        # Generating embeddings for all three personas
        self.persona_embeddings = self._embed(self.persona_texts)

        # Building the FAISS index
        self.index = self._build_faiss_index(self.persona_embeddings)

        print("[INFO] FAISS index built with", len(self.bot_ids), "personas.")

    def _embed(self, texts: list[str]) -> np.ndarray:
        # Converting text to float32 numpy array (cause FAISS requires float32)
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.astype("float32")
    
    def _build_faiss_index(self, embeddings: np.ndarray) -> faiss.IndexFlatIP:
        # Normalizing vectors so inner product will behave like cosine similarity
        faiss.normalize_L2(embeddings)

        dimension = embeddings.shape[1]
        # IndexFlatIP = exact inner product search (cosine similarity after normalization)
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        return index

    def route_post_to_bots(self, post_content: str, threshold: float = 0.35) -> list[dict]:
        """
        Given a post, find which bots care about it based on cosine similarity.

        Args:
            post_content: The incoming social media post text
            threshold: Minimum cosine similarity score to include a bot (0 to 1)

        Returns:
            List of dicts with bot_id and similarity score
        """
        print(f"\n[INFO] Routing post: \"{post_content}\"")
        print(f"[INFO] Using similarity threshold: {threshold}")

        # Embedding the incoming post
        post_embedding = self._embed([post_content])
        faiss.normalize_L2(post_embedding) #(This asks FAISS to compare the post against all bot persona vectors)

        # Query all personas (k = total number of bots)
        similarities, indices = self.index.search(post_embedding, k=len(self.bot_ids))

        matched_bots = []

        for sim_score, idx in zip(similarities[0], indices[0]):
            bot_id = self.bot_ids[idx]
            score = float(sim_score)

            print(f"  -> {bot_id}: similarity = {score:.4f}")

            if score >= threshold:
                matched_bots.append({
                    "bot_id": bot_id,
                    "similarity_score": round(score, 4),
                    "persona": self.persona_texts[idx]
                })

        if not matched_bots:
            print("[WARN] No bots matched above the threshold.")
        else:
            print(f"[INFO] {len(matched_bots)} bot(s) matched.")

        return matched_bots
