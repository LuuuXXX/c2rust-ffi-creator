// Integration tests for complex-kv-store.
//
// These call the safe Rust API (KvStore) which in turn calls the compiled C
// library through bindgen-generated FFI bindings.

use kv_store::KvStore;
use kv_store::error::KvError;

// ── Lifecycle ─────────────────────────────────────────────────────────────

#[test]
fn new_returns_empty_store() {
    let store = KvStore::new(0).expect("allocation failed");
    assert_eq!(store.count(), 0);
}

#[test]
fn new_with_custom_capacity() {
    let store = KvStore::new(32).expect("allocation failed");
    assert_eq!(store.count(), 0);
}

// ── Set and Get ───────────────────────────────────────────────────────────

#[test]
fn set_and_get_single_entry() {
    let mut store = KvStore::new(0).unwrap();
    store.set("greeting", "hello").unwrap();
    assert_eq!(store.get("greeting").as_deref(), Some("hello"));
}

#[test]
fn set_multiple_entries() {
    let mut store = KvStore::new(4).unwrap();
    store.set("a", "1").unwrap();
    store.set("b", "2").unwrap();
    store.set("c", "3").unwrap();
    assert_eq!(store.count(), 3);
    assert_eq!(store.get("a").as_deref(), Some("1"));
    assert_eq!(store.get("b").as_deref(), Some("2"));
    assert_eq!(store.get("c").as_deref(), Some("3"));
}

#[test]
fn get_missing_key_returns_none() {
    let store = KvStore::new(0).unwrap();
    assert!(store.get("nonexistent").is_none());
}

// ── Update ────────────────────────────────────────────────────────────────

#[test]
fn set_same_key_twice_updates_value() {
    let mut store = KvStore::new(0).unwrap();
    store.set("k", "v1").unwrap();
    store.set("k", "v2").unwrap();
    assert_eq!(store.count(), 1, "update must not increase count");
    assert_eq!(store.get("k").as_deref(), Some("v2"));
}

// ── Delete ────────────────────────────────────────────────────────────────

#[test]
fn delete_existing_key() {
    let mut store = KvStore::new(0).unwrap();
    store.set("x", "val").unwrap();
    store.delete("x").unwrap();
    assert_eq!(store.count(), 0);
    assert!(store.get("x").is_none());
}

#[test]
fn delete_middle_entry_preserves_others() {
    let mut store = KvStore::new(0).unwrap();
    store.set("a", "1").unwrap();
    store.set("b", "2").unwrap();
    store.set("c", "3").unwrap();
    store.delete("b").unwrap();
    assert_eq!(store.count(), 2);
    assert_eq!(store.get("a").as_deref(), Some("1"));
    assert!(store.get("b").is_none());
    assert_eq!(store.get("c").as_deref(), Some("3"));
}

#[test]
fn delete_missing_key_returns_not_found() {
    let mut store = KvStore::new(0).unwrap();
    assert_eq!(store.delete("ghost"), Err(KvError::NotFound));
}

// ── Error handling ────────────────────────────────────────────────────────

#[test]
fn set_key_with_null_byte_returns_invalid_argument() {
    let mut store = KvStore::new(0).unwrap();
    assert_eq!(store.set("key\0bad", "v"), Err(KvError::InvalidArgument));
}

#[test]
fn set_value_with_null_byte_returns_invalid_argument() {
    let mut store = KvStore::new(0).unwrap();
    assert_eq!(store.set("k", "v\0bad"), Err(KvError::InvalidArgument));
}

// ── Stress / growth ───────────────────────────────────────────────────────

#[test]
fn store_grows_beyond_initial_capacity() {
    let mut store = KvStore::new(2).unwrap();
    for i in 0..50 {
        let key = format!("key{i}");
        let val = format!("val{i}");
        store.set(&key, &val).unwrap();
    }
    assert_eq!(store.count(), 50);
    // Spot-check a few values
    assert_eq!(store.get("key0").as_deref(),  Some("val0"));
    assert_eq!(store.get("key49").as_deref(), Some("val49"));
}

// ── Drop / RAII ───────────────────────────────────────────────────────────

#[test]
fn store_is_dropped_without_panic() {
    let mut store = KvStore::new(0).unwrap();
    store.set("tmp", "data").unwrap();
    drop(store); // kv_destroy must not crash or leak
}
