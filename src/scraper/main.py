#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch_parse_idealista_full_json.py

Reads ALL .html/.htm files under ./source_html (recursively), extracts rich
listing data PLUS every image URL it can find, and prints a single JSON to stdout.

Output format (printed to stdout):
[
  {
    "file": "relative/path/to/file.html",
    "url": "...",
    "listing_id": "...",
    "title": "...",
    "price": 123456,
    "price_text": "123.456 €",
    "address": {
      "full": "...",
      "street": "...",
      "neighborhood": "...",
      "district": "...",
      "municipality": "...",
      "province": "...",
      "postal_code": "..."
    },
    "geo": {"lat": 40.123, "lng": -3.456},
    "features": {
      "bedrooms": 3,
      "bathrooms": 2,
      "size_m2": 120,
      "floor": "3ª",
      "has_elevator": true,
      "has_terrace": false,
      "energy_cert": "D",
      "year_built": 1999,
      "housing_type": "flat|duplex|chalet|...",
      "parking": "yes|no|optional",
      "other": ["...","..."]   # any extra raw labels we see
    },
    "description": "...",
    "agency": {
      "name": "...",
      "phone": "...",
      "is_professional": true
    },
    "images": ["https://...", "...", ...]
  },
  ...
]

Requires:
  pip install beautifulsoup4

Run:
  python batch_parse_idealista_full_json.py  > out.json
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write("This script requires beautifulsoup4. Install with: pip install beautifulsoup4\n")
    sys.exit(1)

SRC_ROOT = Path("source_html")
HTML_GLOB = "**/*.htm*"

# ---------- Utilities ----------

IMG_EXT_PATTERN = r"\.(?:jpg|jpeg|png|webp)\b"
URL_PATTERN = rf"https?://[^\s\"'>]+{IMG_EXT_PATTERN}(?:[^\s\"'>]*)"
URL_RE = re.compile(URL_PATTERN, re.IGNORECASE)

SRCSET_SPLIT_RE = re.compile(r"\s*,\s*")
SRCSET_URL_RE = re.compile(r"^\s*(\S+)\s*(?:\s+\d+[wx])?$", re.IGNORECASE)

LIKELY_IMG_HOSTS = (
    "img1.idealista.com", "img2.idealista.com", "img3.idealista.com", "img4.idealista.com",
    "st1.idealista.com", "st2.idealista.com", "st3.idealista.com", "st.idealista.com",
    "images.idealista.com", "multimedia.idealista.com",
)

def clean_text(x: Optional[str]) -> str:
    if not x:
        return ""
    return re.sub(r"\s+", " ", x).strip()

