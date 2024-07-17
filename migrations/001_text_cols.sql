-- 1. Add columns
ALTER TABLE post ADD text_html TEXT;
ALTER TABLE post ADD text_markdown TEXT;

-- 2. Run 001_text_cols.py (with test_run=False)

-- 3. Drop column "text"
CREATE TEMPORARY TABLE temp AS
SELECT
  id,
  title,
  published_date,
  last_modified_date,
  is_published,
  user_id,
  text_html,
  text_markdown
FROM post;

DROP TABLE post;

CREATE TABLE post (
	id INTEGER NOT NULL,
	title VARCHAR,
	text_html TEXT,
	text_markdown TEXT,
	published_date DATETIME,
	last_modified_date DATETIME,
	is_published BOOLEAN,
	user_id INTEGER NOT NULL,
	CONSTRAINT POST_PK PRIMARY KEY (id),
	CONSTRAINT FK_post_user FOREIGN KEY (user_id) REFERENCES "user"(id)
);
CREATE INDEX ix_post_id ON post (id);

INSERT INTO post
 (id,
  title,
  published_date,
  last_modified_date,
  is_published,
  user_id,
  text_html,
  text_markdown)
SELECT
  id,
  title,
  published_date,
  last_modified_date,
  is_published,
  user_id,
  text_html,
  text_markdown
FROM temp;

DROP TABLE temp;
