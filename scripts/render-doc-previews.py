# -*- coding: utf-8 -*-
"""Render LOCAL dos previews dos modelos de documentos.

NÃO roda na Vercel (depende de LibreOffice). Roda na máquina do autor e os
PNGs/exemplos resultantes são commitados como assets.

Fluxo:
  1. Lê os exemplos preenchidos em design/templates/documentos-empresa/examples/*-exemplo.docx
  2. Converte cada um para PDF via LibreOffice headless
  3. Rasteriza cada página em PNG (PyMuPDF) -> assets/modelos-documentos/previews/<id>/pN.png
  4. Copia o .docx de exemplo -> assets/modelos-documentos/examples/

<id> = nome do template sem extensão (ex: Metta-Proposta-Comercial), batendo com a
section.id do download-manifest. O build-manifest.mjs escaneia essas pastas.
"""
import os, sys, shutil, subprocess, tempfile, glob

BS   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))            # output/brand-system
EXSRC = os.path.abspath(os.path.join(BS, '..', '..', '..', 'design', 'templates', 'documentos-empresa', 'examples'))
PREV = os.path.join(BS, 'assets', 'modelos-documentos', 'previews')
EXOUT = os.path.join(BS, 'assets', 'modelos-documentos', 'examples')
SOFFICE = r'C:\Program Files\LibreOffice\program\soffice.exe'
ZOOM = 1.6   # ~108 dpi -> ~950px de largura, bom p/ preview web

def find_soffice():
    for p in (SOFFICE, r'C:\Program Files (x86)\LibreOffice\program\soffice.exe'):
        if os.path.exists(p): return p
    raise SystemExit('LibreOffice (soffice.exe) não encontrado.')

def main():
    import fitz  # PyMuPDF
    soffice = find_soffice()
    os.makedirs(PREV, exist_ok=True)
    os.makedirs(EXOUT, exist_ok=True)
    docs = sorted(glob.glob(os.path.join(EXSRC, '*-exemplo.docx')))
    if not docs:
        raise SystemExit(f'Nenhum exemplo em {EXSRC}')
    total_pages = 0
    with tempfile.TemporaryDirectory() as tmp:
        for src in docs:
            base = os.path.basename(src).replace('-exemplo.docx', '')   # Metta-Proposta-Comercial
            # 1) copia o docx de exemplo p/ servir como download secundário
            shutil.copy2(src, os.path.join(EXOUT, os.path.basename(src)))
            # 2) docx -> pdf
            subprocess.run([soffice, '--headless', '--convert-to', 'pdf', '--outdir', tmp, src],
                           check=True, capture_output=True)
            pdf = os.path.join(tmp, os.path.basename(src).replace('.docx', '.pdf'))
            # 3) pdf -> pngs
            outdir = os.path.join(PREV, base)
            if os.path.isdir(outdir): shutil.rmtree(outdir)
            os.makedirs(outdir, exist_ok=True)
            doc = fitz.open(pdf)
            for i, page in enumerate(doc):
                pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM))
                pix.save(os.path.join(outdir, f'p{i+1}.png'))
            n = doc.page_count
            doc.close()
            total_pages += n
            print(f'OK {base}  ({n} pág)')
    print(f'\n{len(docs)} documentos · {total_pages} páginas renderizadas')
    print(f'previews -> {PREV}')
    print(f'exemplos -> {EXOUT}')

if __name__ == '__main__':
    try:
        main()
    except UnicodeEncodeError:
        pass
