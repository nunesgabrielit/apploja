from __future__ import annotations

import argparse
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx
from PIL import Image, ImageStat
from pypdf import PdfReader

API_TIMEOUT = 30.0
DEFAULT_PAGE_SIZE = 100
DEFAULT_STOCK_CURRENT = 10
DEFAULT_STOCK_MINIMUM = 2
IMAGE_OUTPUT_DIRS = (
    Path("admin/public/catalog"),
    Path("storefront/public/catalog"),
)

CATEGORY_BY_PREFIX = {
    "FO": ("Fones e Headsets", "Linha de fones bluetooth, headsets gamer e fones com fio."),
    "CS": ("Caixas de Som", "Linha de caixas de som bluetooth e caixas portateis."),
    "CA": ("Carregadores e Fontes", "Carregadores, fontes, carregadores veiculares e power banks."),
    "CR": ("Cameras e Seguranca", "Cameras de seguranca e monitoramento residencial."),
    "OT": ("Eletronicos Diversos", "Itens eletronicos diversos e utilidades de tecnologia."),
    "MS": ("Perifericos", "Linha de perifericos para desktop e notebooks."),
    "TC": ("Perifericos", "Linha de perifericos para desktop e notebooks."),
    "CU": ("Casa e Conectividade", "Acessorios de conectividade e utilidades para o dia a dia."),
    "RW": ("Casa e Conectividade", "Acessorios de conectividade e utilidades para o dia a dia."),
    "AD": ("Casa e Conectividade", "Acessorios de conectividade e utilidades para o dia a dia."),
    "SC": ("Suportes e Mobilidade", "Suportes e acessorios para uso diario e mobilidade."),
    "PU": ("Suportes e Mobilidade", "Suportes e acessorios para uso diario e mobilidade."),
    "LR": ("Ferramentas Portateis", "Ferramentas portateis e solucoes praticas."),
    "MC": ("Ferramentas Portateis", "Ferramentas portateis e solucoes praticas."),
    "CG": ("Games e Controles", "Controles gamer e acessorios para jogos."),
    "MF": ("Audio Profissional", "Microfones e acessorios de captura de audio."),
    "CM": ("Armazenamento e Cabos", "Itens de armazenamento, cabos e conectividade."),
    "PD": ("Armazenamento e Cabos", "Itens de armazenamento, cabos e conectividade."),
    "CB": ("Armazenamento e Cabos", "Itens de armazenamento, cabos e conectividade."),
    "CP": ("Lifestyle", "Itens lifestyle, garrafas e acessorios do dia a dia."),
}

BRANDS = [
    "LEHMOX",
    "JBL",
    "REDMI",
    "XIAOMI",
    "IPHONE",
    "APPLE",
    "MOTOROLA",
    "SAMSUNG",
    "STARMEGA",
    "ULTRAPODS",
    "BARBIE",
    "STANLEY",
    "A'GOLD",
    "AGOLD",
]

CATALOG_ITEM_PATTERN = re.compile(
    r"([A-Z]{2}\d{3})\s+(.*?)\n_+\s*\nATACADO R\$\s*([\d.,]+)",
    re.S,
)


@dataclass(slots=True)
class ParsedCatalogItem:
    internal_code: str
    sku: str
    name: str
    short_description: str
    price: Decimal
    category_name: str
    category_description: str
    product_name: str
    brand: str | None
    connector_type: str | None
    power: str | None
    voltage: str | None
    page_number: int


