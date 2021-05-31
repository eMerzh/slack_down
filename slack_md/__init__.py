import re
import xml.etree.ElementTree as etree
from typing import Callable, Optional

import markdown
from markdown import util
from markdown.blockparser import BlockParser
from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from markdown.inlinepatterns import (
    EMPHASIS_RE,
    STRONG_RE,
    AsteriskProcessor,
    EmStrongItem,
    InlineProcessor,
    SimpleTagPattern,
    SubstituteTagInlineProcessor,
    SubstituteTagPattern,
)

from .emojis import EMOJIS

# <http://www.123.com|Hello>
AUTOLINK_RE = r"<((?:[Ff]|[Hh][Tt])[Tt][Pp][Ss]?://[^<>|]*)(\|(?P<name>[^>]*))?>"

# two spaces at end of line
LINE_BREAK_RE = r"\n"

# shortcode emoji
RE_EMOJI = r"(:(?P<shortname>[+\-\w]+):)"


# ~this is strike~
DEL_PATTERN_ER = r"~(\S(?:\\[\s\S]|[^\\])*?\S|\S)~(?!~)"

# <!channel>
AT_CHANNEL_PATTERN_RE = r"<!channel(\|(?P<label>[^>]*))?>"

# <!everyone>
AT_EVERYONE_PATTERN_RE = r"<!everyone(\|(?P<label>[^>]*))?>"

# <!here>
AT_HERE_PATTERN_RE = r"<!here(\|([^>]*))?>"

# <#ID|channel>
CHAN_PATTERN_RE = r"<#(?P<id>[^|>]+)(\|(?P<label>[^>]*))?>"

# <@ID|user>
USER_PATTERN_RE = r"<@(?P<id>[^|>]+)(\|(?P<label>[^>]*))?>"

# <!subteam^ID|user>
SUBTEAM_PATTERN_RE = r"<!subteam\^(?P<id>[^|>]+)(\|(?P<label>[^>]+))?>"


class DelInlineProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        el = etree.Element("del")
        el.text = m.group(1)
        return el, m.start(0), m.end(0)


class AtChannelInlineProcessor(InlineProcessor):
    callback: Callable[[int, Exception], None]

    def __init__(self, pattern, callback: Callable[[str, str], str], md=None):
        super().__init__(pattern, md)
        self.callback = callback

    def handleMatch(self, m, data):
        el = etree.Element("span")
        el.set("class", "mention")
        el.text = self.callback(m.groupdict().get("label"), m.groupdict().get("label"))
        return el, m.start(0), m.end(0)


class SlackAsteriskProcessor(AsteriskProcessor):
    PATTERNS = [
        # Remove regular strong/em patterns
        EmStrongItem(re.compile(STRONG_RE, re.DOTALL | re.UNICODE), "single", "em"),
        EmStrongItem(re.compile(EMPHASIS_RE, re.DOTALL | re.UNICODE), "single", "strong"),
    ]


class SlackAutolinkInlineProcessor(InlineProcessor):
    """Return a link Element given an autolink (`<http://example/com>`)."""

    def handleMatch(self, m, data):
        el = etree.Element("a")
        el.set("href", self.unescape(m.group(1)))
        text = m.group("name") or m.group(1)
        self.md.parser.parseChunk(el, text)

        return el, m.start(0), m.end(0)


class SlackNewLine(SimpleTagPattern):  # pragma: no cover
    """Return an element of type `tag` with no children."""

    def handleMatch(self, m):
        return etree.Element("br")


class EmojiPattern(InlineProcessor):
    """Return element of type `tag` with a text attribute of group(2) of an `InlineProcessor`."""

    def handleMatch(self, m, data):
        """Handle emoji pattern matches."""

        el = m.group(1)
        shortname = m.group("shortname")
        emoji = next((e for e in EMOJIS if e["shortname"] == f":{shortname}:"), None)
        if emoji:
            return emoji["emoji"], m.start(0), m.end(0)

        return el, m.start(0), m.end(0)


class BlockQuoteProcessor(BlockProcessor):

    RE = re.compile(r"(^|\n)[ ]{0,3}>[ ]?(.*)")

    def test(self, parent, block):
        return bool(self.RE.search(block)) and not util.nearing_recursion_limit()

    def process_block_quote(self, parent, block):
        sibling = self.lastChild(parent)
        if sibling is not None and sibling.tag == "blockquote":
            # Previous block was a blockquote so set that as this blocks parent
            quote = sibling
        else:
            # This is a new blockquote. Create a new parent element.
            quote = etree.SubElement(parent, "blockquote")
        # Recursively parse block with blockquote as parent.
        # change parser state so blockquotes embedded in lists use p tags
        self.parser.state.set("blockquote")
        self.parser.parseChunk(quote, block)

    def run(self, parent, blocks):
        block = blocks.pop(0)
        m = self.RE.search(block)
        if m:
            before = block[: m.start()]  # Lines before blockquote
            after = None
            # Pass lines before blockquote in recursively for parsing forst.
            self.parser.parseBlocks(parent, [before])
            # Remove ``> `` from beginning of each line.
            new_blocks = []
            for line in block[m.start() :].split("\n"):
                if line_match := self.RE.search(line):
                    new_blocks.append(self.clean(line))
                else:
                    # It's the end of the blockquote, process what we already have
                    if new_blocks:
                        # process the block quotes
                        self.process_block_quote(parent, "\n".join(new_blocks))
                        new_blocks = []
                        # process the current line
                        self.parser.parseBlocks(parent, [line])
        if new_blocks:
            self.process_block_quote(parent, "\n".join(new_blocks))

        self.parser.state.reset()

    def clean(self, line):
        """Remove ``>`` from beginning of a line."""
        m = self.RE.match(line)
        if line.strip() == ">":
            return ""
        elif m:
            return m.group(2)
        else:
            return line


