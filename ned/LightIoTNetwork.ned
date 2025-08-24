package ned;

network LightIoTNetwork
{
    parameters:
        int numSensorNodes = default(5);
    submodules:
        sensor[numSensorNodes]: SensorNode {
            parameters:
                @display("i=device/wifilaptop");
        }
        gateway: GatewayNode {
            @display("i=device/router");
        }
        cloud: CloudServer {
            @display("i=cloud");
        }
        fakeNode: FakeNode {
            @display("i=block/process");
        }
    connections allowunconnected:
        for i=0..numSensorNodes-1 {
            sensor[i].out --> gateway.in++;
        }
        gateway.out --> cloud.in;
        fakeNode.out --> gateway.in++;
}
