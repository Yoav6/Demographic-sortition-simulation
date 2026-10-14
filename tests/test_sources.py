"""Every source referenced by the model exists, and every downloaded file is pinned."""

from popsim import paths
from popsim.model_spec import load_spec
from popsim.sources import load_lock, load_sources


def test_registry_parses():
    assert load_sources()


def test_dag_sources_exist():
    srcs = load_sources()
    for node in load_spec().nodes:
        for sid in node.raw.get("sources", []):
            assert sid in srcs, f"{node.id} cites unknown source {sid}"


def test_downloaded_files_are_pinned():
    lock = load_lock()
    for src in load_sources().values():
        for f in src.files:
            if src.raw_path(f).exists():
                assert f.path in lock.get(src.id, {}), f"{src.id}/{f.path} downloaded but not pinned"


def test_manual_files_exist():
    for src in load_sources().values():
        for m in src.manual:
            assert (paths.MANUAL / m).exists(), f"{src.id}: missing data/manual/{m}"
