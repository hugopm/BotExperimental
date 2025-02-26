from dataclasses import dataclass

@dataclass
class Channels:
    RANKING = 1063952121180979311
    DEBRIEF = 1017111913387282523

@dataclass
class Roles:
    DEBRIEF = 1154058349529268255
    RANKING = 1154058816636330024
    PARTICIPANT = 1197122920032514088

@dataclass
class Contest:
    NB_PROBLEMS = 4
    ABC = "A+B+C+D"
    EXEMPLE = "42+50+10+80"
    NOM_EPREUVE = "épreuve 3"
    MESSAGE = (
        "{user_mention}, **avez vous bien fini les trois épreuves (ouvertes le 30 janvier, le 13 février et le 26 février) ?** "
        "Tout abus pourra entraîner une disqualification."
    )

@dataclass
class cfg:
    GUILD_ID = 696724725279359097
    channels = Channels()
    roles = Roles()
    contest = Contest()
