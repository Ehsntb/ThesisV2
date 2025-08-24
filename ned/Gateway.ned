package ned;

simple GatewayNode
{
    parameters:
        @class(::GatewayNode);
        @display("i=device/router");

        // Energy & timing
        bool   securityEnabled = default(true);
        double hmacWindow @unit(s) = default(1s);
        double procDelay  @unit(s) = default(0s);
        double costForward_mJ = default(5);
        double costVerify_mJ  = default(5);
        double batteryInit_mJ = default(5000);

        // Ablation toggles
        bool checkHmac      = default(true);
        bool checkFreshness = default(true);
        bool checkDuplicate = default(true);

        // Duplicate method: "set" | "bloom"
        string duplicateMethod = default("set");
        int    bloomBits    = default(16384); // ~2KB
        int    bloomHashes  = default(3);

    gates:
        input  in[];
        output out;
}
