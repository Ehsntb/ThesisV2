// /src/CloudServer.cc

#include <omnetpp.h>
#include "LightIoTMessage_m.h"
using namespace omnetpp;

class CloudServer : public cSimpleModule {
  private:
    int received = 0;
    simtime_t totalDelay = 0;

    cOutVector e2eValid;     // e2eDelay_valid
    cOutVector e2eDebug;     // e2eDelay_debug
    int debugCount = 0;

  protected:
    virtual void initialize() override {
        e2eValid.setName("e2eDelay_valid");
        e2eDebug.setName("e2eDelay_debug");
    }

    virtual void handleMessage(cMessage *msg) override {
        auto *m = check_and_cast<LightIoTMessage*>(msg);
        simtime_t delay = simTime() - m->getTimestamp();

        e2eValid.record(delay.dbl());
        if (debugCount < 10) { e2eDebug.record(delay.dbl()); debugCount++; }

        totalDelay += delay;
        received++;
        delete m;
    }

    virtual void finish() override {
        double avgDelay = (received > 0) ? totalDelay.dbl() / received : 0.0;
        recordScalar("Cloud_TotalReceived", received);
        recordScalar("Cloud_AvgDelay_s", avgDelay);
    }
};
Define_Module(CloudServer);