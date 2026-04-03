"""
Re-ranking engine.

FINAL SCORE = 0.4 * Skill Coverage
            + 0.3 * BM25 (SkillIntelligence weighted)
            + 0.2 * DB Importance Weight
            + 0.1 * Raw BM25

SkillIntelligence is computed inline from IT_Job_Roles_Skills.csv:
    0.40 * semantic IDF   — rare skills score higher
    0.25 * market demand  — frequency across all roles
    0.20 * graph PageRank — skill co-occurrence network centrality
    0.15 * TF-IDF         — distinctiveness across corpus

Results are cached to apps/documents/data/skill_scores.pkl on first run.
"""
from __future__ import annotations

import logging
import math
import pickle
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Set

#Used to build a skill relationship graph.


logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────
# BM25 hyperparameters
# ──────────────────────────────────────────────────────────────────
BM25_K1 = 1.5
BM25_B  = 0.75

_PERFECT_TERM = (BM25_K1 + 1) / (1 + BM25_K1 * (1 - BM25_B + BM25_B))

# CSV and cache paths
_DATA_DIR   = Path(__file__).resolve().parent.parent.parent.parent / "apps" / "documents" / "data"
_CSV_PATH   = _DATA_DIR / "IT_Job_Roles_Skills.csv"
_CACHE_PATH = _DATA_DIR / "skill_scores.pkl"


# ──────────────────────────────────────────────────────────────────
# SkillIntelligence — inline, no separate file
# ──────────────────────────────────────────────────────────────────

def _normalize_skills(raw) -> Set[str]:
    parts = raw.split(",") if isinstance(raw, str) else list(raw or [])
    return {s.strip().lower() for s in parts if isinstance(s, str) and s.strip()}

#min-max normalisation to 0-1 range, preserving relative importance between skills.
def _minmax(scores: Dict[str, float]) -> Dict[str, float]:
    if not scores:
        return {}
    vals = list(scores.values())
    mn, mx = min(vals), max(vals)
    if math.isclose(mn, mx):
        return {k: 0.0 for k in scores}
    return {k: (v - mn) / (mx - mn) for k, v in scores.items()}

# Compute semantic IDF: rarer skills across all roles get higher scores. Normalised to 0-1.
#N= total number of documents (roles), df= document frequency of skill, idf = log((N+1)/(df+1)) + 1
'''in python in in 80 roles and rust is in 20 roles, then: 
rust is log((100+1)/(20+1)) + 1 = log(4.81) + 1 = 2.57, 
while python is log((100+1)/(80+1)) + 1 = log(1.25) + 1 = 1.22. 
After min-max normalisation, rust would have a higher score than python, 
reflecting its relative rarity and potential value in the job market.'''
def _semantic_idf(docs: List[Set[str]]) -> Dict[str, float]:
    N = len(docs)
    df: Dict[str, int] = {}
    for d in docs:
        for s in d:
            df[s] = df.get(s, 0) + 1
    return _minmax({s: math.log((N + 1) / (c + 1)) + 1 for s, c in df.items()})

'''calculates how frequently each skill appears in the market.Skills that appear in more roles are more in demand. Normalised to 0-1.
Market Demand Calculation Example
docs = [
    {"python", "sql", "ml"},
    {"python", "aws"},
    {"python", "sql"}
]
Step 1: Count how many documents (roles) contain each skill
python → 3
sql    → 2
ml     → 1
aws    → 1
Step 2: Divide by total number of documents (3) to get frequency
python → 3/3 = 1.0
sql    → 2/3 ≈ 0.67
ml     → 1/3 ≈ 0.33
aws    → 1/3 ≈ 0.33
Step 3: Apply min-max normalization (_minmax)
final demand scores scaled between 0 and 1
Result:
{
  "python": 1.0,
  "sql": 0.67,
  "ml": 0.33,
  "aws": 0.33
}
Meaning: python has highest market demand since it appears in most roles.'''

def _market_demand(docs: List[Set[str]]) -> Dict[str, float]:
    total = len(docs)
    demand: Dict[str, int] = {}
    for d in docs:
        for s in d:
            demand[s] = demand.get(s, 0) + 1
    return _minmax({k: v / total for k, v in demand.items()})

