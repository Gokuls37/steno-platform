import re

# ─────────────────────────────────────────────────────────────────────────────
# VARIANTS DICTIONARY
# ─────────────────────────────────────────────────────────────────────────────
# IMPORTANT: Store ALL forms WITHOUT trailing dots.
# The evaluator strips trailing dots before any comparison.
# So "Hon." in a passage becomes "Hon" for matching purposes.
# "Govt." becomes "Govt", etc.
#
# Key   = canonical word (as in master passage, dots stripped)
# Value = set of accepted alternate forms (dots stripped)
# ─────────────────────────────────────────────────────────────────────────────

_VARIANTS: dict = {

    # Honourable
    "Honourable":  {"Hon", "Honble", "Honorable", "honorable", "hon", "honble"},
    "honourable":  {"hon", "honble", "honorable"},

    # Shri / Smt
    "Shri":        {"Sh", "Sri"},
    "shri":        {"sh", "sri"},
    "Smt":         {"Srimati", "Smti"},
    "smt":         {"srimati", "smti"},

    # Months
    "January":     {"Jan"},    "january":   {"jan"},
    "February":    {"Feb"},    "february":  {"feb"},
    "March":       {"Mar"},    "march":     {"mar"},
    "April":       {"Apr"},    "april":     {"apr"},
    "June":        {"Jun"},    "june":      {"jun"},
    "July":        {"Jul"},    "july":      {"jul"},
    "August":      {"Aug"},    "august":    {"aug"},
    "September":   {"Sep", "Sept"},
    "september":   {"sep", "sept"},
    "October":     {"Oct"},    "october":   {"oct"},
    "November":    {"Nov"},    "november":  {"nov"},
    "December":    {"Dec"},    "december":  {"dec"},

    # Government & Administration
    "Government":    {"Govt"},         "government":    {"govt"},
    "GOVERNMENT":    {"GOVT"},
    "Department":    {"Dept"},         "department":    {"dept"},
    "Secretary":     {"Secy", "Sec"},  "secretary":     {"secy", "sec"},
    "Director":      {"Dir"},          "director":      {"dir"},
    "Minister":      {"Min"},          "minister":      {"min"},
    "Chairman":      {"Ch", "Chairperson"}, "chairman": {"ch", "chairperson"},
    "Parliament":    {"Parl"},         "parliament":    {"parl"},
    "Committee":     {"Comm", "Com"},  "committee":     {"comm", "com"},
    "Commission":    {"Comn", "Comm"}, "commission":    {"comn", "comm"},
    "Amendment":     {"Amdt"},         "amendment":     {"amdt"},
    "Constitution":  {"Const"},        "constitution":  {"const"},
    "Article":       {"Art"},          "article":       {"art"},
    "Section":       {"Sec", "S"},     "section":       {"sec", "s"},
    "Schedule":      {"Sch"},          "schedule":      {"sch"},
    "Clause":        {"Cl"},           "clause":        {"cl"},
    "Regulation":    {"Reg"},          "regulation":    {"reg"},
    "Notification":  {"Notif"},        "notification":  {"notif"},
    "Memorandum":    {"Memo"},         "memorandum":    {"memo"},
    "Establishment": {"Estab", "Estt"},"establishment": {"estab", "estt"},
    "Administration":{"Admn", "Admin"},"administration":{"admn", "admin"},
    "Administrative":{"Admn", "Admin"},"administrative":{"admn", "admin"},
    "Organisation":  {"Org", "Organization"},
    "organisation":  {"org", "organization"},
    "Organization":  {"Org", "Organisation"},
    "organization":  {"org", "organisation"},
    "Corporation":   {"Corp", "Corpn"},"corporation":   {"corp", "corpn"},
    "Institute":     {"Inst", "Instt"},"institute":     {"inst", "instt"},
    "Institution":   {"Instn", "Inst"},"institution":   {"instn", "inst"},
    "University":    {"Univ"},         "university":    {"univ"},
    "Authority":     {"Auth"},         "authority":     {"auth"},
    "Association":   {"Assn", "Assoc"},"association":   {"assn", "assoc"},
    "Federation":    {"Fedn"},         "federation":    {"fedn"},
    "Conference":    {"Conf"},         "conference":    {"conf"},
    "Publication":   {"Pub", "Publn"}, "publication":   {"pub", "publn"},
    "Member":        {"Mem"},          "member":        {"mem"},
    "Circular":      {"Circ"},         "circular":      {"circ"},

    # Legal / Common
    "Versus":        {"Vs", "vs"},     "versus":        {"vs", "Vs"},
    "Number":        {"No", "Nos"},    "number":        {"no", "nos"},
    "Rupees":        {"Rs"},           "rupees":        {"rs"},
    "Approximately": {"Approx"},       "approximately": {"approx"},
    "Maximum":       {"Max"},          "maximum":       {"max"},
    "Minimum":       {"Min"},          "minimum":       {"min"},
    "Average":       {"Avg"},          "average":       {"avg"},
    "Kilometre":     {"Km", "Kilometer"},   "kilometre":     {"km", "kilometer"},
    "Kilogram":      {"Kg"},           "kilogram":      {"kg"},
    "Centimetre":    {"Cm", "Centimeter"}, "centimetre":  {"cm", "centimeter"},
    "Millimetre":    {"Mm", "Millimeter"}, "millimetre":  {"mm", "millimeter"},
    "Litre":         {"Lt", "Liter"},  "litre":         {"lt", "liter"},
    "Gram":          {"Gm"},           "gram":          {"gm"},

    # British <-> Indian English (bidirectional)
    "colour":     {"color"},    "color":     {"colour"},
    "Colour":     {"Color"},    "Color":     {"Colour"},
    "honour":     {"honor"},    "honor":     {"honour"},
    "Honour":     {"Honor"},    "Honor":     {"Honour"},
    "honoured":   {"honored"},  "honored":   {"honoured"},
    "labour":     {"labor"},    "labor":     {"labour"},
    "Labour":     {"Labor"},    "Labor":     {"Labour"},
    "behaviour":  {"behavior"}, "behavior":  {"behaviour"},
    "Behaviour":  {"Behavior"}, "Behavior":  {"Behaviour"},
    "favour":     {"favor"},    "favor":     {"favour"},
    "Favour":     {"Favor"},    "Favor":     {"Favour"},
    "favourable": {"favorable"},"favorable": {"favourable"},
    "Favourable": {"Favorable"},"Favorable": {"Favourable"},
    "neighbour":  {"neighbor"}, "neighbor":  {"neighbour"},
    "centre":     {"center"},   "center":    {"centre"},
    "Centre":     {"Center"},   "Center":    {"Centre"},
    "defence":    {"defense"},  "defense":   {"defence"},
    "Defence":    {"Defense"},  "Defense":   {"Defence"},
    "licence":    {"license"},  "license":   {"licence"},
    "Licence":    {"License"},  "License":   {"Licence"},
    "practise":   {"practice"}, "practice":  {"practise"},
    "programme":  {"program"},  "program":   {"programme"},
    "Programme":  {"Program"},  "Program":   {"Programme"},
    "catalogue":  {"catalog"},  "catalog":   {"catalogue"},
    "dialogue":   {"dialog"},   "dialog":    {"dialogue"},
    "Dialogue":   {"Dialog"},
    "travelled":  {"traveled"}, "traveled":  {"travelled"},
    "Travelled":  {"Traveled"},
    "travelling": {"traveling"},"traveling": {"travelling"},
    "Travelling": {"Traveling"},
    "recognised": {"recognized"},"recognized":{"recognised"},
    "Recognised": {"Recognized"},"Recognized":{"Recognised"},
    "organised":  {"organized"}, "organized": {"organised"},
    "Organised":  {"Organized"}, "Organized": {"Organised"},
    "realised":   {"realized"},  "realized":  {"realised"},
    "Realised":   {"Realized"},
    "analysed":   {"analyzed"},  "analyzed":  {"analysed"},
    "Analysed":   {"Analyzed"},
    "finalised":  {"finalized"}, "finalized": {"finalised"},
    "Finalised":  {"Finalized"},
    "authorised": {"authorized"},"authorized":{"authorised"},
    "Authorised": {"Authorized"},
    "summarised": {"summarized"},"summarized":{"summarised"},
    "emphasised": {"emphasized"},"emphasized":{"emphasised"},
    "judgement":  {"judgment"},  "judgment":  {"judgement"},
    "Judgement":  {"Judgment"},  "Judgment":  {"Judgement"},
    "acknowledgement":{"acknowledgment"},
    "acknowledgment": {"acknowledgement"},
    "fulfil":     {"fulfill"},   "fulfill":   {"fulfil"},
    "Fulfil":     {"Fulfill"},
    "enrol":      {"enroll"},    "enroll":    {"enrol"},
    "skilful":    {"skillful"},  "skillful":  {"skilful"},
    "instalment": {"installment"},"installment":{"instalment"},
    "woollen":    {"woolen"},    "woolen":    {"woollen"},
    "mould":      {"mold"},      "mold":      {"mould"},
    "draught":    {"draft"},     "draft":     {"draught"},
    "tyre":       {"tire"},      "tire":      {"tyre"},
    "ageing":     {"aging"},     "aging":     {"ageing"},

    # SSC-specific
    "crores":        {"crore"},       "crore":         {"crores"},
    "lakhs":         {"lakh", "lac"}, "lakh":          {"lakhs", "lac"},
    "lac":           {"lakh", "lakhs"},
    "percent":       {"per cent"},    "per cent":      {"percent"},
    "Percent":       {"Per cent", "Per Cent"},
    "Per cent":      {"Percent", "Per Cent"},
    "Per Cent":      {"Percent", "Per cent"},
    "cooperation":   {"co-operation"},  "co-operation":  {"cooperation"},
    "Cooperation":   {"Co-operation"},  "Co-operation":  {"Cooperation"},
    "cooperative":   {"co-operative"},  "co-operative":  {"cooperative"},
    "Cooperative":   {"Co-operative"},  "Co-operative":  {"Cooperative"},
    "wellbeing":     {"well-being"},    "well-being":    {"wellbeing"},
    "Wellbeing":     {"Well-being"},    "Well-being":    {"Wellbeing"},
    "longterm":      {"long-term"},     "long-term":     {"longterm"},
    "shortterm":     {"short-term"},    "short-term":    {"shortterm"},
    "midterm":       {"mid-term"},      "mid-term":      {"midterm"},
    "reelection":    {"re-election"},   "re-election":   {"reelection"},

    # Ordinal numbers (typed as words or numerals)
    "1st":  {"first"},   "first":  {"1st"},
    "2nd":  {"second"},  "second": {"2nd"},
    "3rd":  {"third"},   "third":  {"3rd"},
    "4th":  {"fourth"},  "fourth": {"4th"},
    "5th":  {"fifth"},   "fifth":  {"5th"},
    "6th":  {"sixth"},   "sixth":  {"6th"},
    "7th":  {"seventh"}, "seventh":{"7th"},
    "8th":  {"eighth"},  "eighth": {"8th"},
    "9th":  {"ninth"},   "ninth":  {"9th"},
    "10th": {"tenth"},   "tenth":  {"10th"},
    "11th": {"eleventh"},"eleventh":{"11th"},
    "12th": {"twelfth"}, "twelfth":{"12th"},
    "20th": {"twentieth"},"twentieth":{"20th"},
    "21st": {"twenty-first"},
    "22nd": {"twenty-second"},
    "25th": {"twenty-fifth"},
    "30th": {"thirtieth"},
    "50th": {"fiftieth"},
    "100th":{"hundredth"},
}

