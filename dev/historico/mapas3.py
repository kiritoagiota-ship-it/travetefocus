"""Rascunho dos mapas novos (R=3) em blocos de 10 colunas separados por |."""

NOVAS_CORES = {
    'a': (1.00, 0.94, 0.85, 1),     # pele: luz
    't': (0.66, 0.40, 0.44, 1),     # pele: sombra profunda (quente, puxa para o vinho)
    'l': (0.98, 0.68, 0.66, 1),     # bochecha
    'i': (0.84, 0.87, 0.96, 1),     # branco do olho
    '3': (0.33, 0.43, 0.70, 1),     # iris: meio
    'U': (0.70, 0.82, 1.00, 1),     # cabelo: reflexo
    '%': (0.50, 0.58, 0.76, 1),     # couro do sobretudo: reflexo
}


def lim(m):
    out = [l.replace('|', '') for l in m]
    for i, l in enumerate(out):
        assert len(l) == len(out[0]), (i, len(l), l)
    return out


LADO = lim([
    "..........|......J...|.......J..|.........",  # 0
    "..........|.....JHJ..|......JJ..|.........",  # 1
    "........J.|...JJHIJJ.|..JJHHJ...|.........",  # 2
    ".......JHJ|JJJHHIHHHJ|JJHHHHHJJ.|.........",  # 3
    "..JJJ.JHHH|HHHHHHHHHH|HHHHHHHHHH|JJ.......",  # 4
    "..JHHJHHHH|HHHHHHHHHH|HHHHHHHHHH|HHJ......",  # 5
    "JJHHHHHHHH|HHHHHHHHHH|HHHHHHHHHH|HHHJ.....",  # 6
    "JJHHHHHHHH|HHHHIIIIHI|IIIIIHHHHH|HHHHJ....",  # 7
    "..JHHHHHHH|HIIhhhhhIh|hUUhhIIHHH|HHHHHJ...",  # 8
    "JJHHHHHHHI|IhhIIIIIHI|IIIIhhIIHH|HHHHHHJ..",  # 9
    "..JJHHHHIh|hIIHHHHHHH|HHHHIIhhIH|HHHHHHHJJ",  # 10
    "..JJHHHHHI|IHHHHHHHHH|HHHHHHIIhI|HHHHHHHJJ",  # 11
    "JJHHJJHHHH|HHHHHHHHHH|HHHHHHHHII|IIHHHHHHJ",  # 12
    "JJHHJJHHHH|HHHHHHHHHH|JHHHHHHHHH|HhIHHHHHJ",  # 13
    "..JHJJHHHH|HHHHHHHHHJ|HHHHHHHJHH|HHHHHHHHH",  # 14
    "JJHHJJHHHH|HHHHHHHHJH|HHHHHHJHHH|HHHJHHHHH",  # 15
    "..JHHHJJHH|HHHHHHHJHH|HHHHHJHHHH|HHHJHHHHH",  # 16
    "..JHHHJJHH|HHHHHHJHHH|HHHHJHHHHH|HHJHHHHHH",  # 17
    "JJHHHHJJHH|HHHHHJHHHH|HHHHJHIIHH|HHJHHHHHH",  # 18
    "JJHHHHJJHH|HHHHJHHHHH|HHHJHIIHHH|HHJHHHHHH",  # 19
    "JJHHHHHHJH|HHHHssHHHS|SsssJHHHss|ssssssHHs",  # 20
    "JJHHHHHHHH|HHHHssHHss|EEEEEEHHss|SEEESSHHH",  # 21
    "JJHHHHHHHH|HHHHsSSSSE|eeEEnnSSSS|SeEnSSSSs",  # 22
    ".JHHHHHHHH|HHHsSSSSSS|e3EEn3SSSS|S3EeSSSSs",  # 23
    "..JJHHHHHH|HHssSSSSSS|33mmm3SSSS|S3m3SSSss",  # 24
    "..JJHHHHHH|HHssSSSSSS|SmmmmSSSSS|SmmSSSSss",  # 25
    "...JHHHHHH|HHsSSSSSSS|SssssSSSSS|SSSSSSssS",  # 26
    "...JHHHHHH|HsSSSSSSSS|SSSSSSSSSS|SSSsSS...",  # 27
    "....JJHHHH|ssSSSSSSSS|SSSSSSSSss|ssSSS....",  # 28
    "....JJHHHH|HsSSSSSSSS|SSSSSSSSSs|sSSS.....",  # 29
    "......JHHH|HHssSSSSSS|SSSSSSSSSS|Ss.......",  # 30
    ".......JHH|HHssSSSSSS|SSSSSSSSSS|SS.......",  # 31
    ".........J|HHHHssssSS|SSSSSSss..|.........",  # 32
])

