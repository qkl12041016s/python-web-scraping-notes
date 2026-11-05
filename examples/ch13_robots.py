"""Read a robots rule without contacting a website."""

from urllib.robotparser import RobotFileParser


parser = RobotFileParser()
parser.parse([
    "User-agent: *",
    "Disallow: /private/",
    "Allow: /public/",
])

base = "https://example.org"
for path in ("/private/report", "/public/report"):
    print(path, parser.can_fetch("StudyCrawler", base + path))
