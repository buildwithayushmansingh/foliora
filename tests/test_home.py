from app import create_app
from config import DevConfig


class Cfg(DevConfig):
    TESTING = True
    PORTFOLIO_URL = "https://example.com"


def test_home_renders_with_portfolio():
    c = create_app(Cfg).test_client()
    r = c.get("/")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert 'src="https://example.com"' in html
    for anchor in ("how-it-works", "featured", "about", "contact", "coming-soon"):
        assert f'id="{anchor}"' in html


def test_home_without_portfolio_url():
    class Empty(Cfg):
        PORTFOLIO_URL = ""
    html = create_app(Empty).test_client().get("/").get_data(as_text=True)
    assert "PORTFOLIO_URL" in html
