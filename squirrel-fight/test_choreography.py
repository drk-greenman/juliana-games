from choreography import PLAYER, RIVAL, ActorState, Timeline, sample


def test_empty_timeline_samples_neutral():
    timeline = Timeline(hp_start={PLAYER: 60, RIVAL: 60}, total_ms=0)
    frame = sample(timeline, 0)
    assert frame.actors[PLAYER] == ActorState()
    assert frame.actors[RIVAL] == ActorState()
    assert frame.hp == {PLAYER: 60, RIVAL: 60}
    assert frame.caption == ""
