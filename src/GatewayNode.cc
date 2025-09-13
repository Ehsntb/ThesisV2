// /src/GatewayNode.cc

#include <omnetpp.h>
#include <cstring>
#include <set>
#include <unordered_map>
#include <vector>
#include <string>
#include <functional>
#include <cstdint>
#include <cmath>
#include <algorithm>
#include "LightIoTMessage_m.h"
#include "crypto/crypto_utils.h"
#include "crypto/cmac.h"
using namespace omnetpp;

class GatewayNode : public cSimpleModule {
  private:
    // ===== انرژی
    double batteryInit = 5000.0;
    double battery     = 5000.0;
    double costForward = 5.0;
    double costVerify  = 5.0;

    // ===== کلید و امنیت
    std::string aesKeyHex;
    std::vector<uint8_t> keyBytes;
    bool securityEnabled = true;
    bool checkHmac       = true;
    bool checkFreshness  = true;
    bool checkDuplicate  = true;

    // ترتیب مراحل
    std::string stageOrder = "HFB";
    int orderId = 1; // HFB=1, HBF=2, FHB=3, FBH=4, BHF=5, BFH=6, else 0

    simtime_t hmacWindow = 1;   // s
    simtime_t procDelay  = 0;   // s

    // ===== شمارنده‌ها
    int inReceived = 0;
    int totalAccepted = 0;
    int totalDroppedHmac = 0;
    int totalDroppedReplay = 0;
    int totalDroppedDup = 0;
    int mismatchCounter = 0;

    // ===== تازگی: ماسک 64 بیتی per-sensor (seq-based)
    struct FreshState {
        uint64_t maxSeq = 0;
        uint64_t mask   = 0;
        simtime_t lastTs = 0;
        double avgPeriod = 1.0; // برآورد دوره ارسال
        int Wmsgs = 64;
    };
    std::unordered_map<int, FreshState> freshMap; // key = src

    // ===== Duplicate ground truth برای FP
    std::set<int> truthSeenIds;

    // ===== روش حذف تکرار
    std::string duplicateMethod = "set";

    // set
    std::set<int> seenIds;

    // Bloom
    int bloomBits = 16384;
    int bloomHashes = 3;
    std::vector<uint8_t> bloomBitsArr;

    // SBF
    int sbfBits = 16384;
    int sbfHashes = 3;
    double sbfDecay = 0.02;
    std::vector<uint8_t> sbfCounters; // 4-bit style (0..15), stored in bytes for سادگی

    // آمار Bloom/SBF
    long bloomQueries = 0;
    long bloomInserts = 0;
    long bloomFalsePos = 0;

    // بردارهای زمانی
    cOutVector bloomCallsVec;    // q_bloom_calls
    cOutVector bloomInsertsVec;  // q_bloom_inserts

    // ===== شمارنده‌های «کار» (برای Workavg)
    long workH_checks = 0;   // تعداد دفعات اجرای مرحله H
    long workF_checks = 0;   // تعداد دفعات اجرای مرحله F
    long workB_checks = 0;   // تعداد دفعات اجرای مرحله Duplicate (B)

    // ===== کمکی‌ها
    inline void bloomInit(int bits) {
        int bytes = (bits + 7) / 8;
        bloomBitsArr.assign(bytes, 0u);
    }
    inline size_t hashMix(uint64_t x, uint64_t seed) const {
        return std::hash<uint64_t>{}(x ^ (seed * 0x9e3779b97f4a7c15ULL));
    }
    inline bool bloomTest_id(int id) const {
        if (bloomBitsArr.empty()) return false;
        for (int k = 0; k < bloomHashes; ++k) {
            size_t h = hashMix((uint64_t)id, (uint64_t)k);
            size_t bit = h % (size_t)bloomBits;
            if ((bloomBitsArr[bit >> 3] & (uint8_t)(1u << (bit & 7))) == 0)
                return false;
        }
        return true;
    }
    inline void bloomAdd_id(int id) {
        if (bloomBitsArr.empty()) return;
        for (int k = 0; k < bloomHashes; ++k) {
            size_t h = hashMix((uint64_t)id, (uint64_t)k);
            size_t bit = h % (size_t)bloomBits;
            bloomBitsArr[bit >> 3] |= (uint8_t)(1u << (bit & 7));
        }
    }

