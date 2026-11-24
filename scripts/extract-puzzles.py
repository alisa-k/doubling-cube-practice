"""Extract the first curated cube-practice set from an analyzed GNUbg match.

Run this inside GNU Backgammon's embedded Python runtime:

    ./scripts/gnubg --tty --quiet --no-rc --python=scripts/extract-puzzles.py

The normalized match and analyzed SGF are private generated intermediates. Only
the compact puzzle records written to public/puzzles.json reach the browser app.
"""

import json
from pathlib import Path


PROJECT_ROOT = Path.cwd()
SOURCE_RELATIVE = (
    "data/matches/allgammon/recent-2026-11-18/"
    "20261118T021008Z_d8b5bc53-2d53-4553-8005-0c196e59dfac.mat"
)
ANALYZED_MATCH = PROJECT_ROOT / "data/generated/pilot-analysis.sgf"
NORMALIZED_MATCH = PROJECT_ROOT / "data/generated/pilot-normalized.mat"
OUTPUT = PROJECT_ROOT / "public/puzzles.json"

# A deliberately small, varied pilot set. Tuple values are (game, record).
SELECTED_OFFERS = [
    (2, 20),  # close no double / take
    (1, 15),  # missed double / take
    (1, 28),  # double / pass
    (6, 6),   # too good to double
    (2, 24),  # close double / take
    (3, 36),  # no redouble
    (2, 30),  # double / pass
    (3, 38),  # missed redouble / pass
]

# Actual double records, reoriented so the user is answering the offer.
SELECTED_RESPONSES = [
    (2, 42),  # clear take after an incorrect double
    (1, 28),  # pass
    (4, 9),   # take after an incorrect double
    (3, 29),  # pass
]

PUZZLE_ORDER = [
    ("offer", (2, 20)),
    ("response", (2, 42)),
    ("offer", (1, 15)),
    ("response", (1, 28)),
    ("offer", (1, 28)),
    ("offer", (6, 6)),
    ("response", (4, 9)),
    ("offer", (2, 24)),
    ("offer", (3, 36)),
    ("response", (3, 29)),
    ("offer", (2, 30)),
    ("offer", (3, 38)),
]

ENGINE = "GNU Backgammon 1.08.003"
METHOD = "2-ply cubeful evaluation; pruning on; deterministic; noise 0.000"
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


