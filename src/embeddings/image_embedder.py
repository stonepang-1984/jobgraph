"""Image embedding using CLIP."""

from pathlib import Path
from typing import Union

import numpy as np
from loguru import logger

from config.settings import settings


class ImageEmbedder:
    """Image embedding using CLIP model."""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.embedding.clip_model
        self.dimension = settings.embedding.clip_dimension
        self._model = None
        self._processor = None

    @property
    def model(self):
        if self._model is None:
            self._load_model()
        return self._model

    @property
    def processor(self):
        if self._processor is None:
            self._load_model()
        return self._processor

    def _load_model(self) -> None:
        """Load CLIP model."""
        logger.info(f"Loading CLIP model: {self.model_name}")

        from transformers import CLIPModel, CLIPProcessor

        self._processor = CLIPProcessor.from_pretrained(self.model_name)
        self._model = CLIPModel.from_pretrained(self.model_name)

        logger.info("CLIP model loaded")

    def embed_image(self, image: Union[str, Path, "PIL.Image.Image"]) -> list[float]:
        """Embed a single image."""
        return self.embed_batch([image])[0]

    def embed_batch(self, images: list[Union[str, Path, "PIL.Image.Image"]], batch_size: int = 16) -> list[list[float]]:
        """Embed a batch of images."""
        if not images:
            return []

        from PIL import Image

        # Load images if paths
        pil_images = []
        for img in images:
            if isinstance(img, (str, Path)):
                pil_images.append(Image.open(img).convert("RGB"))
            else:
                pil_images.append(img)

        # Process in batches
        all_embeddings = []
        for i in range(0, len(pil_images), batch_size):
            batch = pil_images[i : i + batch_size]
            inputs = self.processor(images=batch, return_tensors="pt", padding=True)

            import torch

            with torch.no_grad():
                outputs = self.model.get_image_features(**inputs)

            # Normalize
            embeddings = outputs / outputs.norm(dim=-1, keepdim=True)
            all_embeddings.extend(embeddings.cpu().numpy().tolist())

        return all_embeddings

    def embed_text(self, text: str) -> list[float]:
        """Embed text for cross-modal retrieval."""
        inputs = self.processor(text=[text], return_tensors="pt", padding=True)

        import torch

        with torch.no_grad():
            outputs = self.model.get_text_features(**inputs)

        embeddings = outputs / outputs.norm(dim=-1, keepdim=True)
        return embeddings[0].cpu().numpy().tolist()

    def similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """Calculate cosine similarity between embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))


# Singleton instance
image_embedder = ImageEmbedder()
