#include <omnetpp.h>
#include <cstring>
#include <set>
#include "LightIoTMessage_m.h"

using namespace omnetpp;

class GatewayNode : public cSimpleModule {
  private:
    // Stats
    int received = 0;
    int forwarded = 0;
    int dropped = 0;

    // Drop breakdown
    int droppedHmac = 0;
    int droppedStale = 0;
    int droppedDuplicate = 0;

    // Energy
    double batteryInit = 5000.0;   // mJ
    double battery     = 5000.0;   // mJ
    double costForward = 5.0;      // mJ
    double costVerify  = 5.0;      // mJ

    // Security & timing
    bool securityEnabled = true;
    bool checkHmac       = true;
    bool checkFreshness  = true;
    bool checkDuplicate  = true;

    simtime_t hmacWindow = 1;      // s
    simtime_t procDelay  = 0;      // s

    // Anti-replay (ID set)
    std::set<int> seenIds;

  protected:
    virtual void initialize() override {
        batteryInit     = par("batteryInit_mJ").doubleValue();
        battery         = batteryInit;
        costForward     = par("costForward_mJ").doubleValue();
        costVerify      = par("costVerify_mJ").doubleValue();

        securityEnabled = par("securityEnabled").boolValue();
        hmacWindow      = par("hmacWindow");
        procDelay       = par("procDelay");

        // Ablation switches
        checkHmac       = par("checkHmac").boolValue();
        checkFreshness  = par("checkFreshness").boolValue();
        checkDuplicate  = par("checkDuplicate").boolValue();
    }

    virtual void handleMessage(cMessage *msg) override {
        auto *m = check_and_cast<LightIoTMessage*>(msg);
        received++;

        // Minimum energy needed for this message
        double need = costForward + (securityEnabled ? costVerify : 0.0);
        if (battery < need) {
            EV << "[GatewayNode] Battery depleted. Dropping message.\n";
            dropped++;
            delete m;
            return;
        }

        if (securityEnabled) {
            // Charge verification cost once per message
            battery -= costVerify;

            // Compute checks with ablation toggles
            bool hmacOk = !checkHmac || ((m->getHmac() != nullptr) && (std::strcmp(m->getHmac(), "VALID") == 0));
            bool fresh  = !checkFreshness || ((simTime() - m->getTimestamp()) <= hmacWindow);
            bool notDup = !checkDuplicate || (seenIds.find(m->getId()) == seenIds.end());

            if (!(hmacOk && fresh && notDup)) {
                if (checkHmac && !hmacOk)      droppedHmac++;
                if (checkFreshness && !fresh)  droppedStale++;
                if (checkDuplicate && !notDup) droppedDuplicate++;

                dropped++;
                EV << "[GatewayNode] Security check failed -> Dropped"
                   << " (HMAC=" << (hmacOk?"OK":"BAD")
                   << ", fresh=" << (fresh?"OK":"OLD")
                   << ", dup=" << (!notDup?"YES":"NO") << ")\n";
                delete m;
                return;
            }
        }

        // Register ID (harmless even if checkDuplicate=false)
        seenIds.insert(m->getId());

        // Forwarding cost
        battery -= costForward;
        forwarded++;

        // Optional processing delay
        if (procDelay > SIMTIME_ZERO)
            sendDelayed(m, procDelay, "out");
        else
            send(m, "out");
    }

    virtual void finish() override {
        double percent = (batteryInit > 0 ? (battery / batteryInit) * 100.0 : 0.0);

        // Scalars for CSV
        recordScalar("GW_Received", received);
        recordScalar("GW_Forwarded", forwarded);
        recordScalar("GW_Dropped", dropped);
        recordScalar("GW_Dropped_HMAC", droppedHmac);
        recordScalar("GW_Dropped_Stale", droppedStale);
        recordScalar("GW_Dropped_Duplicate", droppedDuplicate);
        recordScalar("GW_BatteryRemaining_mJ", battery);

        // Readable logs
        EV << "[GatewayNode] Received=" << received
           << ", Forwarded=" << forwarded
           << ", Dropped=" << dropped << "\n";
        EV << "[GatewayNode] DropBreakdown: HMAC=" << droppedHmac
           << ", Stale=" << droppedStale
           << ", Duplicate=" << droppedDuplicate << "\n";
        EV << "[GatewayNode] Energy Remaining: " << battery
           << " mJ (" << percent << "%)\n";
    }
};

Define_Module(GatewayNode);
