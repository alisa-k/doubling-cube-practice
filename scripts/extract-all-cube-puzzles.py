"""Generate offer and response puzzles for every recorded double in 300 matches.

Run inside GNU Backgammon's embedded Python runtime:

    ./scripts/gnubg --tty --quiet --no-rc --python=scripts/extract-all-cube-puzzles.py

Raw matches and checkpoints remain ignored under data/. Only the derived puzzle
records written to public/puzzles.json are intended for the browser and GitHub.
"""

import hashlib
import json
import os
from pathlib import Path


PROJECT_ROOT = Path.cwd()
MATCH_ROOT = PROJECT_ROOT / os.environ.get(
    "BG_MATCH_ROOT", "data/matches/allgammon/recent-300-2026-11-19"
)
OUTPUT = PROJECT_ROOT / os.environ.get("BG_OUTPUT", "public/puzzles.json")
CHECKPOINT = PROJECT_ROOT / os.environ.get(
    "BG_CHECKPOINT", "data/generated/all-cube-puzzles-checkpoint.json"
)
NORMALIZED_DIR = PROJECT_ROOT / "data/generated/all-cube-puzzles-normalized"
MATCH_LIMIT = int(os.environ.get("BG_MATCH_LIMIT", "0"))

ENGINE = "GNU Backgammon 1.08.003"
METHOD = "2-ply cubeful evaluation; pruning on; deterministic; noise 0.000"
GENERATOR_SIGNATURE = "all-recorded-doubles-v1-2ply"
EVAL_CONTEXT = gnubg.evalcontext(1, 2, 1, 1, 0.0)


def answer_from_decision(decision):
    if decision in (0, 7, 16, 17):
        return "double-take"
    if decision in (1, 8, 19, 20):
        return "double-pass"
    if decision in (3, 4, 10, 11):
        return "too-good"
    return "no-double"


def board_for_player(position_id):
    opponent, player = gnubg.positionfromid(position_id)
    points = []

    for index in range(24):
        your_count = player[index]
        opponent_count = opponent[23 - index]
        if your_count and opponent_count:
            raise ValueError(f"Both players occupy point {index + 1}")
        points.append(your_count if your_count else -opponent_count)

    return {
        "points": points,
        "bar": [player[24], opponent[24]],
        "off": [15 - sum(player), 15 - sum(opponent)],
    }


def normalize_match(source_match):
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    normalized_match = NORMALIZED_DIR / source_match.name
    source_lines = source_match.read_text(encoding="utf-8").splitlines(keepends=True)
    normalized_lines = [
        line for line in source_lines if line.strip() != "Crawford game"
    ]
    normalized_match.write_text("".join(normalized_lines), encoding="utf-8")
    return normalized_match


def source_key(source_match):
    relative = source_match.relative_to(PROJECT_ROOT).as_posix()
    digest = hashlib.sha1(relative.encode("utf-8")).hexdigest()[:10]
    timestamp = source_match.stem.split("_", 1)[0]
    return relative, f"{timestamp}-{digest}", timestamp[:8]


def cube_owner_label(owner, player):
    if owner == -1:
        return "centered"
    return "you" if owner == player else "opponent"


def initial_cube_owner(game_info):
    value = game_info.get("initial-cube-owner", "centered")
    return {"centered": -1, "X": 0, "O": 1}.get(value, -1)


