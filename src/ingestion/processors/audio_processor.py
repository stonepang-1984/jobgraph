"""Audio processing pipeline."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from loguru import logger

from config.settings import settings
from src.embeddings.text_embedder import TextEmbedder, text_embedder


@dataclass
class AudioSegment:
    """Processed audio segment."""

    id: str
    start_time: float
    end_time: float
    transcript: str
    speaker_id: Optional[str] = None
    language: str = "zh"
    confidence: float = 0.0
    embedding: list[float] = field(default_factory=list)
    source_path: Optional[str] = None


class AudioProcessor:
    """Process audio files with Whisper ASR."""

    def __init__(self, embedder: TextEmbedder = None):
        self.embedder = embedder or text_embedder
        self._whisper_model = None

    @property
    def whisper_model(self):
        if self._whisper_model is None:
            self._load_whisper()
        return self._whisper_model

    def _load_whisper(self) -> None:
        """Load Whisper model."""
        logger.info("Loading Whisper model...")
        import whisper

        self._whisper_model = whisper.load_model("large-v3")
        logger.info("Whisper model loaded")

    def process(
        self,
        audio_path: Union[str, Path],
        language: str = "zh",
    ) -> list[AudioSegment]:
        """Process an audio file."""
        path = Path(audio_path)
        logger.info(f"Processing audio: {path.name}")

        # Transcribe
        result = self._transcribe(path, language)

        # Split into segments
        segments = self._split_segments(result, str(path))

        # Generate embeddings
        for seg in segments:
            seg.embedding = self.embedder.embed(seg.transcript)

        logger.info(f"Created {len(segments)} audio segments")
        return segments

    def _transcribe(self, audio_path: Path, language: str) -> dict:
        """Transcribe audio using Whisper."""
        result = self.whisper_model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=True,
        )
        return result

    def _split_segments(
        self, result: dict, source_path: str
    ) -> list[AudioSegment]:
        """Split transcription into segments."""
        import hashlib

        segments = []

        for i, segment in enumerate(result.get("segments", [])):
            seg_id = hashlib.md5(
                f"{source_path}_{i}".encode()
            ).hexdigest()[:16]

            segments.append(
                AudioSegment(
                    id=seg_id,
                    start_time=segment["start"],
                    end_time=segment["end"],
                    transcript=segment["text"].strip(),
                    language=result.get("language", "zh"),
                    confidence=segment.get("avg_logprob", 0.0),
                    source_path=source_path,
                )
            )

        return segments


# Singleton instance
audio_processor = AudioProcessor()
