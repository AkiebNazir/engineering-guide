/*
FOUNDATION BONUS - What is a webhook signature, really? (optional, read last)
=================================================================================
Every level from 04 onwards called hmac.New(sha256.New, secret) and trusted it.
This file opens that box. There is no webhook-signing helper here, and no
crypto/hmac doing the interesting part - just crypto/sha256 and the definition
of HMAC, printed byte by byte, so you can see that a signature is nothing more
than "a keyed hash of the body".

	HMAC(K, m) = H( (K' XOR opad) || H( (K' XOR ipad) || m ) )

	  H      sha256
	  K'     the key, zero-padded to the hash's 64-byte block size
	         (or, if the key is longer than a block, hashed down first)
	  ipad   the byte 0x36 repeated 64 times
	  opad   the byte 0x5c repeated 64 times
	  ||     plain concatenation of bytes

That is the entire algorithm. Two hashes and two XORs. The nesting is not
decoration: hashing the key with the message ONCE (sha256(key + body)) is a
real, broken scheme - length-extension attacks let an attacker append to your
body and still produce a valid digest without ever knowing the key.

This is optional. Nothing in levels 00-12 depends on it. It exists to answer
"but what is hmac.New actually doing for me?" once you are curious.

You will learn
  - a "signature" is a hex string of 32 bytes: the output of one hash function
  - exactly which bytes get hashed, printed - the secret, the timestamp, the body
  - why HMAC nests two hashes instead of doing the obvious one
  - that our hand-rolled version is byte-identical to the standard library's,
    which is the proof there was never any magic

Run it   go run ./Webhooks/Foundation/golang/13_bonus_hmac_by_hand
*/
package main

import (
	"bytes"
	"crypto/hmac" // imported ONLY to prove our version matches, at the end
	"crypto/sha256"
	"encoding/hex"
	"fmt"
)

const (
	blockSize = 64 // sha256 processes 64-byte blocks - that is where 64 comes from
	ipadByte  = 0x36
	opadByte  = 0x5c
)

func hmacSHA256ByHand(key, message []byte, verbose bool) []byte {
	// STEP 1: normalise the key to exactly one block.
	if len(key) > blockSize {
		sum := sha256.Sum256(key) // too long: hash it down to 32 bytes
		key = sum[:]
	}
	paddedKey := make([]byte, blockSize) // too short: the rest stays zero
	copy(paddedKey, key)

	// STEP 2: two different 64-byte masks, derived from the same key.
	innerKey := make([]byte, blockSize)
	outerKey := make([]byte, blockSize)
	for i, b := range paddedKey {
		innerKey[i] = b ^ ipadByte
		outerKey[i] = b ^ opadByte
	}

	// STEP 3: hash (innerKey || message), then hash (outerKey || that digest).
	innerInput := append(bytes.Clone(innerKey), message...)
	innerDigest := sha256.Sum256(innerInput)
	outerInput := append(bytes.Clone(outerKey), innerDigest[:]...)
	final := sha256.Sum256(outerInput)

	if verbose {
		fmt.Printf("  key padded to %d bytes : %s\n", len(paddedKey), hex.EncodeToString(paddedKey))
		fmt.Printf("  inner key (key XOR 0x36)     : %s\n", hex.EncodeToString(innerKey))
		fmt.Printf("  outer key (key XOR 0x5c)     : %s\n", hex.EncodeToString(outerKey))
		fmt.Printf("  inner input  (%3d bytes)     : %s... || %q\n",
			len(innerInput), hex.EncodeToString(innerKey)[:16], message)
		fmt.Printf("  inner digest ( 32 bytes)     : %s\n", hex.EncodeToString(innerDigest[:]))
		fmt.Printf("  outer input  (%3d bytes)     : %s... || <inner digest>\n",
			len(outerInput), hex.EncodeToString(outerKey)[:16])
		fmt.Printf("  final digest ( 32 bytes)     : %s\n", hex.EncodeToString(final[:]))
	}
	return final[:]
}

func main() {
	secret := []byte("whsec_shared_with_the_provider")
	timestamp := "1700000000"
	body := []byte(`{"type":"invoice.paid","id":"evt_1","data":{"amount":500}}`)

	// This is the ONE byte string a webhook signature is computed over (level
	// 07). Nothing clever: the timestamp, a dot, and the raw body bytes.
	signedPayload := append([]byte(timestamp+"."), body...)
	fmt.Println("---- the exact bytes being hashed ----")
	fmt.Printf("  secret        : %q   (%d bytes, never sent over the wire)\n", secret, len(secret))
	fmt.Printf("  signed payload: %q   (%d bytes)\n", signedPayload, len(signedPayload))
	fmt.Println()

	fmt.Println("---- HMAC-SHA256, computed by hand from sha256 alone ----")
	byHand := hmacSHA256ByHand(secret, signedPayload, true)
	fmt.Println()
	fmt.Printf("signature header value: %s\n", hex.EncodeToString(byHand))
	fmt.Println()

	// The proof: the standard library, which every level from 04 on used, agrees.
	mac := hmac.New(sha256.New, secret)
	mac.Write(signedPayload)
	fromStdlib := mac.Sum(nil)
	fmt.Printf("hand-rolled == crypto/hmac: %v\n", bytes.Equal(byHand, fromStdlib))
	if !bytes.Equal(byHand, fromStdlib) || len(byHand) != 32 {
		panic("FAILED")
	}

	// Two properties worth seeing for yourself, both straight from "keyed hash":
	// 1. one different byte in the body changes the whole digest (avalanche)
	tamperedPayload := bytes.Replace(signedPayload, []byte("500"), []byte("501"), 1)
	tampered := hmacSHA256ByHand(secret, tamperedPayload, false)
	differing := 0
	for i := range byHand {
		if byHand[i] != tampered[i] {
			differing++
		}
	}
	fmt.Printf("changing one digit of the amount changes %d/32 digest bytes\n", differing)
	if differing < 20 {
		panic("FAILED")
	}

	// 2. without the secret you cannot produce the digest, even with the body
	if bytes.Equal(hmacSHA256ByHand([]byte("whsec_attacker_guess"), signedPayload, false), byHand) {
		panic("FAILED")
	}

	// And the longer-than-a-block key path, which is easy to get wrong.
	longKey := bytes.Repeat([]byte("k"), 100)
	longMac := hmac.New(sha256.New, longKey)
	longMac.Write(signedPayload)
	if !bytes.Equal(hmacSHA256ByHand(longKey, signedPayload, false), longMac.Sum(nil)) {
		panic("FAILED")
	}

	// Finally: verification is just doing all of the above again and comparing.
	// Use hmac.Equal even here - constant time, always (level 04).
	if !hmac.Equal(hmacSHA256ByHand(secret, signedPayload, false), byHand) {
		panic("FAILED")
	}
	fmt.Println("OK")
}
