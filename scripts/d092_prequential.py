"""Completion-aware replay orchestration; delegates decisions, never changes live policy."""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Build:
    number: int
    commit: str | None
    parent: str | None
    started: float
    finished: float
    source_verified: bool = False


@dataclass(frozen=True)
class Outcome:
    classes: frozenset[str]
    failed: frozenset[str]
    complete_as_published: bool
    reason: str | None = None
    skipped_classes: frozenset[str] = frozenset()

    def __post_init__(self):
        for name in ('classes','failed','skipped_classes'):
            object.__setattr__(self,name,frozenset(getattr(self,name)))
        if not (self.failed | self.skipped_classes)<=self.classes:
            raise ValueError('Outcome references an unknown class')


@dataclass(frozen=True)
class Completed:
    build: Build
    outcome: Outcome


def eligible_history(history,ancestors,started):
    usable={};unstable=set()
    for item in history:
        if item.build.finished>started:raise ValueError('Future completion leaked')
        if not item.build.source_verified or item.build.commit not in ancestors:continue
        if not item.outcome.complete_as_published or item.outcome.skipped_classes:continue
        old=usable.get(item.build.commit)
        if old and (old.outcome.failed!=item.outcome.failed or old.outcome.classes!=item.outcome.classes):
            unstable.add(item.build.commit)
        usable[item.build.commit]=item
    for commit in unstable:usable.pop(commit,None)
    return usable,unstable


def replay(builds, decide, load_truth, persist_decision):
    """Persist each forecast before truth access; release observations on finish only."""
    builds=sorted(builds,key=lambda b:(b.started,b.number))
    if len({b.number for b in builds})!=len(builds):raise ValueError('Duplicate build identity')
    if any(not isfinite(b.started) or not isfinite(b.finished) or b.finished<b.started for b in builds):
        raise ValueError('Invalid CI times')
    pending=[];completed=[];records=[]
    for build in builds:
        ready=[item for item in pending if item.build.finished<=build.started]
        completed.extend(sorted(ready,key=lambda item:(item.build.finished,item.build.number)))
        pending=[item for item in pending if item.build.finished>build.started]
        visible=tuple(completed)
        decision=decide(build,visible)
        persist_decision(build,decision,tuple(item.build.number for item in visible))
        # Current ground truth is available only to the evaluator after persistence.
        truth=load_truth(build)
        if not truth.failed<=truth.classes:raise ValueError('Failure outside the reported universe')
        pending.append(Completed(build,truth))
        records.append({'build':build.number,'commit':build.commit,'decision':decision,
            'visible_completed_builds':[item.build.number for item in visible],
            'recorded_classes':len(truth.classes),'recorded_failed_classes':len(truth.failed),
            'complete_as_published':truth.complete_as_published,'report_limitation':truth.reason})
    return records