# Build inverted lookup: form -> set of canonical keys it belongs to
_LOOKUP: dict = {}

def _build_lookup():
    _LOOKUP.clear()
    for canonical, alts in _VARIANTS.items():
        _LOOKUP.setdefault(canonical, set()).add(canonical)
        for alt in alts:
            _LOOKUP.setdefault(alt, set()).add(canonical)

_build_lookup()


def are_variants(mc: str, tc: str) -> bool:
    """
    Case-sensitive variant check.
    Both mc and tc must already have trailing dots stripped (word_core applied).

    A match is only valid if:
      - They are identical, OR
      - tc is directly listed as an accepted form of mc, OR
      - mc is directly listed as an accepted form of tc
    (Shared-canonical-group matching is intentionally disabled to prevent
     false matches like hon/honorable both being under Honourable canonical.)
    """
    if mc == tc:
        return True
    # Direct: tc is listed as an alt of mc
    if tc in _VARIANTS.get(mc, set()):
        return True
    # Reverse: mc is listed as an alt of tc
    if mc in _VARIANTS.get(tc, set()):
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# EDIT DISTANCE (Levenshtein)
# ─────────────────────────────────────────────────────────────────────────────

def edit_distance(a: str, b: str) -> int:
    """
    Damerau-Levenshtein distance — counts insertions, deletions,
    substitutions, AND adjacent transpositions each as 1 edit.
    e.g. teh vs the = 1 (transposition), not 2.
    """
    la, lb = len(a), len(b)
    dp = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1): dp[i][0] = i
    for j in range(lb + 1): dp[0][j] = j
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if a[i-1] == b[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j]   + 1,
                dp[i][j-1]   + 1,
                dp[i-1][j-1] + cost
            )
            if i > 1 and j > 1 and a[i-1] == b[j-2] and a[i-2] == b[j-1]:
                dp[i][j] = min(dp[i][j], dp[i-2][j-2] + 1)
    return dp[la][lb]


