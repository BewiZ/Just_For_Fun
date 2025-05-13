import requests, os, re, time
from bs4 import BeautifulSoup


def get_tai(soup, tai):
    "获取小说标题，作者，简介，总章节数"

    title = soup.select("div.book div.info h1")
    author = [soup.select("div.book div.info div.small span")[0]]
    intro = soup.select("div.book div.info dl dd")
    newest = soup.select("div.book div.info div.small span.last:nth-of-type(4) a")

    tai = title + author + intro + newest
    for i in range(len(tai)):
        item = tai[i].text.strip()
        if i == 3:
            newest_number = int(re.findall(r"第(\d+)章", item)[0])
            break
        clean_tai.append(item)
    clean_tai.append(newest_number)
    return clean_tai


"""
def get_every_content(url):
    "获取每一章的内容"

    response_2 = requests.get(url, headers=headers)
    content_2 = response_2.text
    soup_2 = BeautifulSoup(content_2, "lxml")

    chapter_title = soup_2.select("div.book.reader div.content h1.wap_none")[0].text.strip()  # 章节标题
    chapter_text = soup_2.select("div.book.reader div.content div#chaptercontent")[0].text.split("<br /><br />")[0]

    chapter_orgnaized_text = chapter_title + "\n" + orgnaize_content(chapter_text)  # 整理章节内容
    # chapter[chapter_title] = chapter_title + "\n" + orgnaize_content(chapter_text)  # 标题加内容
    return chapter_title, chapter_orgnaized_text
"""


def get_every_content(url):
    """获取每一章的内容（带超时重试）"""
    max_retries = 3  # 最大重试次数
    retry_delay = 5  # 重试间隔（秒）

    for attempt in range(max_retries):
        try:
            # 添加 timeout 参数（连接超时+读取超时）
            response_2 = requests.get(url, headers=headers, timeout=(10, 30))
            response_2.raise_for_status()  # 检查 HTTP 状态码（如 404/500）
            break  # 请求成功，退出循环
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
            print(f"请求失败（第 {attempt+1} 次重试）: {e}")
            if attempt == max_retries - 1:
                raise  # 重试次数耗尽，抛出异常
            time.sleep(retry_delay)

    content_2 = response_2.text
    soup_2 = BeautifulSoup(content_2, "lxml")

    chapter_title = soup_2.select("div.book.reader div.content h1.wap_none")[0].text.strip()
    chapter_text = soup_2.select("div.book.reader div.content div#chaptercontent")[0].text.split("<br /><br />")[0]

    chapter_orgnaized_text = chapter_title + "\n" + orgnaize_content(chapter_text)
    return chapter_title, chapter_orgnaized_text


def orgnaize_content(chapter_text):
    "整理章节内容"

    chapter_orgnaized_text = chapter_text.replace("\u3000\u3000", "\n\n\u3000\u3000").lstrip("\n") + "\n\n\n\n"
    chapter_orgnaized_text = re.sub(
        r"\s*请收藏本站：https:\/\/www\.bie5\.cc。笔趣阁手机版：https:\/\/m\.bie5\.cc\s*『点此报错』『加入书签』",
        "",
        chapter_orgnaized_text,
    )
    return chapter_orgnaized_text


if __name__ == "__main__":
    book_id = "142619"
    url = f"https://www.bie5.cc/html/{book_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    content = response.text
    soup = BeautifulSoup(content, "lxml")

    tai = []
    clean_tai = []
    # chapter = {}

    get_tai(soup, tai)  # 获取小说标题0，作者1，简介2，总章节数3

    with open(f"{clean_tai[0]}.txt", "w", encoding="utf-8") as file:
        file.write(clean_tai[0] + "\n" + clean_tai[1] + "\n" + clean_tai[2] + "\n\n")  # 小说标题，作者，简介

    for j in range(clean_tai[3]):
        n_url = f"https://www.bie5.cc/html/{book_id}/{j+1}.html"

        chapter_title, chapter_orgnaized_text = get_every_content(n_url)  # 获取每一章的内容
        # chapter_title = list(chapter.keys())[j]  # 章节标题

        with open(f"{clean_tai[0]}.txt", "a", encoding="utf-8") as file:
            file.write(chapter_orgnaized_text + "\n")

        print(f"章节{chapter_title}已添加")
