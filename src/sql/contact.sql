-- auto-generated definition
create table if not exists contact
(
    id       integer
        constraint contact_pk
            primary key autoincrement,
    username TEXT,
    name     text,
    mem      text
);

