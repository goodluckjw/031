import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote

OC = "chetera"
BASE = "http://www.law.go.kr"

def get_law_list_from_api(query):
    exact_query = f'\"{query}\"'
    encoded_query = quote(exact_query)
    page = 1
    laws = []

    while True:
        url = f"{BASE}/DRF/lawSearch.do?OC={OC}&target=law&type=XML&display=100&page={page}&search=2&knd=A0002&query={encoded_query}"
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8'
        if res.status_code != 200:
            break

        root = ET.fromstring(res.content)
        found = 0
        for law in root.findall("law"):
            name = law.findtext("법령명한글").strip()
            mst = law.findtext("법령일련번호")
            detail = law.findtext("법령상세링크")
            full_link = BASE + detail
            laws.append({"법령명": name, "MST": mst, "URL": full_link})
            found += 1

        if found < 100:
            break
        page += 1

    return laws

def get_law_text_by_mst(mst):
    url = f"{BASE}/DRF/lawService.do?OC={OC}&target=law&MST={mst}&type=XML"
    try:
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8'
        if res.status_code == 200:
            return res.content
    except Exception as e:
        print(f"[오류] 본문 요청 실패 (MST={mst}):", e)
    return None

def get_highlighted_articles(mst, keyword):
    xml_data = get_law_text_by_mst(mst)
    if not xml_data:
        return "⚠️ 본문을 불러올 수 없습니다."

    tree = ET.fromstring(xml_data)
    articles = tree.findall(".//조문")
    results = []

    for article in articles:
        jo = article.findtext("조번호", "").strip()
        title = article.findtext("조문제목", "").strip()
        content = article.findtext("조문내용", "").strip()
        항들 = article.findall("항")

        found = False
        항texts = []

        for hang in 항들:
            ha = hang.findtext("항번호", "").strip()
            text = hang.findtext("항내용", "").strip()
            if keyword in text:
                found = True
            항texts.append((ha, text))

        if keyword in title or keyword in content:
            found = True

        if found:
            output = f"<br><strong>📌 제{jo}조 {title}</strong><br>"
            if content:
                content = content.replace(keyword, f"<span style='color:red'>{keyword}</span>")
                output += f"{content}<br>"
            for ha, text in 항texts:
                highlighted = text.replace(keyword, f"<span style='color:red'>{keyword}</span>")
                output += f"제{ha}항: {highlighted}<br>"
            results.append(output)

    if not results:
        return "🔍 해당 단어를 포함한 조문이 없습니다."
    return "".join(results)