    inline void sbfInit(int counters) {
        sbfCounters.assign(counters, 0u);
    }
    inline bool sbfTest_id(int id) const {
        if (sbfCounters.empty()) return false;
        for (int k = 0; k < sbfHashes; ++k) {
            size_t h = hashMix((uint64_t)id, (uint64_t)k + 1337);
            size_t idx = h % (size_t)sbfCounters.size();
            if (sbfCounters[idx] == 0) return false;
        }
        return true;
    }
    inline void sbfAgeOnce() {
        if (sbfCounters.empty()) return;
        size_t idx = (size_t) intrand((int)sbfCounters.size());
        if (sbfCounters[idx] > 0) sbfCounters[idx]--;
    }
    inline void sbfAdd_id(int id) {
        // aging تقریبی: به نسبت sbfDecay
        int ageCount = std::max(1, (int)std::round(sbfDecay * (double)std::max(1, sbfHashes)));
        for (int i=0;i<ageCount;i++) sbfAgeOnce();
        for (int k = 0; k < sbfHashes; ++k) {
            size_t h = hashMix((uint64_t)id, (uint64_t)k + 1337);
            size_t idx = h % (size_t)sbfCounters.size();
            if (sbfCounters[idx] < 15) sbfCounters[idx]++;
        }
    }

    inline int64_t ts_to_us(simtime_t t) const {
        return (int64_t) llround(SIMTIME_DBL(t) * 1e6);
    }

    static int orderIdFromStr(const std::string& s){
        if (s=="HFB") return 1;
        if (s=="HBF") return 2;
        if (s=="FHB") return 3;
        if (s=="FBH") return 4;
        if (s=="BHF") return 5;
        if (s=="BFH") return 6;
        return 0;
    }
    static std::string normalizeOrder(std::string s){
        // upper + keep only H/F/B; map 'D'->'B'
        for (char& c: s){ c = (char)toupper((unsigned char)c); if (c=='D') c='B'; }
        std::string t;
        for (char c: s){ if (c=='H'||c=='F'||c=='B') if (t.find(c)==std::string::npos) t.push_back(c); }
        // append missing to reach length 3, default order HFB
        for (char c: std::string("HFB")) if (t.find(c)==std::string::npos) t.push_back(c);
        if (t.size()!=3) t="HFB";
        return t;
    }

    // ===== مراحل به‌صورت توابع
    bool stage_H(LightIoTMessage* m){
        if (!checkHmac) return true;
        workH_checks++;
        const std::string rxHex = m->getMacHex();
        if (rxHex.empty()) { totalDroppedHmac++; return false; }

        std::vector<uint8_t> msgbytes; packIdTsBigEndian(m->getId(), ts_to_us(m->getTimestamp()), msgbytes);
        uint8_t tag[16]; aes128_cmac(keyBytes.data(), msgbytes.data(), msgbytes.size(), tag);

        std::vector<uint8_t> rx;
        bool ok = hexToBytes(rxHex, rx) && rx.size()==16 && ct_equal(rx.data(), tag, 16);
        if (!ok) { totalDroppedHmac++; }
        return ok;
    }

    bool stage_F(LightIoTMessage* m){
        if (!checkFreshness) return true;
        workF_checks++;
        int src = m->getSrc();
        int s   = m->getSeq();
        auto &fs = freshMap[src];

        if (fs.lastTs > SIMTIME_ZERO) {
            double per = SIMTIME_DBL(simTime() - fs.lastTs);
            if (per > 1e-9) fs.avgPeriod = 0.9*fs.avgPeriod + 0.1*per;
        }
        fs.lastTs = simTime();

        int Wmsgs = (int) std::ceil(std::max(1e-9, SIMTIME_DBL(hmacWindow)) / std::max(1e-9, fs.avgPeriod));
        fs.Wmsgs = std::min(64, std::max(1, Wmsgs));

        bool freshOk = true;
        if ((uint64_t)s > fs.maxSeq) {
            uint64_t shift = (uint64_t)s - fs.maxSeq;
            if (shift >= 64) fs.mask = 0;
            else fs.mask <<= shift;
            fs.mask |= 1ULL; // بیت 0 برای s جدید
            fs.maxSeq = (uint64_t)s;
        } else {
            uint64_t delta = fs.maxSeq - (uint64_t)s;
            if ((int)delta >= fs.Wmsgs) {
                freshOk = false; // خارج از پنجره → replay
            } else {
                uint64_t bit = 1ULL << delta;
                if (fs.mask & bit) freshOk = false; // تکرار در پنجره
                else fs.mask |= bit;
            }
        }
        if (!freshOk) totalDroppedReplay++;
        return freshOk;
    }

