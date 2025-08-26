// /src/crypto/crypto_utils.cpp
#include "crypto_utils.h"
#include <sstream>
#include <iomanip>

static int hexval(char c){
    if (c>='0'&&c<='9') return c-'0';
    if (c>='a'&&c<='f') return c-'a'+10;
    if (c>='A'&&c<='F') return c-'A'+10;
    return -1;
}

bool hexToBytes(const std::string& hex, std::vector<uint8_t>& out){
    out.clear();
    if (hex.size()%2) return false;
    out.reserve(hex.size()/2);
    for (size_t i=0;i<hex.size();i+=2){
        int hi=hexval(hex[i]); int lo=hexval(hex[i+1]);
        if (hi<0||lo<0) return false;
        out.push_back((uint8_t)((hi<<4)|lo));
    }
    return true;
}

std::string bytesToHex(const uint8_t* data, size_t len){
    std::ostringstream oss;
    for (size_t i=0;i<len;i++){
        oss<<std::hex<<std::setw(2)<<std::setfill('0')<<(int)data[i];
    }
    return oss.str();
}

void packIdTsBigEndian(int id, int64_t ts_us, std::vector<uint8_t>& out){
    out.resize(12);
    // id (int32) BE
    out[0]=(uint8_t)((id>>24)&0xFF);
    out[1]=(uint8_t)((id>>16)&0xFF);
    out[2]=(uint8_t)((id>>8)&0xFF);
    out[3]=(uint8_t)(id&0xFF);
    // ts_us (int64) BE
    for (int i=0;i<8;i++){
        out[4+i]=(uint8_t)((ts_us >> (56 - 8*i)) & 0xFF);
    }
}

bool ct_equal(const uint8_t* a, const uint8_t* b, size_t n){
    uint8_t v=0;
    for (size_t i=0;i<n;i++) v |= (uint8_t)(a[i]^b[i]);
    return v==0;
}