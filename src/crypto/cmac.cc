// /src/crypto/cmac.cpp
#include "cmac.h"
#include <cstdint>
#include <cstring>

// tiny-AES-c
extern "C" {
#include "aes.h"
}

// Left shift a 128-bit block by 1 bit
static inline void leftshift128(const uint8_t in[16], uint8_t out[16]) {
    uint8_t carry = 0;
    for (int i = 15; i >= 0; --i) {
        uint8_t b = in[i];
        out[i] = (uint8_t)((b << 1) | carry);
        carry = (uint8_t)((b & 0x80) ? 1 : 0);
    }
}

static inline void xor128(uint8_t *a, const uint8_t *b) {
    for (int i=0;i<16;i++) a[i]^=b[i];
}

static const uint8_t Rb = 0x87;

static void generate_subkeys(const uint8_t key[16], uint8_t K1[16], uint8_t K2[16]) {
    uint8_t L[16] = {0};
    struct AES_ctx ctx;
    AES_init_ctx(&ctx, key);
    AES_ECB_encrypt(&ctx, L); // L = AES-128(0^128)

    // K1
    uint8_t Z[16];
    leftshift128(L, Z);
    if (L[0] & 0x80) Z[15] ^= Rb;
    std::memcpy(K1, Z, 16);

    // K2
    leftshift128(K1, Z);
    if (K1[0] & 0x80) Z[15] ^= Rb;
    std::memcpy(K2, Z, 16);
}

void aes128_cmac(const uint8_t key[16], const uint8_t* msg, size_t len, uint8_t outTag[16]) {
    uint8_t K1[16], K2[16];
    generate_subkeys(key, K1, K2);

    // Number of 16-byte blocks
    size_t n = (len + 15) / 16;
    if (n == 0) n = 1;

    bool lastComplete = (len != 0) && (len % 16 == 0);

    // Prepare last block
    uint8_t M_last[16] = {0};
    if (lastComplete) {
        // last block is complete
        std::memcpy(M_last, msg + 16*(n-1), 16);
        xor128(M_last, K1);
    } else {
        size_t rem = (len == 0) ? 0 : (len % 16);
        if (rem > 0)
            std::memcpy(M_last, msg + 16*(n-1), rem);
        M_last[rem] = 0x80; // 10* padding
        // rest already zero
        xor128(M_last, K2);
    }

    struct AES_ctx ctx;
    AES_init_ctx(&ctx, key);

    uint8_t X[16] = {0};
    uint8_t Y[16] = {0};

    // Process first n-1 blocks
    for (size_t i = 0; i < n-1; ++i) {
        std::memcpy(Y, msg + 16*i, 16);
        xor128(Y, X);
        AES_ECB_encrypt(&ctx, Y);
        std::memcpy(X, Y, 16);
    }

    // Final block
    for (int i=0;i<16;i++) Y[i] = X[i] ^ M_last[i];
    AES_ECB_encrypt(&ctx, Y);
    std::memcpy(outTag, Y, 16);
}