#include <omnetpp.h>
#include <cstring>
#include <set>
#include "LightIoTMessage_m.h"
using namespace omnetpp;

class GatewayNode : public cSimpleModule {
  private:
    int received = 0, forwarded = 0, dropped = 0;
    double battery = 5000.0, costForward = 5.0, costVerify = 5.0;
    bool securityEnabled = true;
    simtime_t hmacWindow = 1, procDelay = 0;
    std::set<int> seenIds;
  protected:
    virtual void initialize() override {
        battery        = par("batteryInit_mJ").doubleValue();
        costForward    = par("costForward_mJ").doubleValue();
        costVerify     = par("costVerify_mJ").doubleValue();
        securityEnabled= par("securityEnabled").boolValue();
        hmacWindow     = par("hmacWindow");
        procDelay      = par("procDelay");
    }
    virtual void handleMessage(cMessage *msg) override {
        received++;
        auto *m = check_and_cast<LightIoTMessage*>(msg);
        double need = costForward + (securityEnabled ? costVerify : 0.0);
        if (battery < need) { dropped++; delete m; return; }

        if (securityEnabled) {
            battery -= costVerify;
            bool hmacOk = (m->getHmac()!=nullptr) && (strcmp(m->getHmac(),"VALID")==0);
            bool fresh  = (simTime() - m->getTimestamp()) <= hmacWindow;
            bool notSeen= (seenIds.find(m->getId()) == seenIds.end());
            if (!(hmacOk && fresh && notSeen)) { dropped++; delete m; return; }
        }
        seenIds.insert(m->getId());
        battery -= costForward;
        forwarded++;
        if (procDelay > SIMTIME_ZERO) sendDelayed(m, procDelay, "out");
        else send(m, "out");
    }
    virtual void finish() override {
        recordScalar("GW_Received", received);
        recordScalar("GW_Forwarded", forwarded);
        recordScalar("GW_Dropped", dropped);
        recordScalar("GW_BatteryRemaining_mJ", battery);
    }
};
Define_Module(GatewayNode);
