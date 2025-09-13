#ifndef __LIGHTIOTMESSAGE_M_H
#define __LIGHTIOTMESSAGE_M_H

#include <omnetpp.h>
#include <string>

using namespace omnetpp;

class LightIoTMessage : public cMessage {
  private:
    int id_ = 0;            // شناسه یکتا برای duplicate
    int src_ = -1;          // شناسه گره مبدأ
    int seq_ = 0;           // شمارنده ترتیبی برای تازگی
    std::string macHex_;    // برچسب MAC به‌صورت hex (طول 16 بایت/32 کاراکتر یا 8 بایت/16 کاراکتر)
    simtime_t ts_ = SIMTIME_ZERO; // timestamp تولید پیام در گره

  public:
    LightIoTMessage(const char *name=nullptr) : cMessage(name) {}
    LightIoTMessage(const LightIoTMessage& other) : cMessage(other) { copy(other); }
    LightIoTMessage& operator=(const LightIoTMessage& other) {
        if (this==&other) return *this; cMessage::operator=(other); copy(other); return *this;
    }
    virtual LightIoTMessage *dup() const override { return new LightIoTMessage(*this); }

    // setters/getters
    void setId(int v)              { id_ = v; }
    int  getId()            const  { return id_; }

    void setSrc(int v)             { src_ = v; }
    int  getSrc()           const  { return src_; }

    void setSeq(int v)             { seq_ = v; }
    int  getSeq()           const  { return seq_; }

    void setMacHex(const char* h)  { macHex_ = h ? std::string(h) : std::string(); }
    void setMacHex(const std::string& h) { macHex_ = h; }
    const std::string& getMacHex() const { return macHex_; }

    void setTimestamp(simtime_t t) { ts_ = t; }
    simtime_t getTimestamp() const { return ts_; }

  private:
    void copy(const LightIoTMessage& o){
        id_ = o.id_; src_ = o.src_; seq_ = o.seq_; macHex_ = o.macHex_; ts_ = o.ts_;
    }
};

#endif