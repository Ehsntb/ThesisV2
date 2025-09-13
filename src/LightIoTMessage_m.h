#pragma once
#include <omnetpp.h>
#include <string>

using namespace omnetpp;

class LightIoTMessage : public cMessage {
  private:
    int id_ = 0;
    int src_ = 0;
    int seq_ = 0;
    simtime_t ts_;
    std::string macHex_;
    void copy(const LightIoTMessage& o) {
        id_ = o.id_; src_ = o.src_; seq_ = o.seq_;
        ts_ = o.ts_; macHex_ = o.macHex_;
    }
  public:
    LightIoTMessage(const char* name=nullptr) : cMessage(name) {}
    LightIoTMessage(const LightIoTMessage& o) : cMessage(o) { copy(o); }
    LightIoTMessage& operator=(const LightIoTMessage& o) {
        if (this==&o) return *this; cMessage::operator=(o); copy(o); return *this;
    }
    virtual LightIoTMessage* dup() const override { return new LightIoTMessage(*this); }

    void setId(int v){ id_ = v; }           int getId()  const { return id_;  }
    void setSrc(int v){ src_ = v; }         int getSrc() const { return src_; }
    void setSeq(int v){ seq_ = v; }         int getSeq() const { return seq_; }
    void setTimestamp(simtime_t t){ ts_ = t; } simtime_t getTimestamp() const { return ts_; }
    void setMacHex(const std::string& s){ macHex_ = s; } const std::string& getMacHex() const { return macHex_; }
};