FRENTE = lim([
    "..........|.....J....|.....J....|.........",  # 0
    "..........|....JHJ...|....JHJ...|.........",  # 1
    "..........|..JJHIHJJ.|..JJHIHJJ.|.........",  # 2
    "..........|.JHHHIHHHJ|JJHHHIHHHJ|J........",  # 3
    ".......JJJ|HHHHHHHHHH|HHHHHHHHHH|HJJ......",  # 4
    "......JHHH|HHHHHHHHHH|HHHHHHHHHH|HHHJ.....",  # 5
    "....JJHHHH|HHHHHHIIII|IIIIIHHHHH|HHHHJJ...",  # 6
    "....JHHHHH|HHHIIIhhhh|hUUhhIIIHH|HHHHHJ...",  # 7
    "...JHHHHHH|HIIhhhIIII|IIIIhhhIIH|HHHHHHJ..",  # 8
    "...JHHHHHI|IhhIIHHHHH|HHHHHIIhhI|IHHHHHJJ.",  # 9
    "..JJHHHHHI|hIHHHHHHHH|HHHHHHHHIh|IHHHHHHJJ",  # 10
    "..JJHHHHHH|IHHHHHHHHH|HHHHHHHHHI|HHHHHHHJJ",  # 11
    "..JHHHHHHH|HHHHJHHHHH|HHHJHHHHHH|HHHHHHHHJ",  # 12
    "..JHHHHHHH|HHHHJHHHHH|HHHJHHHHHH|HHHHHHHHJ",  # 13
    "..JHHHHHHH|HHHJHHHHHJ|HHHHJHHHHH|HHIIHHHHJ",  # 14
    "..JHHHHHHH|HHHJHHHHHJ|HHHHJHHHHH|HHhIHHHHJ",  # 15
    "..JHHHHHHH|HHJHHHHHJH|JHHHHJHHHH|HHHHHHHHJ",  # 16
    "..JHHHHHHH|HHJHHHHHJH|JHHHHJHHHH|HHHHHHHHJ",  # 17
    "..JHHHHHHH|sJHHHHHJsH|sJHHHHJHHH|sHHHHHHHJ",  # 18
    "..JHHHHHHJ|sJHHHHHJss|sJHHHHJHHs|sHHHHHHHJ",  # 19
    "..JHHHHsSS|sJHHHHJsSS|SsJHHJssSS|SsHHHHHHJ",  # 20
    "..JHHHssSs|EEEEEEsSSS|SSSsEEEEEE|sSSsHHHHJ",  # 21
    "..JHHHssSS|eeEEnnSSSS|SSSSnnEEee|SSSsHHHHJ",  # 22
    "..JHHHssSS|e3EEn3SSSS|SSSS3nEE3e|SSSsHHHJJ",  # 23
    "..JJHHssSS|33mmm3SSSS|SSSS3mmm33|SSSsHHJJ.",  # 24
    "..JJHHssSS|SmmmmSSSSS|SSSSSmmmmS|SSSsHHJJ.",  # 25
    "...JHHssSS|SSssSSSSSS|sSSSSSssSS|SSssHHJ..",  # 26
    "...JHHHsSS|SSSSSSSSSS|SSSSSSSSSS|SSssHJ...",  # 27
    "....JJHHsS|SSSSSSSSSs|ssSSSSSSSS|SSsJJ....",  # 28
    "....JJHHss|SSSSSSSSSS|SSSSSSSSSS|SsJJ.....",  # 29
    "......JHss|SSSSSSSSSS|SSSSSSSSSS|ssJ......",  # 30
    ".......JHs|SSSSSSSSSS|SSSSSSSSSS|ss.......",  # 31
    ".........J|HHssssSSSS|SSSSssssJJ|.........",  # 32
])

