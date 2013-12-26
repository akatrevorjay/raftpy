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

"""
Log Consistency

High level of coherency between logs:
    If log entries on different servers have same index and term:
        They store the same command
        The logs are identical in all preceding entries

        TODO ASCII ART

    If a given entry is committed, all preceding entries are also committed
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

    def append_entries(self, sender, prev_index=None, prev_term=None, entry=None):
        """ AppendEntries RPC call.

        If no data is provided, consider it a heartbeat from the sender, but still
        perform consistency checks and reject or pass as allowed.

        Each AppendEntries RPC contains index, term of entry preceding new ones.
        Follower must contain matching previous entry; otherwise it rejects request.
        Implements an induction step, ensures coherency.
        """

        # TODO Consistency checks

        if not prev_index or not prev_term or not entry:
            self.heartbeat(sender)

        # TODO

    def heartbeat(self, sender):
        pass


class Candidate(RaftBase):

    """ Used to elect a new leader. """


"""
Leader Changes

At beginning of new leader's term:
    Old leader may have left entries partially replicated
    No special steps by new leader: just start normal operation
    Leader's log is "the truth"
    Will eventually make follower's logs identical to leader's
    Multiple crashes can leave many extraneous log entries

    TODO ASCII ART
"""


"""
Safety Requirement

Once a log entry has neen applied to a state machine, no other state machine
must apply a different value for that log entry.

Raft safety property:
    If a leader has decided that a log entry is committed, that entry will be
    present in the logs of all future leaders.

This guarantees the safety requirement:
    Leaders never overwrite entries in their logs
    Only entries in the leader's log can be committed
    Entries must be committed before applying to state machine

    Committed --------------------------> Present in future leader's logs
    ^ Restrictions on committment         ^ Restrictions on leader election

"""


"""
Picking the Best Leader

    Can't tell which entries are committed!

        TODO ASCII ART

    During elections, choose candidate with log most likely to contain all
    committed entries

        - Candidates include log info in RequestVote RPCs (index, term of last
        log entry)

        - Voting server V denied vote if it's log is "more complete":
            (lastTerm(V) > lastTerm(C) ||
            (lastTerm(V) == lastTerm(C) && (lastIndex(V) > lastIndex(C)

        - Leader will have "most complete" log among electing majority

"""


"""
Repairing Follower Logs

New Leader must make Follower logs consistent with it's own
    - Delete extraneous entries
    - Fill in missing entries

Leader keeps nextIndex for each Follower:
    - Index of next log entry to send to that Follower
    - Initialized to (1 + Leader's last index)

When AppendEntries consistency check fails, decrement nextIndex for Follower
and try again

    TODO ASCII ART

When Follower overwrites inconsistent entry, it deletes all subsequent entries.

    TODO ASCII ART

"""

"""
Neutralizing Old Leaders

Deposed Leaders may not be dead:
    Temporarily disconnected from network
    Other servers elect new Leader
    Old Leader becomes reconnected, attempts to commit log entries

Terms used to detect stale Leaders (and Candidates):
    Every RPC contains Term of sender

    If Sender's Term is older, RPC is rejected, sender reverts to Follower and
    updates it's Term

Election updates Terms of majority of servers
    Deposed server cannot commit new log entries
"""


class Leader(RaftBase):

    """ Handles all client interactions, log replication.

    Sends empty AppendEntries heartbeats to all followers.
    """
