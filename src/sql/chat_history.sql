-- auto-generated definition
create table if not exists chat_history
(
    "index"   integer
        constraint chat_history_pk
            primary key autoincrement,
    from_user INTEGER,
    to_user   INTEGER,
    type      TEXT,
    content   ANY TEXT,
    send_time integer
);

create unique index if not exists chat_history_index
    on chat_history ("index");

