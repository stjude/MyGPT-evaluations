"""Download arXiv PDFs listed in the Open-rag-bench input CSV."""

import argparse
import csv
import os
import ssl
import time
import urllib.error
import urllib.request


ARXIV_PDF_URL = 'https://arxiv.org/pdf/{arxiv_id}.pdf'


def parse_args():
    parser = argparse.ArgumentParser(
        description='Download arXiv PDFs from the doc_id column in text_queries_170.csv.'
    )
    parser.add_argument(
        '--input',
        default='../inputs/text_queries_170.csv',
        help='Input CSV path with a doc_id column.',
    )
    parser.add_argument(
        '--output-dir',
        default='../inputs/pdfs',
        help='Directory where downloaded PDFs are saved.',
    )
    parser.add_argument(
        '--sleep',
        type=float,
        default=1.0,
        help='Seconds to pause between downloads.',
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=120,
        help='Download timeout in seconds per PDF.',
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Download only the first N unique arXiv IDs.',
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Redownload PDFs that already exist.',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print the PDFs that would be downloaded without downloading them.',
    )
    parser.add_argument(
        '--verify-ssl',
        action='store_true',
        help='Verify SSL certificates. Disabled by default for local self-signed certificate chains.',
    )
    return parser.parse_args()


def load_arxiv_ids(input_path):
    with open(input_path, newline='', encoding='ISO-8859-1') as input_file:
        reader = csv.DictReader(input_file)
        if not reader.fieldnames or 'doc_id' not in reader.fieldnames:
            raise ValueError(f'Input file must contain a doc_id column: {input_path}')

        arxiv_ids = []
        seen_arxiv_ids = set()
        for row in reader:
            arxiv_id = row.get('doc_id', '').strip()
            if arxiv_id and arxiv_id not in seen_arxiv_ids:
                arxiv_ids.append(arxiv_id)
                seen_arxiv_ids.add(arxiv_id)

    return arxiv_ids


def download_pdf(arxiv_id, output_dir, timeout, overwrite, ssl_context):
    pdf_path = os.path.join(output_dir, f'{arxiv_id}.pdf')
    if os.path.exists(pdf_path) and not overwrite:
        return 'skipped'

    url = ARXIV_PDF_URL.format(arxiv_id=arxiv_id)
    request = urllib.request.Request(
        url,
        headers={'User-Agent': 'MyGPT-evaluations arXiv PDF downloader'},
    )
    with urllib.request.urlopen(request, timeout=timeout, context=ssl_context) as response:
        with open(pdf_path, 'wb') as pdf_file:
            pdf_file.write(response.read())

    return 'downloaded'


def main():
    args = parse_args()
    arxiv_ids = load_arxiv_ids(args.input)
    if args.limit is not None:
        arxiv_ids = arxiv_ids[:args.limit]

    os.makedirs(args.output_dir, exist_ok=True)
    ssl_context = None if args.verify_ssl else ssl._create_unverified_context()

    downloaded_count = 0
    skipped_count = 0
    failed_count = 0

    print(f'Found {len(arxiv_ids)} unique arXiv IDs in {args.input}')
    for index, arxiv_id in enumerate(arxiv_ids, start=1):
        pdf_path = os.path.join(args.output_dir, f'{arxiv_id}.pdf')
        url = ARXIV_PDF_URL.format(arxiv_id=arxiv_id)
        if args.dry_run:
            print(f'[{index}/{len(arxiv_ids)}] Would download {url} -> {pdf_path}')
            continue

        try:
            status = download_pdf(arxiv_id, args.output_dir, args.timeout, args.overwrite, ssl_context)
            if status == 'downloaded':
                downloaded_count += 1
                print(f'[{index}/{len(arxiv_ids)}] Downloaded {arxiv_id}')
            else:
                skipped_count += 1
                print(f'[{index}/{len(arxiv_ids)}] Skipped existing {arxiv_id}')
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            failed_count += 1
            print(f'[{index}/{len(arxiv_ids)}] Failed {arxiv_id} from {url}: {error}')

        if index < len(arxiv_ids) and args.sleep > 0:
            time.sleep(args.sleep)

    print(f'Downloaded: {downloaded_count}; skipped: {skipped_count}; failed: {failed_count}')
    print(f'PDF directory: {args.output_dir}')


if __name__ == '__main__':
    main()
