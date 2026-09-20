import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import math
from collections import Counter
from urllib.parse import urljoin, urlparse


# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect("search_engine.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,
    title TEXT,
    content TEXT
)
""")

conn.commit()


# =========================================================
# COMMON WORDS
# =========================================================

STOP_WORDS = {
    "the", "is", "a", "an", "and", "or", "of",
    "to", "in", "for", "on", "with", "this",
    "that", "are", "was", "be", "as", "by",
    "at", "from", "it", "you", "your", "we"
}


# =========================================================
# TEXT PROCESSING
# =========================================================

def tokenize(text):
    """
    Convert text into searchable words.
    """

    text = text.lower()

    words = re.findall(r"[a-zA-Z0-9]+", text)

    result = []

    for word in words:
        if word not in STOP_WORDS and len(word) > 1:
            result.append(word)

    return result


# =========================================================
# SAVE PAGE
# =========================================================

def save_page(url, title, content):

    cursor.execute("""
        INSERT OR REPLACE INTO pages (url, title, content)
        VALUES (?, ?, ?)
    """, (url, title, content))

    conn.commit()


# =========================================================
# CRAWL SINGLE PAGE
# =========================================================

def crawl_page(url):

    try:

        headers = {
            "User-Agent":
            "Mozilla/5.0 MiniSearchEngine/1.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Remove unwanted HTML elements
        for element in soup([
            "script",
            "style",
            "nav",
            "footer",
            "noscript"
        ]):
            element.decompose()

        # Get title
        if soup.title:
            title = soup.title.get_text(
                strip=True
            )
        else:
            title = url

        # Get visible text
        content = soup.get_text(
            separator=" ",
            strip=True
        )

        # Remove excessive spaces
        content = re.sub(
            r"\s+",
            " ",
            content
        )

        save_page(
            url,
            title,
            content
        )

        print("\nPage indexed successfully!")
        print("Title:", title)
        print("URL:", url)

        return soup

    except requests.exceptions.RequestException as e:

        print("\nUnable to crawl page.")
        print("Reason:", e)

        return None


# =========================================================
# WEBSITE CRAWLER
# =========================================================

def crawl_website(start_url, max_pages=10):

    visited = set()

    queue = [start_url]

    domain = urlparse(start_url).netloc

    print("\nStarting crawler...")
    print("Domain:", domain)

    while queue and len(visited) < max_pages:

        url = queue.pop(0)

        if url in visited:
            continue

        print(
            "\nCrawling:",
            url
        )

        soup = crawl_page(url)

        visited.add(url)

        if soup is None:
            continue

        # Find links
        for link in soup.find_all(
            "a",
            href=True
        ):

            new_url = urljoin(
                url,
                link["href"]
            )

            parsed = urlparse(
                new_url
            )

            # Remove # fragments
            new_url = new_url.split("#")[0]

            # Crawl only same website
            if (
                parsed.netloc == domain
                and new_url not in visited
                and new_url.startswith(
                    ("http://", "https://")
                )
            ):

                if new_url not in queue:
                    queue.append(new_url)

    print("\n==========================")
    print("Crawling completed.")
    print(
        len(visited),
        "pages processed."
    )
    print("==========================")


# =========================================================
# VIEW INDEXED PAGES
# =========================================================

def view_pages():

    cursor.execute("""
        SELECT id, title, url
        FROM pages
        ORDER BY id
    """)

    pages = cursor.fetchall()

    if not pages:

        print(
            "\nNo pages have been indexed."
        )

        return

    print("\n========== INDEXED PAGES ==========")

    for page in pages:

        print("\nID:", page[0])
        print("Title:", page[1])
        print("URL:", page[2])


# =========================================================
# CALCULATE SEARCH SCORE
# =========================================================

def calculate_score(
    query_words,
    title,
    content
):

    title_words = tokenize(title)

    content_words = tokenize(content)

    title_counter = Counter(
        title_words
    )

    content_counter = Counter(
        content_words
    )

    score = 0

    for word in query_words:

        # Title matches are more important
        title_frequency = (
            title_counter[word]
        )

        score += (
            title_frequency * 5
        )

        # Content matches
        content_frequency = (
            content_counter[word]
        )

        if content_frequency > 0:

            score += (
                1 +
                math.log(
                    1 + content_frequency
                )
            )

    return score


# =========================================================
# CREATE SEARCH SNIPPET
# =========================================================

def create_snippet(
    content,
    query_words,
    length=180
):

    lower_content = (
        content.lower()
    )

    position = -1

    for word in query_words:

        position = (
            lower_content.find(word)
        )

        if position != -1:
            break

    if position == -1:

        return (
            content[:length] + "..."
        )

    start = max(
        0,
        position - 60
    )

    end = min(
        len(content),
        position + length
    )

    snippet = content[
        start:end
    ]

    return "..." + snippet + "..."


# =========================================================
# SEARCH ENGINE
# =========================================================

def search(query):

    query_words = tokenize(query)

    if not query_words:

        print(
            "\nPlease enter valid search words."
        )

        return

    cursor.execute("""
        SELECT url, title, content
        FROM pages
    """)

    pages = cursor.fetchall()

    if not pages:

        print(
            "\nNo pages indexed yet."
        )

        return

    results = []

    for page in pages:

        url = page[0]
        title = page[1]
        content = page[2]

        score = calculate_score(
            query_words,
            title,
            content
        )

        if score > 0:

            results.append(
                (
                    score,
                    title,
                    url,
                    content
                )
            )

    # Highest score first
    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    if not results:

        print(
            "\nNo matching results found."
        )

        return

    print(
        "\n===================================="
    )

    print(
        "Search Results for:",
        query
    )

    print(
        "===================================="
    )

    for index, result in enumerate(
        results[:10],
        start=1
    ):

        score = result[0]
        title = result[1]
        url = result[2]
        content = result[3]

        snippet = create_snippet(
            content,
            query_words
        )

        print(
            "\n{}. {}".format(
                index,
                title
            )
        )

        print(
            "Score: {:.2f}".format(
                score
            )
        )

        print(
            "URL:",
            url
        )

        print(
            "Preview:",
            snippet
        )


# =========================================================
# DATABASE STATISTICS
# =========================================================

def statistics():

    cursor.execute(
        "SELECT COUNT(*) FROM pages"
    )

    total_pages = (
        cursor.fetchone()[0]
    )

    cursor.execute("""
        SELECT content
        FROM pages
    """)

    rows = cursor.fetchall()

    total_words = 0

    unique_words = set()

    for row in rows:

        words = tokenize(
            row[0]
        )

        total_words += len(words)

        unique_words.update(
            words
        )

    print(
        "\n========== SEARCH ENGINE STATISTICS =========="
    )

    print(
        "Indexed Pages:",
        total_pages
    )

    print(
        "Total Indexed Words:",
        total_words
    )

    print(
        "Unique Words:",
        len(unique_words)
    )


# =========================================================
# DELETE DATABASE CONTENT
# =========================================================

def clear_index():

    confirm = input(
        "\nDelete all indexed pages? (yes/no): "
    )

    if confirm.lower() == "yes":

        cursor.execute(
            "DELETE FROM pages"
        )

        conn.commit()

        print(
            "Search index cleared."
        )

    else:

        print(
            "Operation cancelled."
        )


# =========================================================
# MAIN MENU
# =========================================================

def main():

    while True:

        print(
            "\n======================================"
        )

        print(
            "          MINI SEARCH ENGINE"
        )

        print(
            "======================================"
        )

        print(
            "1. Crawl Single Web Page"
        )

        print(
            "2. Crawl Website"
        )

        print(
            "3. View Indexed Pages"
        )

        print(
            "4. Search"
        )

        print(
            "5. Search Engine Statistics"
        )

        print(
            "6. Clear Search Index"
        )

        print(
            "7. Exit"
        )

        choice = input(
            "\nEnter choice (1-7): "
        ).strip()

        if choice == "1":

            url = input(
                "Enter webpage URL: "
            ).strip()

            if not url.startswith(
                ("http://", "https://")
            ):

                url = (
                    "https://" + url
                )

            crawl_page(url)

        elif choice == "2":

            url = input(
                "Enter website URL: "
            ).strip()

            if not url.startswith(
                ("http://", "https://")
            ):

                url = (
                    "https://" + url
                )

            try:

                max_pages = int(
                    input(
                        "Maximum pages to crawl: "
                    )
                )

            except ValueError:

                print(
                    "Invalid number."
                )

                continue

            crawl_website(
                url,
                max_pages
            )

        elif choice == "3":

            view_pages()

        elif choice == "4":

            query = input(
                "\nSearch: "
            )

            search(query)

        elif choice == "5":

            statistics()

        elif choice == "6":

            clear_index()

        elif choice == "7":

            print(
                "\nSearch engine closed."
            )

            break

        else:

            print(
                "\nInvalid choice."
            )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    try:

        main()

    finally:

        conn.close()