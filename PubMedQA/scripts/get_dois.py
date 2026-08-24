"""Fetch DOI values for PubMedQA entries using PubMed IDs."""

import argparse
import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request


EUTILS_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch DOI values for rows with a pubmed_id column."
    )
    parser.add_argument(
        "--input",
        default="../inputs/questions.csv",
        help="Input CSV path with a pubmed_id column.",
    )
    parser.add_argument(
        "--output",
        default="../inputs/questions_with_doi.csv",
        help="Output CSV path. Defaults to ../inputs/questions_with_doi.csv.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=200,
        help="Number of PubMed IDs to request per API call.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.34,
        help="Seconds to pause between requests. Keep >=0.34 without an NCBI API key.",
    )
    return parser.parse_args()


def get_doi_from_summary(summary):
    for article_id in summary.get("articleids", []):
        if article_id.get("idtype") == "doi":
            return article_id.get("value", "")
    return ""


def fetch_dois(pubmed_ids, batch_size, sleep_seconds):
    doi_by_pubmed_id = {}
    api_key = os.environ.get("NCBI_API_KEY")
    email = os.environ.get("NCBI_EMAIL")

    for start in range(0, len(pubmed_ids), batch_size):
        batch = pubmed_ids[start:start + batch_size]
        params = {
            "db": "pubmed",
            "id": ",".join(batch),
            "retmode": "json",
        }
        if api_key:
            params["api_key"] = api_key
        if email:
            params["email"] = email

        url = f"{EUTILS_SUMMARY_URL}?{urllib.parse.urlencode(params)}"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"NCBI request failed with status {error.code}") from error

        result = payload.get("result", {})
        for pubmed_id in batch:
            summary = result.get(pubmed_id, {})
            doi_by_pubmed_id[pubmed_id] = get_doi_from_summary(summary)

        print(f"Fetched DOI metadata for {min(start + len(batch), len(pubmed_ids))}/{len(pubmed_ids)} PubMed IDs")
        if start + batch_size < len(pubmed_ids):
            time.sleep(sleep_seconds)

    return doi_by_pubmed_id


def main():
    args = parse_args()
    with open(args.input, newline="", encoding="ISO-8859-1") as input_file:
        reader = csv.DictReader(input_file)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    if "pubmed_id" not in fieldnames:
        raise ValueError(f"Input file must contain a pubmed_id column: {args.input}")

    pubmed_ids = []
    seen_pubmed_ids = set()
    for row in rows:
        pubmed_id = row.get("pubmed_id", "").strip()
        if pubmed_id and pubmed_id not in seen_pubmed_ids:
            pubmed_ids.append(pubmed_id)
            seen_pubmed_ids.add(pubmed_id)

    doi_by_pubmed_id = fetch_dois(pubmed_ids, args.batch_size, args.sleep)
    for row in rows:
        pubmed_id = row.get("pubmed_id", "").strip()
        row["doi"] = doi_by_pubmed_id.get(pubmed_id, "")

    output_fieldnames = fieldnames if "doi" in fieldnames else fieldnames + ["doi"]
    with open(args.output, "w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    found_count = sum(1 for row in rows if row.get("doi"))
    print(f"Found DOI values for {found_count}/{len(rows)} rows")
    print(f"Output saved to: {args.output}")


if __name__ == "__main__":
    main()