def normalize_text(value: str, *, preserve_linebreaks: bool = False) -> str:
    replacements = {
        "Ã¢â‚¬â€œ": "-",
        "â€“": "-",
        "â€”": "-",
        "Ã¢â‚¬â„¢": "'",
        "â€™": "'",
        "PortÃ¡til": "Portatil",
        "CÃ¢mera": "Camera",
        "SeguranÃ§a": "Seguranca",
        "RÃ¡pida": "Rapida",
        "ConexÃ£o": "Conexao",
        "MemÃ³ria": "Memoria",
        "MagnÃ©tico": "Magnetico",
        "RecarregÃ¡vel": "Recarregavel",
        "PressÃ£o": "Pressao",
        "NÃ£o": "Nao",
        "visÃ£o": "visao",
        "RÃ¡dio": "Radio",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    if preserve_linebreaks:
        value = re.sub(r"\r\n?", "\n", value)
        value = re.sub(r"[ \t\f\v]+", " ", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        value = value.strip()
    else:
        value = re.sub(r"\s+", " ", value).strip()
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii")


def catalog_key(value: str) -> str:
    return normalize_text(value).casefold()


def infer_brand(description: str) -> str | None:
    normalized = description.upper()
    for brand in BRANDS:
        if brand in normalized:
            if brand == "AGOLD":
                return "A'Gold"
            if brand in {"JBL", "IOS"}:
                return brand
            return brand.title()
    return None


def infer_connector_type(description: str) -> str | None:
    normalized = description.lower()
    if "lightning" in normalized or "iphone" in normalized or "ios" in normalized:
        return "Lightning"
    if "tipo c" in normalized or "usb c" in normalized or "c-c" in normalized:
        return "Tipo C"
    if "v8" in normalized or "micro" in normalized:
        return "Micro USB"
    if "otg" in normalized:
        return "OTG"
    if "3 em 1" in normalized:
        return "3 em 1"
    if "4 em 1" in normalized:
        return "4 em 1"
    return None


def infer_power(description: str) -> str | None:
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(W|w|mAh|MAH|A)\b", description)
    if match is None:
        return None
    value, unit = match.groups()
    normalized_unit = unit.lower()
    if normalized_unit == "w":
        normalized_unit = "W"
    elif normalized_unit == "mah":
        normalized_unit = "mAh"
    elif normalized_unit == "a":
        normalized_unit = "A"
    return f"{value.replace(',', '.')} {normalized_unit}"


def infer_voltage(description: str) -> str | None:
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*V\b", description, re.IGNORECASE)
    if match is None:
        return None
    return f"{match.group(1).replace(',', '.')}V"


def infer_product_name(prefix: str, description: str, brand: str | None) -> str:
    lower = description.lower()
    if prefix == "FO":
        if "headset gamer" in lower:
            base = "Headsets Gamer"
        elif "fone de ouvido" in lower:
            if "lightning" in lower:
                base = "Fones de Ouvido Lightning"
            elif "tipo c" in lower:
                base = "Fones de Ouvido Tipo C"
            else:
                base = "Fones de Ouvido"
        elif "fone sem fio" in lower:
            base = "Fones Sem Fio"
        else:
            base = "Fones Bluetooth"
    elif prefix == "CS":
        base = "Caixas de Som Bluetooth" if "bluetooth" in lower else "Caixas de Som"
    elif prefix == "CA":
        if "veicular" in lower:
            base = "Carregadores Veiculares"
        elif "portatil" in lower:
            base = "Power Banks"
        elif "fonte" in lower:
            base = "Fontes de Carregamento"
        elif "kit apple" in lower or "airpods" in lower:
            base = "Kits Apple"
        else:
            base = "Carregadores de Parede"
    elif prefix == "CR":
        base = "Cameras de Seguranca"
    elif prefix == "OT":
        base = "Eletronicos Diversos"
    elif prefix == "MS":
        base = "Mouses"
    elif prefix == "TC":
        base = "Teclados e Kits"
    elif prefix in {"CU", "RW", "AD"}:
        base = "Casa e Conectividade"
    elif prefix in {"SC", "PU"}:
        base = "Suportes e Mobilidade"
    elif prefix in {"LR", "MC"}:
        base = "Ferramentas Portateis"
    elif prefix == "CG":
        base = "Controles Gamer"
    elif prefix == "MF":
        base = "Microfones"
    elif prefix == "CM":
        base = "Cartoes de Memoria"
    elif prefix == "PD":
        base = "Pen Drives"
    elif prefix == "CB":
        if "otg" in lower:
            base = "Cabos OTG"
        elif "3 em 1" in lower or "4 em 1" in lower:
            base = "Cabos Multifuncionais"
        elif "tipo c" in lower or "usb c" in lower or "c-c" in lower:
            base = "Cabos Tipo C"
        elif "iphone" in lower or "ios" in lower:
            base = "Cabos Lightning"
        elif "v8" in lower or "micro" in lower:
            base = "Cabos Micro USB"
        else:
            base = "Cabos USB"
    elif prefix == "CP":
        base = "Copos" if "copo" in lower else "Garrafas"
    else:
        base = "Catalogo Geral"

    if brand and brand.lower() not in base.lower():
        return f"{base} {brand}"
    return base


def parse_catalog_items(pdf_path: Path) -> list[ParsedCatalogItem]:
    reader = PdfReader(str(pdf_path))
    items: list[ParsedCatalogItem] = []
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = normalize_text(page.extract_text() or "", preserve_linebreaks=True)
        for code, raw_description, raw_price in CATALOG_ITEM_PATTERN.findall(page_text):
            prefix = code[:2]
            category_name, category_description = CATEGORY_BY_PREFIX.get(
                prefix,
                ("Catalogo Geral", "Itens diversos importados do catalogo comercial."),
            )
            description = normalize_text(raw_description)
            price = Decimal(raw_price.replace(".", "").replace(",", "."))
            brand = infer_brand(description)
            items.append(
                ParsedCatalogItem(
                    internal_code=code,
                    sku=f"WM-{code}",
                    name=description,
                    short_description=build_short_description(description),
                    price=price,
                    category_name=category_name,
                    category_description=category_description,
                    product_name=infer_product_name(prefix, description, brand),
                    brand=brand,
                    connector_type=infer_connector_type(description),
                    power=infer_power(description),
                    voltage=infer_voltage(description),
                    page_number=page_number,
                )
            )
    return items


def build_short_description(description: str) -> str:
    lowered = description.lower()
    compact = re.sub(r"\s+", " ", lowered).strip()
    if len(compact) <= 180:
        return compact
    return compact[:177].rstrip() + "..."


def format_brl(value: Decimal) -> str:
    return f"R$ {value:.2f}".replace(".", ",")


def build_product_description(product_name: str, items: list[ParsedCatalogItem]) -> str:
    prices = sorted(item.price for item in items)
    codes = ", ".join(item.internal_code for item in items[:4])
    if len(items) > 4:
        codes = f"{codes} e mais {len(items) - 4}"

    specs: list[str] = []
    connectors = sorted({item.connector_type for item in items if item.connector_type})
    powers = sorted({item.power for item in items if item.power})
    voltages = sorted({item.voltage for item in items if item.voltage})

    if connectors:
        specs.append(f"conectores {', '.join(connectors[:3])}")
    if powers:
        specs.append(f"potencias {', '.join(powers[:3])}")
    if voltages:
        specs.append(f"voltagens {', '.join(voltages[:2])}")

    text = (
        f"Linha {product_name} da WM Distribuidora com {len(items)} variacao(oes) do catalogo. "
        f"Codigos internos: {codes}. "
        f"Faixa de preco: {format_brl(prices[0])} ate {format_brl(prices[-1])}."
    )
    if specs:
        text = f"{text} Destaques tecnicos: {'; '.join(specs)}."
    return text[:1000]


def is_candidate_image(image: Image.Image) -> bool:
    rgb = image.convert("RGB")
    width, height = rgb.size
    area = width * height
    aspect_ratio = width / height if height else 0
    brightness = sum(ImageStat.Stat(rgb).mean) / 3
    return area >= 30000 and 0.45 <= aspect_ratio <= 2.3 and brightness > 20


def extract_image_map(
    pdf_path: Path,
    items: list[ParsedCatalogItem],
) -> dict[str, str]:
    for output_dir in IMAGE_OUTPUT_DIRS:
        output_dir.mkdir(parents=True, exist_ok=True)

    items_by_page: dict[int, list[ParsedCatalogItem]] = defaultdict(list)
    for item in items:
        items_by_page[item.page_number].append(item)

    image_map: dict[str, str] = {}
    reader = PdfReader(str(pdf_path))

    for page_number, page in enumerate(reader.pages, start=1):
        page_items = items_by_page.get(page_number, [])
        if not page_items:
            continue

        candidate_images: list[Image.Image] = []
        for embedded in page.images:
            try:
                image = Image.open(BytesIO(embedded.data)).convert("RGB")
            except Exception:
                continue
            if is_candidate_image(image):
                candidate_images.append(image)

        if len(candidate_images) != len(page_items):
            continue

        for item, image in zip(page_items, candidate_images, strict=True):
            filename = f"{item.internal_code.lower()}.jpg"
            relative_url = f"/catalog/{filename}"
            for output_dir in IMAGE_OUTPUT_DIRS:
                image.save(output_dir / filename, format="JPEG", quality=90, optimize=True)
            image_map[item.internal_code] = relative_url

    return image_map


def auth_headers(api_base_url: str, email: str, password: str) -> dict[str, str]:
    with httpx.Client(timeout=API_TIMEOUT) as client:
        response = client.post(
            f"{api_base_url}/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def fetch_paginated_items(
    client: httpx.Client,
    path: str,
    *,
    params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    page = 1
    items: list[dict[str, Any]] = []
    while True:
        response = client.get(path, params={**(params or {}), "page": page, "page_size": DEFAULT_PAGE_SIZE})
        response.raise_for_status()
        payload = response.json()
        items.extend(payload["data"])
        pagination = payload["pagination"]
        if page >= pagination["total_pages"]:
            break
        page += 1
    return items


def create_or_get_categories(
    client: httpx.Client,
    items: list[ParsedCatalogItem],
) -> dict[str, dict[str, Any]]:
    existing_categories = {
        catalog_key(item["name"]): item for item in fetch_paginated_items(client, "/categories")
    }
    for catalog_item in items:
        key = catalog_key(catalog_item.category_name)
        if key in existing_categories:
            continue
        response = client.post(
            "/admin/categories",
            json={
                "name": catalog_item.category_name,
                "description": catalog_item.category_description,
            },
        )
        response.raise_for_status()
        existing_categories[key] = response.json()["data"]
    return existing_categories


def sync_products(
    client: httpx.Client,
    items: list[ParsedCatalogItem],
    categories_by_name: dict[str, dict[str, Any]],
    image_map: dict[str, str],
) -> dict[tuple[str, str], dict[str, Any]]:
    existing_products = fetch_paginated_items(client, "/products")
    product_map = {
        (item["category"]["id"], item["name_base"].casefold()): item for item in existing_products
    }
    items_by_product: dict[tuple[str, str], list[ParsedCatalogItem]] = defaultdict(list)

    for catalog_item in items:
        category = categories_by_name[catalog_key(catalog_item.category_name)]
        items_by_product[(category["id"], catalog_item.product_name.casefold())].append(catalog_item)

    for key, grouped_items in items_by_product.items():
        category_id, name_key = key
        first_item = grouped_items[0]
        payload = {
            "category_id": category_id,
            "name_base": first_item.product_name,
            "brand": first_item.brand,
            "description": build_product_description(first_item.product_name, grouped_items),
            "image_url": next(
                (image_map[item.internal_code] for item in grouped_items if item.internal_code in image_map),
                None,
            ),
            "is_active": True,
        }

        existing_product = product_map.get((category_id, name_key))
        if existing_product is None:
            response = client.post("/admin/products", json=payload)
            response.raise_for_status()
            product_map[(category_id, name_key)] = response.json()["data"]
            continue

        response = client.put(f"/admin/products/{existing_product['id']}", json=payload)
        response.raise_for_status()
        product_map[(category_id, name_key)] = response.json()["data"]

    return product_map


def sync_product_items(
    client: httpx.Client,
    items: list[ParsedCatalogItem],
    categories_by_name: dict[str, dict[str, Any]],
    products_by_key: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, int]:
    existing_items = {
        item["internal_code"]: item for item in fetch_paginated_items(client, "/product-items")
    }
    summary = {"created": 0, "updated": 0, "skipped": 0}

    for catalog_item in items:
        category = categories_by_name[catalog_key(catalog_item.category_name)]
        product = products_by_key[(category["id"], catalog_item.product_name.casefold())]
        existing_item = existing_items.get(catalog_item.internal_code)

        payload = {
            "product_id": product["id"],
            "internal_code": catalog_item.internal_code,
            "sku": catalog_item.sku,
            "name": catalog_item.name,
            "connector_type": catalog_item.connector_type,
            "power": catalog_item.power,
            "voltage": catalog_item.voltage,
            "short_description": catalog_item.short_description,
            "stock_minimum": DEFAULT_STOCK_MINIMUM,
            "is_active": True,
        }

        if existing_item is None:
            create_payload = {
                **payload,
                "price": str(catalog_item.price),
                "stock_current": DEFAULT_STOCK_CURRENT,
            }
            response = client.post("/admin/product-items", json=create_payload)
            response.raise_for_status()
            existing_items[catalog_item.internal_code] = response.json()["data"]
            summary["created"] += 1
            continue

        update_payload = {
            **payload,
            "stock_minimum": max(existing_item["stock_minimum"], DEFAULT_STOCK_MINIMUM),
        }
        response = client.put(f"/admin/product-items/{existing_item['id']}", json=update_payload)
        response.raise_for_status()
        price_response = client.patch(
            f"/admin/product-items/{existing_item['id']}/price",
            json={"price": str(catalog_item.price)},
        )
        price_response.raise_for_status()
        summary["updated"] += 1
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Importa o catalogo PDF da WM Distribuidora.")
    parser.add_argument(
        "--pdf",
        default=r"C:\Users\gabri\Downloads\CATALOGO WM DISTRIBUIDORA 11.04.2026.pdf",
        help="Caminho do PDF do catalogo.",
    )
    parser.add_argument(
        "--api-base-url",
        default="http://localhost:8000/api/v1",
        help="URL base da API.",
    )
    parser.add_argument(
        "--email",
        default="admin@wmdistribuidora.com",
        help="Usuario admin/employee para autenticacao.",
    )
    parser.add_argument(
        "--password",
        default="Admin@123456",
        help="Senha do usuario administrativo.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        raise SystemExit(f"PDF nao encontrado: {pdf_path}")

    items = parse_catalog_items(pdf_path)
    if not items:
        raise SystemExit("Nenhum item foi extraido do PDF.")

    image_map = extract_image_map(pdf_path, items)
    headers = auth_headers(args.api_base_url, args.email, args.password)
    with httpx.Client(base_url=args.api_base_url, headers=headers, timeout=API_TIMEOUT) as client:
        categories = create_or_get_categories(client, items)
        products = sync_products(client, items, categories, image_map)
        summary = sync_product_items(client, items, categories, products)

    print("Importacao concluida com sucesso.")
    print(f"Itens extraidos: {len(items)}")
    print(f"Categorias ativas mapeadas: {len(categories)}")
    print(f"Produtos comerciais ativos mapeados: {len(products)}")
    print(f"Product items criados: {summary['created']}")
    print(f"Product items atualizados: {summary['updated']}")
    print(f"Imagens associadas com confianca: {len(image_map)}")
    print(f"Estoque padrao aplicado aos novos itens: {DEFAULT_STOCK_CURRENT}")
    print(f"Estoque minimo padrao aplicado aos novos itens: {DEFAULT_STOCK_MINIMUM}")


if __name__ == "__main__":
    main()
