import re

def clean_page_text(text: str):
    try:
        text = re.sub(
            r"""
            \s*\d{1,2}[-/]\d{1,2}[-/]\d{2,4}       # Date (25-10-2025)
            \s+\d{1,2}:\d{2}\s*(?:AM|PM)           # Time (10:10 AM)
            [\s\r\n]*                              # Whitespace/newlines
            Patient\s*Name:.*?(?=\n[A-Z]|$)        # Patient Name: ... until next uppercase line
            """,
            "",
            text,
            flags=re.IGNORECASE | re.DOTALL | re.VERBOSE,
        )

        text = re.sub(r"\bKIMS[-/A-Z0-9]*\b", "", text, flags=re.IGNORECASE)

        text = re.sub(
            r"""
            Krishna\s+Institute\s+Of\s+Medical\s+Sciences\s+Limited.*?
            (?:Website:.*?(?=\n[A-Z]|$))?
            """,
            "",
            text,
            flags=re.IGNORECASE | re.DOTALL | re.VERBOSE,
        )

        text = re.sub(r"\n{2,}", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()
    except Exception as e:
        print(f"Error in clean_page_text: {str(e)}")
        return text

def remove_header_text(text: str):
    try:
        text = text.replace("\xa0", " ")
        text = re.sub(r' {2,}', ' ', text)
        lines = text.split('\n')
        cleaned_lines = []
        header_patterns = [
            r'^\d{2}-\d{2}-\d{4} \d{2}:\d{2}:? ?[AP]?M?',  # Date time
            r'^Patient Name:.*IP#:.*',  # Patient info
            r'^\d{2}-\d{2}-\d{4}.*\d{2}:\d{2}',  # More flexible date-time
        ]
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            skip_line = False
        
            if i < 5:
                for pattern in header_patterns:
                    if re.search(pattern, line_clean):
                        skip_line = True
                        break
            
            if not skip_line:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    except Exception as e:
        print(f"Error in remove_header_text: {str(e)}")
        return text

def remove_garbage(text: str) -> str:
    
    try:
        # Remove repeated date/time and patient details
        text = re.sub(r",\s*\n?\s*\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}[:\s]*[APMapm]*", "", text)
        text = re.sub(r"Patient Name:.*?(?=\n|$)", "", text)
        text = re.sub(r"IP#.*?(?=\n|$)", "", text)
        text = re.sub(r"MRN.*?(?=\n|$)", "", text)
        text = re.sub(r"NOTE:?$", "", text)
        return text.strip()
    except Exception as e:
        print(f"Error in remove_garbage: {str(e)}")
        return text

# def clean_page_text(text):
#     """Remove headers, footers, page numbers, etc."""
#     try:
#         lines = text.split('\n')
#         cleaned = []
#         skip_patterns = [
#             r"25-10-2025 10:10: AM",
#             r"Patient Name:? *PATEL MAHENDRAKUMAR",
#             r"IP#?:? *IPSE2526020259",
#             r"KIMS-/CS/EF/03",
#             r"Page \d+ of \d+"
#         ]
#         for line in lines:
#             line = line.strip()
#             if any(re.search(pat, line, re.IGNORECASE) for pat in skip_patterns):
#                 continue
#             if line and not line.isdigit():  # skip lone page numbers
#                 cleaned.append(line)
#         return "\n".join(cleaned)
#     except Exception as e:
#         print(f"Error in clean_page_text (commented): {str(e)}")
#         return text