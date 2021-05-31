import slack_md


def test_strong():
    """Should convert *text* to <strong>text</strong>"""
    md = "This is a *test* with *some bold* text in it"
    out = "<p>This is a <strong>test</strong> with <strong>some bold</strong> text in it</p>"
    assert slack_md.convert(md) == out


def test_em():
    """Should convert _text_ to <em>text</em>"""
    md = "This is a _test_ with _some italicized_ text in it"
    out = "<p>This is a <em>test</em> with <em>some italicized</em> text in it</p>"
    assert slack_md.convert(md) == out


def test_not_inner_underscore():
    """Should not convert inner_underscored_text to inner<em>underscored</em>text"""
    md = "This is a _test_ with some_italicized_text in it"
    out = "<p>This is a <em>test</em> with some_italicized_text in it</p>"
    assert slack_md.convert(md) == out


def test_backtick_code():
    """Should convert `text` to <code>text</code>"""
    md = "Code: `1 + 1 = 2`"
    out = "<p>Code: <code>1 + 1 = 2</code></p>"
    assert slack_md.convert(md) == out


def test_del():
    """Should convert ~text~ to <del>text</del>"""
    md = "~this~that"
    out = "<p><del>this</del>that</p>"
    assert slack_md.convert(md) == out


def test_not_del():
    """Should leave ~ test ~ alone"""
    md = "this ~ is a ~ test"
    out = "<p>this ~ is a ~ test</p>"
    assert slack_md.convert(md) == out


# def test_link_url():
#     """Should linkify URLs"""
#     md = "https://example.org"
#     out = "<p><a href=\"https://example.org\">https://example.org</a></p>"
#     assert slack_md.convert(md) == out


def test_link_url2():
    """Should linkify URLs 2"""
    md = "<https://example.org>"
    out = '<p><a href="https://example.org">https://example.org</a></p>'
    assert slack_md.convert(md) == out


def test_named_link():
    """Should handle named links"""
    md = "<https://example.org|example>"
    out = '<p><a href="https://example.org">example</a></p>'
    assert slack_md.convert(md) == out


def test_named_link_fmt():
    """Should parse named links contents"""
    md = "<https://example.org|this is *awesome*>"
    out = '<p><a href="https://example.org">this is <strong>awesome</strong></a></p>'
    assert slack_md.convert(md) == out


def test_new_lines():
    """Should parse new lines"""
    md = "new\nline"
    out = "<p>new<br />line</p>"
    assert slack_md.convert(md) == out


def test_fence_code_multi():
    """Should fence code blocks"""
    md = "text\n```code\nblock```\nmore text"
    out = "<p>text<br /><code>code\nblock</code><br />more text</p>"
    assert slack_md.convert(md) == out


def test_fence_code_line():
    """Should fence code blocks on one line"""
    md = "```test```"
    out = "<p><code>test</code></p>"
    assert slack_md.convert(md) == out


# def test_strange():
#     """Should fence weird stuff"""
#     md = "```codeblock `backtick````"
#     out = "<p><pre><code>codeblock `backtick`</code></pre></p>"
#     assert slack_md.convert(md) == out

# def test_html_escape():
#     """Should HTML-escape fenced code blocks"""
#     md = "`test`\n\n```<>```"
#     out = "<p><code>test</code><br /><br /><code>&lt;&gt;</code></p>"
#     assert slack_md.convert(md) == out

# def test_not_marks():
#     """Should not escape marks"""
#     md = "Code: \\`1 + 1` = 2`"
#     out = "<p>Code: \\<code>1 + 1</code> = 2`</p>"
#     assert slack_md.convert(md) == out


def test_simple_quote():
    """Should do simple block quotes"""
    md = "> text\n > here"
    out = "<blockquote>text<br />here</blockquote>"
    assert slack_md.convert(md) == out


def test_quote_single():
    """Should finish off block quotes"""
    md = "hey\n> text\nhere"
    out = "<p>hey</p><blockquote>text</blockquote><p>here</p>"
    assert slack_md.convert(md) == out


def test_quote_double():
    """Should finish off block quotes"""
    md = "hey\n> text\nhere\n> retext"
    out = "<p>hey</p><blockquote>text</blockquote><p>here</p><blockquote>retext</blockquote>"
    assert slack_md.convert(md) == out


def test_quote_line():
    """Should handle block quotes with blank lines"""
    md = "> text\n> \n> here"
    out = "<blockquote>text<br /><br />here</blockquote>"
    assert slack_md.convert(md) == out


def test_emojify():
    """Should emojify things"""
    md = "blah :fox: blah"
    out = "<p>blah 🦊 blah</p>"
    assert slack_md.convert(md) == out


def test_emojify2():
    md = "blah :fox_face: blah"
    out = "<p>blah 🦊 blah</p>"
    assert slack_md.convert(md) == out


def test_emoji_alone():
    """Should leave unknown emojis alone"""
    md = "blah :asdf: blah"
    out = "<p>blah :asdf: blah</p>"
    assert slack_md.convert(md) == out


def test_italicize():
    """Should not italicize in words"""
    md = "_this is italic_regular"
    out = "<p>_this is italic_regular</p>"
    assert slack_md.convert(md) == out