'''Graph Importance Calculation(PageRank + Degree Centrality) 
to find important skills based on co-occurrence with other skills. Normalised to 0-1.

Goal: Find important skills based on how frequently they appear together with other skills.
Example:
docs = [
    {"python", "sql", "ml"},
    {"python", "aws"},
    {"python", "sql"}
]
Step 1: Build a skill co-occurrence graph
If two skills appear in the same document, connect them with an edge.
Graph edges created:
python — sql (2 times)
python — ml  (1 time)
sql    — ml  (1 time)
python — aws (1 time)
Step 2: Edge weights represent how often skills appear together.
Step 3: Calculate importance metrics
pagerank → measures influence of a skill in the network
degree_centrality → measures how many connections a skill has
Step 4: Combine both scores
importance = 0.7 * pagerank + 0.3 * degree_centrality
Step 5: Apply min-max normalization to scale scores between 0 and 1
Result (example):
{
  "python": 1.0,
  "sql": 0.65,
  "ml": 0.45,
  "aws": 0.30
}
Meaning:
python is most important because it connects to many other skills frequently.'''

def _graph_importance(docs: List[Set[str]]) -> Dict[str, float]:
    import networkx as nx
    g = nx.Graph()
    for d in docs:
        for a, b in combinations(d, 2):
            if g.has_edge(a, b):
                g[a][b]["weight"] += 1
            else:
                g.add_edge(a, b, weight=1)
    if not g.nodes:
        return {}
    pagerank = nx.pagerank(g, weight="weight")
    degree   = nx.degree_centrality(g)
    return _minmax({s: 0.7 * pagerank.get(s, 0) + 0.3 * degree.get(s, 0) for s in g.nodes})

'''
TF-IDF Distinctiveness Calculation

Goal: Identify how distinctive (unique) each skill is across all documents (roles).

Example:
docs = [
    {"python", "sql", "ml"},
    {"python", "aws"},
    {"python", "sql"}
]

Step 1: Count document frequency (df) → number of documents containing each skill
python → 3
sql    → 2
ml     → 1
aws    → 1

Step 2: Compute IDF (Inverse Document Frequency)
IDF = log((N + 1) / (df + 1)) + 1
where N = total documents = 3

python → log((4)/(4)) + 1 = 1
sql    → log((4)/(3)) + 1 ≈ 1.29
ml     → log((4)/(2)) + 1 ≈ 1.69
aws    → log((4)/(2)) + 1 ≈ 1.69

Step 3: Add IDF values across documents for each skill
python → 1 + 1 + 1 = 3
sql    → 1.29 + 1.29 = 2.58
ml     → 1.69
aws    → 1.69

Step 4: Apply min-max normalization (_minmax) to scale scores between 0 and 1

Result (example):
{
  "ml": 1.0,
  "aws": 1.0,
  "sql": 0.7,
  "python": 0.5
}

Meaning:
Rarer skills (ml, aws) get higher distinctiveness scores,
while common skills (python) get lower scores.
'''

def _tfidf_distinctiveness(docs: List[Set[str]]) -> Dict[str, float]:
    N = len(docs)
    df: Dict[str, int] = {}
    for d in docs:
        for s in d:
            df[s] = df.get(s, 0) + 1
    tfidf: Dict[str, float] = {}
    for d in docs:
        for s in d:
            idf = math.log((N + 1) / (df[s] + 1)) + 1
            tfidf[s] = tfidf.get(s, 0) + idf
    return _minmax(tfidf)


def _compute_skill_scores() -> Dict[str, float]:
    import pandas as pd

    """Build global skill importance scores from CSV."""
    df = pd.read_csv(_CSV_PATH, encoding="latin1").dropna(subset=["Skills"])
    docs = [_normalize_skills(r) for r in df["Skills"]]
    docs = [d for d in docs if d]

    semantic = _semantic_idf(docs)
    demand   = _market_demand(docs)
    graph    = _graph_importance(docs)
    tfidf    = _tfidf_distinctiveness(docs)

    all_skills = set().union(*docs)
    return {
        skill: round(
            0.40 * semantic.get(skill, 0.0)
            + 0.25 * demand.get(skill, 0.0)
            + 0.20 * graph.get(skill, 0.0)
            + 0.15 * tfidf.get(skill, 0.0),
            6,
        )
        for skill in all_skills
    }


