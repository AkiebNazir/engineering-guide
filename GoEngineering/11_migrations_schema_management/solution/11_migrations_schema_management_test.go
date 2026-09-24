package migrations

import (
	"context"
	"database/sql"
	"errors"
	"path/filepath"
	"testing"

	_ "modernc.org/sqlite"
)

// newTestDB opens a fresh temp-file SQLite database for one test. A temp
// file (rather than ":memory:") exercises the exact same code path
// production would use against Postgres/MySQL, and t.TempDir() guarantees
// cleanup even on failure.
func newTestDB(t *testing.T) *sql.DB {
	t.Helper()
	path := filepath.Join(t.TempDir(), "test.db")
	db, err := sql.Open("sqlite", path)
	if err != nil {
		t.Fatalf("open sqlite: %v", err)
	}
	t.Cleanup(func() { db.Close() })
	return db
}

func sampleSet() []Migration {
	return []Migration{
		{
			Version: 1,
			Name:    "create_users",
			Up:      `CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL);`,
			Down:    `DROP TABLE users;`,
		},
		{
			Version: 2,
			Name:    "create_posts",
			Up:      `CREATE TABLE posts (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL);`,
			Down:    `DROP TABLE posts;`,
		},
		{
			Version: 3,
			Name:    "add_users_bio",
			Up:      `ALTER TABLE users ADD COLUMN bio TEXT;`,
			Down:    ``, // deliberately irreversible
		},
	}
}

func tableExists(t *testing.T, db *sql.DB, name string) bool {
	t.Helper()
	var got string
	err := db.QueryRow(`SELECT name FROM sqlite_master WHERE type='table' AND name = ?`, name).Scan(&got)
	if errors.Is(err, sql.ErrNoRows) {
		return false
	}
	if err != nil {
		t.Fatalf("check table %q: %v", name, err)
	}
	return true
}

