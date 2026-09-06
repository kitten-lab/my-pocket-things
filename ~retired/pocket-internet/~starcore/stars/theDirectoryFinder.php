<?php
/**
 * CHESTER'S NOTE: Finds or creates a directory for the given space slug and subdirectory.
 */

function dirFinder(string $spaceSlug, string $subdir): string {
  $dir = STORAGE_ROOT . '/' . $spaceSlug . '/' . $subdir;
  return $dir;
}


function checkDir(string $dir): void {
  if (!is_dir($dir)) {
    loadContent('body', "<p>No chips folder yet.</p>");
    return;
  }
}

function dirProducer(string $root, string $spaceSlug, string $subdir): string {
    $dir = $root . '/' . $spaceSlug . '/' . $subdir;
    if (!is_dir($dir)) {
        mkdir($dir, 0777, true);
    }
    return $dir;
}

function dirMaker(string $path): void {
    if (!is_dir($path)) {
        mkdir($path, 0777, true);
    }
}

/** Host name of a chip — not the local area copy. */
function masterChipPointer(string $filename): string {
  return '~storage/library/chips/' . $filename;
}

/** Host name of a good — not the local area copy. */
function masterGoodPointer(string $filename): string {
  return '~storage/library/goods/' . $filename;
}

function masterGoodsDir(): string {
  $dir = defined('MASTERGOODS_ROOT') ? MASTERGOODS_ROOT : (STORAGE_ROOT . '/~library/goods');
  dirMaker($dir);
  return $dir;
}

function kindsDir(): string {
  $dir = defined('MASTERKINDS_ROOT') ? MASTERKINDS_ROOT : (STORAGE_ROOT . '/~library/kinds');
  dirMaker($dir);
  return $dir;
}

function listKinds(): array {
  $out = [];
  foreach (glob(kindsDir() . '/*.chip') ?: [] as $path) {
    $paper = openChip($path);
    $type = $paper ? (string) chipAsk($paper, 'kind.type') : '';
    $type = strtoupper(preg_replace('/[^a-z]/i', '', $type));
    if ($type === '') {
      continue;
    }
    $out[$type] = $paper;
  }
  ksort($out);
  return $out;
}

function openKind(string $type): ?array {
  $type = strtoupper(preg_replace('/[^a-z]/i', '', $type));
  $kinds = listKinds();
  return $kinds[$type] ?? null;
}

function kindFlag(?array $kind, string $name, string $default = 'no'): string {
  if ($kind === null) {
    return $default;
  }
  $value = chipAsk($kind, 'kind.' . $name);
  if ($value === null || $value === '') {
    return $default;
  }
  return strtolower((string) $value);
}

function kindLines(?array $kind): array {
  if ($kind === null) {
    return [];
  }
  $lines = chipAsk($kind, 'prop.lines');
  if (!is_array($lines)) {
    return [];
  }
  $clean = [];
  foreach ($lines as $line) {
    $name = strtolower(preg_replace('/[^a-z0-9_]/i', '', (string) $line));
    if ($name !== '') {
      $clean[] = $name;
    }
  }
  return $clean;
}

function citeBasename(string $cite): string {
  return basename(str_replace('\\', '/', $cite));
}

function normalizeGoodCite(string $raw): string {
  if ($raw === '') {
    return '';
  }
  $name = citeBasename($raw);
  if ($name === '' || $name === '.' || $name === '..') {
    return '';
  }
  return masterGoodPointer($name);
}

/** Dual-write a chip: host save + local area copy. Same filename. */
function writeChipBoth(string $filename, string $body): void {
  $local = dirProducer(STORAGE_ROOT, Space_Slug, 'library/chips/');
  $master = MASTERSTORE_ROOT . '/' . $filename;
  dirMaker(dirname($master));
  file_put_contents($local . '/' . $filename, $body);
  file_put_contents($master, $body);
}

/** Dual-write a good file under a GOODS chip code. Same stem as the goods chip. */
function writeGoodBoth(string $stem, string $fromPath): bool {
  $localPath = dirProducer(STORAGE_ROOT, Space_Slug, 'goods/') . '/' . $stem;
  $masterPath = masterGoodsDir() . '/' . $stem;
  $placed = is_uploaded_file($fromPath)
    ? move_uploaded_file($fromPath, $localPath)
    : copy($fromPath, $localPath);
  if (!$placed) {
    return false;
  }
  return copy($localPath, $masterPath);
}

/** Local-area URL for a host cite, if this space has a copy. */
function localGoodUrl(string $cite): ?string {
  $name = citeBasename($cite);
  if ($name === '' || $name === '.' || $name === '..') {
    return null;
  }
  $path = dirFinder(Space_Slug, 'goods') . '/' . $name;
  if (!is_file($path)) {
    return null;
  }
  return URL_ROOT . '/~storage/' . Space_Slug . '/goods/' . rawurlencode($name);
}