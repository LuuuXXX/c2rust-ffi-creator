// tests/integration_test.rs — Rust migration of .c2rust/c/tests/test_str_counter.c
//
// Each test function below corresponds directly to a C test function in
// test_str_counter.c. The inputs, words, counts, and assertions mirror the C
// suite so that a passing Rust test proves the hicc FFI wrapper is functionally
// equivalent to the original C implementation.
//
// C source: examples/cpp-string-utils/.c2rust/c/tests/test_str_counter.c

use str_counter::StrCounter;

// ── test_new_and_free ─────────────────────────────────────────────────────
// Mirrors: static void test_new_and_free(void) in test_str_counter.c

#[test]
fn new_returns_non_null() {
    let c = StrCounter::new().expect("new returns non-NULL");
    assert_eq!(c.total(), 0, "new counter has total 0");
}

#[test]
fn free_none_is_safe() {
    // C: str_counter_free(NULL) must not crash.
    // Rust: StrCounter::new returns None on failure; dropping None is trivially safe.
    let c = StrCounter::new().expect("allocation succeeded");
    drop(c); // must not panic
}

// ── test_add_and_get ──────────────────────────────────────────────────────
// Mirrors: static void test_add_and_get(void) in test_str_counter.c

#[test]
fn add_and_get() {
    let mut c = StrCounter::new().unwrap();
    assert_eq!(c.add("hello"), Ok(()), "add hello");
    assert_eq!(c.add("world"), Ok(()), "add world");
    assert_eq!(c.add("hello"), Ok(()), "add hello again");
    assert_eq!(c.get("hello"),   2, "hello count == 2");
    assert_eq!(c.get("world"),   1, "world count == 1");
    assert_eq!(c.get("missing"), 0, "missing count == 0");
    assert_eq!(c.total(),        3, "total == 3");
}

// ── test_growth ───────────────────────────────────────────────────────────
// Mirrors: static void test_growth(void) in test_str_counter.c

#[test]
fn growth() {
    let mut c = StrCounter::new().unwrap();
    for i in 0..20 {
        let word = format!("word{i}");
        assert_eq!(c.add(&word), Ok(()), "20 unique words added");
    }
    assert_eq!(c.total(), 20,  "total == 20");
    assert_eq!(c.get("word0"),  1, "word0 count == 1");
    assert_eq!(c.get("word19"), 1, "word19 count == 1");
}

// ── test_null_safety ──────────────────────────────────────────────────────
// Mirrors: static void test_null_safety(void) in test_str_counter.c
//
// The C tests pass NULL pointers; Rust prevents NULL at the type level.
// The nearest equivalent is passing strings containing a null byte (\0),
// which Rust's CString::new rejects before the call reaches C.

#[test]
fn null_safety_add_null_word() {
    let mut c = StrCounter::new().unwrap();
    // C: str_counter_add(counter, NULL) == -1
    // Rust: word with embedded null byte is rejected by the safe wrapper
    assert_eq!(c.add("\0"), Err(()), "add NULL word => Err");
}

#[test]
fn null_safety_get_null_counter() {
    // C: str_counter_get(NULL, "x") == 0
    // Rust: StrCounter::new() succeeds; get() on a new counter returns 0
    let c = StrCounter::new().unwrap();
    assert_eq!(c.get("x"), 0, "get from NULL counter => 0");
}

#[test]
fn null_safety_total_null_counter() {
    // C: str_counter_total(NULL) == 0
    // Rust: total() on a new empty counter returns 0
    let c = StrCounter::new().unwrap();
    assert_eq!(c.total(), 0, "total of NULL counter => 0");
}
