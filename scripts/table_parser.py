import numpy as np
import pandas as pd
import pytesseract
from pytesseract import Output

def parse_image_table(image, min_conf=30):
    """
    Parse a table from a PIL image using pytesseract spatial data.
    Returns: (DataFrame, raw_text)
    - DataFrame: reconstructed table (may have header row promoted)
    - raw_text: full OCR text from the page (string)
    """

    raw_text = pytesseract.image_to_string(image)

    data = pytesseract.image_to_data(image, output_type=Output.DICT)

    words = []
    n = len(data['text'])
    for i in range(n):
        text = (data['text'][i] or "").strip()
        conf = -1
        try:
            conf = int(data['conf'][i])
        except Exception:
            try:
                conf = float(data['conf'][i])
                conf = int(conf)
            except Exception:
                conf = -1
        if not text:
            continue
        if conf >= 0 and conf < min_conf:
            # skip very low confidence words (tunable)
            continue
        left = int(data['left'][i])
        top = int(data['top'][i])
        width = int(data['width'][i])
        height = int(data['height'][i])
        cx = left + width / 2.0
        cy = top + height / 2.0
        words.append({
            "text": text,
            "left": left,
            "top": top,
            "width": width,
            "height": height,
            "cx": cx,
            "cy": cy,
            "conf": conf
        })

    if not words:
        return pd.DataFrame(), raw_text

    # median height of word boxes -> used as tolerance
    heights = np.array([w['height'] for w in words])
    median_h = float(np.median(heights)) if len(heights) > 0 else 10.0
    if median_h < 4:
        median_h = 8.0

    # Determine column boundaries by finding large gaps in sorted x-centers
    xs = np.array(sorted([w['cx'] for w in words]))
    if len(xs) <= 1:
        # single column case
        col_bounds = [(min(xs) - median_h, max(xs) + median_h)]
    else:
        diffs = np.diff(xs)
        # threshold chosen relative to typical gap
        gap_threshold = max(np.median(diffs) * 2.5, np.mean(diffs) * 1.5)
        break_idxs = np.where(diffs > gap_threshold)[0]
        groups = []
        start = 0
        for b in break_idxs:
            groups.append(xs[start:b + 1])
            start = b + 1
        groups.append(xs[start:])
        col_bounds = []
        for g in groups:
            minx = float(np.min(g)) - median_h
            maxx = float(np.max(g)) + median_h
            col_bounds.append((minx, maxx))

    # assign each word to the best column (by cx)
    for w in words:
        assigned = False
        for ci, (xmin, xmax) in enumerate(col_bounds):
            if xmin <= w['cx'] <= xmax:
                w['col'] = ci
                assigned = True
                break
        if not assigned:
            # fallback: nearest column center
            centers = [0.5 * (b[0] + b[1]) for b in col_bounds]
            dists = [abs(w['cx'] - c) for c in centers]
            w['col'] = int(np.argmin(dists))

    # per-column cluster words vertically to handle multi-line cells
    col_clusters = {}
    for ci in range(len(col_bounds)):
        cw = [w for w in words if w['col'] == ci]
        if not cw:
            col_clusters[ci] = []
            continue
        cw_sorted = sorted(cw, key=lambda x: x['cy'])
        clusters = []
        current = [cw_sorted[0]]
        for w in cw_sorted[1:]:
            if w['cy'] - current[-1]['cy'] <= median_h * 1.2:
                current.append(w)
            else:
                clusters.append(current)
                current = [w]
        clusters.append(current)
        # produce (cluster_center_y, joined_text) list
        cluster_list = []
        for cl in clusters:
            cl_sorted = sorted(cl, key=lambda x: (x['top'], x['left']))
            joined = " ".join([c['text'] for c in cl_sorted])
            cy_mean = float(np.mean([c['cy'] for c in cl]))
            cluster_list.append((cy_mean, joined))
        col_clusters[ci] = cluster_list

    # build unified row centers by merging cluster centers across columns
    all_centers = []
    for ci in col_clusters:
        for cy, _ in col_clusters[ci]:
            all_centers.append(cy)
    if not all_centers:
        return pd.DataFrame(), raw_text
    all_centers = np.array(sorted(all_centers))

    row_tol = median_h * 1.5
    row_centers = []
    cur = [all_centers[0]]
    for c in all_centers[1:]:
        if c - cur[-1] <= row_tol:
            cur.append(c)
        else:
            row_centers.append(float(np.mean(cur)))
            cur = [c]
    row_centers.append(float(np.mean(cur)))
    row_centers = sorted(row_centers)

    # assemble rows: for each row center and each column pick nearest cluster (if within tol)
    rows = []
    for rc in row_centers:
        row = []
        for ci in range(len(col_bounds)):
            clusters = col_clusters.get(ci, [])
            chosen = ""
            best_d = float("inf")
            for cy, txt in clusters:
                d = abs(cy - rc)
                if d < best_d:
                    best_d = d
                    chosen = txt
            if best_d <= row_tol:
                row.append(chosen)
            else:
                row.append("")
        rows.append(row)

    df = pd.DataFrame(rows)

    # heuristically promote first row to header if it looks like header (non-empty count high)
    non_empty = df.astype(bool).sum(axis=1)
    if len(non_empty) > 1:
        first = non_empty.iloc[0]
        rest_max = int(non_empty.iloc[1:].max()) if non_empty.iloc[1:].size > 0 else 0
        if first >= max(rest_max, 1):
            # set first as header
            header = df.iloc[0].tolist()
            # make unique column names if duplicates
            seen = {}
            new_header = []
            for h in header:
                h_str = str(h).strip() if h is not None else ""
                if not h_str:
                    h_str = "col"
                base = h_str
                i = 1
                while base in seen:
                    base = f"{h_str}_{i}"
                    i += 1
                seen[base] = True
                new_header.append(base)
            df.columns = new_header
            df = df.drop(index=0).reset_index(drop=True)

    return df, raw_text
