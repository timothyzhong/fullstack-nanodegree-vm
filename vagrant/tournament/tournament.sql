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
    draw boolean,
    id serial primary key
);

create view wins as select players.id,count(*) as wins
from players,matches
where players.id=matches.win and draw=false
group by players.id; 

create view loses as select players.id,count(*) as loses
from players,matches
where players.id=matches.lose and draw=false
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
order by wins desc,loses;

create view draws as select players.id as id,
count(*) as draws
from players,matches
where (players.id=matches.win or players.id=matches.lose) and draw=true
group by players.id;

create view standingsWithDraws as select standings.id as id,
name,wins,loses,
coalesce(draws,0) as draws
from standings left join draws
on standings.id=draws.id
order by wins desc,loses;
