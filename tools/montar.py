"""Monta data.json (dados públicos do site) a partir das listagens do banco do Painel GECIRA.

Uso: python3 -I tools/montar.py <pasta-de-entrada> <arquivo-de-saida> <AAAA-MM-DDTHH:MM>

A pasta de entrada tem um arquivo por coleção, com as linhas que db_list devolve
(um objeto JSON por linha, com "id" e "data"): members.jsonl, events.jsonl,
goals.jsonl, entries.jsonl, unipex.jsonl, pedidos.jsonl. E também config.json,
importador.json e alterado.json, cada um com o objeto "data" do documento
(ou {} se o documento não existir).

O que NÃO vai para o site: cobranças, contatos, avisos, envios, fotos enviadas
pelo painel, o campo "by" (id de quem gravou), pedidos excluídos e os campos de
WhatsApp e e-mail da configuração.
"""
import json, os, sys

PUBLIC = ['members', 'events', 'goals', 'entries', 'unipex', 'pedidos']
CONFIG_DROP = {'whatsapp', 'waSectors', 'emailOn'}


def load_jsonl(path):
    out = {}
    if not os.path.exists(path):
        return out
    for n, line in enumerate(open(path, encoding='utf-8'), 1):
        line = line.strip()
        if not line or not line.startswith('{'):
            continue
        obj = json.loads(line)
        if 'id' not in obj or not isinstance(obj.get('data'), dict):
            raise SystemExit('linha %d de %s sem "id" ou "data"' % (n, path))
        d = {k: v for k, v in obj['data'].items() if k != 'by'}
        out[str(obj['id'])] = d
    return out


def load_obj(path):
    if not os.path.exists(path):
        return {}
    txt = open(path, encoding='utf-8').read().strip()
    o = json.loads(txt) if txt else {}
    if isinstance(o, dict) and isinstance(o.get('data'), dict) and len(o) <= 5 and 'id' in o:
        o = o['data']
    return o if isinstance(o, dict) else {}


def main():
    src, dst, now = sys.argv[1], sys.argv[2], sys.argv[3]
    cols = {c: load_jsonl(os.path.join(src, c + '.jsonl')) for c in PUBLIC}
    cols['pedidos'] = {k: v for k, v in cols['pedidos'].items() if v.get('status') != 'excluido'}
    if not cols['members']:
        raise SystemExit('members vazio: nada foi gravado')
    for k, m in cols['members'].items():
        if not m.get('name'):
            raise SystemExit('membro sem nome: ' + k)
    cfg = {k: v for k, v in load_obj(os.path.join(src, 'config.json')).items() if k not in CONFIG_DROP}
    imp = load_obj(os.path.join(src, 'importador.json'))
    alt = load_obj(os.path.join(src, 'alterado.json'))
    data = {
        'exportedAt': now,
        'source': {'alteradoAt': alt.get('at', ''), 'importadorRows': imp.get('rows', None)},
        'collections': cols,
        'docs': {'config/main': cfg, 'status/importador': imp},
    }
    tmp = dst + '.tmp'
    json.dump(data, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, dst)
    print('ok:', ', '.join('%s %d' % (c, len(cols[c])) for c in PUBLIC))


if __name__ == '__main__':
    main()
