from crawler.utils.converter import extract_content, to_markdown


def test_extract_content():
    html = """
    <html>
        <head><title>Test</title></head>
        <body>
            <header>Header</header>
            <main>
                <h1>Main Title</h1>
                <p>This is the main content of the article that should be extracted by readability.</p>
                <p>Some more text to make it longer so readability picks it up.</p>
            </main>
            <footer>Footer</footer>
        </body>
    </html>
    """
    content = extract_content(html)
    assert "Main Title" in content
    assert "This is the main content" in content
    assert "Footer" not in content


def test_to_markdown():
    html = """
    <div>
        <h1>Title</h1>
        <p>Text</p>
        <pre><code class="language-python">print("Hello")</code></pre>
    </div>
    """
    url = "https://example.com/page"
    md = to_markdown(html, url)

    assert "source_url: https://example.com/page" in md
    assert "# Title" in md
    assert "```python" in md or 'print("Hello")' in md