COSTAS = lim([
    "..........|.....J....|.....J....|.........",  # 0
    "..........|....JHJ...|....JHJ...|.........",  # 1
    "..........|..JJHIHJJ.|..JJHIHJJ.|.........",  # 2
    "..........|.JHHHIHHHJ|JJHHHIHHHJ|J........",  # 3
    ".......JJJ|HHHHHHHHHH|HHHHHHHHHH|HJJ......",  # 4
    "......JHHH|HHHHHHHHHH|HHHHHHHHHH|HHHJ.....",  # 5
    "....JJHHHH|HHHHHHIIII|IIIIIHHHHH|HHHHJJ...",  # 6
    "....JHHHHH|HHHIIIhhhh|hUUhhIIIHH|HHHHHJ...",  # 7
    "...JHHHHHH|HIIhhhIIII|IIIIhhhIIH|HHHHHHJ..",  # 8
    "...JHHHHHI|IhhIIHHHHH|HHHHHIIhhI|IHHHHHJJ.",  # 9
    "..JJHHHHHI|hIHHHHHHHH|HHHHHHHHIh|IHHHHHHJJ",  # 10
    "..JJHHHHHH|IHHHHHHHHH|HHHHHHHHHI|HHHHHHHJJ",  # 11
    "..JHHHHHJH|HHHHHHHHJJ|HHHHHHHHJJ|HHHHHHHHJ",  # 12
    "..JHHHHHJH|HHHHHHHHJH|HHHHHHHHJH|HHHHHHHHJ",  # 13
    "..JHHHHHJJ|HHHHHHHHJH|HHHHHHHJHH|HHIHHHHHJ",  # 14
    "..JHHHHHIJ|HHHHHHHHJH|HHHHHHHJHH|HHhIHHHHJ",  # 15
    "..JHHHHHHJ|HHHHHHHHHJ|HHHHHHJHHH|HHHHHHHHJ",  # 16
    "..JHHHHHHJ|JHHHHHHHHJ|HHHHHJIHHH|HHHHHHHJJ",  # 17
    "ssJHHHHHHI|JJHHHHHHHJ|HHHHHJHHHH|HHHHHHJJs",  # 18
    "ssJHHHHHHH|IJHHHHHHHJ|HHHHJHHHHH|HHHHHHJJs",  # 19
    "ssJHHHHHHH|HJHHHHHHHJ|HHHHJHHHHH|HHHHHHJJs",  # 20
    "..JHHHHHHH|HJHHHHHHHI|JHHHJHHHHH|HHHHHHJJ.",  # 21
    "..JHHHHHHH|JHHHHHHHHH|JHHHJHHHHH|HHHHHHJJ.",  # 22
    "..JJHHHHHH|JHHHHHHHHH|JHHHJHHHHH|HHHHHHJ..",  # 23
    "..JJHHHHHJ|HHHHHHHHHH|JHHHJHHHHH|HHHHJJ...",  # 24
    "...JHHHHHJ|HHHHHHHHHJ|HHHHHJHHHH|HHHHJJ...",  # 25
    "....HHHHJH|HHHHHHHHJH|HHHHHHJHHH|HHJJ.....",  # 26
    "....JJHHJH|HHJJHHHJHH|HHJJHHJHHH|JJJJ.....",  # 27
    "......JHHH|..JJHHtSSS|StHHHHJ.JH|HHJ......",  # 28
    "......JHHH|..JJHHsSSS|SsHHHH...J|HH.......",  # 29
    ".........J|....HHsSSS|SsHHJJ....|.........",  # 30
    ".........J|....JHsSSS|SsHH......|.........",  # 31
    "..........|.....sSSSS|Ss........|.........",  # 32
])

