import fitz
import os
import pandas as pd
import argparse


def search_pdf(file_path, keywords):
    """
    Search the text for the keywords.
    """
    doc = fitz.open(file_path)
    mentions_any = "No"
    passages = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()

        for keyword in keywords:
            if keyword in text:
                mentions_any = "Yes"
                start_idx = text.find(keyword)
                # Extract a passage of 100 characters around the keyword
                start_passage = max(0, start_idx - 50)
                end_passage = min(len(text), start_idx + 50)
                passages.append(text[start_passage:end_passage])

    doc.close()
    return mentions_any, passages


def main(folder_path, keywords, output_csv):
    """
    Calls
    """
    # List to store the results
    results = []

    # Iterate through all PDF files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.pdf'):
            file_path = os.path.join(folder_path, filename)
            mentions_any, passages = search_pdf(file_path, keywords)
            results.append({
                "Filename": filename,
                "Contains target word": mentions_any,
                "Extracted text": "; ".join(passages)
            })

    # Convert the results to a DataFrame
    df = pd.DataFrame(results)

    # Output to a CSV file
    df.to_csv(output_csv, index=False)

    print(f'Results have been written to {output_csv}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Search for keywords in PDF files and output results to a CSV file."
        )
    parser.add_argument("folder_path", type=str,
                        help="Path to the folder containing PDF files")
    parser.add_argument("keywords", type=str, nargs='+',
                        help="Keywords to search for")
    parser.add_argument("output_csv", type=str,
                        help="Path to the output CSV file")

    args = parser.parse_args()

    main(args.folder_path, args.keywords, args.output_csv)