def is_half_mistake(mc: str, tc: str) -> bool:
    """
    True if typed core (tc) is a minor spelling error of master core (mc).

    Rules (all case-insensitive):
      d=0          → not a mistake (identical)
      mn <= 2      → never half (2-char word substitutions like to/into,
                     in/on, is/it are full mistakes; prefix cases like
                     be/been are caught earlier by the related-words check)
      mn == 3      → half only if d=1 AND same first char (catches the/teh,
                     not/nor etc.)
      mn >= 4, d=1 → always half (single char typo / transposition)
      mn >= 4, d=2 → half only if same first char or one is prefix of other
                     (catches cooperation/cooperative, practised/practiced;
                     rejects completely different 4-char words)
    """
    d = edit_distance(mc.lower(), tc.lower())
    if d == 0:
        return False
    mn = min(len(mc), len(tc))
    if mn <= 2:
        return False   # short words: full mistake
    same_start = mc[0].lower() == tc[0].lower()
    if mn == 3:
        return d == 1 and same_start
    # mn >= 4
    prefix = mc.lower().startswith(tc.lower()) or tc.lower().startswith(mc.lower())
    if d == 1:
        return True
    if d == 2:
        return prefix or same_start
    return False


# ─────────────────────────────────────────────────────────────────────────────
# TEXT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def normalize_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.])", r"\1", text)
    return text.strip()


