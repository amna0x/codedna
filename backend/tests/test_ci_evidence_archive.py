"""Immutable/resumable CI recording, using temporary repositories and no network."""
import importlib
import json
from pathlib import Path

import pytest


@pytest.fixture
def archive_module(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2]/'scripts'))
    return importlib.import_module('ci_evidence_archive')


def test_resume_does_not_redownload_or_overwrite_report(repo,archive_module):
    module=archive_module;store=repo.path/'archive';archive=module.Archive(store)
    data={'builds':[{'number':1,'url':module.JOB+'1/','building':False,'duration':10,
        'actions':[{'lastBuiltRevision':{'SHA1':'a'*40}}]}]}
    calls=[]
    def get(url):
        calls.append(url)
        return 200,json.dumps(data).encode() if '/testReport/' not in url else b'{"failed":1}',None
    first=module.collect(archive,get)
    second=module.collect(module.Archive(store),get)
    assert first['new_report_observations']==1 and second['already_archived']==1
    assert sum('/testReport/' in url for url in calls)==1
    reports=[e for e in archive.events() if e['role']=='report']
    assert len(reports)==1 and reports[0]['bound_commit']=='a'*40


def test_new_version_and_missing_recovery_preserve_every_observation(repo,archive_module):
    module=archive_module;archive=module.Archive(repo.path/'archive');url=module.JOB+'1/testReport/api/json'
    archive.record(url,404,b'','report','a'*40)
    failed=archive.record(url,200,b'{"failed":1}','report','a'*40)
    passed=archive.record(url,200,b'{"failed":0}','report','a'*40)
    assert failed['object_sha256']!=passed['object_sha256']
    assert len(archive.events())==3
    assert all((archive.path/'objects'/(e['object_sha256']+'.gz')).exists() for e in archive.events())


def test_archive_cannot_silently_switch_jobs(repo,archive_module):
    module=archive_module;store=repo.path/'archive';module.Archive(store)
    with pytest.raises(ValueError,match='another CI job'):
        module.Archive(store,'https://ci-builds.apache.org/job/Other/')
