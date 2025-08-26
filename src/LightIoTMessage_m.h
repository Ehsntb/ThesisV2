// /src/LightIoTMessage_m.h

#ifndef __LIGHTIOTMESSAGE_M_H
#define __LIGHTIOTMESSAGE_M_H

#include <omnetpp.h>
#include <string>

using namespace omnetpp;

class LightIoTMessage : public cMessage {
  private:
    int id = 0;
    std::string macHex;   // CMAC(AES-128) in hex
    simtime_t timestamp = SIMTIME_ZERO;

  public:
    LightIoTMessage(const char *name=nullptr) : cMessage(name) {}
    LightIoTMessage(const LightIoTMessage& other) : cMessage(other) {
        id = other.id;
        macHex = other.macHex;
        timestamp = other.timestamp;
    }

    LightIoTMessage& operator=(const LightIoTMessage& other) {
        if (this == &other) return *this;
        cMessage::operator=(other);
        id = other.id;
        macHex = other.macHex;
        timestamp = other.timestamp;
        return *this;
    }

    virtual LightIoTMessage *dup() const override { return new LightIoTMessage(*this); }

    void setId(int i) { id = i; }
    int getId() const { return id; }

    // Backward-compat with old naming:
    void setHmac(const char* h) { macHex = (h ? h : ""); }
    const char* getHmac() const { return macHex.c_str(); }

    void setMacHex(const std::string& h) { macHex = h; }
    const std::string& getMacHex() const { return macHex; }

    void setTimestamp(simtime_t t) { timestamp = t; }
    simtime_t getTimestamp() const { return timestamp; }
};

#endif