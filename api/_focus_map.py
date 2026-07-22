"""Focus map — mede onde está o SUJEITO na imagem e diz pra qual zona vazia o
texto deve ir. É o que torna a composição focal-aware CONFIÁVEL: em vez de torcer
pro prompt do gerador deixar o topo/base vazio, a gente MEDE a imagem real e ancora
o texto onde de fato não há conteúdo — o texto nunca tampa o assunto.

POC validado à mão (troféu "meta é régua"): sem isso levava 3 tentativas; com isso,
1 geração + medição acerta o foco.

Sem dependências além de PIL. Retorna 'top'|'bottom' + as energias medidas (auditável).
"""

from __future__ import annotations

import io


def _band_energy(img, bands: int = 3) -> list[float]:
    """Energia de conteúdo (gradiente/detalhe) por faixa horizontal, 0..1.

    Downscale forte + magnitude de gradiente: faixa com sujeito = alta energia;
    fundo liso/escuro/desfocado (o vazio) = baixa. Robusto e barato (~ms)."""
    from PIL import Image, ImageFilter
    g = img.convert("L")
    # downscale preservando proporção — 120px de largura basta pra medir massa
    w0, h0 = g.size
    tw = 120
    th = max(1, round(h0 * tw / w0))
    g = g.resize((tw, th), Image.BILINEAR).filter(ImageFilter.FIND_EDGES)
    px = g.load()
    band_h = th / bands
    out = []
    for b in range(bands):
        y0 = int(b * band_h)
        y1 = th if b == bands - 1 else int((b + 1) * band_h)
        s = n = 0
        for y in range(y0, y1):
            for x in range(tw):
                s += px[x, y]
                n += 1
        out.append((s / n / 255.0) if n else 0.0)
    return out


def focus_anchor(image, min_gap: float = 0.04) -> tuple[str, dict]:
    """Decide a âncora do texto ('top'|'bottom') pela zona de MENOR conteúdo.

    `image`: bytes, data-URI ou caminho.
    Retorna (anchor, meta) — meta tem as energias das 3 faixas (auditável) e um
    flag `ambiguous` quando topo e base têm energia parecida (aí o prompt manda,
    fallback 'top' se o meio for o mais cheio = sujeito centralizado)."""
    from PIL import Image
    if isinstance(image, str):
        if image.startswith("data:"):
            import base64
            raw = base64.b64decode(image.split(",", 1)[1])
            img = Image.open(io.BytesIO(raw))
        else:
            img = Image.open(image)
    elif isinstance(image, (bytes, bytearray)):
        img = Image.open(io.BytesIO(bytes(image)))
    else:
        img = image  # já é PIL.Image

    e = _band_energy(img, bands=3)   # [topo, meio, base]
    top, mid, bot = e
    # A âncora vai SEMPRE pra faixa mais vazia entre topo e base — o texto foge do
    # assunto. NUNCA o meio (onde o sujeito costuma estar).
    anchor = "top" if top <= bot else "bottom"
    lo = min(top, bot)
    # Sujeito CENTRALIZADO (o meio é a faixa mais cheia) = topo E base seguros → a
    # leitura é CONFIÁVEL. ERA O BUG: centralizado caía em `abs(top-bot)<gap` e virava
    # "ambíguo", o texto ia pro anchor fixo do blueprint e cobria o rosto.
    subject_centered = mid >= max(top, bot)
    # "Ambíguo" de verdade = não existe faixa vazia (o sujeito ocupa o quadro todo):
    # a faixa mais vazia AINDA está cheia, topo≈base, e não é caso de centralizado.
    ambiguous = (lo > 0.14) and (abs(top - bot) < min_gap) and not subject_centered
    meta = {"energy_top": round(top, 3), "energy_mid": round(mid, 3),
            "energy_bottom": round(bot, 3), "ambiguous": ambiguous, "anchor": anchor,
            "subject_centered": subject_centered}
    return anchor, meta


def _load_img(image):
    from PIL import Image
    if isinstance(image, str):
        if image.startswith("data:"):
            import base64
            return Image.open(io.BytesIO(base64.b64decode(image.split(",", 1)[1])))
        return Image.open(image)
    if isinstance(image, (bytes, bytearray)):
        return Image.open(io.BytesIO(bytes(image)))
    return image


def focal_grid(image, rows: int = 4, cols: int = 3) -> list[list[float]]:
    """Grade 2D de energia de conteúdo (0..1) — mede ONDE está o sujeito na imagem.
    Pura PIL (roda no deploy). Célula cheia = sujeito; célula vazia = fundo liso."""
    from PIL import Image, ImageFilter
    g = _load_img(image).convert("L")
    w0, h0 = g.size
    tw = 144
    th = max(1, round(h0 * tw / w0))
    g = g.resize((tw, th), Image.BILINEAR).filter(ImageFilter.FIND_EDGES)
    px = g.load()
    grid = [[0.0] * cols for _ in range(rows)]
    for r in range(rows):
        y0, y1 = int(r * th / rows), (th if r == rows - 1 else int((r + 1) * th / rows))
        for c in range(cols):
            x0, x1 = int(c * tw / cols), (tw if c == cols - 1 else int((c + 1) * tw / cols))
            s = n = 0
            for y in range(y0, y1):
                for x in range(x0, x1):
                    s += px[x, y]; n += 1
            grid[r][c] = (s / n / 255.0) if n else 0.0
    mx = max((max(row) for row in grid), default=1.0) or 1.0
    return [[round(v / mx, 3) for v in row] for row in grid]


def focal_zone(image) -> tuple[str, dict]:
    """A IMAGEM MANDA: recomenda a zona de texto (a mais VAZIA), independente do
    blueprint. Retorna (zone, meta). zone ∈ {'top','bottom'} + coluna mais vazia em
    meta. Regra do Nathan: no empate, prefere o TOPO ('o plano superior')."""
    grid = focal_grid(image, rows=4, cols=3)
    rows, cols = len(grid), len(grid[0])
    half = rows // 2
    top = sum(sum(r) for r in grid[:half]) / (half * cols)
    bot = sum(sum(r) for r in grid[half:]) / ((rows - half) * cols)
    band = "top" if top <= bot + 0.02 else "bottom"
    zone_rows = grid[:half] if band == "top" else grid[half:]
    col_energy = [sum(row[c] for row in zone_rows) / len(zone_rows) for c in range(cols)]
    col = ["left", "center", "right"][col_energy.index(min(col_energy))]
    meta = {"band": band, "col": col, "energy_top": round(top, 3),
            "energy_bottom": round(bot, 3), "grid": grid}
    return band, meta


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        try:
            a, m = focus_anchor(p)
            print(f"{a:6}  top={m['energy_top']:.3f} mid={m['energy_mid']:.3f} "
                  f"bot={m['energy_bottom']:.3f} {'~ambíguo' if m['ambiguous'] else ''}  {p.split('/')[-1]}")
        except Exception as ex:
            print("ERRO", p, repr(ex)[:120])
