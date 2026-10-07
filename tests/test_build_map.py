#!/usr/bin/env python3
"""Unit tests for scripts/build_map.py on small in-memory fixtures.

The import_graph fixtures below mirror the real shapes observed from
scripts/import_graph.py on quest-coder@71bc83a:
  nodes    {"app/api/friends/route.ts": {"lines": 64, "client": False}}
  edges    [["app/api/friends/route.ts", "lib/friends.ts"], ...]
  pyedges  [["runner/browser_run.py", "runner/quest_runner.py"], ...]
  api_calls{"components/party/party.tsx": ["/api/party"], ...}
  rpcs     {"lib/friends-store.ts": ["quest_coder_friend_remove", ...], ...}
  sqlfns   {"quest_coder_read_progress": ["supabase/migrations/2026...sql", ...], ...}

An edge target is not always a map file node: import_graph resolves `.jsx`, `.css` and
`.json` imports too, and writes "UNRESOLVED:<spec>" when it cannot resolve one.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import build_map as bm  # noqa: E402


# ------------------------------------------------------------------ fixtures

LAYERS = [
    {"id": "api", "label": "API routes", "desc": "Next.js route handlers",
     "aliases": ["endpoints"], "globs": ["app/api/**"]},
    {"id": "ui", "label": "Solve screen", "desc": "Code editor and action bar",
     "aliases": ["editor"], "globs": ["components/solve/**", "lib/editor-open.ts"]},
    {"id": "domain", "label": "Game rules", "desc": "Pure game logic",
     "aliases": ["levels"], "globs": ["lib/levels.ts", "lib/game-types.ts"]},
    {"id": "persistence", "label": "Stores & database", "desc": "Supabase or SQLite",
     "aliases": ["db"], "globs": ["lib/progress-store.ts", "supabase/migrations/**"]},
    {"id": "runner", "label": "Runner service", "desc": "Python grader",
     "aliases": ["grader"], "globs": ["runner/*.py"]},
]
FILES = [
    "app/api/friends/route.ts",
    "app/api/packs/[slug]/route.ts",
    "components/solve/action-bar.tsx",
    "lib/editor-open.ts",
    "lib/levels.ts",
    "lib/game-types.ts",
    "lib/progress-store.ts",
    "runner/quest_runner.py",
    "runner/case_worker.py",
    "supabase/migrations/202610020001_quest_coder_auth_progress.sql",
]
EDGES = [
    ["app/api/friends/route.ts", "lib/progress-store.ts"],
    ["app/api/friends/route.ts", "lib/levels.ts"],
    ["app/api/packs/[slug]/route.ts", "lib/levels.ts"],
    ["components/solve/action-bar.tsx", "lib/levels.ts"],
    ["components/solve/action-bar.tsx", "lib/editor-open.ts"],  # same layer: dropped
    ["lib/progress-store.ts", "lib/game-types.ts"],
]
PYEDGES = [["runner/case_worker.py", "runner/quest_runner.py"]]


def layer_of_fixture():
    return bm.assign_layers(FILES, LAYERS)[0]


# -------------------------------------------------------------------- globs

class TestGlobSemantics(unittest.TestCase):
    def test_double_star_is_a_prefix_match_at_any_depth(self):
        self.assertTrue(bm.match("app/api/friends/route.ts", "app/api/**"))
        self.assertTrue(bm.match("app/api/party/boss/route.ts", "app/api/**"))
        self.assertTrue(bm.match("app/api/route.ts", "app/api/**"))
        self.assertFalse(bm.match("app/apifoo/route.ts", "app/api/**"))
        self.assertFalse(bm.match("components/solve/x.tsx", "app/api/**"))

    def test_plain_glob_needs_the_same_number_of_slashes(self):
        self.assertTrue(bm.match("runner/quest_runner.py", "runner/*.py"))
        self.assertFalse(bm.match("runner/tests/test_smoke.py", "runner/*.py"))
        self.assertTrue(bm.match("next.config.ts", "*.config.ts"))
        self.assertFalse(bm.match("app/next.config.ts", "*.config.ts"))

    def test_exact_path_glob(self):
        self.assertTrue(bm.match("lib/levels.ts", "lib/levels.ts"))
        self.assertFalse(bm.match("lib/levels.test.ts", "lib/levels.ts"))

    def test_matching_is_case_sensitive(self):
        self.assertFalse(bm.match("lib/Levels.ts", "lib/levels.ts"))


# ---------------------------------------------------------------- tokenizer

class TestTokenizer(unittest.TestCase):
    def test_splits_camel_case_and_separators(self):
        self.assertEqual(bm.split_words("partyBoss"), ["party", "boss"])
        self.assertEqual(bm.split_words("quest_coder-store.ts"), ["quest", "coder", "store", "ts"])
        self.assertEqual(bm.split_words("QuestRunner"), ["quest", "runner"])

    def test_splits_acronyms_from_the_following_word(self):
        self.assertEqual(bm.split_words("HTTPServer"), ["http", "server"])
        self.assertEqual(bm.split_words("parseJSONBody"), ["parse", "json", "body"])

    def test_an_all_caps_word_stays_one_token(self):
        self.assertEqual(bm.split_words("RUNNER"), ["runner"])
        self.assertEqual(bm.split_words("TOAST_STAGGER_MS"), ["toast", "stagger", "ms"])

    def test_drops_one_char_tokens_and_dedupes_keeping_order(self):
        self.assertEqual(bm.tokens_of("a run Run RUNNER"), ["run", "runner"])
        self.assertEqual(bm.tokens_of("x y z1"), ["z1"])

    def test_a_camel_split_chunk_also_keeps_its_whole_form(self):
        self.assertEqual(bm.tokens_of("partyBoss"), ["party", "boss", "partyboss"])
        self.assertEqual(bm.tokens_of("levels"), ["levels"])

    def test_tokens_span_every_source_text(self):
        toks = bm.tokens_of("Stores & database", "db", "Supabase or SQLite", "supabase/migrations")
        for want in ("stores", "database", "db", "supabase", "sqlite", "migrations"):
            self.assertIn(want, toks)
        self.assertEqual(len(toks), len(set(toks)))

    def test_empty_and_none_are_safe(self):
        self.assertEqual(bm.tokens_of("", None), [])


# --------------------------------------------------------- layer assignment

class TestAssignLayers(unittest.TestCase):
    def test_every_fixture_file_lands_in_exactly_one_layer(self):
        layer_of, unmapped, double = bm.assign_layers(FILES, LAYERS)
        self.assertEqual(unmapped, [])
        self.assertEqual(double, {})
        self.assertEqual(layer_of["app/api/packs/[slug]/route.ts"], "api")
        self.assertEqual(layer_of["runner/case_worker.py"], "runner")
        self.assertEqual(
            layer_of["supabase/migrations/202610020001_quest_coder_auth_progress.sql"],
            "persistence")

    def test_unmapped_files_are_reported_and_sorted(self):
        files = FILES + ["lib/party-lock.ts", "lib/nope.ts"]
        layer_of, unmapped, double = bm.assign_layers(files, LAYERS)
        self.assertEqual(unmapped, ["lib/nope.ts", "lib/party-lock.ts"])
        self.assertNotIn("lib/nope.ts", layer_of)
        self.assertEqual(double, {})

    def test_double_mapped_files_are_reported_with_every_owner(self):
        overlap = LAYERS + [{"id": "extra", "label": "Extra", "desc": "", "aliases": [],
                             "globs": ["lib/levels.ts"]}]
        _, unmapped, double = bm.assign_layers(FILES, overlap)
        self.assertEqual(unmapped, [])
        self.assertEqual(double, {"lib/levels.ts": ["domain", "extra"]})

    def test_first_matching_layer_wins_for_the_assignment(self):
        overlap = LAYERS + [{"id": "extra", "label": "Extra", "desc": "", "aliases": [],
                             "globs": ["lib/levels.ts"]}]
        layer_of, _, _ = bm.assign_layers(FILES, overlap)
        self.assertEqual(layer_of["lib/levels.ts"], "domain")

    def test_empty_layers_are_detectable(self):
        layer_of, _, _ = bm.assign_layers(["lib/levels.ts"], LAYERS)
        used = set(layer_of.values())
        self.assertEqual([l["id"] for l in LAYERS if l["id"] not in used],
                         ["api", "ui", "persistence", "runner"])


# ------------------------------------------------------------------- rollup

class TestRollup(unittest.TestCase):
    def setUp(self):
        self.layer_of = layer_of_fixture()
        self.edges = bm.rollup([tuple(e) for e in EDGES] + [tuple(e) for e in PYEDGES],
                               self.layer_of)
        self.by_pair = {(e["from"], e["to"]): e for e in self.edges}

    def test_weight_counts_every_file_edge_in_the_pair(self):
        self.assertEqual(self.by_pair[("api", "domain")]["weight"], 2)
        self.assertEqual(self.by_pair[("api", "persistence")]["weight"], 1)

    def test_same_layer_edges_are_dropped(self):
        self.assertNotIn(("ui", "ui"), self.by_pair)
        self.assertNotIn(("runner", "runner"), self.by_pair)  # the only py edge is internal

    def test_sample_is_the_first_contributing_file_pair(self):
        self.assertEqual(self.by_pair[("api", "domain")]["sample"],
                         ["app/api/friends/route.ts", "lib/levels.ts"])

    def test_edges_are_typed_and_sorted(self):
        self.assertTrue(all(e["type"] == "import" for e in self.edges))
        self.assertEqual([(e["from"], e["to"]) for e in self.edges],
                         sorted((e["from"], e["to"]) for e in self.edges))

    def test_edges_touching_an_unmapped_file_are_skipped(self):
        partial = dict(self.layer_of)
        del partial["lib/levels.ts"]
        pairs = {(e["from"], e["to"]) for e in bm.rollup([tuple(e) for e in EDGES], partial)}
        self.assertNotIn(("api", "domain"), pairs)
        self.assertIn(("api", "persistence"), pairs)

    def test_py_edges_roll_up_across_layers(self):
        layer_of = dict(self.layer_of)
        layer_of["runner/case_worker.py"] = "ui"
        edges = bm.rollup([("runner/case_worker.py", "runner/quest_runner.py")], layer_of)
        self.assertEqual(edges, [{"from": "ui", "to": "runner", "type": "import", "weight": 1,
                                  "sample": ["runner/case_worker.py", "runner/quest_runner.py"]}])


# -------------------------------------------------------------- typed edges

class TestTypedEdges(unittest.TestCase):
    ROUTES = ["app/api/friends/route.ts", "app/api/packs/[slug]/route.ts",
              "app/api/packs/route.ts", "app/api/party/assist/route.ts",
              "app/api/party/route.ts"]

    def test_route_resolution_prefers_exact_then_dynamic_then_prefix(self):
        self.assertEqual(bm.resolve_api_route("/api/friends", self.ROUTES),
                         "app/api/friends/route.ts")
        self.assertEqual(bm.resolve_api_route("/api/packs", self.ROUTES),
                         "app/api/packs/route.ts")
        self.assertEqual(bm.resolve_api_route("/api/packs/forest", self.ROUTES),
                         "app/api/packs/[slug]/route.ts")
        self.assertEqual(bm.resolve_api_route("/api/packs/", self.ROUTES),
                         "app/api/packs/route.ts")
        self.assertEqual(bm.resolve_api_route("/api/party/assist", self.ROUTES),
                         "app/api/party/assist/route.ts")

    def test_unknown_route_resolves_to_none(self):
        self.assertIsNone(bm.resolve_api_route("/api/private-pack", self.ROUTES))

    def test_http_edges_point_the_caller_layer_at_the_route_layer(self):
        layer_of = layer_of_fixture()
        api_calls = {"components/solve/action-bar.tsx": ["/api/friends", "/api/packs/forest"],
                     "app/api/friends/route.ts": ["/api/friends"]}  # same layer: dropped
        edges, misses = bm.http_edges(api_calls, layer_of, self.ROUTES)
        self.assertEqual(misses, [])
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["from"], "ui")
        self.assertEqual(edges[0]["to"], "api")
        self.assertEqual(edges[0]["type"], "http")
        self.assertEqual(edges[0]["weight"], 2)
        self.assertEqual(edges[0]["sample"], ["components/solve/action-bar.tsx", "/api/friends"])

    def test_http_calls_with_no_route_handler_are_reported_not_dropped_silently(self):
        edges, misses = bm.http_edges(
            {"components/solve/action-bar.tsx": ["/api/private-pack"]},
            layer_of_fixture(), self.ROUTES)
        self.assertEqual(edges, [])
        self.assertEqual(misses, [["components/solve/action-bar.tsx", "/api/private-pack"]])

    def test_rpc_edges_target_the_migration_that_last_defines_the_function(self):
        layer_of = layer_of_fixture()
        layer_of["lib/progress-store.ts"] = "ui"  # force a cross-layer rpc edge
        early = "supabase/migrations/202610020001_quest_coder_auth_progress.sql"
        late = "supabase/migrations/202610040001_quest_coder_rewards_gold_skills.sql"
        layer_of[late] = "persistence"
        sqlfns = {"quest_coder_read_progress": [early, late]}
        edges, misses = bm.rpc_edges(
            {"lib/progress-store.ts": ["quest_coder_read_progress"]}, sqlfns, layer_of)
        self.assertEqual(misses, [])
        self.assertEqual(edges[0]["from"], "ui")
        self.assertEqual(edges[0]["to"], "persistence")
        self.assertEqual(edges[0]["type"], "rpc")
        self.assertEqual(edges[0]["sample"], ["lib/progress-store.ts", late])
        self.assertIn("quest_coder_read_progress", edges[0]["why"])

    def test_rpc_calls_with_no_sql_definition_are_reported(self):
        edges, misses = bm.rpc_edges({"lib/progress-store.ts": ["quest_coder_ghost"]},
                                     {}, layer_of_fixture())
        self.assertEqual(edges, [])
        self.assertEqual(misses, [["lib/progress-store.ts", "quest_coder_ghost"]])

    def test_same_layer_rpc_edges_are_dropped(self):
        layer_of = layer_of_fixture()
        mig = "supabase/migrations/202610020001_quest_coder_auth_progress.sql"
        edges, misses = bm.rpc_edges({"lib/progress-store.ts": ["quest_coder_read_progress"]},
                                     {"quest_coder_read_progress": [mig]}, layer_of)
        self.assertEqual((edges, misses), ([], []))

    def test_manual_edges_keep_their_type_and_why(self):
        spec = {"manual_edges": [
            {"from": "api", "to": "runner", "type": "http", "why": "QUEST_CODER_RUNNER_URL"}]}
        self.assertEqual(bm.manual_edges(spec), [
            {"from": "api", "to": "runner", "type": "http", "weight": 1, "sample": None,
             "why": "QUEST_CODER_RUNNER_URL"}])

    def test_no_manual_edges_is_an_empty_list(self):
        self.assertEqual(bm.manual_edges({}), [])


# --------------------------------------------------------------- file edges

MIGRATION = "supabase/migrations/202610020001_quest_coder_auth_progress.sql"


class TestFileLevelEdges(unittest.TestCase):
    ROUTES = ["app/api/friends/route.ts", "app/api/packs/[slug]/route.ts"]

    def build(self, **kw):
        args = {"import_pairs": [tuple(e) for e in EDGES] + [tuple(e) for e in PYEDGES],
                "api_calls": {}, "route_files": self.ROUTES, "rpcs": {}, "sqlfns": {},
                "layer_of": layer_of_fixture(), "files": FILES}
        args.update(kw)
        return bm.file_level_edges(**args)

    def test_every_import_pair_becomes_a_file_edge(self):
        edges, dropped = self.build()
        self.assertEqual(dropped, [])
        self.assertEqual(len(edges), len(EDGES) + len(PYEDGES))
        self.assertEqual({(e["from"], e["to"]) for e in edges},
                         {tuple(e) for e in EDGES} | {tuple(e) for e in PYEDGES})
        self.assertTrue(all(e["type"] == "import" for e in edges))

    def test_identical_pairs_are_deduped_per_type(self):
        dupes = [("components/solve/action-bar.tsx", "lib/levels.ts")] * 3
        edges, _ = self.build(import_pairs=dupes)
        self.assertEqual(edges, [{"from": "components/solve/action-bar.tsx",
                                  "to": "lib/levels.ts", "type": "import",
                                  "cross_layer": True}])

    def test_the_same_pair_with_two_types_is_kept_twice(self):
        edges, _ = self.build(
            import_pairs=[("components/solve/action-bar.tsx", "app/api/friends/route.ts")],
            api_calls={"components/solve/action-bar.tsx": ["/api/friends"]})
        self.assertEqual([e["type"] for e in edges], ["http", "import"])

    def test_same_layer_edges_are_kept_and_flagged_not_cross_layer(self):
        edges, _ = self.build()
        by_pair = {(e["from"], e["to"]): e for e in edges}
        same = by_pair[("components/solve/action-bar.tsx", "lib/editor-open.ts")]
        self.assertFalse(same["cross_layer"])  # both in `ui`, dropped by the layer rollup
        self.assertFalse(by_pair[("runner/case_worker.py", "runner/quest_runner.py")]
                         ["cross_layer"])
        self.assertTrue(by_pair[("app/api/friends/route.ts", "lib/levels.ts")]["cross_layer"])

    def test_http_edges_point_at_the_resolved_route_file(self):
        edges, dropped = self.build(
            import_pairs=[],
            api_calls={"components/solve/action-bar.tsx": ["/api/friends", "/api/packs/forest"]})
        self.assertEqual(dropped, [])
        self.assertEqual([(e["from"], e["to"], e["type"], e["cross_layer"]) for e in edges], [
            ("components/solve/action-bar.tsx", "app/api/friends/route.ts", "http", True),
            ("components/solve/action-bar.tsx", "app/api/packs/[slug]/route.ts", "http", True)])

    def test_a_fetch_path_with_no_route_handler_makes_no_edge(self):
        edges, dropped = self.build(
            import_pairs=[],
            api_calls={"components/solve/action-bar.tsx": ["/api/private-pack"]})
        self.assertEqual((edges, dropped), ([], []))

    def test_rpc_edges_target_the_migration_that_last_defines_the_function(self):
        late = "supabase/migrations/202610040001_quest_coder_rewards_gold_skills.sql"
        edges, _ = self.build(
            import_pairs=[], files=FILES + [late],
            rpcs={"lib/progress-store.ts": ["quest_coder_read_progress"]},
            sqlfns={"quest_coder_read_progress": [MIGRATION, late]})
        self.assertEqual([(e["from"], e["to"], e["type"]) for e in edges],
                         [("lib/progress-store.ts", late, "rpc")])

    def test_a_same_layer_rpc_edge_is_kept(self):
        edges, _ = self.build(
            import_pairs=[], rpcs={"lib/progress-store.ts": ["quest_coder_read_progress"]},
            sqlfns={"quest_coder_read_progress": [MIGRATION]})
        self.assertEqual(len(edges), 1)  # both files are in `persistence`
        self.assertFalse(edges[0]["cross_layer"])

    def test_an_rpc_with_no_sql_definition_makes_no_edge(self):
        edges, dropped = self.build(
            import_pairs=[], rpcs={"lib/progress-store.ts": ["quest_coder_ghost"]}, sqlfns={})
        self.assertEqual((edges, dropped), ([], []))

    def test_an_endpoint_that_is_not_a_file_node_is_dropped_and_reported(self):
        edges, dropped = self.build(import_pairs=[
            ("lib/levels.ts", "UNRESOLVED:@/lib/missing"),
            ("components/solve/sprite.jsx", "lib/levels.ts"),
            ("app/api/friends/route.ts", "lib/levels.ts"),
        ])
        self.assertEqual([(e["from"], e["to"]) for e in edges],
                         [("app/api/friends/route.ts", "lib/levels.ts")])
        self.assertEqual(dropped, [
            ["lib/levels.ts", "UNRESOLVED:@/lib/missing", "import"],
            ["components/solve/sprite.jsx", "lib/levels.ts", "import"]])

    def test_self_edges_are_skipped(self):
        edges, dropped = self.build(import_pairs=[("lib/levels.ts", "lib/levels.ts")])
        self.assertEqual((edges, dropped), ([], []))

    def test_edges_are_sorted_by_from_then_to_then_type(self):
        edges, _ = self.build()
        self.assertEqual([(e["from"], e["to"], e["type"]) for e in edges],
                         sorted((e["from"], e["to"], e["type"]) for e in edges))

    def test_an_unmapped_endpoint_still_yields_an_edge(self):
        layer_of = layer_of_fixture()
        del layer_of["lib/levels.ts"]  # unmapped: a FAIL elsewhere, but not an edge drop
        edges, dropped = self.build(
            import_pairs=[("app/api/friends/route.ts", "lib/levels.ts")], layer_of=layer_of)
        self.assertEqual(dropped, [])
        self.assertTrue(edges[0]["cross_layer"])


# ---------------------------------------------------------- graph + closure

def edge(a, b, t="import"):
    return {"from": a, "to": b, "type": t, "weight": 1, "sample": None}


class TestCycles(unittest.TestCase):
    def test_an_acyclic_graph_has_no_cycle(self):
        adj = bm.adjacency([edge("a", "b"), edge("b", "c"), edge("a", "c")], ["a", "b", "c"])
        self.assertIsNone(bm.find_cycle(adj))

    def test_a_two_cycle_is_found_and_closes_on_itself(self):
        adj = bm.adjacency([edge("a", "b"), edge("b", "a")], ["a", "b"])
        self.assertEqual(bm.find_cycle(adj), ["a", "b", "a"])

    def test_a_longer_cycle_is_found(self):
        adj = bm.adjacency([edge("a", "b"), edge("b", "c"), edge("c", "a")], ["a", "b", "c"])
        self.assertEqual(bm.find_cycle(adj), ["a", "b", "c", "a"])

    def test_a_cycle_reachable_only_from_a_root_is_still_found(self):
        adj = bm.adjacency([edge("root", "b"), edge("b", "c"), edge("c", "b")],
                           ["root", "b", "c"])
        self.assertEqual(bm.find_cycle(adj), ["b", "c", "b"])

    def test_realtime_edges_are_ignored_so_they_cannot_make_a_cycle(self):
        edges = [edge("party-ui", "social-domain"),
                 edge("social-domain", "party-ui", "realtime")]
        adj = bm.adjacency(edges, ["party-ui", "social-domain"])
        self.assertIsNone(bm.find_cycle(adj))
        self.assertEqual(adj["social-domain"], set())

    def test_non_realtime_typed_edges_do_count_for_cycles(self):
        edges = [edge("api", "runner", "http"), edge("runner", "api")]
        self.assertIsNotNone(bm.find_cycle(bm.adjacency(edges, ["api", "runner"])))

    def test_edges_to_unknown_ids_are_not_added(self):
        adj = bm.adjacency([edge("a", "ghost")], ["a"])
        self.assertEqual(adj, {"a": set()})


class TestReachable(unittest.TestCase):
    def setUp(self):
        self.adj = bm.adjacency([edge("ui", "api"), edge("api", "domain"),
                                 edge("domain", "persistence"), edge("ui", "domain")],
                                ["ui", "api", "domain", "persistence"])

    def test_transitive_upstream(self):
        self.assertEqual(bm.reachable(self.adj, "ui"), ["api", "domain", "persistence"])
        self.assertEqual(bm.reachable(self.adj, "persistence"), [])

    def test_a_cycle_does_not_hang_and_excludes_the_start_itself(self):
        adj = bm.adjacency([edge("a", "b"), edge("b", "a")], ["a", "b"])
        self.assertEqual(bm.reachable(adj, "a"), ["b"])


# --------------------------------------------------------------------- desc

TS_HEADER = '''/**
 * Character level, derived from XP for display only.
 * Reaching level L takes 10 XP.
 */
export const LEVEL_TITLES = ["Squire"];
'''
TS_AFTER_IMPORTS = '''import { useEffect } from "react";
import { PixelSprite } from "../medieval/sprites";

/** Quest title and the Run / Submit action bar above the editor. */
export function ActionBar({ title }: { title: string }) {
  return null;
}
'''
TS_USE_CLIENT = '''"use client";

// Home hub and world map.
import { useState } from "react";
export default function Home() {}
'''
TS_INTERLEAVED = '''"use client";

import { useState } from "react";
import dynamic from "next/dynamic";

// The shared editor only loads when a party fight opens.
const BossTogether = dynamic(() => import("./boss-together"));

import type { StatBarData } from "./ui-bits";
export default function Home() {}
'''
TS_NO_COMMENT = '''import { z } from "zod";

export function parseRunRequest() {}
export const RUN_SCHEMA_VERSION = 3;
export type RunMode = "run" | "submit";
'''
TS_LINE_RUN = '''// B1: Run basic runs in the browser (Pyodide);
// Submit stays on the runner.
import { test } from "@playwright/test";
test.describe("browser run", () => {});
'''
TS_BARE = 'const x = 1;\n'
PY_DOCSTRING = '''#!/usr/bin/env python3
"""CPython execution and grading engine for Quest Coder."""
import os


def run_one_case():
    pass


def _private():
    pass
'''
PY_NO_DOC = '''import os


class CaseWorker:
    pass


def spawn():
    pass
'''
SQL_HEADER = '''-- Quest Coder Supabase progress store.
-- Idempotent: safe to re-run.
create table x ();
'''
SQL_NO_COMMENT = '''create table y ();
create or replace function quest_coder_read_progress() returns void as $$ $$;
'''


class TestExtractDesc(unittest.TestCase):
    def test_block_comment_at_the_top_of_the_file(self):
        self.assertEqual(
            bm.extract_desc(TS_HEADER, "lib/levels.ts"),
            "Character level, derived from XP for display only. Reaching level L takes 10 XP.")

    def test_comment_after_the_import_block_is_the_file_header(self):
        self.assertEqual(bm.extract_desc(TS_AFTER_IMPORTS, "components/solve/action-bar.tsx"),
                         "Quest title and the Run / Submit action bar above the editor.")

    def test_use_client_directive_is_skipped(self):
        self.assertEqual(bm.extract_desc(TS_USE_CLIENT, "app/page.tsx"),
                         "Home hub and world map.")

    def test_a_comment_interleaved_in_the_imports_is_not_the_file_desc(self):
        self.assertEqual(bm.extract_desc(TS_INTERLEAVED, "app/page.tsx"), "exports: Home")

    def test_a_run_of_line_comments_is_joined(self):
        self.assertEqual(bm.extract_desc(TS_LINE_RUN, "tests/e2e/browser-run.spec.ts"),
                         "B1: Run basic runs in the browser (Pyodide); Submit stays on the runner.")

    def test_falls_back_to_the_export_list(self):
        self.assertEqual(bm.extract_desc(TS_NO_COMMENT, "lib/run-contract.ts"),
                         "exports: parseRunRequest, RUN_SCHEMA_VERSION, RunMode")

    def test_no_comment_and_no_exports_is_the_empty_string(self):
        self.assertEqual(bm.extract_desc(TS_BARE, "tests/unit/levels.test.ts"), "")

    def test_only_the_top_of_file_comment_is_used_not_a_later_one(self):
        text = TS_NO_COMMENT + "\n/** A much later comment. */\nexport const late = 1;\n"
        self.assertTrue(bm.extract_desc(text, "lib/run-contract.ts").startswith("exports:"))

    def test_python_docstring_wins_over_the_shebang(self):
        self.assertEqual(bm.extract_desc(PY_DOCSTRING, "runner/quest_runner.py"),
                         "CPython execution and grading engine for Quest Coder.")

    def test_python_falls_back_to_public_defs_and_classes(self):
        self.assertEqual(bm.extract_desc(PY_NO_DOC, "runner/case_worker.py"),
                         "exports: CaseWorker, spawn")

    def test_sql_line_comments(self):
        self.assertEqual(
            bm.extract_desc(SQL_HEADER, "supabase/migrations/202610020001_x.sql"),
            "Quest Coder Supabase progress store. Idempotent: safe to re-run.")

    def test_sql_falls_back_to_created_functions(self):
        self.assertEqual(bm.extract_desc(SQL_NO_COMMENT, "supabase/migrations/202610020001_x.sql"),
                         "exports: quest_coder_read_progress")

    def test_long_export_lists_are_truncated(self):
        text = "".join(f"export const n{i} = {i};\n" for i in range(9))
        self.assertTrue(bm.extract_desc(text, "lib/x.ts").endswith(", …"))

    def test_an_empty_file_is_safe(self):
        self.assertEqual(bm.extract_desc("", "runner/tests/__init__.py"), "")


# -------------------------------------------------------------------- report

class TestCheckReport(unittest.TestCase):
    def _doc(self):
        return {"nodes": [{"idx": "1", "id": "api", "kind": "layer"},
                          {"idx": "2", "id": "ui", "kind": "layer"},
                          {"idx": "3", "id": "lib/levels.ts", "kind": "file"},
                          {"idx": "4", "id": "components/solve/action-bar.tsx",
                           "kind": "file"}],
                "edges": [{"from": "ui", "to": "api", "type": "import"}],
                "file_edges": [{"from": "components/solve/action-bar.tsx",
                                "to": "lib/levels.ts", "type": "import",
                                "cross_layer": True}]}

    def _run(self, doc, **kw):
        args = {"graph": {"unresolved": []}, "unmapped": [], "double": {}, "empty": [],
                "cycle": None, "layer_ids": ["api", "ui"], "spec": {"manual_edges": []},
                "http_misses": [], "rpc_misses": [], "fedge_drops": []}
        args.update(kw)
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "map.json")
            with open(out, "w") as fh:
                json.dump(doc, fh)
            return bm.check(doc, out, **args)

    def test_a_clean_build_passes_every_check(self):
        report = self._run(self._doc())
        self.assertTrue(all(ok for ok, _, _ in report), report)
        self.assertEqual(len(report), 8)

    def test_unresolved_imports_fail(self):
        report = self._run(self._doc(),
                           graph={"unresolved": [["a.ts", "UNRESOLVED:@/missing"]]})
        self.assertFalse(report[0][0])

    def test_unmapped_and_double_mapped_files_fail(self):
        self.assertFalse(self._run(self._doc(), unmapped=["lib/party-lock.ts"])[1][0])
        self.assertFalse(self._run(self._doc(), double={"lib/levels.ts": ["a", "b"]})[2][0])

    def test_empty_layers_fail(self):
        self.assertFalse(self._run(self._doc(), empty=["content"])[3][0])

    def test_a_cycle_fails_and_is_printed(self):
        ok, _, detail = self._run(self._doc(), cycle=["a", "b", "a"])[4]
        self.assertFalse(ok)
        self.assertIn("a -> b -> a", detail)

    def test_a_manual_edge_to_an_unknown_layer_fails(self):
        spec = {"manual_edges": [{"from": "api", "to": "ghost", "type": "data", "why": ""}]}
        self.assertFalse(self._run(self._doc(), spec=spec)[5][0])

    def test_a_dangling_edge_endpoint_fails_the_round_trip(self):
        doc = self._doc()
        doc["edges"].append({"from": "ui", "to": "ghost", "type": "import"})
        self.assertFalse(self._run(doc)[6][0])

    def test_duplicate_idx_values_fail_the_round_trip(self):
        doc = self._doc()
        doc["nodes"][1]["idx"] = "1"
        self.assertFalse(self._run(doc)[6][0])

    def test_a_file_edge_to_an_unknown_id_fails(self):
        doc = self._doc()
        doc["file_edges"].append({"from": "lib/levels.ts", "to": "lib/ghost.ts",
                                  "type": "import", "cross_layer": True})
        ok, _, detail = self._run(doc)[7]
        self.assertFalse(ok)
        self.assertIn("lib/levels.ts -> lib/ghost.ts (import)", detail)
        self.assertTrue(self._run(doc)[6][0])  # layer edges are still fine

    def test_a_file_edge_to_a_layer_id_fails(self):
        doc = self._doc()
        doc["file_edges"].append({"from": "lib/levels.ts", "to": "api",
                                  "type": "import", "cross_layer": True})
        self.assertFalse(self._run(doc)[7][0])

    def test_misses_are_notes_not_failures(self):
        report = self._run(self._doc(), http_misses=[["a.ts", "/api/ghost"]],
                           rpc_misses=[["b.ts", "fn"]],
                           fedge_drops=[["a.ts", "UNRESOLVED:@/x", "import"]])
        self.assertTrue(all(ok for ok, _, _ in report))
        self.assertEqual(len(report), 11)


if __name__ == "__main__":
    unittest.main()
