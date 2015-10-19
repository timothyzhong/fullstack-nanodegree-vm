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

drop view if exists wins;
drop table if exists matches;
drop table if exists players;

create table players(
    name text,
    id serial primary key
);

create table matches(
    win integer references players(id),
    lose integer references players(id),
    id serial primary key
);

create view wins as select players.id,count(*) as wins
from players,matches
where players.id=matches.win
group by players.id; 

create view loses as select players.id,count(*) as loses
from players,matches
where players.id=matches.lose
group by players.id;

create view rankings as select players.id as id,name,coalesce(wins,0) as wins
from players left join wins
on players.id=wins.id
order by wins desc;

create view standings as select rankings.id,name,
coalesce(wins,0) as wins,
coalesce(loses,0) as loses
from rankings left join loses
on rankings.id=loses.id
order by wins desc;
