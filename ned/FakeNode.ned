package ned;

simple FakeNode
{
    parameters:
        @class(::FakeNode);
        bool   enabled = default(true);
        int    attackMode = default(1);     // 1=Replay, 2=MITM
        double replayInterval @unit(s) = default(2.5s);
        @display("i=block/process");
    gates:
        output out;
}