def main():
    source_match = PROJECT_ROOT / SOURCE_RELATIVE
    if not source_match.exists():
        raise FileNotFoundError(f"Missing private source match: {source_match}")

    NORMALIZED_MATCH.parent.mkdir(parents=True, exist_ok=True)
    source_lines = source_match.read_text(encoding="utf-8").splitlines(keepends=True)
    normalized_lines = [
        line for line in source_lines if line.strip() != "Crawford game"
    ]
    NORMALIZED_MATCH.write_text("".join(normalized_lines), encoding="utf-8")

    gnubg.command("set analysis moves off")
    gnubg.command("set analysis luck off")
    gnubg.command("set analysis cube on")
    gnubg.command(f'import mat "{NORMALIZED_MATCH}"')
    gnubg.command("analyze match")
    gnubg.command(f'save match "{ANALYZED_MATCH}"')

    match = gnubg.match(analysis=1, boards=1, verbose=1)
    match_length = match["match-info"]["match-length"]
    selected_offers = set(SELECTED_OFFERS)
    selected_responses = set(SELECTED_RESPONSES)
    selected = selected_offers | selected_responses
    extracted = {}

    for game_number, game in enumerate(match["games"], start=1):
        score = (game["info"]["score-X"], game["info"]["score-O"])
        crawford = int(game["info"].get("crawford", False))
        cube = game["info"].get("initial-cube", 1)
        owner = -1

        for record_number, record in enumerate(game["game"], start=1):
            location = (game_number, record_number)
            action = record.get("action")

            if location in selected:
                if not record.get("board") or action not in ("move", "double"):
                    raise ValueError(f"Selected record {location} is not a cube decision")
                if location in selected_responses and action != "double":
                    raise ValueError(f"Selected response {location} is not a double")

                player = 0 if record["player"] == "X" else 1
                board = gnubg.positionfromid(record["board"])
                cube_info = gnubg.cubeinfo(
                    cube, owner, player, match_length, score, crawford, 0
                )
                position_info = gnubg.posinfo(player, 0, 0, 1, (0, 0))
                evaluation = gnubg.cfevaluate(board, cube_info, EVAL_CONTEXT)
                optimal, no_double, take, drop, decision, recommendation = evaluation
                record_analysis = record.get("analysis", {})

                if location in selected_offers:
                    answer = answer_from_decision(decision)
                    relative_score = [score[player], score[1 - player]]
                    cube_owner = (
                        "centered"
                        if owner == -1
                        else "you"
                        if owner == player
                        else "opponent"
                    )
                    position_id = gnubg.positionid(board)
                    match_id = gnubg.matchid(cube_info, position_info)
                    tags = ["match-play", "2-ply", "cube-offer", answer]

                    if cube > 1:
                        tags.append("redouble")
                    if record_analysis.get("cube-skill"):
                        tags.append("match-cube-error")

                    extracted[("offer", location)] = {
                        "id": f"allgammon-20261118-g{game_number:02}-r{record_number:03}",
                        "source": f"Allgammon .mat export · Game {game_number}",
                        "positionId": position_id,
                        "matchId": match_id,
                        "decisionType": "offer",
                        "playerOnRoll": "you",
                        "match": {
                            "length": match_length,
                            "score": relative_score,
                            "cubeValue": cube,
                            "cubeOwner": cube_owner,
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
                            "sourceFile": SOURCE_RELATIVE,
                            "game": game_number,
                            "record": record_number,
                            "player": record["player"],
                        },
                        "tags": tags,
                    }

                if location in selected_responses:
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
                    response_position_info = gnubg.posinfo(
                        responder, 0, 1, 1, (0, 0)
                    )
                    response_match_id = gnubg.matchid(
                        response_cube_info, response_position_info
                    )
                    response_score = [score[responder], score[player]]
                    response_cube_owner = (
                        "centered"
                        if owner == -1
                        else "you"
                        if owner == responder
                        else "opponent"
                    )

                    extracted[("response", location)] = {
                        "id": f"allgammon-20261118-g{game_number:02}-r{record_number:03}-response",
                        "source": f"Allgammon .mat export · Game {game_number}",
                        "positionId": response_position_id,
                        "matchId": response_match_id,
                        "decisionType": "response",
                        "playerOnRoll": "opponent",
                        "match": {
                            "length": match_length,
                            "score": response_score,
                            "cubeValue": cube,
                            "offeredCubeValue": cube * 2,
                            "cubeOwner": response_cube_owner,
                        },
                        "board": board_for_player(response_position_id),
                        "answer": {
                            "action": response,
                            "note": response_note,
                        },
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
                            "sourceFile": SOURCE_RELATIVE,
                            "game": game_number,
                            "record": record_number,
                            "player": "X" if responder == 0 else "O",
                            "doubler": record["player"],
                        },
                        "tags": ["match-play", "2-ply", "cube-response", response],
                    }

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

    missing_offers = selected_offers.difference(
        location for kind, location in extracted if kind == "offer"
    )
    missing_responses = selected_responses.difference(
        location for kind, location in extracted if kind == "response"
    )
    if missing_offers or missing_responses:
        raise ValueError(
            f"Selected records were not found: offers={sorted(missing_offers)}, "
            f"responses={sorted(missing_responses)}"
        )

    puzzles = [extracted[key] for key in PUZZLE_ORDER]
    OUTPUT.write_text(json.dumps(puzzles, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(puzzles)} puzzles to {OUTPUT}")


main()
