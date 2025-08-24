#include <omnetpp.h>
#include "LightIoTMessage_m.h"
using namespace omnetpp;

class SensorNode : public cSimpleModule {
  private:
    cMessage *sendEvent = nullptr;
    int msgId = 0, baseOffset = 0;
    double batteryCapacity = 5000.0;
    double consumptionPerMessage = 20.0;
  protected:
    virtual void initialize() override {
        baseOffset = (getIndex() + 1) * 100000;
        sendEvent = new cMessage("sendEvent");
        scheduleAt(simTime() + uniform(0.5, 1.5), sendEvent);
    }
    virtual void handleMessage(cMessage *msg) override {
        if (batteryCapacity < consumptionPerMessage) { delete msg; sendEvent=nullptr; return; }
        auto *packet = new LightIoTMessage("SensorData");
        packet->setId(baseOffset + (msgId++));
        packet->setHmac("VALID");
        packet->setTimestamp(simTime());
        send(packet, "out");
        batteryCapacity -= consumptionPerMessage;
        scheduleAt(simTime() + uniform(0.9, 1.1), sendEvent);
    }
    virtual void finish() override {
        recordScalar("Sensor_BatteryRemaining_mJ", batteryCapacity);
        if (sendEvent) { cancelAndDelete(sendEvent); sendEvent=nullptr; }
    }
};
Define_Module(SensorNode);
