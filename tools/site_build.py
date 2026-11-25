"""Build the T.A Vitality website from the template in `site/`.

Phone and KvK number are public on the site but must never enter git, so the
template only holds placeholders; real values come from `knowledge/private_*`
and the built page lands in `output/site/` (ignored by git).

Usage: .venv/bin/python -m tools.site_build
"""

import html
import json
import re
import shutil
import sys
from pathlib import Path

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "site" / "index.template.html"
CONFIG = ROOT / "site" / "config.json"
CONTACT_FILE = ROOT / "knowledge" / "private_contact.md"
BOOKKEEPING_FILE = ROOT / "knowledge" / "private_bookkeeping.json"
OUT_FILE = ROOT / "output" / "site" / "index.html"
# Session photos show real people, so they stay out of the public repo (site/photos is git-ignored).
PHOTO_DIR = ROOT / "site" / "photos"
OUT_PHOTO_DIR = OUT_FILE.parent / "photos"

PLACEHOLDER = re.compile(r"\{\{[A-Z_0-9]+\}\}")
PHOTO_SLOT = re.compile(r"\{\{PHOTO_([A-Z0-9_]+)\}\}")
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


class Colors(BaseModel):
    primary: str
    accent: str
    background: str
    text: str


class Photo(BaseModel):
    src: str = ""
    alt: str = ""


class SiteConfig(BaseModel):
    form_url: str = ""
    booking_url: str = ""
    colors: Colors
    photos: dict[str, Photo] = {}
    # Concept builds show where photos will go; switch off before the site goes live.
    photo_placeholders: bool = False


class Contact(BaseModel):
    phone: str
    kvk: str


def read_phone(contact_md: str) -> str:
    match = re.search(r"Telefoon:\s*(.+)", contact_md)
    if not match or not match.group(1).strip():
        raise ValueError("No phone number found in private_contact.md")
    return match.group(1).strip()


def read_kvk(bookkeeping: dict) -> str:
    kvk = str(bookkeeping.get("invoice", {}).get("kvk", "")).strip()
    if not kvk:
        raise ValueError("No KvK number found in private_bookkeeping.json")
    return kvk


def phone_link(phone: str) -> str:
    """Digits only (plus a leading +), so tel: links work on every phone."""
    phone = phone.strip()
    prefix = "+" if phone.startswith("+") else ""
    return prefix + re.sub(r"\D", "", phone)


def cta_buttons(config: SiteConfig, phone: str) -> str:
    """Buttons for the contact options Tim has set up; falls back to calling."""
    buttons: list[str] = []
    if config.form_url:
        buttons.append(
            f'<a class="btn primary" href="{html.escape(config.form_url)}" '
            'target="_blank" rel="noopener">Contactformulier invullen</a>'
        )
    if config.booking_url:
        css = "secondary" if buttons else "primary"
        buttons.append(
            f'<a class="btn {css}" href="{html.escape(config.booking_url)}" '
            'target="_blank" rel="noopener">Kennismaking inplannen</a>'
        )
    if not buttons:
        buttons.append(
            f'<a class="btn primary" href="tel:{phone_link(phone)}">Bel voor een kennismaking</a>'
        )
    return "\n          ".join(buttons)


def photo_html(slot: str, config: SiteConfig) -> str:
    """An <img> for a filled slot, a visible frame in concept builds, otherwise nothing."""
    photo = config.photos.get(slot.lower(), Photo())
    if photo.src:
        if not photo.alt.strip():
            raise ValueError(f"Photo '{slot.lower()}' needs alt text")
        return (
            f'<figure class="photo"><img src="photos/{html.escape(photo.src)}" '
            f'alt="{html.escape(photo.alt)}" loading="lazy" decoding="async"></figure>'
        )
    if config.photo_placeholders:
        return f'<figure class="photo photo--empty" aria-hidden="true" data-slot="{slot.lower()}"></figure>'
    return ""


def render(template: str, config: SiteConfig, contact: Contact) -> str:
    for name, value in config.colors.model_dump().items():
        if not HEX_COLOR.match(value):
            raise ValueError(f"Colour '{name}' must look like #1a2b3c, got {value!r}")
    values = {
        "COLOR_PRIMARY": config.colors.primary,
        "COLOR_ACCENT": config.colors.accent,
        "COLOR_BACKGROUND": config.colors.background,
        "COLOR_TEXT": config.colors.text,
        "CTA_BUTTONS": cta_buttons(config, contact.phone),
        "PHONE": html.escape(contact.phone),
        "PHONE_LINK": phone_link(contact.phone),
        "KVK": html.escape(contact.kvk),
    }
    page = PHOTO_SLOT.sub(lambda m: photo_html(m.group(1), config), template)
    for key, value in values.items():
        page = page.replace("{{" + key + "}}", value)
    leftover = PLACEHOLDER.findall(page)
    if leftover:
        raise ValueError(f"Unfilled placeholders in template: {sorted(set(leftover))}")
    return page


def main() -> int:
    config = SiteConfig.model_validate(json.loads(CONFIG.read_text(encoding="utf-8")))
    contact = Contact(
        phone=read_phone(CONTACT_FILE.read_text(encoding="utf-8")),
        kvk=read_kvk(json.loads(BOOKKEEPING_FILE.read_text(encoding="utf-8"))),
    )
    page = render(TEMPLATE.read_text(encoding="utf-8"), config, contact)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(page, encoding="utf-8")
    for photo in config.photos.values():
        if photo.src:
            OUT_PHOTO_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PHOTO_DIR / photo.src, OUT_PHOTO_DIR / photo.src)
    print(OUT_FILE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
