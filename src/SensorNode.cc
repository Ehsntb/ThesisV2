// /src/SensorNode.cc

#include <omnetpp.h>
#include <vector>
#include <cstdint>
#include <cmath>
#include <string>
#include "LightIoTMessage_m.h"
#include "crypto/crypto_utils.h"
#include "crypto/cmac.h"
using namespace omnetpp;

class SensorNode : public cSimpleModule {
  private:
    cMessage *sendEvent = nullptr;
    int seq = 0;
    int baseId = 0;

    std::string aesKeyHex;
    std::string mode; // "Secure" | "NoSecurity" | "Replay"
    simtime_t sendInterval = 0.5;

    // انرژی مدل ساده (اختیاری)
    double batteryCapacity = 5000.0;
    double consumptionPerMessage = 20.0;

    inline int64_t now_us() const {
        return (int64_t) llround(SIMTIME_DBL(simTime()) * 1e6);
    }

  protected:
    virtual void initialize() override {
        baseId = (getIndex() + 1) * 100000;
        aesKeyHex = par("aesKeyHex").stdstringValue();
        mode = par("mode").stdstringValue();
        sendInterval = par("sendInterval");

        sendEvent = new cMessage("sendEvent");
        scheduleAt(simTime() + uniform(0.5, 1.5), sendEvent);
    }

    virtual void handleMessage(cMessage *msg) override {
        if (batteryCapacity < consumptionPerMessage) {
            EV << "[SensorNode] Battery depleted. Node stopped.\n";
            delete msg; sendEvent = nullptr; return;
        }

        auto *packet = new LightIoTMessage("SensorData");
        int id = baseId + (++seq);
        packet->setId(id);
        packet->setSrc(getIndex());
        packet->setSeq(seq);

        int64_t ts_us = now_us();
        packet->setTimestamp(SimTime(ts_us, SIMTIME_US));

        // اگر NoSecurity باشد، MAC را خالی می‌گذاریم
        if (mode == "NoSecurity") {
            packet->setMacHex("");
        } else {
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
        }

        send(packet, "out");
        batteryCapacity -= consumptionPerMessage;
        scheduleAt(simTime() + uniform(SIMTIME_DBL(sendInterval)*0.9, SIMTIME_DBL(sendInterval)*1.1), sendEvent);
    }

    virtual void finish() override {
        recordScalar("Sensor_EnergyRemaining_mJ", batteryCapacity);
        if (sendEvent) { cancelAndDelete(sendEvent); sendEvent=nullptr; }
    }
};

Define_Module(SensorNode);