# Singleton skill scores — loaded once, cached to disk
_SKILL_SCORES: Dict[str, float] | None = None


def _get_skill_scores() -> Dict[str, float]:
    global _SKILL_SCORES
    if _SKILL_SCORES is not None:
        return _SKILL_SCORES

    # Try disk cache first
    if _CACHE_PATH.exists():
        try:
            with open(_CACHE_PATH, "rb") as f:
                _SKILL_SCORES = pickle.load(f)
            logger.info("Loaded cached skill scores (%d skills)", len(_SKILL_SCORES))
            return _SKILL_SCORES
        except Exception:
            logger.warning("Skill score cache corrupt — recomputing", exc_info=True)

    # Compute from CSV
    if not _CSV_PATH.exists():
        logger.warning("IT_Job_Roles_Skills.csv not found — using uniform BM25 weights")
        _SKILL_SCORES = {}
        return _SKILL_SCORES

    logger.info("Computing skill intelligence scores from CSV...")
    _SKILL_SCORES = _compute_skill_scores()

    try:
        with open(_CACHE_PATH, "wb") as f:
            pickle.dump(_SKILL_SCORES, f)
        logger.info("Skill scores cached (%d skills)", len(_SKILL_SCORES))
    except Exception:
        logger.warning("Could not write skill score cache", exc_info=True)

    return _SKILL_SCORES


def _skill_importance(token: str) -> float:
    """Return importance score for a skill token. Floor at 0.1 so unknowns still count."""
    scores = _get_skill_scores()
    return max(0.1, scores.get(token.replace("_", " "), 0.0))


# ──────────────────────────────────────────────────────────────────
# BM25 helpers
# ──────────────────────────────────────────────────────────────────

#cleans skill names for consistent matching
def _tokenise(skills: List[str]) -> List[str]:
    return [s.lower().replace(" ", "_") for s in skills if s]

# freq    = how many times the skill token appears in the role document
# dl      = document length (total skill tokens in this role)
# avg_dl  = average document length across all roles in the corpus
#           Defaults to dl when called for a single document so the formula
#           still normalises correctly even without a corpus average.
def _bm25_term(freq: int, dl: int, avg_dl: float = 0.0) -> float:
    effective_avg = avg_dl if avg_dl > 0 else dl
    num = freq * (BM25_K1 + 1)
    den = freq + BM25_K1 * (1 - BM25_B + BM25_B * (dl / effective_avg))
    return num / den


# ──────────────────────────────────────────────────────────────────
# Signal 1: Skill Coverage
# ──────────────────────────────────────────────────────────────────

def compute_skill_coverage(user_skill_ids: set, role_skill_ids: set) -> float:
    """matched / total role skills. 0-1."""
    if not role_skill_ids:
        return 0.0
    return len(user_skill_ids & role_skill_ids) / len(role_skill_ids)


# ──────────────────────────────────────────────────────────────────
# Signal 2: DB Importance Weight
# ──────────────────────────────────────────────────────────────────

def compute_importance_weight(
    user_skill_ids: set,
    role_skill_weights: Dict[str, float],
) -> float:
    """Average DB importance_weight of matched skills. 0-1."""
    matched = [role_skill_weights[sid] for sid in user_skill_ids if sid in role_skill_weights]
    return sum(matched) / len(matched) if matched else 0.0


# ──────────────────────────────────────────────────────────────────
# Signal 3: Raw BM25
# ──────────────────────────────────────────────────────────────────

'''
Compute raw BM25 similarity between query tokens (user skills) and
document tokens (role skills).

Process:
1. Calculate document length (number of role skills).
2. Compute term frequency of each skill in the role.
3. For each query skill present in the role, calculate BM25 term score.
4. Sum all BM25 scores.
5. Normalize the score using the maximum possible score so the result
   lies between 0 and 1.

Example:
query_tokens = ["python","ml"]
doc_tokens = ["python","sql","aws"]

Matching term → python
BM25 score calculated for python
ml not present → ignored

Final normalized score ≈ 0.33
'''

