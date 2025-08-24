#include <omnetpp.h>
#include "LightIoTMessage_m.h"
using namespace omnetpp;

class CloudServer : public cSimpleModule {
  private:
    int received = 0;
    simtime_t totalDelay = 0;
    cOutVector e2eVec;
  protected:
    virtual void initialize() override {
        e2eVec.setName("EndToEndDelay_s");
    }
    virtual void handleMessage(cMessage *msg) override {
        auto *m = check_and_cast<LightIoTMessage*>(msg);
        simtime_t delay = simTime() - m->getTimestamp();
        e2eVec.record(delay.dbl());
        totalDelay += delay;
        received++;
        delete m;
    }
    virtual void finish() override {
        double avgDelay = received ? totalDelay.dbl() / received : 0.0;
        recordScalar("Cloud_TotalReceived", received);
        recordScalar("Cloud_AvgEndToEndDelay_s", avgDelay);
    }
};
Define_Module(CloudServer);
