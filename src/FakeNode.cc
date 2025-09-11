// /src/FakeNode.cc
#include <omnetpp.h>
#include <cstring>
#include <string>
#include "LightIoTMessage_m.h"
#include "crypto/crypto_utils.h"
#include "crypto/cmac.h"

using namespace omnetpp;

class FakeNode : public cSimpleModule {
  private:
    cMessage *attackEvent = nullptr;

    bool enabled = true;
    int  attackMode = 1;                 // فعلاً فقط replay
    simtime_t replayInterval = 2.5;

    int    replayId = 100000;
    long   replayTsUs = 500000;          // 0.5s
    std::string replayTagHex = "00000000000000000000000000000000";

    bool validMac = false;
    std::string aesKeyHex;

    int    dupBurstLen = 0;              // تعداد کپی اضافه
    simtime_t dupBurstGap = 1.0;
    simtime_t outOfOrderJitter = 0.0;

    // شمارنده‌ها
    long attacksSent = 0;
    long validReplaysSent = 0;
    long dupMsgsSent = 0;
    long bursts = 0;

    LightIoTMessage* makeReplayPacket() {
        auto *p = new LightIoTMessage("FakeReplay");
        p->setId(replayId);
        p->setSrc(-1); // مهاجم
        p->setSeq(0);  // اهمیتی ندارد؛ بازپخش است
        p->setTimestamp(SimTime((int64_t)replayTsUs, SIMTIME_US));

        if (validMac) {
            std::vector<uint8_t> keyBytes;
            if (!hexToBytes(aesKeyHex, keyBytes) || keyBytes.size()!=16)
                keyBytes.assign(16, 0);
            std::vector<uint8_t> mbytes;
            packIdTsBigEndian(replayId, replayTsUs, mbytes);
            uint8_t tag[16];
            aes128_cmac(keyBytes.data(), mbytes.data(), mbytes.size(), tag);
            p->setMacHex(bytesToHex(tag, 16));
        } else {
            p->setMacHex(replayTagHex);
        }
        return p;
    }

  protected:
    virtual void initialize() override {
        enabled = par("enabled").boolValue();
        attackMode = par("attackMode").intValue();
        replayInterval = par("replayInterval");

        replayId = par("replayId").intValue();
        replayTsUs = par("replayTsUs").intValue();
        replayTagHex = par("replayTagHex").stdstringValue();

        validMac = par("validMac").boolValue();
        aesKeyHex = par("aesKeyHex").stdstringValue();

        dupBurstLen = par("dupBurstLen").intValue();
        dupBurstGap = par("dupBurstGap");
        outOfOrderJitter = par("outOfOrderJitter");

        if (enabled) {
            attackEvent = new cMessage("attackEvent");
            scheduleAt(simTime() + uniform(2.0, 3.0), attackEvent);
        }
    }

    virtual void handleMessage(cMessage *msg) override {
        if (msg != attackEvent) { delete msg; return; }

        if (attackMode == 1) {
            // یک برست: اولین پیام + dupBurstLen کپی اضافه
            int copies = 1 + std::max(0, dupBurstLen);
            for (int i=0; i<copies; ++i) {
                auto *pkt = makeReplayPacket();
                simtime_t baseGap = (i == 0 ? 0 : (dupBurstGap * (double)i / std::max(1, dupBurstLen)));
                simtime_t jitter = (outOfOrderJitter > 0) ? uniform(0, outOfOrderJitter) : 0;
                sendDelayed(pkt, baseGap + jitter, "out");
            }
            bursts++;
            attacksSent += copies;
            if (validMac) validReplaysSent += copies;
            if (copies > 1) dupMsgsSent += (copies - 1);
        }

        scheduleAt(simTime() + replayInterval, attackEvent);
    }

    virtual void finish() override {
        if (attackEvent) { cancelAndDelete(attackEvent); attackEvent=nullptr; }
        recordScalar("Fake_AttacksSent", attacksSent);
        recordScalar("Fake_ValidReplaysSent", validReplaysSent);
        recordScalar("Fake_DupMsgsSent", dupMsgsSent);
        recordScalar("Fake_Bursts", bursts);
    }
};

Define_Module(FakeNode);