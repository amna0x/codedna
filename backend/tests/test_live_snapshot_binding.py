"""Risk features must describe the same immutable snapshot as the selected tests."""
from codedna.git_analysis import extract_changes
from codedna.test_history.features import Dataset, Row
from codedna_java import live


def test_worktree_edit_during_risk_analysis_cannot_change_feature_snapshot(repo, tmp_path, monkeypatch):
    repo.write('src/main/java/a/Core.java', 'package a; public class Core { int value() { return 1; } }')
    repo.write('src/test/java/a/CoreTest.java',
               'package a; import org.junit.jupiter.api.Test; class CoreTest { @Test void checksValue() {} }')
    base = repo.commit('base')
    history = tmp_path/'history.csv'
    Dataset([Row(base, 0, 'a.CoreTest', 0, 1., {name: 0. for name in live.LIVE_FEATURES})],
            list(live.LIVE_FEATURES), [base]).to_csv(history)
    repo.write('src/main/java/a/Core.java', 'package a; public class Core { int value() { return 2; } }')
    revisions = []
    def concurrent_edit(path, old, new):
        repo.write('src/main/java/a/Core.java', 'package a; public class Core { int value() { return 999; } }')
        revisions.append((old, new))
        return extract_changes(path, old, new)
    monkeypatch.setattr(live, 'extract_changes', concurrent_edit)
    def no_model(*args, **kwargs):
        raise ValueError('fixture has insufficient audit history')
    monkeypatch.setattr(live, 'fit_audited', no_model)
    result = live.recommend(repo.path, base, 'WORKTREE', history_csv=history)
    assert len(revisions) == 1
    assert revisions[0] == (result['base_commit'], result['head_commit'])
    snapshot = repo.git('show', result['head_commit']+':src/main/java/a/Core.java')
    assert 'return 2' in snapshot and '999' not in snapshot
    assert '999' in (repo.path/'src/main/java/a/Core.java').read_text()
    assert result['risk']['status'] == 'unvalidated'  # no fabricated acceptance
