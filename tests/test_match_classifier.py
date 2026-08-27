from match_classifier import (
    classify,
    clan_is_winner,
    extract_clan_teammates,
    is_ranked_game,
    is_training_game,
    set_teams,
)
from models import ConfigPlayer, Match, Member, Profile, Team, TeamMatch


def make_member(profile_id, outcome=0, teamid=0, alias="player"):
    return Member(
        profile=Profile(id=profile_id, name=alias, alias=alias, personal_statgroup_id=1, xp=0, country="fr"),
        civilization_id=1,
        newrating=1000,
        oldrating=1000,
        outcome=outcome,
        teamid=teamid,
        replay_link=f"https://aoe.ms/replay/?gameId=1&profileId={profile_id}",
    )


def make_match(members, matchtype_id=6, mapname="arabia.rms"):
    return Match(
        id=1,
        mapname=mapname,
        matchtype_id=matchtype_id,
        description="",
        startgametime=0,
        completiontime=0,
        insights_link="https://www.aoe2insights.com/match/1/",
        members=members,
    )


def test_is_ranked_game_true_for_ranked_matchtype():
    assert is_ranked_game(6) is True


def test_is_ranked_game_true_for_unranked_matchtype_due_to_substring_match():
    # Pre-existing quirk, not something this pass fixes: Gametypes[0] is the
    # string "Unranked", and "ranked" is a substring of "unranked", so this
    # matchtype_id is (incorrectly) classified as ranked.
    assert is_ranked_game(0) is True


def test_is_ranked_game_false_for_unknown_matchtype():
    assert is_ranked_game(99999) is False


def test_is_training_game_when_all_members_are_teammates():
    members = [make_member(1), make_member(2)]
    teams = [Team(number=0, members=members)]
    assert is_training_game(teams, members, members) is True


def test_is_training_game_false_for_real_2v2():
    player = make_member(1, teamid=0)
    opponent = make_member(2, teamid=1)
    teammates = [player]
    members = [player, opponent]
    teams = [Team(number=0, members=[player]), Team(number=1, members=[opponent])]
    assert is_training_game(teams, teammates, members) is False


def test_extract_clan_teammates_only_when_two_teams():
    clan_players = [ConfigPlayer(name="me", profileId=1, steamId=1)]
    member = make_member(1)
    match = TeamMatch(
        match=make_match([member]),
        teams=[Team(number=0, members=[member]), Team(number=1, members=[])],
    )
    assert extract_clan_teammates(match, clan_players) == [member]


def test_extract_clan_teammates_empty_when_not_two_teams():
    clan_players = [ConfigPlayer(name="me", profileId=1, steamId=1)]
    member = make_member(1)
    match = TeamMatch(match=make_match([member]), teams=[Team(number=0, members=[member])])
    assert extract_clan_teammates(match, clan_players) == []


def test_clan_is_winner_true_when_a_teammate_won():
    teammates = [make_member(1, outcome=1)]
    assert clan_is_winner(teammates, is_training=False) is True


def test_clan_is_winner_false_when_training():
    teammates = [make_member(1, outcome=1)]
    assert clan_is_winner(teammates, is_training=True) is False


def test_clan_is_winner_false_when_no_teammate_won():
    teammates = [make_member(1, outcome=0)]
    assert clan_is_winner(teammates, is_training=False) is False


def test_set_teams_groups_and_sorts_by_team_number():
    members = [make_member(1, teamid=1), make_member(2, teamid=0), make_member(3, teamid=1)]
    teams = set_teams(members)
    assert [t.number for t in teams] == [0, 1]
    assert len(teams[1].members) == 2


def test_classify_bundles_all_fields_for_a_real_1v1_victory():
    player = make_member(1, outcome=1, teamid=0)
    opponent = make_member(2, outcome=0, teamid=1)
    clan_players = [ConfigPlayer(name="me", profileId=1, steamId=1)]
    team_match = TeamMatch(
        match=make_match([player, opponent], matchtype_id=6),
        teams=[Team(number=0, members=[player]), Team(number=1, members=[opponent])],
    )

    result = classify(team_match, clan_players)

    assert result.teammates == [player]
    assert result.is_ranked is True
    assert result.is_training is False
    assert result.is_victory is True
