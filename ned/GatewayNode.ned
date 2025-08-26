package ned;

simple GatewayNode
{
    parameters:
        @class(::GatewayNode);
        @display("i=device/router");

        // security & crypto
        string aesKeyHex = default("00112233445566778899AABBCCDDEEFF");
        bool   securityEnabled = default(true);
        bool   checkHmac      = default(true);
        bool   checkFreshness = default(true);
        bool   checkDuplicate = default(true);

        // duplicate method
        string duplicateMethod = default("set"); // "set" or "bloom"
        int    bloomBits    = default(16384);
        int    bloomHashes  = default(3);

        // energy & timing
        double costForward_mJ = default(5);
        double costVerify_mJ  = default(5);
        double batteryInit_mJ = default(5000);
        double procDelay @unit(s) = default(0s);
        double hmacWindow @unit(s) = default(1s);
    gates:
        input  in[];
        output out;
}
