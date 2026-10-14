"""Command-line entry point: `uv run popsim <command>`."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="popsim", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("fetch", help="download tier-A sources into data/raw and pin their checksums")
    p.add_argument("ids", nargs="*", help="source ids (default: all)")
    p.add_argument("--update", action="store_true", help="accept upstream changes to pinned files")

    p = sub.add_parser("fetch-cbs-ss", help="run the CBS Social Survey table-generator queries (headless browser)")
    p.add_argument("ids", nargs="*", help="query ids (default: all specs in data/manual/cbs_ss/queries)")

    p = sub.add_parser("discover", help="list the tables of a CBS Statistical Abstract chapter")
    p.add_argument("year", type=int)
    p.add_argument("folder", help="chapter folder, e.g. 2.shnatonpopulation")
    p.add_argument("prefix", help="table prefix, e.g. st02")
    p.add_argument("--max", type=int, default=40)

    p = sub.add_parser("links", help="list file links on a JavaScript-rendered page (headless browser)")
    p.add_argument("url")
    p.add_argument("--pattern", default=r"\.(xlsx?|zip|csv|pdf)(\?|$)")

    p = sub.add_parser("build", help="extract raw data, estimate every node, write model files")
    p.add_argument("steps", nargs="*", help="only these steps (default: all, in order)")

    p = sub.add_parser("export", help="compile model/ into model/build/model.json")
    p.add_argument("--check", action="store_true", help="only verify that the bundle's hash matches model/build/model.sha256")

    p = sub.add_parser("seed", help="derive the default assembly seed from the drand beacon at a fixed time")
    p.add_argument("--at", required=True, help="ISO time, e.g. 2026-10-13T00:00:00Z")

    p = sub.add_parser("assembly", help="draw the published default assembly (TypeScript sampler)")
    p.add_argument("--seed", type=int, default=None, help="override the recorded beacon seed")
    p.add_argument("--check", action="store_true", help="only verify that the committed assembly is reproduced exactly")

    p = sub.add_parser("docs", help="regenerate SOURCES.md and the generated blocks of the methodology docs")
    p.add_argument("--check", action="store_true", help="fail instead of writing if anything is out of date")

    p = sub.add_parser("validate", help="compare a large model sample with official totals")
    p.add_argument("--n", type=int, default=1_000_000)
    p.add_argument("--seed", type=int, default=1)

    args = parser.parse_args(argv)

    if args.cmd == "build":
        from .estimate import run_steps

        run_steps(args.steps or None)
    elif args.cmd == "export":
        from .export.bundle import check_bundle, write_bundle

        if args.check:
            ok, digest, recorded = check_bundle()
            print(f"bundle sha256 {digest} {'matches' if ok else 'DIFFERS from'} model.sha256 ({recorded})")
            return 0 if ok else 1
        print(f"wrote {write_bundle()}")
    elif args.cmd == "seed":
        from .assembly import seed_from_drand

        rec = seed_from_drand(args.at)
        print(f"drand round {rec['round']} at {rec['time']}: seed {rec['seed']}")
    elif args.cmd == "assembly":
        from .assembly import check_assembly, make_assembly

        if args.check:
            ok = check_assembly()
            print("published assembly reproduced exactly" if ok else "published assembly NOT reproduced")
            return 0 if ok else 1
        data = make_assembly(args.seed)
        print(f"assembly: {len(data['people'])} people, seed {data['seed']}, model {data['model_version']}")
    elif args.cmd == "docs":
        from .export.docs import update_docs

        problems = update_docs(check=args.check)
        for p_ in problems:
            print(f"  ✗ {p_}")
        if problems:
            return 1
        print("docs up to date" if args.check else "docs regenerated")
    elif args.cmd == "validate":
        from .validate.run import validate

        return 0 if validate(n=args.n, seed=args.seed) else 1
    elif args.cmd == "fetch":
        from .fetch.base import fetch

        fetch(args.ids or None, update=args.update)
    elif args.cmd == "fetch-cbs-ss":
        from .fetch.cbs_generator import run_queries

        run_queries(args.ids or None)
    elif args.cmd == "links":
        from .fetch.browser import rendered_links

        for text, href in rendered_links(args.url, args.pattern):
            print(f"{text[:70]}\t{href}")
    elif args.cmd == "discover":
        from .fetch.discover import discover

        discover(args.year, args.folder, args.prefix, max_n=args.max)
    return 0


if __name__ == "__main__":
    sys.exit(main())