def strip_punct(word: str) -> str:
    """
    Remove all punctuation EXCEPT a single trailing full stop.
    NOTE: abbreviation dots (Hon., Govt.) are treated as trailing full stops
    and stripped via word_core() before variant/error comparison.
    """
    cleaned = re.sub(r"[^\w.]", "", word)
    cleaned = re.sub(r"^[.]+", "", cleaned)
    cleaned = re.sub(r"[.]{2,}$", ".", cleaned)
    return cleaned


def tokenize(text: str) -> list:
    return [t for t in (strip_punct(w) for w in text.split()) if t]


def word_core(token: str) -> str:
    """Strip ALL trailing dots — handles both sentence dots and abbrev dots."""
    return token.rstrip(".")


def has_fullstop(token: str) -> bool:
    return token.endswith(".")


def tokens_accepted(m: str, t: str) -> bool:
    """
    True if typed token t is accepted for master token m.
    Strips dots first, then checks exact match OR variant dictionary.
    Capitalisation differences are NOT accepted here (caught separately).
    """
    mc = word_core(m)
    tc = word_core(t)
    if mc == tc:
        return True
    if are_variants(mc, tc):
        return True
    return False


def tokens_ci(a: str, b: str) -> bool:
    """Case-insensitive core match (for capitalisation error detection)."""
    return word_core(a).lower() == word_core(b).lower()


# ─────────────────────────────────────────────────────────────────────────────
# RESYNC
# ─────────────────────────────────────────────────────────────────────────────

# Common words that appear too frequently to anchor a resync
_STOPWORDS = frozenset({
    'the','a','an','in','of','to','and','or','it','is','was','has','had',
    'have','been','be','that','this','on','at','by','for','with','from',
    'as','are','were','its','not','he','she','we','they','his','her','our',
    'their','which','who','what','when','where','how','any','all','no','may',
    'but','if','so','do','did','does','will','would','could','should','shall',
    'one','two','per','say','can','i','am','my','me','us','him','its'
})


def _alignment_score(master_tokens, typed_tokens, mi, tj, check=8):
    """
    Score how well master[mi:] aligns with typed[tj:] over 'check' tokens.

    Rules:
    - Anchor check: master[mi] and typed[tj] must themselves match or be
      near-match (edit<=2, both non-stopwords). If anchor fails -> score=0.
    - Matching content word  = +2.0
    - Near-match content word (edit distance 1-2) = +0.8
    - Matching stopword      = +0.2
    - Final requirement: at least 2 content-word matches, else score=0.
    """
    m0 = master_tokens[mi].rstrip('.')
    t0 = typed_tokens[tj].rstrip('.')
    anchor_ok = (
        tokens_accepted(master_tokens[mi], typed_tokens[tj]) or
        tokens_ci(master_tokens[mi], typed_tokens[tj]) or
        (m0.lower() not in _STOPWORDS and t0.lower() not in _STOPWORDS and
         edit_distance(m0.lower(), t0.lower()) <= 2)
    )
    if not anchor_ok:
        return 0.0

    score = 0.0
    content_hits = 0
    for c in range(check):
        if mi + c >= len(master_tokens) or tj + c >= len(typed_tokens):
            break
        mc = master_tokens[mi + c].rstrip('.')
        tc = typed_tokens[tj + c].rstrip('.')
        is_stop = mc.lower() in _STOPWORDS
        matched = (tokens_accepted(master_tokens[mi + c], typed_tokens[tj + c]) or
                   tokens_ci(master_tokens[mi + c], typed_tokens[tj + c]))
        if matched:
            score += 0.2 if is_stop else 2.0
            if not is_stop:
                content_hits += 1
        elif not is_stop and tc.lower() not in _STOPWORDS:
            if edit_distance(mc.lower(), tc.lower()) <= 2:
                score += 0.8
                content_hits += 1

    return score if content_hits >= 2 else 0.0


