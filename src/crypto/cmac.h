// /src/crypto/cmac.h
#pragma once
#include <cstddef>
#include <cstdint>

// AES-128 CMAC per NIST SP 800-38B.
// outTag: 16-byte authentication tag.
void aes128_cmac(const uint8_t key[16], const uint8_t* msg, size_t len, uint8_t outTag[16]);