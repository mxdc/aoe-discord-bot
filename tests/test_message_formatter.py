from message_formatter import MatchPresentation, MessageFormatter
from models import Member, Profile, Team, Translations


def make_translations(**overrides):
    defaults = dict(
        match_results="Match results.",
        victory_plural="{players} are victorious.",
        victory_singular="{player} is victorious.",
        defeat_plural="{players} have been defeated.",
        defeat_singular="{player} has been defeated.",
        players_separator=", ",
        players_last_separator=" and ",
        versus_short="vs",
        versus_long="*Versus*",
        team_label="*Team {number}*",
        ranked="Ranked ",
        unranked="Unranked ",
        view_match_details="[View match details]({link})",
        download_replay="[Download replay]({link})",
        emoji_crown=":crown:",
        emoji_flag=":flag_{country}:",
        emoji_globe=":globe_with_meridians:",
    )
    defaults.update(overrides)
    return Translations(**defaults)


def make_member(alias, outcome=0, country="fr"):
    return Member(
        profile=Profile(id=1, name=alias, alias=alias, personal_statgroup_id=1, xp=0, country=country),
        civilization_id=1,
        newrating=1000,
        oldrating=1000,
        outcome=outcome,
        teamid=0,
        replay_link="https://aoe.ms/replay/?gameId=1&profileId=1",
    )


def test_generate_message_returns_match_results_when_training():
    match = MatchPresentation(
        teams=[], teammates=[], mapname="arabia.rms",
        is_ranked=True, is_training=True, is_victory=False,
    )
    formatter = MessageFormatter(match, make_translations())
    assert formatter.generate_message() == "Match results."


def test_generate_message_victory_singular():
    teammate = make_member("TheViper")
    match = MatchPresentation(
        teams=[], teammates=[teammate], mapname="arabia.rms",
        is_ranked=True, is_training=False, is_victory=True,
    )
    formatter = MessageFormatter(match, make_translations())
    assert formatter.generate_message() == "Theviper is victorious."


def test_generate_message_defeat_plural():
    teammates = [make_member("TheViper"), make_member("Hera")]
    match = MatchPresentation(
        teams=[], teammates=teammates, mapname="arabia.rms",
        is_ranked=True, is_training=False, is_victory=False,
    )
    formatter = MessageFormatter(match, make_translations())
    assert formatter.generate_message() == "Theviper and Hera have been defeated."


def test_generate_embed_1v1_is_inline():
    player1 = make_member("TheViper", outcome=1)
    player2 = make_member("Hera", outcome=0)
    teams = [Team(number=0, members=[player1]), Team(number=1, members=[player2])]
    match = MatchPresentation(
        teams=teams, teammates=[player1], mapname="arabia.rms",
        is_ranked=True, is_training=False, is_victory=True,
    )
    formatter = MessageFormatter(match, make_translations())
    embed = formatter.generate_embed()
    assert len(embed.fields) == 1
    assert "vs" in embed.fields[0].value


def test_generate_embed_multiline_for_more_than_two_teams():
    player1 = make_member("TheViper")
    player2 = make_member("Hera")
    player3 = make_member("MbL")
    teams = [
        Team(number=0, members=[player1]),
        Team(number=1, members=[player2]),
        Team(number=2, members=[player3]),
    ]
    match = MatchPresentation(
        teams=teams, teammates=[player1], mapname="arabia.rms",
        is_ranked=True, is_training=False, is_victory=True,
    )
    formatter = MessageFormatter(match, make_translations())
    embed = formatter.generate_embed()
    assert len(embed.fields) == 1
    assert embed.fields[0].name == ''


def test_generate_embed_includes_links_when_present():
    player1 = make_member("TheViper", outcome=1)
    player2 = make_member("Hera", outcome=0)
    teams = [Team(number=0, members=[player1]), Team(number=1, members=[player2])]
    match = MatchPresentation(
        teams=teams, teammates=[player1], mapname="arabia.rms",
        is_ranked=True, is_training=False, is_victory=True,
        insights_link="https://www.aoe2insights.com/match/1/",
        record_link="https://aoe.ms/replay/?gameId=1&profileId=1",
    )
    formatter = MessageFormatter(match, make_translations())
    embed = formatter.generate_embed()
    # one field for the inline vs description, one for the links
    assert len(embed.fields) == 2
    assert "aoe2insights" in embed.fields[1].value
    assert "aoe.ms/replay" in embed.fields[1].value


def test_generate_embed_omits_links_field_when_absent():
    player1 = make_member("TheViper", outcome=1)
    player2 = make_member("Hera", outcome=0)
    teams = [Team(number=0, members=[player1]), Team(number=1, members=[player2])]
    match = MatchPresentation(
        teams=teams, teammates=[player1], mapname="arabia.rms",
        is_ranked=True, is_training=False, is_victory=True,
    )
    formatter = MessageFormatter(match, make_translations())
    embed = formatter.generate_embed()
    assert len(embed.fields) == 1