def _find_resync(master_tokens, typed_tokens, i, j,
                 max_omit=80, max_extra=10, min_score=3.0):
    """
    Find the EARLIEST valid re-alignment point after a large omission.

    Scans skip_m from 2 upward (skip_m=1 is a substitution, handled separately).
    Returns the FIRST skip_m whose best skip_t score >= min_score.
    Returns (skip_m, skip_t) or None.
    """
    for skip_m in range(2, max_omit + 1):  # start at 2 — skip_m=1 is a substitution
        mi = i + skip_m
        if mi >= len(master_tokens):
            break
        best_t_score = 0.0
        best_t = None
        for skip_t in range(0, max_extra + 1):
            tj = j + skip_t
            if tj >= len(typed_tokens):
                break
            s = _alignment_score(master_tokens, typed_tokens, mi, tj)
            if s > best_t_score:
                best_t_score = s
                best_t = skip_t
        if best_t_score >= min_score:
            return skip_m, best_t
    return None


# ─────────────────────────────────────────────────────────────────────────────
# EVALUATE
# ─────────────────────────────────────────────────────────────────────────────

def evaluate(master_text: str, typed_text: str, total_words) -> dict:
    master_tokens = tokenize(normalize_text(master_text))
    typed_tokens  = tokenize(normalize_text(typed_text))

    LOOKAHEAD = 5
    i = j = 0
    full = extra = omission = 0
    half = capitalization = fullstop = 0.0

    while i < len(master_tokens) and j < len(typed_tokens):
        m, t = master_tokens[i], typed_tokens[j]

        # ── 1. Accepted (exact or variant) ───────────────────────────────────
        if tokens_accepted(m, t):
            if has_fullstop(m) != has_fullstop(t):
                fullstop += 0.5
            i += 1; j += 1
            continue

        # ── 2. Capitalisation-only ────────────────────────────────────────────
        if tokens_ci(m, t):
            capitalization += 0.5
            if has_fullstop(m) != has_fullstop(t):
                fullstop += 0.5
            i += 1; j += 1
            continue

        # ── 3. Direct mistake check — if words are "close", skip lookahead ────
        # This prevents double-penalty: e.g. "Member" vs "Members" being
        # counted as omission(Members) + extra(Member) instead of 1 half mistake.
        mc_pre, tc_pre = word_core(m), word_core(t)
        pre_dist = edit_distance(mc_pre.lower(), tc_pre.lower())
        # Consider words "related" if edit distance ≤ 3 AND they share the
        # same starting character (avoids treating totally different short words
        # like "in"/"on" as related when context says otherwise)
        # Words are "related" (same word with errors) if:
        #   - edit dist <= proportional threshold AND same starting letter, OR
        #   - edit dist == 1 (single-char error always treated as same word)
        # Guards: both words must be >= 3 chars; length ratio must be reasonable.
        # This prevents: hass/was (d=2, diff start) -> NOT related
        #                hon/honorable (d=6) -> NOT related
        #                Members/Member (d=1, same start) -> RELATED
        #                rcall/recall (d=1, same start) -> RELATED
        _min_len = min(len(mc_pre), len(tc_pre))
        _max_len = max(len(mc_pre), len(tc_pre))
        _threshold = max(2, int(_min_len * 0.45))
        _same_start = mc_pre[0].lower() == tc_pre[0].lower() if mc_pre and tc_pre else False
        _len_ratio_ok = _min_len >= 2 and (_max_len / _min_len) <= 2.5
        # Also treat as related if one word is a prefix of the other
        # (e.g. be/been, hon/honorable, introduc/introduced, dept/department)
        _mc_lower = mc_pre.lower()
        _tc_lower = tc_pre.lower()
        _prefix_match = (
            _min_len >= 2 and
            (_mc_lower.startswith(_tc_lower) or _tc_lower.startswith(_mc_lower))
        )
        # For very short words (<=2 chars), require same first char to avoid
        # false matches like is/it, in/on, be/by etc.
        _short_word = _min_len <= 2
        words_are_related = (
            _prefix_match or
            (
                _len_ratio_ok and
                (
                    (pre_dist == 1 and (not _short_word or _same_start)) or
                    (pre_dist <= _threshold and _same_start)
                )
            )
        )
        if words_are_related:
            # Words confirmed as same word with errors — use simple d<=2 for half/full
            # (is_half_mistake has short-word guards for the fallthrough path,
            #  but here we know they are the same word, so d<=2 = half is correct)
            if edit_distance(mc_pre.lower(), tc_pre.lower()) <= 2:
                half += 0.5
            else:
                full += 1
            if has_fullstop(m) != has_fullstop(t):
                fullstop += 0.5
            i += 1; j += 1
            continue

        # ── 4. Small lookahead + look-before (omissions and genuine extras) ──────
        omit_k  = None
        extra_k = None

        # OMISSION: typed[j] found exactly in master[i+1..i+LOOKAHEAD]
        for k in range(1, LOOKAHEAD + 1):
            if i + k < len(master_tokens) and (
                tokens_accepted(master_tokens[i + k], t) or
                tokens_ci(master_tokens[i + k], t)
            ):
                omit_k = k
                break

        # LOOK-AHEAD EXTRA override: even if typed[j] appears ahead in master,
        # if master[i] matches typed[j+1] exactly, then typed[j] is a genuine
        # extra inserted BEFORE the correct word.
        # e.g. master='which worked for', typed='for which worked'
        # omit_k would fire (for at master[2]) but master[i]=which IS typed[j+1]
        # -> typed[j]='for' is extra, not an omission of 'which'+'worked'
        master_i_in_typed_next = (
            j + 1 < len(typed_tokens) and (
                tokens_accepted(m, typed_tokens[j + 1]) or
                tokens_ci(m, typed_tokens[j + 1])
            )
        )
        if master_i_in_typed_next:
            # typed[j] is extra — master[i] is right there at typed[j+1]
            extra_k = 1
            omit_k  = None  # cancel any omit_k — no words were omitted

        # GENUINE EXTRA: typed[j] not in master ahead AND master[i] at typed[j+1]
        # Only look forward (i onward) — words behind are already consumed.
        elif not any(
            tokens_accepted(master_tokens[ii], t) or tokens_ci(master_tokens[ii], t)
            for ii in range(i, min(len(master_tokens), i + LOOKAHEAD + 2))
        ):
            if (j + 1 < len(typed_tokens) and (
                tokens_accepted(m, typed_tokens[j + 1]) or
                tokens_ci(m, typed_tokens[j + 1])
            )):
                extra_k = 1

        if omit_k is not None and (extra_k is None or omit_k <= extra_k):
            omission += omit_k
            i += omit_k
            continue
        elif extra_k is not None:
            extra += extra_k
            j += extra_k
            continue

        # ── 5. Large resync — student skipped many words ──────────────────────
        resync = _find_resync(master_tokens, typed_tokens, i, j)
        if resync:
            skip_m, skip_t = resync
            pairs = min(skip_m, skip_t)
            subs_m = subs_t = 0
            hit_match = False
            for x in range(pairs):
                mw = master_tokens[i + x]
                tw = typed_tokens[j + x] if j + x < len(typed_tokens) else None
                if tw is None:
                    break
                if tokens_accepted(mw, tw) or tokens_ci(mw, tw):
                    hit_match = True
                    break

                # Check if typed[j+x] is a genuine extra:
                # master word (mw) appears ahead in typed -> typed[j+x] is inserted extra
                mw_ahead_in_typed = any(
                    tokens_accepted(mw, typed_tokens[jj]) or tokens_ci(mw, typed_tokens[jj])
                    for jj in range(j + x + 1, min(len(typed_tokens), j + x + 4))
                )
                if mw_ahead_in_typed:
                    # typed[j+x] is extra — count it, but don't advance master
                    extra += 1
                    subs_t += 1
                    # Don't increment subs_m — master[i+x] still needs to be matched
                    # We break out to let the main loop re-handle master[i+x]
                    hit_match = True  # stop pair walk, resume from here
                    break

                mwc, twc = word_core(mw), word_core(tw)
                if is_half_mistake(mwc, twc):
                    half += 0.5
                else:
                    full += 1
                if has_fullstop(mw) != has_fullstop(tw):
                    fullstop += 0.5
                subs_m += 1
                subs_t += 1

            if hit_match:
                i += subs_m
                j += subs_t
            else:
                rem_m = skip_m - subs_m
                rem_t = skip_t - subs_t
                omission += rem_m
                extra    += max(0, rem_t - rem_m)
                i += skip_m
                j += subs_t + max(0, rem_t - rem_m)
            continue

        # ── 6. True substitution — no alignment found anywhere ───────────────
        mc, tc = word_core(m), word_core(t)
        if is_half_mistake(mc, tc):
            half += 0.5
        else:
            full += 1
        if has_fullstop(m) != has_fullstop(t):
            fullstop += 0.5
        i += 1; j += 1

    if i < len(master_tokens): omission += len(master_tokens) - i
    if j < len(typed_tokens):  extra    += len(typed_tokens)  - j

    total_errors  = full + omission + extra + half + capitalization + fullstop
    word_base     = int(total_words) if total_words and int(total_words) > 0 else 1
    error_percent = (total_errors / word_base) * 100

    return {
        "full":           int(full),
        "half":           half,
        "omission":       int(omission),
        "extra":          int(extra),
        "capitalization": capitalization,
        "fullstop":       fullstop,
        "total_errors":   total_errors,
        "error_percent":  round(error_percent, 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# HIGHLIGHT
# ─────────────────────────────────────────────────────────────────────────────

def highlight_passage(master_text: str, typed_text: str) -> str:
    master_tokens = tokenize(normalize_text(master_text))
    typed_tokens  = tokenize(normalize_text(typed_text))

    LOOKAHEAD = 5
    output = []
    i = j = 0

    while i < len(master_tokens) and j < len(typed_tokens):
        m, t = master_tokens[i], typed_tokens[j]

        # Accepted
        if tokens_accepted(m, t):
            mc, tc = word_core(m), word_core(t)
            if has_fullstop(m) != has_fullstop(t):
                output.append(f'<span class="highlight fullstop">{t} <em>({m})</em></span>')
            elif mc != tc:
                output.append(f'<span class="highlight variant">{t} <em>✓({m})</em></span>')
            else:
                output.append(t)
            i += 1; j += 1
            continue

        # Capitalisation
        if tokens_ci(m, t):
            output.append(f'<span class="highlight capital">{t} <em>({m})</em></span>')
            i += 1; j += 1
            continue

        # Direct mistake check — same logic as evaluate()
        mc_pre, tc_pre = word_core(m), word_core(t)
        pre_dist = edit_distance(mc_pre.lower(), tc_pre.lower())
        # Words are "related" (same word with errors) if:
        #   - edit dist <= proportional threshold AND same starting letter, OR
        #   - edit dist == 1 (single-char error always treated as same word)
        # Guards: both words must be >= 3 chars; length ratio must be reasonable.
        # This prevents: hass/was (d=2, diff start) -> NOT related
        #                hon/honorable (d=6) -> NOT related
        #                Members/Member (d=1, same start) -> RELATED
        #                rcall/recall (d=1, same start) -> RELATED
        _min_len = min(len(mc_pre), len(tc_pre))
        _max_len = max(len(mc_pre), len(tc_pre))
        _threshold = max(2, int(_min_len * 0.45))
        _same_start = mc_pre[0].lower() == tc_pre[0].lower() if mc_pre and tc_pre else False
        _len_ratio_ok = _min_len >= 2 and (_max_len / _min_len) <= 2.5
        # Also treat as related if one word is a prefix of the other
        # (e.g. be/been, hon/honorable, introduc/introduced, dept/department)
        _mc_lower = mc_pre.lower()
        _tc_lower = tc_pre.lower()
        _prefix_match = (
            _min_len >= 2 and
            (_mc_lower.startswith(_tc_lower) or _tc_lower.startswith(_mc_lower))
        )
        # For very short words (<=2 chars), require same first char to avoid
        # false matches like is/it, in/on, be/by etc.
        _short_word = _min_len <= 2
        words_are_related = (
            _prefix_match or
            (
                _len_ratio_ok and
                (
                    (pre_dist == 1 and (not _short_word or _same_start)) or
                    (pre_dist <= _threshold and _same_start)
                )
            )
        )
        if words_are_related:
            if edit_distance(mc_pre.lower(), tc_pre.lower()) <= 2:
                output.append(f'<span class="highlight half">{t} <em>({m})</em></span>')
            else:
                output.append(f'<span class="highlight full">{t} <em>({m})</em></span>')
            i += 1; j += 1
            continue

        # Small lookahead + look-ahead extra override
        omit_k  = None
        extra_k = None

        for k in range(1, LOOKAHEAD + 1):
            if i + k < len(master_tokens) and (
                tokens_accepted(master_tokens[i + k], t) or tokens_ci(master_tokens[i + k], t)
            ):
                omit_k = k
                break

        # Look-ahead override: if master[i] matches typed[j+1], typed[j] is extra
        master_i_in_typed_next = (
            j + 1 < len(typed_tokens) and (
                tokens_accepted(m, typed_tokens[j + 1]) or
                tokens_ci(m, typed_tokens[j + 1])
            )
        )
        if master_i_in_typed_next:
            extra_k = 1
            omit_k  = None
        elif not any(
            tokens_accepted(master_tokens[ii], t) or tokens_ci(master_tokens[ii], t)
            for ii in range(i, min(len(master_tokens), i + LOOKAHEAD + 2))
        ):
            if (j + 1 < len(typed_tokens) and (
                tokens_accepted(m, typed_tokens[j + 1]) or
                tokens_ci(m, typed_tokens[j + 1])
            )):
                extra_k = 1

        if omit_k is not None and (extra_k is None or omit_k <= extra_k):
            for x in range(omit_k):
                output.append(f'<span class="highlight omission"><em>[{master_tokens[i + x]}]</em></span>')
            i += omit_k
            continue
        elif extra_k is not None:
            for x in range(extra_k):
                output.append(f'<span class="highlight extra">{typed_tokens[j + x]}</span>')
            j += extra_k
            continue

        # Large resync
        resync = _find_resync(master_tokens, typed_tokens, i, j)
        if resync:
            skip_m, skip_t = resync
            pairs = min(skip_m, skip_t)
            subs_m = subs_t = 0
            hit_match = False
            for x in range(pairs):
                mw = master_tokens[i + x]
                tw = typed_tokens[j + x] if j + x < len(typed_tokens) else None
                if tw is None:
                    break
                if tokens_accepted(mw, tw) or tokens_ci(mw, tw):
                    hit_match = True
                    break
                # Check if typed[j+x] is a genuine extra
                mw_ahead_in_typed = any(
                    tokens_accepted(mw, typed_tokens[jj]) or tokens_ci(mw, typed_tokens[jj])
                    for jj in range(j + x + 1, min(len(typed_tokens), j + x + 4))
                )
                if mw_ahead_in_typed:
                    output.append(f'<span class="highlight extra">{tw}</span>')
                    subs_t += 1
                    hit_match = True
                    break
                mwc, twc = word_core(mw), word_core(tw)
                cls = 'half' if is_half_mistake(mwc, twc) else 'full'
                output.append(f'<span class="highlight {cls}">{tw} <em>({mw})</em></span>')
                subs_m += 1
                subs_t += 1

            if hit_match:
                i += subs_m
                j += subs_t
            else:
                rem_m = skip_m - subs_m
                rem_t = skip_t - subs_t
                for x in range(rem_m):
                    output.append(f'<span class="highlight omission"><em>[{master_tokens[i + subs_m + x]}]</em></span>')
                for x in range(max(0, rem_t - rem_m)):
                    idx = j + subs_t + rem_m + x
                    if idx < len(typed_tokens):
                        output.append(f'<span class="highlight extra">{typed_tokens[idx]}</span>')
                i += skip_m
                j += subs_t + max(0, rem_t - rem_m)
            continue

        # True mismatch
        mc, tc = word_core(m), word_core(t)
        if is_half_mistake(mc, tc):
            output.append(f'<span class="highlight half">{t} <em>({m})</em></span>')
        else:
            output.append(f'<span class="highlight full">{t} <em>({m})</em></span>')
        i += 1; j += 1

    while i < len(master_tokens):
        output.append(f'<span class="highlight omission"><em>[{master_tokens[i]}]</em></span>')
        i += 1
    while j < len(typed_tokens):
        output.append(f'<span class="highlight extra">{typed_tokens[j]}</span>')
        j += 1

    return " ".join(output)


# ── Wrapper matching new platform call signature ──────────────────────────────
def evaluate_and_highlight(original: str, typed: str, word_count: int):
    """
    Returns (result_dict, highlighted_html)
    result_dict keys: full, half, omission, extra, capitalization, fullstop,
                      total_errors, error_percent, wpm
    """
    result = evaluate(original, typed, word_count)
    highlighted = highlight_passage(original, typed)
    # Normalise keys to match what routes expect
    out = {
        "full":          result.get("full_mistakes", result.get("full", 0)),
        "half":          result.get("half_mistakes", result.get("half", 0)),
        "omission":      result.get("omissions",     result.get("omission", 0)),
        "extra":         result.get("extra_words",   result.get("extra", 0)),
        "capitalization":result.get("capitalization",0),
        "fullstop":      result.get("fullstop",      0),
        "total_errors":  result.get("total_errors",  0),
        "error_percent": result.get("error_percent", result.get("error_pct", 0)),
        "wpm":           result.get("wpm", 0),
    }
    return out, highlighted
