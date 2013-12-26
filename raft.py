#!/usr/bin/env python


"""
Log Structure

index ------> 1       2       3       4
           /-----\ /-----\ /-----\ /-----\
term ----> |  1  | |  1  | |  1  | |  2  |
command -> | add | | cmp | | ret | | mov |
           \-----/ \-----/ \-----/ \-----/

Log Entry == index, term, command
Log stored on stable storage (disk); survives crashes
Entry committed if known to be stored on majority of servers
    - Durable, will eventually be executed by state machines
"""


class Log(object):

    """ Replicated Log. """


class LogEntry(object):

    """ Log Entry. """

    index = None
    term = None
    command = None


"""
Terms:
      Term 1       Term 2      Term 3       Term 4       Term 5
    [   |   ]  [  |        ]  [      ]  [  |        ] [ |       ]
     ^    ^     ^   ^            ^       ^       ^     ^     ^
     |    |     |   |            |       |       |     |     |
     |    |     |   |       split vote   |       |     |     |
     |    |     |   |                    |       |     |     |
     \----------+-----------+------------+-------------/     |
          |         |       |                    |           |
          |         |    elections               |           |
          |         |                            |           |
          \---------+-------------+--------------+-----------/
                                  |
                            normal operation

    Time divided into terms:
        election
        normal operation under a single leader

    At most 1 leader per term

    Some terms have no leader (failed election)

    Each server maintains 'current term' value

    Key role of terms: identify obsolete information (out of date servers)
"""


class Term(object):

    """ Term. """

    term = None


class LeaderlessTerm(Term):

    """ Leaderless Term. """

"""
Election

Increment current term

Change to Candidate state

Vote for self

Send RequestVote RPCs to all other servers, retry until either:
    1. Receive votes from majority of servers
        a. Become leader
        b. Send AppendEntries heartbeats to all other servers

    2. Receive RPC from valid leader:
        a. Return to Follower state (step down)

    3. No-one wins election (election timeout elapses) (ie split vote):
        a. Increment term, start new election

Safety: allow at most one winner per term
    Each server gives out only one vote per term (persist on disk)
        - Refuse to give out more than one per election
    Two different Candidates can't accumulate majorities in same term

Liveness: some Candidate must eventually win
    T == electionTimeout
    Choose elections timeouts randomly in [2, 2T]
    One server usually times out and wins election before others wake up
    Works well if T >> broadcast time

"""


class ElectionTerm(LeaderlessTerm):

    """ Term currently undergoing an election. """


class SplitTerm(LeaderlessTerm):

    """ Term that had a split vote between leaders. """


class LeaderTerm(Term):

    """ Term with an elected leader. """

    leader = None


"""
Normal operation: 1 leader, N-1 followers

                         timeout, new election
                               ^  |
Start        timeout, start    |  |   receive votes from
|               election       |  \/  majority of servers
\-> Follower -------------> Candidate ------------------> Leader
    ^ step ^                ^                              |
    | down |                |                              |
    |      \----------------/                              |
    |                                                      |
    \------------------------------------------------------/

dicover current term                                    discover server
or higher term                                          with higher term


1. Client sends command to Leader
2. Leader appends command to it's Log
3. Leader sends AppendEntries RPCs to followers
4. Once new entry committed:
    a. Leader passes command to it's state machine, returns result
    to client
    b. Leader notifies followers of committed entries in subsequent
    AppendEntries RPCs
    c. Followers pass committed commands to their state machines
X. Crashed/slow followers?
    a. Leader retires RPCs until they succeed
X. Performance is optimal in common case:
    a. One successful RPC to any majority of servers
"""


"""
Servers start up as followers.

Followers expect to receive RPCs from leaders or candidates

Leaders must send heartbeats (empty AppendEntries RPCs) to maintain authority

If electionTimeout elapses with no RPCs:
    Follower assumes leader has crashed
    Follower starts new election
    Timeouts typically 100-500ms
"""


class RaftBase(object):

    """ Raft Base object. """


class Follower(RaftBase):

    """ Completely passive (issues no RPCs, responds to incoming RPCs). """


class Candidate(RaftBase):

    """ Used to elect a new leader. """


class Leader(RaftBase):

    """ Handles all client interactions, log replication. """