func TestNewMigrator_ValidatesVersions(t *testing.T) {
	t.Parallel()
	db := newTestDB(t)

	tests := []struct {
		name    string
		set     []Migration
		wantErr bool
	}{
		{"valid", sampleSet(), false},
		{"empty is valid", nil, false},
		{"zero version", []Migration{{Version: 0, Name: "bad"}}, true},
		{"negative version", []Migration{{Version: -1, Name: "bad"}}, true},
		{
			"duplicate version",
			[]Migration{{Version: 1, Name: "a"}, {Version: 1, Name: "b"}},
			true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := NewMigrator(db, tt.set)
			if (err != nil) != tt.wantErr {
				t.Fatalf("NewMigrator() err = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestUp_AppliesInOrderAndIsIdempotent(t *testing.T) {
	t.Parallel()
	db := newTestDB(t)
	ctx := context.Background()

	m, err := NewMigrator(db, sampleSet())
	if err != nil {
		t.Fatalf("NewMigrator: %v", err)
	}
	if err := m.EnsureSchemaTable(ctx); err != nil {
		t.Fatalf("EnsureSchemaTable: %v", err)
	}

	applied, err := m.Up(ctx)
	if err != nil {
		t.Fatalf("Up: %v", err)
	}
	if want := []int{1, 2, 3}; !equalInts(applied, want) {
		t.Fatalf("Up() applied = %v, want %v", applied, want)
	}

	for _, tbl := range []string{"users", "posts"} {
		if !tableExists(t, db, tbl) {
			t.Errorf("expected table %q to exist after Up", tbl)
		}
	}

	// Calling Up again must be a safe no-op: empty, non-nil slice.
	applied2, err := m.Up(ctx)
	if err != nil {
		t.Fatalf("second Up: %v", err)
	}
	if applied2 == nil {
		t.Fatal("second Up() returned nil slice, want empty non-nil slice")
	}
	if len(applied2) != 0 {
		t.Fatalf("second Up() applied = %v, want empty", applied2)
	}
}

func TestUpTo_StopsAtTarget(t *testing.T) {
	t.Parallel()
	db := newTestDB(t)
	ctx := context.Background()

	m, err := NewMigrator(db, sampleSet())
	if err != nil {
		t.Fatalf("NewMigrator: %v", err)
	}
	if err := m.EnsureSchemaTable(ctx); err != nil {
		t.Fatalf("EnsureSchemaTable: %v", err)
	}

	applied, err := m.UpTo(ctx, 2)
	if err != nil {
		t.Fatalf("UpTo: %v", err)
	}
	if want := []int{1, 2}; !equalInts(applied, want) {
		t.Fatalf("UpTo(2) applied = %v, want %v", applied, want)
	}
	if tableExists(t, db, "posts") == false {
		t.Fatal("expected posts table after UpTo(2)")
	}

	// version 3's ALTER TABLE hasn't run yet.
	var hasBio bool
	rows, err := db.Query(`PRAGMA table_info(users)`)
	if err != nil {
		t.Fatalf("pragma table_info: %v", err)
	}
	defer rows.Close()
	for rows.Next() {
		var cid int
		var name, ctype string
		var notnull, pk int
		var dflt sql.NullString
		if err := rows.Scan(&cid, &name, &ctype, &notnull, &dflt, &pk); err != nil {
			t.Fatalf("scan pragma row: %v", err)
		}
		if name == "bio" {
			hasBio = true
		}
	}
	if hasBio {
		t.Fatal("expected users.bio to NOT exist yet after UpTo(2)")
	}

	if _, err := m.UpTo(ctx, 99); !errors.Is(err, ErrUnknownVersion) {
		t.Fatalf("UpTo(99) err = %v, want ErrUnknownVersion", err)
	}
}

func TestUp_FailureLeavesDatabaseUntouched(t *testing.T) {
	t.Parallel()
	db := newTestDB(t)
	ctx := context.Background()

	set := []Migration{
		{Version: 1, Name: "ok", Up: `CREATE TABLE ok_table (id INTEGER PRIMARY KEY);`, Down: `DROP TABLE ok_table;`},
		{Version: 2, Name: "broken", Up: `THIS IS NOT VALID SQL;`, Down: ``},
		{Version: 3, Name: "never_reached", Up: `CREATE TABLE never_table (id INTEGER PRIMARY KEY);`, Down: `DROP TABLE never_table;`},
	}
	m, err := NewMigrator(db, set)
	if err != nil {
		t.Fatalf("NewMigrator: %v", err)
	}
	if err := m.EnsureSchemaTable(ctx); err != nil {
		t.Fatalf("EnsureSchemaTable: %v", err)
	}

	applied, err := m.Up(ctx)
	if err == nil {
		t.Fatal("expected Up to fail on invalid SQL")
	}
	if want := []int{1}; !equalInts(applied, want) {
		t.Fatalf("Up() applied before failure = %v, want %v", applied, want)
	}

	if !tableExists(t, db, "ok_table") {
		t.Error("migration 1 should have committed despite migration 2 failing")
	}
	if tableExists(t, db, "never_table") {
		t.Error("migration 3 should never have run")
	}

	versions, err := m.AppliedVersions(ctx)
	if err != nil {
		t.Fatalf("AppliedVersions: %v", err)
	}
	if _, ok := versions[2]; ok {
		t.Error("failed migration 2 must not appear in schema_migrations")
	}
	if len(versions) != 1 {
		t.Errorf("AppliedVersions = %v, want exactly {1: ...}", versions)
	}

	// Retrying after fixing nothing still fails the same way and still
	// doesn't touch migration 3 — Up() must not skip a permanently-broken
	// migration to "make progress".
	applied2, err := m.Up(ctx)
	if err == nil {
		t.Fatal("expected retry of Up to fail again")
	}
	if len(applied2) != 0 {
		t.Fatalf("retry Up() applied = %v, want empty (migration 2 still broken)", applied2)
	}
}

func TestDown_RevertsInReverseOrder(t *testing.T) {
	t.Parallel()
	db := newTestDB(t)
	ctx := context.Background()

	// Use a set where every migration has a Down script.
	set := []Migration{
		{Version: 1, Name: "a", Up: `CREATE TABLE a_table (id INTEGER PRIMARY KEY);`, Down: `DROP TABLE a_table;`},
		{Version: 2, Name: "b", Up: `CREATE TABLE b_table (id INTEGER PRIMARY KEY);`, Down: `DROP TABLE b_table;`},
	}
	m, err := NewMigrator(db, set)
	if err != nil {
		t.Fatalf("NewMigrator: %v", err)
	}
	if err := m.EnsureSchemaTable(ctx); err != nil {
		t.Fatalf("EnsureSchemaTable: %v", err)
	}
	if _, err := m.Up(ctx); err != nil {
		t.Fatalf("Up: %v", err)
	}

	reverted, err := m.Down(ctx, 1)
	if err != nil {
		t.Fatalf("Down(1): %v", err)
	}
	if want := []int{2}; !equalInts(reverted, want) {
		t.Fatalf("Down(1) reverted = %v, want %v", reverted, want)
	}
	if tableExists(t, db, "b_table") {
		t.Error("b_table should have been dropped by Down(1)")
	}
	if !tableExists(t, db, "a_table") {
		t.Error("a_table should still exist after Down(1)")
	}

	reverted2, err := m.Down(ctx, 5) // more steps than remain applied
	if err != nil {
		t.Fatalf("Down(5): %v", err)
	}
	if want := []int{1}; !equalInts(reverted2, want) {
		t.Fatalf("Down(5) reverted = %v, want %v", reverted2, want)
	}
}

func TestDown_NoDownScriptReturnsSentinel(t *testing.T) {
	t.Parallel()
	db := newTestDB(t)
	ctx := context.Background()

	m, err := NewMigrator(db, sampleSet()) // version 3 has empty Down
	if err != nil {
		t.Fatalf("NewMigrator: %v", err)
	}
	if err := m.EnsureSchemaTable(ctx); err != nil {
		t.Fatalf("EnsureSchemaTable: %v", err)
	}
	if _, err := m.Up(ctx); err != nil {
		t.Fatalf("Up: %v", err)
	}

	if _, err := m.Down(ctx, 1); !errors.Is(err, ErrNoDownScript) {
		t.Fatalf("Down(1) err = %v, want ErrNoDownScript", err)
	}
}

func TestDownTo_UnknownVersion(t *testing.T) {
	t.Parallel()
	db := newTestDB(t)
	ctx := context.Background()

	m, err := NewMigrator(db, sampleSet())
	if err != nil {
		t.Fatalf("NewMigrator: %v", err)
	}
	if err := m.EnsureSchemaTable(ctx); err != nil {
		t.Fatalf("EnsureSchemaTable: %v", err)
	}

	if _, err := m.DownTo(ctx, 999); !errors.Is(err, ErrUnknownVersion) {
		t.Fatalf("DownTo(999) err = %v, want ErrUnknownVersion", err)
	}
}

func TestStatus_ReflectsAppliedState(t *testing.T) {
	t.Parallel()
	db := newTestDB(t)
	ctx := context.Background()

	set := []Migration{
		{Version: 1, Name: "a", Up: `CREATE TABLE a_table (id INTEGER PRIMARY KEY);`, Down: `DROP TABLE a_table;`},
		{Version: 2, Name: "b", Up: `CREATE TABLE b_table (id INTEGER PRIMARY KEY);`, Down: `DROP TABLE b_table;`},
	}
	m, err := NewMigrator(db, set)
	if err != nil {
		t.Fatalf("NewMigrator: %v", err)
	}
	if err := m.EnsureSchemaTable(ctx); err != nil {
		t.Fatalf("EnsureSchemaTable: %v", err)
	}

	status, err := m.Status(ctx)
	if err != nil {
		t.Fatalf("Status: %v", err)
	}
	if len(status) != 2 || status[0].Applied || status[1].Applied {
		t.Fatalf("Status() before Up = %+v, want both unapplied", status)
	}

	if _, err := m.UpTo(ctx, 1); err != nil {
		t.Fatalf("UpTo(1): %v", err)
	}

	status, err = m.Status(ctx)
	if err != nil {
		t.Fatalf("Status: %v", err)
	}
	if !status[0].Applied {
		t.Errorf("Status()[0] (v1) should be applied")
	}
	if status[0].AppliedAt.IsZero() {
		t.Errorf("Status()[0].AppliedAt should be set")
	}
	if status[1].Applied {
		t.Errorf("Status()[1] (v2) should not be applied yet")
	}
	if !status[1].AppliedAt.IsZero() {
		t.Errorf("Status()[1].AppliedAt should be zero value, got %v", status[1].AppliedAt)
	}
}

func equalInts(a, b []int) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}
