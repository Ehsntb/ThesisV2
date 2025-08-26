// /src/FakeNode.cc
#include <omnetpp.h>
#include <cstring>
#include "LightIoTMessage_m.h"

using namespace omnetpp;

class FakeNode : public cSimpleModule {
  private:
    cMessage *attackEvent = nullptr;
    bool enabled = true;
    int mode = 2;         // 1 = Replay, 2 = MITM
    simtime_t interval = 2.5;

    // Replay fields (fill from a captured legit packet if you want a true replay)
    int replayId = 100000;
    long replayTsUs = 500000; // 0.5s
    std::string replayTagHex = "00000000000000000000000000000000";

    int attacksSent = 0;

  protected:
    virtual void initialize() override {
        enabled = par("enabled").boolValue();
        interval = par("replayInterval");

        cPar& p = par("attackMode");
        if (p.isNumeric()) mode = p.intValue();
        else {
            const char* s = p.stringValue();
            if (!strcasecmp(s,"replay")) mode = 1;
            else if (!strcasecmp(s,"mitm")) mode = 2;
            else mode = 2;
        }

        if (hasPar("replayId"))    replayId    = par("replayId").intValue();
        if (hasPar("replayTsUs"))  replayTsUs  = par("replayTsUs").intValue();
        if (hasPar("replayTagHex")) replayTagHex = par("replayTagHex").stdstringValue();

        if (enabled) {
            attackEvent = new cMessage("attackEvent");
            scheduleAt(simTime() + uniform(2.0, 3.0), attackEvent);
        }
    }

    virtual void handleMessage(cMessage *msg) override {
        if (msg != attackEvent) { delete msg; return; }

        auto *fake = new LightIoTMessage("FakePacket");
        if (mode == 1) { // Replay
            fake->setId(replayId);
            fake->setTimestamp(SimTime((int64_t)replayTsUs, SIMTIME_US));
            fake->setHmac(replayTagHex.c_str());
        } else {         // MITM
            static const char* BAD = "00000000000000000000000000000000";
            fake->setId(999999);
            fake->setTimestamp(simTime() - 2); // stale + bogus MAC
            fake->setHmac(BAD);
        }

        send(fake, "out");
        attacksSent++;
        scheduleAt(simTime() + interval, attackEvent);
    }

    virtual void finish() override {
        if (attackEvent) { cancelAndDelete(attackEvent); attackEvent=nullptr; }
        recordScalar("Fake_AttacksSent", attacksSent);
    }
};

Define_Module(FakeNode);