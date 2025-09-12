    // /ned/GatewayNode.ned

    package ned;

    simple GatewayNode
    {
        parameters:
            @class(::GatewayNode);
            @display("i=device/router");

            // security toggles
            bool   securityEnabled = default(true);
            bool   checkHmac      = default(true);
            bool   checkFreshness = default(true);
            bool   checkDuplicate = default(true);

            // permutation of stages: H=HMAC, F=Freshness, B=Duplicate stage (set/bloom/sbf)
            // examples: "HFB" (default), "HBF", "FHB", "FBH", "BHF", "BFH"
            string stageOrder = default("HFB");

            // duplicate method: "set" | "bloom" | "sbf"
            string duplicateMethod = default("set");

            // Bloom (standard)
            int    bloomBits    = default(16384);
            int    bloomHashes  = default(3);

            // Stable Bloom Filter (SBF)
            int    sbfBits      = default(16384);
            int    sbfHashes    = default(3);
            double sbfDecay     = default(0.02);

            // energy & timing
            double costForward_mJ = default(5);
            double costVerify_mJ  = default(5);
            double batteryInit_mJ = default(5000);
            double procDelay @unit(s) = default(0s);
            double hmacWindow @unit(s) = default(1s);

            // crypto
            string aesKeyHex = default("00112233445566778899AABBCCDDEEFF");
        gates:
            input  in[];
            output out;
    }
