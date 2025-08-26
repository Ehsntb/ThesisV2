// /ned/LightIoTNetwork.ned

package ned;

network LightIoTNetwork
{
    parameters:
        int numSensorNodes = default(5);
    submodules:
        sensor[numSensorNodes]: SensorNode {
            parameters: @display("i=device/wifilaptop");
        }
        gateway: GatewayNode {
            parameters: @display("i=device/router");
        }
        cloud: CloudServer {
            parameters: @display("i=cloud");
        }
        fakeNode: FakeNode {
            parameters: @display("i=block/process");
        }
    connections allowunconnected:
        for i=0..numSensorNodes-1 {
            sensor[i].out --> gateway.in++;
        }
        gateway.out --> cloud.in;
        fakeNode.out --> gateway.in++;
}
