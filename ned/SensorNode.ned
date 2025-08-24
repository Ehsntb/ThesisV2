package ned;

simple SensorNode
{
    parameters:
        @class(::SensorNode);
        double sendInterval @unit(s) = default(0.5s);
        string mode = default("Secure"); // Secure | NoSecurity | Replay
        @display("i=device/wifilaptop");
    gates:
        input  in;
        output out;
}
