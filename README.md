# CNES Scraper

Python web scraper that collects health facility data from
[CNES](https://cnes.datasus.gov.br/) (Brazil's National Registry of Health
Establishments). Built for the Information Retrieval course.

## How it works

The CNES website loads its data with JavaScript, so the HTML served by the page
is an empty template. Instead of automating a browser, the scraper calls the
same JSON API that the page itself uses:

1. Fetches the list of facilities for a municipality.
2. For each facility, fetches its details (address, phone, e-mail, coordinates).
3. Also fetches its opening hours.
4. Saves everything to a CSV file.

The script visits the website first to receive the session cookies, and it
pauses between requests to avoid overloading the server.

## Collected fields

CNES code, trade name, legal name, facility type, address, ZIP code,
municipality, state, phone, e-mail, latitude/longitude, whether it is open 24
hours, and weekly opening hours.

## Usage

    pip install -r requirements.txt
    python scraper.py

By default it collects facilities from Igarassu, PE (municipality code 260680)
and writes `estabelecimentos_igarassu.csv`.

A `descartados.csv` file lists the facilities that were skipped (and why),
so the team can handle them later.

## Notes on the data

The data comes straight from a registry filled in by each facility, so some
fields are missing or inconsistent (phone formats, e-mails, a few wrong
coordinates). Facilities that are open 24 hours have no opening hours listed.
