import os
import subprocess
import time
from typing import Any

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = "Your Name <youremail@example.com>"
HEADERS = {"User-Agent": USER_AGENT}
TICKER_URL = "https://www.sec.gov/include/ticker.txt"  # ticker→CIK mapping :contentReference[oaicite:1]{index=1}
BASE_JSON_URL = "https://data.sec.gov/submissions/CIK{cik:0>10}.json"
BASE_ARCHIVES_URL = "https://www.sec.gov/Archives"

# ——— robust session with retries ———
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
session.mount("https://", HTTPAdapter(max_retries=retries))


def get_cik_from_ticker(ticker: str) -> str:
    resp = session.get(TICKER_URL, headers=HEADERS)
    resp.raise_for_status()
    for line in resp.text.splitlines():
        sym, cik = line.split("\t")
        if sym.lower() == ticker.lower():
            return cik
    raise KeyError(f"Ticker {ticker} not found")


def fetch_company_index(cik: str) -> Any:
    url = BASE_JSON_URL.format(cik=cik)
    resp = session.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def list_recent_filings(cik: str, form_type: str = "10-K", count: int = 3) -> list:
    idx = fetch_company_index(cik)
    recent = idx["filings"]["recent"]
    # now pull out accession, primaryDocument, form, date
    entries = zip(
        recent["accessionNumber"], recent["primaryDocument"], recent["form"], recent["filingDate"]
    )
    out = []
    for acc, doc, form, date in entries:
        if form == form_type:
            out.append({"acc": acc.replace("-", ""), "doc": doc, "date": date})
            if len(out) >= count:
                break
    return out


def download_filing(cik: str, accession: str, primary_doc: str, save_dir: str = "filings") -> str:
    os.makedirs(save_dir, exist_ok=True)
    path = f"/edgar/data/{int(cik)}/{accession}/{primary_doc}"
    url = BASE_ARCHIVES_URL + path
    resp = session.get(url, headers=HEADERS)
    resp.raise_for_status()
    fn = os.path.join(save_dir, f"{cik}_{accession}.html")
    with open(fn, "wb") as f:
        f.write(resp.content)
    time.sleep(1)  # slow it down even more
    return fn


def parse_with_bs4(html_path: str) -> str:
    with open(html_path, "rb") as f:
        soup = BeautifulSoup(f, "html.parser")
    body = soup.find("body")
    return body.get_text("\n") if body else soup.get_text("\n")


def run_baml_extractor(input_path: str, output_path: str):
    subprocess.run(["baml_extractor", input_path, "--out", output_path], check=True)


if __name__ == "__main__":
    ticker = "AAPL"
    cik = get_cik_from_ticker(ticker)
    print(f"{ticker} → CIK {cik}")

    filings = list_recent_filings(cik, form_type="10-K", count=2)
    for f in filings:
        print(f"Downloading 10-K filed on {f['date']}…")
        html = download_filing(cik, f["acc"], f["doc"])
        txt_path = html.replace(".html", ".txt")
        with open(txt_path, "w", encoding="utf-8") as out:
            out.write(parse_with_bs4(html))
        baml_path = html.replace(".html", ".baml.json")
        #        run_baml_extractor(txt_path, baml_path)
        print("→ BAML JSON saved to", baml_path)
