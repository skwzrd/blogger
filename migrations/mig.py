import sqlite3
import subprocess

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils import quote_path

def convert_html_to_markdown(html_text):
    result = subprocess.run(
        ["pandoc", "--from=html+raw_html", "--to=markdown"],
        input=html_text.encode("utf-8"),
        stdout=subprocess.PIPE,
    )
    result.check_returncode()
    return result.stdout.decode("utf-8")


def convert_markdown_to_html(markdown_text):
    result = subprocess.run(
        ["pandoc", "--from=markdown", "--to=html+raw_html"],
        input=markdown_text.encode("utf-8"),
        stdout=subprocess.PIPE,
    )
    result.check_returncode()
    return result.stdout.decode("utf-8")


def update_database1(db_path, test_run = True):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info(post)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'text' not in columns:
        return

    cursor.execute("SELECT rowid, text FROM post;")
    posts = cursor.fetchall()

    update_query = "UPDATE post SET text_html = ?, text_markdown = ? WHERE rowid = ? ;"

    for rowid, text in posts:
        text_markdown = convert_html_to_markdown(text)
        text_html = convert_markdown_to_html(text_markdown)

        if not test_run:
            cursor.execute(update_query, (text_html, text_markdown, rowid))

    if not test_run:
        conn.commit()
    conn.close()


def update_database2(db_path, test_run = True):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info(post)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'path' not in columns:
        cursor.execute(f"ALTER TABLE post ADD COLUMN path TEXT")

    cursor.execute("SELECT id, title, CASE WHEN COUNT(title) OVER (PARTITION BY title) > 1 THEN 1 ELSE 0 END AS is_duplicate FROM post;")
    posts = cursor.fetchall()

    update_query = "UPDATE post SET path = ? WHERE id = ? ;"

    for pkid, title, is_duplicate in posts:
        path = quote_path(title) + (pkid if is_duplicate else '')

        if not test_run:
            cursor.execute(update_query, (path, pkid))

    if not test_run:
        conn.commit()
    conn.close()


if __name__ == "__main__":
    db_path = "blogger.db"
    update_database1(db_path, test_run=False)
    update_database2(db_path, test_run=False)
