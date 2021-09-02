from typing import Counter
from lib.api_high import API_High
from lib.database import db

form = """
appver	1.4.2
ver	00000001
npsn	19820000007725193
adid	750e3bc5-899d-4ed8-bb48-a024414ddb48
countryname	DE
devicename	SM-G970N
deviceid	750e3bc5-899d-4ed8-bb48-a024414ddb48
osname	Android OS 5.1.1 / API-22 (LMY49I/V9.5.3.0.LACCNFA)
"""
items = dict(line.split("\t") for line in form.split("\n") if line)

a = API_High(**items)
a.login(
    uuid = "19820000007725193TB5zW20Fa1Pa2r560K0PCa2s01g1750e3bc5-899d-4ed8-bb48-a024414ddb48aabb2e8d51335c794511b02dc38835b60238",
    nptoken="TOUkfnuUeQcy0SiS9y90ssLAPrTYTvxgiY81SIxwjEY6PyeRwj8tZoNCro",
    npaCode="0MS05L910506T"
)
a.join_in('d325d1123c2b04dc4db3a17d03825f77', 979987865923, "2021082700005")
for id in db.huntingquest_stage.keys():
    a.quest(id)