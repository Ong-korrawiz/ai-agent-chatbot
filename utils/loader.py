import pymupdf4llm


class PdfFile:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_markdown(self) -> str:
        """
        Extracts the text from the PDF file and converts it to Markdown format.
        
        Returns:
            str: The extracted text in Markdown format.
        """
        return pymupdf4llm.to_markdown(self.file_path)