    bool stage_B(LightIoTMessage* m){
        if (!checkDuplicate) return true;
        workB_checks++;

        int id = m->getId();
        bool passDup = true;

        if (duplicateMethod == "set") {
            // «پرس‌وجو» را هم به‌عنوان کار می‌شماریم
            if (seenIds.find(id) != seenIds.end()) passDup = false;
        } else if (duplicateMethod == "bloom") {
            bloomQueries++; bloomCallsVec.record(1);
            bool maybe = bloomTest_id(id);
            if (maybe && truthSeenIds.find(id) == truthSeenIds.end()) bloomFalsePos++;
            if (maybe) passDup = false;
        } else { // sbf
            bloomQueries++; bloomCallsVec.record(1);
            bool maybe = sbfTest_id(id);
            if (maybe && truthSeenIds.find(id) == truthSeenIds.end()) bloomFalsePos++;
            if (maybe) passDup = false;
        }

        if (!passDup) totalDroppedDup++;
        return passDup;
    }

  protected:
    virtual void initialize() override {
        // انرژی
        batteryInit     = par("batteryInit_mJ").doubleValue();
        battery         = batteryInit;
        costForward     = par("costForward_mJ").doubleValue();
        costVerify      = par("costVerify_mJ").doubleValue();

        // امنیت/زمان
        securityEnabled = par("securityEnabled").boolValue();
        checkHmac       = par("checkHmac").boolValue();
        checkFreshness  = par("checkFreshness").boolValue();
        checkDuplicate  = par("checkDuplicate").boolValue();
        hmacWindow      = par("hmacWindow");
        procDelay       = par("procDelay");

        // ترتیب
        int idFromPar = (hasPar("stageOrderId") ? par("stageOrderId").intValue() : 0);
        std::string ordFromPar;
        if (hasPar("stageOrder")) {
            ordFromPar = par("stageOrder").stdstringValue();
        }
        // نرمال‌سازی رشته ورودی (اجازه می‌دهد H/F/B با ترتیب دلخواه یا کاراکترهای اضافی داده شود)
        std::string ordNorm = normalizeOrder(ordFromPar);

        if (idFromPar >= 1 && idFromPar <= 6) {
            // اگر شناسه به‌صورت عددی داده شده باشد، بر رشته مقدم است
            static const char* LUT[] = {"", "HFB", "HBF", "FHB", "FBH", "BHF", "BFH"};
            orderId   = idFromPar;
            stageOrder = LUT[orderId];
        } else if (!ordNorm.empty()) {
            // در غیر این صورت از رشته استفاده می‌کنیم
            stageOrder = ordNorm;
            orderId    = orderIdFromStr(stageOrder);
        } else {
            // پیش‌فرض ایمن
            stageOrder = "HFB";
            orderId    = 1;
        }

        // کلید
        aesKeyHex = par("aesKeyHex").stdstringValue();
        if (!hexToBytes(aesKeyHex, keyBytes) || keyBytes.size()!=16) {
            EV << "[GatewayNode] Invalid aesKeyHex; expected 16-byte hex.\n";
            keyBytes.assign(16, 0);
        }

        // روش Duplicate
        duplicateMethod = par("duplicateMethod").stdstringValue();
        if (duplicateMethod != "set" && duplicateMethod != "bloom" && duplicateMethod != "sbf")
            duplicateMethod = "set";

        bloomBits   = hasPar("bloomBits")   ? par("bloomBits").intValue()   : bloomBits;
        bloomHashes = hasPar("bloomHashes") ? par("bloomHashes").intValue() : bloomHashes;
        sbfBits     = hasPar("sbfBits")     ? par("sbfBits").intValue()     : sbfBits;
        sbfHashes   = hasPar("sbfHashes")   ? par("sbfHashes").intValue()   : sbfHashes;
        sbfDecay    = hasPar("sbfDecay")    ? par("sbfDecay").doubleValue() : sbfDecay;

        if (duplicateMethod == "bloom") {
            if (bloomBits < 8) bloomBits = 8;
            if (bloomHashes < 1) bloomHashes = 1;
            bloomInit(bloomBits);
        } else if (duplicateMethod == "sbf") {
            if (sbfBits < 8) sbfBits = 8;
            if (sbfHashes < 1) sbfHashes = 1;
            sbfInit(sbfBits);
        }
        if ((duplicateMethod=="bloom" || duplicateMethod=="sbf") && std::max(bloomBits,sbfBits) < 1024) {
            EV << "[GatewayNode][WARN] bloom/sbf bits < 1024\n";
        }

        bloomCallsVec.setName("q_bloom_calls");
        bloomInsertsVec.setName("q_bloom_inserts");
    }

