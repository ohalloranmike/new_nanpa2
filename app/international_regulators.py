"""Curated links to national numbering regulators (supplement open datasets)."""

REGULATORS: dict[str, dict[str, str]] = {
    "US": {"name": "NANPA", "url": "https://www.nanpa.com/"},
    "CA": {"name": "CNAC", "url": "https://www.cnac.ca/"},
    "GB": {"name": "Ofcom", "url": "https://www.ofcom.org.uk/phones-and-broadband/phone-numbers"},
    "AU": {"name": "ACMA", "url": "https://www.acma.gov.au/phone-numbers"},
    "NZ": {"name": "NZ Telecommunications Forum", "url": "https://www.tcf.org.nz/"},
    "DE": {"name": "BNetzA", "url": "https://www.bundesnetzagentur.de/"},
    "FR": {"name": "ARCEP", "url": "https://www.arcep.fr/"},
    "IN": {"name": "TRAI", "url": "https://www.trai.gov.in/"},
    "JP": {"name": "MIC", "url": "https://www.soumu.go.jp/"},
    "BR": {"name": "Anatel", "url": "https://www.gov.br/anatel/"},
    "MX": {"name": "IFT", "url": "https://www.ift.org.mx/"},
    "IT": {"name": "AGCOM", "url": "https://www.agcom.it/"},
    "ES": {"name": "CNMC", "url": "https://www.cnmc.es/"},
    "NL": {"name": "ACM", "url": "https://www.acm.nl/"},
    "SE": {"name": "PTS", "url": "https://www.pts.se/"},
    "NO": {"name": "Nkom", "url": "https://www.nkom.no/"},
    "IE": {"name": "ComReg", "url": "https://www.comreg.ie/"},
    "SG": {"name": "IMDA", "url": "https://www.imda.gov.sg/"},
    "HK": {"name": "OFCA", "url": "https://www.ofca.gov.hk/"},
    "KR": {"name": "MSIT", "url": "https://www.msit.go.kr/"},
    "ZA": {"name": "ICASA", "url": "https://www.icasa.org.za/"},
}

NANP_ISO2 = frozenset({"US", "CA"})

ITU_REFERENCES = [
    {
        "name": "ITU-T E.164 country codes",
        "url": "https://www.itu.int/pub/T-SP-OB.1114-2016",
    },
    {
        "name": "ITU dialling procedures",
        "url": "https://www.itu.int/dms_pub/itu-t/opb/sp/T-SP-E.164C-2011-PDF-E.pdf",
    },
    {
        "name": "ITU numbering plan portal",
        "url": "https://www.itu.int/itu-t/nnp",
    },
]
