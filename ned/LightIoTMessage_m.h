#ifndef __LIGHTIOTMESSAGE_M_H
#define __LIGHTIOTMESSAGE_M_H

#include <omnetpp.h>

using namespace omnetpp;

class LightIoTMessage : public cMessage {
  private:
    int id;
    const char* hmac;
    simtime_t timestamp;

  public:
    LightIoTMessage(const char *name=nullptr) : cMessage(name) {}
    LightIoTMessage(const LightIoTMessage& other) : cMessage(other) {
        id = other.id;
        hmac = other.hmac;
        timestamp = other.timestamp;
    }

    LightIoTMessage& operator=(const LightIoTMessage& other) {
        if (this == &other) return *this;
        cMessage::operator=(other);
        id = other.id;
        hmac = other.hmac;
        timestamp = other.timestamp;
        return *this;
    }

    virtual LightIoTMessage *dup() const override {
        return new LightIoTMessage(*this);
    }

    void setId(int i) { id = i; }
    int getId() const { return id; }

    void setHmac(const char* h) { hmac = h; }
    const char* getHmac() const { return hmac; }

    void setTimestamp(simtime_t t) { timestamp = t; }
    simtime_t getTimestamp() const { return timestamp; }
};

#endif