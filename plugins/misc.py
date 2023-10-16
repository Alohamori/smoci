from datasette import hookimpl
from markupsafe import Markup
import json, re

GLYPHS = 'αβγδεζ𓇌𓃭𓎛𓆑𓈗𓂀'
SEARCH = 'albegadeepzereliflviwaey'
NOVELTIES = {'picture': '🖼', 'music': '𝄞'}
WORDS = 'alpha beta gamma delta epsilon zeta reeds lion flax viper water eye'.split(' ')

with open('contestants') as f:
    CONTESTANTS = f.read().splitlines()
with open('ocdb_slugs') as f:
    OCDB_SLUGS = f.read().splitlines()

def expand_tags(s):
    s = s.replace('<fg', '<span style=color').replace('/fg', '/span')
    s = s.replace('<bg', '<span class=bg style=;background-color').replace('/bg', '/span')
    s = s.replace('<face:', '<span style=font-family:')
    s = s.replace('<x', '<span class=x').replace('/x', '/span')
    s = re.sub('<rot:(\d+)', r'<span style=display:inline-block;transform:rotate(\1deg)', s)
    s = re.sub('<(small|big|huge)', r'<span class=\1', s)
    s = re.sub('/(small|big|huge|rot)', '/span', s)
    return s

def get_value(row, column):
    v = row[column]
    return v if type(v) == int else v['value']

async def play_desc(base, db, kind, target):
    if kind < 3:
        res = await db.execute('select connection from connequences where id=?', [target])
        connection = res.first()['connection']
        msg = ('stumped by', 'answered', 'missed')[kind]
        return Markup(f'{msg} <a href="{base}/connequences/{target}">{connection}</a>')
    elif kind in (6, 7, 8):
        res = await db.execute('select clue from vowel_clues where id=?', [target])
        clue = res.first()['clue']
        msg = ('missed', 'solved', 'stumped by')[kind - 6]
        return Markup(f'{msg} <a href="{base}/vowel_clues/{target}">{clue}</a>')
    elif kind == 5:
        return Markup(f'<a href="{base}/wall_groups?wall={target}">wall</a> bonus')
    else:
        fi, n = kind // 10, kind % 10
        msg = ('found', 'identified')[fi - 3]
        gs = 'group' if n == 1 else 'groups'
        return Markup(f'{msg} <a href="{base}/wall_groups?wall={target}&{msg}=1">{n} {gs}</a>')

@hookimpl(trylast=True)
async def render_cell(datasette, database, table, row, column, value):
    BASE = datasette.setting("base_url") + 'only-connect'

    if column == 'kind':
        return '🧩' if value == 'connection' else '🔢'

    if column == 'glyph':
        glyph = GLYPHS[SEARCH.index(value[0:2]) // 2]
        return Markup(f'<span class="glyph">{glyph}</span>')

    if column in ('connection', 'solution'):
        if not value:
            return Markup('<em>UNBROADCAST</em>')
        return Markup(f'<span class="spoiler">{value}</span>')

    if column == '!':
        if not value:
            return

        nv = NOVELTIES[value]
        slug = OCDB_SLUGS[get_value(row, 'match')]
        if slug:
            kind = 'conn' if row['kind'] == 'connection' else 'seq'
            i = WORDS.index(row['glyph']) % 6 + 1
            return Markup(f'<a href="https://ocdb.cc/episode/{slug}#{kind}_{i}" target="_blank">{nv}</a>')
        else:
            return nv

    wr = ('wrong', 'right')
    vcbc = BASE + '/vowel_clues_by_contestant?contestant={}&right={}'

    if column in wr and type(value) == str:
        if value == '[]':
            return ' '
        right = wr.index(column)
        links = [f'<a href="{vcbc.format(i, right)}">{CONTESTANTS[i]}</a>'
                 for i in json.loads(value)]
        return Markup('<br>'.join(links))

    if column == 'broadcast':
        short = value.split(' ')[0]
        return Markup(f'<abbr title="{value}">{short}</abbr>')

    if column == 'PG':
        return Markup(f'<a href="https://puzzgrid.com/grid/{value}" target="_blank">▶</a>')

    if table == 'round_scores' and column == 'round':
        match = get_value(row, 'match')
        team = get_value(row, 'team')

        if value < 3:
            kind = ('connection', 'sequence')[value - 1]
            query = f'connequences?match={match}&kind={kind}&team={team}'
        elif value == 3:
            db = datasette.get_database('only-connect')
            res = await db.execute('select id from walls where match=? and team=? limit 1', [match, team])
            wid = res.first()['id']
            query = f'wall_groups?wall={wid}'
        else:
            query = f'vowel_clues?match={match}'
        return Markup(f'<a href="{BASE}/{query}">{value}</a>')

    if column == 'size':
        return Markup(f'<a href="{BASE}/vowel_clues?set={row["id"]}">{value}</a>')

    if column == 'for':
        return Markup(value)

    if column == 'play':
        db = datasette.get_database('only-connect')
        kind, play = json.loads(value)
        return await play_desc(BASE, db, kind, play)

    if table == 'play_by_play' and column == 'LC':
        return '✓' if value else ' '

    if column != 'clues' or not value:
        return None

    clues = json.loads(value)
    if value.find('<') != -1:
        clues = [expand_tags(c) for c in clues]

    if table == 'connequences' and row['kind'] == 'sequence':
        clues[-1] = f'<span class="spoiler">{clues[-1]}</span>'
    wrapped = ''.join(f'<div>{clue}</div>' for clue in clues)
    html = f'<div class="clues">{wrapped}</div>'
    return Markup(html)

@hookimpl
def table_actions(datasette, table):
    acts = []
    tables = datasette.metadata('databases')['only-connect']['tables']

    if table in tables and 'columns' in tables[table]:
        acts.append({'href': f'javascript:toggle_notes("{table}");', 'label': 'Toggle column notes'})

    if table in ('connequences', 'wall_groups', 'vowel_clues'):
        acts.append({'href': 'javascript:toggle_spoilers();', 'label': 'Toggle spoilers (globally)'})

    return acts

@hookimpl
def extra_js_urls(table, view_name):
    if not table and view_name in ('database', 'table'):
        return ['https://cdn.jsdelivr.net/gh/tofsjonas/sortable@latest/sortable.min.js']

@hookimpl
def extra_template_vars(table, columns, request):
    def ctype(v):
        s = str(v)
        if all(c.isdigit() or c == '.' or c == '-' for c in s):
            return 'float' if '.' in s else 'int'
        return 'str'

    return {'cell_type': ctype}
