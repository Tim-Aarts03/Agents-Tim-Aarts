import re

import pytest

from tools.site_build import (
    TEMPLATE,
    Colors,
    Contact,
    SiteConfig,
    cta_buttons,
    phone_link,
    read_kvk,
    read_phone,
    render,
)

COLORS = Colors(primary="#111111", accent="#222222", background="#333333", text="#444444")
CONTACT = Contact(phone="06 12 34 56 78", kvk="12345678")


def test_phone_link_keeps_only_digits():
    assert phone_link("06 12 34 56 78") == "0612345678"
    assert phone_link("+31 6-1234 5678") == "+31612345678"


def test_read_phone_and_kvk():
    assert read_phone("- Telefoon: 06 12 34 56 78\n- E-mail: x") == "06 12 34 56 78"
    assert read_kvk({"invoice": {"kvk": "12345678"}}) == "12345678"
    with pytest.raises(ValueError):
        read_phone("- E-mail: x")
    with pytest.raises(ValueError):
        read_kvk({"invoice": {}})


def test_buttons_fall_back_to_calling_without_links():
    html = cta_buttons(SiteConfig(colors=COLORS), CONTACT.phone)
    assert "Bel voor een kennismaking" in html
    assert "tel:0612345678" in html


def test_buttons_use_form_and_booking_links():
    config = SiteConfig(form_url="https://forms.example/a", booking_url="https://cal.example/b", colors=COLORS)
    html = cta_buttons(config, CONTACT.phone)
    assert "Contactformulier invullen" in html
    assert "Kennismaking inplannen" in html
    assert "Bel voor" not in html


def test_real_template_renders_completely():
    page = render(TEMPLATE.read_text(encoding="utf-8"), SiteConfig(colors=COLORS), CONTACT)
    assert "{{" not in page
    assert "KvK 12345678" in page
    assert "#111111" in page


def test_site_never_names_client_or_email():
    # Tim's rules: no client names, no e-mail address, no prices on the site.
    page = render(TEMPLATE.read_text(encoding="utf-8"), SiteConfig(colors=COLORS), CONTACT).lower()
    assert "jacob" not in page
    # A bare "@" is allowed (CSS @media, font URLs); an e-mail address is not.
    assert not re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", page)
    assert "mailto:" not in page
    assert "€" not in page


def test_invalid_colour_is_rejected():
    bad = SiteConfig(colors=Colors(primary="green", accent="#222222", background="#333333", text="#444444"))
    with pytest.raises(ValueError):
        render(TEMPLATE.read_text(encoding="utf-8"), bad, CONTACT)
