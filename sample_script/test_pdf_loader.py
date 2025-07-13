from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.loader import PdfFile

if __name__ == "__main__":
    # Example usage of PdfFile class
    pdf_path = r"E:\ai-agent-chatbot\data\dental_prices.pdf"  # Replace with your PDF file path
    pdf_file = PdfFile(file_path=pdf_path)
    
    # Extract text in Markdown format
    markdown_text = pdf_file.get_markdown()
    
    # Print the extracted Markdown text
    print(markdown_text)