class ParagraphProcessor(BlockProcessor):
    """Process Paragraph blocks."""

    def test(self, parent, block):
        return True

    def run(self, parent, blocks):
        block = blocks.pop(0)
        if block.strip():
            # Not a blank block. Add to parent, otherwise throw it away.
            if self.parser.state.isstate("list"):
                # The parent is a tight-list.
                #
                # Check for any children. This will likely only happen in a
                # tight-list when a header isn't followed by a blank line.
                # For example:
                #
                #     * # Header
                #     Line 2 of list item - not part of header.
                sibling = self.lastChild(parent)
                if sibling is not None:
                    # Insetrt after sibling.
                    if sibling.tail:
                        sibling.tail = "{}\n{}".format(sibling.tail, block)
                    else:
                        sibling.tail = "\n%s" % block
                else:
                    # Append to parent.text
                    if parent.text:
                        parent.text = "{}\n{}".format(parent.text, block)
                    else:
                        parent.text = block.lstrip()
            else:
                if parent.tag in ["a", "blockquote"]:
                    if parent.text:
                        parent.text = parent.text + "\n" + block.lstrip()
                    else:
                        parent.text = block.lstrip()
                    # parent.text = (parent.text or "") + block.lstrip()
                else:
                    # Create a regular paragraph
                    p = etree.SubElement(parent, "p")
                    p.text = block.lstrip()


class SlackExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {
            "user": [
                lambda id, name: f"@{name or id}",
                "Callable to resolve id to name",
            ],
            "channel": [
                lambda id, name: f"#{name or id}",
                "Callable to resolve id to name",
            ],
            "userGroup": [
                lambda id, name: f"^{name or id}",
                "Callable to resolve id to name",
            ],
            "atHere": [
                lambda id, name: f"@{name or 'here'}",
                "Callable to resolve id to name",
            ],
            "atChannel": [
                lambda id, name: f"@{name or 'channel'}",
                "Callable to resolve id to name",
            ],
            "atEveryone": [
                lambda id, name: f"@{name or 'everyone'}",
                "Callable to resolve id to name",
            ],
        }

        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        # Del only if no space betweens
        md.inlinePatterns.register(DelInlineProcessor(DEL_PATTERN_ER, md), "del", 1)
        md.inlinePatterns.register(SlackAsteriskProcessor(r"\*"), "slack_em_strong", 60)

        md.inlinePatterns.register(SlackAutolinkInlineProcessor(AUTOLINK_RE, md), "autolink", 120)
        md.inlinePatterns.register(SlackNewLine(LINE_BREAK_RE, "br"), "new_break", 130)

        md.inlinePatterns.register(EmojiPattern(RE_EMOJI, md), "emoji", 75)

        md.inlinePatterns.register(
            AtChannelInlineProcessor(CHAN_PATTERN_RE, self.getConfig("channel"), md),
            "at_chan",
            200,
        )
        md.inlinePatterns.register(
            AtChannelInlineProcessor(USER_PATTERN_RE, self.getConfig("user"), md),
            "at_user",
            200,
        )
        md.inlinePatterns.register(
            AtChannelInlineProcessor(SUBTEAM_PATTERN_RE, self.getConfig("userGroup"), md),
            "at_user_group",
            200,
        )
        md.inlinePatterns.register(
            AtChannelInlineProcessor(AT_CHANNEL_PATTERN_RE, self.getConfig("atChannel"), md),
            "at_channel",
            200,
        )
        md.inlinePatterns.register(
            AtChannelInlineProcessor(AT_EVERYONE_PATTERN_RE, self.getConfig("atEveryone"), md),
            "at_everyone",
            200,
        )
        md.inlinePatterns.register(
            AtChannelInlineProcessor(AT_HERE_PATTERN_RE, self.getConfig("atHere"), md),
            "at_here",
            200,
        )
        md.parser.blockprocessors.register(BlockQuoteProcessor(md.parser), "quote", 20)
        md.parser.blockprocessors.register(ParagraphProcessor(md.parser), "paragraph", 10)

        md.preprocessors.deregister("html_block")
        md.inlinePatterns.deregister("em_strong")
        md.inlinePatterns.deregister("linebreak")
        md.treeprocessors.deregister("prettify")


def convert(
    text: str,
    user_cb: Optional[Callable[[str, str], str]] = None,
    channel_cb: Optional[Callable[[str, str], str]] = None,
    user_group_cb: Optional[Callable[[str, str], str]] = None,
    at_here_cb: Optional[Callable[[str, str], str]] = None,
    at_channel_cb: Optional[Callable[[str, str], str]] = None,
    at_everyone_cb: Optional[Callable[[str, str], str]] = None,
) -> str:

    callbacks = {
        "user": user_cb,
        "channel": channel_cb,
        "userGroup": user_group_cb,
        "atHere": at_here_cb,
        "atChannel": at_channel_cb,
        "atEveryone": at_everyone_cb,
    }
    slack_md = markdown.Markdown(extensions=[SlackExtension(**{k: v for k, v in callbacks.items() if v})])
    return slack_md.convert(text)
