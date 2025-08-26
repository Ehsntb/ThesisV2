package ned;

simple SensorNode
{
    parameters:
        @class(::SensorNode);
        @display("i=device/wifilaptop");
        double sendInterval @unit(s) = default(0.5s);
        string mode = default("Secure"); // Secure | NoSecurity | Replay
        string aesKeyHex = default("00112233445566778899AABBCCDDEEFF");
    gates:
        input  in;
        output out;
}
