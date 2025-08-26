package ned;

simple FakeNode
{
    parameters:
        @class(::FakeNode);
        @display("i=block/process");

        bool   enabled        = default(true);
        double replayInterval @unit(s) = default(2.5s);
        int    attackMode     = default(2);          // 1=replay, 2=mitm
        int    replayId       = default(100000);
        int    replayTsUs     = default(500000);     // microseconds
        string replayTagHex   = default("00000000000000000000000000000000");
    gates:
        output out;
}
