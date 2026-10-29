"""Validate and copy only the explicit public site tree. No private inputs or API requests."""
from pathlib import Path
import json
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]

def build(destination=None):
    source=ROOT/'site';destination=Path(destination) if destination else ROOT/'dist'
    if destination.resolve()==source.resolve() or source.resolve() in destination.resolve().parents or destination.resolve() in source.resolve().parents:
        raise ValueError('Build destination must be outside the source tree')
    for p in source.rglob('*'):
        if p.is_symlink():raise ValueError('Symlinks are not permitted in public assets')
        if p.suffix in {'.json'}:json.loads(p.read_text())
        if p.suffix.lower() in {'.env','.pem','.key','.docx','.pdf'}:raise ValueError('Unreviewed/private asset in public tree')
    if destination.exists():
        if any(destination.iterdir()) and not (destination/'.intelligence-observatory-build').is_file():
            raise ValueError('Refusing to replace an unmarked nonempty directory')
        shutil.rmtree(destination)
    shutil.copytree(source,destination)
    (destination/'.nojekyll').touch()
    (destination/'.intelligence-observatory-build').write_text('Generated static output only.\n')
    print(f'Public static build: {destination} ({sum(p.is_file() for p in destination.rglob("*"))} files)')
    return destination

if __name__=='__main__':build(sys.argv[1] if len(sys.argv)>1 else None)
