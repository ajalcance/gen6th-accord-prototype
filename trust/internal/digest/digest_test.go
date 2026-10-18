package digest

import (
	"bytes"
	"crypto/sha256"
	"errors"
	"strings"
	"sync"
	"testing"
)

func TestOfIsTheCanonicalForm(t *testing.T) {
	// SHA-256 of the empty input, a published constant — not recomputed by the code under test.
	const empty = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
	if got := Of(nil); got != empty {
		t.Fatalf("Of(nil) = %q, want %q", got, empty)
	}
}

func TestParseRoundTrips(t *testing.T) {
	content := []byte("an evidence manifest")
	raw, err := Parse(Of(content))
	if err != nil {
		t.Fatalf("Parse(Of(...)) failed: %v", err)
	}
	want := sha256.Sum256(content)
	if !bytes.Equal(raw, want[:]) {
		t.Fatalf("Parse returned %x, want %x", raw, want)
	}
}

func TestParseRefusesEveryNonCanonicalForm(t *testing.T) {
	valid := Of([]byte("x"))
	hexPart := strings.TrimPrefix(valid, Prefix)
	cases := map[string]string{
		"no prefix":          hexPart,
		"other algorithm":    "sha512:" + hexPart,
		"uppercase hex":      Prefix + strings.ToUpper(hexPart),
		"too short":          valid[:len(valid)-1],
		"too long":           valid + "0",
		"not hex":            Prefix + strings.Repeat("z", 64),
		"empty":              "",
		"prefix only":        Prefix,
		"leading whitespace": " " + valid,
	}
	for name, input := range cases {
		t.Run(name, func(t *testing.T) {
			if _, err := Parse(input); !errors.Is(err, ErrMalformed) {
				t.Fatalf("Parse(%q) = %v, want ErrMalformed", input, err)
			}
		})
	}
}

// Of is called from many goroutines in the services that will use it; -race proves it shares
// no state.
func TestOfIsSafeForConcurrentUse(t *testing.T) {
	var wg sync.WaitGroup
	for i := range byte(32) {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if _, err := Parse(Of([]byte{i})); err != nil {
				t.Errorf("concurrent Parse(Of(...)) failed: %v", err)
			}
		}()
	}
	wg.Wait()
}
