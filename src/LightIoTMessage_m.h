// /src/LightIoTMessage_m.h

#ifndef __LIGHTIOTMESSAGE_M_H
#define __LIGHTIOTMESSAGE_M_H

#include <omnetpp.h>
#include <string>
using namespace omnetpp;

class LightIoTMessage : public cMessage {
  private:
    int id = 0;                  // شناسه یکتا (جهانی)
    int src = 0;                 // اندیس فرستنده (sensor index)
    int seq = 0;                 // شماره ترتیبی هر سنسور
    std::string macHex;          // CMAC(AES-128) hex
    simtime_t timestamp = SIMTIME_ZERO;

  public:
    LightIoTMessage(const char *name=nullptr) : cMessage(name) {}
    LightIoTMessage(const LightIoTMessage& other) : cMessage(other) {
        id = other.id; src = other.src; seq = other.seq;
        macHex = other.macHex; timestamp = other.timestamp;
    }
    LightIoTMessage& operator=(const LightIoTMessage& other) {
        if (this == &other) return *this;
        cMessage::operator=(other);
        id = other.id; src = other.src; seq = other.seq;
        macHex = other.macHex; timestamp = other.timestamp;
        return *this;
    }
    virtual LightIoTMessage *dup() const override { return new LightIoTMessage(*this); }

    void setId(int v) { id = v; }           int getId() const { return id; }
    void setSrc(int v){ src = v; }           int getSrc() const{ return src; }
    void setSeq(int v){ seq = v; }           int getSeq() const{ return seq; }

    // سازگاری با کد قبلی
    void setHmac(const char* h) { macHex = (h ? h : ""); }
    const char* getHmac() const { return macHex.c_str(); }

    void setMacHex(const std::string& h) { macHex = h; }
    const std::string& getMacHex() const { return macHex; }

    void setTimestamp(simtime_t t) { timestamp = t; }
    simtime_t getTimestamp() const { return timestamp; }
};

#endif