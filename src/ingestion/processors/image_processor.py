"""Image processing pipeline."""

from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger

from config.settings import settings
from src.embeddings.image_embedder import ImageEmbedder
from src.embeddings.text_embedder import TextEmbedder


@dataclass
class ImageData:
    """Processed image data."""

    id: str
    source_path: str
    caption: str = ""
    ocr_text: str = ""
    width: int = 0
    height: int = 0
    format: str = ""
    visual_embedding: list[float] = field(default_factory=list)
    text_embedding: list[float] = field(default_factory=list)
    page_number: int | None = None
    bbox: dict | None = None


class ImageProcessor:
    """Process images with OCR and captioning."""

    def __init__(
        self,
        image_embedder: ImageEmbedder = None,
        text_embedder: TextEmbedder = None,
    ):
        self.image_embedder = image_embedder or image_embedder
        self.text_embedder = text_embedder or text_embedder
        self._ocr_reader = None

    @property
    def ocr_reader(self):
        if self._ocr_reader is None:
            self._load_ocr()
        return self._ocr_reader

    def _load_ocr(self) -> None:
        """Load EasyOCR reader."""
        logger.info("Loading EasyOCR reader...")
        import easyocr

        self._ocr_reader = easyocr.Reader(["ch_sim", "en"], gpu=True)
        logger.info("EasyOCR loaded")

    def process(
        self,
        image_path: str | Path,
        page_number: int | None = None,
        bbox: dict | None = None,
    ) -> ImageData:
        """Process a single image."""
        path = Path(image_path)
        logger.info(f"Processing image: {path.name}")

        from PIL import Image

        img = Image.open(path).convert("RGB")

        # Generate ID
        import hashlib

        img_id = hashlib.md5(str(path).encode()).hexdigest()[:16]

        # OCR
        ocr_text = self._extract_ocr(path)

        # Caption (using LLM if available, otherwise empty)
        caption = self._generate_caption(path, ocr_text)

        # Embeddings
        visual_embedding = self.image_embedder.embed_image(img)

        text_for_embedding = f"{caption}\n{ocr_text}"
        text_embedding = self.text_embedder.embed(text_for_embedding)

        return ImageData(
            id=img_id,
            source_path=str(path),
            caption=caption,
            ocr_text=ocr_text,
            width=img.width,
            height=img.height,
            format=img.format or path.suffix.lstrip("."),
            visual_embedding=visual_embedding,
            text_embedding=text_embedding,
            page_number=page_number,
            bbox=bbox,
        )

    def _extract_ocr(self, image_path: Path) -> str:
        """Extract text from image using OCR."""
        try:
            results = self.ocr_reader.readtext(str(image_path))
            texts = [text for _, text, _ in results]
            return " ".join(texts)
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
            return ""

    def _generate_caption(self, image_path: Path, ocr_text: str) -> str:
        """Generate image caption using LLM."""
        try:
            import base64

            from langchain_core.messages import HumanMessage
            from langchain_openai import ChatOpenAI

            # Read image as base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()

            llm = ChatOpenAI(
                model=settings.llm.openai_model,
                api_key=settings.llm.openai_api_key,
                base_url=settings.llm.openai_api_base,
                temperature=0,
            )

            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": "请详细描述这张图片的内容，包括主要对象、场景、文字、数据、关系等信息。如果是图表请描述其趋势和关键数据。",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                    },
                ]
            )

            response = llm.invoke([message])
            return response.content

        except Exception as e:
            logger.warning(f"Caption generation failed: {e}")
            return ocr_text[:200] if ocr_text else ""


# Singleton instance
image_processor = ImageProcessor()
