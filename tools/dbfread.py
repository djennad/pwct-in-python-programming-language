"""Minimal FoxPro DBF + FPT reader for inspecting PWCT source (scx/vcx/ssf/dbf)."""
import os
import struct
import sys


def find_memo(path):
    base, ext = os.path.splitext(path)
    cands = {'.scx': ['.sct', '.SCT'], '.vcx': ['.vct', '.VCT'], '.mnx': ['.mnt', '.MNT'],
             '.pjx': ['.pjt', '.PJT'], '.ssf': ['.fpt', '.FPT'], '.dbf': ['.fpt', '.FPT', '.dbt']}
    for e in cands.get(ext.lower(), ['.fpt', '.FPT']):
        p = base + e
        if os.path.exists(p):
            return p
    return None


def read_dbf(path):
    data = open(path, 'rb').read()
    nrec, hlen, rlen = struct.unpack('<IHH', data[4:12])
    fields = []
    off = 32
    while data[off] != 0x0D:
        name = data[off:off + 11].split(b'\0')[0].decode('latin1')
        ftype = chr(data[off + 11])
        fofs = struct.unpack('<I', data[off + 12:off + 16])[0]
        flen = data[off + 16]
        fields.append((name, ftype, flen))
        off += 32
    memo = None
    mp = find_memo(path)
    if mp:
        memo = open(mp, 'rb').read()
        block = struct.unpack('>H', memo[6:8])[0] or 64
    rows = []
    for i in range(nrec):
        r = data[hlen + i * rlen: hlen + (i + 1) * rlen]
        deleted = r[0:1] == b'*'
        pos = 1
        row = {'_deleted': deleted}
        for name, ftype, flen in fields:
            raw = r[pos:pos + flen]
            pos += flen
            if ftype in 'MGW':
                if flen == 4:
                    ptr = struct.unpack('<I', raw)[0]
                else:
                    s = raw.strip()
                    ptr = int(s) if s.isdigit() else 0
                val = ''
                if ptr and memo:
                    o = ptr * block
                    mlen = struct.unpack('>I', memo[o + 4:o + 8])[0]
                    val = memo[o + 8:o + 8 + mlen].decode('cp1256', 'replace')
                row[name] = val
            elif ftype == 'I':
                row[name] = struct.unpack('<i', raw)[0]
            elif ftype == 'L':
                row[name] = raw in (b'T', b't', b'Y', b'y')
            else:
                row[name] = raw.decode('cp1256', 'replace').rstrip()
        rows.append(row)
    return fields, rows


if __name__ == '__main__':
    path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'form'
    fields, rows = read_dbf(path)
    if mode == 'fields':
        print(fields)
        print(len(rows), 'rows')
    elif mode == 'form':
        for r in rows:
            if r['_deleted']:
                continue
            nm = r.get('OBJNAME', '')
            if not nm and not r.get('METHODS'):
                continue
            print('=' * 70)
            print('OBJ:', r.get('PARENT', ''), '.', nm, ' CLASS:', r.get('CLASS', ''), ' BASE:', r.get('BASECLASS', ''))
            props = r.get('PROPERTIES', '')
            if props:
                print('--props--')
                print(props.strip())
            meth = r.get('METHODS', '')
            if meth and '-meth' not in mode:
                print('--methods--')
                print(meth.strip())
    else:
        for r in rows:
            print({k: (v[:300] if isinstance(v, str) else v) for k, v in r.items()})
