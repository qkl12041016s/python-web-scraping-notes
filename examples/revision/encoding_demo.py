import requests


def decode_unreliable_html(response, known_encoding=None):
    guessed = response.apparent_encoding
    encoding = known_encoding or guessed or "utf-8"
    text = response.content.decode(encoding, errors="strict")
    return text, response.encoding, guessed, encoding


if __name__ == "__main__":
    response = requests.Response()
    response.status_code = 200
    response._content = "<p>中文笔记与字符编码</p>".encode("gb18030")
    response.encoding = "utf-8"  # Deliberately incorrect metadata.
    text, declared, guessed, used = decode_unreliable_html(
        response, known_encoding="gb18030"
    )
    print("declared:", declared, "guessed:", guessed, "used:", used)
    print(text)
