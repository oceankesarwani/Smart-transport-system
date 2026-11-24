"""Rebuild five-slide editable deck with the configured Codex Artifact Tool runtime."""
import os
import sys
import json
import hashlib
import time
import subprocess
from pathlib import Path
from scripts.build_slide_content import build_slide_content


def generate_presentation_deck():
    build_slide_content()
    env=os.environ.copy()
    runtime=env.get('CODEX_ARTIFACT_RUNTIME')
    bundled=Path(sys.executable).resolve().parent.parent
    if not runtime and (bundled/'node/bin/node.exe').exists():
        runtime=str(bundled)
    if not runtime and os.name=='nt':
        matches=list(Path('C:/Program Files/WindowsApps').glob('OpenAI.CodexPrimaryRuntime*/dependencies'))
        if matches: runtime=str(sorted(matches)[-1])
    if not runtime:
        raise RuntimeError('Set CODEX_ARTIFACT_RUNTIME to the Codex bundled dependencies directory. Ready-made PPTX/PDF are in docs/.')
    env['CODEX_ARTIFACT_RUNTIME']=runtime
    if 'CODEX_PRESENTATIONS_SKILL' not in env:
        matches=list((Path.home()/'.codex/plugins/cache/openai-primary-runtime/presentations').glob('*/skills/presentations'))
        if not matches: raise RuntimeError('Set CODEX_PRESENTATIONS_SKILL to the installed presentations skill directory')
        env['CODEX_PRESENTATIONS_SKILL']=str(sorted(matches)[-1])
    node=Path(runtime)/'node/bin'/('node.exe' if os.name=='nt' else 'node')
    started=time.time()
    completed=subprocess.run([str(node),'scripts/build_slides.mjs'],env=env)
    if completed.returncode:
        # Windows Artifact Tool can abort during WASM shutdown after completing every export.
        # Accept only that exact shutdown code AND a fresh, hash-matching successful receipt.
        receipt=Path('results/presentation_validation.json')
        output=Path('docs/presentation.pptx')
        shutdown_code=completed.returncode & 0xFFFFFFFF
        verified=False
        if shutdown_code==0xC0000409 and receipt.exists() and output.exists() and receipt.stat().st_mtime>=started:
            data=json.loads(receipt.read_text())
            verified=(data.get('finalSha256')==hashlib.sha256(output.read_bytes()).hexdigest()
                      and data.get('packageIntegrity',{}).get('status')=='pass'
                      and data.get('presentationLayout',{}).get('finding_count')==0
                      and data.get('firstPartyImport',{}).get('passed') is True
                      and data.get('firstPartyImport',{}).get('slideCount')==5)
        if not verified:
            raise subprocess.CalledProcessError(completed.returncode,completed.args)
        print('Artifact runtime reported a Windows WASM shutdown abort after verified export; fresh hash-matching validation receipt confirms the five-slide file.')


if __name__=='__main__':
    generate_presentation_deck()
