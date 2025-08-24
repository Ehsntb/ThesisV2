package ned;
simple GatewayNode
{
    parameters:
        @class(::GatewayNode);
        @display("i=device/router");
        bool securityEnabled = default(true);
        double hmacWindow @unit(s) = default(1s);
        double procDelay @unit(s) = default(0s);
        double costForward_mJ = default(5);
        double costVerify_mJ  = default(5);
        double batteryInit_mJ = default(5000);
        bool checkHmac      = default(true);
        bool checkFreshness = default(true);
        bool checkDuplicate = default(true);
    gates:
        input  in[];
        output out;
}
