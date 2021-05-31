import slack_md

custom_format_at_cb = lambda id, name: "@++" + (name or id) + "++"
custom_format_hash_cb = lambda id, name: "#++" + (name or id) + "++"
custom_format_group_cb = lambda id, name: "^++" + (name or id) + "++"
custom_format_at_here = lambda id, name: "@++here++"
custom_format_at_channel = lambda id, name: "@++channel++"
custom_format_at_everyone = lambda id, name: "@++everyone++"


def test_parse_user_mentions():
    """Should parse user mentions"""
    md = "hey <@ID|user>!"
    out = '<p>hey <span class="mention">@user</span>!</p>'


# with callback to resolve id/name
def test_custom_user():
    """Should do custom user parsing"""
    md = "hey <@ID|user>!"
    out = '<p>hey <span class="mention">@++user++</span>!</p>'
    assert slack_md.convert(md, user_cb=custom_format_at_cb) == out


def test_channel_mentions():
    """Should parse channel mentions"""
    md = "hey <#ID|chan>!"
    out = '<p>hey <span class="mention">#chan</span>!</p>'
    assert slack_md.convert(md) == out


# with callback to resolve id/name
def test_custom_channel():
    """Should do custom channel parsing"""
    md = "hey <#ID|chan>!"
    out = '<p>hey <span class="mention">#++chan++</span>!</p>'
    assert slack_md.convert(md, channel_cb=custom_format_hash_cb) == out


def test_user_group_mentions():
    """Should parse user group mentions"""
    md = "hey <!subteam^ID|usergroup>!"
    out = '<p>hey <span class="mention">^usergroup</span>!</p>'
    assert slack_md.convert(md) == out


# with callback to resolve id/name
def test_custom_user_group():
    """Should do custom user group parsing"""
    md = "hey <!subteam^ID|usergroup>!"
    out = '<p>hey <span class="mention">^++usergroup++</span>!</p>'
    assert slack_md.convert(md, user_group_cb=custom_format_group_cb) == out


# # with callback to resolve id/name
def test_at_here():
    """Should parse at here"""
    md = "hey <!here>!"
    out = '<p>hey <span class="mention">@here</span>!</p>'
    assert slack_md.convert(md) == out


# with callback to resolve id/name
def test_custom_at_here():
    """Should do custom at here parsing"""
    md = "hey <!here>!"
    out = '<p>hey <span class="mention">@++here++</span>!</p>'
    assert slack_md.convert(md, at_here_cb=custom_format_at_here) == out


def test_at_channel():
    """Should parse at channel"""
    md = "hey <!channel>!"
    out = '<p>hey <span class="mention">@channel</span>!</p>'
    assert slack_md.convert(md) == out


# with callback to resolve id/name
def test_custom_at_channel():
    """Should do custom at channel parsing"""
    md = "hey <!channel>!"
    out = '<p>hey <span class="mention">@++channel++</span>!</p>'
    assert slack_md.convert(md, at_channel_cb=custom_format_at_channel) == out


def test_at_everyone():
    """Should parse at everyone"""
    md = "hey <!everyone>!"
    out = '<p>hey <span class="mention">@everyone</span>!</p>'
    assert slack_md.convert(md) == out


def test_at_here():
    """Should parse at everyone"""
    md = "hey <!here>!"
    out = '<p>hey <span class="mention">@here</span>!</p>'
    assert slack_md.convert(md) == out


# with callback to resolve id/name
def test_custom_at_everyone():
    """Should do custom at everyone parsing"""
    md = "hey <!everyone>!"
    out = '<p>hey <span class="mention">@++everyone++</span>!</p>'
    assert slack_md.convert(md, at_everyone_cb=custom_format_at_everyone) == out


def test_prio_links():
    """should prioritize links"""
    md = "Hey _beep <https://example.org|hmm_yeah>"
    out = '<p>Hey _beep <a href="https://example.org">hmm_yeah</a></p>'
    assert slack_md.convert(md) == out