def analyze_double(
    source_match,
    source_id,
    source_date,
    match_length,
    game_number,
    record_number,
    record,
    score,
    crawford,
    cube,
    owner,
):
    player = 0 if record["player"] == "X" else 1
    board = gnubg.positionfromid(record["board"])
    cube_info = gnubg.cubeinfo(
        cube, owner, player, match_length, score, crawford, 0
    )
    position_info = gnubg.posinfo(player, 0, 0, 1, (0, 0))
    optimal, no_double, take, drop, decision, recommendation = gnubg.cfevaluate(
        board, cube_info, EVAL_CONTEXT
    )
    answer = answer_from_decision(decision)
    position_id = gnubg.positionid(board)
    match_id = gnubg.matchid(cube_info, position_info)
    source_relative = source_match.relative_to(PROJECT_ROOT).as_posix()
    base_id = f"allgammon-{source_id}-g{game_number:02}-r{record_number:03}"
    source_label = f"Allgammon .mat export · {source_date} · Game {game_number}"
    tags = ["match-play", "2-ply", "recorded-double", "cube-offer", answer]

    if cube > 1:
        tags.append("redouble")

    offer = {
        "id": f"{base_id}-offer",
        "source": source_label,
        "positionId": position_id,
        "matchId": match_id,
        "decisionType": "offer",
        "playerOnRoll": "you",
        "match": {
            "length": match_length,
            "score": [score[player], score[1 - player]],
            "cubeValue": cube,
            "cubeOwner": cube_owner_label(owner, player),
        },
        "board": board_for_player(position_id),
        "answer": {
            "action": answer,
            "note": (
                f"GNUbg says: {recommendation}. Normalized equity — "
                f"no double {no_double:+.3f}; double/take {take:+.3f}; "
                f"double/pass {drop:+.3f}."
            ),
        },
        "analysis": {
            "engine": ENGINE,
            "method": METHOD,
            "recommendation": recommendation,
            "equities": {
                "optimal": round(optimal, 6),
                "noDouble": round(no_double, 6),
                "doubleTake": round(take, 6),
                "doublePass": round(drop, 6),
                "unit": "normalized equity",
            },
            "settings": {
                "plies": 2,
                "cubeful": True,
                "pruning": True,
                "deterministic": True,
                "noise": 0.0,
            },
        },
        "provenance": {
            "sourceFile": source_relative,
            "game": game_number,
            "record": record_number,
            "player": record["player"],
        },
        "tags": tags,
    }

    responder = 1 - player
    response = "take" if take <= drop else "pass"
    response_label = response.capitalize()
    opponent_double_was_wrong = recommendation.startswith(
        ("No double", "No redouble", "Too good", "Never")
    )
    response_note = f"GNUbg says: {response_label}. "
    if opponent_double_was_wrong:
        response_note += (
            "The opponent should not have doubled, but once they did, "
            f"{response_label.lower()} is your best response."
        )
    else:
        response_note += (
            f"After the opponent's double, {response_label.lower()} "
            "is your best response at this score."
        )

    response_board = (board[1], board[0])
    response_position_id = gnubg.positionid(response_board)
    response_cube_info = gnubg.cubeinfo(
        cube, owner, responder, match_length, score, crawford, 0
    )
    response_position_info = gnubg.posinfo(responder, 0, 1, 1, (0, 0))
    response_match_id = gnubg.matchid(
        response_cube_info, response_position_info
    )

    response_puzzle = {
        "id": f"{base_id}-response",
        "source": source_label,
        "positionId": response_position_id,
        "matchId": response_match_id,
        "decisionType": "response",
        "playerOnRoll": "opponent",
        "match": {
            "length": match_length,
            "score": [score[responder], score[player]],
            "cubeValue": cube,
            "offeredCubeValue": cube * 2,
            "cubeOwner": cube_owner_label(owner, responder),
        },
        "board": board_for_player(response_position_id),
        "answer": {"action": response, "note": response_note},
        "analysis": {
            "engine": ENGINE,
            "method": METHOD,
            "recommendation": response_label,
            "offerRecommendation": recommendation,
            "equities": {
                "optimal": round(min(take, drop), 6),
                "noDouble": round(no_double, 6),
                "doubleTake": round(take, 6),
                "doublePass": round(drop, 6),
                "unit": "normalized equity (doubler perspective)",
            },
            "settings": {
                "plies": 2,
                "cubeful": True,
                "pruning": True,
                "deterministic": True,
                "noise": 0.0,
            },
        },
        "provenance": {
            "sourceFile": source_relative,
            "game": game_number,
            "record": record_number,
            "player": "X" if responder == 0 else "O",
            "doubler": record["player"],
        },
        "tags": [
            "match-play",
            "2-ply",
            "recorded-double",
            "cube-response",
            response,
        ],
    }

    return [offer, response_puzzle]


def analyze_match(source_match):
    normalized_match = normalize_match(source_match)
    gnubg.command(f'import mat "{normalized_match}"')
    match = gnubg.match(analysis=0, boards=1, verbose=1)
    match_length = match["match-info"]["match-length"]
    source_relative, source_id, source_date = source_key(source_match)
    puzzles = []

    for game_number, game in enumerate(match["games"], start=1):
        game_info = game["info"]
        score = (game_info["score-X"], game_info["score-O"])
        crawford = int(game_info.get("crawford", False))
        cube = game_info.get("initial-cube", 1)
        owner = initial_cube_owner(game_info)

        for record_number, record in enumerate(game["game"], start=1):
            action = record.get("action")

            if action == "double":
                if not record.get("board"):
                    raise ValueError(
                        f"Double missing board: {source_relative} "
                        f"game {game_number} record {record_number}"
                    )
                puzzles.extend(
                    analyze_double(
                        source_match,
                        source_id,
                        source_date,
                        match_length,
                        game_number,
                        record_number,
                        record,
                        score,
                        crawford,
                        cube,
                        owner,
                    )
                )

            if action == "take":
                cube *= 2
                owner = 0 if record["player"] == "X" else 1
            elif action == "set":
                if "cube" in record:
                    cube = record["cube"]
                if "cube-owner" in record:
                    owner = {"centered": -1, "X": 0, "O": 1}[
                        record["cube-owner"]
                    ]

    return puzzles


def load_checkpoint():
    if not CHECKPOINT.exists():
        return {"signature": GENERATOR_SIGNATURE, "processed": [], "puzzles": []}
    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    if checkpoint.get("signature") != GENERATOR_SIGNATURE:
        raise ValueError("Existing checkpoint belongs to a different generator version")
    return checkpoint


def save_checkpoint(checkpoint):
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(
        json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8"
    )


def main():
    if not MATCH_ROOT.exists():
        raise FileNotFoundError(f"Missing private match directory: {MATCH_ROOT}")

    matches = sorted(MATCH_ROOT.glob("*.mat"))
    if MATCH_LIMIT:
        matches = matches[:MATCH_LIMIT]
    if not matches:
        raise FileNotFoundError(f"No .mat matches found under {MATCH_ROOT}")

    checkpoint = load_checkpoint()
    processed = set(checkpoint["processed"])
    total = len(matches)

    for index, source_match in enumerate(matches, start=1):
        source_relative = source_match.relative_to(PROJECT_ROOT).as_posix()
        if source_relative in processed:
            print(f"[{index}/{total}] already analyzed {source_match.name}", flush=True)
            continue

        print(f"[{index}/{total}] analyzing {source_match.name}", flush=True)
        puzzles = analyze_match(source_match)
        checkpoint["puzzles"].extend(puzzles)
        checkpoint["processed"].append(source_relative)
        save_checkpoint(checkpoint)
        print(
            f"[{index}/{total}] added {len(puzzles)} puzzles; "
            f"total {len(checkpoint['puzzles'])}",
            flush=True,
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(checkpoint["puzzles"], indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Wrote {len(checkpoint['puzzles'])} puzzles from "
        f"{len(checkpoint['processed'])} matches to {OUTPUT}",
        flush=True,
    )


main()