def to_int_safe(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    t = text.replace(".", "").replace(",", "").replace("€", "").replace("\xa0", " ")
    m = re.search(r"(-?\d+)", t)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None

def first_nonempty(*vals) -> Optional[str]:
    for v in vals:
        if v and clean_text(v):
            return clean_text(v)
    return None

def ordered_dedupe(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

def is_likely_image_url(url: str) -> bool:
    if not url or not url.lower().startswith(("http://","https://")):
        return False
    if not re.search(IMG_EXT_PATTERN, url, flags=re.IGNORECASE):
        return False
    return True

def extract_from_srcset(srcset: str) -> List[str]:
    urls = []
    if not srcset:
        return urls
    for part in SRCSET_SPLIT_RE.split(srcset.strip()):
        m = SRCSET_URL_RE.match(part)
        if m:
            u = m.group(1)
            if is_likely_image_url(u):
                urls.append(u)
    return urls

def prioritize_images(urls: List[str]) -> List[str]:
    def _priority(u: str) -> Tuple[int, int, int]:
        host_priority = -1 if any(h in u for h in LIKELY_IMG_HOSTS) else 0
        size_priority = -3 if "WEB_DETAIL" in u else (-2 if "WEB_DETAIL_TOP" in u else (-1 if "XLARGE" in u else 0))
        return (host_priority, size_priority, len(u))
    urls = ordered_dedupe(urls)
    urls.sort(key=_priority)
    return urls

# ---------- Extraction helpers ----------

def extract_url(soup: BeautifulSoup) -> Optional[str]:
    return first_nonempty(
        *(m.get("content") for m in soup.find_all("meta", attrs={"property": "og:url"})),
        *(l.get("href") for l in soup.find_all("link", attrs={"rel": ["canonical", "Canonical", "CANONICAL"]})),
    )

def extract_listing_id(soup: BeautifulSoup, url: Optional[str]) -> Optional[str]:
    # Try data-adid in DOM
    adid = None
    root = soup.find(attrs={"data-adid": True})
    if root:
        adid = root.get("data-adid")

    # Fallback: parse from URL (classic: idealista.com/inmueble/12345678/)
    if not adid and url:
        m = re.search(r"/inmueble/(\d+)", url)
        if m:
            adid = m.group(1)
    # Another fallback: look for "adId" in inline scripts
    if not adid:
        for s in soup.find_all("script"):
            txt = s.string if s.string else (s.text or "")
            if not txt:
                continue
            m = re.search(r'"adId"\s*:\s*"?(?P<id>\d+)"?', txt)
            if m:
                adid = m.group("id")
                break
    return adid

def extract_title(soup: BeautifulSoup) -> Optional[str]:
    h1 = soup.find("h1")
    title = clean_text(h1.get_text()) if h1 else None
    if not title:
        tt = soup.find("title")
        title = clean_text(tt.get_text()) if tt else None
    # JSON-LD name as fallback
    if not title:
        for sc in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                data = json.loads(sc.string)
            except Exception:
                continue
            def _yield(d):
                if isinstance(d, dict):
                    yield d
                elif isinstance(d, list):
                    for x in d:
                        if isinstance(x, (dict, list)):
                            yield from _yield(x)
            for d in _yield(data):
                name = d.get("name") if isinstance(d, dict) else None
                if name:
                    return clean_text(name)
    return title

def extract_price(soup: BeautifulSoup) -> Tuple[Optional[int], Optional[str]]:
    price_text = None
    price_int = None

    # Common price node classes (Idealista varies by A/B)
    candidates = []
    candidates += soup.select(".price, .price-value, .txt-bold, .detail-info .info-data-price, .info-data-price")
    for c in candidates:
        maybe = clean_text(c.get_text())
        if "€" in maybe or re.search(r"\d", maybe):
            price_text = maybe
            break

    # Meta/JSON-LD fallbacks
    if not price_text:
        for sc in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                data = json.loads(sc.string)
            except Exception:
                continue
            if isinstance(data, dict) and "offers" in data:
                offers = data.get("offers")
                if isinstance(offers, dict) and "price" in offers:
                    try:
                        price_int = int(offers["price"])
                        price_text = f"{offers['price']} €"
                        break
                    except Exception:
                        pass
            if isinstance(data, dict) and "price" in data:
                price_text = str(data["price"])

    if price_int is None and price_text:
        price_int = to_int_safe(price_text)

    return price_int, price_text

def extract_description(soup: BeautifulSoup) -> Optional[str]:
    # Typical description block
    blocks = soup.select(".adCommentsLanguage, .expanded, .comment, #description, .adComments, .adCommentsText")
    best = None
    for b in blocks:
        txt = clean_text(b.get_text(separator=" "))
        if len(txt) > len(best or ""):
            best = txt
    # JSON-LD fallback
    if not best:
        for sc in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                data = json.loads(sc.string)
            except Exception:
                continue
            if isinstance(data, dict) and "description" in data:
                cand = clean_text(str(data["description"]))
                if cand:
                    best = cand
    return best

def extract_address_and_geo(soup: BeautifulSoup) -> Tuple[Dict[str, Any], Dict[str, Optional[float]]]:
    addr = {
        "full": None,
        "street": None,
        "neighborhood": None,
        "district": None,
        "municipality": None,
        "province": None,
        "postal_code": None,
    }
    geo = {"lat": None, "lng": None}

    # JSON-LD is most reliable
    for sc in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(sc.string)
        except Exception:
            continue

        candidates = []
        if isinstance(data, dict):
            candidates = [data]
        elif isinstance(data, list):
            candidates = [x for x in data if isinstance(x, dict)]

        for d in candidates:
            # Address
            address = d.get("address") if isinstance(d, dict) else None
            if isinstance(address, dict):
                addr["full"] = first_nonempty(addr["full"], address.get("streetAddress"), address.get("addressLocality"))
                addr["street"] = first_nonempty(addr["street"], address.get("streetAddress"))
                addr["municipality"] = first_nonempty(addr["municipality"], address.get("addressLocality"), address.get("addressRegion"))
                addr["province"] = first_nonempty(addr["province"], address.get("addressRegion"))
                addr["postal_code"] = first_nonempty(addr["postal_code"], address.get("postalCode"))

            # Geo
            geo_d = d.get("geo") if isinstance(d, dict) else None
            if isinstance(geo_d, dict):
                try:
                    geo["lat"] = float(geo_d.get("latitude")) if geo_d.get("latitude") is not None else geo["lat"]
                    geo["lng"] = float(geo_d.get("longitude")) if geo_d.get("longitude") is not None else geo["lng"]
                except Exception:
                    pass

            # Full composite address sometimes lives in "name" or breadcrumbs
            nm = d.get("name") if isinstance(d, dict) else None
            if nm and not addr["full"]:
                addr["full"] = clean_text(nm)

    # DOM fallbacks (crumbs)
    if not addr["full"]:
        crumbs = soup.select(".breadcrumb, .breadcrumb-container, nav[aria-label='breadcrumb']")
        for bc in crumbs:
            txt = clean_text(bc.get_text(" / "))
            if len(txt) > len(addr["full"] or ""):
                addr["full"] = txt

    # Another DOM full address spot
    if not addr["full"]:
        loc = soup.select_one(".main-info__title-minor, .main-info__title-minor span, .info-property .txt-lighter")
        if loc:
            addr["full"] = clean_text(loc.get_text())

    return addr, geo

def extract_features(soup: BeautifulSoup) -> Dict[str, Any]:
    feats: Dict[str, Any] = {
        "bedrooms": None,
        "bathrooms": None,
        "size_m2": None,
        "floor": None,
        "has_elevator": None,
        "has_terrace": None,
        "energy_cert": None,
        "year_built": None,
        "housing_type": None,
        "parking": None,
        "other": [],
    }

    # Common “features” lists (labels)
    candidates = []
    candidates += soup.select(".details-property, .info-data, .info-features, ul.feature-list, .charblock, .extended-info")
    text_blobs = []

    for c in candidates:
        for li in c.find_all(["li","span","div"]):
            t = clean_text(li.get_text(" "))
            if t and len(t) >= 2:
                text_blobs.append(t)

    # Quick parsers
    for t in text_blobs:
        # bedrooms
        m = re.search(r"(\d+)\s*(?:hab|hab\.)|(\d+)\s*habitaciones|(\d+)\s*rooms?", t, flags=re.IGNORECASE)
        if m and feats["bedrooms"] is None:
            feats["bedrooms"] = to_int_safe("".join(x for x in m.groups() if x))

        # bathrooms
        m = re.search(r"(\d+)\s*bañ|(\d+)\s*wc|(\d+)\s*ba?th", t, flags=re.IGNORECASE)
        if m and feats["bathrooms"] is None:
            feats["bathrooms"] = to_int_safe("".join(x for x in m.groups() if x))

        # size
        m = re.search(r"(\d+)\s*(?:m2|m²|metros)", t, flags=re.IGNORECASE)
        if m and feats["size_m2"] is None:
            feats["size_m2"] = to_int_safe(m.group(1))

        # floor
        if any(k in t.lower() for k in ["planta", "ground floor", "bajo", "ático", "sótano", "entresuelo", "3ª", "4ª", "5ª"]):
            if feats["floor"] is None:
                feats["floor"] = t

        # elevator
        if "ascensor" in t.lower():
            feats["has_elevator"] = True if "sin" not in t.lower() else False

        # terrace
        if "terraza" in t.lower():
            feats["has_terrace"] = True

        # energy cert
        m = re.search(r"certificado.*?([A-G])\b", t, flags=re.IGNORECASE)
        if m and feats["energy_cert"] is None:
            feats["energy_cert"] = m.group(1).upper()

        # year built
        m = re.search(r"(?:año|año de construcción|construido en)\s*(\d{4})", t, flags=re.IGNORECASE)
        if m and feats["year_built"] is None:
            feats["year_built"] = to_int_safe(m.group(1))

        # housing type
        if feats["housing_type"] is None:
            for kw in ["piso","apartamento","ático","duplex","dúplex","chalet","adosado","estudio","loft","planta baja","bungalow"]:
                if re.search(rf"\b{kw}\b", t, flags=re.IGNORECASE):
                    feats["housing_type"] = kw
                    break

        # parking
        if "garaje" in t.lower() or "plaza de garaje" in t.lower() or "aparcamiento" in t.lower():
            if feats["parking"] is None:
                feats["parking"] = "yes"

    # Collect any unusual labels as "other"
    for t in text_blobs:
        if not any(x and x in t for x in [
            str(feats.get("floor") or ""),
        ]):
            if t and t not in feats["other"]:
                feats["other"].append(t)

    # JSON-LD enrich (rooms/size)
    for sc in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(sc.string)
        except Exception:
            continue
        ds = []
        if isinstance(data, dict):
            ds = [data]
        elif isinstance(data, list):
            ds = [x for x in data if isinstance(x, dict)]
        for d in ds:
            if feats["bedrooms"] is None:
                br = d.get("numberOfRooms") or d.get("numberOfBedrooms")
                if isinstance(br, (int, float, str)):
                    feats["bedrooms"] = to_int_safe(str(br))
            if feats["size_m2"] is None:
                fs = d.get("floorSize")
                if isinstance(fs, dict) and "value" in fs:
                    feats["size_m2"] = to_int_safe(str(fs.get("value")))

    return feats

def extract_agency(soup: BeautifulSoup) -> Dict[str, Any]:
    agency = {"name": None, "phone": None, "is_professional": None}

    # Common selectors
    name = None
    node = soup.select_one(".about-advertiser-name, .professional-name, .ad-footer .name, .advertiser__name")
    if node:
        name = clean_text(node.get_text())

    phone = None
    pnode = soup.select_one(".phone, .advertiser-phone, a[href^='tel:']")
    if pnode:
        if pnode.has_attr("href") and pnode["href"].startswith("tel:"):
            phone = pnode["href"].split(":",1)[1]
        else:
            phone = clean_text(pnode.get_text())

    is_prof = None
    badge = soup.select_one(".is-professional, .professional-badge, .about-advertiser")
    if badge:
        txt = clean_text(badge.get_text()).lower()
        if any(k in txt for k in ["profesional","agency","inmobiliaria","real estate"]):
            is_prof = True

    # JSON-LD fallback (seller)
    for sc in soup.find_all("script", attrs={"type":"application/ld+json"}):
        try:
            data = json.loads(sc.string)
        except Exception:
            continue
        seller = data.get("seller") if isinstance(data, dict) else None
        if isinstance(seller, dict):
            name = first_nonempty(name, seller.get("name"))
            tel = seller.get("telephone")
            if tel and not phone:
                phone = clean_text(tel)
            stype = seller.get("@type")
            if is_prof is None and isinstance(stype, str):
                is_prof = stype.lower() in ("realestageagent","organization","localbusiness","realestateagent","realestatelisting")

    agency["name"] = name
    agency["phone"] = phone
    agency["is_professional"] = is_prof
    return agency

def extract_images(soup: BeautifulSoup) -> List[str]:
    urls: List[str] = []

    # 1) <img> direct / lazy
    for img in soup.find_all("img"):
        for attr in ("src", "data-src", "data-original", "data-ondemand-img"):
            u = img.get(attr)
            if u and is_likely_image_url(u):
                urls.append(u)
        if img.has_attr("srcset"):
            urls.extend(extract_from_srcset(img["srcset"]))

    # 2) <source> tags
    for source in soup.find_all("source"):
        for attr in ("srcset", "src"):
            v = source.get(attr)
            if v:
                if attr == "srcset":
                    urls.extend(extract_from_srcset(v))
                elif is_likely_image_url(v):
                    urls.append(v)

    # 3) OG / link icons
    for meta_prop in soup.find_all("meta", attrs={"property": "og:image"}):
        v = meta_prop.get("content")
        if v and is_likely_image_url(v):
            urls.append(v)
    for link in soup.find_all("link"):
        v = link.get("href")
        if v and is_likely_image_url(v):
            urls.append(v)

    # 4) Inline JS blobs where Idealista hides gallery arrays
    for script in soup.find_all("script"):
        content = script.string if script.string else (script.text or "")
        if not content:
            continue
        if ("adMultimediasInfo" in content or
            "multimediaCarrousel" in content or
            "imageDataService" in content or
            "imageUrl" in content or
            "WEB_DETAIL" in content or
            len(content) > 500):
            for u in URL_RE.findall(content):
                if is_likely_image_url(u):
                    urls.append(u)

    return prioritize_images(urls)

# ---------- Main walk ----------

def parse_file(path: Path, rel: str) -> Dict[str, Any]:
    try:
        html = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return {"file": rel, "error": f"read_error: {e}"}

    soup = BeautifulSoup(html, "html.parser")

    url = extract_url(soup)
    listing_id = extract_listing_id(soup, url)
    title = extract_title(soup)
    price_int, price_text = extract_price(soup)
    address, geo = extract_address_and_geo(soup)
    features = extract_features(soup)
    description = extract_description(soup)
    agency = extract_agency(soup)
    images = extract_images(soup)

    return {
        "file": rel,
        "url": url,
        "listing_id": listing_id,
        "title": title,
        "price": price_int,
        "price_text": price_text,
        "address": address,
        "geo": geo,
        "features": features,
        "description": description,
        "agency": agency,
        "images": images,
    }

def main():
    if not SRC_ROOT.exists() or not SRC_ROOT.is_dir():
        sys.stderr.write(f"Source folder not found: {SRC_ROOT.resolve()}\n")
        sys.exit(2)

    files = sorted(SRC_ROOT.glob(HTML_GLOB))
    if not files:
        sys.stderr.write(f"No HTML files matched under {SRC_ROOT.resolve()} with pattern {HTML_GLOB}\n")
        sys.exit(3)

    results: List[Dict[str, Any]] = []
    for f in files:
        try:
            rel = str(f.relative_to(SRC_ROOT)).replace("\\", "/")
        except Exception:
            rel = f.name
        results.append(parse_file(f, rel))

    # Print ONE JSON to stdout
    sys.stdout.write(json.dumps(results, ensure_ascii=False, indent=2))
    sys.stdout.flush()

if __name__ == "__main__":
    main()
