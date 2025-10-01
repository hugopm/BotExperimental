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
    FINALE = 1352376440078860368 # 2025

@dataclass
class Contest:
    NB_PROBLEMS = 4
    ABC = "A+B+C+D"
    EXEMPLE = "100+25+33+15"
    NOM_EPREUVE = "épreuve 3"
    MESSAGE = (
        "{user_mention}, avez vous bien fini les **trois épreuves** de sélection (l'épreuve 1, l'épreuve 2 **et** l'épreuve 3) pour le stage de la Toussaint ? "
        "Tout abus pourra entraîner une disqualification."
    )

@dataclass
class cfg:
    GUILD_ID = 696724725279359097
    channels = Channels()
    roles = Roles()
    contest = Contest()
    lock_msg = None
