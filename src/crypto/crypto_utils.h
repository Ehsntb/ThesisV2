// /src/crypto/crypto_utils.h
#pragma once
#include <string>
#include <vector>
#include <cstdint>

bool hexToBytes(const std::string& hex, std::vector<uint8_t>& out);
std::string bytesToHex(const uint8_t* data, size_t len);
void packIdTsBigEndian(int id, int64_t ts_us, std::vector<uint8_t>& out);
bool ct_equal(const uint8_t* a, const uint8_t* b, size_t n);