def _bm25_raw(query_tokens: List[str], doc_tokens: List[str]) -> float:
    """Pure BM25 — no intelligence weighting."""
    if not query_tokens or not doc_tokens:
        return 0.0
    dl = len(doc_tokens)
    tf: Dict[str, int] = {}
    for t in doc_tokens:
        tf[t] = tf.get(t, 0) + 1
    total = sum(_bm25_term(tf[qt], dl) for qt in query_tokens if qt in tf)
    max_p = _PERFECT_TERM * len(query_tokens)
    return max(0.0, min(1.0, total / max_p)) if max_p else 0.0


# ──────────────────────────────────────────────────────────────────
# Signal 4: BM25 weighted by SkillIntelligence
# ──────────────────────────────────────────────────────────────────


def compute_bm25_intelligence_score(
    user_skill_names: List[str],
    role_skill_names: List[str],
) -> float:
    """
    BM25 score where each matched term is weighted by its global
    market importance (semantic IDF + demand + PageRank + TF-IDF).

    Example:
        user:  ["Python", "Django", "SQL"]
        role:  ["Python", "Django", "AWS", "Docker"]

        "Python" matched → BM25 term × importance(python)  e.g. × 0.91
        "Django" matched → BM25 term × importance(django)  e.g. × 0.74
        "SQL"  not in role → 0
        score = normalised weighted sum → ~0.68
    """
    if not user_skill_names or not role_skill_names:
        return 0.0

    query_tokens = _tokenise(user_skill_names)
    doc_tokens   = _tokenise(role_skill_names)
    dl = len(doc_tokens)

    tf: Dict[str, int] = {}
    for t in doc_tokens:
        tf[t] = tf.get(t, 0) + 1

    total_score  = 0.0
    max_possible = 0.0

    for qt in query_tokens:
        w = _skill_importance(qt)
        max_possible += _PERFECT_TERM * w
        if qt in tf:
            total_score += w * _bm25_term(tf[qt], dl)

    return max(0.0, min(1.0, total_score / max_possible)) if max_possible else 0.0


# ──────────────────────────────────────────────────────────────────
# Re-rank: FAISS top-30 → top-k
# ──────────────────────────────────────────────────────────────────

def re_rank(
    candidate_roles: List[Dict[str, Any]],
    user_skill_ids: set,
    user_skill_names: List[str],
    role_skills_map: Dict[str, List[Dict]],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Re-rank FAISS top-30 → return top_k with scores.

    Formula:
        0.4 × skill_coverage     — fraction of role skills user has
        0.3 × bm25_intelligence  — BM25 weighted by market importance
        0.2 × importance_weight  — DB importance of matched skills
        0.1 × bm25_raw           — pure BM25 baseline
    """
    scored = []

    for role in candidate_roles:
        rid              = str(role.get("id", ""))
        rs_list          = role_skills_map.get(rid, [])
        role_skill_ids   = {str(s["skill_id"]) for s in rs_list}
        role_skill_names = [s.get("skill_name", "") for s in rs_list]
        role_weights     = {str(s["skill_id"]): s.get("importance_weight", 1.0) for s in rs_list}

        cov      = compute_skill_coverage(user_skill_ids, role_skill_ids)
        imp      = compute_importance_weight(user_skill_ids, role_weights)
        bm25_si  = compute_bm25_intelligence_score(user_skill_names, role_skill_names)
        bm25_raw = _bm25_raw(_tokenise(user_skill_names), _tokenise(role_skill_names))

        final = 0.4 * cov + 0.3 * bm25_si + 0.2 * imp + 0.1 * bm25_raw

        scored.append({
            **role,
            "match_score":      round(final,    4),
            "skill_coverage":   round(cov,      4),
            "importance_score": round(imp,      4),
            "bm25_score":       round(bm25_si,  4),
            "bm25_raw_score":   round(bm25_raw, 4),
        })

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored[:top_k]