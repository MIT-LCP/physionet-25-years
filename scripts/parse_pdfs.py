import pymupdf
import os
import pandas as pd
import argparse


def get_subfolders(base_path, depth_target):
    subfolders = []
    for root, dirs, files in os.walk(base_path):
        # Determine the depth of the current directory
        depth = root[len(base_path):].count(os.sep)
        if depth == depth_target:
            subfolders.extend([os.path.join(root, d) for d in dirs])
    return subfolders


def search_pdf(file_path, keywords):
    """
    Search the text for the keywords.
    """
    passages = []

    try:
        doc = pymupdf.open(file_path)

        mentions_any = "No"

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

    except pymupdf.FileDataError:
        mentions_any = "N/A"
        return mentions_any, passages


def main(base_path, keywords, output_csv, depth_target):
    """
    Calls
    """
    # List to store the results
    results = []

    # Get subfolder paths
    subfolders = get_subfolders(base_path, depth_target) # [os.path.join(base_path, f.name) for f in os.scandir(base_path) if f.is_dir()]

    # Iterate through all PDF files in the subfolders
    for folder_path in subfolders:
        publisher = os.path.split(folder_path)[-1]
        type = os.path.split(os.path.split(folder_path)[0])[-1]
        for filename in os.listdir(folder_path):
            if filename.endswith('.pdf'):
                file_path = os.path.join(folder_path, filename)
                mentions_any, passages = search_pdf(file_path, keywords)
                if not mentions_any == "N/A":
                    results.append({
                        "Type": type,
                        "Publisher": publisher,
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
    parser.add_argument("--base_path", "-p", type=str,
                        help="Path to the folder containing PDF files")
    parser.add_argument("--keywords", "-k", type=str, nargs='+',
                        help="Keywords to search for")
    parser.add_argument("--output_csv", "-o", type=str,
                        help="Path to the output CSV file")
    parser.add_argument("--depth_target", "-d", type=int,
                        help="Number of levels below the base_path to the folders with the PDF files")

    args = parser.parse_args()

    main(args.base_path, args.keywords, args.output_csv)
