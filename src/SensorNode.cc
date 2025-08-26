// /src/SensorNode.cc

#include <omnetpp.h>
#include <vector>
#include <cstdint>
#include <cmath>
#include "LightIoTMessage_m.h"
#include "crypto/crypto_utils.h"
#include "crypto/cmac.h"

using namespace omnetpp;

class SensorNode : public cSimpleModule {
  private:
    cMessage *sendEvent = nullptr;
    int msgId = 0;
    int baseOffset = 0;
    double batteryCapacity = 5000.0;
    double consumptionPerMessage = 20.0;
    std::string aesKeyHex;

    inline int64_t now_us() const {
        double d = SIMTIME_DBL(simTime());
        return (int64_t) llround(d * 1e6);
    }

  protected:
    virtual void initialize() override {
        baseOffset = (getIndex() + 1) * 100000;
        aesKeyHex = par("aesKeyHex").stdstringValue();
        sendEvent = new cMessage("sendEvent");
        scheduleAt(simTime() + uniform(0.5, 1.5), sendEvent);
    }

    virtual void handleMessage(cMessage *msg) override {
        if (batteryCapacity < consumptionPerMessage) {
            EV << "[SensorNode] Battery depleted. Node stopped.\n";
            delete msg; sendEvent = nullptr; return;
        }

        auto *packet = new LightIoTMessage("SensorData");
        int id = baseOffset + (msgId++);
        packet->setId(id);

        int64_t ts_us = now_us();
        packet->setTimestamp(SimTime(ts_us, SIMTIME_US));

        // CMAC over (id || ts_us)
        std::vector<uint8_t> keyBytes;
        if (!hexToBytes(aesKeyHex, keyBytes) || keyBytes.size()!=16) {
            EV << "[SensorNode] Invalid aesKeyHex; expected 16-byte hex.\n";
            keyBytes.assign(16, 0);
        }
        std::vector<uint8_t> mbytes;
        packIdTsBigEndian(id, ts_us, mbytes);
        uint8_t tag[16];
        aes128_cmac(keyBytes.data(), mbytes.data(), mbytes.size(), tag);
        packet->setMacHex(bytesToHex(tag, 16));

        send(packet, "out");
        batteryCapacity -= consumptionPerMessage;
        scheduleAt(simTime() + uniform(0.9, 1.1), sendEvent);
    }

    virtual void finish() override {
        double percent = (batteryCapacity / 5000.0) * 100;
        EV << "[SensorNode] Energy Remaining: " << batteryCapacity
           << " mJ (" << percent << "%)\n";
        if (sendEvent != nullptr) { cancelAndDelete(sendEvent); sendEvent=nullptr; }
        recordScalar("Sensor_BatteryRemaining_mJ", batteryCapacity);
    }
};

Define_Module(SensorNode);