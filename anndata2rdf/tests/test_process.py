from process import remove_stale_graphs


def _touch(directory, name):
    path = directory / name
    path.write_text("")
    return path


def test_removes_all_other_versions_of_the_dataset(tmp_path):
    old_1 = _touch(tmp_path, "m1__old1.owl")
    old_2 = _touch(tmp_path, "m1__old2.owl")
    current = _touch(tmp_path, "m1__new.owl")
    other_dataset = _touch(tmp_path, "m2__any.owl")

    remove_stale_graphs(str(tmp_path), "m1", str(current))

    assert not old_1.exists()
    assert not old_2.exists()
    assert current.exists()
    assert other_dataset.exists()


def test_keeps_previous_versions_when_current_graph_missing(tmp_path):
    old = _touch(tmp_path, "m1__old.owl")

    remove_stale_graphs(str(tmp_path), "m1", str(tmp_path / "m1__new.owl"))

    assert old.exists()