TOR = lim([
    ".........2|CCCCctSSSS|StCCcccc..|.........",  # 0
    ".........2|CCCCctSSSS|StCCcccc..|.........",  # 1
    ".........2|CCCCcsSSSS|SsCCAAcc..|.........",  # 2
    ".........2|CCZZCZZZ44|4ZZZAAcc..|.........",  # 3
    ".........2|CCCZZZ4444|4ZZZAAcccc|.........",  # 4
    "........22|CCCCZZ4C44|4ZZZAAAccc|.........",  # 5
    "......222C|CCCCCCZZ44|4ZZCCCAAAA|cc.......",  # 6
    "......22CC|CCCCCCZZ44|4ZCCCCCAAA|ccc......",  # 7
    "......22CC|ccCCCCCZZ4|ZZCCCCCAAA|AAc......",  # 8
    "......22CC|ccCCCCCCZZ|ZZCCCCCAAA|AAc......",  # 9
    "......22CC|ccCCCCCCZZ|2CCCCC2AAA|AAc......",  # 10
    "......22CC|ccCCCCCCZZ|2CCCCC2AAA|AAc......",  # 11
    "......222C|ccCCCCCCZZ|2CCC22CAAA|AAc......",  # 12
    "......222C|ccCCCCCCZZ|2CCC22CAAA|AAc......",  # 13
    ".....22CCC|ccCCCCCCZZ|2C22CCCCAA|AAcc.....",  # 14
    "....22CCCC|ccCCCCCCZZ|2C22CCCCAA|AAccc....",  # 15
    "...22CCCCC|ccCCCCCCZZ|2CCC22CCAA|AAAccc...",  # 16
    "...22CCCCC|ccCCCCCCZZ|2CCC22CCAA|AAAccc...",  # 17
    "...2MKMMMM|MMMMMgGkkk|GgMMMMMMKM|MMMMcc...",  # 18
    "...2MgMMMM|MMMMMgK++k|KgMMMMMMgM|MMMMcc...",  # 19
    "...222MKMM|MMMMMgGkkk|GgMMMMMMKM|MMMMcc...",  # 20
    "...222CCCC|CCCCCPPPPP|PPPPCCCCCC|AAAccc...",  # 21
    "...222CCCC|CCCCC7PPPP|PPPPCCCCCC|AAAccc...",  # 22
    "...222CCCC|CCCCC7PPPP|PPP7CCCCCC|AAAccc...",  # 23
])

TORC = lim([
    ".........2|CCCCCCCCCC|CCCCcccc..|.........",  # 0
    ".........2|CCCCCCCCCC|CCCCcccc..|.........",  # 1
    ".........2|CCCCCCCCCC|CCCCAAcc..|.........",  # 2
    ".........2|CCCCCCCCCZ|CCCCAAcc..|.........",  # 3
    ".........2|CCCCCCCCZZ|ZCCCAAcccc|.........",  # 4
    "........22|CCCCCCCCZZ|ZCCCAAAccc|.........",  # 5
    "......222C|CCCCCCCCZZ|ZCCCCCAAAA|cc.......",  # 6
    "......22CC|CCCCCCCCZZ|ZCCCCCCAAA|ccc......",  # 7
    "......22CC|ccCCCCCCZZ|ZCCCCCCAAA|AAc......",  # 8
    "......22CC|ccCCCCCCZZ|ZCCCCCCAAA|AAc......",  # 9
    "......22CC|ccCCC2CCZZ|ZC22CCCAAA|AAc......",  # 10
    "......22CC|ccCCC2CCZZ|ZC22CCCAAA|AAc......",  # 11
    "......222C|ccCC2CCCZZ|ZCCC22CAAA|AAc......",  # 12
    "......222C|ccCC2CCCZZ|ZCCC22CAAA|AAc......",  # 13
    ".....22CCC|ccCCCCCCZZ|ZCCCCCCCAA|AAcc.....",  # 14
    "....22CCCC|ccCCCCCCZZ|ZCCCCCCCAA|AAccc....",  # 15
    "...22CCCCC|ccCCCCCCZZ|ZCCCCCCCAA|AAAccc...",  # 16
    "...22CCCCC|ccCCCCCCZZ|ZCCCCCCCAA|AAAccc...",  # 17
    "...2MKMMMM|MMMMMMMKMM|MMMMMMMMKM|MMMMcc...",  # 18
    "...2MgMMMM|MMMMMMMgMM|MMMMMMMMgM|MMMMcc...",  # 19
    "...222MKMM|MMMMMMMKMM|MMMMMMMMKM|MMMMcc...",  # 20
    "...222CCCC|CCCCCCCCCC|CCCCCCCCCC|AAAccc...",  # 21
    "...222CCCC|CCCCCCCCCC|CCCCCCCCCC|AAAccc...",  # 22
    "...222CCCC|CCCCCCCCCC|CCCCCCCCCC|AAAccc...",  # 23
])
