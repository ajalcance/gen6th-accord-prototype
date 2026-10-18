// Package digest names content by its SHA-256 digest, in the one textual form the trust
// services use everywhere: "sha256:" followed by 64 lowercase hexadecimal characters.
//
// Every signed record, log leaf and evidence manifest in Accord refers to content by a digest.
// Keeping the encoding in one place means a record written by the Trust Signer, a leaf in the
// Trust Log and a check in the Public Verifier cannot disagree about how a digest is spelled —
// a disagreement that would make a genuine record fail verification, or a forged one pass.
package digest

import (
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"strings"
)

// Prefix is the algorithm label every digest carries. A bare hex string is refused, so an
// algorithm change can never be mistaken for the old one.
const Prefix = "sha256:"

// ErrMalformed reports a digest that is not in the canonical form.
var ErrMalformed = errors.New("digest: malformed")

// Of returns the canonical digest of content.
func Of(content []byte) string {
	sum := sha256.Sum256(content)
	return Prefix + hex.EncodeToString(sum[:])
}

// Parse validates a digest string and returns its raw 32 bytes.
//
// Only the canonical form is accepted: the prefix, then exactly 64 LOWERCASE hex characters.
// Uppercase hex decodes to the same bytes, so accepting it would let two different strings
// name one piece of content — and a log that deduplicates by string would record it twice.
func Parse(s string) ([]byte, error) {
	hexPart, ok := strings.CutPrefix(s, Prefix)
	if !ok {
		return nil, fmt.Errorf("%w: missing %q prefix", ErrMalformed, Prefix)
	}
	if len(hexPart) != sha256.Size*2 {
		return nil, fmt.Errorf("%w: want %d hex characters, got %d", ErrMalformed, sha256.Size*2, len(hexPart))
	}
	if strings.ToLower(hexPart) != hexPart {
		return nil, fmt.Errorf("%w: hex must be lowercase", ErrMalformed)
	}
	raw, err := hex.DecodeString(hexPart)
	if err != nil {
		return nil, fmt.Errorf("%w: %w", ErrMalformed, err)
	}
	return raw, nil
}
