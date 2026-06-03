"""简历文件解析器

支持 PDF、DOCX 格式的简历解析
"""

import tempfile
from pathlib import Path

from loguru import logger


class ResumeParser:
    """简历文件解析器"""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

    def parse(self, file_path: str | Path) -> str:
        """解析简历文件为纯文本

        Args:
            file_path: 简历文件路径

        Returns:
            解析后的纯文本内容
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"不支持的文件格式: {ext}，支持: {', '.join(self.SUPPORTED_EXTENSIONS)}")

        logger.info(f"解析简历文件: {path.name}")

        if ext == ".pdf":
            return self._parse_pdf(path)
        elif ext == ".docx":
            return self._parse_docx(path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

    def parse_uploaded_file(self, uploaded_file) -> str:
        """解析 Streamlit 上传的文件

        Args:
            uploaded_file: Streamlit 上传的文件对象

        Returns:
            解析后的纯文本内容
        """
        import os

        # 获取文件扩展名
        ext = Path(uploaded_file.name).suffix.lower()

        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"不支持的文件格式: {ext}，支持: {', '.join(self.SUPPORTED_EXTENSIONS)}")

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name

        try:
            # 解析文件
            text = self.parse(tmp_path)
            return text
        finally:
            # 清理临时文件
            os.unlink(tmp_path)

    def _parse_pdf(self, path: Path) -> str:
        """解析 PDF 文件

        使用 PyMuPDF (fitz) 解析 PDF
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(path))
            pages = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                pages.append(page.get_text())

            content = "\n\n".join(pages)
            doc.close()

            logger.info(f"PDF 解析完成，共 {len(pages)} 页")
            return content

        except ImportError:
            logger.error("未安装 PyMuPDF，请运行: pip install pymupdf")
            raise
        except Exception as e:
            logger.error(f"PDF 解析失败: {e}")
            raise

    def _parse_docx(self, path: Path) -> str:
        """解析 DOCX 文件

        使用 python-docx 解析 Word 文档
        """
        try:
            from docx import Document as DocxDocument

            doc = DocxDocument(str(path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            content = "\n\n".join(paragraphs)

            logger.info(f"DOCX 解析完成，共 {len(paragraphs)} 段")
            return content

        except ImportError:
            logger.error("未安装 python-docx，请运行: pip install python-docx")
            raise
        except Exception as e:
            logger.error(f"DOCX 解析失败: {e}")
            raise


# 全局实例
resume_parser = ResumeParser()
