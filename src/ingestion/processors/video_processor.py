"""Video processing pipeline."""

from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger

from src.embeddings.image_embedder import ImageEmbedder
from src.embeddings.text_embedder import TextEmbedder


@dataclass
class VideoSegment:
    """Processed video segment."""

    id: str
    start_time: float
    end_time: float
    keyframe_path: str | None = None
    transcript: str = ""
    scene_description: str = ""
    transcript_embedding: list[float] = field(default_factory=list)
    visual_embedding: list[float] = field(default_factory=list)
    source_path: str | None = None


class VideoProcessor:
    """Process video files with scene detection and ASR."""

    def __init__(
        self,
        image_embedder: ImageEmbedder = None,
        text_embedder: TextEmbedder = None,
    ):
        self.image_embedder = image_embedder or image_embedder
        self.text_embedder = text_embedder or text_embedder

    def process(
        self,
        video_path: str | Path,
        output_dir: str | Path = None,
    ) -> list[VideoSegment]:
        """Process a video file."""
        path = Path(video_path)
        logger.info(f"Processing video: {path.name}")

        if output_dir is None:
            output_dir = path.parent / f"{path.stem}_frames"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Extract audio and transcribe
        transcript = self._extract_and_transcribe(path)

        # Detect scenes and extract keyframes
        scenes = self._detect_scenes(path)

        # Create segments
        segments = self._create_segments(scenes, transcript, str(path), output_dir)

        # Generate embeddings
        for seg in segments:
            if seg.transcript:
                seg.transcript_embedding = self.text_embedder.embed(seg.transcript)
            if seg.keyframe_path:
                seg.visual_embedding = self.image_embedder.embed_image(seg.keyframe_path)

        logger.info(f"Created {len(segments)} video segments")
        return segments

    def _extract_and_transcribe(self, video_path: Path) -> dict:
        """Extract audio and transcribe."""
        import os
        import tempfile

        import whisper

        # Extract audio using ffmpeg
        audio_path = tempfile.mktemp(suffix=".wav")

        try:
            os.system(f"ffmpeg -i {video_path} -vn -acodec pcm_s16le -ar 16000 -ac 1 {audio_path} -y")

            # Transcribe
            model = whisper.load_model("large-v3")
            result = model.transcribe(
                audio_path,
                language="zh",
                word_timestamps=True,
            )
            return result

        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)

    def _detect_scenes(self, video_path: Path) -> list[dict]:
        """Detect scene changes in video."""
        import cv2

        scenes = []
        cap = cv2.VideoCapture(str(video_path))

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        prev_hist = None
        scene_start = 0
        threshold = 30.0

        for frame_idx in range(0, total_frames, int(fps)):  # Sample 1 frame per second
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()

            if not ret:
                break

            # Calculate histogram
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = cv2.normalize(hist, hist).flatten()

            if prev_hist is not None:
                # Compare histograms
                diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA)

                if diff > threshold:
                    # Scene change detected
                    scenes.append(
                        {
                            "start_frame": scene_start,
                            "end_frame": frame_idx,
                            "start_time": scene_start / fps,
                            "end_time": frame_idx / fps,
                        }
                    )
                    scene_start = frame_idx

            prev_hist = hist

        # Add last scene
        scenes.append(
            {
                "start_frame": scene_start,
                "end_frame": total_frames,
                "start_time": scene_start / fps,
                "end_time": total_frames / fps,
            }
        )

        cap.release()
        return scenes

    def _create_segments(
        self,
        scenes: list[dict],
        transcript: dict,
        source_path: str,
        output_dir: Path,
    ) -> list[VideoSegment]:
        """Create video segments from scenes."""
        import hashlib

        segments = []
        transcript_segments = transcript.get("segments", [])

        for i, scene in enumerate(scenes):
            seg_id = hashlib.md5(f"{source_path}_{i}".encode()).hexdigest()[:16]

            # Extract keyframe
            keyframe_path = output_dir / f"frame_{i:04d}.jpg"
            self._extract_keyframe(source_path, scene, keyframe_path)

            # Align transcript
            scene_transcript = self._align_transcript(transcript_segments, scene["start_time"], scene["end_time"])

            segments.append(
                VideoSegment(
                    id=seg_id,
                    start_time=scene["start_time"],
                    end_time=scene["end_time"],
                    keyframe_path=str(keyframe_path),
                    transcript=scene_transcript,
                    source_path=source_path,
                )
            )

        return segments

    def _extract_keyframe(self, video_path: str, scene: dict, output_path: Path) -> None:
        """Extract keyframe from scene."""
        import cv2

        cap = cv2.VideoCapture(video_path)

        # Use middle frame of scene
        mid_frame = (scene["start_frame"] + scene["end_frame"]) // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)

        ret, frame = cap.read()
        if ret:
            cv2.imwrite(str(output_path), frame)

        cap.release()

    def _align_transcript(
        self,
        transcript_segments: list[dict],
        start_time: float,
        end_time: float,
    ) -> str:
        """Align transcript segments with scene timing."""
        texts = []

        for seg in transcript_segments:
            seg_start = seg.get("start", 0)
            seg_end = seg.get("end", 0)

            # Check overlap
            if seg_end >= start_time and seg_start <= end_time:
                texts.append(seg.get("text", "").strip())

        return " ".join(texts)


# Singleton instance
video_processor = VideoProcessor()
