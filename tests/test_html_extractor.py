"""Unit tests for HTMLExtractor."""

import pytest

from abzu.html_extractor import HTMLExtractor


@pytest.fixture
def extractor():
    """Create an HTMLExtractor instance for testing."""
    return HTMLExtractor()


def test_plaintext_extraction(extractor):
    """Test extraction of plaintext content."""
    html = "This is just text without HTML tags."
    result = extractor.extract(html)
    assert "This is just text without HTML tags." in result


def test_simple_html_extraction(extractor):
    """Test extraction of simple HTML content."""
    html = """
    <html>
        <head><title>Test Article</title></head>
        <body>
            <h1>Main Heading</h1>
            <p>This is a paragraph.</p>
            <p>Another paragraph.</p>
        </body>
    </html>
    """
    result = extractor.extract(html)
    assert "Title: Test Article" in result
    assert "# Main Heading" in result
    assert "This is a paragraph." in result
    assert "Another paragraph." in result


def test_complex_html_with_structure(extractor):
    """Test extraction preserves document structure."""
    html = """
    <html>
        <head><title>Complex Article</title></head>
        <body>
            <article>
                <h1>Main Title</h1>
                <h2>Section 1</h2>
                <p>Section 1 content.</p>
                <h3>Subsection 1.1</h3>
                <p>Subsection content.</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </article>
        </body>
    </html>
    """
    result = extractor.extract(html)
    assert "# Main Title" in result
    assert "## Section 1" in result
    assert "### Subsection 1.1" in result
    assert "- Item 1" in result
    assert "- Item 2" in result


def test_script_and_style_removal(extractor):
    """Test that script and style tags are removed."""
    html = """
    <html>
        <head>
            <style>body { color: red; }</style>
        </head>
        <body>
            <h1>Title</h1>
            <script>alert('hello');</script>
            <p>Content</p>
        </body>
    </html>
    """
    result = extractor.extract(html)
    assert "color: red" not in result
    assert "alert('hello')" not in result
    assert "# Title" in result
    assert "Content" in result


def test_no_article_container(extractor):
    """Test extraction when no article container is found."""
    html = """
    <html>
        <body>
            <div>
                <h1>No Article Tag</h1>
                <p>This HTML has no article tag.</p>
            </div>
        </body>
    </html>
    """
    result = extractor.extract(html)
    assert "# No Article Tag" in result
    assert "This HTML has no article tag." in result


def test_empty_html(extractor):
    """Test handling of empty HTML."""
    html = "<html><body></body></html>"
    result = extractor.extract(html)
    assert result == ""


def test_malformed_html(extractor):
    """Test handling of malformed HTML."""
    html = "<h1>Title<p>Paragraph"
    result = extractor.extract(html)
    # Should still extract text without crashing
    assert "Title" in result
    assert "Paragraph" in result


def test_nested_lists(extractor):
    """Test extraction of nested list items."""
    html = """
    <html>
        <body>
            <ul>
                <li>Item 1</li>
                <li>Item 2
                    <ul>
                        <li>Nested Item 2.1</li>
                        <li>Nested Item 2.2</li>
                    </ul>
                </li>
                <li>Item 3</li>
            </ul>
        </body>
    </html>
    """
    result = extractor.extract(html)
    assert "- Item 1" in result
    assert "- Item 2" in result
    assert "- Nested Item 2.1" in result
    assert "- Nested Item 2.2" in result
    assert "- Item 3" in result


def test_whitespace_handling(extractor):
    """Test proper handling of whitespace."""
    html = """
    <html>
        <body>
            <h1>    Title with spaces    </h1>
            <p>


                Content with many spaces


            </p>
        </body>
    </html>
    """
    result = extractor.extract(html)
    assert "# Title with spaces" in result
    assert "Content with many spaces" in result
    # Should not have excessive blank lines
    assert "\n\n\n" not in result


def test_special_characters(extractor):
    """Test handling of special HTML characters."""
    html = """
    <html>
        <body>
            <h1>Title &amp; More</h1>
            <p>Content with &lt;special&gt; characters &quot;quoted&quot;</p>
        </body>
    </html>
    """
    result = extractor.extract(html)
    assert "Title & More" in result
    assert 'Content with <special> characters "quoted"' in result


def test_multiple_article_containers(extractor):
    """Test extraction with multiple potential article containers."""
    html = """
    <html>
        <body>
            <div class="content">
                <p>Not the main content</p>
            </div>
            <article>
                <h1>Main Article</h1>
                <p>This is the main article content.</p>
            </article>
        </body>
    </html>
    """
    result = extractor.extract(html)
    # Should prefer the article tag
    assert "# Main Article" in result
    assert "This is the main article content." in result


def test_all_heading_levels(extractor):
    """Test extraction of all heading levels (h1-h6)."""
    html = """
    <html>
        <body>
            <h1>Heading 1</h1>
            <h2>Heading 2</h2>
            <h3>Heading 3</h3>
            <h4>Heading 4</h4>
            <h5>Heading 5</h5>
            <h6>Heading 6</h6>
        </body>
    </html>
    """
    result = extractor.extract(html)
    assert "# Heading 1" in result
    assert "## Heading 2" in result
    assert "### Heading 3" in result
    assert "#### Heading 4" in result
    assert "##### Heading 5" in result
    assert "###### Heading 6" in result


def test_exception_handling(extractor):
    """Test that extractor handles exceptions gracefully."""
    # Pass non-string input
    result = extractor.extract(None)
    # Should not crash and return empty or fallback
    assert isinstance(result, str)


def test_no_title(extractor):
    """Test extraction when no title is present."""
    html = """
    <html>
        <body>
            <h1>Main Content</h1>
            <p>No title tag in this HTML.</p>
        </body>
    </html>
    """
    result = extractor.extract(html)
    assert "Title:" not in result
    assert "# Main Content" in result


def test_empty_title(extractor):
    """Test extraction when title tag is empty."""
    html = """
    <html>
        <head><title></title></head>
        <body>
            <h1>Content</h1>
        </body>
    </html>
    """
    result = extractor.extract(html)
    assert "Title:" not in result
    assert "# Content" in result


def test_main_role_container(extractor):
    """Test extraction with role='main' container."""
    html = """
    <html>
        <body>
            <div>Side content</div>
            <div role="main">
                <h1>Main Content</h1>
                <p>This is the main area.</p>
            </div>
        </body>
    </html>
    """
    result = extractor.extract(html)
    assert "# Main Content" in result
    assert "This is the main area." in result


def test_content_class_container(extractor):
    """Test extraction with class='content' container."""
    html = """
    <html>
        <body>
            <nav>Navigation</nav>
            <div class="content">
                <h1>Article Title</h1>
                <p>Article content.</p>
            </div>
            <footer>Footer</footer>
        </body>
    </html>
    """
    result = extractor.extract(html)
    assert "# Article Title" in result
    assert "Article content." in result
