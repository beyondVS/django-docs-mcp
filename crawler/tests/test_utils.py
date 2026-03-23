from pathlib import Path

from bs4 import BeautifulSoup
from utils.converter import extract_content, fix_links, to_markdown
from utils.scraper import Scraper
from utils.storage import get_file_path


def test_storage_get_file_path() -> None:
    base_dir = ".temp"
    url = "https://docs.djangoproject.com/en/5.2/topics/db/models/"

    # HTML path
    html_path = get_file_path(base_dir, url, extension=".html")
    assert html_path == Path(".temp/topics/db/models.html")

    # Markdown path
    md_path = get_file_path(base_dir, url, extension=".md")
    assert md_path == Path(".temp/topics/db/models.md")

    # Root index
    root_url = "https://docs.djangoproject.com/en/5.2/"
    root_path = get_file_path(base_dir, root_url)
    assert root_path == Path(".temp/index.html")


def test_scraper_normalize_url() -> None:
    scraper = Scraper()
    url = "https://docs.djangoproject.com/en/5.2/topics/db/models"
    normalized = scraper.normalize_url(url)
    assert normalized == "https://docs.djangoproject.com/en/5.2/topics/db/models/"

    url_with_slash = "https://docs.djangoproject.com/en/5.2/topics/db/models/"
    assert (
        scraper.normalize_url(url_with_slash)
        == "https://docs.djangoproject.com/en/5.2/topics/db/models/"
    )


def test_scraper_is_target_url() -> None:
    scraper = Scraper()
    base = "https://docs.djangoproject.com/en/5.2/"
    exclusions = ["https://docs.djangoproject.com/en/5.2/releases/"]

    assert (
        scraper.is_target_url("https://docs.djangoproject.com/en/5.2/topics/", base, exclusions)
        is True
    )
    assert (
        scraper.is_target_url(
            "https://docs.djangoproject.com/en/5.2/releases/5.2/", base, exclusions
        )
        is False
    )
    assert scraper.is_target_url("https://www.google.com", base, exclusions) is False


def test_converter_extract_content() -> None:
    html = """
    <html>
        <body>
            <nav>Nav</nav>
            <article id="docs-content">
                <h1>Title</h1>
                <p>Content</p>
            </article>
            <footer>Footer</footer>
        </body>
    </html>
    """
    selectors = ["article#docs-content"]
    content = extract_content(html, selectors=selectors)
    assert "Title" in content
    assert "Content" in content
    assert "Nav" not in content
    assert "Footer" not in content


def test_converter_fix_links() -> None:
    html = '<article><a href="../howto/">Link</a><img src="../../_images/img.png"></article>'
    soup = BeautifulSoup(html, "html.parser")
    base_url = "https://docs.djangoproject.com/en/5.2/topics/db/"

    fix_links(soup, base_url)

    a_tag = soup.find("a")
    img_tag = soup.find("img")

    assert a_tag is not None
    assert img_tag is not None
    assert a_tag["href"] == "https://docs.djangoproject.com/en/5.2/topics/howto/"
    assert img_tag["src"] == "https://docs.djangoproject.com/en/5.2/_images/img.png"


def test_converter_to_markdown() -> None:
    html = "<article><h1>My Title</h1><p>Hello World</p></article>"
    url = "https://docs.djangoproject.com/en/5.2/test/"

    md_output = to_markdown(html, url, target_version="5.2")

    assert "url: https://docs.djangoproject.com/en/5.2/test/" in md_output
    assert 'title: "My Title"' in md_output
    assert "version: 5.2" in md_output
    assert "# My Title" in md_output
    assert "Hello World" in md_output
