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
    NB_PROBLEMS = 3
    ABC = "arrayser+flooding+treedash"
    EXEMPLE = "42+50+10"
    NOM_EPREUVE = "FARIO"
    MESSAGE = (
        "{user_mention}, avez vous bien fini toutes les épreuves (ouvertes le 30 janvier, le 13 février et le 26 février) ainsi que le FARIO (le 9 mars) ? "
        "Tout abus pourra entraîner une disqualification."
    )

@dataclass
class cfg:
    GUILD_ID = 696724725279359097
    channels = Channels()
    roles = Roles()
    contest = Contest()
    lock_msg = None
