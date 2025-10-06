import os
import pdfplumber

def find_title_on_page(page):
    """
    Analyzes a pdfplumber page object to find a likely title.
    The heuristic looks for centered, all-caps text near the top of the page.
    """
    page_center_x = page.width / 2
    center_tolerance = page.width * 0.15  # 15% of page width

    title_lines = []
    in_title = False

    words = page.extract_words(x_tolerance=3, y_tolerance=3, keep_blank_chars=False, use_text_flow=False)
    
    lines = {}
    for word in words:
        y0 = int(word['top'])
        if y0 not in lines:
            lines[y0] = []
        lines[y0].append(word)

    sorted_lines_y = sorted(lines.keys())

    for y0 in sorted_lines_y:
        line_words = sorted(lines[y0], key=lambda w: w['x0'])
        if not line_words:
            continue
            
        line_text = " ".join(w['text'] for w in line_words)
        
        line_x0 = min(w['x0'] for w in line_words)
        line_x1 = max(w['x1'] for w in line_words)
        line_center_x = (line_x0 + line_x1) / 2

        is_centered = abs(line_center_x - page_center_x) < center_tolerance
        is_all_caps = line_text.isupper() and len(line_text.split()) > 1

        if is_centered and is_all_caps:
            title_lines.append(line_text)
            in_title = True
        elif in_title:
            break
    
    return " ".join(title_lines) if title_lines else None

def process_directory(folder_path):
    """
    Scans a directory for PDF files and renames them based on titles found.
    """
    print(f"Scanning directory: {folder_path}")
    for filename in os.listdir(folder_path):
        if not filename.lower().endswith(".pdf"):
            continue

        file_path = os.path.join(folder_path, filename)
        try:
            title = None
            with pdfplumber.open(file_path) as pdf:
                if not pdf.pages:
                    print(f"ℹ️  '{filename}' has no pages.")
                    continue
                
                first_page = pdf.pages[0]
                title = find_title_on_page(first_page)

            if title:
                clean_title = "".join(c for c in title if c not in r'\/:*?"<>|')
                new_filename = clean_title.strip() + ".pdf"
                new_path = os.path.join(folder_path, new_filename)

                if file_path.lower() == new_path.lower():
                    print(f"ℹ️  '{filename}' is already named correctly.")
                    continue

                if not os.path.exists(new_path):
                    os.rename(file_path, new_path)
                    print(f"✅ '{filename}' -> '{new_filename}'")
                else:
                    print(f"⚠️  '{new_filename}' already exists, skipping.")
            else:
                print(f"ℹ️  No title found for '{filename}'.")
        except Exception as e:
            print(f"❌ Error processing '{filename}': {e}")

def main():
    """
    Entry point for the console script.
    Processes the current working directory.
    """
    process_directory(os.getcwd())

if __name__ == '__main__':
    main()
