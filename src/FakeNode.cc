#include <omnetpp.h>
#include <cstring>
#include "LightIoTMessage_m.h"
using namespace omnetpp;

class FakeNode : public cSimpleModule {
  private:
    cMessage *attackEvent = nullptr;
    int fakeId = 1000;
    int mode = 1; // 1=replay, 2=mitm
    simtime_t interval = 2.5;
    int attacksSent = 0;
  protected:
    virtual void initialize() override {
        bool enabled = par("enabled").boolValue();
        interval = par("replayInterval");
        cPar& p = par("attackMode");
        if (p.isNumeric()) mode = p.intValue();
        else { const char* m = p.stringValue();
               if (!strcasecmp(m,"replay")) mode=1;
               else if (!strcasecmp(m,"mitm")) mode=2;
               else mode=1; }
        if (enabled) {
            attackEvent = new cMessage("attackEvent");
            scheduleAt(simTime() + uniform(2.0, 3.0), attackEvent);
        }
    }
    virtual void handleMessage(cMessage *msg) override {
        if (msg == attackEvent) {
            auto *fake = new LightIoTMessage("FakePacket");
            if (mode==1) { fake->setId(fakeId);         fake->setHmac("VALID");   }
            else         { fake->setId(fakeId++);       fake->setHmac("INVALID"); }
            fake->setTimestamp(simTime() - 2);
            send(fake, "out");
            attacksSent++;
            scheduleAt(simTime() + interval, attackEvent);
        } else delete msg;
    }
    virtual void finish() override {
        if (attackEvent) { cancelAndDelete(attackEvent); attackEvent=nullptr; }
        recordScalar("Fake_AttacksSent", attacksSent);
    }
};
Define_Module(FakeNode);
