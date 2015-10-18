-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

drop database if exists tournament;

create database tournament;

\c tournament;

drop table if exists matches;
drop table if exists players;

create table players(
    name text,
    id serial primary key
);

create table matches(
    id serial references players(id) primary key,
    win integer,
    lose integer
);
