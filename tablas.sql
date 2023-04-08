CREATE TABLE films IF NOT EXISTS(
    id integer,
    vote_average numeric,
    year integer
)

CREATE TABLE stats IF NOT EXISTS(
    year integer,
    vote_average numeric,
    quantity integer
)
