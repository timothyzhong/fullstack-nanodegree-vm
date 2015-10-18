#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("delete from matches;")
    conn.commit()
    conn.close()


def deletePlayers():
    """Remove all the player records from the database."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("delete from players;")
    conn.commit()
    conn.close()


def countPlayers():
    """Returns the number of players currently registered."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("select count(*) from players;")
    result = cursor.fetchone()
    count = result[0]
    conn.close()
    return count


def registerPlayer(name):
    """Adds a player to the tournament database.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
      name: the player's full name (need not be unique).
    """
    conn = connect()
    cursor = conn.cursor()
    sql = "insert into players values(%s);"
    cursor.execute(sql, (name,))
    conn.commit()
    conn.close()


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a
    player tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    conn = connect()
    cursor = conn.cursor()
    sql = "select players.id,name,win,lose\
           from players left join matches\
           on players.id=matches.id\
           order by win desc,lose;"
    cursor.execute(sql)
    rows = cursor.fetchall()
    result = []
    for row in rows:
        player_id = row[0]
        name = row[1]
        wins = row[2]
        if wins is None:
            wins = 0
        loses = row[3]
        if loses is None:
            loses = 0
        matches = wins + loses
        result.append([player_id, name, wins, matches])
    return result


def reportMatch(winner, loser, draw):
    """Records the outcome of a single match between two players.
       If it's a draw game, no need to update database.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
      draw:  whether the game is draw
    """
    conn = connect()
    cursor = conn.cursor()
    # draw game
    if(draw == True):
        sqlSelect = "select win from matches where id=%s"
        sqlInsert = "insert into matches values(%s,0,0)"

        cursor.execute(sqlSelect, (winner,))
        row = cursor.fetchone()
        if(row is None):       # insert match row with (0,0) score
           cursor.execute(sqlInsert,(winner,))

        cursor.execute(sqlSelect, (loser,))
        row = cursor.fetchone()
        if(row is None):
           cursor.execute(sqlInsert,(loser,))

        conn.commit()
        conn.close() 
        return 


    # update winner
    sql = "select win from matches where id=%s"
    cursor.execute(sql, (winner,))
    row = cursor.fetchone()
    if(row is None):		# not exist
        sql = "insert into matches values(%s,1,0)"
        cursor.execute(sql, (winner,))
    else:                       # update existed row
        winCount = row[0]
        winCount += 1
        sql = "update matches set win=%s where id=%s"
        cursor.execute(sql, (winCount, winner,))

    # update loser
    sql = "select lose from matches where id=%s"
    cursor.execute(sql, (loser,))
    row = cursor.fetchone()
    if(row is None):
        sql = "insert into matches values(%s,0,1)"
        cursor.execute(sql, (loser,))
    else:
        loseCount = row[0]
        loseCount += 1
        sql = "update matches set lose=%s where id=%s"
        cursor.execute(sql, (loseCount, loser,))

    conn.commit()
    conn.close()


def swissPairings():
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    conn = connect()
    cursor = conn.cursor()

    sql = "select players.id,name,win\
          from players,matches\
          where players.id=matches.id\
          order by win desc,lose;"
    cursor.execute(sql)
    rows = cursor.fetchall()
    players = []
    for row in rows:
        players.append((row[0], row[1]))
    pairs = []
    x = 0
    while x < len(players):
        pairs.append((players[x][0], players[x][1],
                      players[x+1][0], players[x+1][1]))
        x += 2
    conn.close()
    return pairs