    virtual void handleMessage(cMessage *msg) override {
        auto *m = check_and_cast<LightIoTMessage*>(msg);
        inReceived++;

        // انرژی حداقلی برای پردازش این پیام
        double need = costForward + (securityEnabled ? costVerify : 0.0);
        if (battery < need) {
            EV << "[GatewayNode] Battery depleted. Drop.\n";
            totalDroppedDup++; // شمردن در dup برای سادگی
            delete m;
            return;
        }

        if (securityEnabled) {
            battery -= costVerify; // هزینه ثابتِ بررسی
            // اجرای مراحل به ترتیب stageOrder
            for (char c : stageOrder) {
                bool ok = true;
                if (c=='H') ok = stage_H(m);
                else if (c=='F') ok = stage_F(m);
                else if (c=='B') ok = stage_B(m);
                if (!ok) { delete m; return; } // درون مرحلۀ مربوطه شمارنده حذف افزایش یافته است
            }
        }

        // در صورت عبور، «ثبت برای دفعات بعد»
        int id = m->getId();
        truthSeenIds.insert(id);
        if (checkDuplicate) {
            if (duplicateMethod == "set") {
                seenIds.insert(id);
            } else if (duplicateMethod == "bloom") {
                bloomInserts++; bloomInsertsVec.record(1);
                bloomAdd_id(id);
            } else {
                bloomInserts++; bloomInsertsVec.record(1);
                sbfAdd_id(id);
            }
        }

        // هزینه ارسال و فوروارد
        battery -= costForward;
        totalAccepted++;

        if (procDelay > SIMTIME_ZERO) sendDelayed(m, procDelay, "out");
        else send(m, "out");
    }

    virtual void finish() override {
        // صحت مجموع شمارش‌ها
        int totalDrops = totalDroppedHmac + totalDroppedReplay + totalDroppedDup;
        if (inReceived != (totalAccepted + totalDrops)) mismatchCounter++;

        // goodput = totalAccepted / duration
        double duration = SIMTIME_DBL(simTime());
        double goodput = (duration > 0) ? ((double)totalAccepted / duration) : 0.0;

        // Bloom/SBF مقادیر خلاصه
        double bloomFP = (bloomQueries > 0) ? ((double)bloomFalsePos / (double)bloomQueries) : 0.0;
        double callsPerK = (inReceived > 0) ? (1000.0 * (double)bloomQueries / (double)inReceived) : 0.0;

        // انرژی
        double energyGW_mJ = batteryInit - battery;
        double energyPerMsg_mJ = (totalAccepted > 0) ? (energyGW_mJ / (double)totalAccepted) : 0.0;

        // Workavg برحسب «تعداد اجرای مراحل» (مقایسه‌ی ترتیبی)
        double workAvg_units = (inReceived > 0)
            ? ((double)(workH_checks + workF_checks + workB_checks) / (double)inReceived)
            : 0.0;

        // ==== Scalars (نام‌ها مطابق پایان‌نامه) ====
        recordScalar("totalAccepted", totalAccepted);
        recordScalar("totalDroppedHmac", totalDroppedHmac);
        recordScalar("totalDroppedReplay", totalDroppedReplay);
        recordScalar("totalDroppedDup", totalDroppedDup);
        recordScalar("goodput", goodput);

        recordScalar("bloomFP", bloomFP);
        recordScalar("bloomCallsPerK", callsPerK);
        recordScalar("bloomQueriesTotal", (double)bloomQueries);
        recordScalar("bloomInsertsTotal", (double)bloomInserts);

        recordScalar("energyGW_mJ", energyGW_mJ);
        recordScalar("energyPerMsg_mJ", energyPerMsg_mJ);

        recordScalar("workAvg_units", workAvg_units);
        recordScalar("workH_count", (double)workH_checks);
        recordScalar("workF_count", (double)workF_checks);
        recordScalar("workB_count", (double)workB_checks);

        recordScalar("stageOrderId", (double)orderId);
        recordScalar("mismatchCounter", mismatchCounter);
    }
};

Define_Module(GatewayNode);
